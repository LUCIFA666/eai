# 其他范式

主线（VLA 基础与策略训练）讲的是"BC/SFT 训出来的端到端 VLA"这一条路。本节收纳它之外**已被广泛使用的其他建模范式**，以及代表这些范式的旗舰模型档案——它们不再是"前沿尝鲜"，而是 2025–2026 年与主线并行的成熟路线。

## 本组页面

| 三级页面 | 性质 | 重点 |
|---|---|---|
| [π0.7](05-advanced/01-pi07-steerable-generalist.md) | 代表模型 | flow-matching 通用模型旗舰：可引导性、组合泛化、视觉子目标 |
| [World Action Models](05-advanced/02-world-action-models.md) | 范式 | 世界演化 + 动作联合建模；下设 [DreamZero 原理](05-advanced/02-world-action-models/01-dreamzero.md)、[复现](05-advanced/02-world-action-models/02-dreamzero-reproduction.md) 与 [Fast-WAM](05-advanced/02-world-action-models/03-fast-wam.md)；与第 10 章按"动作为中心 / 环境为中心"划界 |
| [双系统 VLA](05-advanced/03-dual-system-vla.md) | 范式 | 快慢系统架构（Helix/GR00T/Gemini Robotics）；下设 ThinkAct / Fast-ThinkAct |
| [视频动作模型](05-advanced/04-video-action-models.md) | 范式 | 视频生成先验 + 动作，与 WAM 互为近亲 |
| [Gemini Robotics](05-advanced/05-gemini-robotics.md) | 代表模型 | 含 Gemini Robotics-ER；双系统范式的闭源旗舰档案 |
| [国产开源 VLA 速览](05-advanced/06-chinese-open-source-vla.md) | 代表模型 | WALL-OSS、RoboBrain 2.0、GO-1、RDT-2 |
| [实时分块与异步执行](05-advanced/07-realtime-chunking-async-execution.md) | 执行范式 | RTC 实时分块、异步推理、chunk 边界一致性与延迟鲁棒性 |
| [在线学习与自我改进](05-advanced/08-online-learning-self-improvement.md) | 训练范式 | π0.6/RECAP 路线：从自身经验与纠偏数据持续改进的数据飞轮 |

## 学习方式

范式页要写清"这条路线与主线的差异点和适用场景"；代表模型档案按阅读卡体例，写清"能学到什么"和"不能直接复现什么"。尚未开源或未稳定评测的能力，不当作已验证工程能力。
