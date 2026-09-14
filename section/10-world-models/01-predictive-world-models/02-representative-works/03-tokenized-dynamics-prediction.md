# Token 化动态预测

目标：梳理把环境动态建模成离散 token 序列预测的世界模型路线。这类方法通常先把观测压缩成离散 token，再用 Transformer 或自回归模型预测未来 token，并用想象轨迹训练策略。

## 子页

- [IRIS](03-tokenized-dynamics-prediction/01-iris.md)：用离散 autoencoder + autoregressive Transformer 建模世界动态。
- [Delta-IRIS](03-tokenized-dynamics-prediction/02-delta-iris.md)：IRIS 的后续改进，关注更高效的 context-aware tokenization。
