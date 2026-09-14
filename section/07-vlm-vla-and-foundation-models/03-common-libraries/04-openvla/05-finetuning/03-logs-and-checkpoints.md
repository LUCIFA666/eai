# 训练日志与 checkpoint

目标：理解 OpenVLA LoRA 微调日志中三个指标的含义，以及 checkpoint 保存后包含哪些产物。

LoRA 微调跑起来后，最常看到的是 `train_loss`、`action_accuracy` 和 `l1_loss`。这些指标来自训练 batch，适合判断数据和训练循环是否正常拟合；checkpoint 产物则决定后面能否用 `from_pretrained()` 加载并继续做 rollout。

## 训练指标

`train_loss` 直接来自模型输出的 causal LM loss。`action_accuracy` 和 `l1_loss` 是脚本额外计算的动作指标。

```python
action_logits = output.logits[:, vla.module.vision_backbone.featurizer.patch_embed.num_patches : -1]
action_preds = action_logits.argmax(dim=2)
action_gt = batch["labels"][:, 1:].to(action_preds.device)
mask = action_gt > action_tokenizer.action_token_begin_idx

correct_preds = (action_preds == action_gt) & mask
action_accuracy = correct_preds.sum().float() / mask.sum().float()
```

这里的 `mask` 会筛出 action token 位置。`action_accuracy` 统计的是这些位置上的 token 预测是否命中，所以它反映训练 batch 上的动作 token 拟合情况。

```python
continuous_actions_pred = torch.tensor(
    action_tokenizer.decode_token_ids_to_actions(action_preds[mask].cpu().numpy())
)
continuous_actions_gt = torch.tensor(
    action_tokenizer.decode_token_ids_to_actions(action_gt[mask].cpu().numpy())
)
action_l1_loss = torch.nn.functional.l1_loss(continuous_actions_pred, continuous_actions_gt)
```

`l1_loss` 会先把预测 token 和真值 token 解码成归一化动作，再计算 L1 距离。它能补充观察 token accuracy：两个相邻 bin 的错误和相距很远的 bin 错误，在 accuracy 中都算错，但在 L1 中差别明显。

## 日志怎样记录

脚本每 10 个 gradient step 向 W&B 写一次平滑后的训练指标。

```python
if distributed_state.is_main_process and gradient_step_idx % 10 == 0:
    wandb.log(
        {
            "train_loss": smoothened_loss,
            "action_accuracy": smoothened_action_accuracy,
            "l1_loss": smoothened_l1_loss,
        },
        step=gradient_step_idx,
    )
```

如果使用离线日志，仍然重点看这三个字段的趋势。短训练可以验证数据、前向、反向、日志和保存链路；长训练曲线主要说明训练集拟合情况，闭环任务表现要交给评测。

## 统计量保存

训练开始后，主进程会把数据集统计量保存到 `run_dir`。

```python
if distributed_state.is_main_process:
    save_dataset_statistics(vla_dataset.dataset_statistics, run_dir)
```

这一步会生成后续推理需要的 `dataset_statistics.json`。用 LoRA 微调得到的新 checkpoint 做 `predict_action` 时，`unnorm_key` 要和这个文件里的 key 对上。

## Adapter 与 merged checkpoint

到达 `save_steps` 后，脚本先保存 processor 和模型权重。LoRA 路径会先把 adapter 写到临时目录，再加载 base model，把 adapter merge 回完整模型。

```python
save_dir = adapter_dir if cfg.use_lora else run_dir

processor.save_pretrained(run_dir)
vla.module.save_pretrained(save_dir)
```

这段代码里，`processor` 保存在 `run_dir`，LoRA adapter 先保存在 `adapter_dir`。随后脚本会重新加载 base VLA 并 merge。

```python
base_vla = AutoModelForVision2Seq.from_pretrained(
    cfg.vla_path, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True, trust_remote_code=True
)
merged_vla = PeftModel.from_pretrained(base_vla, adapter_dir)
merged_vla = merged_vla.merge_and_unload()
if distributed_state.is_main_process:
    if cfg.save_latest_checkpoint_only:
        merged_vla.save_pretrained(run_dir)
    else:
        checkpoint_dir = Path(str(run_dir) + f"--{gradient_step_idx}_chkpt")
        save_dataset_statistics(vla_dataset.dataset_statistics, checkpoint_dir)
        processor.save_pretrained(checkpoint_dir)
        merged_vla.save_pretrained(checkpoint_dir)
```

默认 `save_latest_checkpoint_only=True` 时，`run_dir` 里会持续保留最新 merged checkpoint，并带上 processor 和 `dataset_statistics.json`。设为 `False` 时，每个保存点会写到单独的 checkpoint 目录，并再次保存统计量、processor 和 merged model。

## 保存后检查什么

无论当前看到的是最新覆盖目录还是分步 checkpoint 目录，可用于推理的 LoRA 微调产物至少要能满足下面几项：

| 检查项 | 说明 |
| --- | --- |
| model weights | merged 后的模型权重能被 `AutoModelForVision2Seq.from_pretrained()` 读取。 |
| processor files | processor 能被 `AutoProcessor.from_pretrained()` 读取。 |
| `dataset_statistics.json` | 文件里有目标数据集对应的统计量 key。 |
| `unnorm_key` | 推理代码传入的 key 能命中统计量。 |
| action shape | `predict_action()` 返回的动作维度和目标环境一致。 |

这些检查通过后，checkpoint 才适合进入评测脚本。评测仍然要单独记录环境、任务、rollout 次数和成功率。

## 本页小结

- `train_loss` 来自 causal LM loss，`action_accuracy` 和 `l1_loss` 来自动作 token 位置。
- `action_accuracy` 高说明训练 batch 上 token 命中率高，任务完成情况要看 rollout。
- LoRA 保存时会先写 adapter，再 merge 回完整模型。
- `dataset_statistics.json` 是 checkpoint 能正确反归一化动作的必要文件。

## 导航

- 上一节：[`finetune.py` 训练流程](02-finetune-script.md)
- 返回上级：[LoRA 微调](../05-finetuning.md)
- 下一节：[LoRA 训练参考](04-training-reference.md)
