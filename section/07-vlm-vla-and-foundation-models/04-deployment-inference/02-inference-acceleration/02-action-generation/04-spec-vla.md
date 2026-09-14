# Spec-VLA

Spec-VLA 把投机解码（speculative decoding）用到 VLA 的动作生成上：让一个小的 draft 模型先快速草拟一串动作 token，大模型只用一次前向并行验证这串草稿，接受其中正确的前缀。它的验证模型直接用微调后的 OpenVLA-7B，原样不重训，draft 模型是 Eagle-2 风格的一个轻量网络。针对动作 token 接受率偏低的问题，Spec-VLA 引入松弛接受（relaxed acceptance），利用动作被离散成 bin 后序号之差即反映动作幅度之差这一点，把接受判定从逐 token 相等放宽到相邻若干个 bin，LIBERO 上最高提速 1.42×（论文报告）。

## 本节目标

先建立对 Spec-VLA 这个方法的整体认识：它在 VLA 加速里的定位、投机解码的基本盘、验证模型与 draft 模型的架构，以及 draft 模型怎么训出来。再深入理解推理路径上的两块加速核心：draft 与验证如何组成一次并行解码循环，以及松弛接受如何提高接受率、代价是什么。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [Spec-VLA 是什么](04-spec-vla/01-what-is-spec-vla.md) | 在 VLA 加速里的定位、投机解码基本盘、动作 token 的 bin 结构、提速的整体量级 |
| [验证模型与 draft 模型](04-spec-vla/02-architecture.md) | 冻结的 OpenVLA-7B 验证模型、Eagle-2 风格 draft 模型的组成、draft 怎么蒸馏训出来 |
| [投机解码流水线](04-spec-vla/03-speculative-decoding-pipeline.md) | draft 树草拟、tree-attention 并行验证、接受长度指标、严格接受为何在 VLA 失效 |
| [松弛接受](04-spec-vla/04-relaxed-acceptance.md) | bin 距离阈值 r、松弛接受判定与解码算法、提速与接受长度、阈值与精度的取舍 |

## References

- 论文：[Spec-VLA: Speculative Decoding for Vision-Language-Action Models with Relaxed Acceptance](https://arxiv.org/abs/2507.22424)
- 代码：[PineTreeWss/SpecVLA](https://github.com/PineTreeWss/SpecVLA)

## 导航

- 上一节：[FAST](03-fast.md)
- 返回上级：[动作生成加速](../02-action-generation.md)
- 下一节：[Spec-VLA 是什么](04-spec-vla/01-what-is-spec-vla.md)
