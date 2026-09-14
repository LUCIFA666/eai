# RLBench

## 目标

本节目标是把 RLBench 作为一个经典的视觉引导机器人操作 benchmark 来学习。读者应能够理解 RLBench 的任务组织方式、observation 结构、demonstration 数据格式、评测协议，以及如何基于 RLBench 进行 imitation learning、reinforcement learning 或多任务操作实验。


## 推荐阅读顺序

| 页面 | 作用 |
|---|---|
| [概览与评测协议](10-rlbench-benchmark/01-overview-and-benchmark-protocol.md) | 说明 RLBench 是什么、包含哪些任务、常用指标怎么计算 |
| [环境配置](10-rlbench-benchmark/02-env-setup.md) | 安装 CoppeliaSim、PyRep 和 RLBench，并处理 headless 运行问题 |
| [任务结构与观测空间](10-rlbench-benchmark/03-task-structure-and-observations.md) | 理解 task class、variation、多视角图像、深度、mask 和低维状态 |
| [演示数据生成与数据集](10-rlbench-benchmark/04-demo-generation-and-dataset.md) | 说明 demonstrations 如何生成、保存和读取，episode 中包含什么 |
| [Policy 训练与评测](10-rlbench-benchmark/05-policy-training-and-evaluation.md) | 介绍如何用 RLBench 数据训练 policy，并用 success rate 做闭环评测 |
| [自定义任务构建](10-rlbench-benchmark/06-custom-task-building.md) | 说明如何定义新任务、waypoints、variation 和 success condition |