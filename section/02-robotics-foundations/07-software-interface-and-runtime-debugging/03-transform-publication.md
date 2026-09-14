# 空间变换发布

在机器人系统中，"末端在哪里""相机看到了什么""物体在哪个坐标系下"这些问题都必须通过空间变换（Transform）来回答。与计算机视觉中通常只需要一个相机坐标系不同，机器人拥有数十个坐标系——底座（base_link）、各关节连杆（link_1～link_N）、末端工具（tool_frame）、相机（camera_frame）、激光雷达（lidar_frame）、世界（world）、里程计（odom）和地图（map）。这些坐标系之间的变换关系必须被持续发布和查询，才能使感知、规划和控制模块在同一空间参考下协作。

本节说明空间变换从模型文件到运行时发布的完整链路，区分静态变换和动态变换，介绍 TF buffer 的查询机制，最后给出常见 TF 问题的排查方法。

## 空间变换的发布链路

从 URDF / MJCF 模型文件到运行时可查询的 TF 树，需要经过一条标准的数据发布链路：robot_description 提供机器人运动学模型，joint_states 提供关节实时状态，robot_state_publisher 负责发布机器人运动学链上的 TF；其他坐标变换（如 map、odom、object 等）通常由定位、SLAM 或感知模块发布。

**robot_description** 是机器人运动学模型的文本描述，通常以 URDF 或 xacro 格式存储，在运行时作为 ROS Parameter 加载。它定义了机器人由哪些 link（连杆）组成、link 之间通过哪些 joint（关节）连接、每个 joint 的类型（revolute、prismatic、fixed 等）和运动范围（limit）、以及 link 之间的初始相对位姿（origin）。robot_description 是静态的——它描述的是机器人的结构，而不是机器人当前的状态。

**joint_states** 是实时数据流，由硬件驱动或仿真接口以固定频率（通常以几十到数百 Hz 发布，具体频率取决于机器人控制周期）发布到 /joint_states Topic。每条消息包含所有关节的名称、位置、速度和力矩。joint_states 的关节名称必须与 robot_description 中定义的关节名称完全一致，否则 robot_state_publisher 无法将其与运动学模型匹配。

**robot_state_publisher** 从 Parameter 获取 robot_description，并订阅 joint_states，根据关节的实际角度，通过正向运动学计算每个 link 在根坐标系（通常是 base_link）下的位姿，并将结果作为 TF 变换持续广播。robot_state_publisher 不负责运动规划或逆运动学，而是依据 URDF 描述的运动学链和 joint_states 计算各 link 的正向运动学结果，并发布对应 TF。

以下代码演示了在 ROS 2 中启动 robot_state_publisher 的典型方式：

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    robot_description = Command([
        'xacro ', PathJoinSubstitution([
            FindPackageShare('my_robot_description'),
            'urdf', 'my_robot.urdf.xacro'
        ])
    ])

    return LaunchDescription([
        # 将 URDF 加载为 Parameter
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description,
                         'use_sim_time': True}],
        ),
    ])
