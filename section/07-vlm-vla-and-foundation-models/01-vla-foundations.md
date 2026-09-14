# VLA 基础

VLA 这一节不急着进入训练脚本。真正开始写代码之前，读者更需要先理解一个变化：机器人策略正在从“给定视觉观测，模仿专家动作”，走向**“利用视觉语言模型的语义知识，在物理世界里生成可执行动作”**。这个变化听起来像模型名字的变化，背后其实牵动了动作表示、动作 token、连续动作生成、跨机器人适配和长视距规划等一整组问题。

本组采用一条**渐进式路线**。先讲 VLA 之前的 VA 模型，说明视觉动作策略已经能解决什么、又为什么不够；再用一个较长的小节集中讲 VLA 的定义、输入输出、控制模式、动作规范、时序建模、动作生成头和跨本体对齐；然后把 OpenVLA、Octo、π0/OpenPI 放到同一节里，讲 VLA 模型的**架构演变**；最后以世界模型收束，说明 VLA 行为克隆范式还缺少“预测后果”的能力。

<div class="concept-note concept-green">阅读路线：问题逐步变难</div>

## 三级目录

| 小节 | 需要介绍什么 |
|---|---|
| [VLA 出现之前：视觉动作模型为什么不够用](01-vla-foundations/01-before-vla-vision-action.md) | 从行为克隆、视觉伺服、ACT、Diffusion Policy 等 VA 路线讲起，说明它们的核心思想、典型优势和语言/语义泛化不足。 |
| [什么是 VLA：基础概念、接口规范与演进路线](01-vla-foundations/02-what-is-vla-and-evolution.md) | 集中讲 VLA 系统边界、最小样本、多模态输入、控制模式、动作表示规范、时序建模、动作生成头和跨本体对齐。 |
| [VLA 模型的架构演变：从动作 token 到连续 flow action](01-vla-foundations/03-vla-architecture-evolution.md) | 把 OpenVLA、Octo、π0/OpenPI 放到同一条架构演变线上，比较动作 token、通用策略接口和连续 flow action。 |
| [从 VLA 到世界模型：机器人需要先在脑中试一遍](01-vla-foundations/04-world-models-for-vla.md) | 介绍世界模型是什么，为什么能补足 VLA 在数据依赖、长视距规划和反事实推理上的不足。 |

## 阅读路线

建议按顺序阅读。本组不是论文列表，而是一条问题被逐步逼出来的技术路线：

```text
VA：看图做动作，能模仿，但语言和开放语义弱
  ↓
VLA：把视觉、语言、状态和动作联合建模
  ↓
OpenVLA / Octo：开源化、通用策略和接口适配
  ↓
π0 / OpenPI：连续 flow action，生成平滑动作片段
  ↓
世界模型：预测动作后果，为长视距规划补上想象能力
```

这条线也解释了为什么本组暂时不展开部署代码。训练命令、服务接口、runtime queue 和安全 watchdog 都很重要，但它们属于后面的 [常用库](03-common-libraries.md) 与 [部署推理](04-deployment-inference.md)。本节的任务是先把概念讲清楚。

## 本组边界

本节只讲 **VLA 概念、接口规范、技术路线和关键模型演变**。行为克隆训练目标放到 [策略训练](02-behavior-cloning.md)，OpenPI、LeRobot、OpenVLA、StarVLA 等工程入口放到 [常用库](03-common-libraries.md)，推理服务、runtime 和推理加速放到 [部署推理](04-deployment-inference.md)，π0.7、World Action Model、记忆、分层和更强跨本体泛化放到 [其他范式](05-advanced.md)。

## 自查问题

1. VA 模型和 VLA 模型的根本差异是什么？
2. 为什么动作表示不是实现细节，而是数据、训练和部署之间的 contract？
3. 动作 token 路线为什么能接入 LLM/VLM，又为什么会遇到延迟和量化误差？
4. OpenVLA、Octo、π0/OpenPI 分别推进了 VLA 架构的哪一部分？
5. 世界模型想补足 VLA 的哪类能力？

## 参考资料

- 【RT-2 论文，VLA 概念和动作 token 路线的重要起点】[https://arxiv.org/abs/2307.15818](https://arxiv.org/abs/2307.15818)
- 【OpenVLA 论文，开源 VLA 基准模型】[https://arxiv.org/abs/2406.09246](https://arxiv.org/abs/2406.09246)
- 【Octo 论文，通用机器人策略和灵活接口设计】[https://arxiv.org/abs/2405.12213](https://arxiv.org/abs/2405.12213)
- 【π0 论文，连续 flow-action VLA 代表】[https://arxiv.org/abs/2410.24164](https://arxiv.org/abs/2410.24164)
- 【UniPi 论文，文本条件视频生成式规划先驱】[https://arxiv.org/abs/2302.00111](https://arxiv.org/abs/2302.00111)
