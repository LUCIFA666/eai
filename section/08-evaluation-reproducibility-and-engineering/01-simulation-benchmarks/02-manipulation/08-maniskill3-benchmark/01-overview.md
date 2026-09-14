# Overview

本节是 ManiSkill3 章节的总览。ManiSkill3 是一个面向机器人操作与 embodied AI 研究的仿真和学习框架，底层基于 SAPIEN / PhysX，接口接近 Gymnasium，支持 GPU 并行仿真、任务资产下载、官方 demonstration、trajectory replay / convert，以及 RL、IL、VLA 等 baseline 路线。



## 章节结构

| 小节 | 作用 |
|---|---|
| [ManiSkill Task 种类](02-task-types.md) | 了解官方 task index 与任务类别 |
| [安装与渲染依赖](03-installation-and-rendering-deps.md) | 配置固定路径 Python 环境、Torch、Vulkan |
| [用 Gymnasium 创建任务](04-gymnasium-create-task.md) | 复现官方 quick start 的最小任务交互 |
| [随机动作 demo](05-random-action-demo.md) | 用官方脚本验证 CPU/GPU 运行与渲染 |
| [下载任务、资产与演示数据](06-download-demonstrations.md) | 下载 assets 和 demonstration |
| [Replay 与 Convert Trajectory](07-replay-and-convert-trajectory.md) | 将 demonstration 转为训练可用轨迹 |
| [RL、IL、VLA Baselines](08-baselines-rl-il-vla.md) | 运行 PPO / BC，并了解 DP、ACT、VLA 入口 |


## 导航

| 上一节 | 下一节 |
|---|---|
| [ManiSkill3](../08-maniskill3-benchmark.md) | [ManiSkill Task 种类](02-task-types.md) |
