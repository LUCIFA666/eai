# RLINF

RLINF 是面向 Embodied AI 和 Agentic AI 的强化学习基础设施（RL infrastructure）。本单元从框架定位与架构设计讲起，落到本地安装和一次完整的多模型 PPO 训练与推理评测，最后给出总结与展望。

## 主线

阅读顺序：

1. [导读](03-rlinf-vla-rl/README.md)：本单元结构和阅读方式。
2. [框架总览与核心价值](03-rlinf-vla-rl/01-framework-overview-and-value.md)：RLinf 是什么、传统 RL 框架在大模型时代的瓶颈、核心性能指标和硬件底线。
3. [架构与设计理念](03-rlinf-vla-rl/02-architecture-and-design-philosophy.md)：解耦的分层架构（采集 / 推理采样 / 训练优化）与宏观到微观的流转设计。
4. [完整本地安装指南](03-rlinf-vla-rl/03-local-installation-guide.md)：从零搭建 RLinf 运行环境的分步命令与常见问题。
5. [具身智能实战闭环](03-rlinf-vla-rl/04-end-to-end-embodied-practice.md)：多模型 PPO 训练、评测与推理的端到端实操。
6. [总结与展望](03-rlinf-vla-rl/05-conclusion-and-future-development.md)：当前边界与后续发展方向。

## 代码覆盖

`inventory/` 目录保存按模块拆分的逐 Python 文件索引笔记（覆盖 `RLinf` 仓库的 `.py` 文件：文件路径、行数、架构角色、顶层 class/function 和主要依赖），供查任意文件在系统中的位置时使用；正文负责讲主调用链。

## 读完标准

读完这一单元后，你应该能：

- 说清 RLinf 三层架构（数据采集 / 推理采样 / 训练优化）各自负责什么，为什么要解耦。
- 解释"宏观到微观流转"如何把配置文件里的抽象数据流编译成 Actor / Rollout / Learner 三端协同的混合执行。
- 独立完成本地安装，并跑通一次具身 PPO 训练与评测。
- 判断自己的硬件（显卡数量与显存）适合哪种规模的 RLinf 训练。
