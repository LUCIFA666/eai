# LoRA 微调

目标：理解 OpenVLA 原生 LoRA 微调的入口、训练脚本、日志指标、训练记录和 checkpoint 产物。

前面的数据章节已经讲到 `dataset_statistics.json`、`norm_stats` 和 `unnorm_key`。进入微调时，这些内容会重新出现：训练脚本会读取 RLDS 数据、计算动作 token、保存统计量；推理时再用这些统计量把 action tokens 还原成连续动作。

OpenVLA 提供两条训练路径。LoRA 微调通过 Hugging Face AutoClass 加载 `openvla/openvla-7b`，再用 PEFT 给线性层加低秩参数；全量微调走 Prismatic 训练脚本和 `openvla/openvla-7b-prismatic` checkpoint，资源要求和配置改动都更重。这里从 LoRA 路径开始，因为它是官方示例里的轻量微调入口，也和前面最小 `predict_action` 路径衔接得最直接。

## LoRA 微调链路

LoRA 微调链路包含命令、脚本、日志和训练记录：

| 页面 | 重点 |
| --- | --- |
| [LoRA 启动命令](05-finetuning/01-lora-command.md) | 命令形状、核心参数、显存和 batch 设置。 |
| [`finetune.py` 训练流程](05-finetuning/02-finetune-script.md) | 模型加载、LoRA 包装、RLDS 数据、batch transform 和训练循环。 |
| [训练日志与 checkpoint](05-finetuning/03-logs-and-checkpoints.md) | `train_loss`、`action_accuracy`、`l1_loss`、adapter、merged checkpoint 和统计量文件。 |
| [LoRA 训练参考](05-finetuning/04-training-reference.md) | smoke run、从短跑切到长跑、训练曲线、关键 step 指标和结果判断。 |

这组页面合在一起回答一个具体问题：训练命令启动后，数据怎样变成 action token 监督信号，哪些参数会影响显存和保存结果，训练日志和曲线能说明到哪一步。

## 训练指标的证据范围

LoRA 训练日志主要用于判断训练是否在正常拟合数据。`action_accuracy` 统计动作 token 是否预测正确，`l1_loss` 来自 token 解码后的连续动作距离。它们能帮助检查数据、action tokenizer 和训练循环，但任务完成情况仍要靠 rollout 评测。

这一区分很重要。一个能正常保存 checkpoint 的短训练，说明加载、反向传播和保存链路可用；一个收敛良好的训练曲线，说明模型拟合了当前训练集；LIBERO 或 Bridge 中的闭环表现，需要到评测页面结合环境、图像处理和动作执行一起看。

## 本页小结

- LoRA 微调使用 `vla-scripts/finetune.py`，沿用 Hugging Face 加载和 PEFT LoRA 包装。
- 数据侧仍然依赖 RLDS / OXE 管线，训练脚本会保存后续推理需要的 `dataset_statistics.json`。
- `action_accuracy`、`l1_loss` 和 loss 曲线是训练侧结果，还不足以代表 rollout 表现。
- 全量微调属于另一条训练路径，入口、checkpoint 和训练脚本都和 LoRA 不同。

## 导航

- 上一节：[数据与动作统计量](04-data-and-statistics.md)
- 返回上级：[OpenVLA](../04-openvla.md)
- 下一节：[LoRA 启动命令](05-finetuning/01-lora-command.md)
