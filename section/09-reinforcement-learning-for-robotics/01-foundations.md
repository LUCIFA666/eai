# 10.1 基础概念

这一组只解决一个问题：机器人任务怎样被写成可训练、可调试的 RL 闭环。先把 observation、action、reward、termination、success 和 episode 定义清楚，再讨论具体算法才有意义。

## 子页

- [MDP/POMDP](01-foundations/01-mdp-pomdp.md)：把 agent、environment、state、observation、action、reward、return、value、advantage 和 episode 串成机器人任务闭环。
- [奖励](01-foundations/02-reward-design.md)：区分 sparse reward、dense shaping、success signal、安全惩罚和奖励漏洞。

## 读完标准

- 能把一个机器人任务写成 MDP/POMDP 表。
- 能说明哪些量是可观测 observation，哪些只是隐藏 state。
- 能把 reward 拆成 success、shaping、安全约束和不该泄漏的信息。

- 返回本章：[强化学习](README.md)
