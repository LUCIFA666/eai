# RoboTwin 2.0

## 目标

本节目标是把 RoboTwin 2.0 作为一个可运行、可复现、可报告的双臂操作 benchmark 来学习。读者应能够完成环境配置、理解 object/assets 与 domain randomization 机制，采集 expert 数据，并接入 ACT、DP、Pi0 等 policy 完成训练与闭环评测。

## 推荐阅读顺序

| 页面 | 作用 |
|---|---|
| [概览与评测协议](05-robotwin2-benchmark/01-overview-and-benchmark-protocol.md) | 说明 RoboTwin 2.0 是什么、测什么、指标怎么报 |
| [环境配置](05-robotwin2-benchmark/02-env-setup.md) | 安装依赖、下载 assets、确认机器人与相机配置 |
| [Object 与 Assets 机制](05-robotwin2-benchmark/03-object-assets.md) | 理解任务物体、资产文件、功能点和 success checker 的关系 |
| [数据采集、任务体系与 Domain Randomization](05-robotwin2-benchmark/04-data-collection.md) | 运行 `collect_data.sh`，理解 task config、50 个任务和 Easy/Hard 难度 |
| [Policy 训练、接入与评测](05-robotwin2-benchmark/05-policy-training-and-evaluation.md) | 解释 HDF5、观测和动作接口，统一评测口径；具体模型训练/评测见子章节 |

