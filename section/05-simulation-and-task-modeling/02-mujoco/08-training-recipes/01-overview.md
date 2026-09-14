# 训练总览

“训练”这个词容易让人只想到调 PPO（一种常用的 RL 算法，本页后面会给一句话定义）的超参，但一次训练通常至少由三块组成：仿真器（提供数据）、算法（怎么从数据里学）、训练循环框架（把仿真和算法串起来）。

## 本节目标

本节回答几个问题：

1. 训练栈的三块各自扮演什么角色？
2. MuJoCo（和 MJX）在其中处于哪一层？
3. 这一章四个示例分别覆盖什么场景？

## 训练栈三件套：sim + algo + harness

<figure class="doc-figure" aria-label="训练栈分层">
  <p class="doc-figure-title">训练栈的三层结构</p>
  <table>
    <tr><th>层</th><th>做什么</th><th>本章用到的</th></tr>
    <tr><td><strong>Sim</strong>（仿真器）</td><td>提供环境交互：step → 产生 obs + reward + done</td><td>MuJoCo、MJX、dm_control 环境</td></tr>
    <tr><td><strong>Algo</strong>（算法）</td><td>从交互数据中更新策略：PPO 限制每次策略更新的幅度，SAC 用最大熵框架平衡探索</td><td>SB3 的 PPO、Brax 的 PPO、PyTorch BC</td></tr>
    <tr><td><strong>Harness</strong>（训练循环）</td><td>把 sim 和 algo 串起来：收集 rollout → 更新模型 → 记录日志 → 评估</td><td>SB3 learn()、Brax train、手写循环</td></tr>
  </table>
</figure>

这三层在代码里并不总是严格分离的（不少框架把它们揉在一起），但在概念上分开来看，往往更容易定位问题："训练不收敛"，到底是仿真不对、算法调得不好，还是训练循环有 bug？

## MuJoCo 在训练里的位置

MuJoCo（包括 MJX）处于训练栈的**仿真层**。它只负责：给定动作（ctrl），输出下一状态（qpos/qvel/sensor）。奖励信号由任务定义层提供。算法和训练循环不是 MuJoCo 的职责。

- **MuJoCo / dm_control** → 提供单环境交互（`env.step`）。
- **MJX** → 提供 GPU 批量交互（`mjx.step` + vmap → 几千个环境同时 step）。
- **Brax / SB3** → 把批量交互数据和算法（这里用 PPO）串起来。Brax 是 Google 的 JAX 原生 RL 训练框架，细节在 [MJX + Brax 管线](03-mjx-brax-pipeline.md) 展开。

## 本章四个示例的路线

| 示例 | 仿真后端 | 算法 | 适合场景 |
|---|---|---|---|
| 02 CartPole + SB3 | CPU (dm_control) | PPO | 入门：用最少的代码看到训练全过程 |
| 03 MJX + Brax | GPU (MJX) | PPO | 加速：几千个环境同时训练 |
| 04 行为克隆 | CPU | 监督学习 | 当已有 demo 数据时，比 RL 更快出结果 |
| 05 Sim2Real 指路 | 不限 | 不限 | 从仿真到真机的关注点清单 |

## 想深入 RL，去强化学习章

这一章聚焦"在 MuJoCo 上怎么跑训练"，不展开 RL 算法细节。PPO（Proximal Policy Optimization，通过限制每次策略更新幅度来避免训练崩溃的 on-policy 算法）、SAC（Soft Actor-Critic，在最大化奖励的同时鼓励探索的 off-policy 算法）、行为克隆（把专家动作当作标签，用监督学习直接拟合策略）这些术语，在本章出现时会给一句话定义。如果想真正理解它们为什么这样设计、数学原理是什么、以及如何针对具体任务调优，可以参考 [10 强化学习](../../../09-reinforcement-learning-for-robotics/README.md)。

## 小结

- 训练栈 = Sim（提供数据）+ Algo（从数据中学）+ Harness（串起来）。
- MuJoCo 处于 Sim 层；SB3/Brax 处于 Algo + Harness 层。
- 本章是入门 recipe，跑通流程，不深入算法。

## 参考资料

- [Stable-Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [Brax（GitHub）](https://github.com/google/brax)
- [MuJoCo Documentation: MJX](https://mujoco.readthedocs.io/en/stable/mjx.html)

## 导航

- 上一节：[训练教程](../08-training-recipes.md)
- 返回上级：[训练教程](../08-training-recipes.md)
- 下一节：[CartPole + SB3](02-cartpole-with-sb3.md)
