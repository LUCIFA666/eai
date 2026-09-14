# Fast-LeWM

目标：说明 Fast-LeWM 如何改进 LeWorldModel 的规划效率，用 action-prefix prediction 替代逐步 latent rollout，以降低长视界预测和实时控制开销。

## 需要覆盖

- Fast-LeWM 与 LeWM 的关系：快速规划改进，不是完全独立路线。
- Action-prefix prediction 的作用。
- 长视界误差累积、规划开销和实时控制约束。
- 适合哪些机器人控制场景，哪些场景仍需要谨慎验证。
- 代码入口：https://github.com/Yuntian-Gao/Fast-LeWorldModel

## 已完成的深入材料

- [论文精读](04-fast-lewm/01-paper-deep-dive.md)：面向新手的 Fast-LeWM 逐节讲解。

- 返回上级：[视觉表征动态预测](../02-visual-representation-dynamics.md)
