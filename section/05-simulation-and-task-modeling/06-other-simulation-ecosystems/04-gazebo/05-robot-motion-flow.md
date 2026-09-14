# Gazebo 中的机器人运动流程

目标：理解一条速度命令如何从 ROS 或 Gazebo topic 进入仿真，让机器人在物理世界里运动，并产生新的传感器反馈。

很多人第一次用 Gazebo 让机器人动起来时，会把问题想得太简单：发一个 `/cmd_vel`，机器人就应该走。实际上，中间至少有模型、插件、topic、物理步进、里程计和传感器反馈几层。只要其中一层没接上，机器人就不会按预期运动。

以最常见的差速移动机器人为例，运动流程可以写成：

```text
速度命令 /cmd_vel
  -> Gazebo 中的 DiffDrive 插件接收命令
  -> 插件根据 wheel radius 和 wheel separation 计算轮子运动
  -> Physics system 更新轮子、底盘、碰撞和位姿
  -> Gazebo 发布 odom、joint state、sensor data
  -> ROS 2 节点读取反馈，继续输出下一条命令
```

## 模型先要具备“能动”的条件

机器人不是有两个轮子就能动。至少要有下面这些条件：

| 条件 | 为什么重要 |
|---|---|
| 左右轮 link 和底盘 link | 物理世界里必须有可以运动的刚体 |
| 左右轮 joint | 插件需要知道控制哪个关节 |
| 合理的 collision 和 inertial | 否则机器人可能穿地、乱抖或飞走 |
| DiffDrive 之类的控制插件 | 把速度命令转换成轮子运动 |
| 正确的 topic | 外部命令要发到插件正在监听的话题上 |

官方移动机器人教程里使用的是 `DiffDrive` 系统插件，核心配置包括左轮关节、右轮关节、轮距、轮子半径、里程计发布频率和命令 topic。这里不要死记具体数值，而要明白每一项在描述什么：轮距和轮子半径决定速度命令如何换算成轮子角速度；joint 名称决定插件控制哪两个关节；topic 决定命令从哪里进来。

## 一段典型配置长什么样

下面是差速驱动插件的结构示意，真实项目中 joint 名称、轮距、半径和 topic 要按自己的机器人改：

```xml
<plugin
    filename="gz-sim-diff-drive-system"
    name="gz::sim::systems::DiffDrive">
  <left_joint>left_wheel_joint</left_joint>
  <right_joint>right_wheel_joint</right_joint>
  <wheel_separation>0.32</wheel_separation>
  <wheel_radius>0.05</wheel_radius>
  <odom_publish_frequency>30</odom_publish_frequency>
  <topic>cmd_vel</topic>
</plugin>
```

这段配置不是“让机器人变智能”，它只是让仿真机器人具备接收速度命令并按差速模型运动的能力。真正的导航、避障、路径规划通常在 ROS 2 侧完成，比如由 Nav2 输出 `/cmd_vel`。

## 物理步进发生了什么

Gazebo 每个仿真步都会更新世界状态。控制插件收到命令后，不是直接把机器人瞬移到新位置，而是通过关节速度、力或约束影响物理系统。物理系统再根据时间步长、碰撞、摩擦、质量和关节约束更新机器人位姿。

因此，机器人运动不正常时要分层看：

| 现象 | 可能原因 |
|---|---|
| 发命令后完全不动 | topic 不对、插件没加载、joint 名字不对、仿真暂停 |
| 原地打滑或转圈 | 左右轮 joint、轮距、半径或坐标方向写错 |
| 一启动就抖动 | inertial、collision、关节限制或物理参数不合理 |
| RViz 中位置不动 | Gazebo 里动了，但 odom / TF / bridge 没接到 ROS |
| 避障不正常 | lidar frame、`/scan`、TF 或 costmap 参数有问题 |

## 传感器反馈让闭环成立

只让机器人动起来还不够。导航算法需要反馈：机器人在哪里、周围有什么障碍、当前时间是多少、各坐标系关系是什么。Gazebo 里的移动机器人实验通常会输出：

| 数据 | 用途 |
|---|---|
| odom | 估计机器人局部运动 |
| joint states | 更新轮子等关节状态 |
| lidar scan | 用于避障、建图或定位 |
| IMU | 提供角速度、线加速度等信息 |
| clock | 让 ROS 2 节点使用仿真时间 |
| TF | 表达 `map`、`odom`、`base_link`、`laser` 等坐标关系 |

一个合格的 Gazebo 移动机器人例子，应该不仅能看到小车在窗口里动，还能在 ROS 2 侧看到这些反馈话题，并且它们的时间戳和坐标系关系是合理的。

## 进一步阅读可以看：

- [Moving the robot](https://gazebosim.org/docs/latest/moving_robot/)
- [Sensors](https://gazebosim.org/docs/latest/sensors/)