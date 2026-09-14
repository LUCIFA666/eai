# 面向控制的潜变量动力学

目标：梳理以控制性能为目标设计 latent dynamics 的世界模型路线。这类方法不是为了重建像素，而是把任务奖励、价值函数和动作优化纳入世界模型设计，使 latent model 直接服务连续控制。

## 子页

- [TD-MPC](04-control-oriented-latent-dynamics/01-td-mpc.md)：学习 Task-Oriented Latent Dynamics (TOLD) 与价值函数，在 latent space 里用 MPPI / MPC 做动作优化。
- [TD-MPC2](04-control-oriented-latent-dynamics/02-td-mpc2.md)：TD-MPC 的规模化版本，覆盖多任务连续控制和跨 embodiment 训练。
