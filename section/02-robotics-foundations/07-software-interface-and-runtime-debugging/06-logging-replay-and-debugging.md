# 日志记录、回放与问题定位

机器人实验中最令人沮丧的体验之一，是看到机器人执行失败了，却无法解释为什么失败——动作是在哪一步偏离预期的、接触力在什么时候不够了、坐标偏移从哪个时刻开始累积的。没有足够的日志证据，每一次失败都是一次黑盒事件，策略迭代也只能凭感觉调整。

日志记录、回放与问题定位的目标，是让每一次实验都可以被完整复盘——从传感器观测到策略输出、从原始动作到转换后的控制命令、从控制器接收命令、开始执行到最终执行反馈，整个链路中每个环节的数据和时间戳都被保留下来，使失败分析从"猜测"变为"追溯"。

本节定义最小可复盘字段，介绍常用调试工具的使用视角，给出排查问题的标准顺序，并列举常见问题类型对应需要查找的日志证据。

## 最小可复盘字段

一次可复盘的机器人实验，日志中至少应包含以下字段。这些字段不要求记录所有传感器原始数据（如完整分辨率的图像），但要求记录足够判断每个环节是否正常的关键信号。

**Observation（观测）**：策略接收到的输入数据。应包含图像的时间戳和 frame_id（在资源受限情况下，至少应记录图像 Topic 的时间戳序列；若需要分析视觉失败原因，则通常需要保存压缩图像或原始图像数据）、关节状态（位置、速度、力矩）的完整数组、以及末端执行器状态（夹爪宽度/真空压力）。观测数据的记录时机应为策略推理之前，而非推理之后——因为推理延迟会使记录的观测与实际用于决策的观测之间产生偏差。

**Robot State（机器人状态）**：机器人的完整运动学和动力学状态。应包含所有关节的位置、速度和力矩，可以直接记录末端执行器位姿，也可以仅记录 joint_states，在离线分析时利用 TF 重建末端位姿，当前装载的末端工具类型，以及控制器的生命周期状态和 fault 标志。机器人状态通常以最高可用频率记录（跟随 joint_states 频率），因为后续分析可能需要查看状态在两次策略推理之间的变化趋势。

**Raw Action（原始动作）**：策略模型直接输出的动作向量，在进行任何 Adapter 转换之前记录。应包含完整的动作数值（关节增量或末端位姿增量），以及策略的推理时间戳和模型版本标识。Raw action 对分析策略行为至关重要——如果在 Adapter 转换后命令看起来"合理"但实际执行出错，可以通过对比 raw action 和 converted command 确定问题出在策略还是 Adapter。

**Converted Command（转换后的命令）**：Adapter 对 raw action 进行坐标变换、单位转换、裁剪和封装后，最终发送给控制器的命令。应包含转换后的完整命令字段、命令类型（joint_target / ee_pose / trajectory）、参考坐标系（frame_id）、以及转换过程中触发的任何裁剪或告警（如"关节 3 角度被裁剪到上限"）。

**Controller Feedback（控制器反馈）**：控制器返回的执行状态。应包含 Goal 是否被接受、执行过程中的跟踪误差序列、最终的 Result（error_code 和 error_string）、以及执行是否因 Aborted、Timeout 或 Preempted 而终止。控制器反馈是判断"命令发出后到底发生了什么"的最直接依据。

**Timestamp（时间戳）**：每条日志记录必须携带时间戳，且必须明确使用的是 wall time 还是 ROS time（sim time）。日志文件的首条记录和末条记录时间戳应覆盖实验的实际时间跨度，偏移不超过 1 秒。

**Frame ID（坐标系标识）**：所有包含位姿或位置的日志字段必须附带 frame_id，说明该数值所在的参考坐标系。仅有数值而没有 frame_id 的位姿记录在事后分析中几乎没有意义——无法确定这个位置是相对于 base_link、map 还是 camera_frame。

**Error Code（错误码）**：当执行出现异常时，记录系统级的错误码或 fault 码。错误码应采用统一的枚举定义（参考 2.6 节的执行结果状态字段），避免在不同模块中使用相同的数值表示不同的错误类型。

以下代码演示了一个最小日志记录器的实现，它在一次策略-执行循环中记录上述关键字段：

```python
import json
import time as wall_time
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from control_msgs.action import FollowJointTrajectory

class MinimalLogger(Node):
    def __init__(self, log_path='/tmp/experiment_log.jsonl'):
        super().__init__('minimal_logger')
        self.log_file = open(log_path, 'w')
        self.episode_data = []

    def log_step(self, observation_stamp, joint_state: JointState,
                 raw_action, converted_command, controller_feedback=None):
        record = {
            'wall_time': wall_time.time(),
            'ros_time': self.get_clock().now().nanoseconds / 1e9,
            'observation': {
                'timestamp': {
                    'sec': observation_stamp.sec,
                    'nanosec': observation_stamp.nanosec,
                },
                'joint_positions': list(joint_state.position),
                'joint_names': list(joint_state.name),
            },
            'raw_action': raw_action,
            'converted_command': {
                'joint_names': converted_command.joint_names,
                'positions': list(converted_command.points[0].positions),
                'time_from_start': converted_command.points[0].time_from_start,
            },
            'controller_feedback': controller_feedback,
            'controller_active': True,  # 从 controller_state Topic 读取
            'fault': None,
        }
        self.episode_data.append(record)
        self.log_file.write(json.dumps(record) + '\n')

    def close(self):
        self.log_file.close()
```

