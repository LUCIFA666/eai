# 认识 Isaac Sim

先建立对 Isaac Sim 的整体认识（是什么、能做什么、为什么比 MuJoCo 更像一个平台），再亲手跑通第一个最小仿真，用最小的代码了解全架构，同时把后面所有页面要讲的内容串成一条预览线。

## 本节目标

本节围绕下面几个问题展开：

1. 入门要先对 Isaac Sim 建立哪些基本认识？
2. 第一次运行之前，需要准备哪些环境、版本和启动方式？
3. 最小任务跑起来后，应该学会哪些理解视角？
4. 后续小节之间应该按什么顺序学习？

## 前置概念

本部分是 Isaac Sim 单元入口，只需会基础 Python、对"物理仿真会在 step 循环里推进"有大致直觉就够了。你不需要事先懂 USD、PhysX、Omniverse、ROS 2 或 Isaac Lab；这些概念会在后面逐步展开。

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [Isaac Sim 是什么](01-getting-started/01-what-is-isaac-sim.md) | Isaac Sim 到底是什么？和 MuJoCo、Isaac Lab 怎么分工？ | 平台定位、适用场景、职责边界 |
| [第一次仿真](01-getting-started/02-first-simulation.md) | 怎么让 Isaac Sim 第一次真正动起来？如何判断已经跑通？ | `SimulationApp` → `World` → `reset` → `step` → `close` |
| [三个理解视角](01-getting-started/03-three-mental-models.md) | 为什么启动顺序、Prim 路径和 reset 这么重要？ | 一张主图贯穿全单元 |
| [安装与版本对照](01-getting-started/04-install-and-versions.md) | 自己机器怎么装？版本和 import 名称怎么对齐？ | 安装方式、版本矩阵、常见环境错误 |

## 导航

- 返回上级：[Isaac Sim](../03-isaac-sim.md)
- 下一页：[场景构建与坐标约定](02-building-a-world.md)
