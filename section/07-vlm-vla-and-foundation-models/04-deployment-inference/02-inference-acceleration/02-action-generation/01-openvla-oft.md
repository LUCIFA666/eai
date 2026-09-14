# OpenVLA-OFT

OpenVLA 用自回归逐 token 解码动作，七维动作要七次串行前向才能解完一步，单步动作生成只有 3–5 Hz，达不到高频控制需要的 25–50 Hz。OpenVLA-OFT 是在同一个 OpenVLA 主干上换一套微调配方（Optimized Fine-Tuning）：把动作生成段从逐 token 自回归换成一次前向并行输出整段动作，同时把离散动作 token 换成连续动作、用 L1 回归训练。动作生成这一段的吞吐因此从约 4 Hz 提到百 Hz 量级，LIBERO 四个任务套件的平均成功率也从 76.5% 提到 97.1%（论文报告）。

## 本节目标

本节先建立 OFT 的整体印象和架构，再聚焦推理路径上的提速机制：并行解码怎么去掉串行依赖、action chunking 怎么一次出整段，以及这些改动落到仓库哪些源码入口。随后落到复现：环境与数据准备、OFT 配方 LoRA 微调，以及在 LIBERO-Spatial 上评测自训 checkpoint。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [OpenVLA-OFT 是什么](01-openvla-oft/01-what-is-openvla-oft.md) | 自回归解码的瓶颈在哪、OFT 的三项改动总览、论文报告的提速与精度数字 |
| [架构](01-openvla-oft/02-architecture.md) | 输入与主体、连续动作替代离散 token、L1 与 diffusion 两个动作头变体、与原始 OpenVLA 的差异 |
| [并行解码](01-openvla-oft/03-parallel-decoding.md) | 空动作 embedding、双向注意力、单次前向取出整段，以及 action chunk 的切分 |
| [推理调用链](01-openvla-oft/04-inference-path.md) | `predict_action()` 的完整调用链、提速落在哪一步、训练与推理的一致性约束 |
| [环境与数据准备](01-openvla-oft/05-environment-and-data.md) | conda 环境与 Flash Attention 2、LIBERO 仿真安装、版本冲突钉版、RLDS 数据下载 |
| [训练](01-openvla-oft/06-training.md) | OFT 配方 LoRA 微调的开关配置、收敛判据、本地 50K 缩短版 loss 曲线 |
| [评测](01-openvla-oft/07-evaluation.md) | LIBERO-Spatial 成功率（自训 vs 论文报告）与 rollout 示例 |

## References

- 论文：[Fine-Tuning Vision-Language-Action Models: Optimizing Speed and Success](https://arxiv.org/abs/2502.19645)
- 代码：[moojink/openvla-oft](https://github.com/moojink/openvla-oft)

## 导航

- 上一节：[动作生成加速](../02-action-generation.md)
- 返回上级：[动作生成加速](../02-action-generation.md)
- 下一节：[OpenVLA-OFT 是什么](01-openvla-oft/01-what-is-openvla-oft.md)
