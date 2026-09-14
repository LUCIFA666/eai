# 8.5.2.1 LeRobot 整体介绍

本页是 LeRobot 动手学习指南的 overview 页面，目标是帮助读者理解 LeRobot 是什么、它在具身智能训练流程中扮演什么角色，以及后续教程会围绕哪些核心模块展开。

## 学习目标
1. LeRobot 解决了具身智能中的什么问题？
2. 一个 LeRobot 训练流程通常包括哪些步骤？
3. LeRobot 支持哪些类型的 policy 模型？

## LeRobot 是什么

LeRobot 是 Hugging Face 推出的开源机器人学习框架，目标是降低机器人学习和具身智能模型训练的门槛。它将机器人数据集、数据可视化、策略模型训练、模型评估以及真实机器人 / 仿真环境部署整合到一个统一框架中。

在 LeRobot 中，机器人策略模型通常被称为 policy。一个 policy 的目标是根据当前观测信息，例如图像、机器人状态和语言指令，预测机器人下一步应该执行的动作。

## LeRobot 所解决的问题
在具身智能任务中，从数据采集到模型训练通常会遇到很多工程问题：

- 不同机器人数据格式不统一；
- 图像、状态、动作和时间戳难以对齐；
- 每个 policy 的训练脚本和数据接口不同；
- 训练完成后难以评估和部署；
- 自己收集的数据很难复用到其他模型上。

LeRobot 的作用就是尽可能把这些环节标准化，让研究者可以围绕统一的数据格式和训练接口，快速复现和比较不同机器人策略模型。



## LeRobot的整体流程
一个典型的 LeRobot 训练流程如下：

1. **准备数据集**：可以使用 Hugging Face Hub 上已有的 LeRobot 数据集，也可以使用自己采集的数据。
2. **统一成 LeRobotDataset 格式**：数据中通常包含图像、机器人状态、动作、时间戳和任务信息。
3. **检查数据与 stats**：在训练前，需要确认数据可以正常加载，图像可以解码，action/state 维度正确，并且 stats 可用。
4. **选择 policy**：根据任务类型选择 ACT、Diffusion Policy、SmolVLA、X-VLA、π0 等模型。
5. **启动训练**：使用 `lerobot-train` 启动训练，并根据显存调整 batch size 和训练步数。
6. **检查结果**：查看 loss、checkpoint、output_dir，并进一步做 eval 或 rollout。

## LeRobot 支持的 policy 类型

在 LeRobot 中，模型通常被称为 policy。根据任务形式和模型规模，可以大致分为三类：

| 类型 | 代表模型 | 适合场景 |
|---|---|---|
| 传统模仿学习 policy | ACT、Diffusion Policy、VQ-BeT | 入门复现、单任务操作、baseline 对比 |
| 强化学习 policy | TD-MPC、HIL-SERL | 需要交互式优化或强化学习的任务 |
| VLA / 通用机器人策略 | SmolVLA、X-VLA、π0、π0.5、GR00T | 多模态、多任务、语言条件机器人控制 |

本教程后续会优先关注可以实际跑通训练的模型，并按照"传统模仿学习 policy → VLA policy"的顺序展开。

## 导航

- 返回父页：[LeRobot](../08-lerobot.md)
- 下一节：[环境安装与版本固定](02-setup.md)
