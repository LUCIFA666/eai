# 代表性工作

目标：按预测式世界模型的建模范式梳理代表工作，说明每类方法预测什么、如何学习动态、为什么和具身智能相关。

预测式世界模型不要按“能不能规划”这类应用方式简单分组，而要看模型本身如何表示和预测世界动态。本节分为四条路线：

- [从像素预测到潜变量想象](02-representative-works/01-pixel-to-latent-imagination.md)：PlaNet、Dreamer、DreamerV2、DreamerV3、DayDreamer。
- [视觉表征动态预测](02-representative-works/02-visual-representation-dynamics.md)：DINO-WM、JEPA 系列、LeWorldModel、Fast-LeWM。
- [Token 化动态预测](02-representative-works/03-tokenized-dynamics-prediction.md)：IRIS、Delta-IRIS。
- [面向控制的潜变量动力学](02-representative-works/04-control-oriented-latent-dynamics.md)：TD-MPC、TD-MPC2。

写作时每个子页都要避免写成论文列表。重点不是“列出所有工作”，而是写清楚这一类预测式世界模型的建模对象、训练信号、决策接口和机器人任务中的适用边界。
