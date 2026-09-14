# JEPA 系列

目标：说明 JEPA（Joint Embedding Predictive Architecture）作为预测式表征学习框架，如何从图像扩展到视频世界模型和 action-conditioned 机器人控制。JEPA 系列只放在本文件中，不再拆分子页。

## 需要覆盖

- JEPA 的基本思想：不重建像素，而是在 embedding space 预测缺失区域或未来状态。
- I-JEPA：图像版，面向图像表征预测。
- V-JEPA：视频版，面向视频时空表征预测。
- V-JEPA 2：更强的视频世界模型版本，强调物理世界理解和预测能力。
- V-JEPA 2-AC：加入 action-conditioned 控制扩展，用少量机器人轨迹把 V-JEPA 2 接到机器人规划/控制。
- LeCun 提出的 JEPA 路线与世界模型、自监督学习的关系。
- 代码入口：https://github.com/facebookresearch/vjepa2

- 返回上级：[视觉表征动态预测](../02-visual-representation-dynamics.md)
