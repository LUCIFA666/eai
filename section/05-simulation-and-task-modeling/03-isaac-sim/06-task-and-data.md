# 任务、数据采集与合成数据

一次能动、能看的仿真，还不是"一个任务"。这一章讲怎么把它收敛成有明确开始、结束和成功判定的 episode，再讲怎么把过程采集成可训练、可回放、可质检的数据，用 headless 批量跑出可复现的结果，最后用 Replicator 批量生成带标注感知数据。

## 本节目标

本节围绕下面几个问题展开：

1. 一个仿真任务怎样组织成 episode？
2. success、reset、phase、action 和 observation 应该怎样记录？
3. 数据采集、存放格式和回放验证之间是什么关系？
4. headless、随机种子和合成数据会带来哪些复现问题？

## 学习路径

| 页面 | 重点 | 学习产出 |
|---|---|---|
| [任务、episode 与成功判定](06-task-and-data/01-task-episode-success.md) | 任务拆解、回合边界、重置、成功 / 失败条件 | 把一段仿真定义成一个任务 |
| [数据采集、回放与质检](06-task-and-data/02-data-collection.md) | 记录什么、对齐时间、回放与质量检查 | 产出一份可用的任务数据 |
| [数据存放格式](06-task-and-data/03-data-storage-format.md) | episode 目录、frames 表、metadata、schema | 设计一套能训练、回放和迁移的数据格式 |
| [headless 批量与可复现](06-task-and-data/04-headless-and-repro.md) | 无显示器批量、随机种子、可复现要点 | 批量稳定地产出数据 |
| [Replicator 合成数据（SDG）](06-task-and-data/05-replicator-sdg.md) | render product、annotator、writer、随机化 | 批量产出带标注感知数据集 |

## 导航

- 返回上级：[Isaac Sim](../03-isaac-sim.md)
- 上一页：[观测与传感器](05-observation.md)
- 下一页：[仿真接口](07-ecosystem.md)
