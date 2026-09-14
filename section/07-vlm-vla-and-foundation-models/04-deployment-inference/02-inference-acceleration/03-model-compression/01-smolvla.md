# SmolVLA

SmolVLA 是一个总参数约 4.5 亿的紧凑 VLA：骨干用预训练的 SmolVLM2-500M，动作端接一个约 1 亿参数、用 flow matching 训练的 action expert。它只在社区采集的数据上做模仿学习训练，不依赖大规模机器人数据预训练，整套设计面向消费级和端侧算力。

在小型 VLA 这条机制里，SmolVLA 的做法不是压缩一个已有的大模型，而是从设计上就选小骨干，再在结构上进一步压低单次前向的开销：只用 VLM 的前若干层、把每帧视觉 token 压缩到 64 个、给 action expert 减窄并交替使用两种注意力。除了压缩单次前向，它还配了一套异步推理栈，把动作预测和执行解耦，进一步提高控制吞吐。

## 本节目标

- 建立对 SmolVLA 的整体认识：它在小型 VLA 里的定位、开销来自哪里、从哪几处压缩。
- 理解 SmolVLA 的架构：VLM 与 action expert 各是什么、怎么连、动作怎么生成。
- 理解 SmolVLA 在哪些环节加速推理：单次前向从哪几处压缩，以及异步推理如何提高控制吞吐。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [SmolVLA 是什么](01-smolvla/01-what-is-smolvla.md) | 小型 VLA 定位、4.5 亿参数与 SmolVLM2 骨干、社区数据训练、加速的整体量级与对 π0 的收益 |
| [整体架构](01-smolvla/02-architecture.md) | VLM（SigLIP 加 SmolLM2）与 flow matching action expert 的组成、连接、条件序列与动作生成路径 |
| [压缩单次前向](01-smolvla/03-compress-single-forward.md) | 层裁剪、视觉 token 压缩、action expert 减窄与交替注意力、少步积分与动作分块 |
| [异步推理](01-smolvla/04-async-inference.md) | 预测与执行解耦、动作队列与阈值、块重叠聚合、真机吞吐与延迟数字 |

## References

- 论文：[SmolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics](https://arxiv.org/abs/2506.01844)
- 模型：[lerobot/smolvla_base](https://huggingface.co/lerobot/smolvla_base)
- 代码：[huggingface/lerobot](https://github.com/huggingface/lerobot)（策略实现在 `src/lerobot/policies/smolvla/`）

## 导航

- 上一节：[模型压缩](../03-model-compression.md)
- 返回上级：[模型压缩](../03-model-compression.md)
- 下一节：[SmolVLA 是什么](01-smolvla/01-what-is-smolvla.md)
