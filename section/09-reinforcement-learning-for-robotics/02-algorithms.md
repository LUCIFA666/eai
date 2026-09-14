# 经典强化学习算法

这一组按强化学习算法谱系组织：先从值函数方法和策略梯度方法建立基本分支，再进入演员-评论家框架，最后覆盖机器人连续控制中最常见的 PPO、DDPG、TD3、SAC，以及离线强化学习和基于模型的强化学习。这里不是泛 RL 算法百科，重点是让读者知道这些经典算法在机器人任务中各自解决什么问题、为什么后来会演化到 VLA-RL 和真实机器人后训练。

## 子页

- [Q 学习与深度 Q 网络](02-algorithms/01-q-learning-and-deep-q-network.md)：理解值函数、Bellman 更新、经验回放、目标网络，以及离散动作强化学习的基本范式。
- [策略梯度与 REINFORCE](02-algorithms/02-policy-gradient-and-reinforce.md)：理解直接优化策略、轨迹回报、log-prob 梯度和高方差问题。
- [演员-评论家方法](02-algorithms/03-actor-critic.md)：理解 actor、critic、advantage、TD error，以及 A2C/A3C 到现代策略优化方法的桥梁作用。
- [信赖域策略优化](02-algorithms/04-trust-region-policy-optimization.md)：理解 trust region、KL 约束、单调改进直觉，以及它和 PPO 的关系。
- [近端策略优化](02-algorithms/05-proximal-policy-optimization.md)：理解 rollout buffer、advantage、clipped objective 和多轮更新。
- [深度确定性策略梯度](02-algorithms/06-deep-deterministic-policy-gradient.md)：理解确定性 actor-critic、连续动作、replay buffer 和 target network。
- [双延迟深度确定性策略梯度](02-algorithms/07-twin-delayed-deep-deterministic-policy-gradient.md)：理解 twin critic、delayed policy update、target policy smoothing，以及它如何修正 DDPG 的过估计问题。
- [软演员-评论家](02-algorithms/08-soft-actor-critic.md)：理解 replay buffer、Q function、entropy、temperature 和连续动作控制。
- [离线强化学习](02-algorithms/09-offline-reinforcement-learning.md)：区分 BC、offline RL、online RL，理解数据质量、分布外动作风险，以及 CQL/IQL/AWAC 等代表路线。
- [基于模型的强化学习](02-algorithms/10-model-based-reinforcement-learning.md)：理解学习动力学模型、隐空间规划、想象训练，以及 TD-MPC2 / DreamerV3 与 model-free RL 的取舍。

## 读完标准

- 能说明值函数方法、策略梯度方法和演员-评论家方法分别在优化什么。
- 能解释 DDPG、TD3、SAC 为什么构成机器人连续控制中常见的 off-policy 演化链路。
- 能判断一个机器人任务先用 PPO、SAC、BC、offline RL 还是 model-based RL 做 baseline。
- 能解释离线数据为什么不能直接等同于可安全探索的环境交互。
- 能说明基于模型的强化学习为什么样本效率更高，但会受到模型误差累积和推理开销影响。

- 返回本章：[强化学习](README.md)
