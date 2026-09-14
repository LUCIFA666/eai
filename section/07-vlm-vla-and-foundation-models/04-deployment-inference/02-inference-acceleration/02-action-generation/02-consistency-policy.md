# Consistency Policy

Diffusion Policy 把动作生成建模成从噪声逐步去噪的过程，一次动作要沿轨迹迭代很多步：DDPM 常用约 100 步，DDiM 约 15 步，步数直接决定这一段的延迟。在缺少高端 GPU 的移动机械臂、无人机等平台上，这样的动作生成速度无法满足实时控制的延迟预算。Consistency Policy 以步数为主攻方向，在保持 Diffusion Policy 精度的前提下，把推理降到一步或少数几步。

## 本节目标

本节先建立 Consistency Policy 的整体印象与架构，再聚焦推理路径上的提速机制：一致性蒸馏怎么把多步去噪压成一步、单步与三步推理的取舍，以及这些改动落到仓库哪些源码入口。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [Consistency Policy 是什么](02-consistency-policy/01-what-is-consistency-policy.md) | 采样步数为何是延迟主因、教师→蒸馏→少步的三段式、论文报告的提速与精度 |
| [架构](02-consistency-policy/02-architecture.md) | 1D 卷积 UNet 主干与观测条件、教师（EDM，确定性 ODE）与学生（CTM，停止时间 s）的结构差异 |
| [一致性蒸馏](02-consistency-policy/03-consistency-distillation.md) | CTM-local 一致性与 DSM 联合损失、s→0 dropout、warm-start，以及各机制的消融证据 |
| [少步推理](02-consistency-policy/04-few-step-inference.md) | 单步与三步推理的写法与取舍、部署调用链、提速的收益与代价 |

## References

- 论文：[Consistency Policy: Accelerated Visuomotor Policies via Consistency Distillation](https://arxiv.org/abs/2405.07503)
- 代码：[Aaditya-Prasad/Consistency-Policy](https://github.com/Aaditya-Prasad/Consistency-Policy)

## 导航

- 上一节：[OpenVLA-OFT](01-openvla-oft.md)
- 返回上级：[动作生成加速](../02-action-generation.md)
- 下一节：[Consistency Policy 是什么](02-consistency-policy/01-what-is-consistency-policy.md)
