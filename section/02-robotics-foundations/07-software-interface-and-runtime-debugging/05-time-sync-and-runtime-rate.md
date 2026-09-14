# 时间同步与运行频率

机器人系统中有多种"时钟"同时运转：墙上时钟（wall time）记录现实世界的时间流逝，ROS 时间（ROS time）由 /clock Topic 驱动可以加速或暂停，仿真时间（sim time）可能比真实时间快或慢数倍，每个传感器和控制器还有自己独立的硬件时间戳。当这些时间源不一致、频率不匹配或存在不可忽略的延迟时，就会出现 TF 查询失败、rosbag 回放错位、控制命令超时、感知与控制之间出现"时差"等难以直观定位的问题。

本节介绍机器人系统中的时间概念，区分各模块的运行频率及其不一致时的后果，分析端到端延迟的构成，并给出时间同步问题的最小检查项。

## 三种时间概念

**Wall Time（墙上时钟）**是操作系统提供的系统时间，通常对应真实世界时间，用于与外部环境保持一致的时间测量，不受仿真、回放或任何 ROS 设置影响。Wall time 用于记录实验的绝对时间戳、计算端到端延迟、以及驱动那些需要真实时间的操作（如文件写入时间、网络超时）。在纯真机部署中，ROS 时间通常直接跟随 wall time。

**ROS Time（ROS 时间）**是 ROS 生态中统一的时间标准，可以由 /clock Topic 驱动，也可以直接映射到 wall time（当 use_sim_time 为 false 时）。ROS time 的关键特性是它可以被外部控制——在仿真中由仿真器发布 /clock 来驱动时间推进；在 rosbag 回放中由 rosbag play 的 --clock 选项发布与记录时一致的时间戳。消息中的 header.stamp、TF 时间戳等通常采用 ROS Time；依赖节点时钟的超时判断（如部分 Action Server）也会随 use_sim_time 设置使用对应的时间源。

**Sim Time（仿真时间）**是 ROS time 的一种特殊模式（use_sim_time 设为 true）。在仿真中，仿真器每完成一个物理步就推进一次 sim time——如果仿真比实时慢（物理计算量大），sim time 会比 wall time 慢；如果仿真被暂停，sim time 也停止。Sim time 的机制使得控制器和传感器在仿真中看到的"时间"保持一致，即使真实 wall time 不均匀。

以下代码演示了在 ROS 2 节点中获取不同类型的时间戳：

```python
import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Time

class TimeExample(Node):
    def __init__(self):
        super().__init__('time_example')
        self.timer = self.create_timer(1.0, self.print_times)

    def print_times(self):
        # ROS 时间（跟随 /clock 或 wall time）
        ros_now = self.get_clock().now()
        self.get_logger().info(
            f'ROS time: {ros_now.nanoseconds / 1e9:.3f}'
        )

        # 检查是否使用 sim time
        self.get_logger().info(
            f'use_sim_time: {self.get_parameter("use_sim_time").value}'
        )
```

三种时间概念的使用原则如下：所有机器人数据（传感器消息、TF 变换、控制命令）的时间戳必须使用 ROS time；仅在与外部世界交互（记录日志的 wall time 字段、网络通信超时）时使用 wall time；真机部署时 use_sim_time 应为 false，仿真和 rosbag 回放时应为 true。

## 各模块的运行频率

机器人系统中不存在一个统一的"系统频率"，不同模块各有其周期。理解各模块的典型频率及其不一致时的表现，是排查系统行为异常的基础。

**Sensor Rate（传感器频率）**由硬件决定。常见传感器频率：关节编码器一般为几十到数千 Hz，具体取决于驱动器和控制系统、RGB 相机 30～60 Hz、深度相机 15～30 Hz、力/力矩传感器 100～1000 Hz、IMU 100～500 Hz、激光雷达 10～30 Hz。传感器频率差异意味着在同一时刻，关节位置的数据可能比图像数据"新"几十倍。

**State Rate（状态发布频率）**通常是传感器频率的下采样或组合。joint_states 的发布频率通常由驱动程序决定，可能与编码器采样频率一致，也可能经过降采样后发布；robot_state_publisher 的 TF 发布频率通常与 joint_states 保持一致；controller_state 通常以 10～50 Hz 发布。

**Control Rate（控制频率）**由控制器的 update rate 决定。典型值：关节位置控制器 500～2000 Hz（用于工业机器人）、力控/阻抗控制器 500～1000 Hz、移动底盘控制器 50～200 Hz。控制器的 update rate 直接影响轨迹跟踪精度——频率越高，插值越细密，跟踪越精确。控制器每个周期通常遵循 read → update → write 的流程；如果本周期没有新的状态数据，则继续使用最近一次读取到的状态。

