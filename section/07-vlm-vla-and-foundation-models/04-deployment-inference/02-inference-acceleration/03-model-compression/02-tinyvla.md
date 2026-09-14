# TinyVLA

TinyVLA 是一条把 VLA 缩小并加速的路线：骨干换成十亿参数级以下的 Llava-Pythia 多模态模型，动作端用一个 diffusion policy 头直接回归连续动作，取代 OpenVLA 把动作离散成 token 再逐维自回归解码的方式。它不做 OpenX 这类大规模机器人预训练，而是用 LoRA 在目标任务数据上微调。这两处改动叠加，把单动作推理延迟从 7B OpenVLA 的 292ms 降到 14ms，约 20 倍，参数量少约 5.5 倍（论文报告，单卡 A6000）。

## 本节目标

- 建立对 TinyVLA 的整体认识：它在小型 VLA 里的定位、延迟来自哪两处、对应各改了什么。
- 理解 TinyVLA 的架构：Llava-Pythia VLM 与 diffusion policy 头各是什么、如何连接、一段动作如何生成。
- 理解 TinyVLA 在哪几处降低推理延迟：小骨干与 diffusion 头各贡献多少，以及少步扩散、动作分块、LoRA 合并的作用。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [TinyVLA 是什么](02-tinyvla/01-what-is-tinyvla.md) | 小型 VLA 定位、两处延迟根源、免机器人预训练与 LoRA 微调、加速整体量级与对 OpenVLA 的对比 |
| [整体架构](02-tinyvla/02-architecture.md) | Llava-Pythia（Pythia 加 CLIP）VLM 与 diffusion policy 头的组成、条件流水线、动作块的生成路径 |
| [降低推理延迟](02-tinyvla/03-fast-inference.md) | 延迟分解与两条杠杆、少步 DDIM 扩散、动作分块与开环执行、LoRA 合并、整体收益与代价 |

## References

- 论文：[TinyVLA: Towards Fast, Data-Efficient Vision-Language-Action Models for Robotic Manipulation](https://arxiv.org/abs/2409.12514)
- 代码：[liyaxuanliyaxuan/TinyVLA](https://github.com/liyaxuanliyaxuan/TinyVLA)

## 导航

- 上一节：[SmolVLA](01-smolvla.md)
- 返回上级：[模型压缩](../03-model-compression.md)
- 下一节：[TinyVLA 是什么](02-tinyvla/01-what-is-tinyvla.md)
