# 训练教程

前面所有的建模、控制、观测、加速，最终都指向一件事：训练出一个能干活的策略。这一章给 MuJoCo 上训练的几个入门配方，把典型路径跑通。至于 PPO、SAC、模仿学习这些算法本身，留给 [10 强化学习](../../09-reinforcement-learning-for-robotics/README.md) 展开，这里只讲“在 MuJoCo 上怎么把训练跑起来”。

## 前置概念

读这一章前，建议先理解：

- **MJX**（详见 [MJX 与 GPU 并行](07-mjx-and-gpu.md)）：本章 GPU 训练路径的基础。
- **Gymnasium 风格包装**（详见 [Gymnasium 风格包装](05-interfaces-and-ecosystem/05-gymnasium-wrappers.md)）：SB3（Stable-Baselines3）期望的接口。
- **抓取实战**（详见 [抓取实战](06-grasping-walkthrough.md)）：用作模仿学习 demo 的来源。
- **PPO / 行为克隆等 RL/IL 术语**：本章给一句话定义，深入见 [10 强化学习](../../09-reinforcement-learning-for-robotics/README.md)。

## 学习路径

| 小节 | 读完能回答 | 重点 |
|---|---|---|
| [训练总览](08-training-recipes/01-overview.md) | 训练栈由哪几块组成？MuJoCo 在其中的位置？ | sim + algo + harness 三件套 |
| [CartPole + SB3](08-training-recipes/02-cartpole-with-sb3.md) | 最简单的 CPU 路径怎么跑？ | dm_control + Gymnasium + SB3 |
| [MJX + Brax 管线](08-training-recipes/03-mjx-brax-pipeline.md) | GPU 路径大规模训练怎么搭？ | MJX + Brax PPO |
| [行为克隆入门](08-training-recipes/04-imitation-from-demo.md) | 录 demo 学策略是什么过程？ | demo 录制、BC 训练、回放 |
| [Sim2Real 指路](08-training-recipes/05-sim2real-pointers.md) | 仿真训出来的策略怎么上真机？ | 关注点、域随机化、链到 12 真机实战 |

## 导航

- 上一节：[MJX 与 GPU 并行](07-mjx-and-gpu.md)
- 返回上级：[MuJoCo](../02-mujoco.md)
- 下一节：[附录：速查表](99-cheat-sheet.md)
