# Habitat

目标：理解 Habitat 在具身智能仿真生态中的位置，并沿着 Habitat-Sim、Habitat-Lab、数据集、任务、实验流程和学习路线逐步建立完整心智模型。

Habitat 更适合作为 **室内 embodied AI 任务生态** 来理解：底层用 Habitat-Sim 快速加载和渲染 3D 室内场景，上层用 Habitat-Lab 定义 episode、任务、动作、奖励、指标和训练流程。它最常见的研究对象不是低层关节控制，而是 PointNav、ObjectNav、ImageNav、VLN、EQA、Rearrangement 这类导航、语义理解和家庭任务。

这里按从概念到实验的顺序展开。不要急着一上来下载大数据集或训练 PPO，先把生态层级看清楚：场景数据集提供世界，Habitat-Sim 让世界运行起来，Habitat-Lab 把世界包装成任务，策略根据 observation 输出 action，最后由 measure 解释结果。


## 学习路径

| 页面                                                               | 这一页回答的问题 | 重点 |
|------------------------------------------------------------------|---|---|
| [Habitat 生态总览](01-habitat-simulation/01-ecosystem-overview.md)   | Habitat-Sim、Habitat-Lab 和数据集是什么关系？ | 生态分层、scene dataset、episode dataset、实验闭环 |
| [Habitat-Sim](01-habitat-simulation/02-habitat-sim.md)           | 底层仿真器到底负责什么？ | 3D 场景、agent、sensor、navmesh、动作、物理边界 |
| [Habitat-Lab](01-habitat-simulation/03-habitat-lab.md)           | 任务、训练接口和指标在哪里定义？ | config、dataset、episode、task、measure、baseline |
| [常见数据集](01-habitat-simulation/04-common-datasets.md)             | Matterport3D、Gibson、HM3D、Replica 有什么区别？ | 真实扫描、语义标注、访问许可、适用任务 |
| [典型任务](01-habitat-simulation/05-typical-tasks.md)                | PointNav、ObjectNav、ImageNav、VLN、EQA、Rearrangement 分别在评测什么？ | 目标形式、观测需求、评价口径 |
| [从 1.0 到 3.0](01-habitat-simulation/06-habitat-versions.md)      | Habitat 为什么从导航走到交互和人机协作？ | Habitat 1.0、2.0、3.0 的研究问题变化 |
| [ObjectNav 实验流程](01-habitat-simulation/07-objectnav-workflow.md) | 一个完整 Habitat 实验怎么组织？ | 数据、episode、sensor、action、policy、metric、记录卡 |
| [与其他仿真生态对比](01-habitat-simulation/08-comparison.md)              | 什么时候选 Habitat，什么时候不选？ | MuJoCo、Isaac Sim、Isaac Lab、ManiSkill、Genesis、Gazebo 对比 |
| [新手学习路线](01-habitat-simulation/09-learning-path.md)              | 初学者应该按什么顺序学？ | 最小运行、viewer、PointNav、ObjectNav、Rearrangement |
| [Habitat 示例](01-habitat-simulation/10-server-minimal-run.md)     | 在服务器上怎么真实跑通 Habitat？ | headless 安装、测试场景、PointNav、RGB 帧和视频 |

## 怎么读这一组

建议先顺序读前三页。前三页解决最容易混的层级问题：Habitat-Sim 是 simulator，Habitat-Lab 是 task / training framework，数据集和 episode dataset 不是一回事。只要这三层不清楚，后面看任何任务都会乱。

中间三页解决“Habitat 到底能做什么”。数据集决定智能体进入什么世界，任务决定智能体要完成什么目标，版本脉络说明 Habitat 为什么从导航推进到交互和人机协作。

最后四页更接近实战。ObjectNav 流程页会把一个实验从数据、配置、传感器、动作、策略和指标串起来；对比页帮助你判断是否该选 Habitat；学习路线页给出从最小测试到正式实验的路径；服务器最小运行流程页则记录一条已经跑通的 headless 实验链路。

## 导航

- 返回：[其他仿真生态](../06-other-simulation-ecosystems.md)
- 下一页：[Habitat 生态总览](01-habitat-simulation/01-ecosystem-overview.md)

## 进一步阅读可以看：

- [Habitat-Sim GitHub](https://github.com/facebookresearch/habitat-sim)
- [Habitat-Sim documentation](https://aihabitat.org/docs/habitat-sim/)
- [Habitat-Lab GitHub](https://github.com/facebookresearch/habitat-lab)
- [Habitat-Lab documentation](https://aihabitat.org/docs/habitat-lab/)
- [Habitat-Sim supported datasets](https://github.com/facebookresearch/habitat-sim/blob/main/DATASETS.md)
- [Habitat 1.0 paper](https://arxiv.org/abs/1904.01201)
- [Habitat 2.0 paper](https://arxiv.org/abs/2106.14405)
- [Habitat 3.0](https://aihabitat.org/habitat3/)