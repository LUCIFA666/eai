# RoboMemArena

RoboMemArena 是一个大规模、长时程的机器人记忆 benchmark，26 个操作任务按四类记忆需求组织，平均轨迹超过一千步、历史依赖子任务比例在同类中最高，带子任务与关键帧的多模态标注，并配对一组真机任务。它建立在 LIBERO 之上，配套一个双系统记忆方法 PrediMem。

## 阅读顺序

| 页面 | 作用 |
|---|---|
| [概览与定位](03-robomemarena/01-overview.md) | 定位、要填的缺口、与 MIKASA / RoboMME / MemoryBench 的区别 |
| [记忆类型与任务](03-robomemarena/02-memory-tasks.md) | 四类记忆与 26 个任务，各类怎么逼出记忆 |
| [记忆负载与标注](03-robomemarena/03-memory-load-and-annotation.md) | 轨迹长度、历史依赖比例的推导、多模态标注 |
| [数据生成管线](03-robomemarena/04-data-generation.md) | VLM 分解 → AnyGrasp 生成 → 多条件关键帧抽取 |
| [任务定义与观测/数据格式](03-robomemarena/05-task-definition-and-io.md) | BDDL 与 LIBERO、观测与动作、HDF5 与 RLDS |
| [评测协议与指标](03-robomemarena/06-evaluation-protocol.md) | TSR / CSR 定义、评测命令、策略适配器契约 |
| [PrediMem 方法](03-robomemarena/07-predimem.md) | 双系统 + 记忆库 + 预测编码头 |
| [结果与发现](03-robomemarena/08-results.md) | 主结果、消融、真机迁移与失败证据 |

## References

- 论文：[RoboMemArena: A Comprehensive and Challenging Robotic Memory Benchmark (arXiv:2605.10921)](https://arxiv.org/abs/2605.10921)
- 项目主页：[robomemarena.github.io](https://robomemarena.github.io/)
- GitHub：[OpenHelix-Team/RoboMemArena](https://github.com/OpenHelix-Team/RoboMemArena)

## 导航

- 返回上级：[记忆](../03-memory.md)
- 上一节：[RoboMME](02-robomme.md)
- 下一节：[RoboHiMan](04-robohiman.md)
