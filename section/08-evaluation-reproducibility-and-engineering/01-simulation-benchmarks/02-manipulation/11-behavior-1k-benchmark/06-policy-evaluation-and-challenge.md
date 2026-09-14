# 12.6 Policy 评测

## 目标

前面已经介绍了 BEHAVIOR-1K 的任务定义、场景物体状态，以及环境运行时的基本交互流程。本节关注最后一个问题：当我们把一个 policy 放进 BEHAVIOR-1K 后，应该如何理解它的评测结果？

读完本节后，你应该能够回答下面几个问题：

```text
Policy 在 BEHAVIOR-1K 评测中处在什么位置？
success 和 progress 的结果应该怎么分析？
Standard Track 和 Privileged Information Track 有什么区别？
Baseline 对初学者有什么参考价值？
阅读 Challenge 结果时应该注意什么？
```


## Policy 接入 BEHAVIOR-1K 的位置

在上一节中，我们已经看到 BEHAVIOR-1K 的基本运行链路：

```text
reset 环境
-> 得到 observation
-> 输入 policy
-> 输出 action
-> env.step(action)
-> 环境返回新 observation 和任务反馈
```

Policy 接入的位置就在中间：

```text
observation / task information
-> policy
-> action
```

也就是说，policy 的任务是根据当前环境观测和任务目标，决定下一步动作。对于 BEHAVIOR-1K 这种长程家务任务，policy 不只是要完成一个抓取动作，还需要连续做出多个决策。

例如：

```text
找到目标物体
-> 移动到目标物体附近
-> 抓取或操作物体
-> 找到目标位置
-> 放置物体或改变状态
-> 检查任务目标是否完成
```

所以 BEHAVIOR-1K 评测的不是单步动作预测，而是 policy 在复杂环境中的连续执行能力。

## 评测时真正关心什么

在 BEHAVIOR-1K 中，评测时最核心的不是训练 loss，而是 policy 放回环境后能不能完成任务。

可以把评测结果分成三层来看：

| 层次 | 关注点 |
| --- | --- |
| Success | 任务是否完全完成 |
| Progress | 目标条件完成了多少 |
| Failure case | 没完成时失败在哪里 |

其中，success 是最严格的指标。只要有关键目标条件没有满足，整个任务就可能被判定为失败。

但 BEHAVIOR-1K 的任务通常比较长，只看 success 有时不够。例如一个 agent 没有完全成功，但它可能已经完成了多个子目标。这时 progress 就很重要。

可以这样理解：

```text
success 关注最终是否全部完成
progress 关注中间完成了多少
failure case 帮助分析为什么没完成
```

## Success 和 Progress 怎么一起看

阅读 BEHAVIOR-1K 结果时，不建议只看一个 success 数字。更合理的是把 success 和 progress 放在一起分析。

| 现象 | 可能说明 |
| --- | --- |
| success 高，progress 高 | policy 能稳定完成任务 |
| success 低，progress 高 | 能完成部分子目标，但长程稳定性不足 |
| success 低，progress 低 | 感知、规划或动作执行可能都有明显问题 |
| progress 有提升但 success 不变 | policy 已经学到部分能力，但还没跨过完整成功门槛 |
| 某类任务 progress 明显低 | policy 可能不擅长该类场景、物体或状态变化 |

例如，一个整理任务包含多个目标物体。如果 policy 能移动其中一部分物体，但没有全部放到正确位置，那么 success 可能仍然是 0，但 progress 会反映它完成了一部分任务。

这也是长程 embodied AI 评测和简单抓取任务不同的地方：  
任务失败不一定意味着完全没有能力，可能只是某个子步骤不稳定。

## 为什么不能只看训练 loss

很多 policy 会用 imitation learning 训练。训练时常见目标是让模型输出的动作接近专家动作：

```text
policy action 接近 expert action
```

但训练 loss 低，不代表闭环评测成功率一定高。

原因是 BEHAVIOR-1K 的评测发生在环境里，policy 的每一步动作都会影响后续状态。一个小错误可能让物体偏离位置，后面 observation 也会跟着变化，最终导致任务失败。

常见问题包括：

| 问题 | 说明 |
| --- | --- |
| 闭环误差累积 | 一步动作偏差会影响后续所有状态 |
| 分布偏移 | policy 进入了 demonstration 中没有出现过的状态 |
| 长程依赖 | 前面的小失误会影响后面多个子目标 |
| 状态变化复杂 | 任务可能涉及打开、装满、清洁、加热等状态 |
| 接口不一致 | 训练和评测时 observation 或 action 表示不同 |

所以最终还是要把 policy 放回 BEHAVIOR-1K 环境中评测，看它是否真的完成任务。

## Standard Track 和 Privileged Information Track

在 Challenge 或正式评测中，经常会区分不同的信息使用设置。最常见的是 Standard Track 和 Privileged Information Track。

### Standard Track

Standard Track 通常只允许 policy 使用机器人正常传感器能够获得的信息，例如：

```text
RGB 图像
深度图
分割信息
机器人本体状态
任务指令
```

这种设置更接近真实机器人，因为真实机器人通常只能依靠自己的相机和传感器观察世界。

可以简单理解为：

```text
Standard Track = 只用机器人自己能看到的信息
```

### Privileged Information Track

Privileged Information Track 允许 policy 使用仿真器中的额外真值信息，例如：

