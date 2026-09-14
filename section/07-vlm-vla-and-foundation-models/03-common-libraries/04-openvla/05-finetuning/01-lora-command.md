# LoRA 启动命令

目标：知道 OpenVLA LoRA 微调命令由哪些参数组成，以及启动前要检查哪些资源和数据条件。

OpenVLA 的 LoRA 微调入口是 `vla-scripts/finetune.py`。它默认从 `openvla/openvla-7b` 加载模型，用 RLDS 数据集构造训练 batch，再把 LoRA adapter 合并回 Hugging Face 格式的模型目录。

## 参考命令

下面的命令保留官方 LoRA 示例里的主要参数，并把目录写成环境变量。实际运行前，先让这些变量指向自己的模型、数据和输出目录。

```bash
export DATA_ROOT="<rlds_data_root>"
export RUN_ROOT="<run_output_root>"
export ADAPTER_TMP="<adapter_tmp_root>"

torchrun --standalone --nnodes 1 --nproc-per-node 1 vla-scripts/finetune.py \
  --vla_path "openvla/openvla-7b" \
  --data_root_dir "${DATA_ROOT}" \
  --dataset_name bridge_orig \
  --run_root_dir "${RUN_ROOT}" \
  --adapter_tmp_dir "${ADAPTER_TMP}" \
  --lora_rank 32 \
  --batch_size 16 \
  --grad_accumulation_steps 1 \
  --learning_rate 5e-4 \
  --image_aug True \
  --save_steps 5000 \
  --wandb_project openvla
```

`--dataset_name` 要和 OXE mixture 或自定义 RLDS 注册名对上。训练完成后，这个名字也会影响保存的统计量 key；后面推理时使用的 `unnorm_key` 需要能命中同一组统计量。

## 核心参数

| 参数 | 作用 | 检查重点 |
| --- | --- | --- |
| `vla_path` | Hugging Face OpenVLA checkpoint 或本地模型目录。 | LoRA 路径通常使用 `openvla/openvla-7b` 或等价本地目录。 |
| `data_root_dir` | RLDS / TFDS 数据所在根目录。 | 目录下应能找到 `dataset_name` 对应的数据集。 |
| `dataset_name` | 传给 `RLDSDataset` 的数据集或 mixture 名称。 | 名称要和 `OXE_NAMED_MIXTURES`、custom data 注册结果对齐。 |
| `run_root_dir` | 训练日志和合并后 checkpoint 的保存根目录。 | 需要有足够空间保存完整 merged model 和统计量文件。 |
| `adapter_tmp_dir` | 保存 LoRA adapter 的临时目录。 | 训练保存时会先写 adapter，再 merge 到完整模型。 |
| `lora_rank` | LoRA 低秩矩阵的 rank。 | 官方示例和脚本默认值都是 `32`。 |
| `batch_size` | 每个训练进程的 batch size。 | 显存不足时先降低它。 |
| `grad_accumulation_steps` | 梯度累积步数。 | 降低 `batch_size` 后，可以增加它来维持有效 batch。 |
| `learning_rate` | AdamW 学习率。 | LoRA 示例使用 `5e-4`。 |
| `image_aug` | 是否开启图像增强。 | 关闭增强时，训练集上的 token accuracy 可能虚高。 |
| `save_steps` | 每隔多少个 gradient step 保存一次。 | 保存时会触发 adapter 写入和模型 merge，间隔过短会增加训练中断时间。 |

## 显存和 batch

官方 LoRA 示例使用单张 A100 80GB，`batch_size=16`、`grad_accumulation_steps=1` 大约需要 72GB 显存。更小的 GPU 可以先降低 `batch_size`，再增加 `grad_accumulation_steps`。多卡训练时，`torchrun --nproc-per-node` 控制进程数；有效 batch 可以按下面的关系估算：

```text
effective_batch = batch_size * nproc_per_node * grad_accumulation_steps
```

这个数值用于估算训练负载。最终能否稳定训练，还受图像分辨率、LoRA rank、quantization、CUDA 版本和数据加载状态影响。

## 量化选项

`finetune.py` 提供 `--use_quantization`。打开后会使用 4-bit quantization，并在 LoRA 前调用 `prepare_model_for_kbit_training()`。脚本注释里也提示了代价：量化能降低显存压力，但可能损伤性能。默认路线保持 `use_quantization=False`，先把标准 LoRA 路径跑稳。

## 训练启动后的日志检查

命令启动后，日志检查集中在这些现象：

1. 模型和 processor 是否能从 `vla_path` 加载。
2. `RLDSDataset` 是否能用 `data_root_dir` 和 `dataset_name` 构造 batch。
3. W&B 或离线日志里是否开始出现 `train_loss`、`action_accuracy`、`l1_loss`。
4. 到达 `save_steps` 后，`run_root_dir` 下是否出现 processor、merged model 和 `dataset_statistics.json`。

这一步验证的是训练入口和保存链路。策略能否完成任务，要到 rollout 评测中判断。

## 本页小结

- LoRA 微调的主命令是 `torchrun ... vla-scripts/finetune.py`。
- `dataset_name` 同时影响数据加载、统计量保存和后续 `unnorm_key`。
- 显存紧张时优先调整 `batch_size` 和 `grad_accumulation_steps`。
- 训练启动成功说明微调链路可用，策略表现需要结合评测结果。

## 导航

- 上一节：[LoRA 微调](../05-finetuning.md)
- 返回上级：[LoRA 微调](../05-finetuning.md)
- 下一节：[`finetune.py` 训练流程](02-finetune-script.md)
