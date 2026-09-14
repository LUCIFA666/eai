# Habitat 支持的典型任务：PointNav、ObjectNav、ImageNav、VLN、EQA、Rearrangement

目标：理解 Habitat 里几类典型任务分别在评测什么，能根据目标形式区分 PointNav、ObjectNav、ImageNav、VLN、EQA 和 Rearrangement。

Habitat 的任务不是随便换一个名字。每种任务都代表一种不同的具身智能问题：目标从哪里来，agent 能看到什么，动作怎么执行，成功怎么判断。把任务分清楚，比一开始追训练分数更重要。

## 按目标形式理解任务

| 任务 | 目标怎么给 | 主要能力 | 常见指标 |
|---|---|---|---|
| PointNav | 目标点或相对坐标 | 几何导航、定位、路径规划 | success、SPL、distance_to_goal |
| ObjectNav | 物体类别 | 语义探索、目标搜索、空间记忆 | success、SPL、distance_to_goal |
| ImageNav | 一张目标图像 | 视觉匹配、实例定位、视角理解 | success、SPL |
| VLN | 自然语言路径指令 | 语言理解、视觉定位、指令跟随 | success、SPL、nDTW 等 |
| EQA | 问题文本 | 主动感知、探索、问答 | answer accuracy、navigation metrics |
| Rearrangement | 目标物体状态 | 导航、操作、物理交互、任务分解 | task success、子目标完成率、效率 |

## PointNav

PointNav 是最基础的导航任务。目标通常是一个点，或者相对于当前位置的目标坐标。agent 的任务是从起点走到目标附近，并在合适的时候停止。

PointNav 主要考察几何导航能力。它不要求 agent 理解“椅子”“床”“杯子”这些语义，只要能根据传感器和目标信息找到路线即可。

PointNav 适合做入门任务，因为它把很多复杂因素去掉了：没有目标类别歧义，没有语言理解，也不需要移动物体。它能帮助读者先理解 observation、action、episode、success 和 SPL。

## ObjectNav

ObjectNav 的目标是物体类别，比如 `chair`、`bed`、`toilet`。这比 PointNav 更接近真实机器人需求，因为人通常不会给机器人一个精确坐标，而是说“去找椅子”。

ObjectNav 要求 agent 具备几类能力：

1. 根据视觉识别目标类别或目标相关线索。
2. 探索陌生房间，而不是只走固定路线。
3. 建立空间记忆，避免重复搜索。
4. 在接近目标时判断是否应该 `stop`。

ObjectNav 的结果很依赖语义标注、目标类别集合和 episode 采样方式。如果两个工作使用不同数据集或不同目标类别，分数不能简单横向比较。

## ImageNav

ImageNav 给的不是类别名，而是一张目标图像。agent 需要移动到能看到对应目标位置或对象实例的位置。

它的难点和 ObjectNav 不一样。ObjectNav 依赖类别语义，ImageNav 更依赖视觉匹配和实例级识别。目标图像的拍摄角度、视场、是否包含明显物体、是否和 agent 传感器规格一致，都会影响任务难度。

因此 ImageNav 实验一定要写清目标图像如何采样。随便从墙面采样一张图，和围绕某个对象实例采样目标图像，是不同任务难度。

## VLN

VLN 是 Vision-and-Language Navigation。它给 agent 的目标是一段自然语言路径指令，例如“走出厨房，经过沙发，停在卧室门口”。

VLN 同时考察语言理解和视觉导航。agent 需要把指令中的空间关系、物体线索和动作顺序对应到当前场景里。相比 ObjectNav，VLN 不只是找一个类别，而是沿着语言描述完成一段路径。

在 Habitat 生态中，VLN 常见的重要变体是连续环境中的 VLN，例如 VLN-CE。它把过去离散全景图上的导航问题推进到更接近连续控制的环境里。

## EQA

EQA 是 Embodied Question Answering。它不是静态图像问答，而是让 agent 在环境中移动、观察，再回答问题。

例如问题可能是：“客厅里的沙发是什么颜色？”如果 agent 一开始看不到沙发，就需要探索环境，找到相关视角，再进行回答。

EQA 的核心是主动感知。只会回答图像问题还不够，agent 要知道自己缺少什么信息，并通过移动去获取信息。

## Rearrangement

Rearrangement 从“走到哪里”进入“改变世界状态”。目标不再只是到达某个位置，而是让物体满足某种状态，例如把杯子放到桌上、把物品移动到目标 receptacle、打开抽屉再取物体。

这个任务比导航复杂很多，因为它同时需要导航、操作、物理交互、任务分解和状态评估。到了这里，成功不只是 agent 停在哪里，而是物体是否真的到达目标状态。

## 任务之间怎么选

如果你是第一次学习 Habitat，建议顺序是：PointNav → ObjectNav → ImageNav / VLN / EQA → Rearrangement。

PointNav 帮你理解基本环境接口；ObjectNav 引入语义和探索；ImageNav、VLN、EQA 分别引入图像目标、语言目标和问答目标；Rearrangement 再引入物理交互和对象状态。

不要一开始就直接做 Rearrangement 或 Habitat 3.0 的 social tasks。那样会同时遇到数据、物理、任务、策略和多智能体问题，很难定位自己到底哪里没懂。

## 本页小结

Habitat 的任务可以按目标形式来理解。PointNav 是几何目标，ObjectNav 是类别目标，ImageNav 是图像目标，VLN 是语言路径目标，EQA 是问题目标，Rearrangement 是物体状态目标。目标形式不同，传感器、动作、指标和难度都会变。

## 导航

- 上一页：[常见数据集](04-common-datasets.md)
- 返回：[Habitat 简介](../01-habitat-simulation.md)
- 下一页：[从 1.0 到 3.0](06-habitat-versions.md)

## 进一步阅读可以看：

- [Habitat 1.0 paper](https://arxiv.org/abs/1904.01201)
- [Habitat-Lab documentation](https://aihabitat.org/docs/habitat-lab/)
- [Habitat 2.0 paper](https://arxiv.org/abs/2106.14405)