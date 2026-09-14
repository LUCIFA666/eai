# DayDreamer

目标：说明 DayDreamer 如何把 Dreamer 路线推进到真实机器人在线学习。它的重点不是提出全新的世界模型结构，而是验证 learned world model 和 latent imagination 能否在真实机器人闭环中工作。

## 需要覆盖

- DayDreamer 与 Dreamer 的关系：真实机器人扩展，不是 Dreamer 主版本迭代。
- 真实机器人在线学习的数据闭环：采样、训练、执行、再采样。
- 样本效率、reset 成本、安全边界和硬件约束。
- 为什么 DayDreamer 对具身智能重要：它连接了 world model RL 和真实机器人实验。
- 代码入口：https://github.com/danijar/daydreamer

- 返回上级：[从像素预测到潜变量想象](../01-pixel-to-latent-imagination.md)
