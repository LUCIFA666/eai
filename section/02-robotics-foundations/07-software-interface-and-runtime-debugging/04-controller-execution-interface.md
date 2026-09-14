# 控制器执行接口

策略输出的动作目标（关节角度、末端位姿、底盘速度）最终必须交给控制器执行。控制器执行接口是策略与硬件之间的最后一道桥梁——它接收来自上层（策略或规划器）的命令，在安全约束下驱动执行器完成动作，并持续回读执行状态和异常信息。如果这道接口的语义不对齐（策略发的是末端位姿但控制器只接受关节角度）、生命周期不对（控制器未激活就发送了命令）、或者反馈没有被正确读取（命令已执行但策略不知道结果），整个具身智能系统的控制闭环就无法建立。

本节介绍 ros2_control 框架下控制器执行接口的核心组件，说明不同类型的控制器接口差异，覆盖执行反馈的信号体系，并给出策略接入控制器前的检查清单。

## ros2_control 的核心角色

ros2_control 是 ROS 2 生态中广泛采用的控制框架，为机器人控制器和硬件接口提供统一抽象，但具体机器人也可能使用厂商自定义控制框架。它的核心设计思想是：将"机器人怎么被控制"与"机器人硬件怎么被驱动"解耦。上层控制器只关心"我要达到什么目标"，硬件接口只关心"如何发送电信号驱动电机"，ros2_control 在中间完成两者的桥接。

ros2_control 的核心组件包括：

**Hardware Interface（硬件接口）**负责与机器人执行器及其状态反馈接口通信，为控制器提供标准的 State Interface 与 Command Interface。它向上暴露标准的 state interface（读取关节位置、速度、力矩）和 command interface（写入关节位置、速度、力矩目标），向下则通过具体的通信协议（EtherCAT、CAN、串口或仿真 API）驱动硬件。对于策略而言，硬件接口是透明的——策略不直接与硬件接口交互，而是通过控制器间接控制。

**Controller Manager（控制器管理器）**负责加载、配置、启动和停止各个控制器。它是运行时调度控制器的中枢：在每一个控制周期中，Controller Manager 先通过硬件接口读取最新状态，然后依次调用所有已激活控制器的 update 方法，最后将各控制器输出的命令写入硬件接口。每个控制周期通常遵循 read → update → write 的执行流程：先读取硬件状态，再执行控制器更新，最后写回控制命令。Controller Manager 还管理控制器的生命周期状态切换。

**Controller Lifecycle（控制器生命周期）**是 ros2_control 引入的重要概念。每个控制器遵循标准的生命周期状态机：

```text
unconfigured → inactive → active → (inactive → unconfigured)
                     ↑        ↓
                   finalize (清理退出)
```

- **unconfigured**：控制器已加载但未配置，此时没有分配资源，不能接收命令。
- **inactive**：控制器已配置（参数加载、资源分配），但尚未开始执行控制循环。处于 inactive 时可以接收配置但不能执行命令。
- **active**：控制器正常运行，在每个控制周期中读取状态、计算输出、写入命令。只有 active 状态下才能接收和执行 Action 或 Topic 命令。
- **finalized**：控制器正在被清理和卸载。

生命周期状态是排查"命令发出但机器人不动"问题的首要检查点——控制器如果不在 active 状态，任何命令都会被静默忽略或返回拒绝。以下代码演示了在 ROS 2 launch 文件中加载并激活控制器的配置：

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessStart

def generate_launch_description():
    # Controller Manager
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=['robot_description',
                     'controller_config.yaml'],
    )

    # 在 Controller Manager 启动后加载并激活 joint_trajectory_controller
    load_controller = RegisterEventHandler(
        OnProcessStart(
            target_action=controller_manager,
            on_start=[
                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=[
                        'joint_trajectory_controller',
                        '--controller-manager', '/controller_manager',
                    ],
                ),
            ],
        )
    )

    return LaunchDescription([controller_manager, load_controller])
```

## 不同控制器的接口差异

不同类型的任务和机器人结构对应不同类型的控制器，它们的命令接口和反馈字段各有不同。理解这些差异有助于为策略选择合适的控制接口。

**Joint Trajectory Controller（关节轨迹控制器）**是机械臂控制中最常用的控制器类型。它通过 FollowJointTrajectory Action 接收一组带有时间戳的路径点（waypoint），在每个控制周期中根据当前时间和路径点进行插值，输出关节位置或速度命令。轨迹可以包含任意数量的路径点，控制器根据轨迹中的时间信息对参考轨迹进行采样，并输出对应时刻的关节命令。其命令和反馈接口如下：

```text
# Action Goal（命令输入）
trajectory:
  joint_names: [joint_1, joint_2, ..., joint_N]
  points:
    - positions: [q1, q2, ..., qN]
      velocities: [v1, v2, ..., vN]   # 可选
      time_from_start: {sec: 0, nanosec: 0}

