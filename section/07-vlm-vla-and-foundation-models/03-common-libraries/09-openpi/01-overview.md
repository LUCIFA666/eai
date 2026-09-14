# 8.5.1.1 OpenPI 整体介绍

本页是 OpenPI 动手学习指南的 overview 页面，目标是帮助读者理解 OpenPI 是什么、它在 VLA 训练流程中扮演什么角色，以及后续教程会围绕哪些核心模块展开。

## 学习目标
1. OpenPI 在 VLA 模型生态中处于什么位置？它和 LeRobot 是什么关系？
2. 一个 OpenPI 微调 + 部署流程通常包括哪些步骤？
3. OpenPI 支持哪些模型变体，各自适合什么场景？

## OpenPI 是什么

OpenPI 是 Physical Intelligence开源的机器人基础模型库，提供了 π0、π0-FAST 和 π0.5 三个 VLA模型的完整训练、微调和部署代码。它的目标是让研究者能够基于 Physical Intelligence 在大规模机器人数据上预训练的通用模型，在自己的机器人和任务数据上进行微调和部署。

OpenPI 的核心架构基于 PaliGemma作为语言骨干、SigLIP 作为视觉编码器，以及一个独立的 Action Expert 负责动作生成。模型接收图像、机器人状态和语言指令作为输入，输出下一步的动作序列。

与 LeRobot 不同的是，OpenPI 的定位更"上层"——它不是通用机器人学习框架，而是专门为大规模 VLA 模型设计的训练和推理框架。OpenPI 的数据层依赖 LeRobot 格式，但其配置系统、模型架构和部署方式都围绕 Physical Intelligence 的 π 模型家族设计。

## OpenPI 所解决的问题
在 VLA 模型的实际使用中，研究者通常会遇到以下问题：

- 通用模型在自己的机器人平台上不 work，需要微调但不知道怎么下手；
- π0 / π0.5 等大模型参数量大，单卡消费级 GPU 难以完整加载和训练；
- 不同机器人平台（如ALOHA、DROID、LIBERO 等）的观测和动作空间差异大，需要专门的输入输出映射；
- 模型训练时的数据格式、归一化统计量、checkpoint 管理与推理部署之间的链路不连贯。

OpenPI 的作用就是把这些问题封装成一套可复用的流程：通过统一的配置系统管理模型、数据和训练参数；通过 LoRA 和 FSDP 支持不同显存条件下的微调；通过 robot-specific policy 层屏蔽不同平台的差异；通过 WebSocket 推理服务把训练好的模型直接对接到机器人控制端。

## OpenPI 的整体流程
一个典型的 OpenPI 使用流程如下：

1. **安装环境**：使用 `uv` 管理 Python 依赖，拉取 git submodule 获取 ALOHA、LIBERO 等仿真环境。
2. **准备数据**：将自己的机器人数据转换为 LeRobot 格式，或直接使用 Hugging Face Hub 上已有的 LeRobot 数据集。
3. **计算归一化统计量**：为数据集计算归一化参数（mean/std 或 quantile-based），供模型训练和推理时使用。
4. **选择模型与配置**：根据任务选择 π0、π0-FAST 或 π0.5，通过 `TrainConfig` 集中管理模型架构、数据集路径和训练超参数。
5. **启动微调**：支持 JAX 和 PyTorch 两种后端，可按需启用 LoRA 低显存微调或 FSDP 多卡分布式训练。
6. **部署推理**：启动 WebSocket 推理服务，机器人端通过 `openpi-client` 包发送观测并接收动作。

## OpenPI 支持的模型变体

OpenPI 的核心模型均基于 PaliGemma + SigLIP 架构，根据动作生成方式和能力差异分为三种变体：

| 模型 | 动作生成方式 | 关键特点 | 适合场景 |
|---|---|---|---|
| π0 | Flow Matching（10 步反向 ODE） | 基础 VLA 模型，从噪声到动作通过学习速度场 `u_t` 逐步去噪 | 通用机器人操作任务的微调和部署 |
| π0-FAST | 自回归（FAST action tokenizer） | 将动作离散化为 FAST token，自回归生成，推理速度更快 | 对推理延迟敏感的场景 |
| π0.5 | Flow Matching + adaRMSNorm | π0 的升级版，状态输入通过离散语言 token 表示，更强的开放世界泛化和"知识隔离" | 需要跨场景泛化的复杂任务 |

三种模型共享同一套训练基础设施（配置系统、数据加载、checkpoint 管理），可以通过切换配置名称在不同模型和任务之间切换。

此外，OpenPI 为不同机器人平台提供了专用的 policy 层（`aloha_policy.py`、`droid_policy.py`、`libero_policy.py`），负责将原始传感器数据映射为模型输入，以及将模型输出映射为机器人指令。这意味着同一个 π0.5 模型可以通过换 policy 层适配不同的机器人。

## 阅读路线

本教程按照"环境安装 → π0 → π0-FAST → π0.5"的顺序展开，建议按编号依次阅读：

| 章节 | 内容 |
|---|---|
| [环境安装](02-setup.md) | `uv` 环境搭建、JAX/PyTorch 后端安装、硬件要求 |
| [π0 训练](03-pi0.md) | Flow Matching 架构、TrainConfig 配置、多卡分布式训练 |
| [PI0-FAST 训练](04-pi0fast.md) | FAST tokenizer 动作生成、与 π0 的差异、低显存训练策略 |
| [π0.5 训练](05-pi05.md) | AdaRMS + Quantiles 归一化、离散状态输入、跨场景泛化 |
| [自定义数据集训练](06-custom-dataset.md) | 将自己的机器人数据转为 LeRobot 格式，编写自定义 TrainConfig，适配不同 action/state 维度 |

## 导航

- 返回父页：[OpenPI](../09-openpi.md)
- 下一节：[环境安装](02-setup.md)
