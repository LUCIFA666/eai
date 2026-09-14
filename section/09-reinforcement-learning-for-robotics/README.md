# 强化学习

本章把强化学习从“算法名词表”整理成一条机器人学习路径：先理解基础概念，再用值函数、策略梯度、演员-评论家、连续控制、离线强化学习和基于模型的强化学习建立算法视角，然后进入 RLINF 和 SimpleVLA-RL 的真实代码阅读，最后落到足式运动控制 RL 这一具身 RL 最成功的落地方向。

强化学习在具身 AI 中不是万能解法。它最适合解决“策略需要通过交互反馈改进”的问题，例如从成功/失败奖励中提升抓取成功率、在仿真中补足示教数据覆盖不到的状态，或对 VLA 模型做任务成功率导向的后训练。

## 小节目录

### [基础概念](01-foundations.md)

- [MDP/POMDP](01-foundations/01-mdp-pomdp.md)：把 agent、environment、state、observation、action、return、value、advantage 和 episode 串成机器人任务闭环。
- [奖励](01-foundations/02-reward-design.md)：从 sparse/dense reward、success signal、shaping、惩罚项和安全边界设计可调试的机器人奖励。

### [经典算法](02-algorithms.md)

- [Q 学习与深度 Q 网络](02-algorithms/01-q-learning-and-deep-q-network.md)：理解值函数、Bellman 更新、经验回放和目标网络。
- [策略梯度与 REINFORCE](02-algorithms/02-policy-gradient-and-reinforce.md)：理解直接优化策略、轨迹回报和高方差问题。
- [演员-评论家方法](02-algorithms/03-actor-critic.md)：理解 actor、critic、advantage 和 TD error。
- [信赖域策略优化](02-algorithms/04-trust-region-policy-optimization.md)：理解 KL 约束、trust region 和 PPO 的来源。
- [近端策略优化](02-algorithms/05-proximal-policy-optimization.md)：理解 clipped objective、advantage、rollout buffer、更新轮数和为什么 PPO 常作为机器人强化学习的第一条 baseline。
- [深度确定性策略梯度](02-algorithms/06-deep-deterministic-policy-gradient.md)：理解确定性策略梯度和连续动作 off-policy 控制。
- [双延迟深度确定性策略梯度](02-algorithms/07-twin-delayed-deep-deterministic-policy-gradient.md)：理解 twin critic、delayed update 和 target smoothing。
- [软演员-评论家](02-algorithms/08-soft-actor-critic.md)：理解 replay buffer、Q function、entropy bonus、temperature 和连续动作控制。
- [离线强化学习](02-algorithms/09-offline-reinforcement-learning.md)：区分 behavior cloning、offline RL、online RL，理解分布外动作和数据质量风险。
- [基于模型的强化学习](02-algorithms/10-model-based-reinforcement-learning.md)：TD-MPC2、DreamerV3 等模型类方法在机器人上的取舍。

### [RLINF](03-rlinf-vla-rl.md)

- [导读](03-rlinf-vla-rl/README.md)：单元结构与阅读方式。
- [框架总览与核心价值](03-rlinf-vla-rl/01-framework-overview-and-value.md)、[架构与设计理念](03-rlinf-vla-rl/02-architecture-and-design-philosophy.md)、[完整本地安装](03-rlinf-vla-rl/03-local-installation-guide.md)、[具身智能实战闭环](03-rlinf-vla-rl/04-end-to-end-embodied-practice.md)、[总结与展望](03-rlinf-vla-rl/05-conclusion-and-future-development.md)。

### [SimpleVLA-RL](04-simplevla-rl.md)

- [导读与运行准备](04-simplevla-rl/README.md)：单元结构、本地目录组织与仓库下载。
- [架构与算法](04-simplevla-rl/01-architecture-and-algorithms.md)、[环境搭建](04-simplevla-rl/02-setup-quickstart.md)、[配置与数据](04-simplevla-rl/03-config-data.md)、[模型代码流程](04-simplevla-rl/04-model-code-flow.md)（Trainer/Rollout/Actor 走读）、[SFT 冷启动与 RL 训练](04-simplevla-rl/07-sft-rl-training.md)、[OpenArm 实战](04-simplevla-rl/08-openarm-practice.md)与[故障排查](04-simplevla-rl/09-troubleshooting-index.md)。

### [足式运动控制 RL](05-legged-locomotion-rl.md)

- 四足/人形 locomotion 的任务建模、PPO+域随机化主线、教师-学生蒸馏、AMP 风格模仿与 sim2real 部署；是第 7 章 Loco-Manipulation VLA 和第 11 章 Unitree 平台默认存在的底层运动控制器的训练方法（待写）。

## 本章边界

本章覆盖基础概念、经典算法、两个 VLA-RL 框架实战（RLINF、SimpleVLA-RL），以及足式运动控制 RL。三章分工：第 5 章是工具层（在 Isaac Lab 等平台里怎么跑 RL），本章是方法层（算法原理与方法选型），第 11 章是部署迁移工程。训练调试与实战细节回到具体框架或 benchmark 页面处理。

## 本章实践产出

- 一份任务建模表，写清 observation、state、action、reward、termination、success 和 reset。
- 一个 PPO 或 SAC baseline，并记录随机策略、训练曲线、最终评测和视频证据。
- 一份奖励设计说明，区分 success reward、dense shaping、安全惩罚和不该泄漏的信息。
- 一份 RLINF 或 SimpleVLA-RL 代码阅读笔记，能从配置一路追到 rollout、reward、advantage/loss、checkpoint 和评测。

## 验收方式

- 能否把一个机器人抓取任务写成 MDP/POMDP，并指出哪些量是 observation、哪些量只是隐藏 state？
- 能否说明 PPO 为什么需要 rollout 后再更新，SAC 为什么可以复用 replay buffer，TD3 为什么要用双评论家缓解过估计？
- 看到 reward 曲线升高但 success 不变，能否判断是奖励黑客、探索不足、终止条件错误还是评测口径错误？
- 能否解释为什么 VLA RL 通常要从 SFT checkpoint 开始，而不是从随机初始化的大模型开始？
