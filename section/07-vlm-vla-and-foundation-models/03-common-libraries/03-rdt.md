# RDT

RDT（Robotics Diffusion Transformer）是清华等机构提出的双臂操作扩散基础模型。它把图像、语言和机器人状态作为条件，用一个 1B 级参数的 Diffusion Transformer 主干，通过扩散采样生成未来 64 步连续动作。

让我们回顾一下之前两节：RT-1 用 action token 做分类，Octo 用 Transformer 主干接一个较小的 diffusion action head，RDT 则把**整个主干**做成扩散模型，并用一个 128 维的统一动作空间容纳从单臂到双臂、从关节控制到末端控制的几乎所有现代操作臂。它在 1M+ 个多机器人 episode 上预训练，又在 6K+ 条自采双臂数据上微调部署到 ALOHA。

## 阅读路线

| 章节 | 读完能回答 | 重点 |
|---|---|---|
| [RDT 理论基础](03-rdt/01-theory.md) | 128 维统一动作空间怎么填充 / 取回？条件为什么用 cross-attention 而不进 token 序列？`prediction_type=sample` 和预测噪声有什么区别？ | 统一动作空间填槽代码、交替 cross-attention、训练用 DDPM 1000 步 / 推理用 DPM-Solver 5 步 |
| [RDT 实践（一）：微调环境与数据准备](03-rdt/02-practice.md) | `agilex` 占位名为什么不用改？`dataset_stat.json` 的统计量在哪一步被用到？ | flash-attn wheel 选择、符号链接接模型、ManiSkill 加载器接入、`agilex` 统计复用原因 |
| [RDT 实践（二）：微调训练与验证](03-rdt/03-finetune.md) | `finetune_maniskill.sh` 里哪几处配置会让单机直接跑失败？训练存出的 checkpoint 为什么能直接被评测脚本加载？ | 多机配置删改、ZeRO-2 单机多卡启动、DeepSpeed checkpoint 格式自洽 |

## References

- [RDT 官方仓库](https://github.com/thu-ml/RoboticsDiffusionTransformer)

## 导航

- 上一节：[Octo](02-octo.md)
- 返回上级：[常用库](../03-common-libraries.md)
- 下一节：[RDT 理论基础](03-rdt/01-theory.md)
