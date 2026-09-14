# 模型结构与动作推理

目标：读懂 OpenVLA 模型侧的三段实现：Prismatic backbone 如何接收图像和指令，action tokenizer 如何表示连续动作，`predict_action` 如何返回 7 维动作。

上一单元已经跑通了 `predict_action`。这一单元继续往模型内部看：图像和指令进入 Prismatic VLM，连续动作被写成 Llama 可以生成的 tokens，推理时再把 tokens 解码成连续动作，并按 `unnorm_key` 选择统计量恢复尺度。

本单元聚焦模型侧实现：Prismatic backbone 怎样接收多模态输入，action tokenizer 怎样表示动作，`predict_action` 怎样把生成结果还原成连续动作。

## 学习路径

| 页面 | 重点 |
| --- | --- |
| [Prismatic Backbone](03-model-and-action-inference/01-prismatic-backbone.md) | OpenVLA 的 Prismatic 结构，视觉编码器、projector、LLM 和 checkpoint 变体。 |
| [Action Tokenizer](03-model-and-action-inference/02-action-tokenizer.md) | 连续动作怎样离散成 256 个 bins，并映射到 Llama tokenizer 词表末尾。 |
| [`predict_action` 动作推理](03-model-and-action-inference/03-predict-action.md) | HF 推理路径如何生成 action tokens、解码归一化动作，再按统计量反归一化。 |

## 模型侧和数据侧的分工

`ActionTokenizer` 处理的是归一化动作。它把 `[-1, 1]` 区间内的动作值离散到 bins，再映射到 token id。`predict_action` 会把模型生成的 token id 还原成归一化动作。

动作回到具体数据集尺度时，会用到 `q01`、`q99` 和 `mask`。这些统计量来自 checkpoint 中的 `norm_stats` 或本地目录里的 `dataset_statistics.json`。这里先看 `predict_action` 怎样读取和使用统计量；统计量文件的生成、保存和 key 来源，接着进入数据页核对。

## 源码入口

| 源码入口 | 作用 |
| --- | --- |
| `prismatic/vla/action_tokenizer.py` | 训练路径中的 action token 编码和解码。 |
| `prismatic/extern/hf/modeling_prismatic.py` | Hugging Face AutoClass 路径中的 `predict_action()`。 |
| `prismatic/models/vlas/openvla.py` | Prismatic 训练路径中的 `OpenVLA` 类和原生 `predict_action()`。 |

这三处源码回答的是同一条问题：OpenVLA 怎样把“图像 + 指令”变成动作 token，再把 token 变回连续动作。把这三处源码和 `dataset_statistics.json` 分开看，可以避免混淆 token decode、统计量选择和数据准备。

## 导航

- 上一节：[第一次 `predict_action`](02-setup/04-first-predict-action.md)
- 返回上级：[OpenVLA](../04-openvla.md)
- 下一节：[Prismatic Backbone](03-model-and-action-inference/01-prismatic-backbone.md)
