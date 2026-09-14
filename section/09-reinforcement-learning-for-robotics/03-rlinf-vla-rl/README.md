# 导读

这一组小节介绍 RLINF：一个面向 Embodied AI 与 Agentic AI 的分布式强化学习基础设施。它不是 SB3/CleanRL 那种单文件训练循环，而是把 actor、rollout、env、reward 等组件做成分布式 worker，再通过通信与调度机制组织它们，用于 VLA 等基础模型的 RL 后训练。

## 小节结构

- [框架总览与核心价值](01-framework-overview-and-value.md)：RLinf 是什么、要解决什么瓶颈、基准结果与硬件底线。
- [架构与设计理念](02-architecture-and-design-philosophy.md)：三层解耦架构与宏观到微观的流转设计。
- [完整本地安装指南](03-local-installation-guide.md)：分步安装命令与验证方式。
- [具身智能实战闭环](04-end-to-end-embodied-practice.md)：多模型 PPO 训练、评测与推理的端到端实操。
- [总结与展望](05-conclusion-and-future-development.md)：能力边界与发展方向。

## 阅读建议

1. 先读总览与架构两节，建立"为什么要解耦、解耦成什么样"的心智模型。
2. 再按安装指南搭好环境，跑通实战闭环一节的最小训练。
3. 需要查某个 `.py` 文件在系统里的位置时，使用 `inventory/` 下按模块拆分的文件索引笔记。

- 返回上级：[RLINF](../03-rlinf-vla-rl.md)
