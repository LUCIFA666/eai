# Gazebo 简介与整体架构

目标：把 Gazebo 看成一个由 server、GUI、插件、通信中间件和一组底层库组成的仿真系统，而不是一个单独的可视化窗口。

新版 Gazebo 的入口通常是 `gz sim`。执行 `gz sim xxx.sdf` 时，Gazebo 会加载一个 SDF world，然后启动仿真。这个仿真不是只有一个进程在画图，而是分成后端 server 和前端 client。后端负责仿真循环、物理、传感器、插件和状态更新；前端主要是 GUI，用来显示 3D 场景、插入模型、查看属性和操作仿真。

官方文档里把 Gazebo Sim 描述为 Gazebo 的应用入口，它会把 Gazebo 的多个库组合起来使用。理解这一点很重要：`gz-sim` 不是孤立存在的，它会通过插件使用 `gz-physics`、`gz-sensors`、`gz-rendering`、`gz-transport`、`gz-msgs`、`sdformat` 等库。

## 从一个命令看整体结构

最常见的启动方式是：

```bash
gz sim shapes.sdf
```

这条命令背后大致发生了几件事：

1. Gazebo 读取 SDF 文件，知道 world 里有哪些模型、光源、物理设置和插件。
2. 后端 server 建立仿真状态，运行物理系统、用户命令系统、场景广播系统等插件。
3. GUI client 通过 Gazebo Transport 接收场景状态，把后端世界显示出来。
4. 如果 world 或机器人模型里加载了传感器、控制器、差速驱动等系统，它们会在仿真循环里更新状态、发布消息或接收命令。
5. 如果需要接入 ROS 2，可以用 `ros_gz` 把 Gazebo Transport 的话题和 ROS 2 话题桥接起来。

如果只想跑后端、不打开 GUI，可以用 server-only 模式；如果 GUI 单独连接一个已经运行的 server，也可以拆开。初学阶段不必马上记住所有命令，先记住 Gazebo 不是“一个窗口”，它是“后端仿真 + 前端可视化 + 通信 + 插件”的组合。

## 后端：Entity-Component-System

Gazebo Sim 的后端使用 Entity-Component-System，也就是 ECS 架构。可以粗略这样理解：

| 概念 | 在 Gazebo 中大概对应什么 | 作用 |
|---|---|---|
| Entity | model、link、joint、light、actor 等场景对象 | 表示世界中的“东西” |
| Component | pose、name、geometry、velocity 等属性 | 描述 entity 当前有什么状态和属性 |
| System | physics、sensor、diff-drive、scene broadcaster 等插件 | 在仿真循环里读取和修改组件 |

比如一个差速小车模型是一个 entity，它有左右轮 link、joint、pose、速度等组件。DiffDrive system 读入速度命令，修改轮子相关状态；Physics system 根据关节、碰撞和力学参数更新世界；Sensor system 再根据新的世界状态生成雷达或相机数据。

这种结构解释了为什么 Gazebo 里很多功能都以 plugin / system 的形式出现。插件不是附属装饰，而是仿真循环的一部分。你想让机器人动，需要控制插件；想要传感器数据，需要传感器系统；想让 GUI 看到后端状态，需要场景广播系统。

## 前端：GUI 不是算法运行的地方

Gazebo GUI 主要负责可视化和交互。你可以在 GUI 里查看模型、移动视角、暂停和播放仿真、插入模型、观察传感器效果。但真正的物理步进、传感器计算、插件控制主要在后端 server 中进行。

这也解释了一个常见现象：有时候仿真可以 headless 运行，没有窗口也能发布话题；有时候 GUI 卡顿并不一定代表后端算法全坏了；还有时候你关闭 GUI，只要 server 还在，仿真仍然可能继续跑。

## 新版 Gazebo 和 Gazebo Classic

很多中文旧教程会写 `gazebo`、`gazebo_ros`、`gazebo_plugins`，这些大多是 Gazebo Classic 时代的资料。新版 Gazebo 文档里更常见的是 `gz sim`、`gz topic`、`gz service`、`ros_gz`、`gz-sim-*` 插件。

学习时建议把两条线分开：

| 线索 | 常见关键词 | 适合怎么读 |
|---|---|---|
| Gazebo Classic | `gazebo`、`gazebo_ros`、`gazebo_plugins` | 维护旧项目时再看 |
| 新版 Gazebo | `gz sim`、`gz topic`、`ros_gz`、`gz-sim-*` | 新项目优先按这条线学习 |

如果你照着一篇教程做却发现插件名字、命令、ROS 包名都对不上，第一件事不是怀疑自己环境坏了，而是先检查那篇教程到底写的是 Classic 还是新版 Gazebo。

## 进一步阅读可以看：

- [Gazebo Sim architecture](https://gazebosim.org/docs/latest/architecture/)
- [Gazebo documentation](https://gazebosim.org/docs/latest/)