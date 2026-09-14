# 5.3 EDH、TfD 与 TATC Benchmark

## 目标

TEACh 不只是一个数据集，也定义了多个评测设置。最核心的是 EDH、TfD 和 TATC。它们都来自 TEACh 的人类协作数据，但考察的问题不同。

可以先用一句话区分：

```text
EDH：从一段对话历史和中间状态继续完成任务
TfD：根据完整对话生成完整动作轨迹
TATC：同时建模 Commander 和 Follower 的协作完成过程
```

## 三个 benchmark 的总体对比

| Benchmark | 全称 | 输入 | 输出 | 主要考察 |
| --- | --- | --- | --- | --- |
| EDH | Execution from Dialog History | 历史对话、当前视觉状态、已执行历史 | 后续动作序列 | 是否能从中间状态接手并完成任务 |
| TfD | Trajectory from Dialog | 完整对话、视觉反馈 | 完整或主要动作轨迹 | 是否能把完整对话转化为可执行计划 |
| TATC | Two-Agent Task Completion | Commander 任务信息、Follower 环境观察、双方对话接口 | 双方协作产生语言和动作 | 是否能完整模拟两-agent 协作任务完成 |

这三个设置从局部执行到完整协作逐渐变难。EDH 更像“接着人类做到一半的任务继续做”，TfD 更像“读完整对话后复现行动”，TATC 则要求系统自己生成对话和动作。

## EDH：Execution from Dialog History

EDH 是 TEACh 中最常用的设置之一。模型拿到一段已经发生过的对话历史和环境状态，然后需要预测后续动作，继续完成任务。

可以理解为：

```text
给定：
已经发生的 Commander / Follower 对话
已经执行过的一部分动作
当前第一人称观察
当前环境状态

要求：
从当前点继续执行动作
直到任务完成
```

EDH 的难点在于模型不是从零开始。它必须判断：

```text
任务目标是什么？
哪些子目标已经完成？
Commander 给过哪些线索？
当前还缺哪些状态变化？
下一步应该继续搜索、交互，还是停止？
```

如果模型没有正确理解历史，它可能会重复已经完成的动作，或者忽略 Commander 之前给出的关键提示。

### EDH 的输入

EDH instance 通常包含：

| 信息 | 作用 |
| --- | --- |
| 对话历史 | 提供任务目标、位置线索、纠错和协作信息 |
| 动作历史 | 告诉模型任务已经执行到哪里 |
| 当前视觉观察 | 告诉模型现在看到什么 |
| 当前状态 | 用于 simulator 继续执行和评测 |
| 目标状态变化 | 用于判断任务是否成功 |

实际建模时，模型可能使用图像特征、文本编码、历史动作编码和物体检测结果。入门阶段可以先关注概念流程，不必一开始就实现完整模型。

### EDH 的输出

模型输出的是后续动作序列。例如：

```text
MoveAhead
RotateRight
PickupObject(Potato)
PutObject(Pot)
ToggleObjectOn(StoveBurner)
Stop
```

这些动作会在 AI2-THOR 中真实执行。评测不是看它们是否和人类动作逐步完全一致，而是看执行后环境状态是否满足任务要求。

## TfD：Trajectory from Dialog

TfD 表示 Trajectory from Dialog。它关注的是：给定完整对话，模型是否能生成完成任务所需的动作轨迹。

可以理解为：

```text
给定：
完整 Commander / Follower 对话

要求：
生成一条能在环境中完成任务的动作轨迹
```

TfD 更强调把整段对话转化为计划。完整对话中可能包含：

```text
初始任务目标
中途失败
替代方案
位置提示
完成确认
```

模型需要识别哪些内容真正影响动作，哪些只是礼貌回应或状态报告。

### TfD 与 EDH 的区别

| 维度 | EDH | TfD |
| --- | --- | --- |
| 起点 | 中间状态 | 通常从完整对话出发 |
| 重点 | 接续执行 | 从对话恢复整条轨迹 |
| 历史信息 | 部分历史和当前状态 | 完整对话信息 |
| 常见错误 | 不知道任务进度、重复旧动作 | 抽取错目标、忽略后期纠错 |

