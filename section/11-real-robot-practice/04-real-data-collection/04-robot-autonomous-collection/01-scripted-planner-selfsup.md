
# 脚本、规划器与自监督采集

本页讲全自动采集:用确定性控制器/脚本、经典运动规划器或感知模块自动执行任务并记录数据,可大规模生成成功与失败轨迹,适合标准 pick-and-place、固定工位、自动 reset 的桌面任务,以及作为 bootstrapping 数据与人类示教混合。缺点:任务多样性依赖人工写规则、复杂接触/柔性/长程效果差、策略单一缺人类多样解法、perception 与 planner 本身要调。

# 脚本、规划器与自监督数据采集

在机器人数据采集的各类方案中,人工遥操作虽然能够提供高质量的专家演示,但每条轨迹都需要操作员全程参与,时间和人力成本随数据规模线性增长。当任务场景相对固定、操作对象形状规则、环境可控性较高时,完全可以在无人干预的情况下,由机器人自主完成任务执行与数据记录,从而以极低的边际成本生成大规模训练数据。这类方法的核心思路是利用已有的确定性程序——无论是手工编写的规则脚本、经典运动规划器,还是基于视觉的感知-规划闭环来自动化地驱动机械臂执行任务,并在执行过程中同步记录观测、状态和动作序列。

与人类遥操作相比,自主采集最显著的优势在于吞吐量。一台机械臂可以在夜间或周末连续运行,以固定的节拍反复执行同一任务,单日即可产出数百甚至上千条轨迹。更重要的是,自主采集不仅能生成成功轨迹,还能系统性地记录失败案例——包括抓取失败、碰撞触发、物体滑落等边界情况——这些数据对于训练鲁棒的闭环策略具有独特价值。此外,由于执行策略是确定性的,每条轨迹的动作分布和时序特征高度一致,这使得数据具有较好的可控性和可复现性,便于后续的消融实验和系统性分析。

## 基于规则脚本的自主采集

最直接的自主采集方式是为特定任务编写一套确定性的控制脚本,按照预设的状态机逻辑依次执行感知、规划、执行和数据记录步骤。这类方法适用于操作对象位置相对固定、任务流程简单的场景,例如桌面上的标准 pick-and-place、定点搬运或零件排序等。

一个典型的脚本化采集流程如下:机械臂首先回到预定义的 home 位置,触发环境相机拍摄当前场景;然后调用物体位姿估计模块(例如基于 ArUco 标记、颜色分割或预训练的检测模型)获取目标物体的三维坐标;随后根据物体位姿计算抓取姿态,调用运动规划器生成无碰撞轨迹并执行抓取;最后将物体搬运至目标位置释放,完成单次任务循环。每一步执行的同时,系统持续记录图像帧、关节状态、末端位姿和夹爪指令,在任务完成后将整条轨迹打包写入数据集。

以下是一个基于 Python 伪代码的简化示例,展示了桌面 pick-and-place 任务的自主采集主循环:

```python
class ScriptedPickPlaceCollector:
    def __init__(self, robot, camera, planner, data_writer):
        self.robot = robot
        self.camera = camera
        self.planner = planner
        self.writer = data_writer
        self.home_joints = [0.0, -0.78, 0.0, -2.36, 0.0, 1.57, 0.78]

    def run_collection_loop(self, num_episodes: int):
        for ep in range(num_episodes):
            # 回到安全起始位姿
            self.robot.move_joints(self.home_joints, speed=0.5)
            self.robot.open_gripper()

            # 随机化物体初始位置(增大数据多样性)
            object_pose = self.randomize_object_pose()

            # 拍摄场景并定位物体
            rgb, depth = self.camera.capture()
            detected_pose = self.detect_object(rgb, depth)

            if detected_pose is None:
                continue  # 物体不可见,跳过本周期

            # 规划并执行抓取
            pre_grasp = self.compute_pre_grasp(detected_pose, offset_z=0.10)
            grasp = self.compute_grasp(detected_pose)

            self.writer.start_episode()
            success = self.execute_stage("approach", pre_grasp)
            success &= self.execute_stage("grasp", grasp)
            if success:
                self.robot.close_gripper()
                self.robot.move_linear(dz=0.10)  # 提起物体

                # 搬运至目标位置
                place_pose = self.get_place_pose(ep)
                success &= self.execute_stage("place_above", place_pose)
                success &= self.execute_stage("place", place_pose)

            self.robot.open_gripper()
            self.robot.move_linear(dz=0.10)
            self.robot.move_joints(self.home_joints)

            # 记录轨迹元信息
            self.writer.end_episode(tag="success" if success else "failure")
            self.log(f"Episode {ep}: {'SUCCESS' if success else 'FAILURE'}")

    def execute_stage(self, stage_name: str, target_pose):
        """执行单个运动阶段并沿途记录数据"""
        traj = self.planner.plan(self.robot.state(), target_pose)
        if traj is None:
            return False
        for waypoint in traj:
            self.robot.servo_to(waypoint)
            obs = self.camera.capture()
            state = self.robot.get_state()
            self.writer.add_step(
                observation=obs,
                state=state,
                action=waypoint,
                stage=stage_name
            )
        return True
```

