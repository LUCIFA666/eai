# 5.5 评测指标与结果分析

## 目标

TEACh 的评测不只关注最终任务是否完成，也关注模型是否能根据对话历史理解当前状态、正确预测后续动作、处理物体交互并恢复错误。

本节主要介绍 TEACh 的评测思路、常见指标、失败类型和结果分析方式。

## 评测的整体思路

TEACh 的评测围绕任务执行结果展开。模型需要根据输入的对话历史、视觉观察或完整对话，输出动作序列，并在 AI2-THOR 环境中执行。

评测关注几个问题：

```text
任务是否最终完成？
模型是否完成了关键状态变化？
执行路径是否高效？
是否正确利用了对话历史？
是否在 seen / unseen 场景中都稳定？
是否能处理物体约束和失败恢复？
```

与普通语言任务不同，TEACh 的输出不是一句文本，而是在环境中真正执行的一串动作。因此，评测结果既反映语言理解，也反映视觉 grounding、导航、物体交互和任务规划。

## Success Rate

Success Rate 表示任务是否最终成功完成。

在 TEACh 中，成功通常依赖最终环境状态是否满足任务要求。例如：

```text
Boil Potato：
土豆是否被正确煮好

Make Coffee：
咖啡制作相关物体和状态是否满足任务目标

Clean Object：
目标物体是否被清洗并放到正确位置
```

Success Rate 是最直观的指标，但也很严格。一个模型可能完成了大部分步骤，只在最后放置位置或状态变化上失败，最终仍然会被记为失败。

## Goal-Condition Success

TEACh 任务常常包含多个 goal condition。Goal-condition success 用于衡量模型完成了多少关键条件。

例如一个任务可能包含：

```text
找到目标物体
拿起目标物体
改变物体状态
放到指定位置
```

即使完整任务失败，模型也可能完成其中一部分条件。

这个指标可以帮助区分：

```text
完全没有推进任务
和
完成了一部分任务，但最终没有全部满足
```

在长程任务中，这种中间进展分析非常重要。

## Path Length 与 Efficiency

TEACh 中也会关注动作序列长度和路径效率。

如果两个模型都完成任务：

```text
模型 A：
用较少动作完成

模型 B：
绕了很久才完成
```

模型 A 通常更高效。

路径或动作效率可以反映模型是否真正理解任务流程，而不是依赖随机探索。例如，模型如果反复打开关闭同一个容器、在房间中来回走动，可能最终也接近目标，但执行效率很差。这类行为在真实机器人中会增加时间成本和失败风险。

## EDH 结果阅读

EDH 的重点是从中间状态接手任务。

阅读 EDH 结果时，需要关注：

```text
模型是否理解已有对话历史
模型是否知道当前任务阶段
模型是否能接着完成剩余步骤
模型是否重复已经完成的动作
模型是否忽略 Commander 已经给出的线索
```

如果 EDH 成功率低，可能说明模型没有正确利用历史对话，或者无法从当前状态恢复任务进度。

典型失败包括：

```text
重复寻找已经找到的物体
重新执行已经完成的步骤
忽略 Commander 的位置提示
无法判断下一步该做什么
```

## TfD 结果阅读

TfD 的重点是从完整对话生成完整执行轨迹。

阅读 TfD 结果时，需要关注：

```text
模型是否正确提取任务目标
是否能从对话中恢复执行顺序
是否能处理 Commander 的纠错和替代方案
是否生成了合理的长程动作序列
```

如果 TfD 表现较差，说明模型可能不能把整段对话转化为可执行计划。

例如，Commander 在对话后半段给出替代方案：

```text
Use a cup to fill the pot with water.
```

如果模型忽略这句话，仍然执行原本失败的动作，就说明它没有正确整合对话中的关键更新。

## TATC 结果阅读

TATC 更关注两个 agent 的协作质量。

分析 TATC 时，需要同时考虑 Commander 和 Follower：

```text
Commander 是否给出清晰指导？
Follower 是否正确执行？
Follower 是否在不确定时提问？
Commander 是否能回答关键问题？
双方是否能从错误中恢复？
```

TATC 的失败可能来自任意一方。

例如：

