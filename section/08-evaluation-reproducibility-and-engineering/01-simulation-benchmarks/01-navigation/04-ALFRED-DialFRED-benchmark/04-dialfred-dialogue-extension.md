# 4.4 DialFRED：对话式指令扩展

## 目标

普通 ALFRED 中，agent 接收用户给出的任务指令，然后被动执行任务。DialFRED 在此基础上加入了对话能力，使 agent 可以主动向用户提问，并利用用户回答补充任务信息。

本节主要介绍 DialFRED 的任务动机、对话形式、QA 数据、questioner-performer 框架和它相比 ALFRED 的新增难点。

## 从单向指令到双向对话

在 ALFRED 中，通信方式通常是单向的：

```text
用户给出任务指令
-> agent 理解指令
-> agent 执行动作
```

这种设置假设用户一开始已经提供了足够清楚的任务信息。但真实场景中，用户指令经常是不完整或模糊的。

例如：

```text
把杯子放到桌上
```

这句话可能没有说明：

```text
哪个杯子？
桌子在哪里？
杯子长什么样？
我应该往哪个方向走？
```

如果 agent 只能被动执行，就可能因为信息不足而失败。

DialFRED 将这个过程改成双向交互：

```text
用户给出任务指令
-> agent 判断信息是否不足
-> agent 主动提问
-> 用户回答
-> agent 利用回答继续执行任务
```

这种设置更接近真实人机协作。机器人不一定要一次性理解所有内容，而是可以在不确定时寻求帮助。

## DialFRED 的基本形式

DialFRED 基于 ALFRED 构建，但为任务加入了问题和回答。Agent 可以在执行过程中提出与任务相关的问题。

典型问题包括三类：

| 问题类型 | 示例                             | 作用              |
| ---- | ------------------------------ | --------------- |
| 位置澄清 | Where is the mug?              | 帮助 agent 缩小搜索范围 |
| 外观澄清 | What does the mug look like?   | 帮助 agent 区分同类物体 |
| 方向澄清 | Which direction should I turn? | 帮助 agent 进行局部导航 |

这些问题不是闲聊，而是 task-relevant question。它们的目标是补充执行任务所需的信息。

例如：

```text
User:
Put the mug in the coffee maker.

Agent:
Where is the mug?

User:
The mug is on the counter near the sink.

Agent:
继续导航到水槽附近并寻找 mug。
```

这种交互可以降低语言和视觉不确定性。

## QA 数据

DialFRED 提供了人工标注的任务相关问答数据。每条 QA 通常和某个任务、某个子目标或某个执行阶段有关。

数据中可能包含：

```text
数据划分
任务 ID
trial ID
房间类型
原始 ALFRED 任务类型
子目标起止时间
问题类型
问题文本
回答文本
```

这些 QA 数据可以用于训练 questioner，也可以用于分析 agent 在不同阶段需要什么信息。

例如，在寻找目标物体阶段，位置问题更有帮助；在多个同类物体共存时，外观问题更有帮助；在局部导航阶段，方向问题更有帮助。

## Questioner-Performer 框架

DialFRED 的一个核心思想是把 agent 拆成两个部分：

```text
Questioner：
判断是否需要提问，以及应该问什么问题

Performer：
根据任务指令、视觉观测和回答信息执行动作
```

可以理解为：

```text
Questioner 负责获取信息
Performer 负责完成任务
```

执行流程可以写成：

```text
输入任务指令
-> agent 观察环境
-> questioner 判断是否需要提问
-> 用户或 oracle 返回答案
-> performer 利用答案生成动作
-> 环境更新
-> 继续执行任务
```

这种框架把“问问题”和“做任务”分开，有助于研究对话对 embodied task completion 的影响。

## Oracle Answer

在训练和评测中，DialFRED 可以使用 oracle 来回答 agent 的问题。Oracle 可以根据虚拟环境中的 ground-truth 信息生成回答。

例如，agent 问：

```text
Where is the mug?
```

Oracle 可以根据当前任务和场景信息回答：

```text
The mug is on the counter near the sink.
```

Oracle 的作用是减少人类实时参与，让模型可以在可控条件下评估“提问是否有帮助”。

需要注意的是，oracle answer 并不等于真实世界中的用户回答。在真实人机交互中，用户回答可能不完整、含糊或存在误差。但在 benchmark 中，oracle 能让研究者先分析对话机制本身是否有效。

## DialFRED 带来的新增能力要求

相比 ALFRED，DialFRED 不只是多了几句对话，而是增加了新的决策问题。

Agent 需要判断：

```text
当前信息是否足够？
是否值得提问？
应该问位置、外观还是方向？
用户回答和当前观测如何结合？
什么时候停止提问并继续执行？
```

如果 agent 随意提问，会浪费交互次数；如果 agent 不提问，又可能因为信息不足而失败。

因此，DialFRED 评估的不只是任务执行能力，也评估主动信息获取能力。

## 对话如何改善任务执行

对话主要在三个方面帮助 agent。

### 缩小搜索范围

如果目标物体不可见，位置回答可以帮助 agent 少走弯路。

```text
没有回答：
agent 可能随机搜索多个房间

有回答：
agent 可以优先前往 sink、countertop 或 table 附近
```

### 区分相似物体

如果场景中有多个同类物体，外观回答可以帮助 agent 选择正确实例。

```text
Question:
What does the mug look like?

Answer:
It is a white mug near the coffee machine.
```

### 修正局部导航

方向回答可以帮助 agent 在不确定下一步动作时调整方向。

```text
Question:
Which direction should I turn?

Answer:
Turn left and move toward the countertop.
```

这些回答能够补充视觉观测不足，降低长程任务中的不确定性。

## DialFRED 与 ALFRED 的区别

| 方面   | ALFRED           | DialFRED             |
| ---- | ---------------- | -------------------- |
| 通信方式 | 用户给指令，agent 被动执行 | agent 可以主动提问         |
| 输入信息 | 语言指令 + 视觉观测      | 语言指令 + 视觉观测 + QA 信息  |
| 主要难点 | 长程任务、视觉导航、物体交互   | 还需要判断何时提问、问什么、如何用回答  |
| 数据形式 | 专家轨迹和语言标注        | 在 ALFRED 基础上加入任务相关问答 |
| 研究重点 | 从语言到动作序列         | 对话式信息获取和任务执行         |

可以把 DialFRED 看作 ALFRED 的对话增强版本。它保留了 ALFRED 的家庭任务结构，但把 agent 从被动执行者扩展为能够主动沟通的执行者。

## 本节小结

DialFRED 的核心价值在于引入主动提问机制。它使 embodied agent 不再只是被动跟随指令，而是能够在信息不足时向用户请求帮助，并利用回答改善任务执行。

这种设置更接近真实家庭机器人场景：用户指令经常不完整，环境信息也可能不充分。一个更智能的 agent 应该能够判断不确定性，并通过对话获取关键线索。
