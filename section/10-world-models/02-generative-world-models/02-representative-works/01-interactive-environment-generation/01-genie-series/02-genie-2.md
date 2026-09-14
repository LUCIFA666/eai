# Genie 2

## 官方资源

| 资源 | 作用 |
| --- | --- |
| [Genie 2 官方页面](https://deepmind.google/blog/genie-2-a-large-scale-foundation-world-model/) | 查看 Genie 2 的能力介绍、模型结构和动态演示 |
| [Genie 系列模型页面](https://deepmind.google/models/genie/) | 查看 Genie 系列的整体发展和后续模型 |
| [Genie 原始论文](https://arxiv.org/abs/2402.15391) | 理解第一代 Genie 的潜在动作与生成式可交互环境方法 |
| [SIMA 官方介绍](https://deepmind.google/blog/sima-generalist-ai-agent-for-3d-virtual-environments/) | 理解在 Genie 2 世界中执行任务的通用智能体 |

## 推荐阅读顺序

| 页面 | 作用 |
| --- | --- |
| [概览与技术演进](02-genie-2/01-overview-and-evolution.md) | 理解 Genie 2 如何从二维交互生成扩展到更丰富的三维世界 |
| [模型结构与生成过程](02-genie-2/02-model-architecture-and-generation.md) | 理解自回归潜空间扩散模型如何根据图像、历史状态和动作生成未来 |
| [生成能力与世界一致性](02-genie-2/03-capabilities-and-world-consistency.md) | 理解动作控制、反事实轨迹、长期记忆、物体交互和环境动态 |
| [快速原型与智能体评测](02-genie-2/04-rapid-prototyping-and-agent-evaluation.md) | 理解概念设计如何转化为交互环境，以及 SIMA 如何在生成世界中执行任务 |
| [局限与研究意义](02-genie-2/05-limitations-and-research-significance.md) | 理解 Genie 2 的能力边界及其对具身智能训练环境的意义 |

## 本节定位

Genie 2 是 Google DeepMind 提出的生成式三维世界模型。它可以从一张初始图像开始，根据人类或智能体持续提供的键盘和鼠标动作，逐步生成可控制的三维环境。

其基本过程可以表示为：

```text
文本描述
-> Imagen 3 生成初始图像
-> Genie 2 将图像编码为潜在状态
-> 人类或智能体输入动作
-> 模型预测下一时刻世界
-> 持续生成可交互轨迹
```

与第一代 Genie 主要展示二维平台场景和潜在动作不同，Genie 2 更强调：

```text
三维世界
键盘和鼠标控制
更长时间的一致性
物体交互
环境物理
其他智能体和 NPC
用于训练与评测 embodied agent
```

本章按照下面顺序展开：

```text
技术演进
-> 模型结构
-> 世界能力
-> 环境原型和智能体评测
-> 局限与研究意义
```
