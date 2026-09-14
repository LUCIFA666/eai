# 从像素预测到潜变量想象

目标：梳理从像素观测学习潜变量动力学，并在潜变量空间中规划或想象训练策略的代表工作。这条路线的核心是把高维观测压缩成 latent state，再学习 latent dynamics、reward、discount/continue 等预测头。

## 子页

- [PlaNet](01-pixel-to-latent-imagination/01-planet.md)：从像素学习 RSSM 潜变量动力学，并在 latent space 中用 CEM 做规划。
- [Dreamer](01-pixel-to-latent-imagination/02-dreamer.md)：从 PlaNet 的 latent dynamics 出发，在 latent imagination 中训练 actor-critic。
- [DreamerV2](01-pixel-to-latent-imagination/03-dreamerv2.md)：引入离散 latent，并在 Atari 等复杂任务上强化 Dreamer 路线的稳定性和表现。
- [DreamerV3](01-pixel-to-latent-imagination/04-dreamerv3.md)：固定超参数、跨域统一训练和更强的通用 world model agent；本页包含复现报告。
- [DayDreamer](01-pixel-to-latent-imagination/05-daydreamer.md)：将 Dreamer 路线推进到真实机器人在线学习。
