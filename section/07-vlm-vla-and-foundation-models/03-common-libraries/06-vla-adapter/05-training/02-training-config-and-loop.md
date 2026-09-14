# 训练配置与训练循环

目标：理解上一页的命令进入 `vla-scripts/finetune.py` 后，如何变成数据加载、模型构造、LoRA 注入、action head loss 和 checkpoint 保存。

## 从命令到 FinetuneConfig

`finetune.py` 使用 `@draccus.wrap()` 包装 `finetune(cfg: FinetuneConfig)`。命令行里的 `--dataset_name`、`--run_root_dir`、`--use_lora`、`--use_proprio` 等参数会被解析到 `cfg`，没有显式传入的字段则使用 `FinetuneConfig` 默认值。

训练入口先做几件事：

1. 检查 `use_l1_regression` 和 `use_diffusion` 不能同时开启。
2. 清理 `config_file_path` 末尾的 `/`。
3. 调用 `get_run_id(cfg)` 生成 run id。
4. 用 `cfg.run_root_dir / run_id` 创建基础输出目录。
5. 初始化 GPU、DDP 状态和 W&B offline run。

`get_run_id(cfg)` 会把 `config_file_path` 最后一段、`dataset_name`、`batch_size * grad_accumulation_steps`（不含 GPU 数）、learning rate、LoRA rank、image augmentation 和 `run_id_note` 拼到目录名里。因此同一套参数不建议复用同一个 `run_id_note`，否则后续复查时容易混淆短程验证和正式训练产物。

下面几组字段会直接接到前面的实现对应关系：

| 字段组 | 进入哪里 |
| --- | --- |
| `data_root_dir`、`dataset_name` | `RLDSDataset`、OXE registry、statistics。 |
| `vlm_path`、`config_file_path`、`use_minivlm` | 基础 Prismatic VLM 和 processor/config 加载。 |
| `num_images_in_input`、`use_proprio` | batch 字段、processor 输入、proprio projector。 |
| `use_l1_regression`、`use_pro_version` | action head 初始化和 checkpoint 组件。 |
| `use_lora`、`lora_rank`、`merge_lora_during_training` | LoRA 注入、可训练参数和保存形态。 |

## 数据链路

训练数据从 `cfg.data_root_dir` 和 `cfg.dataset_name` 找到对应 RLDS / TFDS 数据集。主线用的是：

```bash
--data_root_dir data/libero
--dataset_name libero_spatial_no_noops
```

进入 dataloader 前，`RLDSDataset` 负责读取数据集，`RLDSBatchTransform` 负责把 episode / step 转成训练需要的字段，collator 再把 batch 整理成模型输入。短程验证日志里能看到 dataset statistics、dataset 名称和 dataloader 长度，说明这段链路至少已经跑通。

训练 batch 里最关键的字段包括：

| 字段 | 用途 |
| --- | --- |
| `input_ids`、`attention_mask`、`labels` | 语言 prompt 和 action token 相关输入。 |
| `pixel_values` | 图像输入，数量受 `num_images_in_input` 影响。 |
| `actions` | 连续 action 监督信号，主线使用 L1 regression。 |
| `proprio` | 机器人本体状态，只有 `use_proprio=True` 时进入模型。 |

如果第一个 batch 就失败，通常优先检查 dataset 名称、RLDS 数据结构、`num_images_in_input`、`use_proprio` 和 action / proprio shape。

## 模型和 LoRA 链路

模型加载分成基础 VLM 和训练组件两层。`config_file_path` 提供 Prismatic / OpenVLA 配置和 processor，`vlm_path` 提供基础 VLM 权重。主线命令中：

```bash
--config_file_path pretrained_models/configs
--vlm_path pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b
--use_minivlm True
```

`use_lora=True` 时，脚本用 `peft.LoraConfig` 给 VLA 注入 LoRA，并让 `action_queries` 保持可训练。`use_proprio=True` 时，会额外初始化 `ProprioProjector`，把 8D proprio state 映射到模型可用的隐藏空间。action head 负责把 VLM hidden states 转成 action chunk，也是 checkpoint 里需要保存并会被 `run_libero_eval.py` 加载的组件。

主线配置暂时不展开 FiLM、diffusion 和 full finetune：`use_film=False`、`use_diffusion=False`、`use_fz=False`。这些字段保留在参数表里，是为了读源码时能看懂分支，但第一次跑 LIBERO Spatial 不建议同时打开。

## 一个训练 step 做什么

在 L1 regression 主线中，一步训练可以按下面顺序理解：

1. dataloader 取出 image、language、action、proprio 等字段。
2. processor / collator 准备 `input_ids`、`attention_mask`、`pixel_values` 和 `labels`。
3. VLA forward 输出 hidden states。
4. 根据 action token mask 取出当前动作和后续 action chunk 对应的 hidden states。
5. action head 预测未来动作；如果开启 proprio，会同时使用 proprio projector。
6. 用预测 action 和 batch 里的 ground-truth `actions` 计算 L1 loss。
7. 按 `grad_accumulation_steps` 累积梯度，到更新点后执行 optimizer step。
8. 记录 metrics，并在达到 `save_freq` 时保存 checkpoint。

## 保存链路

`run_root_dir` 决定输出根目录，主线用 `$ARTIFACT_ROOT/runs`。训练开始时会创建基础 run 目录，例如：

```text
$ARTIFACT_ROOT/runs/<run_id>/
```

达到 `save_freq` 时，会额外生成带 step 后缀的 checkpoint 目录，例如短程验证时常见的：

```text
$ARTIFACT_ROOT/runs/...--10_chkpt/
$ARTIFACT_ROOT/runs/...--20_chkpt/
```

如果 `merge_lora_during_training=True`，保存阶段会同时 merge LoRA，方便后续 eval 直接加载，但这个阶段可能比普通训练 step 慢很多。短程验证时看到保存 checkpoint 花几分钟，不一定说明训练卡死；需要结合日志是否继续推进到下一 step 判断。

本地 checkpoint 进入完整 eval 前，至少核对：

| 检查项 | 原因 |
| --- | --- |
| step checkpoint 目录存在 | `--pretrained_checkpoint` 需要指向可加载目录。 |
| action head 文件存在 | continuous action head 权重不在基础 VLM 里。 |
| proprio projector 文件存在 | `use_proprio=True` 时需要加载。 |
| `dataset_statistics.json` 存在 | eval / deploy 需要 action unnorm 和 proprio normalization。 |
| 训练和评测 flags 一致 | 输入结构、action head、Pro 配置需要对齐。 |

## 导航

- 上一节：[LoRA 微调](01-lora-finetune-command.md)
- 返回上级：[LoRA 微调训练](../05-training.md)
- 下一节：[短程训练链路检查](03-short-run-smoke-test.md)
