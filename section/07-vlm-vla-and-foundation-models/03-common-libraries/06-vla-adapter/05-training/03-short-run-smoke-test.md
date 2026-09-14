# 短程训练链路检查

目标：在正式训练前，用少量 step 检查 dataloader、forward、backward、日志和 checkpoint 保存链路。

短程验证命令以 [LoRA 微调](01-lora-finetune-command.md) 中的 Spatial 低显存训练命令为模板，只临时缩短训练步数和保存间隔。它不是看模型效果，而是把训练链路问题提前暴露出来，避免正式训练数小时后才发现数据、显存或保存配置不对。

## 推荐改动

在正式 Spatial 命令基础上，只改下面几个参数：

```bash
--max_steps 20
--save_freq 10
--run_id_note VLA-Adapter--libero_spatial_no_noops--smoke
```

`save_freq` 要小于等于 `max_steps`，否则短程验证可能结束了还没触发保存。其它路径、dataset、proprio、LoRA 和 Pro 相关参数先保持不变，这样短程验证才能检查正式命令本身。

如果显存紧张，优先沿用 [LoRA 微调](01-lora-finetune-command.md) 中的低显存配置：`batch_size=1`、`grad_accumulation_steps=8`、单卡运行。短程验证通过后，再进入下一页恢复正式训练参数。

## 预期现象

| 现象 | 说明 |
| --- | --- |
| 日志能打印数据集和模型配置 | `FinetuneConfig` 和路径解析基本可用。 |
| 能进入训练 step | dataloader、collator、forward 至少跑通。 |
| loss 有数值而不是 NaN | action loss 计算基本可用。 |
| `$ARTIFACT_ROOT/runs` 下出现本次 run 对应的 checkpoint 目录 | 例如 `...--10_chkpt`、`...--20_chkpt`，说明保存链路可用。 |
| 本地 log 能持续写入 | 后续复查 warning、traceback 和 step 信息有依据。 |

如果命令中保留 `--merge_lora_during_training True`，第 10 step 触发保存时会同时做 LoRA merge，耗时可能明显长于普通训练 step。日志里可能反复看到 `Saving Model Checkpoint for Step 10` 和 `Saved merged model for Step 10`，这不一定是失败；如果后续继续推进到 `20/20`，并出现 `Max step 20 reached! Stopping training...`，就可以认为短程验证链路通过。

## 失败时优先查

1. `data_root_dir` 和 `dataset_name`。
2. `use_proprio` 和 batch 中的 proprio 字段。
3. action shape 与 `ACTION_DIM` / `NUM_ACTIONS_CHUNK`。
4. 显存、`batch_size` 和 `grad_accumulation_steps`。
5. 保存目录是否可写、磁盘空间是否充足。

## 导航

- 上一节：[训练配置与训练循环](02-training-config-and-loop.md)
- 返回上级：[LoRA 微调训练](../05-training.md)
- 下一节：[正式训练](04-full-run-training.md)
