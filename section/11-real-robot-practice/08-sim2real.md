# Sim2Real

本节简要介绍 Sim2Real 接口:策略在仿真训练、迁移到真机时跨越的 reality gap(动力学差距 + 感知差距),以及仿真与真机之间需要对齐的接口——observation/action 空间、坐标系、控制频率与延迟。缩小 gap 的具体方法(域随机化、系统辨识、teacher-student 特权学习、少样本真机微调)与 RL 视角的方法选型见 [Sim-to-Real RL](../09-reinforcement-learning-for-robotics/06-sim2real-rl.md);真机上线门控见本章真机部署与推理。

# Sim2Real：从仿真策略到真机执行的迁移接口

仿真环境为机器人策略训练提供了两个不可替代的优势:几乎为零的数据获取成本和完全可控的实验条件。在 Isaac Sim、MuJoCo、SAPIEN 等仿真平台中,机械臂可以以数千倍于真实时间的速度并行运行,生成规模远超人工采集的训练数据;同时仿真器能够精确重置环境状态,使研究者可以在完全相同的初始条件下反复评估策略的改进效果。然而,当训练好的策略从仿真环境迁移到真实机器人上执行时,仿真与真实世界之间的系统性差异——通常称为 Reality Gap——会导致策略性能出现显著退化,严重时甚至完全失效。

Sim2Real 的核心问题因此可以表述为:如何设计仿真训练流程和策略接口,使得在仿真中表现良好的策略,在迁移到真机时不需要或仅需要极少的额外调整就能保持可接受的成功率。这个问题的难点在于,仿真器本质上是一个对真实物理世界的近似模型——它对刚体动力学、接触力学、光照渲染和传感器噪声的建模都存在不同程度的简化或偏差,而这些偏差恰恰是策略在仿真中学会依赖的"捷径"特征。本节将从 Reality Gap 的构成分析出发,逐步拆解仿真与真机之间需要对齐的接口要素,并概述缩小 gap 的主流方法论。

## Reality Gap 的构成:动力学差距与感知差距

Reality Gap 可以粗略地分为两个相互关联但性质不同的维度:动力学差距和感知差距。理解它们各自的来源和表现形式,是设计有效迁移策略的前提。

动力学差距指的是仿真物理引擎与真实物理世界在物体运动规律上的偏差。现代仿真器通常将机械臂建模为理想刚体,其连杆质量、惯量矩阵和质心位置来自 CAD 模型或出厂参数,但在真实世界中这些参数总是存在制造公差和装配误差。例如,一个在仿真中被建模为质量均匀分布的铝制连杆,实际上可能因为内部走线和螺栓孔洞而具有不同的转动惯量。更关键的是,接触力学——包括摩擦力、接触刚度、阻尼和 restitution 系数——在仿真中通常被高度简化。MuJoCo 使用软接触模型和凸面近似来处理碰撞检测,Isaac Sim 的 PhysX 引擎在高速碰撞场景下可能引入数值不稳定性,而真实世界中物体之间的微观接触形变、表面纹理和材料非线性几乎不可能被精确建模。这意味着一个在仿真中通过精准力度控制完成精细装配的策略,在真机上很可能因为摩擦力差异而卡住或滑脱。

感知差距则来源于仿真渲染的视觉图像与真实相机采集图像之间的分布偏移。仿真器虽然可以通过光线追踪和 PBR 材质生成高保真图像,但渲染结果与真实照片之间仍然存在纹理细节、光照自然度、阴影柔和度和景深效果等方面的系统性差异。一个在仿真中训练好的视觉策略,往往已经学会了利用渲染图像中特定的颜色分布、纹理模式甚至背景特征作为决策依据,当被部署到真实的实验室光照和相机噪声环境中时,这些视觉线索可能完全失效。更隐蔽的是,仿真中的相机模型通常假设理想的小孔成像和无噪声传感器,而真实相机存在镜头畸变、CMOS 噪声、白平衡偏移和自动曝光调节,这些看似微小的差异在策略的深层视觉特征空间中可能被放大数倍。

实际工程中,动力学差距和感知差距往往相互耦合。例如,机械臂在真实环境中执行动作后,末端的实际到达位置与仿真预期存在偏差,这个偏差改变了下一帧图像中物体的外观位置,进而导致策略的后续决策基于错误的视觉输入不断累积误差——最终的结果是策略在真机上快速偏离仿真中的行为轨迹。