```

整个发布链路可以概括为：**结构（URDF）+ 状态（joint_states）→ 变换（TF）**。这个链路中任何一个环节断裂——URDF 未加载、joint_states 停发、关节名称不匹配——都会导致 TF 树不完整。

## 静态变换与动态变换

并非所有坐标变换都需要频繁更新。区分静态变换和动态变换，可以显著减少 TF 树的发布负载和带宽占用。

**静态变换（Static Transform）**描述两个坐标系之间固定不变的相对位姿，只在系统启动时发布一次。典型场景包括：相机在机械臂末端的安装位姿、激光雷达在底座上的固定位置、工具坐标系相对于末端法兰的偏移（TCP）、以及多传感器之间的标定外参。在 ROS 2 中，静态变换发布到 /tf_static Topic，/tf_static 默认采用 Transient Local Durability。订阅方通过 TF buffer 的 Transient Local Durability 可以在任意时刻获取，不受发布时间先后顺序的影响。

**动态变换（Dynamic Transform）**描述随关节运动而不断变化的坐标系关系，需要以固定频率持续发布。典型场景包括：机械臂各 link 之间的变换（随关节角度变化）、移动底盘的 odom → base_link 变换（随里程计更新）、以及物体跟踪结果（object_frame 随物体运动更新）。动态变换发布到 /tf Topic，查询时通常需要指定目标时间戳；若使用 Time()，则表示请求当前最新可用变换。

下表说明了各类 frame 应采用的发布方式：

| Frame 对 | 父 → 子 | 发布方式 | 更新频率 |
|---|---|---|---|
| base_link → link_1 → ... → link_N | 运动学链 | 动态，robot_state_publisher | 随 joint_states 频率 |
| link_N → tool_frame | 末端 TCP | 静态（通常） | 启动时一次 |
| tool_frame → camera_frame | 手眼标定 | 静态 | 启动时一次 |
| base_link → lidar_frame | 传感器底座 | 静态 | 启动时一次 |
| world → map | 全局定位 | 静态或低频动态 | 启动时或定位更新时 |
| map → odom | 定位漂移修正 | 低频动态 | 定位更新时（通常 1～10 Hz） |
| odom → base_link | 里程计 | 动态 | 轮式里程计频率（通常 50～200 Hz） |

以下代码演示了在 ROS 2 中发布静态变换：

```python
from geometry_msgs.msg import TransformStamped
import rclpy
from rclpy.node import Node
from tf2_ros import StaticTransformBroadcaster

class StaticTransformPublisher(Node):
    def __init__(self):
        super().__init__('static_tf_publisher')
        self.broadcaster = StaticTransformBroadcaster(self)

        # 发布 tool_frame 在 link_6 末端的固定偏移
        tool_transform = TransformStamped()
        tool_transform.header.stamp = self.get_clock().now().to_msg()
        tool_transform.header.frame_id = 'link_6'
        tool_transform.child_frame_id = 'tool_frame'
        tool_transform.transform.translation.x = 0.0
        tool_transform.transform.translation.y = 0.0
        tool_transform.transform.translation.z = 0.15  # 工具长 15 cm
        tool_transform.transform.rotation.w = 1.0  # 无旋转

        self.broadcaster.sendTransform([tool_transform])
```

对于大多数具身智能系统而言，静态变换数量通常不少于动态变换，因此合理区分二者能够减少不必要的通信开销，正确地将它们与动态变换分离，是构建可维护 TF 树的第一步。

## TF Buffer 与坐标查询

TF buffer 是坐标变换系统的核心数据结构。它接收并缓存一段时间内的所有 TF 消息，对外提供按时间戳查询任意两个 frame 之间相对位姿的能力。大多数应用模块不会直接处理 /tf Topic，而是通过 tf2 提供的 Buffer 与 TransformListener 接口查询所需变换。

TF buffer 的典型查询方式为：给定目标 frame、源 frame 和时间戳，返回源 frame 在目标 frame 下的位姿。时间戳参数尤为关键——当传入 Time() 时，表示查询当前最新可用的变换，这在静态场景中没问题，但在快速运动时可能导致不同传感器数据之间的坐标系对应关系错误。

以下代码演示了在 ROS 2 中使用 TF buffer 查询相机坐标系到 base_link 的变换：

```python
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
import rclpy
from rclpy.node import Node

class TransformLookupExample(Node):
    def __init__(self):
        super().__init__('tf_lookup_example')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(0.1, self.lookup_transform)

    def lookup_transform(self):
        try:
            # 查询 camera_frame 在 base_link 下的位姿（最新）
            transform = self.tf_buffer.lookup_transform(
                'base_link',           # target frame
                'camera_frame',        # source frame
                rclpy.time.Time(),     # 查询最新可用变换
                timeout=rclpy.duration.Duration(seconds=0.5)
            )
            self.get_logger().info(
                f'Camera in base_link: '
                f'x={transform.transform.translation.x:.3f}, '
                f'y={transform.transform.translation.y:.3f}, '
                f'z={transform.transform.translation.z:.3f}'
            )
        except Exception as e:
            self.get_logger().warn(f'Transform lookup failed: {e}')
