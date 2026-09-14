# zero-shot 推理

本节介绍 VLA 的免微调（zero-shot）部署，以及推理期的适配技术。要写清的内容：

- 免微调直接部署：何时可不微调直接用通用 VLA，以及零样本 / 少样本 / 微调的边界
- 推理期适配技术：prompting 与语言条件、in-context learning、test-time adaptation / test-time scaling、retrieval-augmented action、system prompt 与安全约束
- 零样本的边界与局限：分布漂移脆弱、依赖记忆化的视觉/位置线索、语言利用不足（具体模型如 RT-2/π0.5/Gemini Robotics 见 VLA 基础、常用库，本节只讲部署与推理期，不重复模型）