在实际部署中,脚本化采集的成功率高度依赖于感知模块的鲁棒性。物体位姿估计是其中最脆弱的一环——光照变化、物体反光、背景杂乱或部分遮挡都可能导致检测失败或位姿偏差,进而引发抓取失败甚至碰撞。为了提高采集成功率,通常需要在脚本中加入多重安全检查和异常恢复逻辑:例如在执行抓取前检查末端是否到达预期位置误差范围内,在碰撞检测触发时自动撤回并重新规划,以及在连续失败若干次后暂停采集并发出告警。

另一个关键设计是环境 reset 的自动化。如果每次任务结束后都需要人工将物体归位,自主采集的吞吐量优势将大打折扣。常见的自动 reset 策略包括:利用机械臂自身将物体从目标位置拨回初始区域;通过振动盘或传送带循环供料;在容器底部设置斜面使物体自动滑回起始位置;或者使用气压吹送将轻质零件推回供料区。在理想情况下,整个采集流程从供料、执行到 reset 形成完整的闭环,从而实现数小时甚至数天的不间断运行。

## 基于运动规划器的自主采集

当任务涉及更复杂的操作轨迹或需要处理工作空间中的障碍物时,仅靠简单的规则脚本往往不足以可靠地完成任务。此时可以引入经典运动规划器作为动作生成的引擎,将任务分解为一系列目标位姿,交由规划器求解连接相邻目标的可行轨迹。常用的规划器包括基于采样的 RRT-Connect、PRM,以及基于优化的 STOMP、CHOMP 和 TrajOpt 等。

以标准 pick-and-place 任务为例,规划器驱动的采集流程与脚本方案的整体框架相似,但运动生成部分全部交给规划器处理。系统首先通过感知模块获取抓取和放置目标位姿,然后调用 RRT-Connect 规划从当前位置到预抓取位姿的无碰撞路径,接着执行一条直线笛卡尔运动逼近物体,闭合夹爪后再规划提起到放置目标上方的轨迹,最后执行放置并撤回。整个过程中,每次规划调用都在一个新的环境碰撞模型中完成,从而动态适应场景中的变化。

相比于脚本方案,基于规划器的采集能够更好地处理复杂工作空间中的避障需求。例如在 bin-picking 场景中,机械臂需要避开料箱壁和已抓取零件旁边的其他物体;在装配任务中,末端需要沿特定插入方向运动,同时避免与夹具或工件发生碰撞。规划器能够自动搜索满足这些约束的可行路径,从而大幅减少手工编写避障逻辑的工作量。

以下是一个使用规划器进行自主采集的示例,展示了 pick-and-place 任务中的核心规划-执行循环:

```python
class PlannerBasedCollector:
    def __init__(self, robot, planner, scene, camera, writer):
        self.robot = robot
        self.planner = planner          # 例如 OMPL RRT-Connect
        self.scene = scene              # 碰撞场景
        self.camera = camera
        self.writer = writer

    def plan_and_execute(self, target_pose, stage_name):
        """规划到目标位姿的无碰撞轨迹,执行并记录"""
        start_state = self.robot.get_state()
        self.scene.update_from_camera(self.camera.capture())

        # 调用规划器求解
        plan = self.planner.solve(
            start=start_state,
            goal=target_pose,
            scene=self.scene,
            allowed_time=2.0
        )

        if plan is None:
            return False, "planning_failed"

        # 轨迹平滑(短路径优化/速度规划)
        smoothed = self.planner.smooth(plan, iterations=50)

        # 执行并记录
        for waypoint in smoothed:
            result = self.robot.servo_to(waypoint)
            obs = self.camera.capture()
            state = self.robot.get_state()

            self.writer.add_step(
                observation=obs,
                state=state,
                action=waypoint,
                plan=plan,
                stage=stage_name
            )

            # 实时碰撞检测
            if result.collision_detected:
                return False, "collision"

        return True, "ok"
```