日志格式建议使用 JSONL（每行一个 JSON 对象），便于逐行解析和增量写入，也方便使用标准工具（如 jq、pandas）进行事后分析。

## 常用调试工具与使用视角

ROS / ROS 2 提供了一组命令行和可视化工具，各自覆盖调试链路中的不同环节。理解每个工具解决"什么问题"，比记住它的所有参数更重要。

**RViz（可视化）**用于检查空间信息是否正确——机器人模型是否按预期运动、TF 树是否正确、传感器数据（点云、图像）是否投射在正确的位置、末端工具是否与物体模型对齐。在使用 RViz 调试时，首先确认 Fixed Frame 设置正确（通常为 base_link 或 world），然后依次添加 RobotModel、TF、Camera、PointCloud2 等显示面板，逐一验证空间关系。如果机器人模型不动——检查 joint_states 是否在更新、RobotModel 是否配置了正确的 TF Prefix。如果点云飘在空中——检查点云的 frame_id 与 TF 树是否匹配。

**rosbag（记录与回放）**用于将一次实验的所有 Topic 数据保存到磁盘，然后以不同速度重复回放，配合不同的策略或参数进行离线调试。rosbag 的核心价值在于"一次采集，多次分析"——真机实验成本高，通过回放可以反复测试不同的 Adapter 参数、策略阈值和失败判定逻辑，而不需要重新运行机器人。rosbag 记录时应包含所有关键 Topic（观测、状态、命令、TF、控制器反馈），避免在复盘时发现所需 Topic 未被记录。回放时应设置 use_sim_time 为 true，并通过 rosbag play 的 --clock 选项发布 /clock。

以下代码演示了在 ROS 2 中使用 rosbag2 的 Python API 进行记录：

```python
from rosbag2_py import SequentialWriter, StorageOptions, RecordOptions
from rclpy.node import Node

class RosbagRecorder(Node):
    def __init__(self, bag_path='/tmp/experiment_bag'):
        super().__init__('rosbag_recorder')
        self.writer = SequentialWriter()

        storage_options = StorageOptions(
            uri=bag_path,
            storage_id='sqlite3',  # 或 'mcap'
        )
        record_options = RecordOptions()
        record_options.all = True  # 记录所有 Topic
        # 也可以指定 Topic 列表以减少存储：
        # record_options.topics = [
        #     '/joint_states', '/tf', '/tf_static',
        #     '/camera/image_raw', '/joint_trajectory_controller/state',
        # ]

        self.writer.open(storage_options, record_options)
        self.get_logger().info(f'Recording to {bag_path}')
```

**Topic Echo（字段查看）**用于快速查看某个 Topic 的最新消息内容。`ros2 topic echo <topic_name>` 打印每条消息的所有字段，适合确认消息是否包含预期数据、字段是否有值（非 NaN 或空数组）、时间戳是否合理。加上 `--once` 参数只看最新一条，适合快速检查；加上 `--field <field_name>` 只看特定字段，适合检查数值。

**Topic Hz（频率检查）**用于测量 Topic 的发布频率。`ros2 topic hz <topic_name>` 统计一段时间内的消息数量并计算平均频率、标准差和最小/最大间隔。用于确认传感器是否稳定输出、策略是否按预期频率推理、控制器反馈是否中断。频率不稳定（标准差大）通常意味着节点负载过高、网络拥塞或定时器配置错误。

**TF Tree（坐标树可视化）**用于检查 TF 树的拓扑结构。`ros2 run tf2_tools view_frames` 生成 PDF 显示所有 frame 的连接关系和发布者信息。用于确认 frame 是否存在、parent/child 关系是否正确、树是否连通无断链。还可用 `tf2_echo <source> <target>` 实时查看两个 frame 之间的变换数值和更新频率。

**Diagnostics（健康监控）**用于汇总各节点的运行健康状态。diagnostics Topic 以固定频率发布各节点的状态等级（OK / WARN / ERROR / STALE）和详细状态信息（如驱动器温度、通信延迟、电池电压），由 diagnostic_aggregator 汇总后供 RViz 或 dashboard 显示。在长时间运行的实验中，diagnostics 是发现硬件渐变故障（如温度逐渐升高、通信丢包率缓慢增加）的最有效手段。

## 排查问题的标准顺序

面对机器人行为异常时，按照"从存在到质量、从数据源到执行端"的顺序排查，可以避免在错误的方向上浪费大量时间。推荐的排查顺序如下：

**第一步：Topic 是否存在**。确认被怀疑出问题的模块对应的 Topic 是否可以被订阅到。使用 `ros2 topic list` 列出所有活跃 Topic，对比预期列表。如果 Topic 不存在，检查对应的节点是否启动、是否 crash、namespace 是否匹配。

