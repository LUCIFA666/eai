# VLA-Cache

VLA-Cache 是 token cache 路线上的免训练方法：在 OpenVLA 这类自回归 VLA 上，把上一帧已经算过、当前帧几乎没变的视觉 token 的 key-value 缓存下来跨控制步复用，只对变化明显或任务相关的 token 重新计算。它不改模型结构、不重新训练，作为一层推理优化叠加在已有权重上。

加速来自时序冗余。闭环操作里相邻相机帧高度重叠，背景和远离操作点的物体几乎不动，但 OpenVLA 每一步都把全部视觉 token 重新编码一次。标准 KV cache 只消除单次自回归解码内部、序列方向上的重复，不覆盖跨帧的视觉重复。VLA-Cache 用帧间 patch 相似度找出静态区域，复用它们缓存的 KV，按复用比例降低语言解码器这段开销。这与 FastV、SparseVLM 这类单帧 token 剪枝方法方向不同：后者在一帧之内丢弃 token，而 VLA-Cache 跨帧复用 token，更贴合逐帧推理的控制场景。在 LIBERO 上，它把 OpenVLA 的 FLOPs 降约 27%、单步延迟从 51.91ms 降到 31.83ms，平均成功率仅降 0.3 个百分点（论文报告）。

## 本节目标

- 建立对 VLA-Cache 的整体认识：它在 token cache 路线里的定位、跨帧复用与单帧剪枝的差别、免训练插拔的前提。
- 理解 VLA-Cache 的架构：静态 token 选择、任务相关过滤、层自适应复用三个阶段如何决定复用哪些 token，以及一帧动作如何借上一帧缓存生成。
- 理解 VLA-Cache 在哪一环节降低推理开销：帧间静态 patch 检测、任务相关剔除、层自适应比例的源码实现，KV 拼接落在何处，以及可调参数与加速数字。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [VLA-Cache 是什么](01-vla-cache/01-what-is-vla-cache.md) | token cache 路线定位、跨帧复用与单帧剪枝（FastV/SparseVLM）的差别、复用与重算的划分、免训练与基座模型、加速整体量级 |
| [整体架构](01-vla-cache/02-architecture.md) | 静态 token 选择、任务相关过滤、层自适应复用三阶段，KV 复用机制与一帧动作的生成路径 |
| [跨帧 token 缓存](01-vla-cache/03-token-caching.md) | `find_static_patches`、`task_relevant_selection`、`get_layer_mask_schedule` 的实现，config 挂载、跨帧 cache 携带与裁剪、可调参数、FLOPs 与延迟 |

## References

- 论文：[VLA-Cache: Efficient Vision-Language-Action Manipulation via Adaptive Token Caching](https://arxiv.org/abs/2502.02175)
- 代码：[siyuhsu/vla-cache](https://github.com/siyuhsu/vla-cache)

## 导航

- 上一节：[token / KV 优化](../04-token-cache-and-pruning.md)
- 返回上级：[token / KV 优化](../04-token-cache-and-pruning.md)
- 下一节：[VLA-Cache 是什么](01-vla-cache/01-what-is-vla-cache.md)