## 观测空间与动作空间的接口对齐

将策略从仿真迁移到真机的第一个工程步骤,是确保仿真环境暴露的观测接口和动作接口与真机完全一致。这里的"完全一致"不仅是数据类型和维度的一致,还包括数值范围、归一化方式、坐标系约定和时序对齐方式的匹配。

观测空间的对应关系需要在仿真配置中显式定义。以最常用的机器人观测为例,仿真器通常能够直接读取每个关节的角度、角速度和力矩,以及末端执行器的六自由度位姿和速度。在真机上,这些状态信息来自机器人驱动器的反馈报文或控制器状态接口。仿真环境中需要配置与真机相同的观测字段和排列顺序,以确保训练出的策略在接收到真实观测时能够正确解析。以下是一个观测空间对齐的配置示例,展示了如何定义仿真与真机之间共享的观测字典结构:

```python
class ObservationSpec:
    """仿真与真机共享的观测规格定义"""

    def __init__(self, robot_config):
        # 本体感知观测:关节状态
        self.proprio_keys = [
            "joint_positions",      # (7,)  for 7-DoF arm
            "joint_velocities",     # (7,)
            "joint_torques",        # (7,)
            "ee_pose",              # (7,)  xyz + quaternion
            "gripper_position",     # (1,)  gripper opening width
        ]

        # 视觉观测:相机图像
        self.visual_keys = [
            "front_camera_rgb",     # (480, 640, 3)  uint8
            "wrist_camera_rgb",     # (480, 640, 3)  uint8
            "front_camera_depth",   # (480, 640, 1)  float32 (m)
        ]

        # 每个观测字段的归一化参数
        self.normalization = {
            "joint_positions": {
                "mean": robot_config.joint_means,   # shape (7,)
                "std":  robot_config.joint_stds,     # shape (7,)
            },
            "ee_pose": {
                "mean": [0.3, 0.0, 0.2, 0, 0, 0, 1],
                "std":  [0.15, 0.15, 0.1, 1, 1, 1, 1],
            },
            "front_camera_rgb": {
                "mean": [0.485, 0.456, 0.406],      # ImageNet stats
                "std":  [0.229, 0.224, 0.225],
            },
        }
```

动作空间的对称性同样重要。仿真和真机必须使用完全相同的动作表示——如果用绝对关节位置作为动作,仿真和真机都需要直接输出目标关节角;如果用末端位姿增量作为动作,两者都需要输出六自由度的 delta pose。更关键的是动作的数值尺度:仿真中的关节力矩或速度通常没有实际物理限制,而真机存在硬性的速度、加速度和力矩上限。如果仿真训练时策略学会了以每秒三弧度的速度移动关节,而真机的安全限速仅为一弧度每秒,策略在真机上的行为就会被硬截断,导致完全不同的运动轨迹。

以下是动作空间对齐的典型实现,展示如何在仿真环境和真机控制器之间建立一致的接口:

```python
class ActionInterface:
    """仿真与真机共用的动作接口"""

    def __init__(self, action_type, robot_config):
        self.action_type = action_type
        self.robot_config = robot_config

    def normalize_action(self, raw_action):
        """将策略输出的归一化动作转换为物理量"""

        if self.action_type == "joint_position_absolute":
            # 策略输出 [-1, 1]^7 → 转换为实际关节弧度
            low = self.robot_config.joint_lower_limits  # e.g. [-2.89, -1.76, ...]
            high = self.robot_config.joint_upper_limits  # e.g. [2.89, 1.76, ...]
            physical = (raw_action + 1.0) / 2.0 * (high - low) + low
            return physical

        elif self.action_type == "ee_delta_pose":
            # 策略输出 [-1, 1]^6 → 转换为末端位姿增量
            # 前三维:平移增量 (m),范围 ±5cm
            # 后三维:旋转增量 (axis-angle),范围 ±0.5rad
            delta_xyz = raw_action[:3] * 0.05
            delta_rot = raw_action[3:] * 0.5
            return np.concatenate([delta_xyz, delta_rot])

        elif self.action_type == "joint_position_delta":
            # 策略输出 [-1, 1]^7 → 转换为关节角增量
            # 每个关节最大步进步长根据关节类型分别设定
            max_step = self.robot_config.joint_delta_limits  # shape (7,)
            return raw_action * max_step

    def clamp_to_limits(self, action):
        """将动作裁剪到机器人物理限制范围内"""
        if self.action_type == "joint_position_absolute":
            return np.clip(
                action,
                self.robot_config.joint_lower_limits,
                self.robot_config.joint_upper_limits
            )
        elif self.action_type == "ee_delta_pose":
            # 速度限制:位置增量不超过 5cm/step,旋转不超过 0.5rad/step
            action[:3] = np.clip(action[:3], -0.05, 0.05)
            action[3:] = np.clip(action[3:], -0.5, 0.5)
            return action
        else:
            return action
```