```

TF buffer 的关键行为包括：按时间戳插值——当请求时间位于缓存区间内且不存在精确时间戳时，Buffer 会利用相邻变换进行插值；若超出缓存范围，则会抛出外推异常（ExtrapolationException）；时间窗口——buffer 只保留一定时长（默认 10 秒）内的变换历史，超时数据被自动清除；阻塞等待——可以指定 timeout 让 lookup 等待直到所需变换可用，适用于传感器数据到达时 TF 尚未就绪的情况。

## 常见 TF 问题与排查

TF 问题通常不会导致系统崩溃，但会导致感知结果偏移、抓取位置错误、规划失败或 RViz 显示异常。以下是具身智能系统中最常见的 TF 问题类型。

**Frame 不存在**：调用 lookup_transform 时请求的 frame 没有被任何发布者广播。排查方法——使用 `ros2 run tf2_tools view_frames` 生成当前 TF 树的可视化 PDF，检查目标 frame 是否在树中；或使用 `tf2_echo` 检查特定 frame 是否有数据。同时检查 frame 名称是否与发布端完全一致（包括大小写）。

**TF 树断开**：两个需要互查的 frame 之间缺少连通的变换链。例如 camera_frame 挂在 link_3 上，但 link_3 与 base_link 之间缺少某个 link 的变换发布。TF 查询只能在连通图中进行——如果两个 frame 不属于同一棵 TF 树，则无法完成坐标查询。排查方法——检查 `view_frames` 生成的树是否从根 frame 到所有叶子 frame 完全连通。

**时间戳过旧**：查询的历史时间戳超出了 TF buffer 的缓存窗口（默认 10 秒）。当使用 rosbag 回放数据时，如果回放速度与记录速度不一致、或者 use_sim_time 未正确设置，传感器时间戳与 TF 数据的时间戳可能错位。排查方法——检查 lookup_transform 是否指定了正确的时间戳，确认 /clock Topic 是否被正确发布且所有节点使用了 sim time。

**重复发布**：两个以上发布者以相同 parent/child frame 发布变换，导致 TF buffer 中的变换值在不同来源之间跳变。这在多个 robot_state_publisher 实例同时运行或静态变换发布者冲突时常见。排查方法——使用 `tf2_monitor` 查看每个 frame 的发布者信息。

**parent / child 反了**：发布变换时 frame_id 和 child_frame_id 填反，导致 TF 树方向错误。静态变换发布尤其容易出现此问题——视觉上很难察觉，但所有的坐标查询结果都会偏移一个固定的变换量。排查方法——在 RViz 中检查 TF 树箭头方向是否与预期一致。

**static transform 写错**：手眼标定、TCP 偏移或传感器安装位姿的静态变换数值录入错误。这类错误不会产生任何告警，但会导致所有依赖该变换的感知和操作结果系统性偏移。排查方法——通过 RViz 叠加显示点云和机器人模型，肉眼检查对齐情况。

## TF 最小检查清单

在调试空间变换相关问题时，按以下顺序检查通常能快速定位根因：

- 各 frame 是否已存在于 TF 树中（`ros2 run tf2_tools view_frames`）；
- TF 树从根到所有叶子是否连通（无断开的分支）；
- 查询时指定的时间戳是否在 TF buffer 缓存窗口内；
- base → tool → camera 之间能否互相查到变换；
- 静态变换的数值（平移和旋转）是否与实际安装一致；
- joint_states 中的关节名称是否与 URDF 定义完全匹配；
- robot_state_publisher 是否在运行且无报错。

## 本节小结

空间变换发布将机器人的静态结构和动态状态统一为可查询的 TF 树。发布链路由 robot_description（结构定义）、joint_states（实时状态）和 robot_state_publisher（正向运动学计算）三个环节串联构成。静态变换描述固定不变的安装关系（手眼标定、TCP 偏移），动态变换描述随关节运动而变化的连杆位姿。TF buffer 提供按时间戳的坐标查询能力，是感知、规划和控制模块获得空间参考信息的统一入口。常见 TF 问题的排查遵循"frame 是否存在 → 树是否连通 → 时间戳是否匹配 → 发布数值是否正确"的顺序，把握这条链路即可覆盖绝大多数空间变换调试场景。
