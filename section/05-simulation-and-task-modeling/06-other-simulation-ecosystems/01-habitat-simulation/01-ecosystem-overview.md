# Habitat 生态总览：Habitat-Sim、Habitat-Lab 与数据集

目标：分清 Habitat 生态里的三层核心对象：Habitat-Sim、Habitat-Lab 和数据集，并能用这三层解释一个 Habitat 实验是怎样跑起来的。

初学 Habitat 时，最容易犯的错误是把所有东西都叫作“Habitat”。其实在正式实验里，至少要分清三件事：底层仿真器、上层任务框架和场景数据集。它们各自解决的问题不同，排错方式也不同。

如果用一句话概括：**Habitat-Sim 负责让 3D 世界能被看到和走动，Habitat-Lab 负责把这个世界变成任务，数据集负责提供这个世界本身。**

## 先看三层结构

Habitat 生态可以拆成下面三层：

| 层级 | 代表对象 | 负责什么 | 常见问题 |
|---|---|---|---|
| 场景数据集 | Matterport3D、Gibson、HM3D、Replica、ReplicaCAD | 提供房间、建筑、物体、语义和可导航区域 | 数据路径、许可、语义文件、scene config |
| Habitat-Sim | simulator、agent、sensor、navmesh、physics | 加载场景，渲染观测，执行动作，维护仿真状态 | 场景加载失败、传感器 shape 不对、navmesh 不可用 |
| Habitat-Lab | env、dataset、episode、task、measure、baseline | 定义任务、读取 episode、训练和评测 agent | episode 找不到、指标不一致、config 覆盖错误 |

这张表里的 `dataset` 有两个含义，要特别小心。

第一个是 **scene dataset**，也就是 3D 场景数据。它提供的是房间或建筑本身，比如 HM3D 的某个 house，Matterport3D 的某个 building，Replica 的某个 apartment。

第二个是 **episode dataset**，它提供的是任务实例。比如 ObjectNav 里，一个 episode 会指定：在哪个场景、从哪里出发、目标类别是什么、目标物体在哪里、成功距离是多少。episode dataset 依赖 scene dataset，但不是同一个东西。

## 一个 Habitat 实验怎么流动

可以把一次 Habitat 实验理解成下面这条流水线：

```text
scene dataset
  -> Habitat-Sim 加载 3D 场景
  -> agent 带着 RGB / depth / semantic 等 sensor 进入场景
  -> Habitat-Lab 从 episode dataset 读取任务实例
  -> task 定义 action、reward、success 和 measure
  -> policy 根据 observation 输出 action
  -> env.step(action) 推进仿真和任务状态
  -> measure 计算 success、SPL、distance_to_goal 等指标
```

这条线里任何一层出错，表现出来可能都像“Habitat 跑不了”，但排查方向完全不同。

| 现象 | 更可能在哪一层 | 优先检查 |
|---|---|---|
| 找不到 `.glb` 或 scene | scene dataset / Habitat-Sim | 场景路径、scene dataset config、数据下载是否完整 |
| RGB 有图，但 semantic 全黑或无效 | scene dataset / sensor config | 是否有语义标注，是否启用 semantic sensor |
| `reset()` 报 episode 错误 | Habitat-Lab | episode json、split、config 里的 dataset path |
| 策略能跑但指标很差 | task / policy / measure | action space、传感器、reward、训练步数、评测 split |
| success 高但路径很绕 | measure 解读问题 | 同时查看 SPL 和 path length |

## Habitat-Sim 和 Habitat-Lab 的关系

Habitat-Lab 通常使用 Habitat-Sim 作为核心 simulator，但二者不是绑定死的同义词。Habitat-Sim 可以单独用来加载场景、查看 sensor、测试 navmesh；Habitat-Lab 则在它之上组织任务和训练。

一个很实用的判断方法是：

| 你正在处理的问题 | 更接近哪一层 |
|---|---|
| 如何加载 HM3D 场景？ | Habitat-Sim |
| RGB 和 depth 的分辨率在哪里设？ | Habitat-Sim / config |
| ObjectNav 的目标类别在哪里读？ | Habitat-Lab episode dataset |
| SPL 指标怎么计算？ | Habitat-Lab measure |
| PPO 训练脚本怎么启动？ | habitat-baselines |
| 人在环交互怎么接入？ | habitat-hitl / Habitat 3.0 相关工具 |

理解这点后，读代码会顺很多。看到 `SimulatorConfiguration`、`CameraSensorSpec`、`AgentConfiguration`，你大概率在读 Habitat-Sim；看到 `Task`、`Measure`、`Dataset`、`Env`、`Benchmark`，你大概率在读 Habitat-Lab。

## 数据集不是背景图

在 Habitat 里，数据集不是随便换的背景。数据集会影响任务难度和实验结论。

同样是 PointNav，在 Matterport3D、Gibson、HM3D 上训练和评测，结果可能不同；同样是 ObjectNav，如果一个数据集没有稳定语义标注，就不能直接做同样的物体目标任务；同样是重排任务，如果场景没有可交互对象，就不可能直接做 Habitat 2.0 式的 rearrangement。

## 本页小结

Habitat 的核心是一个分层生态。场景数据集提供世界，Habitat-Sim 让世界运行起来，Habitat-Lab 把世界组织成任务。学习时先分清这三层，后面无论看 PointNav、ObjectNav、VLN 还是 Rearrangement，都能知道自己正在处理的是场景问题、仿真问题、任务问题，还是训练问题。

## 导航

- 上一页：[Habitat 简介](../01-habitat-simulation.md)
- 返回：[Habitat 简介](../01-habitat-simulation.md)
- 下一页：[Habitat-Sim](02-habitat-sim.md)

## 进一步阅读可以看：

- [Habitat-Sim GitHub](https://github.com/facebookresearch/habitat-sim)
- [Habitat-Lab GitHub](https://github.com/facebookresearch/habitat-lab)
- [Habitat-Lab documentation](https://aihabitat.org/docs/habitat-lab/)