**第二步：频率是否正常**。对于存在的 Topic，使用 `ros2 topic hz` 检查发布频率是否在预期范围内。频率为零说明发布者已挂起；频率大幅波动说明节点负载过重或存在资源竞争。

**第三步：时间戳是否合理**。使用 `ros2 topic echo` 抽取消息，检查 header.stamp 是否单调递增、是否与 wall time 合理对应（真机场景）、是否使用了正确的时间源（sim time vs wall time）。时间戳为 0（全零）是常见错误——通常是因为发布者未调用 node.get_clock().now() 而直接使用默认构造的 Time 消息。

**第四步：Frame 是否匹配**。对于涉及空间位置的消息，检查 frame_id 是否与下游消费者预期的坐标系一致。用 `tf2_echo` 验证消息中引用的 frame_id 能否在 TF 树中查询到变换。

**第五步：命令是否被控制器接受**。如果机器人不动，首先检查控制器是否在 active 生命周期状态，然后检查发送的 Goal 是否被 Accepted。如果 Goal 被 Rejected，检查控制器的日志输出以获取拒绝原因。

**第六步：Fault 是否被触发**。检查 diagnostics 和 controller_state 中是否有活跃的 fault 标志。常见 fault 包括驱动器过流、编码器通信中断、关节位置超限和紧急停止按钮被按下。

这个排查顺序的核心原则是：**先确认数据在流动，再确认数据的质量，最后确认数据被正确消费**。跳过前两步直接分析"为什么抓取失败"，很可能在数据根本没有到达策略节点的情况下浪费大量分析时间。

## 常见问题与对应的日志证据

以下是具身智能系统中高频出现的接口问题，以及定位这些问题需要查看的日志证据。

**机器人不动（No Motion）**。日志证据：检查 joint_states 是否持续更新、trajectory Goal 是否被 Accepted、controller_state 中 desired 和 actual 之间是否有差异、fault 标志是否被触发。如果 joint_states 更新但 actual 始终不变 → 控制器未激活或硬件 fault。如果 Goal 被 Rejected → 关节名称/顺序不匹配或位置超限。如果 desired 和 actual 都变化但机器人实际不动 → 仿真与真机状态不一致或远程操作/示教模式未切换。

**坐标漂移（Coordinate Drift）**。日志证据：检查 odom → base_link 变换的长期趋势（是否随时间累积偏移）、多次 TF lookup 同一时刻的结果是否一致（排除buffer 竞争条件）、重复发布者是否导致变换值在多个来源间跳变。坐标漂移通常源于里程计的累积误差或定位系统的跳变，而非 TF 机制本身的问题。

**抓取失败（Grasp Failure）**。日志证据：检查 raw action 中的抓取命令是否在正确的时间点发出（时间戳对齐）、converted command 中夹爪命令是否被裁剪（裁剪日志）、夹爪宽度反馈是否按预期变化、夹持力是否达到目标值（如果力未达标则可能为空抓或滑落）、以及执行结果的 failure_reason 字段。对比日志中的期望夹爪宽度与实际宽度的时间曲线，可以清晰看到夹爪是在物体表面闭合还是在空隙中闭合。

**控制超时（Control Timeout）**。日志证据：检查 trajectory Goal 的路径点时间戳是否合理（最后一个路径点的时间标记是否超过了 Action 的超时容忍值）、控制器日志中是否有"跟踪误差超限导致 abort"的记录、以及控制器 feedback 中 error 数组的趋势图——error 是否在轨迹末尾阶段突然增大而非收敛。

**传感器丢帧（Sensor Dropout）**。日志证据：检查目标 Topic 的频率是否突然下降或归零、消息时间戳之间的间隔是否突然变大、以及同一时间窗口内与其他 Topic 的时间戳对齐程度——如果所有 Topic 同时出现频率下降，则可能是系统级资源问题（CPU 或带宽）而非传感器硬件故障。

**TF 查询失败（TF Lookup Failure）**。日志证据：检查报错时刻附近 TF 树是否完整——通过 rosbag 回放到该时间点，运行 view_frames 检查 frame 是否存在和树是否连通；检查 TF buffer 缓存时长是否覆盖查询的时间戳范围；检查是否存在两个发布者以相同的 parent/child frame 发布冲突的变换。

## 本节小结

日志记录、回放与问题定位构成了具身智能系统调试的闭环。最小可复盘字段覆盖观测、状态、原始动作、转换命令、控制器反馈、时间戳、坐标系标识和错误码，确保实验的每个环节都有据可查。ROS 生态提供的 RViz、rosbag、topic echo/hz、TF tree 和 diagnostics 各司其职——RViz 看空间、rosbag 做回放、echo 看字段、hz 看频率、TF tree 看连通性、diagnostics 看健康。排查问题时遵循"Topic 是否存在 → 频率是否正常 → 时间戳是否合理 → Frame 是否匹配 → 命令是否被接受 → Fault 是否触发"的顺序，可以将黑盒式的失败变为可追溯的证据链。
