# 4.2 任务结构、语言指令与动作序列

## 目标

ALFRED 的任务不是简单的“找到某个物体”，而是由高层目标、分步语言指令、低层动作序列和环境状态变化共同构成。理解这些结构，才能看懂 ALFRED 的数据、模型输入输出和评测指标。

本节主要介绍 ALFRED 的任务类型、语言指令、动作空间、专家轨迹和错误来源。

## 任务类型

ALFRED 中的家庭任务通常围绕物体和容器展开。常见任务类型包括：

| 任务类型             | 示例             | 主要动作           |
| ---------------- | -------------- | -------------- |
| Pick & Place     | 把苹果放到桌子上       | 找物体、拿起、移动、放下   |
| Stack & Place    | 把物体放到另一个物体上    | 拿起、导航、放置       |
| Clean & Place    | 清洗物体后放到目标位置    | 拿起、到水槽、清洗、放置   |
| Heat & Place     | 加热物体后放到目标位置    | 拿起、到微波炉、加热、放置  |
| Cool & Place     | 冷却物体后放到目标位置    | 拿起、到冰箱、冷却、放置   |
| Examine in Light | 用灯光照亮或检查物体     | 找物体、移动、开灯或接近灯源 |
| Pick Two & Place | 拿两个目标物体并放到指定位置 | 多次搜索、拾取和放置     |

这些任务都不是单步完成，而是需要跨多个位置和多个物体状态。

例如 Clean & Place 可以拆成：

```text
找到目标物体
-> 拿起目标物体
-> 找到水槽
-> 清洗目标物体
-> 找到目标容器或表面
-> 放置目标物体
```

这类任务会同时考察 agent 的导航、物体识别、交互动作和状态判断。

## 高层目标与分步指令

ALFRED 中通常包含两类语言信息：

```text
Goal Instruction：
描述最终要完成的任务

Step-by-Step Instructions：
描述完成任务所需的中间步骤
```

例如：

```text
Goal:
Rinse off a mug and place it in the coffee maker.

Step-by-Step:
Walk to the coffee maker on the right.
Pick up the dirty mug from the coffee maker.
Turn and walk to the sink.
Wash the mug in the sink.
Pick up the mug and go back to the coffee maker.
Put the clean mug in the coffee maker.
```

高层目标给出任务整体语义，分步指令提供更细的执行线索。

可以简单理解为：

```text
Goal Instruction：
告诉 agent 最终要完成什么

Step-by-Step Instructions：
告诉 agent 大致应该按什么顺序做
```

对于模型来说，分步指令很重要，因为它能降低长程任务的规划难度。但即使有分步指令，agent 仍然需要在视觉环境中找到对应物体并正确执行动作。

## 语言 grounding

ALFRED 的语言指令必须和环境中的物体、位置和动作对应起来，这个过程可以称为 grounding。

例如：

```text
the dirty mug
-> 当前场景中的某个 mug

the sink
-> 厨房中的 sink basin

the coffee maker
-> countertop 附近的 coffee machine
```

如果 grounding 错误，后续动作就会失败。

常见 grounding 难点包括：

```text
同类物体有多个实例
目标物体初始时不可见
物体被遮挡
容器需要打开后才能看到内部物体
语言描述和视觉外观不完全一致
```

例如，任务要求拿起 “the mug from the coffee maker”，但场景中可能存在多个 mug。Agent 需要根据视觉线索和任务上下文判断哪一个才是正确目标。

## 低层动作序列

ALFRED 的输出通常是一串低层动作。动作可以分为导航动作和物体交互动作。

| 动作类别 | 典型动作                                             | 作用              |
| ---- | ------------------------------------------------ | --------------- |
| 导航动作 | MoveAhead、RotateLeft、RotateRight、LookUp、LookDown | 改变位置和视角         |
| 拾取放置 | PickupObject、PutObject                           | 拿起或放下物体         |
| 容器操作 | OpenObject、CloseObject                           | 打开或关闭冰箱、柜子、微波炉等 |
| 状态变化 | ToggleObjectOn、ToggleObjectOff、SliceObject       | 打开灯、启动设备或改变物体状态 |
| 结束动作 | Stop / Done                                      | 表示任务完成          |