在动作接口的实现中还有一个容易被忽略但影响显著的细节:仿真器通常在同一时间步内完成动作的执行和下一帧观测的渲染,而真机系统中动作下发、电机响应、传感器采集之间存在非零延迟。如果仿真中的控制频率设定为 50 Hz,但真机实际只能以 20 Hz 的形式完成"感知-决策-执行"完整闭环,那么策略在仿真中学到的动态响应特性(例如在快速抓取任务中对视觉反馈的即时反应)在真机上就无法复现。因此,仿真环境的控制周期应尽可能与真机实际可达到的频率保持一致,或者在仿真中刻意引入控制延迟,使策略在训练阶段就适应这种异步性。

## 坐标系的统一与外部标定

当仿真策略迁移到真机时,所有空间量——末端位姿、物体位置、相机外参、工作空间边界——都需要在统一的坐标系下表达。仿真环境通常使用一个全局世界坐标系,而真机系统中至少存在机器人基座坐标系、相机坐标系和世界坐标系三个不同的参照系,它们之间的关系需要通过标定来确定。

最常见的坐标系对齐流程是:首先在真机工作空间中定义一个 world frame,通常选择机器人基座的前方桌面某一点作为原点,以桌面平面为 xy 平面、竖直向上为 z 轴的正方向。然后通过手眼标定确定相机坐标系到机器人基座坐标系的变换矩阵,使视觉感知结果可以直接在机器人运动空间的坐标系中表达。最后,将仿真环境中的物体布局、相机位姿和工作空间范围全部与真机的对应坐标系对齐。这样做的目的是让策略在仿真中看到的"物体位于相机前方 30 厘米处"这个观测,与真机上完全相同的空间关系对应起来。

以下是一个坐标系对齐的简化实现,展示仿真与真机之间的变换链:

```python
class CoordinateAlignment:
    """仿真与真机之间的坐标系对齐管理"""

    def __init__(self):
        self.T_cam_to_base = None   # 相机→机器人基座
        self.T_base_to_world = None  # 机器人基座→世界
        self.T_ee_to_base = None     # 末端→机器人基座 (来自正运动学)

    def calibrate_camera(self, robot, camera, calibration_board):
        """通过手眼标定获取相机到机器人基座的变换"""
        # 采集多组观测:机械臂末端移动到不同位置,同时拍摄标定板
        T_board_to_cam_list = []
        T_base_to_ee_list = []

        for pose in self.generate_calibration_poses():
            robot.move_to(pose)
            T_base_to_ee_list.append(robot.forward_kinematics())

            rgb = camera.capture()
            T_board_to_cam = self.detect_board_pose(rgb, calibration_board)
            if T_board_to_cam is not None:
                T_board_to_cam_list.append(T_board_to_cam)

        # 求解 AX = XB 问题:求解相机到末端的固定变换
        T_cam_to_ee = self.solve_hand_eye(
            T_base_to_ee_list, T_board_to_cam_list
        )

        # 组合得到相机到机器人基座的变换
        self.T_cam_to_base = T_base_to_ee_list[-1] @ T_cam_to_ee

    def sim_to_real_observation(self, sim_obs):
        """将仿真观测中的空间量转换到真机坐标系"""
        # 仿真中物体位姿是相对于世界坐标系的
        # 真机中物体位姿是相对于相机坐标系的
        # 需要将两者对齐后才能喂给策略

        if "object_pose_in_world" in sim_obs:
            # 转换到真机相机坐标系
            obj_in_world = sim_obs["object_pose_in_world"]
            obj_in_cam = np.linalg.inv(self.T_cam_to_base) @ \
                         np.linalg.inv(self.T_base_to_world) @ \
                         obj_in_world
            sim_obs["object_pose_in_world"] = obj_in_cam

        return sim_obs
```

