# 视觉表征动态预测

目标：梳理不直接重建像素，而是在视觉表征或 embedding 空间预测动态的世界模型路线。这类方法的核心问题是：预测什么样的视觉特征，如何让预测结果对机器人规划和控制有用。

## 子页

- [DINO-WM](02-visual-representation-dynamics/01-dino-wm.md)：在 DINOv2 patch feature 上学习 visual dynamics。
- [JEPA 系列](02-visual-representation-dynamics/02-jepa-series.md)：覆盖 I-JEPA、V-JEPA、V-JEPA 2、V-JEPA 2-AC，不再继续拆分。
- [LeWorldModel（LeWM）](02-visual-representation-dynamics/03-leworldmodel.md)：端到端 JEPA latent world model。
- [Fast-LeWM](02-visual-representation-dynamics/04-fast-lewm.md)：LeWM 的快速规划改进。
