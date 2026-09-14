# SP-VLA

SP-VLA 是 token pruning 路线上的免训练方法，SP 指它同时做模型调度（Scheduling）和 token 剪枝（Pruning）。在 OpenVLA、CogACT 这类 VLA 上，它把连续控制里两类冗余分开处理：动作序列里大量过渡步彼此接近，用一个轻量回归器外推就够，不必每步都跑完整 VLA；单帧图像里背景和无关区域的视觉 token 对当前动作贡献很小，进语言模型前先剪掉。两套机制都不改模型结构、不重新训练，作为一层推理优化叠在已有权重上。

加速来自时序冗余和空间冗余两头。调度按末端平移把动作分成 deliberative（抓取、转向这类精细步，跑完整 VLA）和 intuitive（平滑过渡步，用 Ridge 回归外推），剪枝按注意力与边缘联合打分保留重要 token、并让剪枝比例随速度自适应。LIBERO（OpenVLA 基座）上无损档 74.90% 成功率、1.35× 加速，激进档 71.90%、1.50×；SimplerEnv（CogACT 基座）上视觉匹配 2.15×、WidowX 2.41×，控制频率约翻倍；真机 Franka 端到端约 2.5×、成功率仅降 1 个百分点（论文报告）。

## 本节目标

- 建立对 SP-VLA 的整体认识：它在 token 剪枝路线里的定位、时序冗余与空间冗余的分工、免训练插拔的前提与加速量级。
- 理解 SP-VLA 的架构：动作类型感知的模型调度、spatial-semantic 双感知 token 剪枝两个模块如何协作。
- 理解调度这一半在哪一环降低开销：动作缓冲、跳步触发条件、Ridge 回归轻量生成器的源码实现与可调参数。
- 理解剪枝这一半在哪一环降低开销：Canny 边缘与注意力联合选 token、速度自适应剪枝比例的源码实现与加速数字。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [SP-VLA 是什么](03-sp-vla/01-what-is-sp-vla.md) | token 剪枝路线定位、与 FastV/VLA-Cache/EfficientVLA 的差别、时序与空间两类冗余、免训练与基座、加速整体量级 |
| [整体架构](03-sp-vla/02-architecture.md) | 动作类型感知的模型调度、spatial-semantic 双感知 token 剪枝两个模块的判据、输入输出与协作路径 |
| [模型调度源码](03-sp-vla/03-model-scheduling.md) | `predict_action` 调度器、`save_actions` 缓冲与触发、`fit_next_action` Ridge 回归生成器的实现、可调参数与消融 |
| [token 剪枝源码](03-sp-vla/04-token-pruning.md) | `edge_detection`/`map_edges_to_tokens`、`PrismaticVisionBackbone.forward` 的注意力打分与并集选 token、速度自适应比例、可调参数与加速数字 |

## References

- 论文：[SP-VLA: A Joint Model Scheduling and Token Pruning Approach for VLA Model Acceleration](https://arxiv.org/abs/2506.12723)
- 代码：[ChildTang/SP-VLA](https://github.com/ChildTang/SP-VLA)

## 导航

- 上一节：[EfficientVLA](02-efficientvla.md)
- 返回上级：[token / KV 优化](../04-token-cache-and-pruning.md)
- 下一节：[SP-VLA 是什么](03-sp-vla/01-what-is-sp-vla.md)
