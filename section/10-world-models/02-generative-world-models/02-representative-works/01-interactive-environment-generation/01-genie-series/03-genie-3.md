# Genie 3

## 官方资源

| 资源 | 作用 |
| --- | --- |
| [Genie 3 官方介绍](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/) | 查看实时交互、环境一致性、Promptable World Events 和智能体演示 |
| [Genie 模型页面](https://deepmind.google/models/genie/) | 查看 Genie 3 当前能力、自然世界案例和 Project Genie |
| [Genie Prompt Guide](https://deepmind.google/models/genie/prompt-guide/) | 学习环境、角色和运动方式的提示词设计 |
| [Project Genie](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/) | 了解世界创建、探索和 Remix 原型 |
| [Project Genie 与 Street View](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie-expands/) | 了解如何使用现实地点图像创建生成世界 |
| [SIMA 2](https://deepmind.google/blog/sima-2-an-agent-that-plays-reasons-and-learns-with-you-in-virtual-3d-worlds/) | 查看具身智能体如何在 Genie 3 世界中行动和学习 |

## 专题页面

每个专题页面均可独立阅读。

| 页面 | 核心问题 |
| --- | --- |
| [概览与问题设定](03-genie-3/01-overview-and-problem-setting.md) | Genie 3 是什么，为什么普通视频生成不能直接等同于世界模拟 |
| [实时可交互世界生成](03-genie-3/02-real-time-interactive-world-generation.md) | 文本和图像如何成为世界入口，720p 和 20–24 FPS 意味着什么 |
| [物理、自然与多样世界](03-genie-3/03-physical-natural-and-diverse-worlds.md) | 模型可以生成哪些物理现象、生态、动画和历史场景 |
| [长时一致性与环境记忆](03-genie-3/04-long-horizon-consistency-and-memory.md) | 数分钟一致性和一分钟视觉记忆如何支持持续交互 |
| [Promptable World Events](03-genie-3/05-promptable-world-events.md) | 文本事件如何在导航过程中改变天气、对象和角色 |
| [Project Genie 与世界创作](03-genie-3/06-project-genie-and-world-creation.md) | World Sketching、Exploration、Remixing 和 Street View 如何工作 |
| [具身智能体、评测与局限](03-genie-3/07-embodied-agents-evaluation-and-limitations.md) | SIMA 如何使用生成世界，以及如何评价环境可靠性 |

## 本章定位

Genie 3 是 Google DeepMind 提出的通用世界模型。它可以根据文本描述生成动态环境，并在用户或智能体持续输入动作时，实时生成下一时刻的世界画面。

官方首发资料给出的代表性能力包括：

```text
720p 视觉输出
约 24 FPS 的实时交互
数分钟连续环境一致性
最长约一分钟的部分视觉记忆
物理和自然现象生成
Promptable World Events
具身智能体在生成世界中执行任务
```

当前 Genie 模型页面将其实时速度表述为约 20–24 FPS。

其交互闭环可以表示为：

```text
文本或图像定义世界起点
-> 用户或智能体输入动作
-> 模型生成下一观察
-> 新观察进入下一轮预测
-> 世界随探索继续扩展
```

普通视频生成通常一次性决定后续内容；Genie 3 则让动作持续参与生成过程，使世界未来随交互不断变化。

Project Genie 是由 Genie 3 驱动的实验性用户原型，它将底层世界模型组织成 World Sketching、World Exploration、World Remixing 和 Street View Grounding 等流程。
