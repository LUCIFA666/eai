# 3.2 场景、动作、观测与任务

## 目标

AI2-THOR 的核心不是单个任务，而是一套可交互的环境接口。Agent 可以在室内场景中移动、旋转、观察、拾取物体、打开容器，并通过返回的 event 获取图像和 metadata。

本节主要介绍 AI2-THOR 中的场景类型、动作空间、观测数据和常见任务形式。

## 场景类型

iTHOR 中的场景主要是家庭室内环境。典型场景包括：

```text
Kitchen
Living Room
Bedroom
Bathroom
```

这些场景不是简单贴图，而是包含大量可交互对象和语义信息。例如厨房中可能有冰箱、微波炉、锅、盘子、杯子和水槽；客厅中可能有沙发、电视、茶几和遥控器；卧室中可能有床、台灯和书桌；卫生间中可能有马桶、洗手池和镜子。

场景的作用不只是提供背景，而是决定任务难度：

```text
房间布局影响路径规划
物体分布影响目标搜索
遮挡关系影响视觉识别
可交互属性影响任务执行
```

例如，同样是寻找杯子，在厨房中可能比较容易，因为杯子通常出现在柜台或水槽附近；在客厅中则可能需要根据桌子、沙发和茶几等上下文进行搜索。

## 动作空间

AI2-THOR 中的 agent 通过动作与环境交互。常见动作可以分为三类：

| 动作类别   | 例子                                                     | 作用             |
| ------ | ------------------------------------------------------ | -------------- |
| 导航动作   | MoveAhead、RotateLeft、RotateRight、LookUp、LookDown       | 改变 agent 位置和视角 |
| 物体交互动作 | PickupObject、PutObject、OpenObject、CloseObject          | 改变物体位置或状态      |
| 状态动作   | ToggleObjectOn、ToggleObjectOff、SliceObject、BreakObject | 触发物体状态变化       |

最基础的导航动作通常包括：

```text
MoveAhead
RotateLeft
RotateRight
LookUp
LookDown
Done / Stop
```

这些动作类似于很多导航 benchmark 中的离散动作空间。Agent 每一步选择一个动作，环境返回新的观察结果。

物体交互动作则让 AI2-THOR 比纯导航环境更丰富。例如 agent 可以：

```text
拾取杯子
打开冰箱
把苹果放进碗里
打开微波炉
关闭柜门
打开灯
```

这类动作使 AI2-THOR 适合研究 embodied reasoning 和 object interaction。

## Observation：agent 能看到什么

AI2-THOR 每一步会返回一个 event。Event 中包含当前视觉观测和环境状态信息。

常见观测包括：

| 观测                    | 含义                |
| --------------------- | ----------------- |
| RGB frame             | 第一人称彩色图像          |
| Depth frame           | 深度图，用于判断距离        |
| Instance segmentation | 实例分割结果            |
| Semantic segmentation | 语义分割结果            |
| Metadata              | 场景、物体、位置、状态等结构化信息 |

可以简单理解为：

```text
RGB：
agent 当前看到的画面

Depth：
画面中各位置到 agent 的距离

Segmentation：
每个像素属于哪个物体或类别

Metadata：
环境中物体的结构化状态信息
```

与普通图像任务不同，AI2-THOR 的 observation 会随着动作变化。Agent 转头、前进、靠近物体后，看到的图像都会改变。

```text
当前位置看到一部分房间
-> MoveAhead
-> 视角接近目标
-> RotateRight
-> 看到新的区域
-> PickupObject
-> 物体状态变化
```

这种连续变化是 embodied AI 的关键。

## Metadata 的作用

Metadata 是 AI2-THOR 很重要的组成部分。它记录了当前场景中大量结构化信息，例如：

```text
agent 当前位姿
每个物体的位置
每个物体是否可见
每个物体是否可拾取
每个物体是否打开
每个物体是否被切换开关
动作是否成功
失败原因是什么
```

