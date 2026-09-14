# FAST

FAST 是一套动作分词的编解码器：把一段连续动作先做离散余弦变换（DCT）转到频域，量化后再用字节对编码（BPE）压成少量离散 token，供自回归 VLA 按 next-token 预测。它替换的是 RT-2、OpenVLA 这类模型常用的逐维均匀分箱，压缩后 token 数贴近动作信号本身的复杂度，而不随控制频率线性膨胀。FAST 只做动作的编解码，不绑定特定 VLA 骨干。

## 本节目标

先建立 FAST 的整体印象：它替换什么、解决什么瓶颈、压缩到什么量级。再深入两块推理加速强相关的内容：DCT+BPE 编解码流水线为什么能把动作压成少量高信息 token，以及通用分词器 FAST+ 在跨本体数据上的压缩证据。策略模型侧（用 FAST token 训练 VLA、模型级成功率与延迟）不在本节展开。

## 学习路径

| 模块 | 主要内容 |
| --- | --- |
| [FAST 是什么](03-fast/01-what-is-fast.md) | 替换逐维均匀分箱、高频下 token 爆炸与边际信息趋零两个瓶颈、压缩比与 token 数的整体量级 |
| [DCT 与 BPE 编解码](03-fast/02-dct-bpe-codec.md) | 频域压缩为什么成立、五步编码流水线与可逆解码回路、两个不敏感的超参 |
| [通用分词器 FAST+](03-fast/03-universal-tokenizer.md) | 百万级动作块训练的通用词表、跨未见数据集的压缩泛化、与 VQ 基线的对比及 BPE 消融 |

## References

- 论文：[FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://arxiv.org/abs/2501.09747)
- 模型：[physical-intelligence/fast](https://huggingface.co/physical-intelligence/fast)
- 代码：[openpi](https://github.com/Physical-Intelligence/openpi)

## 导航

- 上一节：[Consistency Policy](02-consistency-policy.md)
- 返回上级：[动作生成加速](../02-action-generation.md)
- 下一节：[FAST 是什么](03-fast/01-what-is-fast.md)