```text
物体真实位置
完整场景状态
目标物体状态
机器人全局位姿
任务目标条件真值
```

这些信息在仿真环境中可以直接查询，但真实机器人不一定能直接获得。

可以简单理解为：

```text
Privileged Track = 可以使用仿真器提供的额外信息
```

## 两种 Track 为什么不能直接比较

Standard Track 和 Privileged Information Track 的难度不同，所以结果不能直接混在一起比较。

| Track | 能使用的信息 | 难度 | 更接近什么 |
| --- | --- | --- | --- |
| Standard Track | 机器人传感器观测 | 更难 | 真实机器人部署 |
| Privileged Track | 仿真器额外真值信息 | 相对容易 | 规划、诊断或上层决策实验 |

如果一个方法在 Privileged Track 表现很好，但在 Standard Track 表现一般，说明它可能比较依赖仿真器真值信息，还没有完全解决真实感知问题。

所以读结果时要先确认：

```text
这个方法属于哪个 track？
它用了哪些输入信息？
是否使用了仿真器真值？
```

否则不同方法之间的比较可能不公平。


## 一个完整 Policy Pipeline 通常包含什么

无论具体方法是 ACT、Diffusion Policy 还是 VLA，一个完整 policy pipeline 通常都包括下面几部分：

| 模块 | 作用 |
| --- | --- |
| Dataset | 读取 demonstration 或 rollout 数据 |
| Preprocess | 处理图像、状态、语言和动作 |
| Policy Model | 根据 observation 输出 action |
| Trainer | 训练模型参数 |
| Checkpoint | 保存和加载模型 |
| Evaluation Loop | 把 policy 放进环境中闭环执行 |
| Metrics | 统计 success、progress 和其他结果 |

可以把它压缩成：

```text
数据
-> 训练 policy
-> 保存 checkpoint
-> 加载 policy
-> 环境中评测
-> 输出 success / progress
```

BEHAVIOR-1K 主要提供任务、环境和评测协议；具体 policy 怎么训练，则取决于所使用的 baseline 或研究方法。

## Evaluation 输出怎么看

一次 evaluation 输出通常会包含：

```text
任务名称
episode 编号
是否成功
progress
执行步数
失败原因或调试信息
```

结果可能类似：

```text
Task: cleaning_table
Episode 0: success=False, progress=0.40
Episode 1: success=True, progress=1.00
Episode 2: success=False, progress=0.20

Average success: 0.33
Average progress: 0.53
```

阅读这类结果时，建议按下面顺序分析：

```text
先看 average success
-> 再看 average progress
-> 再看不同任务类别的差异
-> 最后看失败案例
```

例如：

| 结果现象 | 可能解释 |
| --- | --- |
| success 低但 progress 高 | 能完成部分子目标，但长程执行不稳定 |
| 某类任务明显更差 | policy 不擅长该类物体或状态变化 |
| episode 经常超时 | policy 可能探索效率低或规划能力弱 |
| 失败集中在最后一步 | 前面能力还可以，但收尾动作不稳定 |
| Privileged Track 明显更好 | 方法可能依赖额外真值信息 |

对于 BEHAVIOR-1K 这种长程任务，失败案例分析比单个平均分更有解释价值。

## 官方评测结果应该怎么读

阅读官方评测结果应该怎么读时，建议先确认这些问题：

```text
使用的是 Standard Track 还是 Privileged Track？
评测任务列表是否相同？
是否使用官方 demonstration？
是否使用额外真值信息？
指标是 success、progress，还是综合分数？
环境版本和任务版本是否一致？
```

不要只看排行榜名次。对于学习来说，更重要的是理解方法为什么表现好或不好。

例如：

```text
方法 A success 较高，但只在 Privileged Track
-> 说明它可能依赖额外状态信息

方法 B success 不高，但 progress 较高
-> 说明它能完成部分子目标，但长程稳定性不足

方法 C 在整理任务上表现好，在烹饪任务上表现差
-> 说明它可能擅长物体移动，但不擅长复杂状态变化
```

这样分析，才能真正看懂一个方法解决了什么能力，还没有解决什么能力。

## 评测时最容易出错的地方

### 1. 输入信息不一致

训练时使用的 observation，评测时也应该保持一致。  
如果训练时用 RGB + robot state，评测时却多了或少了某些输入，模型可能无法正常工作。

### 2. Action 表示不一致

不同 policy 的 action 形式可能不同，例如低层连续动作、高层 primitive 或动作 token。  
评测时必须保证 policy 输出能被环境正确解释。

### 3. 归一化方式不一致

训练时如果对图像、状态或动作做了归一化，评测时也必须使用相同的处理方式。

### 4. 混淆不同 Track

Standard Track 和 Privileged Track 使用的信息不同，不能直接比较最终分数。

### 5. 只看平均分，不看失败案例

长程任务失败原因很多。只看平均 success 可能看不出 policy 到底卡在哪里。



## 本节小结

BEHAVIOR-1K 的 policy 评测重点不是看模型在离线数据上拟合得多好，而是看它在环境中连续执行任务时能完成多少目标。

可以用一句话概括：

```text
Policy 评测关注闭环任务完成能力；success 看是否完全完成，progress 看完成了多少，而 Challenge 和 baseline 提供了统一比较方法的入口。
```