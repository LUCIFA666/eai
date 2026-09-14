# Gazebo 与其他仿真工具对比

目标：知道什么时候应该选 Gazebo，什么时候应该把 Gazebo 和 MuJoCo、Isaac Sim、Habitat、ManiSkill、Drake 等工具区分开。

仿真工具没有绝对的最好，只有适不适合当前任务。Gazebo 的强项不是“最快”或“最真实的画面”，而是和 ROS 机器人系统的结合。它很适合把机器人模型、传感器、控制插件、ROS 2 topic、导航栈和真机迁移流程串起来。

## 一句话定位

Gazebo 更像是 ROS 机器人系统的工程仿真环境。它强调：

- 机器人模型能接入 ROS 软件栈。
- 传感器话题、控制话题、TF 和仿真时间能闭环。
- 导航、底盘控制、多机器人、传感器联调可以先在仿真里跑通。
- 之后有机会把同一套 ROS 逻辑迁移到真实机器人上。

如果你的任务是“验证一个机器人系统能不能跑起来”，Gazebo 很合适。如果你的任务是“用百万级并行环境训练策略”或“做照片级合成数据”，Gazebo 可能不是首选。

## 和常见工具对比

| 工具 | 更适合什么 | 和 Gazebo 的区别 |
|---|---|---|
| MuJoCo | 机器人控制、接触动力学、强化学习、小规模高效仿真 | MuJoCo 更轻量，动力学和控制研究常用；Gazebo 更贴近 ROS 系统联调 |
| Isaac Sim / Isaac Lab | 高保真渲染、合成数据、GPU 加速、机器人学习 | Isaac 生态视觉和大规模训练能力强；Gazebo 更常用于 ROS 工程链路 |
| Habitat | 室内导航、具身问答、VLN、ObjectNav 等 embodied AI benchmark | Habitat 重点是任务和场景数据集；Gazebo 重点是机器人系统和 ROS 接口 |
| ManiSkill | 机械臂操作、具身操作 benchmark、可复现实验任务 | ManiSkill 更像任务基准；Gazebo 更像工程仿真环境 |
| Drake | 模型化动力学、系统框图、轨迹优化、形式化分析 | Drake 强调 white-box 建模和优化；Gazebo 强调插件化仿真和系统联调 |
| PyBullet | 轻量物理仿真、教学、快速原型 | PyBullet 上手快；Gazebo 的 ROS 和传感器生态更完整 |

## 什么时候优先选 Gazebo

下面这些情况，Gazebo 通常是合理选择：

1. 你的项目本来就是 ROS 2 机器人项目。
2. 你需要调 `/cmd_vel`、`/scan`、`/odom`、`/tf`、`/clock` 这些链路。
3. 你在做移动机器人导航、SLAM、避障或多机器人系统。
4. 你希望仿真结构和真机部署结构尽量接近。
5. 你需要用插件模拟传感器、底盘、关节控制或外部设备。

如果读者的课程目标是从仿真过渡到真实机器人，Gazebo 的工程价值就很明显。

## 什么时候不要硬选 Gazebo

下面这些情况，Gazebo 可能不是最顺手的工具：

| 目标 | 更可能考虑的工具 |
|---|---|
| 大规模并行强化学习 | Isaac Lab、MuJoCo、ManiSkill、Genesis |
| 机械臂精细接触和策略学习 benchmark | MuJoCo、ManiSkill、robosuite |
| 室内导航标准 benchmark | Habitat |
| 轨迹优化、可解释动力学建模 | Drake |
| 高质量合成图像和 RTX 渲染 | Isaac Sim |
| 快速写一个教学小 demo | PyBullet 或更轻量的脚本环境 |

这不是说 Gazebo 完全不能做这些事，而是说它不一定是最省力、最标准、最容易复现的选择。选工具时要看课程目标，而不是看工具名气。

## 一个实用判断标准

可以用下面三个问题判断是否该用 Gazebo：

```text
我的实验是否强依赖 ROS 2 topic、TF、Nav2 或真实机器人接口？
我的重点是不是先把机器人系统链路跑通，而不是追求最大训练吞吐？
仿真结果是否要服务于之后的真机调试或工程部署？
```

如果三个问题大多回答“是”，Gazebo 值得优先考虑。如果回答大多是“不是”，就应该认真比较其他仿真生态。

## 进一步阅读可以看：

- [Gazebo documentation](https://gazebosim.org/docs/latest/)
- [Gazebo Sim architecture](https://gazebosim.org/docs/latest/architecture/)
- [ROS 2 integration overview](https://gazebosim.org/docs/latest/ros2_overview/)