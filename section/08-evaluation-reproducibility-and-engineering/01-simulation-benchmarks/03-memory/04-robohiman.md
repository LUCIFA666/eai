# RoboHiMan

RoboHiMan 是一套面向长时程操作中组合泛化的分层评测范式，在 Colosseum / RLBench 之上提供原子与组合任务，并用分层的规划器加策略架构，把长任务的失败归因到规划还是执行。

## 阅读顺序

| 页面 | 作用 |
|---|---|
| [概览与定位](04-robohiman/01-overview.md) | 要填的缺口、分层评测与组合泛化的含义、与 RLBench/LIBERO/Colosseum/DeCoBench 的区别 |
| [HiMan-Bench 任务](04-robohiman/02-tasks.md) | 10 原子任务与 12 组合任务、四类任务规模、组合如何由原子子阶段拼成 |
| [扰动因子](04-robohiman/03-perturbations.md) | 12 个 Colosseum 扰动因子与扰动空间 |
| [多级数据与渐进缩放](04-robohiman/04-dataset-and-scaling.md) | L1–L4 训练集设计、渐进数据缩放、数据生成与格式 |
| [三种评测设置](04-robohiman/05-evaluation-paradigms.md) | Vanilla、Decoupled、Coupled 的机制，子任务切换规则与 VLM 规划器 |
| [指标与协议](04-robohiman/06-metrics-and-protocol.md) | 成功率判定、episode 分配与有效 episode、离线规划器准确率、评测入口与结果汇总 |
| [基线与结果发现](04-robohiman/07-baselines-and-results.md) | 四个低层基线、主结果与规划瓶颈、真机验证 |

## References

- 论文：[RoboHiMan: A Hierarchical Evaluation Paradigm for Compositional Generalization in Long-Horizon Manipulation (arXiv:2510.13149)](https://arxiv.org/abs/2510.13149)
- 项目主页：[chenyt31.github.io/robo-himan.github.io](https://chenyt31.github.io/robo-himan.github.io/)
- GitHub：[RoboHiMan](https://github.com/chenyt31/RoboHiMan)

## 导航

- 返回上级：[记忆](../03-memory.md)
- 上一节：[RoboMemArena](03-robomemarena.md)
