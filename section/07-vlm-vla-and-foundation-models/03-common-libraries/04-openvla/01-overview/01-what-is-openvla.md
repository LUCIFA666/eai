# OpenVLA 是什么

目标：理解 OpenVLA 解决的问题、核心组件和使用范围。

## 基本定位

OpenVLA 是一个 7B 级别的开源 Vision-Language-Action 模型。它以 Prismatic-7B VLM 为起点，在 Open X-Embodiment 机器人示教数据上继续训练，让模型根据图像观测和语言指令预测机器人动作。

OpenVLA 把模型权重、训练代码、数据读取、fine-tuning 和部署脚本都开放出来。复现时可以从 checkpoint 开始，沿着数据统计量、action token 解码和 `predict_action` 输出一路核对；改模型时，也能找到对应的训练和部署入口。

在目标任务上使用 OpenVLA 时，常见做法是从大规模机器人数据预训练得到的 checkpoint 出发，用 LoRA fine-tuning 对齐新的任务数据，再通过 REST server 把策略接到仿真或机器人端。

## 核心组件

下面这几个组件默认以主线 checkpoint `openvla/openvla-7b` 为参照。

| 组件 | 作用 | 读这一部分时重点看 |
| --- | --- | --- |
| Prismatic backbone | 处理图像和语言上下文。主线 `openvla/openvla-7b` 使用 DINOv2 + SigLIP 视觉 backbone，语言侧使用 Llama 2。 | 图像特征、语言指令和 LLM 生成接口如何接在一起。 |
| action token prediction | 把连续机器人动作表示成 LLM 可以生成的 tokens。 | 动作维度、token 数量和生成速度会怎样影响推理。 |
| OpenX / OXE 数据与统计量 | 提供多机器人示教数据，并保存动作归一化所需的统计量。 | `dataset_statistics.json` 和 `unnorm_key` 怎样影响动作尺度。 |

这三个部分共同决定了 OpenVLA 的使用方式：Prismatic 提供视觉语言基础，action tokens 把动作放进生成式模型，数据统计量负责把归一化动作恢复到目标数据集的尺度。

## 常见用途

- 作为开源 VLA baseline。它的模型、训练和评测入口都能检查，可以用来对齐自己的环境、数据和评测脚本。
- 作为 fine-tuning 起点。目标任务有示教数据时，可以从 OpenVLA checkpoint 出发做 LoRA 或 full fine-tuning，再用目标数据集的统计量恢复动作尺度。
- 用于学习 action token 路线。`ActionTokenizer`、`predict_action`、`dataset_statistics.json` 和 `unnorm_key` 串起了离散动作生成到连续动作输出的过程，可以用来读 VLA 源码。

## 局限性

OpenVLA 也具有一定的局限性：

- OpenVLA 原始路线预测的是单步 7D end-effector action。目标机器人如果使用不同动作空间、双臂控制、高频控制或 action chunk，需要先确认动作表示和训练数据是否匹配。
- 动作尺度依赖数据统计量。action token 解码后还要通过 `dataset_statistics.json` 和 `unnorm_key` 做反归一化；统计量选错时，模型可能返回形状正确的 action，但动作幅度已经偏离当前机器人或 benchmark。
- 推理速度会受到自回归生成影响。OpenVLA 需要逐 token 生成动作，动作维度和 token 数量会进入闭环控制频率。对需要高频控制的场景，这个因素需要单独评估。
- 预训练能力还需要目标域适配来落到具体平台。目标机器人的相机视角、任务分布、动作范围和数据采集方式变化较大时，仍然需要 fine-tuning 或数据对齐。

## 本页小结

- OpenVLA 是基于 Prismatic 的开源 VLA 模型和代码库。
- OpenVLA 的动作路线是 action token prediction。
- OpenVLA 可以作为开源 baseline、fine-tuning 起点和 action token 路线的源码样本。

## 导航

- 章节入口：[认识 OpenVLA](../01-overview.md)
- 返回上级：[认识 OpenVLA](../01-overview.md)
- 下一节：[架构与推理主线](02-architecture-and-inference.md)
