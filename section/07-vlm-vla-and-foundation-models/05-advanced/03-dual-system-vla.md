# 双系统 VLA

本节介绍双系统（快慢耦合）VLA 架构：用一个慢速、基于 VLM 的 System-2 做语义理解与规划，用一个快速 System-1 做高频动作生成，兼顾泛化能力与实时控制频率。要讲的内容：System-1 / System-2 的职责划分与参数共享、与 π0 类 action expert 设计的关系、控制频率提升的来源。代表系统包括 Gemini Robotics（见 [Gemini Robotics](05-gemini-robotics.md)）、Helix、GR00T、π0.5，以及推理增强的 ThinkAct 一族。参考资料：Awesome Dual-System VLA 列表 https://github.com/OpenHelix-robot/awesome-dual-system-vla 。

## 本组页面

| 三级页面 | 重点 |
|---|---|
| [ThinkAct](03-dual-system-vla/01-thinkact.md) | 推理增强双系统：RL 训练的 System-2 推理器 + visual plan latent 条件化的 System-1 |
| [Fast-ThinkAct](03-dual-system-vla/02-fast-thinkact.md) | ThinkAct 提效后续：verbalizable latent planning + latent CoT 蒸馏 |