**Policy Rate（策略频率）**由模型推理速度决定。VLA 模型通常 5～15 Hz（受大模型推理延迟限制），模仿学习策略通常 10～50 Hz（取决于模型大小和硬件），强化学习策略推理通常可以达到较高频率，具体取决于模型规模和硬件性能。Policy rate 远低于 control rate 是常态——策略负责宏观决策，控制器负责微观执行。

**Logging Rate（日志记录频率）**由 rosbag 或自定义 logger 的订阅和写入机制决定。日志通常以最高有效频率记录（即传感器的实际发布频率），但也可以配置为定时采样以节省存储。

频率不一致带来的后果取决于具体的失配组合：

- **策略频率远低于控制频率**（如 10 Hz vs 500 Hz）：控制器通常会保持最近一次目标，或依据控制器实现对轨迹进行采样和平滑处理，运动平滑但可能滞后于环境变化。
- **传感器频率低于控制频率**（如相机 30 Hz vs 控制 500 Hz）：视觉伺服的反馈带宽受限于相机帧率，对于高速运动场景，控制可能"看不清"当前状态。
- **传感器之间频率不一致**（关节 500 Hz vs 图像 30 Hz）：关节状态比视觉信息及时得多，将两者直接拼接为策略输入时，视觉信息"代表的是过去"。
- **日志频率低于传感器频率**：回放时丢失了高频细节，无法精确判断事件发生的时刻。

## 端到端延迟的构成

从传感器采集到数据到执行器产生响应，整个链路中存在多重延迟。理解延迟的构成有助于判断哪些延迟是可优化的，哪些是必须通过预测或补偿来容忍的。

端到端延迟的典型构成依次为：

**传感器采集延迟**：相机曝光和读出时间（通常 5～33 ms，取决于快门和帧率）、编码器采样和总线传输时间（通常 0.1～2 ms）。这部分延迟由硬件决定，一般不可优化。

**网络传输延迟**：传感器数据从采集节点通过 ROS 通信层传输到策略节点的时间。对于 Topic 通信，包括序列化、DDS 传输和反序列化。Composition 能够显著减少跨进程通信开销，从而降低消息传输延迟。

**模型推理延迟**：策略模型从接收到输入到输出动作的时间。VLA 模型由于参数量大，推理延迟可能是端到端延迟的最大组成部分（100～500 ms）；轻量模仿学习模型通常为 5～30 ms。推理延迟的波动（jitter）比绝对延迟对控制的影响更大——不稳定的推理时间导致动作间隔不均匀。

**Adapter 转换延迟**：将策略输出转换为控制器命令的时间，包括坐标变换（TF lookup）、单位转换、裁剪和命令封装。通常为亚毫秒级，但如果 TF lookup 需要等待变换到达，可能引入额外延迟。

**控制器执行延迟**：控制器接收到命令后，从命令到电机产生实际运动的时间。包括通信总线延迟（EtherCAT 约 0.1～1 ms）和控制器的内部处理延迟。这部分延迟通常很小且确定性强。

**日志写入延迟**：数据写入磁盘的时间。对于 rosbag，通常为非阻塞写入，延迟可忽略；但如果磁盘 IO 拥塞，可能影响整个系统的实时性。

以下代码演示了如何测量从策略输出到控制器接收的延迟：

```python
class LatencyMeasurer(Node):
    def __init__(self):
        super().__init__('latency_measurer')
        self.last_action_time = None

        # 策略输出时记录时间
        self.action_pub = self.create_publisher(
            JointTrajectory, '/trajectory_command', 10)

        # 控制器反馈时计算延迟
        self.create_subscription(
            JointTrajectoryControllerState,
            '/joint_trajectory_controller/state',
            self.feedback_cb, 10)

    def send_action(self, trajectory):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        # ... 填充 trajectory ...
        self.action_pub.publish(msg)

    def feedback_cb(self, msg):
        # 从反馈中获取 desired 的时间戳
        action_stamp = msg.header.stamp
        now = self.get_clock().now()
        latency = (now - action_stamp).nanoseconds / 1e6  # ms
        self.get_logger().info(f'Action-to-feedback latency: {latency:.1f} ms')
```

## 时间同步影响的关键任务

**视觉伺服（Visual Servoing）**对延迟最为敏感。视觉伺服将相机图像中的特征误差直接映射为末端速度命令，如果图像数据延迟过大，末端可能在"过去"的误差引导下运动，导致超调或振荡。因此视觉伺服通常要求端到端延迟在 30 ms 以内，且必须使用最新帧（丢弃积压的历史帧）。

**移动操作（Mobile Manipulation）**中底盘里程计与机械臂状态的时间对齐尤为关键。如果在底盘运动过程中机械臂需要抓取，odom → base_link 的变换时间戳与关节状态的时间戳必须对齐——否则末端在全局坐标系中的位置存在偏移。

