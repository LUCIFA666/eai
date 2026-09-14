# MIKASA-Robo-VLA

MIKASA-Robo-VLA 是 ManiSkill 上面向 VLA 研究的记忆密集型桌面操作 benchmark，90 个任务覆盖 10 类记忆，要求策略在部分可观测环境下保留并使用历史观测与动作。

## 阅读顺序

| 页面 | 作用 |
|---|---|
| [概览与定位](01-mikasa/01-overview.md) | benchmark 定位、要填的评测缺口，以及与 32 任务 RL 原版的关系 |
| [记忆类型体系](01-mikasa/02-memory-taxonomy.md) | 10 类记忆各自要求策略记住什么 |
| [任务目录](01-mikasa/03-task-catalogue.md) | 26 个任务家族、90 个环境，代表任务与考察点 |
| [记忆负载机制](01-mikasa/04-memory-load.md) | 部分可观测设计：线索先可见、之后被遮挡或延迟 |
| [难度与时间跨度](01-mikasa/05-difficulty-and-horizon.md) | 难度档与 Short/Medium/Long 分档、步数分布 |
| [观测与动作接口](01-mikasa/06-observation-and-action.md) | 观测模式、观测键、动作空间与 VLA wrapper |
| [评测协议与指标](01-mikasa/07-evaluation-protocol.md) | 任务选取、seed、多任务训练与 `success_once` 指标 |
| [数据集](01-mikasa/08-datasets.md) | oracle 轨迹规模与 NPZ / RLDS / LeRobot 格式 |
| [基线与记忆瓶颈证据](01-mikasa/09-baselines-and-memory-bottleneck.md) | 仓库提供的 PPO / PPO-LSTM 基线，以及评估它们揭示的记忆瓶颈 |

## References

- 论文：[Memory, Benchmark & Robots: A Benchmark for Solving Complex Tasks with Reinforcement Learning (arXiv:2502.10550, ICLR 2026)](https://arxiv.org/abs/2502.10550)
- 文档：[mikasarobo.github.io](https://mikasarobo.github.io/)
- GitHub：[CognitiveAISystems/MIKASA-Robo](https://github.com/CognitiveAISystems/MIKASA-Robo)

## 导航

- 返回上级：[记忆](../03-memory.md)
- 下一节：[RoboMME](02-robomme.md)
