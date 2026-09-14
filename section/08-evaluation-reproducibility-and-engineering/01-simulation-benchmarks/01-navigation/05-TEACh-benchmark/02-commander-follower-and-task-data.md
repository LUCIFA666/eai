# 5.2 Commander / Follower 与任务数据

## 目标

本节介绍 TEACh 的数据组织方式。重点不是先训练模型，而是先理解一个 TEACh episode 里到底记录了什么：谁在说话、谁在行动、环境如何变化，以及这些信息如何被转换成 EDH、TfD 和 TATC benchmark 的输入。

## 两个角色的视角差异

TEACh 的 Commander 和 Follower 并不是两个对称角色。它们看到的信息不同，承担的任务也不同。

| 角色 | 可见信息 | 主要能力 | 典型问题 |
| --- | --- | --- | --- |
| Commander | 任务目标、部分环境线索、目标物体信息 | 用语言指导 Follower | 如何给出清晰、有用、不过度冗余的指导 |
| Follower | 第一人称视觉观察、历史对话、自己已执行动作 | 在环境中导航和操作物体 | 如何把语言和视觉状态转化为动作 |

Commander 更像一个远程协作者，知道任务目标和环境中的重要信息，但不能直接操作世界。Follower 更像机器人本体，能执行动作，但信息更局部。

这种信息不对称是 TEACh 的核心。对话之所以重要，正是因为 Follower 无法直接访问 Commander 的全部知识。

## Game Session

TEACh 中一个完整的人类协作过程通常称为 game session。它可以理解为一条完整轨迹，里面交织了：

```text
任务目标
场景初始化信息
Commander utterance
Follower utterance
Follower action
环境状态变化
最终任务结果
```

这些 game session 是后续 benchmark 的基础。EDH 会从中间状态截取，TfD 会使用完整对话，TATC 则把 Commander 和 Follower 都建模出来。

## Dialogue

TEACh 的 dialogue 是任务过程的一部分，而不是事后说明。每一句话都可能影响后续动作。

常见对话内容包括：

| 类型 | 例子 | 对 Follower 的意义 |
| --- | --- | --- |
| 任务目标 | Please make coffee. | 设定最终目标 |
| 位置提示 | The mug is on the counter. | 缩小搜索空间 |
| 操作建议 | Use the sink to fill the cup. | 提供下一步策略 |
| 纠错 | No, use the white mug. | 修正当前计划 |
| 完成确认 | That is done. | 判断是否结束或进入下一阶段 |

在建模时，模型通常需要把这些话和视觉输入、动作历史一起编码。仅做文本分类通常不够，因为同一句话在不同环境状态下可能对应不同动作。

## Action

Follower 在 AI2-THOR 环境中执行动作。动作可以粗略分为几类：

| 动作类别 | 示例 | 说明 |
| --- | --- | --- |
| 导航动作 | MoveAhead、RotateLeft、LookUp | 改变 agent 位姿或视角 |
| 物体交互 | PickupObject、PutObject、OpenObject | 与可交互物体发生关系 |
| 状态改变 | ToggleObjectOn、SliceObject、PourObject | 改变物体或设备状态 |
| 停止动作 | Stop | 表示模型认为任务完成 |

动作不是孤立标签。它们会改变环境状态，也会影响下一帧视觉观察。例如，打开冰箱后可以看到内部物体，拿起杯子后 agent 的手中状态会改变。

## State Change

TEACh 的任务成功通常不是看语言输出是否相似，而是看环境状态是否满足目标。比如：

```text
目标：煮土豆
关键状态变化：
土豆被找到
土豆被放入合适容器
容器中有水
加热设备被正确使用
土豆最终处于 cooked / boiled 相关状态
```

实际评测会根据任务定义和 episode 中的目标状态，判断模型是否完成了必要的 state changes。这样可以避免只看动作序列表面相似，却没有真正完成任务的问题。

## 数据目录的典型结构