在实际大规模采集中,规划器的稳定性和实时性是主要的工程瓶颈。基于采样的规划器每次运行可能产生不同的路径,导致同一条任务的轨迹之间出现较大的动作分布差异——这虽然在一定程度上增加了数据多样性,但也可能引入低效的、绕远的甚至抖动明显的路径,降低数据集的质量。因此通常需要在后处理阶段对轨迹进行过滤,剔除耗时过长、关节速度波动过大或接近奇异的轨迹。另一方面,基于优化的规划器虽然能保证输出质量的稳定性,但求解时间更长,在大批量采集时可能成为吞吐量的制约因素。实践中常采用混合策略:对于常规运动,使用确定性插值直接生成轨迹;仅在遇到障碍或需要避障的阶段才调用完整规划器,从而在效率和质量之间取得平衡。

## 感知驱动的自监督采集

脚本和规划器方案的核心局限在于依赖人工预定义的任务逻辑——每一步需要做什么、在哪里抓取、往哪里放置,都需要工程师事先编写。当任务目标或场景布局频繁变化时,这些硬编码逻辑很快就会失效。感知驱动的自监督采集试图解决这一问题,让视觉模块承担更高层次的决策职责,使机器人能够根据当前观测自主判断下一步该做什么。

一个典型的感知驱动采集系统由三个核心模块组成:物体检测与位姿估计模块负责从图像中识别操作对象并输出其在三维空间中的位置和朝向;抓取生成模块根据物体位姿和点云几何信息,生成一组候选抓取姿态并对每个候选给出成功概率的评分;策略模块则负责编排任务的宏观流程——选择当前应该抓取哪个物体、放入哪个容器、是否需要先移动障碍物,以及判断任务是否已经完成。这三个模块协同工作,使机器人能够在不依赖手工规则的情况下,自主完成操作-记录的闭环。

在抓取生成方面,基于深度学习的抓取检测方法近年来取得了显著进展。以 Dex-Net 系列和 GG-CNN 为代表的方法能够在单张深度图或 RGB-D 图像上,以端到端的方式输出抓取质量热力图和对应的抓取姿态。这些模型可以预先在仿真环境或大规模合成数据上训练,然后直接部署到真实场景中使用。每次采集迭代中,系统拍摄当前场景的深度图,送入抓取检测网络,选取置信度最高的抓取姿态,执行抓取后验证是否成功,最后记录整条轨迹。如果抓取失败,系统可以自动调整相机视角或轻微扰动物体位置,然后重新尝试。

以下是一个基于视觉抓取模型的自监督采集框架的简化实现:

```python
class SelfSupervisedCollector:
    def __init__(self, robot, camera, grasp_model, writer, config):
        self.robot = robot
        self.camera = camera
        self.grasp_model = grasp_model  # 预训练的抓取检测网络
        self.writer = writer
        self.bin_bounds = config["bin_bounds"]

    def run(self, num_episodes):
        success_count = 0
        attempt = 0

        while success_count < num_episodes:
            attempt += 1

            # 随机选取一个料箱区域拍摄
            rgb, depth, cam_pose = self.camera.capture_viewpoint(
                self.sample_viewpoint()
            )

            # 推理抓取位姿
            grasps = self.grasp_model.predict(rgb, depth, cam_pose)
            grasps = self.filter_colliding_grasps(grasps)  # 滤除碰撞抓取
            grasps = self.rank_by_quality(grasps)          # 按质量分数排序

            if len(grasps) == 0:
                self.shuffle_bin()  # 无可用抓取,扰动物体
                continue

            # 选择最优抓取并执行
            best_grasp = grasps[0]
            self.writer.start_episode()

            success = self.execute_grasp_and_place(
                grasp_pose=best_grasp.pose,
                grasp_width=best_grasp.width,
                place_region=self.sample_place_region()
            )

            tag = "success" if success else "failure"
            self.writer.end_episode(tag=tag)
            self.update_statistics(tag)

            if success:
                success_count += 1

            # 自适应记录频率
            if attempt > 0 and attempt % 100 == 0:
                print(f"Attempts: {attempt}, "
                      f"Successes: {success_count}, "
                      f"Rate: {success_count / attempt:.2%}")
```