需要注意的是,仿真环境中的坐标系对齐不仅影响策略输入,还影响策略输出的解释。如果策略输出的是末端在世界坐标系中的绝对位姿,那么仿真的世界坐标系与真机的世界坐标系必须使用完全相同的原点和朝向;如果策略输出的是相对于当前末端位姿的增量,那么坐标系的对齐要求就宽松得多——这也是为什么许多 Sim2Real 成功的案例倾向于使用相对动作表示而非绝对动作表示。

## 控制频率与延迟的匹配

仿真与真机在时间维度上的不匹配是 Sim2Real 迁移中最容易被低估的问题。仿真器在单步内完成动作执行和状态更新,而真机系统中动作从软件指令到物理执行之间经历着多级延迟:控制线程将指令写入驱动 → 驱动通过总线(如 EtherCAT 或 CAN)发送到电机驱动器 → 电机响应并产生扭矩 → 机械结构在惯量作用下加速到位。这一整条链路的延迟通常在数毫秒到数十毫秒之间,而仿真中这一延迟为零。

真机系统中不同的信号通道具有不同的延迟特性。相机图像从曝光到在内存中可读取,通常需要经历传感器读出、ISP 处理和 USB 或以太网传输,延迟通常在 30 到 60 毫秒。而关节编码器的反馈通常通过实时总线以 1 kHz 的频率更新,延迟不到 1 毫秒。这就导致了所谓的时间错位问题:当策略接收到一帧图像时,图像反映的是约 50 毫秒前的场景状态,而同时读取到的关节角度则是几乎实时的。如果不进行补偿,策略就会基于时间不一致的观测做出决策,这也会导致一些问题。

以下是一个延迟测量的工程实现,用于在真机上量化各信号通道的延迟:

```python
class LatencyProfiler:
    """测量真机系统中各信号通道的延迟"""

    def __init__(self, robot, camera):
        self.robot = robot
        self.camera = camera

    def measure_action_latency(self, num_trials=100):
        """测量从下发指令到关节实际响应的延迟"""
        latencies = []

        for _ in range(num_trials):
            # 记录指令下发时刻
            cmd_time = time.perf_counter()

            # 下发一个微小的关节角扰动
            target = self.robot.get_joint_positions() + 0.01
            self.robot.command_joint_positions(target)

            # 轮询直到关节到达目标(容差范围内)
            while True:
                current = self.robot.get_joint_positions()
                if np.max(np.abs(current - target)) < 0.005:
                    response_time = time.perf_counter()
                    latencies.append(response_time - cmd_time)
                    break

        return {
            "mean_ms": np.mean(latencies) * 1000,
            "std_ms": np.std(latencies) * 1000,
            "p99_ms": np.percentile(latencies, 99) * 1000,
        }

    def measure_camera_latency(self, num_trials=100):
        """测量相机从触发到图像可读的延迟"""
        latencies = []

        for _ in range(num_trials):
            trigger_time = time.perf_counter()
            frame = self.camera.capture()
            receive_time = time.perf_counter()

            # 某些相机在帧元数据中携带硬件时间戳
            if hasattr(frame, 'hardware_timestamp'):
                hw_time = frame.hardware_timestamp
                latencies.append(receive_time - hw_time)

        return {
            "mean_ms": np.mean(latencies) * 1000,
            "std_ms": np.std(latencies) * 1000,
        }

    def generate_sync_report(self):
        """生成各信号通道的同步报告"""
        action_lat = self.measure_action_latency()
        cam_lat = self.measure_camera_latency()

        report = f"""
        === 信号延迟报告 ===
        动作下发延迟: {action_lat['mean_ms']:.1f} ± {action_lat['std_ms']:.1f} ms
        相机采集延迟: {cam_lat['mean_ms']:.1f} ± {cam_lat['std_ms']:.1f} ms
        时间错位: {abs(action_lat['mean_ms'] - cam_lat['mean_ms']):.1f} ms

        建议:
        - 仿真控制周期设为 {max(action_lat['mean_ms'], cam_lat['mean_ms']) / 1000:.3f} s
        - 观测缓冲中需补偿 {cam_lat['mean_ms']:.0f} ms 的图像延迟
        """
        return report
```