通过官方 `teach_download` 下载后，数据通常被组织成类似结构：

```text
teach-dataset/
├── games/
├── edh_instances/
├── tfd_instances/
├── images_and_states/
└── ...
```

其中：

| 目录 | 含义 |
| --- | --- |
| `games/` | 完整 game session，包含对话、动作和状态记录 |
| `edh_instances/` | EDH benchmark 使用的中间状态实例 |
| `tfd_instances/` | TfD benchmark 使用的从完整对话到轨迹实例 |
| `images_and_states/` | replay 后的图像、状态和辅助信息 |

入门时不需要马上读懂所有字段。更重要的是先把三层关系看清：

```text
完整 game session
-> 生成 EDH / TfD 等 benchmark 实例
-> 模型在 simulator 中执行并输出动作
-> evaluation 根据状态变化打分
```

## Game、Instance 与 Replay 的关系

TEACh 的数据文件和 simulator 运行可以分成三种层次：

| 层次 | 作用 |
| --- | --- |
| Game file | 记录人类完成任务的完整过程 |
| Benchmark instance | 把完整过程裁剪或重组为模型输入 |
| Replay output | 在 AI2-THOR 中重放后产生图像、状态和视频 |

例如，EDH instance 可能从一个完整 game session 的中间位置开始。它会给模型一段历史对话和当前状态，让模型继续执行剩余任务。

这和直接从头执行完整任务不同，因为模型需要理解“任务已经做到哪一步”，不能重复已经完成的步骤。

## 数据字段阅读方法

阅读 TEACh JSON 时，可以按下面顺序理解，而不是一上来逐字段硬啃：

```text
1. 先找任务类型和目标
2. 再看 dialogue 历史
3. 找 Follower 已经执行过的动作
4. 查看当前场景和物体状态
5. 判断后续还缺哪些 state changes
```

对入门读者来说，一个好习惯是把数据拆成四条时间线：

```text
语言时间线：谁说了什么
动作时间线：Follower 做了什么
视觉时间线：每步看到什么
状态时间线：环境发生了什么变化
```

TEACh 的难点就在于这四条时间线必须被联合理解。

## 与 AI2-THOR 的关系

TEACh 的底层环境来自 AI2-THOR。AI2-THOR 提供：

```text
室内房间场景
第一人称视觉观察
可交互物体
物体状态变化
离散动作接口
```

TEACh 在此基础上加入了人类对话、任务目标、game session 和 benchmark instance。可以这样理解：

```text
AI2-THOR：
提供可交互世界

TEACh：
在这个世界里记录对话协作任务
并把记录整理成 benchmark
```

因此，学习 TEACh 时如果已经了解 AI2-THOR，会更容易理解导航动作、物体交互和状态变化。但 TEACh 的独特之处在于对话历史和协作信息。

## 常见任务类型

TEACh 中的任务来自家庭场景，通常涉及找物体、移动物体、改变物体状态和组合多个步骤。例如：

| 任务类型 | 可能涉及的能力 |
| --- | --- |
| Make Coffee | 找杯子、使用咖啡机、处理液体或容器 |
| Boil Potato | 找土豆、找锅、加水、使用炉灶 |
| Clean Object | 找目标物体、移动到水槽、清洗并放置 |
| Prepare Breakfast | 多物体、多步骤、多个子目标组合 |

这些任务比单步导航更复杂，因为它们需要长期记忆和状态追踪。一个动作成功不代表任务成功，模型必须持续推进到最终目标状态。

## 本节小结

TEACh 的数据不是“文本指令 + 正确答案”这种简单形式，而是完整的对话式具身交互记录。理解 Commander / Follower、game session、dialogue、action 和 state change 的关系，是后面学习 EDH、TfD、TATC 的基础。

一句话概括：

```text
TEACh 数据记录的是人类如何通过对话协作完成具身任务，
benchmark 则把这些记录转化为模型需要继续执行或复现的任务。
```

