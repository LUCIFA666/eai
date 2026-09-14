# Habitat 与其他仿真生态的对比

目标：理解 Habitat 和 MuJoCo、Isaac Sim、Isaac Lab、ManiSkill、Genesis、Gazebo 等平台的差异，能根据任务需求判断是否应该选择 Habitat。

Habitat 很强，但不是所有机器人仿真问题都适合用 Habitat。它最擅长的是室内场景中的 embodied AI benchmark，尤其是导航、语义目标搜索、语言指令、问答和家庭重排任务。它不擅长的，是低层控制、精细接触、完整机器人系统联调和多物理材料仿真。

## 总览对比

| 生态 | 更适合 | 不适合直接替代 |
|---|---|---|
| Habitat | 室内导航、ObjectNav、VLN、EQA、Rearrangement、标准 benchmark | 低层控制器、精细接触仿真、ROS 2 工程联调 |
| MuJoCo | 机器人动力学、关节控制、接触调参、快速 RL 原型 | 大规模真实感室内场景和语义导航任务 |
| Isaac Sim | USD 场景、高保真传感器、ROS 2、合成数据、工程仿真 | 轻量快速的导航 benchmark 复现实验 |
| Isaac Lab | Isaac Sim 上的大规模并行训练、manager-based task | Habitat 现成的室内导航和 VLN / EQA 生态 |
| ManiSkill | 操作任务、移动操作、桌面 manipulation benchmark | 大规模建筑级室内导航任务 |
| Genesis | Python-first 多物理、并行、多材料探索 | 标准室内导航 benchmark 和 Habitat 数据生态 |
| Gazebo | ROS / ROS 2 机器人系统集成 | 大规模视觉导航训练和标准 embodied AI benchmark |

## 什么时候选 Habitat

适合选 Habitat 的信号：

| 信号 | 说明 |
|---|---|
| 任务是室内导航或语义目标搜索 | PointNav、ObjectNav、ImageNav 是 Habitat 的强项 |
| 需要标准 episode 和指标 | success、SPL、distance_to_goal 等已有成熟定义 |
| 需要大量室内场景 | HM3D、MP3D、Gibson、Replica 等有生态支持 |
| 研究语言导航或问答 | VLN、EQA 与 Habitat 生态关系紧密 |
| 研究家庭重排或人机协作 | Habitat 2.0 / 3.0 提供相关任务基础 |

不适合优先选 Habitat 的信号：

| 信号 | 更应该看什么 |
|---|---|
| 重点是精细接触和力控 | MuJoCo、Isaac Sim、ManiSkill |
| 重点是 ROS 2 工程联调 | Gazebo、Isaac Sim |
| 重点是多物理材料 | Genesis 或专门多物理平台 |
| 重点是桌面操作 benchmark | ManiSkill、robosuite、Isaac Lab 等 |
| 只想快速验证一个动力学控制器 | MuJoCo 或 PyBullet |

## 本页小结

Habitat 的优势不是“什么都能仿真”，而是“把室内场景、任务 episode、第一视角传感器和标准评测组织成研究生态”。选平台时先问任务核心是什么：如果核心是室内目标导航、语言导航、问答或家庭重排，Habitat 很合适；如果核心是接触控制、工程联调或多物理，应该优先看其他生态。

## 导航

- 上一页：[ObjectNav 实验流程](07-objectnav-workflow.md)
- 返回：[Habitat 简介](../01-habitat-simulation.md)
- 下一页：[新手学习路线](09-learning-path.md)

## 进一步阅读可以看：

- [Habitat-Sim GitHub](https://github.com/facebookresearch/habitat-sim)
- [Habitat-Lab GitHub](https://github.com/facebookresearch/habitat-lab)
- [Isaac Sim](../../03-isaac-sim.md)
- [MuJoCo](../../02-mujoco.md)
- [Genesis](../02-genesis.md)