如果 EDH 测的是“接手能力”，TfD 测的就是“从对话恢复计划”的能力。

## TATC：Two-Agent Task Completion

TATC 是最完整的设置。它不只要求一个 Follower 模型执行动作，还要求建模 Commander 与 Follower 之间的协作。

可以理解为：

```text
Commander 模型：
根据任务目标和可见信息生成指导语言

Follower 模型：
根据语言、视觉观察和动作历史执行环境动作

双方持续交互：
语言 -> 行动 -> 新观察 -> 新语言 -> 新行动
```

TATC 更接近真实人机协作场景，因为系统不能假设完整对话已经提前给定。它需要决定什么时候说话、说什么、如何根据对方回应更新计划。

## TATC 的难点

TATC 同时包含语言生成、视觉理解、动作执行和协作策略，因此难度更高。

常见挑战包括：

```text
Commander 是否知道当前应该提供什么线索？
Follower 是否会在不确定时提问？
双方是否能避免重复无效对话？
语言是否足够具体，能转化为动作？
Follower 是否能把 Commander 的提示 grounded 到物体和位置？
```

在 TATC 中，失败可能来自任意一方。Commander 说得不清楚会导致 Follower 迷路；Follower 不提问会导致任务卡住；双方对任务阶段理解不一致，也可能造成重复动作。

## 三个 benchmark 的学习顺序

对于入门读者，建议按下面顺序学习：

```text
先看 TfD：
理解完整对话如何对应动作轨迹

再看 EDH：
理解如何从中间状态接续任务

最后看 TATC：
理解完整双 agent 协作设置
```

如果从实现角度看，通常先跑通官方 SampleModel 的 EDH inference 和 evaluation，再逐步理解 TfD 和 TATC。

## Benchmark 与数据文件的关系

三个 benchmark 都不是凭空定义的，它们都从 TEACh game session 中构造。

```text
完整 game session
├── 可以切分出 EDH instances
├── 可以整理成 TfD instances
└── 可以用于研究 TATC 中的双 agent 协作
```

这也是为什么理解上一节的数据结构很重要。只有知道原始 game session 记录了哪些信息，才能理解不同 benchmark 为什么这样设计。

## 失败案例举例

下面是三个设置中常见失败方式：

| 设置 | 失败方式 | 说明 |
| --- | --- | --- |
| EDH | 重复已经做过的动作 | 没有正确追踪历史对话和动作 |
| EDH | 过早 Stop | 误以为任务已经完成 |
| TfD | 忽略后期纠错 | 只记住初始任务，没有利用完整对话 |
| TfD | 生成动作顺序不合理 | 没有把对话转换成可执行计划 |
| TATC | Commander 指导模糊 | Follower 难以落地到具体物体或位置 |
| TATC | Follower 不提问 | 不确定时继续盲目探索，导致失败 |

这些失败往往不是单点错误，而是语言理解、视觉 grounding、计划和执行共同作用的结果。

## 与前面几个 benchmark 的关系

和前面的 benchmark 对比时，可以这样看：

| Benchmark | 主要评测对象 | TEACh 中对应的进一步挑战 |
| --- | --- | --- |
| OmniNavBench | 多类型导航任务 | TEACh 在导航外增加对话协作和物体状态变化 |
| Habitat Challenge | 标准化导航和重排挑战 | TEACh 更强调任务型自然语言和中途协作 |
| AI2-THOR / RoboTHOR | 可交互环境和对象操作 | TEACh 使用类似交互环境，但加入人类对话轨迹 |
| ALFRED / DialFRED | 长程语言指令和主动提问 | TEACh 更系统地定义 Commander / Follower 协作和多 benchmark 设置 |

因此，TEACh 可以作为从“看见并行动”走向“对话、协作并行动”的重要章节。

## 本节小结

EDH、TfD 和 TATC 是理解 TEACh 的三把钥匙：

```text
EDH 关注从对话历史中接续执行
TfD 关注从完整对话恢复动作轨迹
TATC 关注 Commander 和 Follower 的完整协作
```

三个 benchmark 共同把自然语言、视觉观察、动作执行和任务状态连接起来，使 TEACh 成为研究对话式具身智能的重要平台。