感知驱动方案的独特价值在于它能够生成大规模且多样化的数据。由于采集过程由模型自身的判断驱动,而非人类预设的固定步骤,每次执行产生的轨迹在运动模式、抓取策略和失败原因上天然具有差异。这种多样性对于训练能够泛化到未见场景的策略模型尤为重要。此外,自监督采集天然适合与自监督学习目标配合——例如利用抓取成功/失败信号作为弱标注,训练物体可抓取性的表征模型;或者利用时序信息构造对比学习正负样本对,为视觉编码器提供丰富的预训练信号。

值得注意的是,在自监督采集中,失败轨迹本身也是宝贵的数据资产。对于下游的策略学习而言,知道"什么样的动作会导致失败"与知道"什么样的动作能成功"几乎同等重要。因此通常建议保留全部采集轨迹(包括失败案例),并在数据元信息中添加成功/失败标签和失败原因分类,供训练阶段选择性使用。

## 环境自动 Reset 与任务随机化

在自主采集中,单次任务执行只是整个循环的一部分。要实现真正意义上的无人值守运行,环境 reset 的自动化是必不可少的一环。人工 reset 不仅消耗人力,还会引入等待延迟,使自主采集失去了连续性带来的吞吐量优势。

对于标准桌面 pick-and-place 任务,最简单的 reset 策略是由机械臂自身完成。任务结束后,机械臂将目标位姿记录为当前物体所在位置,释放夹爪后移动到物体侧面,以推动的方式将物体扫回初始供料区,或者利用末端自带的小刷子将桌面物体归拢到固定区域。对于需要精确初始位姿的任务(例如精密装配),reset 通常需要借助机械定位夹具:物体被放置在一个带有锥形导向槽的托盘中,机械臂在每次任务开始前通过预定义的运动将物体推入导向槽底部,从而确保每次的初始位姿具有亚毫米级的一致性。

对于涉及多个操作对象的任务,传送带或转盘供料是一种常用的循环供料方案。物体随传送带或转盘运动至操作工位,机械臂执行抓取和放置后,传送带继续转动将下一个物体送入工位,同时已放置的物体随传送带末端落入回收箱。这种方式将供料、执行和回收整合到单一的物理流水线中,大幅降低了软件层面的时序协调复杂度。

任务的随机化同样是自主采集中需要系统化处理的问题。如果每次采集中物体的初始位姿、光照条件和背景完全一致,采集得到的数据将严重缺乏多样性,训练出的策略模型也难以泛化到真实场景中的微小变化。因此,自主采集系统通常会在每次迭代中引入受控的随机扰动:物体的初始位置在料箱内随机采样(x,y)坐标和绕 z 轴的旋转角度;物体数量在预设范围内随机选取;光照通过调节 LED 灯带的亮度和色温产生变化;甚至在多物体场景中随机打乱物体的堆叠顺序。这些随机化参数在每轮循环开始时生成,并作为元信息记录在轨迹数据中,以便后续分析不同条件下策略的表现。

## Bootstrapping 与混合数据策略

自主采集生成的数据虽然规模庞大,但往往在动作的精细度、轨迹的自然性和策略的多样性上无法与人类专家演示相比。因此在实际工程中,自主采集数据通常被用作 bootstrapping 阶段的初始数据源,与少量高质量人类演示数据混合使用,以达到数据质量和规模之间的平衡。

这种混合策略的一种常见实践是:首先利用自主采集生成数百到数千条成功轨迹,训练一个初始策略模型;然后将该模型部署到真实环境中执行,收集模型在上述状态下遇到困难的典型失败案例;最后让人类操作员在这些关键状态上提供专家修正演示,形成针对性的人工补充数据。经过一轮或多轮这样的迭代,数据集的覆盖范围逐步从简单任务扩展到边界情况,策略性能也随之持续提升。

从数据配比的角度来看,自主采集与人工演示的混合比例取决于任务的复杂度和对动作精度的要求。对于标准 pick-and-place 类任务,自主采集数据通常可以占数据集的 80% 以上,仅需少量人工演示用于定义任务语义和调优动作风格;而对于需要精细力控或动态操作的任务,人工演示的比例需要显著提高。实践中建议从一个等比例混合的数据集开始训练,然后通过消融实验逐步调整配比,观察不同配比下策略的成功率和行为质量变化。

