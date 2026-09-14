# Dreamer

目标：说明 Dreamer 如何在 learned world model 的 latent imagination 中训练 actor-critic。它继承 PlaNet 的潜变量动力学，但把每步在线规划改成在模型内部想象轨迹并训练策略。

## 需要覆盖

- RSSM 世界模型、reward prediction、continue/discount prediction 的作用。
- Latent imagination 如何生成训练 actor-critic 的虚拟轨迹。
- Dreamer 相对 PlaNet 的关键变化：从 planning by optimization 转向 policy learning in imagination。
- 与 DreamerV2 / DreamerV3 的关系：后续版本主要增强 latent 表示、稳定性和跨域能力。

- 返回上级：[从像素预测到潜变量想象](../01-pixel-to-latent-imagination.md)
