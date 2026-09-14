# LeWorldModel（LeWM）

目标：说明 LeWorldModel 如何作为端到端 JEPA latent world model，从像素直接学习 embedding dynamics，并支持快速规划。

## 需要覆盖

- LeWM 的建模对象：从像素到 latent/embedding dynamics。
- 它如何利用较少损失项稳定训练。
- 它和 DINO-WM、V-JEPA 的区别：是否依赖外部特征、是否端到端、如何接规划。
- 机器人规划接口和适用边界。
- 项目页：https://le-wm.github.io/

## 已完成的深入材料

- [论文精读](03-leworldmodel/01-paper-deep-dive.md)：面向新手的 LeWM 逐节讲解。
- [复现报告](03-leworldmodel/02-reproduction-report.md)：含 PushT 50 episode 真实评测（成功率 96%）与验证证据。

- 返回上级：[视觉表征动态预测](../02-visual-representation-dynamics.md)
