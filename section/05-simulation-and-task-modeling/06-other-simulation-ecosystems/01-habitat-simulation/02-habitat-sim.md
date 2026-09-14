# Habitat-Sim：3D 场景、传感器与动作模拟

目标：理解 Habitat-Sim 在 Habitat 生态中的职责，能说清 scene、agent、sensor、navmesh、action 和 physics 分别是什么，并知道它和低层机器人动力学仿真的边界。

Habitat-Sim 是 Habitat 生态的底层仿真器。它最重要的能力是快速加载 3D 场景，并从 agent 的第一视角生成观测。对 PointNav、ObjectNav、ImageNav、VLN 这类任务来说，agent 需要在大量室内空间里反复移动、观察和决策，仿真速度和数据集支持非常关键。

它不是专门为“精细机械臂接触控制”设计的低层动力学引擎。虽然 Habitat-Sim 支持 Bullet 物理、刚体、关节对象和 URDF 机器人，但它的典型用法仍然围绕室内场景、传感器和任务数据展开。

## Habitat-Sim 里的主要对象

读 Habitat-Sim 时，可以先抓住六个对象。

| 对象 | 作用 | 初学时怎么看 |
|---|---|---|
| scene | 一个 3D 场景，通常来自 HM3D、MP3D、Gibson、Replica 等数据集 | 智能体所在的房间或建筑 |
| agent | 在场景中移动的实体 | 带相机和动作接口的虚拟机器人 |
| sensor | RGB、depth、semantic、egomotion 等传感器 | 决定 observation 里有什么 |
| navmesh | 可导航网格 | 决定 agent 可以站在哪里、走到哪里 |
| action | 前进、转向、停止或自定义动作 | 决定 agent 怎么改变状态 |
| physics | Bullet 支持的刚体 / 关节物体交互 | 重排和交互任务才会重点使用 |

## 3D 场景：不只是 `.glb` 文件

Habitat-Sim 可以加载很多 3D 场景格式和数据集。初学者容易以为只要有一个 `.glb` 文件就够了，其实正式任务通常还需要额外配置。

比如一个可用的 Habitat 场景，可能包含：

```text
scene mesh:        house.glb
navmesh:           house.navmesh
semantic mesh:     house.semantic.glb
semantic mapping:  house.semantic.txt
scene config:      xxx.scene_dataset_config.json
episode file:      ObjectNav / PointNav episodes
```

这些文件不是每个任务都全部需要，但要知道它们解决的问题不同。RGB 渲染只需要可视 mesh；导航需要 navmesh；语义观测需要 semantic 文件；ObjectNav 还需要 episode 里写清目标类别和实例信息。

如果一个实验 RGB 正常但语义不正常，不能简单说 Habitat-Sim 有问题，应该先检查这个场景是否有语义标注，config 是否指向正确的 semantic 文件。

## 传感器：智能体能看见什么

Habitat-Sim 常见传感器包括 RGB、depth、semantic，也可以配置 egomotion sensing 等信息。不同传感器会让任务难度完全不同。

| 传感器 | 给智能体的信息 | 对任务的影响 |
|---|---|---|
| RGB | 第一视角彩色图像 | 接近普通视觉输入，但语义和几何需要模型自己学 |
| depth | 每个像素的距离 | 对导航、避障和几何理解很有帮助 |
| semantic | 每个像素的语义类别或实例信息 | 会显著降低 ObjectNav 等语义任务难度 |
| GPS+Compass / heading | 位置或方向相关信息 | PointNav 中常见，但真实机器人未必有完美定位 |

写实验结果时，必须说明传感器配置。一个使用 RGB-D + GPS+Compass 的 PointNav agent，和一个只使用 RGB 的 agent，难度不是一个级别。把它们的 success 直接比较，会误导读者。

## 动作模拟：离散动作不是底盘控制器

很多 Habitat 导航任务使用离散动作，例如：

```text
move_forward
turn_left
turn_right
stop
```

这些动作是任务层的抽象。`move_forward` 可能表示前进固定距离，`turn_left` 可能表示左转固定角度。它们非常适合做视觉导航研究，因为任务简单、可控、可复现，但不能直接等同于真实机器人底盘控制。

真实机器人底盘会面对速度控制、加速度限制、轮子打滑、定位误差、碰撞安全、动态障碍物等问题。Habitat 可以加入动作噪声或更复杂 embodiment，但初学时要先分清：导航 benchmark 的 action space 是研究抽象，不是真机控制接口。

## Navmesh：导航任务的隐藏基础

navmesh 是 Habitat 导航任务里很重要但容易被忽略的文件。它描述哪些区域可以站立和通行。没有 navmesh，agent 可能无法采样起点、无法规划 shortest path，也无法稳定计算一些导航指标。

调试时要看三个问题：

| 问题 | 说明 |
|---|---|
| navmesh 是否存在 | 有些场景只有 mesh，没有可导航网格 |
| agent 半径和高度是否合理 | 半径过大可能导致很多区域不可达 |
| shortest path 是否可计算 | SPL 等指标依赖最短路径长度 |

一个常见误解是“画面里看起来能走，就一定可导航”。不一定。导航任务里的可达性由 navmesh 决定，而不是由人眼看 RGB 图判断。

## 物理交互：有支持，但不是万能

Habitat-Sim 支持 Bullet 物理，可以用于刚体、关节对象和一些交互任务。Habitat 2.0 的 rearrangement 和 ReplicaCAD 就会用到这些能力。

但使用时要注意边界。Habitat-Sim 的物理支持是为 embodied AI 任务服务的，重点是让 agent 在室内环境里移动物体、打开抽屉、完成重排任务。它不是为了替代 MuJoCo 做高精度接触建模，也不是为了替代 Isaac Sim 做完整 ROS 2 机器人系统仿真。

## 本页小结

Habitat-Sim 负责让室内 3D 世界跑起来：加载场景，配置 agent 和 sensor，维护 navmesh，执行动作并返回观测。学习时先看 scene、sensor、navmesh 和 action，不要一开始就把它当成通用物理引擎。它的强项是高速室内场景仿真和 embodied AI 任务数据生成。

## 导航

- 上一页：[Habitat 生态总览](01-ecosystem-overview.md)
- 返回：[Habitat 简介](../01-habitat-simulation.md)
- 下一页：[Habitat-Lab](03-habitat-lab.md)

## 进一步阅读可以看：

- [Habitat-Sim documentation](https://aihabitat.org/docs/habitat-sim/)
- [Habitat-Sim GitHub](https://github.com/facebookresearch/habitat-sim)
- [Habitat-Sim supported datasets](https://github.com/facebookresearch/habitat-sim/blob/main/DATASETS.md)