对于调试和教学来说，metadata 非常有用。它可以帮助我们确认：

```text
agent 是否真的移动了
物体是否在当前视野中
动作为什么失败
目标物体距离 agent 多远
物体状态是否发生变化
```

例如，agent 尝试拾取一个杯子，如果动作失败，可以通过 metadata 查看失败原因：可能是物体不可见、距离太远，或者该物体本身不可拾取。

## ObjectNav：目标物体导航

ObjectNav 是 AI2-THOR / RoboTHOR 中很常见的任务。Agent 会被给定一个目标物体类别，例如：

```text
Mug
Apple
Chair
Television
Toilet
Sofa
```

任务要求 agent 在环境中移动，找到该类别物体，并在合适距离内停止。

ObjectNav 的难点在于目标位置未知。Agent 需要根据视觉观察和场景常识主动搜索。

例如：

```text
目标是 Mug：
可能在厨房柜台、餐桌或水槽附近

目标是 Television：
可能在客厅墙面或电视柜附近

目标是 Toilet：
通常在卫生间
```

ObjectNav 主要考察：

```text
物体识别
语义场景理解
主动探索
路径规划
停止判断
```

如果 agent 只会随机移动，很难高效找到目标。好的策略通常需要利用场景常识和历史观察。

## PointNav：目标点导航

PointNav 是目标点导航任务。Agent 的目标不是物体类别，而是一个空间位置或相对位移。

例如：

```text
向前移动若干距离
移动到某个坐标附近
回到指定位置
```

PointNav 更强调几何空间理解。Agent 需要估计自己和目标之间的相对关系，并规划可行路径。

PointNav 主要考察：

```text
位置估计
路径规划
避障
动作执行
到达判断
```

相比 ObjectNav，PointNav 对语义识别要求较低，但对空间定位和运动控制要求更直接。

在学习 AI2-THOR 时，可以先从 PointNav 或简单移动动作开始，再逐步理解 ObjectNav 和物体交互任务。

## Object Interaction：物体交互任务

AI2-THOR 的特色之一是丰富的物体交互。Agent 不只是到达目标附近，还可以改变物体状态。

例如：

```text
PickupObject：
拾取可拿起的物体

PutObject：
将手中物体放到指定位置

OpenObject / CloseObject：
打开或关闭柜门、冰箱、微波炉等

ToggleObjectOn / ToggleObjectOff：
打开或关闭灯、电视、炉灶等

SliceObject：
切开可切割物体

BreakObject：
打碎可破坏物体
```

这些动作使 AI2-THOR 可以构造更复杂的任务：

```text
找到一个苹果
-> 拿起苹果
-> 放进碗里

找到杯子
-> 放进微波炉
-> 关上微波炉门

找到灯
-> 打开灯
```

这类任务比纯导航更难，因为 agent 既要找到物体，也要满足动作执行条件。

## 从任务到 episode

无论是导航还是交互任务，本质上都可以表示为一个 episode。

一个 episode 通常包括：

```text
选择场景
-> 初始化 agent 位置
-> 指定任务目标
-> agent 连续接收 observation
-> agent 输出 action
-> 环境返回 event
-> 判断是否成功或终止
```

这种形式和 RLBench 中的 task episode 有相似之处，但 AI2-THOR 更强调房间级探索和物体状态变化，而 RLBench 更强调机械臂任务和专家 demonstration。

可以把 AI2-THOR 的 episode 理解为：

```text
agent 在房间里执行一段连续行为
```

这段行为可能只是移动到目标点，也可能包括寻找物体、拾取物体、放置物体或改变物体状态。

## 本节小结

AI2-THOR 的核心由场景、动作、观测和任务组成。场景提供室内空间和物体，动作让 agent 能移动和交互，observation 和 metadata 让 agent 感知当前环境状态，任务则规定 agent 需要完成什么目标。