在测量得到各通道的延迟特性后,可以在仿真中通过两种方式补偿这些延迟。第一种方式是直接在仿真环境中模拟延迟:在每次策略接收观测之前,故意使用 N 步前的旧图像而非当前帧,或者在动作执行后等待若干毫秒才更新环境状态。第二种方式是在策略训练时保持仿真零延迟,但在真机部署时通过观测缓冲和动作预测来补偿延迟——例如维护一个时间戳对齐的观测历史窗口,将图像帧与其实际采集时刻的关节状态匹配后再输入策略。两种方式的选型取决于任务对延迟的敏感程度:需要一定精度的装配任务通常使用第二种就足够,而高动态的抛掷或翻转任务则强烈建议使用第一种,让策略在训练时就适应延迟的存在。如果是准静态的 pick and place 任务，训练的时候添加的噪声已经足够覆盖延迟问题。

## 缩小 Reality Gap 的方法论概述

域随机化(Domain Randomization)是 Sim2Real 迁移中使用最广泛的基础方法。其核心思想是在仿真训练过程中,对仿真环境的关键参数施加随机扰动,使策略被迫学会忽略那些在仿真和真实之间不一致的特征,转而依赖真正具有因果关系的物理规律。具体的随机化对象包括:物体的质量、摩擦系数和恢复系数;关节的阻尼和力矩常数;工作空间中光照的色温、亮度和方向;相机的位置偏移和图像噪声水平;以及物体初始位姿的分布范围。通过足够广泛的随机化分布,策略在仿真中见过的状态分布将覆盖真机部署时可能遇到的情况,从而提高迁移的鲁棒性。在实际实验中一般是添加高斯噪声进行域随机化，通过调整方差和期望来进行噪声大小的调整。

域随机化的工程实践中有几个重要的权衡。随机化范围过窄,策略仍可能对仿真特有的特征产生过拟合;随机化范围过宽,策略学习的难度急剧上升,甚至可能无法在合理时间内收敛到可接受的成功率。因此,通常采用渐进式随机化的策略:初始阶段使用较小的随机化范围使策略快速学会基本技能,然后逐步扩大随机化范围直到覆盖真机环境中的全部变化。以下是域随机化配置的一个典型实现:

```python
class DomainRandomizer:
    """仿真环境的域随机化配置"""

    def __init__(self, difficulty="medium"):
        # 根据训练阶段调整随机化强度
        self.ranges = {
            "easy": {
                "object_mass_scale": (0.9, 1.1),
                "friction_coef": (0.4, 0.8),
                "joint_damping_scale": (0.95, 1.05),
                "light_temp_kelvin": (4500, 5500),
                "camera_noise_std": (0.0, 0.01),
            },
            "medium": {
                "object_mass_scale": (0.7, 1.5),
                "friction_coef": (0.2, 1.2),
                "joint_damping_scale": (0.8, 1.2),
                "light_temp_kelvin": (3000, 7000),
                "camera_noise_std": (0.0, 0.05),
            },
            "hard": {
                "object_mass_scale": (0.5, 2.0),
                "friction_coef": (0.05, 1.5),
                "joint_damping_scale": (0.5, 1.5),
                "light_temp_kelvin": (2500, 9000),
                "camera_noise_std": (0.0, 0.10),
            },
        }

    def randomize_episode(self, sim_env, difficulty=None):
        """在每个 episode 开始前对仿真环境进行随机化"""
        ranges = self.ranges[difficulty or "medium"]

        # 随机化物理参数
        for obj in sim_env.get_manipulatable_objects():
            scale = np.random.uniform(*ranges["object_mass_scale"])
            obj.set_mass(obj.nominal_mass * scale)

            friction = np.random.uniform(*ranges["friction_coef"])
            obj.set_friction(friction)

        # 随机化机器人动力学
        for joint in sim_env.robot.get_joints():
            damping_scale = np.random.uniform(*ranges["joint_damping_scale"])
            joint.set_damping(joint.nominal_damping * damping_scale)

        # 随机化光照
        sim_env.set_light_temperature(
            np.random.uniform(*ranges["light_temp_kelvin"])
        )

        # 随机化相机位姿(微小扰动)
        for cam in sim_env.get_cameras():
            pos_noise = np.random.normal(0, 0.005, size=3)
            rot_noise = np.random.normal(0, 0.02, size=3)
            cam.set_pose(cam.nominal_pose + pos_noise, cam.nominal_rot + rot_noise)

            # 添加传感器噪声
            noise_std = np.random.uniform(*ranges["camera_noise_std"])
            cam.set_noise(gaussian_std=noise_std)
```

