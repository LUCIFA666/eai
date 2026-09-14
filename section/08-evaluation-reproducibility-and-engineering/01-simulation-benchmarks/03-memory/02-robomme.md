# RoboMME

RoboMME 是面向 Vision-Language-Action（VLA）通用策略的记忆评测 benchmark，16 个长时程操作任务按四类认知记忆组织，用来系统比较不同记忆机制在历史依赖任务上的效果。

## 阅读顺序

| 页面 | 作用 |
|---|---|
| [概览与定位](02-robomme/01-overview.md) | 评测缺口、四维记忆一览、与 MIKASA / MemoryBench 的区别 |
| [记忆类型与套件](02-robomme/02-memory-suites.md) | 四认知维度 T/S/O/P 对应四个任务套件 |
| [任务目录](02-robomme/03-task-catalogue.md) | 16 个任务的套件、记忆类型、步数与考察点 |
| [记忆负载机制](02-robomme/04-memory-load.md) | 遮挡、洗牌、计数、视频条件与分阶段验证怎么逼出记忆 |
| [观测与动作接口](02-robomme/05-observation-and-action.md) | 四种动作空间、视频/单帧观测、HDF5 字段 |
| [评测协议与指标](02-robomme/06-evaluation-protocol.md) | 成功率与 status、split 与 seed、分阶段判定 |
| [MME-VLA 记忆方法](02-robomme/07-mme-vla-methods.md) | π0.5 上的三类记忆表示 × 三种集成方式 |
| [结果与发现](02-robomme/08-results-and-findings.md) | 主结果、主要发现与真机迁移 |
| [数据集](02-robomme/09-datasets.md) | 1600 条 demo、HDF5 格式、切分与数据筛选 |

## References

- 论文：[RoboMME: Benchmarking and Understanding Memory for Robotic Generalist Policies (arXiv:2603.04639, ICML 2026)](https://arxiv.org/abs/2603.04639)
- 项目主页：[robomme.github.io](https://robomme.github.io/)
- GitHub：[RoboMME/robomme_benchmark](https://github.com/RoboMME/robomme_benchmark)

## 导航

- 返回上级：[记忆](../03-memory.md)
- 上一节：[MIKASA-Robo-VLA](01-mikasa.md)
- 下一节：[RoboMemArena](03-robomemarena.md)
