# Octo

真实机器人系统里，数据来自不同实验室、不同机械臂、不同相机布局和不同任务标注方式；如果每换一个机器人就从零训练策略，成本会非常高。那么，能不能有一个不绑定特定机械臂、特定相机、特定任务的通用机器人策略？Octo 就是对这个问题的回答。

Octo 是一个开源的 generalist robot policy（通用机器人策略）。它不是把机器人动作当作语言 token 来生成，而是把图像、语言或目标图像组织成 token 序列，交给 Transformer 做上下文建模，再通过 diffusion action head（扩散式动作头）输出连续机器人动作。

它很适合放在 RT-1 和 OpenVLA 之间理解：RT-1 把连续动作离散成 token，让模型像做分类一样预测每一维落在哪个桶里；OpenVLA 更进一步，用语言模型直接生成action token。Octo 走的是第三条路：主干仍然是 Transformer，但动作不再离散成 token，而是交给一个 diffusion action head 直接输出连续动作 chunk（一次预测未来若干步动作）。再往后的 RDT 会把整个主干都做成 Diffusion Transformer，而 Octo 这里只是在 Transformer 主干上接一个较小的 diffusion action head。同样是 diffusion ，用在哪、用多大，是它们的关键区别，这一点留到 RDT 那节再展开。

## 阅读路线

| 章节 | 读完能回答 | 重点 |
|---|---|---|
| [Octo 理论基础](02-octo/01-theory.md) | `timestep_pad_mask` 和 `pad_mask_dict` 分别管什么？readout token 为什么不叫动作 token？diffusion head 预测噪声还是干净动作？ | blockwise-causal attention mask、diffusion action head 训练 / 采样对称关系、预训练与微调边界 |
| [Octo 实践：debug finetune 复现](02-octo/02-practice.md) | `--debug` 跑通能证说明什么？ | jax + scipy + transformers 版本组合、warmup_steps 联动陷阱、小步验证含义 |

## References

- [Octo project page](https://octo-models.github.io/)

## 导航

- 上一节：[RT-1](01-rt1.md)
- 返回上级：[常用库](../03-common-libraries.md)
- 下一节：[Octo 理论基础](02-octo/01-theory.md)