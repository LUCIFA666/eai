# ROS 与 Gazebo 通信机制

目标：理解 Gazebo Transport 和 ROS 2 是两套通信系统，知道为什么需要 `ros_gz` bridge，以及常见 topic 应该怎么接。

Gazebo 不是 ROS 2 的一个普通节点。新版 Gazebo 有自己的通信机制，叫 Gazebo Transport；ROS 2 也有自己的 topic、service、action 和参数系统。两边都能发布和订阅消息，但消息类型、命名空间和运行时并不是天然同一套。

所以 ROS 与 Gazebo 集成时，核心问题是：哪些数据留在 Gazebo 内部，哪些数据要桥接到 ROS 2？哪些命令从 ROS 2 发给 Gazebo，哪些状态从 Gazebo 发回 ROS 2？

## 三种常见集成方式

ROS 2 和 Gazebo 的集成分成几类，初学时可以记成三件事：

| 集成方式 | 解决什么问题 | 例子 |
|---|---|---|
| 用 ROS 2 launch 启动 Gazebo | 让仿真、bridge、机器人节点一起启动 | 一个 launch 文件启动 world、bridge、RViz |
| 用 `ros_gz` bridge 连接 topic | 让 ROS 2 节点和 Gazebo topic 交换消息 | `/cmd_vel`、`/scan`、`/odom`、`/clock` |
| 运行时从 ROS 2 spawn 模型 | 仿真启动后再插入机器人或物体 | 多机器人、动态场景、测试脚本 |

这三件事经常同时出现。比如一个移动机器人导航实验，会用 launch 启动 Gazebo world，用 bridge 转换传感器和控制话题，再在需要时把机器人模型 spawn 到 world 中。

## `ros_gz` bridge 是什么

`ros_gz` bridge 的作用是把 Gazebo Transport 消息转换成 ROS 2 消息，或者反过来。它不是简单地“转发字符串”，而是要知道两边的 topic 名、消息类型和方向。

一个 bridge 配置通常要回答四个问题：

| 问题 | 示例 |
|---|---|
| ROS 2 侧 topic 叫什么？ | `/cmd_vel` |
| Gazebo 侧 topic 叫什么？ | `/cmd_vel` 或 `/model/robot/cmd_vel` |
| ROS 2 消息类型是什么？ | `geometry_msgs/msg/Twist` |
| Gazebo 消息类型是什么？ | `gz.msgs.Twist` |

方向也很重要。速度命令通常是 ROS 2 到 Gazebo；激光、图像、里程计和仿真时间通常是 Gazebo 到 ROS 2。有些话题可以双向，但初学时建议先明确每条桥的方向，不要一上来就全部双向。

## 移动机器人常见 bridge

| 方向 | ROS 2 话题 | Gazebo 数据 | 用途 |
|---|---|---|---|
| ROS 2 -> Gazebo | `/cmd_vel` | `gz.msgs.Twist` | 导航栈或键盘控制输出速度命令 |
| Gazebo -> ROS 2 | `/scan` | lidar scan | 供 SLAM、定位、避障或 Nav2 使用 |
| Gazebo -> ROS 2 | `/odom` | odometry | 提供局部运动估计 |
| Gazebo -> ROS 2 | `/imu` | IMU data | 提供姿态、角速度、线加速度 |
| Gazebo -> ROS 2 | `/clock` | simulation clock | 让 ROS 节点使用仿真时间 |

这些名字不是硬规定。真实项目里 Gazebo 侧 topic 可能带有 world、model 或 sensor 前缀。写教程时最稳妥的做法不是假设所有机器人都叫 `/scan`，而是教读者先查：Gazebo 侧到底发布了什么，ROS 侧到底需要什么，再配置 bridge。

## `/clock` 和 `use_sim_time`

仿真里有一个很容易忽视的问题：时间。Gazebo 有仿真时间，ROS 2 节点默认可能使用系统时间。如果仿真暂停、加速、减速，而 ROS 节点还在用真实时间，日志、TF、传感器消息和导航行为都可能出问题。

因此，Gazebo 接 ROS 2 时通常要 bridge `/clock`，并让相关 ROS 2 节点设置 `use_sim_time=true`。这一步不显眼，但很关键。很多“TF extrapolation error”“消息时间戳不对”“RViz 显示异常”都和仿真时间没接好有关。

## TF 和 robot_state_publisher

TF 是机器人坐标系关系，不是 Gazebo 自动替你完全处理的一切。常见做法是：

1. 机器人描述文件定义 link 和 joint。
2. `robot_state_publisher` 根据机器人描述和 joint state 发布动态或静态 TF。
3. Gazebo 或 bridge 提供 joint state、odom、传感器数据。
4. RViz、Nav2、SLAM 等 ROS 节点依赖 TF 理解数据位置。

这也是为什么“Gazebo 画面里机器人在动”不等于“ROS 侧导航能用”。导航栈关心的是 ROS topic、TF 和时间是否一致。

## 排查顺序

ROS 和 Gazebo 通信出问题时，可以按下面顺序查：

1. Gazebo 侧是否真的有 topic：用 `gz topic` 查看。
2. ROS 侧是否真的有 topic：用 `ros2 topic list` 查看。
3. bridge 是否启动，topic 名和类型是否匹配。
4. 方向是否正确：命令要从 ROS 到 Gazebo，传感器通常从 Gazebo 到 ROS。
5. `/clock` 是否接入，ROS 节点是否设置 `use_sim_time`。
6. TF 是否完整，`base_link`、`odom`、`laser` 等 frame 是否连通。

只要按这个顺序查，大多数“Gazebo 和 ROS 连不上”的问题都能缩小范围。

## 进一步阅读可以看：

- [ROS 2 integration overview](https://gazebosim.org/docs/latest/ros2_overview/)
- [ROS 2 interoperability](https://gazebosim.org/docs/latest/ros2_interop/)