# VLA 的 RL 后训练

本节介绍在 SFT 之后用强化学习进一步提升 VLA 的「后训练」范式。要讲的内容：二值 / 稀疏任务奖励的设计、GRPO / PPO 等策略优化在 VLA 上的应用、世界模型辅助的可验证奖励，以及与第 9 章强化学习框架的衔接。参考实现：VLA-RL https://github.com/VLA-RL/VLA-RL ；VLA-RFT（世界模型辅助 + GRPO）https://github.com/OpenHelix-Team/VLA-RFT ；底层 RL 基础设施 veRL https://github.com/volcengine/verl 。
