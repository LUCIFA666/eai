# Habitat 1.0 到 3.0：从导航到交互再到人机协作

目标：理解 Habitat 1.0、2.0、3.0 的研究重点如何变化，知道它为什么从视觉导航扩展到交互式家庭任务，再扩展到人类、虚拟人和机器人协作。

Habitat 不是一次性完成的单个平台。它的发展路线很清楚：先解决“室内导航怎么大规模训练和评测”，再解决“智能体如何在家庭场景中改变物体状态”，最后推进到“机器人如何和人或虚拟人共同生活、协作和评测”。

## 总体脉络

| 阶段 | 主要问题 | 代表内容 |
|---|---|---|
| Habitat 1.0 | 如何高效训练和评测 embodied navigation agent？ | Habitat-Sim、Habitat-API、PointNav、ObjectNav、EQA |
| Habitat 2.0 | 家庭助手如何在交互式环境里移动和重排物体？ | ReplicaCAD、physics-enabled simulation、Home Assistant Benchmark |
| Habitat 3.0 | 机器人如何和人类、humanoid avatar 协作？ | humanoid simulation、human-in-the-loop、Social Navigation、Social Rearrangement |

这三个阶段不是互相替代，而是逐层扩展。Habitat 3.0 并不意味着 PointNav 过时；相反，导航仍然是后续交互和协作任务的基础。

## Habitat 1.0：高效视觉导航平台

Habitat 1.0 的核心贡献是把 embodied AI 里的视觉导航实验做成一个高效、可复现的平台。论文中把它拆成两部分：Habitat-Sim 和 Habitat-API。今天我们更常说 Habitat-Sim 和 Habitat-Lab。

这一阶段重点关注的问题包括：

1. 如何在 photorealistic 3D simulation 中训练 embodied agents。
2. 如何配置 agent、sensor 和任务。
3. 如何用标准指标比较不同导航方法。
4. 如何进行跨数据集泛化实验，比如在 Matterport3D 和 Gibson 间训练测试。

Habitat 1.0 中的典型任务是 PointNav、ObjectNav、instruction following 和 EQA。它们的共同点是：agent 主要通过移动和观察完成任务，不一定需要真正改变场景中的物体状态。

## Habitat 2.0：从导航走向家庭交互

Habitat 2.0 的关键词是 **rearrangement** 和 **home assistant**。它把 Habitat 从“走到目标”推进到“改变环境”。论文里强调了三层贡献：数据、仿真和 benchmark。

数据层是 ReplicaCAD。它提供带可交互对象和关节物体的公寓场景，比如可打开的抽屉、柜门和可移动物品。

仿真层是高性能 physics-enabled simulation。这里不只是渲染 RGB-D，而是要支持物体被移动、关节对象被打开关闭、机器人和物体发生交互。

任务层是 Home Assistant Benchmark。它用家庭助手任务评测 agent，例如整理房间、准备物品、设置餐桌等。这里的成功不再只是“到达目标点”，而是物体状态是否被改变到目标状态。

## Habitat 3.0：人、虚拟人和机器人共处

Habitat 3.0 的主题是 co-habitat，也就是 humans、avatars 和 robots 共同存在的家庭环境。它把 Habitat 2.0 的家庭交互进一步扩展到人机协作。

这一阶段有三个重点：

| 方向 | 说明 |
|---|---|
| humanoid simulation | 支持复杂 humanoid body、外观和动作 |
| human-in-the-loop | 真实人可以通过鼠标键盘或 VR 与仿真机器人交互 |
| collaborative tasks | 提供 Social Navigation 和 Social Rearrangement 等协作任务 |

Social Navigation 不是普通导航。机器人需要找到并跟随 humanoid，同时保持安全距离，避免阻挡人类移动。

Social Rearrangement 也不是普通重排。机器人和 humanoid 需要协作，把物体从初始状态整理到目标状态。此时策略不仅要考虑物体和房间，还要考虑另一个智能体的行为。

## 三个版本怎么连起来

```text
Habitat 1.0
  先让 agent 在室内空间里高效导航和评测

Habitat 2.0
  再让 agent 能改变环境中的物体状态

Habitat 3.0
  最后把人类、虚拟人和机器人放进同一个任务闭环
```

这条线也对应学习顺序。先学 1.0 的导航任务，再学 2.0 的重排任务，最后再看 3.0 的人机协作。如果顺序反过来，很容易被 humanoid、VR、social task、rearrangement 和 physics 同时淹没。

## 使用版本时要注意什么

Habitat-Sim 和 Habitat-Lab 的 GitHub README 都显示，v0.3.4 之后 Meta 内部团队不再进行官方 active development 或 maintenance。

所以写实验记录时，建议写清：

```text
Habitat-Sim version or commit
Habitat-Lab version or commit
Habitat 1.0 / 2.0 / 3.0 related task
scene dataset and version
episode dataset and split
config file
metrics
```

## 本页小结

Habitat 1.0 建立了高效导航实验平台，Habitat 2.0 把任务推进到交互式家庭重排，Habitat 3.0 进一步引入人类、虚拟人和协作任务。它的发展路线不是“功能越来越多”这么简单，而是研究问题从空间导航、物体交互，逐步走向人机共处。

## 导航

- 上一页：[典型任务](05-typical-tasks.md)
- 返回：[Habitat 简介](../01-habitat-simulation.md)
- 下一页：[ObjectNav 实验流程](07-objectnav-workflow.md)

## 进一步阅读可以看：

- [Habitat 1.0 paper](https://arxiv.org/abs/1904.01201)
- [Habitat 2.0 paper](https://arxiv.org/abs/2106.14405)
- [Habitat 3.0 project page](https://aihabitat.org/habitat3/)
- [Habitat 3.0 paper](https://arxiv.org/abs/2310.13724)