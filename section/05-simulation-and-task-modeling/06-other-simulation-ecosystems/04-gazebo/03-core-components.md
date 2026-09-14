# Gazebo 的核心组成

目标：把 Gazebo 中最常见的五个概念讲清楚：World 环境、Robot Model、Physics Engine、Sensor Simulation 和 ROS Interface。

第一次看 Gazebo 项目时，很多文件和概念会混在一起：`.sdf`、`.urdf`、`.xacro`、mesh、plugin、launch、bridge、Nav2、RViz、topic。可以先不要急着看具体文件，把 Gazebo 拆成五块：世界、机器人、物理、传感器、ROS 接口。

## World 环境

World 是仿真的外部世界。它可以包含地面、墙、桌子、障碍物、灯光、天空盒、重力、物理参数和全局插件。对于移动机器人，world 通常就是走廊、房间、仓库或简单障碍场；对于机械臂，world 可能是桌面、物体、托盘和夹具。

一个 world 不只是背景图，它会影响机器人能否运动、能否碰撞、传感器能看到什么。比如地面没有碰撞体，机器人可能直接掉下去；障碍物只有 visual 没有 collision，激光和碰撞都可能表现不符合预期；光源和材质不合理，相机图像也会受影响。

## Robot Model

Robot Model 描述机器人本体。它通常包括：

| 内容 | 说明 |
|---|---|
| link | 机器人刚体部件，例如底盘、轮子、机械臂连杆 |
| joint | link 之间的连接关系，例如转动关节、固定关节、轮子关节 |
| visual | 给人看的几何外观，常用 mesh 或简单几何体 |
| collision | 给物理引擎和传感器用的碰撞几何 |
| inertial | 质量、质心和转动惯量 |
| sensor | 相机、雷达、IMU、接触传感器等 |
| plugin | 控制器、差速驱动、传感器系统等运行逻辑 |

初学者最容易只关心 visual，觉得模型“看起来对”就行。Gazebo 中真正影响运动的是 collision、joint、inertial 和 plugin。一个外观看起来很漂亮的模型，如果惯量乱写、碰撞体过复杂、关节轴方向错了，运动结果仍然会很怪。

## Physics Engine

Physics Engine 负责更新世界状态：重力、碰撞、接触、关节约束、速度、加速度等都会在物理步进里处理。SDF world 中通常可以设置物理相关参数，例如步长、实时因子、重力和物理引擎类型。

这里有两个常见指标：

| 参数 | 含义 | 读实验时怎么理解 |
|---|---|---|
| `max_step_size` | 每个仿真步的时间间隔 | 越小越精细，但计算更重 |
| `real_time_factor` | 仿真时间相对真实时间的比例 | 1.0 附近表示仿真接近实时运行 |

如果机器人在仿真里抖动、穿模、飞走，不能只调控制器。还要检查碰撞体、惯量、关节限制、物理步长和接触参数。

## Sensor Simulation

传感器仿真负责从 Gazebo 世界生成观测数据。常见传感器包括 RGB camera、depth camera、lidar、IMU、contact sensor、GPS 等。传感器通常挂在某个 link 上，并设置 topic、update rate、噪声、视场角、分辨率、量程等参数。

例如 IMU 会输出姿态、角速度和线加速度；lidar 会根据场景几何返回距离扫描；contact sensor 会在发生接触时输出接触信息。传感器不是“自动存在”的，模型里必须定义它，相关系统也要加载，必要时还要把 Gazebo topic bridge 到 ROS topic。

## ROS Interface

Gazebo 自己有 Gazebo Transport，它的话题和服务不等同于 ROS 2 话题。ROS Interface 的核心工作就是把 Gazebo 世界和 ROS 机器人软件连接起来。新版 Gazebo 中最常见的工具是 `ros_gz`，它可以在 Gazebo Transport 和 ROS 2 之间转换消息类型。

典型桥接包括：

| 方向 | 示例 | 作用 |
|---|---|---|
| ROS 2 -> Gazebo | `/cmd_vel` | ROS 导航栈输出速度命令，Gazebo 中的驱动插件接收 |
| Gazebo -> ROS 2 | `/scan`、`/odom`、`/imu` | Gazebo 传感器和里程计输出给 ROS 节点 |
| Gazebo -> ROS 2 | `/clock` | 让 ROS 节点使用仿真时间 |
| Gazebo / ROS 2 | `/tf` | 维护机器人坐标系关系，具体来源取决于项目配置 |

## 五块之间的关系

```text
World 定义外部环境
  + Robot Model 定义机器人身体
  + Physics Engine 更新运动和接触
  + Sensor Simulation 生成观测
  + ROS Interface 把观测和命令接到 ROS 2
```

一个 Gazebo 项目出问题时，也可以按这五块排查：世界是不是加载了？模型是不是正确？物理是不是稳定？传感器有没有发布？ROS bridge 有没有连上？这样比盲目改参数更有效。

## 进一步阅读可以看：

- [SDF worlds](https://gazebosim.org/docs/latest/sdf_worlds/)
- [Sensors](https://gazebosim.org/docs/latest/sensors/)
- [ROS 2 integration overview](https://gazebosim.org/docs/latest/ros2_overview/)