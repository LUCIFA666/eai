# BitVLA

BitVLA 是量化路线上的一个方法：把 VLA 的主干直接设计成原生 1-bit，而不是对训好的全精度模型做训练后量化。语言主干用 BitNet b1.58 2B4T，权重取三值 {−1, 0, 1}、激活用 INT8；视觉编码器 SigLIP-L 经一个 Quantize-then-Distill 阶段压缩到 1.58-bit 权重加 INT8 激活；连接层和动作头保留全精度。动作生成沿用 OpenVLA-OFT 的并行解码加动作分块，因此它的推理加速不来自动作生成方式，而来自主干和视觉编码器的低比特化。

低比特直接换来显存和算力的下降：三值权重按约 1.58-bit 存储，线性层的矩阵乘退化为整数加减，浮点只剩每元素缩放。BitVLA 总参 3.0B、显存 1.4GB，约为全精度 OpenVLA-OFT 的十一分之一，而 LIBERO 平均成功率 96.0 对 97.1，仅低约 1.1 个百分点（论文报告）。

## 本节目标

- 建立对 BitVLA 的整体认识：它在量化路线里的定位、什么被量化到三值、什么保留全精度，以及加速来自哪里。
- 理解 BitVLA 的架构：SigLIP 视觉编码器、连接层、BitNet 主干与动作头如何连接，一段动作如何生成。
- 理解 BitVLA 在哪一环节降低推理开销：三值权重和 INT8 激活如何降低显存与计算量，以及低比特视觉编码器靠什么维持精度。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [BitVLA 是什么](03-bitvla/01-what-is-bitvla.md) | 量化路线定位、原生 1-bit 与训练后量化的差别、量化范围与全精度部分、显存与精度的整体量级 |
| [整体架构](03-bitvla/02-architecture.md) | SigLIP 加连接层加 BitNet 主干加动作头的组成、三阶段训练流水线、沿用 OFT 的并行解码与动作生成路径 |
| [低比特量化](03-bitvla/03-low-bit-quantization.md) | 权重三值与 INT8 激活的量化器、BitLinear 覆盖哪些层、低比特为何降低显存与计算量、在线量化与真实打包的差别、加速数字 |
| [Quantize-then-Distill](03-bitvla/04-quantize-then-distill.md) | 1.58-bit 视觉编码器的量化感知训练、全精度 teacher 的逐层 MSE 对齐、数据效率与消融收益 |

## References

- 论文：[BitVLA: 1-bit Vision-Language-Action Models for Robotics Manipulation](https://arxiv.org/abs/2506.07530)
- 代码：[ustcwhy/BitVLA](https://github.com/ustcwhy/BitVLA)

## 导航

- 上一节：[TinyVLA](02-tinyvla.md)
- 返回上级：[模型压缩](../03-model-compression.md)
- 下一节：[BitVLA 是什么](03-bitvla/01-what-is-bitvla.md)