系统辨识(System Identification)是域随机化的互补方法,它试图从真机的少量交互数据中估计出仿真环境的关键物理参数,从而使仿真更贴近特定真机的动力学特性。例如,通过让真机执行一组预定义的运动轨迹并记录关节扭矩和角速度,可以拟合出每个关节的实际摩擦力模型参数;通过推拉桌面上的物体并记录位移,可以估计出物体与桌面之间的实际摩擦系数。这些辨识出的参数被直接写入仿真环境的配置中,让仿真更精确地模拟目标真机的行为。系统辨识的优点在于它减少了对随机化覆盖范围的依赖,从而降低了训练难度;缺点则是辨识得到的参数仅对单一真机和单一任务环境有效,当更换硬件或环境时辨识过程需要重新执行。

少样本真机微调是在策略完成仿真训练后,利用极少量(通常 10 到 50 条)的真人演示数据或自主采集轨迹对策略参数进行进一步优化。微调阶段的目的是让策略快速适应仿真和真实之间的残差,而不是从零开始学习任务。实践中最常用的微调策略包括:冻结视觉编码器,仅对策略网络的最后几层进行参数更新,以保留仿真阶段学到的视觉表征同时适应真机的动作分布;使用极低的学习率(通常比仿真训练阶段低一到两个数量级)进行少量的参数更新,避免灾难性遗忘;以及在微调过程中混合一定比例的仿真数据 replay,防止策略过度适应微调数据的有限多样性。

Teacher-student 特权学习是另一种具有代表性的 Sim2Real 方法。其思路是在仿真中训练一个 teacher 策略,该 teacher 可以访问真机无法获得的特权信息——例如物体的精确位姿、接触力、全局坐标等——因此能够在仿真中达到极高的成功率。然后,训练一个 student 策略,该策略仅能访问真机上可获得的传感器信息(如 RGB 图像和关节状态),但通过模仿 teacher 的行为或蒸馏 teacher 的决策分布,间接学习到完成任务所需的能力。由于 student 从未直接依赖特权信息,在迁移到真机时不会因为缺少这些信息而失效。

以上方法的详细选型分析与 RL 视角下的实现细节,请参阅 [Sim-to-Real RL](../09-reinforcement-learning-for-robotics/06-sim2real-rl.md) 章节,那里对域随机化的粒度控制、系统辨识的在线更新策略、以及 teacher-student 架构在强化学习框架中的具体实现做了更系统的展开。

## 真机上线前的安全门控

无论 Sim2Real 迁移方法多么精巧,策略在真机上首次运行时总是存在失败甚至发生危险的可能。因此在正式部署前,需要设置一系列安全门控条件,确保策略在不安全行为发生时能够被立即终止。

最基本的安全门控包括:关节速度和力矩的硬限幅,即使策略输出了超出安全范围的动作,底层控制器也会将其截断到安全包络内;机械臂末端运动范围的几何围栏,当末端接近工作空间边界或桌面上方的危险区域时自动触发降速或停止;以及碰撞检测阈值监控,当关节电流或力传感器读数超过正常操作范围时立即触发急停。这些门控的实现与策略本身解耦,运行在独立的监控线程中,不依赖于策略代码的正确性。

更高级的安全门控还包括策略行为的语义检查:例如在 pick-and-place 任务中,如果策略在未检测到物体抓取成功确认的情况下就试图向放置位置移动,系统将拦截该动作并暂停执行;在多步任务中,如果策略的连续动作序列在时序上不满足任务的自然约束(例如在没有先打开夹爪的情况下就试图抓取),也会被监控逻辑捕获。这些语义级的门控在本质上是对任务知识的硬编码,但它们为策略的自由探索提供了一个安全的护栏,使研究人员能够在大规模真机实验中放心地测试尚不完全成熟的策略。关于真机部署中 server-side 和 edge-side 的完整推理架构、通信协议以及状态流管理,请参阅本章的真机部署与推理章节。

综合来看,Sim2Real 与其说是一个技术问题,不如说是一个系统性工程问题。它要求从仿真环境搭建的第一天起,就将真机部署的需求作为设计的约束条件:观测和动作接口的规格、坐标系和时间的对齐方式、物理参数的变化范围、以及安全门控的触发条件——所有这些都在训练开始之前就需要被仔细规划和验证。只有当仿真和真机之间的接口被精确对齐,缩小 gap 的方法被合理选择和组合,真机上线前的安全检查被逐项落实之后,策略从仿真到现实的跨越才真正具备可靠的基础。
