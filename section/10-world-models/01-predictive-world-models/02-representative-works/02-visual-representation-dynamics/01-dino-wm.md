# DINO-WM

目标：说明 DINO-WM 如何在 DINOv2 patch feature 上学习 visual dynamics，并用目标特征匹配支持 action sequence optimization。重点是预训练视觉表征如何降低世界模型训练难度。

## 需要覆盖

- 为什么不直接重建像素，而是在 DINOv2 feature space 预测动态。
- Visual dynamics 的输入、输出和训练信号。
- 目标特征匹配如何连接到动作序列优化。
- DINO-WM 与 JEPA / LeWM 路线的区别。
- 项目页：https://dino-wm.github.io/

## 已完成的深入材料

- [论文精读](01-dino-wm/01-paper-deep-dive.md)：面向新手的 DINO-WM 逐节讲解。
- [复现报告](01-dino-wm/02-reproduction-report.md)：PointMaze / PushT / Wall 的完整复现记录与结果证据。
- [复现命令清单](01-dino-wm/03-commands-by-purpose.md)：按作用分组的可执行命令。

- 返回上级：[视觉表征动态预测](../02-visual-representation-dynamics.md)
