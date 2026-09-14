# 实战案例：移动机器人导航

目标：用一个移动机器人导航实验把前面的概念串起来，知道 Gazebo、ROS 2、Nav2、传感器和模型文件分别在流程里做什么。

移动机器人导航是 Gazebo 最典型的使用场景之一。这个案例不追求一上来写完整命令，而是先把实验结构讲清楚。只要结构清楚，换 TurtleBot、差速小车、四轮底盘或者自己的机器人模型，本质流程都类似。

## 实验要完成什么

我们希望机器人在 Gazebo world 中完成一段导航任务：

```text
给定目标点
  -> ROS 2 导航栈规划路径并输出 /cmd_vel
  -> Gazebo 中的机器人执行速度命令
  -> lidar / odom / TF 反馈给 ROS 2
  -> 导航栈持续修正路径和速度
```

这看起来简单，但它同时依赖四类文件和工具：world、robot model、ROS launch / bridge、Nav2 配置。任何一块没接上，最后表现都可能是“机器人不动”或“机器人乱动”。

## 第一步：准备 world

world 决定机器人在哪个环境里跑。最小 world 可以只有地面和几个障碍物；复杂一些可以是办公室、走廊、仓库或真实扫描场景。对导航实验来说，world 至少要满足：

| 检查项 | 为什么重要 |
|---|---|
| 有地面 collision | 否则机器人可能掉落或接触异常 |
| 障碍物有 collision | 否则激光和碰撞结果不可信 |
| 空间尺度合理 | 机器人尺寸、走廊宽度、障碍间距要符合真实比例 |
| 光照不是核心依赖 | 如果只做 lidar 导航，不要让相机效果干扰判断 |

初学阶段建议用简单 world。不要一开始就上真实大场景。简单 world 更容易判断问题来自模型、bridge 还是导航参数。

## 第二步：准备机器人模型

移动机器人模型至少要包含底盘、轮子、碰撞体、惯量、传感器和驱动插件。一个常见结构是：

```text
mobile_robot
  ├─ base_link
  ├─ left_wheel_link / left_wheel_joint
  ├─ right_wheel_link / right_wheel_joint
  ├─ lidar_link / lidar sensor
  ├─ imu_link / imu sensor
  └─ DiffDrive plugin
```

如果只在 Gazebo GUI 里看到小车模型，并不能说明模型已经可用。要确认 DiffDrive 插件加载成功，左右轮 joint 名称正确，lidar sensor 正在发布数据，odom 或 joint state 能被外部读取。

## 第三步：连接 ROS 2

ROS 2 侧通常包括几个节点或模块：

| 模块 | 作用 |
|---|---|
| `robot_state_publisher` | 根据机器人描述和 joint state 发布 TF |
| `ros_gz_bridge` | 在 Gazebo 和 ROS 2 之间转换 topic |
| RViz | 查看模型、TF、激光、地图和导航目标 |
| Nav2 | 负责路径规划、局部避障和速度命令输出 |
| 可选 SLAM / localization | 建图或定位，根据任务选择 |

典型桥接关系是：ROS 2 的 `/cmd_vel` 发给 Gazebo，Gazebo 的 `/scan`、`/odom`、`/clock` 发回 ROS 2。具体 topic 名称取决于模型和 world，不能生搬硬套。

## 第四步：让 Nav2 闭环

Nav2 不是直接控制 Gazebo，它只看到 ROS 2 世界里的 topic。只要 ROS 2 侧的数据像真机一样可用，Nav2 并不关心底层是真机还是 Gazebo。

一个导航闭环至少需要：

| 数据 | 用途 |
|---|---|
| 地图或 SLAM 输出 | 全局规划需要环境信息 |
| `/scan` | 局部代价地图和避障使用 |
| `/odom` | 估计机器人局部运动 |
| `/tf` | 把 map、odom、base_link、laser 等坐标系连起来 |
| `/cmd_vel` | Nav2 输出给底盘的速度命令 |
| `/clock` | 仿真时间同步 |

如果你在 RViz 里设置了目标点，但机器人不动，先不要马上改 Nav2 参数。应该先确认 `/cmd_vel` 有没有输出；如果有输出，再看 Gazebo 侧是否收到；如果收到还不动，再查 DiffDrive 插件和模型关节。

## 实验记录应该写什么

Gazebo 导航实验的记录最好不要只截一张“机器人到了终点”的图。建议至少记录：

1. 使用的 Gazebo 版本、ROS 2 版本和 world 名称。
2. 机器人模型来源，是否修改了 URDF / SDF / xacro。
3. bridge 的 topic 列表和方向。
4. Nav2 的主要配置，例如地图、定位方式、局部规划器。
5. RViz 截图：TF、激光、地图、目标点和路径。
6. 失败情况：机器人不动、打滑、避障失败、TF 报错、时间戳异常等。

这样记录的好处是，下一次换 world、换传感器或上真机时，你知道是哪一层发生了变化。

## 常见问题

| 现象 | 优先检查 |
|---|---|
| Gazebo 里机器人能动，RViz 里不动 | `/odom`、`/tf`、bridge 和 `use_sim_time` |
| RViz 能看到激光，但导航不避障 | laser frame、costmap 配置、障碍物高度和 topic 名 |
| `/cmd_vel` 有输出，小车不动 | Gazebo 侧 topic、DiffDrive 插件、joint 名称 |
| 小车一直旋转 | 左右轮方向、轮距、里程计 frame、坐标轴 |
| TF 报未来或过去时间 | `/clock` 和 `use_sim_time` |

## 进一步阅读可以看：

- [Moving the robot](https://gazebosim.org/docs/latest/moving_robot/)
- [ROS 2 integration overview](https://gazebosim.org/docs/latest/ros2_overview/)
- [ROS 2 interoperability](https://gazebosim.org/docs/latest/ros2_interop/)