动作序列可以表示为：

```text
MoveAhead
-> RotateRight
-> PickupObject
-> RotateLeft
-> MoveAhead
-> PutObject
-> Stop
```

这类低层动作要求模型持续观察环境并调整策略。一步错误动作可能导致后续全部偏离。

## 子目标与动作阶段

ALFRED 中的长程任务可以进一步拆成多个子目标。每个子目标通常对应任务中的一个中间阶段。

例如 Clean & Place：

| 子目标                           | 行为阶段   |
| ----------------------------- | ------ |
| Navigate to object            | 找到目标物体 |
| Pickup object                 | 拿起目标物体 |
| Navigate to sink              | 前往水槽   |
| Clean object                  | 清洗物体   |
| Navigate to target receptacle | 前往目标容器 |
| Put object                    | 放置物体   |

这种子目标结构对模型训练和结果分析都很有用。

如果一个 agent 最终任务失败，可以进一步判断它失败在哪个阶段：

```text
找不到目标物体
拿不起目标物体
找不到水槽
没有成功清洗
找不到最终容器
放置失败
```

相比只看最终成功率，子目标分析能更具体地暴露模型短板。

## 任务视频示例：检查物体

<video src="assets/alfred-look-at-object-demo.mp4" controls width="100%"></video>

如果视频无法播放，可以点击查看：[ALFRED look at object demo](assets/alfred-look-at-object-demo.mp4)

视频展示了一个“检查物体”类任务。Agent 需要根据语言目标找到相关物体，并通过导航和环境交互完成最终要求。这类任务体现了 ALFRED 中视觉导航和物体状态操作的结合。

## 任务视频示例：拾取与放置

<video src="assets/alfred-pick-and-place-demo.mp4" controls width="100%"></video>

如果视频无法播放，可以点击查看：[ALFRED pick and place demo](assets/alfred-pick-and-place-demo.mp4)

视频展示了一个 pick-and-place 风格任务。Agent 需要在房间中找到目标物体、移动到目标位置，并完成放置动作。相比单纯 ObjectNav，这类任务要求 agent 对物体、容器和动作结果保持连续理解。

## 专家轨迹

ALFRED 数据集中的 expert trajectory 记录了专家完成任务时的完整动作和观测。

一条轨迹通常包含：

```text
任务说明
分步语言指令
场景信息
每一步低层动作
每一步视觉观测
物体交互信息
任务成功标记
```

模型训练时，可以把轨迹整理成监督学习样本：

```text
当前图像 + 语言指令 + 历史动作
-> 下一步专家动作
```

也可以进一步引入子目标预测：

```text
当前图像 + 当前指令
-> 当前子目标
-> 下一步动作
```

专家轨迹的价值在于，它提供了从语言到动作的完整监督信号。

## 常见失败类型

ALFRED 的失败通常不是单一原因造成的，而是多种错误叠加。

常见失败包括：

| 失败类型   | 说明               |
| ------ | ---------------- |
| 导航失败   | agent 没有走到正确区域   |
| 目标识别失败 | 识别错物体或没有看到目标物体   |
| 交互失败   | 距离太远、视角不对或物体不可交互 |
| 状态变化失败 | 没有成功清洗、加热、冷却或开关  |
| 放置失败   | 目标容器不对或放置位置不满足条件 |
| 长程记忆失败 | 忘记已完成步骤或目标物体位置   |
| 停止失败   | 没有在任务完成后正确结束     |

这说明 ALFRED 不只是语言理解任务，也不是单纯视觉导航任务，而是完整家庭任务执行 benchmark。

## 本节小结

ALFRED 的任务由高层目标、分步语言指令、子目标、低层动作和环境状态变化组成。Agent 需要把自然语言映射成一串可执行动作，并在执行过程中持续检查视觉环境和物体状态。

理解任务结构后，就可以进一步看 ALFRED 的环境配置和数据准备方式。
