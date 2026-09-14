# PlaNet

目标：说明 PlaNet 在预测式世界模型中的位置：从像素学习 RSSM 潜变量动力学，并在 latent space 中用 CEM 做在线规划。PlaNet 是 Dreamer 路线的直接前身，但不应写成 Dreamer 系列成员。

## 需要覆盖

- 从 image observation 到 latent state 的建模流程。
- RSSM / latent dynamics 如何预测未来 latent state。
- CEM 在 latent space 中搜索动作序列的方式。
- PlaNet 和 Dreamer 的关系：PlaNet 更偏在线规划，Dreamer 转向 latent imagination actor-critic。
- 项目页：https://planetrl.github.io/

- 返回上级：[从像素预测到潜变量想象](../01-pixel-to-latent-imagination.md)
