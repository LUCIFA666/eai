# Genie

Genie 是 Google DeepMind 提出的一种生成式可交互环境模型。它只使用视频进行训练，不要求视频同时提供键盘、手柄或机器人动作标签。
它与普通视频生成模型的关键区别是：用户或智能体可以在每个时间步继续输入动作，而不是只在视频生成前提供一次文本或图像提示。

## 官方资源

| 资源 | 作用 |
| --- | --- |
| [Genie 官方项目页](https://sites.google.com/view/genie-2024/home) | 查看平台游戏、手绘草图、真实照片和机器人场景的动态交互演示 |
| [Genie 原始论文](https://arxiv.org/abs/2402.15391) | 查看方法、数据集、实验结果、消融研究和可复现案例 |
| [Genie 论文 HTML](https://arxiv.org/html/2402.15391v1) | 在线阅读论文并查看高清结构图和实验图 |
| [Google DeepMind 论文页面](https://deepmind.google/research/publications/60474/) | 查看官方论文摘要和发表信息 |

## 专题页面

每个专题页面都可以独立阅读。既可以按照表格顺序学习，也可以直接进入感兴趣的部分。

| 页面 | 核心问题 |
| --- | --- |
| [概览与问题设定](01-genie/01-overview-and-problem-setting.md) | Genie 为什么需要从无动作标签视频中学习可交互环境 |
| [潜在动作学习](01-genie/02-latent-action-learning.md) | 模型如何从连续画面中发现并离散化 latent action |
| [模型组件与训练](01-genie/03-model-components-and-training.md) | Video Tokenizer、LAM 和 Dynamics Model 如何协同工作 |
| [交互生成与泛化](01-genie/04-interactive-generation-and-generalization.md) | Genie 如何从生成图、手绘草图、照片和未见场景中生成可控轨迹 |
| [机器人与智能体学习](01-genie/05-robotics-and-agent-learning.md) | latent action 如何用于机器人视频和无动作专家视频的策略学习 |
| [评测、局限与研究意义](01-genie/06-evaluation-limitations-and-significance.md) | 如何评价生成质量和可控性，以及 Genie 距离成熟世界模拟器还有多远 |


