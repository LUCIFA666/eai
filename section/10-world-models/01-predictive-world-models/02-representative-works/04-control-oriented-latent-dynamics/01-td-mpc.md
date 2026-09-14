# TD-MPC

目标：说明 TD-MPC 如何学习 Task-Oriented Latent Dynamics (TOLD) 与价值函数，并在 latent space 中用 MPPI / MPC 做动作优化。

## 需要覆盖

- TOLD 的建模对象：latent dynamics、reward、value。
- 如何把 model-free value learning 和 model-based planning 结合。
- MPPI / MPC 在 latent space 中的动作优化流程。
- TD-MPC 为什么是面向控制的潜变量动力学，而不是像素重建世界模型。
- 项目页：https://www.nicklashansen.com/td-mpc/

- 返回上级：[面向控制的潜变量动力学](../04-control-oriented-latent-dynamics.md)
