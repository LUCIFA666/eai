# IRIS

目标：说明 IRIS 如何用离散 autoencoder 和 autoregressive Transformer 建模世界动态，并在低样本设置中通过想象轨迹训练策略。

## 需要覆盖

- 离散 autoencoder 如何把观测压缩成 token。
- Autoregressive Transformer 如何预测未来 token dynamics。
- Imagined rollout 如何连接到策略训练。
- IRIS 和 RSSM/latent dynamics 路线的区别。
- 代码入口：https://github.com/eloialonso/iris

## 已完成的深入材料

- [IRIS 与 Delta-IRIS 学习指南](01-iris/01-study-guide.md)：两代方法的原理对照精读。
- [复现指南](01-iris/02-reproduction-guide.md)：Breakout 训练与评测的完整复现记录。

- 返回上级：[Token 化动态预测](../03-tokenized-dynamics-prediction.md)