**数据集回放（Dataset Replay）**依赖于 sim time 和时间戳的一致性。回放时必须设置 use_sim_time 为 true，由 rosbag 发布 /clock，所有节点的 ROS time 同步到记录的原始时间戳上。如果任何节点未使用 sim time，其时间戳将与其他节点不一致，导致 TF lookup 失败或消息被判定为过期。

**Sim-to-Real 迁移**中，仿真和真机的时间行为差异可能导致策略表现不同。仿真中物理步长固定且均匀，真机中传感器和控制频率存在 jitter；仿真中通常可以通过降低实时倍率或暂停仿真来弱化推理延迟的影响，而真机系统必须在真实时间约束下完成推理，因此两者的时间行为存在差异。这些时间行为差异应在迁移策略时被显式考虑。

**失败复盘（Failure Analysis）**依赖精确的时间戳对齐。当复盘一次失败的抓取实验时，需要沿着时间轴逐一确认：策略在何时输出了抓取命令 → 控制器在何时接收并执行 → 夹持力在何时开始上升 → 视觉系统在何时检测到物体滑落。如果各模块的时间戳不对齐，事件之间的因果关系就难以建立。

## 时间同步最小检查清单

在调试时间同步相关问题时，按以下顺序检查通常能快速定位根因：

- **时间戳是否单调递增**。检查同一 Topic 的消息时间戳是否单调递增且无跳变。时间戳回退会导致 TF 插值异常和 rosbag 回放错误。使用 `ros2 topic echo <topic>` 抽取连续消息的时间戳进行人工检查。

- **use_sim_time 是否一致**。使用 sim time 的场景（仿真、rosbag 回放）中，所有节点必须统一设置 use_sim_time 为 true。可以通过 `ros2 param get /<node_name> use_sim_time` 逐节点确认。

- **不同 Topic 的时间戳是否对齐**。在同一 wall time 时刻，camera/image_raw 的 header.stamp 与 joint_states 的 header.stamp 之间的差值即为感知与控制之间的时间偏差。使用 `ros2 topic echo` 同时对比两个 Topic 的最新时间戳。

- **TF 是否能按时间戳查询**。如果 TF buffer 缓存窗口（默认 10 秒）小于数据的时间跨度，旧时间戳的 TF 将无法查询。在 rosbag 回放中尤为常见——回放速度过快时，TF 数据被快速刷新出 buffer。

- **控制命令是否超时**。控制器的 Action Server 会对 Goal 设置目标完成时间（goal_time_tolerance），如果轨迹的路径点时间戳不合理（例如最后一个路径点的时间标记为一个不可能的时间），控制器可能立即返回 Timeout。

- **日志记录的时间戳与实际事件是否一致**。检查 rosbag 中记录的首条消息和末条消息时间戳是否覆盖了实验的真实时间跨度，确保日志未丢失开头或结尾的关键数据。

以下代码演示了如何监控多个 Topic 的时间戳对齐情况：

```python
class TimestampMonitor(Node):
    def __init__(self):
        super().__init__('timestamp_monitor')
        self.last_joint_stamp = None
        self.last_camera_stamp = None

        self.create_subscription(
            JointState, '/joint_states', self.joint_cb, 10)
        self.create_subscription(
            Image, '/camera/image_raw', self.camera_cb, 10)
        self.create_timer(1.0, self.check_alignment)

    def joint_cb(self, msg):
        self.last_joint_stamp = msg.header.stamp

    def camera_cb(self, msg):
        self.last_camera_stamp = msg.header.stamp

    def check_alignment(self):
        if self.last_joint_stamp and self.last_camera_stamp:
            joint_t = (self.last_joint_stamp.sec +
                       self.last_joint_stamp.nanosec * 1e-9)
            camera_t = (self.last_camera_stamp.sec +
                        self.last_camera_stamp.nanosec * 1e-9)
            diff_ms = abs(joint_t - camera_t) * 1000
            self.get_logger().info(
                f'Joint-Camera timestamp diff: {diff_ms:.1f} ms'
            )
            if diff_ms > 100:
                self.get_logger().warn(
                    'Large timestamp mismatch — '
                    'perception and control may be out of sync'
                )
```

## 本节小结

机器人系统中的时间同步与运行频率管理，本质上是确保"各模块看到的状态是同一时刻的真实状态"。"同一时刻"由 ROS time 维护——仿真和回放时通过 /clock 控制，真机部署时跟随 wall time。"真实状态"取决于各模块的频率匹配和延迟管理——传感器频率决定数据的新鲜度，控制频率决定执行的精度，策略频率决定决策的响应速度，三者之间的频率差异通过插值、保持和帧丢弃来弥合。时间同步问题的排查遵循"检查时间戳单调性 → 检查 use_sim_time → 检查 Topic 间时间戳对齐 → 检查 TF 可查询 → 检查命令超时"的顺序。理解这些概念并在 Adapter 和 Logger 中增加时间戳监控，可以在问题发生时快速定位是哪个环节的时间出了问题。
