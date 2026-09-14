# Gazebo 学习路线

目标：给初学者一条不容易走乱的学习路线，从最小 world 开始，逐步走到机器人模型、传感器、ROS bridge 和导航实验。

Gazebo 学习最怕一开始就复制一个复杂工程。复杂工程里有 world、model、mesh、plugin、launch、bridge、Nav2、RViz、参数文件和脚本，出错以后很难判断是哪一层。更稳的路线是先把每一层单独跑通，再组合起来。

## 第一步：先分清版本

先确认自己学的是新版 Gazebo 还是 Gazebo Classic。新版 Gazebo 常见命令是 `gz sim`、`gz topic`、`gz service`，ROS 2 集成常见包是 `ros_gz`。Classic 教程里常见 `gazebo`、`gazebo_ros`、`gazebo_plugins`。

如果版本线没分清，后面复制插件、命令和 launch 文件时会非常痛苦。建议新项目优先按新版 Gazebo 官方文档学习。

## 第二步：跑一个最小 world

先不要放机器人。只运行一个简单 world，例如几何体、地面和光源。目标是确认：

- Gazebo 能启动。
- GUI 能看到场景。
- 可以暂停、播放、切换视角。
- 能理解 world 文件里模型、灯光和物理参数在哪里。

这一步的意义是建立“world 是什么”的直觉。不要一上来就把所有问题都和 ROS 混在一起。

## 第三步：读懂一个 robot model

找一个简单差速小车模型，先看它的结构：

```text
base_link
wheel links and joints
lidar or camera link
collision and inertial
control plugin
sensor plugin
```

重点不是模型有多漂亮，而是能不能回答几个问题：轮子 joint 叫什么？碰撞体在哪里？质量和惯量有没有写？雷达挂在哪个 frame 上？DiffDrive 插件听哪个 topic？

## 第四步：让机器人在 Gazebo 内部动起来

先不接 Nav2，只让机器人能在 Gazebo 中响应速度命令。可以用 Gazebo topic 或简单控制节点发送速度命令。目标是确认：

| 检查项 | 说明 |
|---|---|
| 插件加载成功 | 启动日志里没有明显报错 |
| topic 正确 | 命令发到了插件正在监听的话题 |
| 轮子方向正确 | 前进、后退、转弯符合预期 |
| odom 合理 | 位姿变化和肉眼看到的运动一致 |

这一步完成后，再接 ROS 才有意义。

## 第五步：加传感器

接下来加 lidar、camera、IMU 等传感器。初学时建议先从 lidar 和 IMU 开始，因为它们和移动机器人导航关系最直接。

传感器要检查三件事：

1. 模型里是否定义了传感器。
2. Gazebo 中是否有对应 topic。
3. 数据内容是否合理，例如 lidar 量程、频率、frame、障碍物距离。

如果传感器在 Gazebo 内部都没有数据，ROS 侧 bridge 再怎么配也不会有正确结果。

## 第六步：接入 ROS 2 bridge

这一步只做通信，不急着做导航。把 `/clock`、`/scan`、`/odom`、`/cmd_vel` 等关键话题 bridge 到 ROS 2，确认：

- `ros2 topic list` 能看到需要的话题。
- `ros2 topic echo` 能看到数据。
- 速度命令从 ROS 2 发出后，Gazebo 中机器人能动。
- ROS 2 节点使用 `use_sim_time=true`。
- RViz 能看到模型、TF 和传感器数据。

如果这一步不稳，后面 Nav2 报错很难排查。

## 第七步：再上导航

等 world、robot、sensor、bridge 都跑通，再接 Nav2。先用简单地图和简单障碍物，验证目标点导航、局部避障、路径显示和速度输出。成功以后再逐步换复杂 world、增加障碍、调规划器参数。

导航实验建议保留一张记录表：

| 项目 | 记录内容 |
|---|---|
| 环境 | Gazebo 版本、ROS 2 版本、world 名称 |
| 模型 | robot model 来源、改过哪些参数 |
| 传感器 | lidar / IMU / camera 的 topic 和 frame |
| bridge | 每条 bridge 的方向和消息类型 |
| 导航 | 地图、定位方式、planner、controller |
| 结果 | 是否到达目标、失败现象、截图或 rosbag |

## 推荐学习顺序

```text
Gazebo 版本线
  -> 最小 world
  -> robot model
  -> DiffDrive 或关节控制
  -> sensor simulation
  -> ros_gz bridge
  -> RViz 检查 TF 和话题
  -> Nav2 导航
  -> 更复杂 world 和真机迁移
```

这条路线看起来慢，但实际更快。因为每一层都能独立验证，出了问题知道该查哪里。

## 导航

- 上一页：[Gazebo 与其他仿真工具对比](08-comparison.md)
- 返回：[Gazebo](../04-gazebo.md)
- 下一页：[Gazebo 服务器最小运行流程](10-server-minimal-run.md)

## 进一步阅读可以看：

- [Gazebo documentation](https://gazebosim.org/docs/latest/)
- [SDF worlds](https://gazebosim.org/docs/latest/sdf_worlds/)
- [Moving the robot](https://gazebosim.org/docs/latest/moving_robot/)
- [Sensors](https://gazebosim.org/docs/latest/sensors/)
- [ROS 2 integration overview](https://gazebosim.org/docs/latest/ros2_overview/)
