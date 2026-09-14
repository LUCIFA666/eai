# Isaac Lab

Isaac Sim 解决“世界能不能被仿真”的问题，Isaac Lab 解决“这个世界能不能被训练”的问题。它把机器人资产、并行场景、观测、动作、奖励、终止、随机化和训练库接口组织成一个完整的机器人学习任务，让同一个任务既能回放调试，也能交给 PPO、模仿学习或分布式训练流程反复优化。

阅读本节前，最好已经读过 [Isaac Sim](03-isaac-sim.md) 的基本概念：USD 场景、机器人 articulation、传感器和 headless 运行。不要求已经掌握强化学习算法；本节专注把 Isaac Lab 的工程结构和训练流程讲清楚，强化学习本身的原理（MDP、回报与价值、策略梯度、GAE、PPO 等）统一放到后面的[第 9 章 面向机器人的强化学习](../09-reinforcement-learning-for-robotics/README.md)讲解，本单元不展开。

## 本节目标

本节围绕下面几个问题展开：

1. Isaac Lab 在 Isaac Sim 之上到底补了哪一层？
2. 它和 Isaac Sim、MuJoCo、普通 Gym 环境的边界在哪里？
3. 学 Isaac Lab 时，为什么要按任务、场景、观测、奖励、训练这条线推进？
4. 初学者第一次训练应该先看哪些日志、曲线和回放结果？

## 这一单元想解决什么

Isaac Lab 的门槛不在“多写几个 API”，而在三种思维转换：

1. **从单场景到并行环境**：训练时不是一个机器人慢慢跑，而是成百上千个环境同时在 GPU 上推进。观测、动作、奖励和终止都以 `[num_envs, ...]` 张量组织。
2. **从脚本流程到配置化任务**：一个任务通常由 `@configclass`、`InteractiveSceneCfg` 和一组 Manager 拼装出来。读任务时要先看结构，再看某个具体函数。
3. **从仿真对象到学习接口**：机器人和物体只是起点，真正的 RL / IL 环境还需要 observation、action、reward、termination、event、recorder 和训练库 wrapper。

本单元按“先跑通，再读懂，再搭建，再训练”的顺序展开。读完之后，应该能从一个官方任务出发，知道它的场景在哪里、观测怎么拼、动作怎么作用到机器人、奖励和终止怎么定义、训练脚本怎样接到不同 RL 库，并能用日志和视频判断策略是否真的学对。

## 本单元边界

本单元聚焦 Isaac Lab 内部的任务定义、并行训练、回放评测和训练信号解释。以下内容不在这里展开：

- **Isaac Sim 基础**：USD、光照、相机、机器人导入、仿真循环见 [Isaac Sim](03-isaac-sim.md)。
- **强化学习理论与算法**：MDP、回报与价值、策略梯度、GAE、PPO 等训练信号背后的原理，以及 SAC / TD3 / offline RL 等算法，统一放到 [第 9 章 面向机器人的强化学习](../09-reinforcement-learning-for-robotics/README.md)，本单元不展开。
- **策略导出与真机部署**：Sim2Real、真机通信、安全联调留给真机实战章节。
- **数据集工程**：大规模数据格式、遥操作数据治理和跨格式转换见数据相关章节。

## 学习路径

| 页面 | 学习者此刻在问 | 重点 |
|---|---|---|
| [认识 Isaac Lab](04-isaac-lab/01-getting-started.md) | 这是什么？怎么先跑起来？ | 定位、第一次训练、三个理解视角、安装与版本 |
| [任务结构与 Manager 系统](04-isaac-lab/02-reading-a-task.md) | 刚跑通的任务由哪些模块组成？ | 环境结构、八大 Manager、任务注册、Manager-based 与 Direct |
| [场景与机器人资产](04-isaac-lab/03-scene-and-robot.md) | 机器人、物体和并行场景怎么配置？ | `InteractiveSceneCfg`、资产类型、执行器、自定义机器人 |
| [任务逻辑配置](04-isaac-lab/04-task-logic.md) | 任务规则如何变成可训练接口？ | 观测、传感器、动作 / 控制器、奖励、终止、课程 |
| [训练与评测](04-isaac-lab/05-training.md) | 任务定义好了，怎么训练、回放和排查？ | train / play、CLI 覆盖、RL 库、模仿学习、随机化、分布式、性能调试 |

## 版本轴

Isaac Lab 强依赖 Isaac Sim、Python、NVIDIA Driver 和训练库版本。具体安装命令放在入门组的安装页，本页先给出课程锁定版本：**本节示例按 Isaac Sim 5.1.0 + Isaac Lab 2.3.2 + Python 3.11 编写和验收**。

如果读者使用官方最新版，例如 Isaac Lab 3.0 beta / Isaac Sim 6.0 / Python 3.12 这条线，需要按官方版本矩阵替换安装命令、Python 版本和部分脚本参数。不要把最新版 quickstart 与本节 2.3.2 示例混装；排查环境问题时，先确认 Isaac Sim、Isaac Lab 和 Python 是否属于同一条版本轴。


## 导航

- 上一页：[Isaac Sim](03-isaac-sim.md)
- 返回目录：[06 仿真建模](README.md)
- 下一页：[SAPIEN 生态](05-sapien-ecosystem.md)

## 延伸阅读

- Isaac Lab documentation. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab repository. https://github.com/isaac-sim/IsaacLab
