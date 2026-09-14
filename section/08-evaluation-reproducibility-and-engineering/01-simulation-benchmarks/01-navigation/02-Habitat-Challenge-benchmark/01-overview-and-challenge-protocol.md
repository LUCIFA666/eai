# 2.1 概览与挑战协议

## 目标

Habitat Challenge 是 AI Habitat 平台中的公开评测任务集合，主要用于评估 embodied agent 在三维仿真环境中的导航、感知、交互和任务完成能力。

本节主要介绍 Habitat Challenge 的基本定位、挑战形式和评测流程。理解这一节后，可以更清楚地看出：为什么具身智能 benchmark 不只是下载数据集做预测，而是需要在环境中运行 agent。

## Habitat Challenge 的基本定位

Habitat Challenge 是面向 embodied AI 的年度挑战任务。它依托 Habitat-Sim 和 Habitat-Lab 构建三维仿真环境、任务接口和评测协议，用于比较不同 agent 在相同任务设定下的表现。

和传统视觉任务不同，Habitat Challenge 中的 agent 通常需要在环境中连续执行动作。例如，agent 需要从初始位置出发，根据目标信息移动、观察、避障，并在合适时机停止或完成任务。

可以简单理解为：

```text
传统静态数据集：
输入图像或文本
-> 模型输出预测结果
-> 计算准确率

Habitat Challenge：
初始化三维环境
-> agent 接收第一人称观测
-> agent 连续输出动作
-> 环境状态随动作变化
-> 根据完整 episode 计算指标
```

这使得 Habitat Challenge 更接近真实机器人任务。模型不能只看一张图做判断，而是需要在环境中主动移动、不断观察并调整策略。

## 上传代码而不是上传预测结果

Habitat Challenge 的一个重要特点是：参赛者提交的是 agent 代码，而不是静态预测文件。

这意味着评测系统会真正运行参赛者的 agent，让它在测试环境中完成任务。Agent 每一步会根据当前 observation 输出 action，仿真器再根据 action 更新位置和视角。

流程可以理解为：

```text
提交 agent 代码
-> 评测服务器加载测试场景
-> agent 在未见过的环境中运行
-> 系统记录完整 episode
-> 根据评测指标生成结果
```

这种方式能够考察 agent 的闭环决策能力。因为每一步动作都会影响下一步看到的画面，所以早期错误可能会影响后续整个任务。

## 未见环境中的泛化评测

Habitat Challenge 通常强调在 unseen environments 中评测。也就是说，测试场景和训练场景不同，agent 不能只记住训练环境中的路线和物体位置。

这种设定主要考察泛化能力：

```text
agent 是否真的学会了导航策略？
agent 是否能适应新的房间布局？
agent 是否能在没见过的环境中寻找目标？
agent 是否能处理不同视觉纹理和遮挡关系？
```

对于具身智能来说，泛化能力非常重要。真实机器人部署时，遇到的家庭、办公室或公共空间不会和训练环境完全一致。如果模型只能在固定场景中表现好，就很难说明它具有真实应用价值。

## Habitat-Sim、Habitat-Lab 与 Challenge 的关系

理解 Habitat Challenge 时，需要区分三个概念：

| 组成 | 作用 |
| --- | --- |
| Habitat-Sim | 高性能 3D 仿真器，负责场景加载、渲染、物理和传感器输出 |
| Habitat-Lab | 高层任务库，负责定义任务、配置 agent、训练和评测 |
| Habitat Challenge | 公开评测协议，把任务、数据、规则和排行榜组织起来 |

三者之间的关系可以写成：

```text
Habitat-Sim 提供仿真环境
Habitat-Lab 定义任务和训练评测接口
Habitat Challenge 提供统一评测入口
```

例如，ObjectNav 和 ImageNav 等任务可以在 Habitat-Lab 中定义，底层运行时由 Habitat-Sim 提供场景渲染和传感器观测，最终通过 challenge 协议进行在线评测和排名。

## Challenge 页面和任务年份

Habitat Challenge 不同年份的任务会有所变化。早期任务更集中在 PointNav 和 ObjectNav，后续逐渐加入 ImageNav、Rearrangement 等更复杂任务。

可以大致理解为：

| 任务方向 | 关注点 |
| --- | --- |
| PointNav | 移动到指定相对坐标或目标点 |
| ObjectNav | 根据物体类别寻找目标物体 |
| ImageNav | 根据目标图像寻找对应实例 |
| Rearrangement | 移动物体，使环境从初始状态变成目标状态 |

因此，阅读 Habitat Challenge 时不能只看一个年份的页面，而要结合不同年份理解它的发展方向：从基础导航逐步扩展到视觉目标导航、实例导航和移动操作。

## 总览示意

![Habitat overview](assets/habitat-overview.gif)

图中展示了 Habitat 平台中的 agent 与三维环境交互过程。Agent 通过第一人称观测理解环境，并根据任务目标输出动作。与静态数据集不同，Habitat 中的输入会随着 agent 的移动不断变化，因此更适合研究闭环具身决策。

## 本节小结

Habitat Challenge 的核心价值在于，它把具身智能评测从静态预测扩展为环境中的连续决策。Agent 需要在未见过的三维环境中根据第一人称观测完成任务，评测结果反映的不只是视觉识别能力，也包括导航、规划、泛化和动作执行能力。