以下是一个混合数据训练的基本流程示意,展示如何将自主采集轨迹和人工演示轨迹统一加载并合并:

```python
def build_mixed_dataset(auto_data_dir, human_data_dir, mix_ratio=0.7):
    """混合自主采集数据与人工演示数据"""
    auto_trajs = load_trajectories(auto_data_dir)
    human_trajs = load_trajectories(human_data_dir)

    # 按比例采样
    n_mixed = int(len(auto_trajs) * mix_ratio / (1 - mix_ratio))
    n_human = min(len(human_trajs), n_mixed)

    sampled_auto = random.sample(auto_trajs, n_mixed)
    sampled_human = random.sample(human_trajs, n_human)

    # 统一标准化
    dataset = []
    for traj in sampled_auto + sampled_human:
        # 每步数据包含: 观测、动作、来源标签
        for step in traj:
            dataset.append({
                "observation": normalize_obs(step.observation),
                "action": normalize_action(step.action),
                "source": "auto" if traj in sampled_auto else "human",
                "episode_id": traj.episode_id,
                "success": traj.success
            })

    random.shuffle(dataset)
    return dataset
```

在数据元信息中保留 `source` 字段(标记数据来自自主采集还是人工演示)是一个重要的工程细节。这允许训练过程中对不同来源的数据施加不同的权重或不同的损失函数——例如对人工演示数据使用较高的行为克隆损失权重,而对自主采集的成功轨迹使用较小的权重,对失败轨迹则使用 value 函数或对比学习损失——从而更充分地利用每种数据的价值。

## 局限性与工程实践建议

尽管自主采集在成本和规模上具有明显优势,但在实践中仍面临若干重要的局限性。

1.任务多样性严重依赖人工规则的设计。无论是基于脚本、规划器还是感知模块,自主采集系统所能完成的任务类型最终受限于工程师预先编写的逻辑范围。引入新的操作对象或新的任务目标,通常需要重新编写对应的感知策略、抓取逻辑和 error recovery 模块,无法像人类操作员那样灵活适应。这一局限使得自主采集更适合标准化操作场景(工厂产线、实验室固定实验台),而在家庭服务、多品类物流分拣等高度非结构化场景中效果有限。

2.复杂接触和柔性任务表现不佳。自主系统缺乏人类对接触状态的精细感知和调节能力,在需要根据力反馈实时调整末端运动的场景中尤为明显。例如精细装配任务中需要根据插入阻力微调切入角度和推进力,而自主采集系统中的经典规划器难以处理这种实时力控闭环。类似地,柔性物体操作(折叠布料、理线、操作软管)中物体的形变难以预测,常规的基于刚体假设的规划方法几乎无法工作。

3.动作策略单一,缺乏人类自然行为中丰富的风格多样性。自主采集系统中的所有轨迹源自同一套确定性或随机化程序,虽然通过随机种子可以引入一定差异,但整体动作模式远不如不同人类操作员之间的自然差异丰富。这一特性导致仅用自主数据训练的策略在面对与训练分布偏离较大的场景时,缺乏适应性行为储备。

4.感知与规划模块本身需要大量调试。在实际部署中,为让感知模块稳定工作所需的环境光照、相机标定、背景控制和模型适配工作量往往远超预期。同样,规划器在特定机器人和特定工作空间中可能暴露出路径质量不稳定、接近奇异点时失败率升高、碰撞检测假阳性导致不必要的避障绕行等问题,这些都需要逐台机器、逐个场景地调参优化。

综合来看,脚本、规划器与自监督采集在具身智能数据获取的生态中扮演着"大规模基础设施"的角色——适合作为初始数据源为模型训练提供冷启动所需的样本量,适合承担重复性高、结构固定的任务的数据生产,也适合与人类遥操作数据配合构成分层的混合数据集。

对于刚搭建好真机实验环境的研究团队,建议的路径是:先使用遥操作采集约 50 到 100 条高质量人工演示,验证任务可行性和基础策略性能;然后在任务结构具有较高确定性，任务多为强结构化(如pick and place)的前提下,逐步引入自主采集系统,在实践中迭代优化感知和规划模块的鲁棒性,最终过渡到以自主采集为主、人工演示为辅的大规模数据生产模式。
