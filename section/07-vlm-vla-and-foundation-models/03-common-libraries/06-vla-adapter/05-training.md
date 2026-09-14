# LoRA 微调训练

目标：读懂 VLA-Adapter LoRA 微调脚本如何把命令参数、RLDS 数据、模型组件、loss、optimizer 和 checkpoint 保存串起来。

本模块会沿着 `FinetuneConfig` 展开：`dataset_name`、`vlm_path`、`config_file_path`、`use_proprio`、`num_images_in_input`、`use_pro_version`、LoRA 参数和 checkpoint 保存逻辑如何串成一次可评测训练。

## 学习路径

| 页面 | 重点 |
| --- | --- |
| [LoRA 微调](05-training/01-lora-finetune-command.md) | 按显存条件准备 Spatial LoRA 训练命令，并理解完整参数表 |
| [训练配置与训练循环](05-training/02-training-config-and-loop.md) | 命令进入 `finetune.py` 后如何变成数据加载、模型 forward、loss 和保存 |
| [短程训练链路检查](05-training/03-short-run-smoke-test.md) | 把正式命令改成短程验证版本，检查训练链路 |
| [正式训练](05-training/04-full-run-training.md) | 短程验证通过后恢复正式参数、启动训练，并用 checkpoint eval 决定早停 |
| [Checkpoint 保存与合并](05-training/05-checkpoint-save-and-merge.md) | checkpoint 保存、merge、磁盘占用和评测候选选择 |
| [训练日志](05-training/06-training-logs.md) | 训练日志、loss、warning 和 checkpoint 选择线索怎么读 |

## 导航

- 上一节：[训练、评测与部署的一致性](04-model/06-training-eval-consistency.md)
- 返回上级：[VLA-Adapter](../06-vla-adapter.md)
- 下一节：[LoRA 微调](05-training/01-lora-finetune-command.md)
