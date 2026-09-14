# PD-VLA

PD-VLA 针对的是 action chunking 与自回归解码叠加后的速度问题：一次预测多步动作能提升成功率，但动作序列随步数线性变长，逐 token 自回归解码随之变慢。它把这段自回归解码重写成一组非线性方程，用 Jacobi 式不动点迭代、配合 bidirectional attention，一次前向并行更新整串动作 token，迭代到不动点时得到与逐 token 贪心解一致的结果。整套加速只改解码循环，不重训、不改网络结构，因此和量化、缓存等方法正交可叠加。相比基座 LLaVA-VLA，执行频率提到 2.52×，其中并行解码单独贡献 1.28× 解码速度；LIBERO 平均成功率 94.7%、LIBERO-Long 91.7%，均为当时最好（论文报告）。

## 本节目标

先建立对 PD-VLA 的整体认识：它在 VLA 加速里的定位、它操作的底座 VLA 与动作编码结构。再深入并行解码这一推理核心：自回归解码怎么被改写成 Jacobi 并行迭代、bidirectional attention 与 fixed token 为什么能加速收敛、decoding horizon 怎么取又如何影响速度。最后落到整体评测：提速如何拆分到两个部件、与 token 剪枝路线的对比、仿真与真机结果。PD-VLA 没有公开代码实现，本节为纯理论页，不含复现步骤。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [PD-VLA 是什么](05-pd-vla/01-what-is-pd-vla.md) | 在 VLA 加速里的定位、action chunking 与解码慢的关系、免训练免改结构的三项特性、提速与精度量级 |
| [底座 VLA 与动作编码](05-pd-vla/02-architecture.md) | LLaVA-VLA 的输入与主体、256-bin 动作 tokenization、action chunking 与响应长度 l=37 |
| [Jacobi 并行解码](05-pd-vla/03-parallel-decoding.md) | 自回归写成非线性方程组、Jacobi 不动点迭代、bidirectional attention、fixed token、decoding horizon 取值与速度消融 |
| [整体加速效果与评测](05-pd-vla/04-results.md) | 提速拆解（chunking vs 并行解码）、token 剪枝为何失效、LIBERO 与真机结果、训练成本 |

## References

- 论文：[PD-VLA: Accelerating Vision-Language-Action Model Integrated with Action Chunking via Parallel Decoding](https://arxiv.org/abs/2503.02310)

## 导航

- 上一节：[Spec-VLA](04-spec-vla.md)
- 返回上级：[动作生成加速](../02-action-generation.md)
- 下一节：[PD-VLA 是什么](05-pd-vla/01-what-is-pd-vla.md)