```text
Commander 指令模糊
Follower 没有提问
Commander 没有纠正错误
Follower 执行动作失败
双方对任务阶段理解不一致
```

因此，TATC 不只是 action prediction benchmark，更接近完整人机协作 benchmark。

## 常见失败类型

TEACh 的失败通常可以分为几类：

| 失败类型 | 表现 |
| --- | --- |
| Dialogue Understanding Error | 没有理解 Commander 的目标或提示 |
| History Tracking Error | 忘记对话中已经给出的线索 |
| Navigation Error | 没有走到正确区域 |
| Object Grounding Error | 找错物体或没有识别目标物体 |
| Interaction Error | 拿取、放置、打开、关闭或切换状态失败 |
| State Change Error | 没有完成加热、清洗、煮沸等状态变化 |
| Recovery Error | 出错后没有通过对话或动作恢复 |
| Stop Error | 没有在任务完成后正确结束 |

这些失败往往会叠加出现。例如，模型忽略 Commander 提供的位置线索，导致导航到错误区域；随后找不到目标物体，最终无法完成状态变化。

## Seen 与 Unseen

TEACh 的结果也需要区分 seen 和 unseen 设置。

```text
Seen：
环境或任务分布更接近训练数据

Unseen：
需要泛化到未见过的场景或任务实例
```

如果 seen 表现明显高于 unseen，说明模型可能依赖训练场景中的固定布局、对话模式或物体分布。

对于对话式具身任务来说，unseen 更困难，因为模型需要同时泛化：

```text
新场景布局
新物体位置
新对话表达方式
新任务组合
```

## 对话行为分析

TEACh 后续加入的 dialog act annotation 可以帮助分析每句对话的作用。

例如，可以观察：

```text
Commander 的指令是否清楚
Follower 的问题是否出现在合理时机
回答是否真正帮助后续动作
纠错是否被模型利用
完成确认是否对应真实环境状态
```

如果模型能识别对话行为，就可以更好地判断当前语言是在给指令、回答问题、纠错还是确认完成。

这对任务执行很有帮助，因为不同对话行为对应不同决策：

```text
指令：
更新任务目标

位置提示：
更新搜索区域

纠错：
修改当前计划

确认：
判断是否进入下一阶段
```

## 与前面几个 benchmark 的结果阅读差异

TEACh 的结果阅读方式和前面几个 benchmark 有明显差异。

| Benchmark | 结果阅读重点 |
| --- | --- |
| OmniNavBench | 多类导航任务在组合 episode 中的连续执行和跨形态泛化 |
| Habitat Challenge | ObjectNav、ImageNav、Rearrangement 的 success、SPL 和 challenge 排名 |
| AI2-THOR / RoboTHOR | 室内交互、ObjectNav、sim-to-real 和动作执行结果 |
| ALFRED / DialFRED | 语言指令到长程动作序列，以及主动提问是否帮助任务完成 |
| TEACh | 对话历史如何影响任务执行，以及 Commander / Follower 协作是否推动任务完成 |

TEACh 的失败不一定来自单个动作，也可能来自对话理解、历史线索丢失、协作失败或错误恢复失败。因此分析 TEACh 结果时，需要同时看 dialogue、visual observation、action sequence 和 final state。

## 结果分析顺序

阅读 TEACh 结果时，可以按下面顺序分析：

```text
先看完整任务成功率
-> 再看 goal-condition 进展
-> 分析 EDH / TfD / TATC 的差异
-> 查看 seen / unseen 差距
-> 分析对话历史是否被正确利用
-> 查看具体失败类型
```

这种分析方式比单纯看排行榜更有用。因为 TEACh 的目标不是只证明哪个模型最高分，而是帮助研究者定位模型在对话理解、任务执行、状态变化和协作恢复中的短板。

## 本节小结

TEACh 的评测重点在于对话式具身任务执行。模型不仅要理解环境，还要理解 Commander / Follower 的历史对话，并将对话信息转化为后续动作。

从结果分析角度看，TEACh 的价值在于揭示语言协作、视觉 grounding、长程任务执行和错误恢复之间的关系。它比普通导航或静态指令跟随任务更接近真实人机协作场景。