# Action Feedback（执行反馈）
feedback:
  desired: {positions: [...], velocities: [...]}
  actual: {positions: [...], velocities: [...]}
  error: {positions: [...], velocities: [...]}  # desired - actual

# Action Result（执行结果）
result:
  error_code: 0  # 0 = SUCCESSFUL
  error_string: ""
```

以下是一个发送关节轨迹命令的 Python 代码示例：

```python
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory

class TrajectorySender(Node):
    def __init__(self):
        super().__init__('trajectory_sender')
        self.action_client = ActionClient(
            self, FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory'
        )

    def send_trajectory(self, joint_names, positions, duration_sec=3.0):
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory()
        goal.trajectory.joint_names = joint_names

        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start.sec = int(duration_sec)
        goal.trajectory.points.append(point)

        self.action_client.wait_for_server()
        send_goal_future = self.action_client.send_goal_async(
            goal,
            feedback_callback=self.feedback_callback
        )
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected')
            return
        self.get_logger().info('Goal accepted')
        goal_handle.get_result_async().add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        error = feedback_msg.feedback.error.positions
        self.get_logger().info(f'Tracking error: {error}')

    def result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Result: error_code={result.error_code}')
```

**Gripper Controller（夹爪控制器）**的接口相对简单，通常通过 Topic 接收位置或力命令，返回当前开合宽度和夹持力。部分夹爪控制器也提供 Action 接口以支持带确认的抓取-确认流程。

**Diff Drive Controller（差速驱动控制器）**用于轮式移动底盘，通过 Topic 接收线速度和角速度命令（geometry_msgs/Twist），通过里程计消息（nav_msgs/Odometry）反馈实际位姿和速度。它是移动操作中最基础的移动控制接口。

**Whole-Body Controller（全身控制器，WBC）**协调多关节、多任务约束，适用于人形机器人或移动操作平台。其命令接口通常是多任务目标的组合（末端位姿、质心位置、接触力分配等），反馈包含全身关节状态、接触力和任务跟踪误差。WBC 的接口复杂度远高于单关节控制器，通常需要专门的适配层将策略输出映射为 WBC 的输入格式。

## 执行反馈的信号体系

策略不能仅凭"已发送命令"就认为任务已完成，而必须根据控制器反馈判断命令是否被接受、执行是否正常、结果是否成功。FollowJointTrajectory Action 的反馈信号贯穿整个执行过程。

**Goal Accepted / Rejected**是执行反馈的第一道信号。如果 Goal 被 Rejected，说明控制器认为命令不可执行——可能原因包括关节名称不匹配、位置超限、轨迹时间戳不合理、或控制器不在 active 状态。策略收到 Rejected 后不应重发相同命令，而应检查命令合法性。

**Active**表示控制器正在执行轨迹。在 Active 期间，控制器以固定频率发送 Feedback 消息，包含期望位置（desired）、实际位置（actual）和跟踪误差（error = desired - actual）。跟踪误差是最核心的执行质量指标——如果误差持续增大，可能意味着负载过重、关节卡滞或控制器增益设置不当。

**Result**在轨迹执行完毕后返回，包含最终的执行结果判定。error_code 为 0 表示正常完成；非零值需结合 error_string 判断具体原因。

除正常执行路径外，Action 还支持以下非正常终止路径：

- **Aborted（中止）**：执行过程中发生错误，控制器主动中止轨迹。常见原因包括跟踪误差过大（超过容差阈值）、关节力矩超限、或硬件进入 fault 状态。
- **Preempted（抢占）**该状态在 ROS 1 中有，而 ROS 2 已经将其删除新 Goal 到达后，控制器可能取消当前 Goal 并开始执行新的 Goal，具体行为由控制器实现决定。这是正常的控制行为——策略可以随时发送新轨迹替换旧轨迹，但策略应意识到旧轨迹的 Result 将是 Preempted。
- **Timeout（超时）**：轨迹执行时间超过了 Action 的目标完成时间（goal_time_tolerance），控制器判定轨迹无法在规定时间内完成。

以下代码演示了如何订阅控制器状态 Topic 来监控控制器健康状况：

```python
from control_msgs.msg import JointTrajectoryControllerState
from rclpy.node import Node

