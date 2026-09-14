# Gazebo

目标：理解 Gazebo 在机器人仿真链路中的定位，能分清 world、robot model、physics、sensor、plugin 和 ROS 2 bridge 分别负责什么，并能读懂一个移动机器人从 Gazebo 到 ROS 导航栈的基本流程。

Gazebo 最适合放在“机器人系统联调”这一层理解。它不是只用来渲染一个 3D 场景，也不是单纯的动力学引擎，而是把场景、机器人模型、物理、传感器、插件、话题通信和 ROS 集成放到同一套工作流里。很多移动机器人、无人车、服务机器人和 ROS 教学项目都会用 Gazebo 先跑通仿真，再逐步迁移到真机。

这里讲的是新版 Gazebo，也就是文档里常见的 `gz sim`、`gz topic`、`gz-transport`、`ros_gz` 这一套。Gazebo Classic 是旧版本，历史资料里大量出现 `gazebo_ros`、`gazebo_plugins`、`gazebo` 命令和 Classic 专用插件。读旧教程时要特别注意版本，不要把 Classic 的插件和新版 Gazebo 的插件直接混用。

## 学习路径

| 页面 | 这一页回答的问题 | 重点 |
|---|---|---|
| [为什么机器人需要 Gazebo 仿真](04-gazebo/01-why-gazebo.md) | 已经有真机了，为什么还要仿真？ | 成本、安全、可重复测试、ROS 系统联调 |
| [Gazebo 简介与整体架构](04-gazebo/02-overview-architecture.md) | Gazebo 到底由哪些层组成？ | server、GUI、ECS、plugin、Gazebo libraries |
| [Gazebo 的核心组成](04-gazebo/03-core-components.md) | world、model、physics、sensor、ROS interface 分别是什么？ | 五个核心概念及其关系 |
| [机器人模型描述：URDF 与 SDF](04-gazebo/04-urdf-and-sdf.md) | 什么时候用 URDF，什么时候用 SDF？ | ROS 描述、仿真描述、碰撞和惯量 |
| [Gazebo 中的机器人运动流程](04-gazebo/05-robot-motion-flow.md) | 一条速度命令如何让仿真机器人动起来？ | `cmd_vel`、DiffDrive、物理步进、传感器反馈 |
| [ROS 与 Gazebo 通信机制](04-gazebo/06-ros-gazebo-communication.md) | ROS 节点怎么和 Gazebo 交换消息？ | Gazebo Transport、`ros_gz` bridge、`/clock`、`/tf` |
| [实战案例：移动机器人导航](04-gazebo/07-mobile-robot-navigation.md) | 一个移动机器人导航仿真怎么组织？ | world、robot、lidar、odom、Nav2、记录检查 |
| [Gazebo 与其他仿真工具对比](04-gazebo/08-comparison.md) | 什么任务适合选 Gazebo，什么任务不适合？ | MuJoCo、Isaac Sim、Habitat、ManiSkill、Drake 对比 |
| [Gazebo 学习路线](04-gazebo/09-learning-path.md) | 新手怎么学不会乱？ | 最小 world、模型、传感器、ROS bridge、导航实验 |
| [Gazebo 服务器最小运行流程](04-gazebo/10-server-minimal-run.md) | 在服务器上怎么真实跑通 Gazebo？ | `gz-jetty`、server-only、SDF world、topic 验证、X11 GUI |

## 导航

- 上一页：[PyBullet](03-pybullet.md)
- 返回：[其他仿真生态](../06-other-simulation-ecosystems.md)
- 下一页：[为什么机器人需要 Gazebo 仿真](04-gazebo/01-why-gazebo.md)

## 进一步阅读可以看：

- [Gazebo documentation](https://gazebosim.org/docs/latest/)
- [Gazebo Sim architecture](https://gazebosim.org/docs/latest/architecture/)
- [ROS 2 integration overview](https://gazebosim.org/docs/latest/ros2_overview/)
- [SDF worlds](https://gazebosim.org/docs/latest/sdf_worlds/)
- [Sensors](https://gazebosim.org/docs/latest/sensors/)
- [Moving the robot](https://gazebosim.org/docs/latest/moving_robot/)