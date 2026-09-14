# 正式训练

目标：在短程训练链路检查通过后，恢复正式训练参数并启动 Spatial LoRA 训练。

短程验证检查的是训练链路，正式训练会产生后续评测要使用的 checkpoint。开始正式训练前，需要确认 dataloader、forward、backward、日志写入和 checkpoint 保存都没有明显错误。

## 从短程验证恢复正式参数

如果上一页为了短程验证临时改过参数，正式训练前先恢复训练步数、保存频率和 run id：

```bash
--max_steps 400005
--save_freq 5000
--run_id_note VLA-Adapter--libero_spatial_no_noops--$current_time
```

`save_freq` 决定多久保存一次 checkpoint。`run_id_note` 不建议继续使用 `--smoke`，否则后续复查时容易把短程验证和正式训练产物混在一起。

## 沿用显存配置

正式训练仍然沿用 [LoRA 微调](01-lora-finetune-command.md) 中选择的显存档位。低显存单卡可以继续使用：

```bash
--batch_size 1
--grad_accumulation_steps 8
```

如果短程验证已经证明 24GB、40GB 或多卡配置能稳定运行，可以按前面的显存分档放大 `batch_size`、减少 `grad_accumulation_steps`，并同步调整 `CUDA_VISIBLE_DEVICES` 和 `--nproc-per-node`。如果只改 GPU 数，不改 batch 和累积步数，有效 batch 和训练耗时都会变。

## 启动前检查

| 检查项 | 说明 |
| --- | --- |
| 空闲 GPU | 用 `nvidia-smi` 确认目标 GPU 仍然空闲，尤其是共享服务器。 |
| 训练日志 | 日志写到 `$ARTIFACT_ROOT/logs`，文件名包含 suite 和时间，避免覆盖短程验证日志。 |
| 训练产物 | checkpoint 写到 `$ARTIFACT_ROOT/runs`；正式训练前确认 `ARTIFACT_ROOT` 所在磁盘空间充足。 |
| W&B | 如果使用 W&B，确认 `wandb_entity`、`wandb_project` 和网络状态。 |
| dataset | `data_name`、`--dataset_name` 和当前 suite 一致。 |
| checkpoint 保存 | `save_freq` 小于 `max_steps`，并符合预期保存间隔。 |

正式训练命令可以继续使用 `01-lora-finetune-command.md` 中的完整 Spatial 命令；这里不再复制一遍，避免两处命令后续不一致。

## 4×A100 Spatial Pro 实测正式训练

本教程实测使用 4 张 A100-SXM4-80GB 跑 `libero_spatial_no_noops`，配置为 `batch_size=16`、`grad_accumulation_steps=1`、`nproc-per-node=4`，有效 batch 为 64。训练保留 `max_steps=150005` 作为保护上限，但没有把它当作需要跑满的目标。

实测过程中，每 `5000` step 保存一个 merge 后 checkpoint。训练到约 `40000_chkpt` 时，完整 Spatial eval 已达到本轮最高成功率；`45000_chkpt` 持平，`50000_chkpt` 回落。因此最终在确认 `50000_chkpt` 已完整保存后，约 `53972` step 手动停止训练。这里的 `53972` 是实际停止记录，不是推荐训练步数；如果希望训练在 `50000_chkpt` 附近自然结束，可以把 `max_steps` 设成类似 `50005` 的保护上限。

这次训练从启动到手动停止约 `14:56`。这个时间包括模型加载、训练、周期性 checkpoint 保存和 merge。官方 README 中的小时数不宜理解成跑满 `max_steps` 的时间；更合理的口径是达到目标成功率前需要的训练时间。

## 什么时候停

`max_steps` 适合当保护上限，不适合当需要完成的目标。正式训练推荐按下面的顺序决定是否继续：

1. 确认 checkpoint 已按 `save_freq` 正常保存。
2. 对候选 checkpoint 跑完整 eval，而不是只看 loss。
3. 如果成功率进入平台区，或更晚 checkpoint 明显回落，就停止训练。

本次实测中，`30000_chkpt` 为 `98.2%`，`40000_chkpt` 为 `98.6%`，`45000_chkpt` 仍为 `98.6%`，`50000_chkpt` 回落到 `97.2%`。因此继续跑到 `150005` step 没有必要。这个停止判断来自候选 checkpoint 的完整 rollout eval，而不是 loss 最低或训练步数最多。

## 运行中看什么

正式训练期间，除了确认进程是否还在，也建议定期检查三类信号：

| 信号 | 关注点 |
| --- | --- |
| loss | 是否有数值、是否出现 NaN、是否长时间异常震荡。 |
| step time | 是否明显变慢，是否可能遇到 I/O、显存或保存阶段卡顿。 |
| checkpoint | 是否按 `save_freq` 在 `$ARTIFACT_ROOT/runs` 下生成本次 run 对应的 `...--N_chkpt` 目录。 |

如果训练中途失败，优先保留本地 log、启动命令、GPU 配置和已经生成的 checkpoint 列表。这些信息会在后面的日志复查和排错中使用。

## 正式训练结束后

正式训练完成后，下一步不是立刻跑 eval，而是先确认 checkpoint 目录是否完整、merge 后目录是否可加载。确认完成后再进入训练日志页复查 loss 和运行过程，最后把可加载 checkpoint 交给评测模块。

## 本页小结

- 短程验证通过后，先恢复 `max_steps`、`save_freq` 和非 smoke 的 `run_id_note`。
- 正式训练沿用前面选择的显存档位，但要同步考虑 GPU 数、batch 和累积步数。
- `max_steps` 是上限；正式训练是否停止应由 checkpoint 完整 eval 的成功率决定。
- 正式训练完成后，先检查 checkpoint / merge，再读训练日志，最后进入 eval。

## 导航

- 上一节：[短程训练链路检查](03-short-run-smoke-test.md)
- 返回上级：[LoRA 微调训练](../05-training.md)
- 下一节：[Checkpoint 保存与合并](05-checkpoint-save-and-merge.md)
