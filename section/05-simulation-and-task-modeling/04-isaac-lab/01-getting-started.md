# 认识 Isaac Lab

先建立对 Isaac Lab 的整体认知，再亲手跑完一个训练与回放闭环。先不要急着改 reward、换机器人或写自己的任务；最重要的是知道 Isaac Lab 在 Isaac Sim 和训练库之间扮演什么角色，以及用最小代码了解全架构。

## 本节目标

本节围绕下面几个问题展开：

1. 入门要先对 Isaac Lab 建立哪些基本认识？
2. 第一次运行之前，需要准备哪些环境、版本和启动方式？
3. 最小脚本或最小任务跑起来后，应该看哪些结果，应该学会哪些理解视角？
4. 后续小节之间应该按什么顺序学习？

本部分采用和 Isaac Sim 入门一致的节奏：先认识 Isaac Lab 的职责边界，再跑通 CartPole 的训练与回放闭环；跑完之后回头解释并行张量、配置驱动和仿真到 RL 环境这三个理解视角，最后附上安装与版本相关经验。

## 学习路径

| 页面 | 重点 | 学习产出 |
|---|---|---|
| [Isaac Lab 是什么](01-getting-started/01-what-is-isaac-lab.md) | 在 Sim ↔ RL 之间的位置；为什么不能直接拿 Isaac Sim 训练 | 建立 Isaac Lab 的职责边界 |
| [第一次训练](01-getting-started/02-first-run-cartpole.md) | 用 CartPole 跑通 `train` + `play`，获得一次完整体验 | 完成一次训练与回放闭环 |
| [三个理解视角](01-getting-started/03-three-mental-models.md) | 并行张量、配置驱动 + Manager、仿真 → RL 环境 | 解释日志、代码和多环境现象 |
| [安装与版本对照](01-getting-started/04-install-and-versions.md) | 安装方式、版本对应、常见坑 | 能按依赖链定位环境问题 |

## 读完本部分后

完成这一部分后，应该能回答三类问题：Isaac Lab 为什么不是另一个 Isaac Sim；`Isaac-Cartpole-v0` 从训练到回放的最小闭环怎么跑；遇到环境报错时，应该先查驱动、Isaac Sim、Python、Isaac Lab 还是训练库。

## 导航

- 返回上级：[Isaac Lab](../04-isaac-lab.md)
- 下一页：[任务结构与 Manager 系统](02-reading-a-task.md)