class ControllerStateMonitor(Node):
    def __init__(self):
        super().__init__('controller_state_monitor')
        self.subscription = self.create_subscription(
            JointTrajectoryControllerState,
            '/joint_trajectory_controller/state',
            self.state_callback,
            10,
        )

    def state_callback(self, msg: JointTrajectoryControllerState):
        # 检查跟踪误差
        if msg.error.positions:
            max_error = max(abs(e) for e in msg.error.positions)
            if max_error > 0.05:  # 超过 0.05 rad
                self.get_logger().warn(
                    f'Large tracking error: {max_error:.4f} rad'
                )

        # 检查是否达到目标
        if msg.error.positions:
            total_error = sum(abs(e) for e in msg.error.positions)
            if total_error < 0.01:
                self.get_logger().info('On target')
```

## 策略接入控制器前的检查清单

在策略向控制器发送第一条命令之前，以下检查项必须逐一通过，否则系统可能在运行中因接口不匹配而出现难以排查的错误：

**关节名称和顺序**。策略输出的关节数组顺序必须与控制器的 joint_names 顺序完全一致。不同机器人平台对同一类型关节的命名可能不同（例如有的用 "shoulder_pan_joint" 有的用 "joint_1"），数组位置与名称之间的映射应以控制器端定义的名称列表为准。建议在 Adapter 节点中使用名称索引而非位置索引来封装命令。

**控制模式**。控制器当前激活的控制模式（position / velocity / effort）必须与策略输出的命令类型匹配。例如策略输出速度命令但控制器处于 position 模式时，速度值会被错误地解释为位置值。控制模式通常通过控制器的配置文件（YAML）设定，运行中可通过 Service 切换。

**控制频率**。控制器的 update rate（一般为几十到上千 Hz，具体取决于机器人硬件和控制器实现）决定了它能多快地响应命令变化。策略的推理频率（通常在 10～50 Hz）远低于控制频率，因此中间需要插值或保持机制。如果策略以 10 Hz 发送新的轨迹 Goal 而控制器以 500 Hz 更新，高频的 Goal 替换可能导致运动抖动。

**关节限位**。策略输出的目标位置必须在控制器端配置的关节限位（soft limit）范围内。超出限位的命令会被控制器拒绝（Goal Rejected）或裁剪到限位边界，后者意味着实际执行的位置与策略预期不一致。

**控制器启动状态**。发送命令前必须确认控制器处于 active 生命周期状态。可以通过查询 controller_manager 的 Service 或检查 /controller_state Topic 中是否定期有数据更新来判断。

**Fault 状态**。发送命令前应检查硬件接口是否有活跃的 fault 状态。如果硬件已进入 fault（如驱动过流、编码器断线），控制器可能仍在 active 状态但物理上无法驱动电机——此时任何命令都不会产生实际运动。

以下代码演示了在发送命令前执行基本检查的 Adapter 逻辑：

```python
class CommandAdapter(Node):
    def __init__(self):
        super().__init__('command_adapter')
        self.controller_active = False
        self.hardware_fault = False

        # 订阅控制器状态
        self.create_subscription(
            JointTrajectoryControllerState,
            '/joint_trajectory_controller/state',
            self.controller_state_cb, 10)

    def controller_state_cb(self, msg):
        # 有正常的数据更新即说明控制器处于 active
        self.controller_active = True

    def send_command_if_ready(self, joint_names, positions):
        if not self.controller_active:
            self.get_logger().warn('Controller not active, command held')
            return False
        if self.hardware_fault:
            self.get_logger().error('Hardware in fault, command blocked')
            return False
        # 检查关节限位
        for name, pos in zip(joint_names, positions):
            if pos < self.limits[name]['lower'] or \
               pos > self.limits[name]['upper']:
                self.get_logger().error(
                    f'Joint {name} position {pos} out of limit'
                )
                return False
        # 通过检查，发送命令
        self.send_trajectory(joint_names, positions)
        return True
```

## 本节小结

控制器执行接口是策略意图转化为物理运动的最后一环。ros2_control 框架通过分离硬件接口、控制器管理器和生命周期管理，将"控制什么"与"如何驱动硬件"解耦。不同类型控制器（关节轨迹、夹爪、差速驱动、全身控制）的命令接口和反馈字段各有不同，策略必须根据实际控制器的接口语义封装命令。执行反馈信号（Goal Accepted/Rejected、Active、Feedback、Result、Aborted、Preempted、Timeout）构成了策略判断命令执行状态的信息依据。策略接入控制器前，必须逐一检查关节名称/顺序、控制模式、频率、限位、启动状态和 fault 状态——这六个检查点覆盖了绝大多数"命令发出但机器人不动"的根因。
