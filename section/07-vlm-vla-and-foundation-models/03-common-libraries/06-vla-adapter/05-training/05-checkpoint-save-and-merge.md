# Checkpoint 保存与合并

目标：理解训练输出目录里哪些文件会被后续评测和部署使用。

`finetune.py` 的保存逻辑不仅保存 backbone 或 LoRA 权重，还会保存 action head、proprio projector、processor/config 和 dataset statistics 等评测所需组件。`merge_lora_during_training=True` 时，脚本会在保存阶段生成更方便评测加载的目录。

## 训练产物

| 产物 | 用途 |
| --- | --- |
| `$ARTIFACT_ROOT/runs/<run_id>/` | 本次 run 的基础输出目录，通常包含 `dataset_statistics.json` 等运行信息。 |
| `$ARTIFACT_ROOT/runs/...--N_chkpt/` | 按 `save_freq` 生成的 checkpoint 目录，包含模型组件权重，也是后续 eval / deploy 最关心的目录。 |
| `$ARTIFACT_ROOT/logs/*.log` | 本地训练日志，用来复查启动参数、warning、traceback 和 step 信息。 |
| W&B run | 可选，用于画 loss 曲线和对比多次运行。 |
| merge 后 checkpoint | 评测时更方便；如果训练中 merge 很慢，可以考虑训练后单独 merge。 |

每个保存点可能占用数 GB，正式训练前应确认 `ARTIFACT_ROOT` 所在磁盘空间充足。如果 `save_latest_checkpoint_only=False`，多个保存点会继续累积占用空间。

## 本次实测产物

4×A100 Spatial Pro 正式训练中，`save_freq=5000`、`save_latest_checkpoint_only=False`，因此保存了多个候选 checkpoint。目录形态类似：

```text
$ARTIFACT_ROOT/runs/<run_id>--5000_chkpt
$ARTIFACT_ROOT/runs/<run_id>--10000_chkpt
...
$ARTIFACT_ROOT/runs/<run_id>--50000_chkpt
```

每个 merge 后 checkpoint 约 `3.2G`。这类目录会随保存点线性累积，占用空间明显大于本地日志。

本次最终进入完整 eval 对比的候选是：

```text
$ARTIFACT_ROOT/runs/<run_id>--30000_chkpt
$ARTIFACT_ROOT/runs/<run_id>--40000_chkpt
$ARTIFACT_ROOT/runs/<run_id>--45000_chkpt
$ARTIFACT_ROOT/runs/<run_id>--50000_chkpt
```

评测结果显示 `40000_chkpt` 和 `45000_chkpt` 持平，`50000_chkpt` 回落。因此后续使用较早达到平台区的 `40000_chkpt`，而不是默认选择最后保存的 checkpoint。选择 checkpoint 时，建议把 eval 日志、checkpoint 文件列表和训练日志放在一起保存；这样后续能复查当时选的是哪个目录，以及为什么没有继续采用更晚的保存点。

## 一个 checkpoint 目录里有什么

`merge_lora_during_training=True` 时，一个保存点目录的文件构成大致如下（`N` 是保存 step，大小为 Spatial Pro 实测的近似值）：

```text
$ARTIFACT_ROOT/runs/<run_id>--40000_chkpt/
├── model.safetensors                        # 已合并 LoRA 的 base 权重，约 2.4G
├── action_head--40000_checkpoint.pt          # 连续 action head 权重，约 416M
├── proprio_projector--40000_checkpoint.pt    # proprio projector 权重，约 1.6M
├── dataset_statistics.json                   # action / proprio 归一化统计
├── config.json                               # Prismatic 模型配置
├── configuration_prismatic.py / modeling_prismatic.py / processing_prismatic.py
├── tokenizer.json / vocab.json / merges.txt / *tokens*.json   # processor / tokenizer
└── lora_adapter/
    ├── adapter_config.json                    # LoRA 配置，r=64、lora_alpha=128、target_modules
    └── adapter_model.safetensors              # 未合并的 LoRA delta，约 458M
```

三类权重合起来和上面「约 3.2G」的量级吻合：`model.safetensors` 是合并后的 base，`action_head--N_checkpoint.pt` 和 `proprio_projector--N_checkpoint.pt` 是不在 base 里的独立组件，`lora_adapter/` 保留未合并的 delta。

merge 开关决定 `model.safetensors` 的含义：

- `merge_lora_during_training=True`：`model.safetensors` 已经把 LoRA 合并进 base，`run_libero_eval.py` 用 `--pretrained_checkpoint` 指向该目录即可直接加载，`lora_adapter/` 里仍保留未合并的 delta。
- `merge_lora_during_training=False`：`model.safetensors` 是未合并的 base，评测前需要先跑 `vla-scripts/merge_lora_weights_and_save.py`，用 `--base_checkpoint` 指向基础 VLM、`--lora_finetuned_checkpoint_dir` 指向该保存点目录，把 `lora_adapter/` 合并进去后才能被评测脚本直接加载。

## 保存相关字段

| 字段 | 作用 |
| --- | --- |
| `run_root_dir` | 输出根目录，教程主线用 `$ARTIFACT_ROOT/runs`。 |
| `run_id_note` | run id 的一部分，用于区分运行。 |
| `save_freq` | 保存间隔。 |
| `save_latest_checkpoint_only` | 是否只保留最新 checkpoint。 |
| `merge_lora_during_training` | 是否保存 merge 后可评测 checkpoint。 |

## 评测前检查

先列出本次 run 相关目录：

```bash
find "$ARTIFACT_ROOT/runs" -maxdepth 1 -type d -name '*VLA-Adapter--libero_spatial_no_noops*' | sort
```

再检查要交给 eval 的 checkpoint 目录，例如第 20 step 的短程验证 checkpoint：

```bash
find "$ARTIFACT_ROOT/runs"/*--20_chkpt -maxdepth 1 -type f | sort
```

预期能看到模型配置、权重文件、processor/tokenizer 文件、action head 或 proprio projector 文件、`dataset_statistics.json` 等评测需要的组件。具体目录名和文件名以实际训练输出为准。

如果后续 eval 的 `--pretrained_checkpoint` 指向这个目录仍然加载失败，优先检查训练和评测的 `use_proprio`、`num_images_in_input`、`use_pro_version`、`lora_rank` 是否匹配。

## 保存慢怎么办

如果 `merge_lora_during_training=True` 导致保存非常慢，可以在运行记录中明确说明，并考虑改为训练后单独 merge。无论采用哪种方式，正式 eval 的 `--pretrained_checkpoint` 都应指向评测脚本能直接加载的目录。

保存阶段比普通训练 step 慢是正常现象。判断是否卡住时，应看日志是否从 `Saving Model Checkpoint for Step N` 继续推进到 `Saved merged model for Step N`，以及之后训练 step 是否继续增加。

## 导航

- 上一节：[正式训练](04-full-run-training.md)
- 返回上级：[LoRA 微调训练](../05-training.md)
- 下一节：[训练日志](06-training-logs.md)
