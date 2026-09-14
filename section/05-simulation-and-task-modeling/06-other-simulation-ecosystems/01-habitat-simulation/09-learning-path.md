# 新手学习路线

目标：给初学者一条可执行的 Habitat 学习顺序，避免一上来就被安装、数据下载、PPO 训练和复杂任务同时卡住。

Habitat 的学习难点不只是 API。它同时涉及数据集、仿真器、任务框架、训练库和评测指标。新手如果一开始就下载大数据集、跑完整训练，很容易出问题后不知道从哪里查。

更稳的路线是：先理解概念，再跑最小场景，再看 viewer，再跑简单任务，最后进入 ObjectNav、VLN、EQA 和 Rearrangement。

## 第一阶段：只理解生态，不急着运行

先把下面几个词说清楚：

| 概念 | 一句话解释 |
|---|---|
| Habitat-Sim | 底层 3D simulator，负责场景、agent、sensor 和仿真状态 |
| Habitat-Lab | 上层任务框架，负责 episode、task、measure、baseline |
| scene dataset | 3D 房间或建筑数据 |
| episode dataset | 任务实例数据 |
| sensor | agent 能看到或知道的信息 |
| action space | agent 能执行的动作集合 |
| measure | 评测指标 |

这一阶段不要急着训练。能把这些概念连成一条实验流程，就已经完成了第一步。

## 第二阶段：跑最小测试场景

下一步才是运行。建议从官方 test scenes 或小型示例开始，不要一上来下载 HM3D 全量数据。

你要验证的是：

```text
Python 环境能 import habitat_sim
测试 scene 能加载
agent 能初始化
RGB / depth observation 能返回
step 后状态会变化
```

如果这一步失败，先解决环境、安装、数据路径和渲染问题。不要跳到 Habitat-Lab 训练脚本，否则错误会更难定位。

## 第三阶段：用 viewer 看场景

viewer 的价值是让你用眼睛检查场景是否正常。它可以帮助你发现：

| 问题 | 说明 |
|---|---|
| 场景是否加载正确 | 黑屏、缺材质、路径错误都能很快发现 |
| navmesh 是否可用 | agent 是否能在场景中移动 |
| 语义是否可用 | semantic sensor 是否有合理输出 |
| 交互物体是否可操作 | ReplicaCAD 等场景能否打开抽屉或移动物体 |

不要把 viewer 当成最终实验工具。它是调试工具，用来确认数据和仿真基本正常。

## 第四阶段：跑 PointNav

PointNav 是最适合入门的任务。它目标简单，不要求理解物体语义，也不需要语言和物理交互。

这一阶段重点看：

1. `reset()` 返回了什么 observation。
2. `action_space` 里有哪些动作。
3. `step()` 后 reward、done、info 怎么变化。
4. success 和 SPL 怎么计算。
5. episode 为什么会结束。

如果 PointNav 都看不懂，不建议直接做 ObjectNav 或 Rearrangement。

## 第五阶段：跑 ObjectNav

ObjectNav 是第二个关键任务。它会引入语义目标和探索问题。

| 内容 | 为什么重要 |
|---|---|
| 目标类别 | agent 到底在找什么 |
| semantic 标注 | 目标类别是否能被数据集支持 |
| episode split | 泛化评估是否干净 |
| sensor 设置 | RGB / depth / semantic / GPS+Compass 会改变难度 |
| stop 动作 | 到目标附近后必须正确停止 |

ObjectNav 看懂后，你会真正理解 Habitat 里 scene dataset、episode dataset、sensor 和 metric 的关系。

## 第六阶段：再看 ImageNav、VLN 和 EQA

这三个任务都在 ObjectNav 的基础上增加了新的目标形式。

ImageNav 把目标从类别换成目标图像。你要关注图像如何采样、是否有歧义、是否和 agent 视角一致。

VLN 把目标换成自然语言指令。你要关注语言是否描述路径、场景中是否存在对应线索、评测指标是否只看终点还是也看路径贴合度。

EQA 把目标换成问题。你要关注 agent 是否需要主动探索，以及最后回答准确率和导航质量怎么一起解释。

## 第七阶段：最后进入 Rearrangement 和 Habitat 3.0

Rearrangement 和 Habitat 3.0 不适合作为第一站。它们会同时引入物理交互、物体状态、机器人 embodiment、任务分解、多智能体或人在环交互。

进入这一阶段前，至少应该已经能回答：

```text
当前 scene dataset 是什么？
当前 episode dataset 是什么？
agent 有哪些 sensor？
action space 是什么？
success 怎么定义？
SPL 或其他指标怎么解释？
```

如果这些问题还不清楚，先回到 PointNav 和 ObjectNav。

## 推荐路线图

| 阶段 | 学习目标 | 通过标准 |
|---|---|---|
| 生态概念 | 分清 Sim、Lab、dataset、episode | 能画出实验流程 |
| 最小运行 | 加载 test scene，返回观测 | 能打印 RGB / depth shape |
| viewer 调试 | 用可视化确认场景和传感器 | 能说明画面来自哪个 scene |
| PointNav | 理解导航任务和 SPL | 能解释 success 和 SPL 差别 |
| ObjectNav | 理解语义目标和 episode | 能写完整实验记录卡 |
| 扩展任务 | 看 ImageNav、VLN、EQA | 能说明目标形式差异 |
| 交互任务 | 看 Rearrangement / Habitat 3.0 | 能区分导航、操作和协作问题 |

## 常见学习误区

**误区一：先下载大数据集。**

不建议。先用 test scene 跑通环境，再决定下载哪个正式数据集。否则路径、许可、语义文件和下载中断会同时出现。

**误区二：先训练 PPO。**

不建议。训练慢，失败原因多。先用随机策略或简单脚本看懂 observation、action 和 info。

**误区三：只看 success。**

不够。导航任务至少还要看 SPL、路径长度和失败原因。

**误区四：把 Habitat 当真实机器人部署工具。**

Habitat 很适合研究和 benchmark，但真实机器人还需要控制、定位、传感器标定、安全和系统集成。

## 本页小结

学习 Habitat 要从简单到复杂：先分清生态层级，再跑最小场景，再看 PointNav，接着进入 ObjectNav，最后再扩展到 ImageNav、VLN、EQA、Rearrangement 和 Habitat 3.0。每一步都留下可检查证据，比盲目跑大训练更重要。

## 导航

- 上一页：[与其他仿真生态对比](08-comparison.md)
- 返回：[Habitat 简介](../01-habitat-simulation.md)
- 下一页：[Genesis](../02-genesis.md)

## 进一步阅读可以看：

- [Habitat-Lab documentation](https://aihabitat.org/docs/habitat-lab/)
- [Habitat-Sim documentation](https://aihabitat.org/docs/habitat-sim/)
- [Habitat-Sim supported datasets](https://github.com/facebookresearch/habitat-sim/blob/main/DATASETS.md)