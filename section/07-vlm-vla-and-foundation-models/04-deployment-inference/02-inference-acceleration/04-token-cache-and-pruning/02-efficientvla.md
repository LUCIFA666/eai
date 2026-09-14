# EfficientVLA

EfficientVLA 属于 token 剪枝这条路线，但把剪枝放进一个更完整的免训练框架：针对 CogACT 这类带 diffusion 动作头的 VLA，它同时压缩三处冗余，即按层间相似度剪除语言模块中作用小的层、用 task-aware 的方式筛出一组紧凑视觉 token、在扩散动作头里缓存并复用相邻去噪步的中间特征。它不改模型结构、不重新训练，作为一层结构化推理优化叠加在 CogACT 权重上。

单点优化很快触及瓶颈。前一节 VLA-Cache 只跨帧复用静态视觉 token 的 KV，语言模块进入显存受限区后收益饱和，在 CogACT 上仅 1.38× 加速。EfficientVLA 的出发点是：视觉 token、语言模块层深、扩散去噪步这三处冗余分处算力受限区与显存受限区，只优化其中一处，另一处会立即成为新瓶颈，因此三处一起压缩才能突破单点上限。在 SIMPLER 上，保留 22 层、56 个视觉 token 的配置把 FLOPs 降到 28.9%、单步推理加速 1.93×，平均成功率仅降 0.6 个百分点（论文报告）。

## 本节目标

- 建立对 EfficientVLA 的整体认识：它在 token 剪枝路线里的定位、与 VLA-Cache/FastV 的差别、免训练叠加的前提，以及三处冗余与整体加速量级。
- 理解 EfficientVLA 的架构：CogACT 三模块的数据流，层剪枝、视觉 token 筛选、扩散特征缓存分别插在哪一环，以及模块级瓶颈落在算力受限区还是显存受限区。
- 理解三条策略各自在哪一环降低推理开销：层重要度打分与非连续剪枝、task-relevance 与多样性驱动的视觉 token 选择、扩散头的定步长特征缓存，以及可调参数与加速数字。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [EfficientVLA 是什么](02-efficientvla/01-what-is-efficientvla.md) | token 剪枝路线定位、与 VLA-Cache/FastV 的对照、免训练与基座 CogACT、三处冗余、加速整体量级 |
| [整体架构](02-efficientvla/02-architecture.md) | CogACT 三模块与数据流、三条策略的插入点、模块级瓶颈分析（算力受限区与显存受限区）、组件消融 |
| [三条加速策略](02-efficientvla/03-acceleration.md) | 层重要度打分与非连续剪枝、task-relevance 加多样性的视觉 token 选择、扩散头定步长特征缓存、可调参数与主结果 |

## References

- 论文：[EfficientVLA: Training-Free Acceleration and Compression for Vision-Language-Action Models](https://arxiv.org/abs/2506.10100)

## 导航

- 上一节：[VLA-Cache](01-vla-cache.md)
- 返回上级：[token / KV 优化](../04-token-cache-and-pruning.md)
- 下一节：[EfficientVLA 是什么](02-efficientvla/01-what-is-efficientvla.md)
