# LoRA 微调

目标：按显存条件配置 VLA-Adapter LIBERO LoRA 微调，理解 GPU 数、`batch_size`、`grad_accumulation_steps`、`max_steps` 和 checkpoint 保存的关系。

这一页是训练命令准备页，默认已经完成环境安装、LIBERO 数据准备和官方 checkpoint smoke test。第一次训练推荐从 `libero_spatial_no_noops` 开始，因为 Spatial suite 比较适合做低成本闭环检查。

## 训练产物目录

训练 checkpoint 和日志是这次运行生成的产物，和源码分开存放，放到一个产物目录下。用 `ARTIFACT_ROOT` 指向这个目录，训练命令再用参数把产物写过去：

```bash
export ARTIFACT_ROOT=<artifact-root>
mkdir -p "$ARTIFACT_ROOT/runs" "$ARTIFACT_ROOT/logs"
```

`--run_root_dir "$ARTIFACT_ROOT/runs"` 保存训练 run 目录、`dataset_statistics.json`，以及 `...--N_chkpt` 形式的 checkpoint 目录；shell stdout / stderr 日志重定向到 `"$ARTIFACT_ROOT/logs"`，用来复查启动参数、warning、traceback 和 step 信息。

`ARTIFACT_ROOT` 指向一个存放训练产物的目录：正式训练、保存多个 checkpoint 时放到代码树外空间充足的位置；只做短程链路检查或临时调参，放在仓库内的目录也够用。

## 训练前确认

训练命令默认在 VLA-Adapter 源码根目录运行。启动前先确认这些路径和资源：

| 检查项 | 预期 |
| --- | --- |
| 源码根目录 | 当前目录下能看到 `vla-scripts/finetune.py`。 |
| 基础 VLM | 已按 [基础 VLM 与 Prismatic 配置](../02-setup/03-pretrained-backbone.md) 下载。 |
| 配置目录 | `pretrained_models/configs` 已准备好。 |
| LIBERO 数据 | `data/libero` 下有对应 RLDS / TFDS 数据。 |
| 产物目录 | 已设好 `ARTIFACT_ROOT`，并创建 `runs/`、`logs/` 子目录。 |
| 空闲 GPU | 用 `nvidia-smi` 确认训练会占用的 GPU 没有被其它任务占满。 |

## 有效 batch 怎么算

`finetune.py` 的 `batch_size` 是每张 GPU 每个 step 的样本数。有效 batch 可以近似理解为：

```text
effective_batch = batch_size * GPU 数 * grad_accumulation_steps
```

`grad_accumulation_steps` 的作用是用多次小 batch 累积梯度，缓解显存压力。它可以让更新时看到的样本数接近大 batch，但不能完全等价于真实大 batch：训练速度会变慢，batch 内统计和梯度噪声也会不同。

例如单卡 `batch_size=1`、`grad_accumulation_steps=8` 时，有效 batch 约为 8；4 卡 `batch_size=16`、`grad_accumulation_steps=1` 时，有效 batch 约为 64。对比不同运行结果时，至少要同时看 GPU 数、每卡 batch、累积步数和总训练步数。

`get_run_id` 生成的目录名里，`b` 标记只等于 `batch_size * grad_accumulation_steps`，不含 GPU 数（`vla-scripts/finetune.py:180`）。因此 GPU 数不同、每卡配置相同的两次运行会得到相同的 `b` 标记，`--nproc-per-node` 需要在结果记录里另外保存，才能区分两者的真实有效 batch。

## 显存分档参考

下面的分档参考了官方 README 的 `Training for Different Configurations`。这些配置适合作为起点，实际训练时仍以运行时显存占用、step time 和 loss 稳定性为准。

| GPU 显存 | 推荐起点 | 参考显存 | 说明 |
| --- | --- | --- | --- |
| 10GB-12GB | `batch_size=1`、`grad_accumulation_steps=8`、`lora_rank=64` | 约 9.6GB | 极低显存起步配置，速度慢，loss 波动可能更明显。 |
| 24GB | `batch_size=4`、`grad_accumulation_steps=4`、`lora_rank=64` | 约 20GB | 适合 3090 / 4090 一类单卡，仍建议先做短程验证。 |
| 32GB/40GB/48GB | `batch_size=8`、`grad_accumulation_steps=2`、`lora_rank=64` | 约 29GB | 适合 5090、A100-40GB、A800-40GB、L20、RTX A6000 等。 |
| 80GB+ / 多卡 | `batch_size=16`、`grad_accumulation_steps=1`、`lora_rank=64` | 取决于 GPU 数 | 可以接近官方高资源训练设置；多卡时同时调整 `CUDA_VISIBLE_DEVICES` 和 `--nproc-per-node`。 |

本教程主线先给低显存 Spatial 命令，目的是让读者能在更常见的单卡资源上启动训练；如果资源充足，再按上表逐步放大 batch 和 GPU 数。

命令里的 `learning_rate=2e-4`、`lora_rank=64`，以及 `num_steps_before_decay` / `max_steps` 都来自这份 README 的分显存推荐，而不是 `FinetuneConfig` 的默认值。`FinetuneConfig` 默认是 `learning_rate=5e-4`、`lora_rank=32`、`max_steps=200000`、`num_steps_before_decay=100000`，和 README 推荐并不一致。这也是命令要显式写出这几项的原因，和后面参数说明里必须显式覆盖的那组 flag 属于同一类问题：漏掉就退回默认值，跑出来的不是官方推荐设置。

### 4×80GB 实测配置

本教程的 Spatial Pro 实测正式训练使用 4 张 A100-SXM4-80GB，采用官方 Sufficient VRAM 风格配置：

```text
CUDA_VISIBLE_DEVICES=4,5,6,7
--nproc-per-node 4
--batch_size 16
--grad_accumulation_steps 1
--max_steps 150005
--save_freq 5000
--save_latest_checkpoint_only False
--merge_lora_during_training True
--use_pro_version True
```

这个配置的有效 batch 是 `16 * 4 * 1 = 64`。这里的 `max_steps=150005` 是训练上限，不需要跑满；实际做法是每 5000 step 保存 checkpoint，定期跑完整 eval，成功率进入平台区或回落后手动停止。

## Spatial 低显存训练命令

Spatial 低显存参考命令如下。它使用单卡、每卡 batch 为 1、累积 8 步，适合先跑通训练链路。运行前先设好 `ARTIFACT_ROOT` 并创建 `runs/`、`logs/` 子目录。

```bash
mkdir -p "$ARTIFACT_ROOT/runs" "$ARTIFACT_ROOT/logs"
current_time=$(date +%Y%m%d-%H%M%S)
data_name=libero_spatial_no_noops

CUDA_VISIBLE_DEVICES=0 torchrun --standalone --nnodes 1 --nproc-per-node 1 vla-scripts/finetune.py \
--vlm_path pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b \
--config_file_path pretrained_models/configs \
--data_root_dir data/libero \
--dataset_name $data_name \
--run_root_dir "$ARTIFACT_ROOT/runs" \
--use_film False \
--num_images_in_input 2 \
--use_proprio True \
--use_lora True \
--use_fz False \
--use_minivlm True \
--image_aug True \
--num_steps_before_decay 400000 \
--max_steps 400005 \
--save_freq 5000 \
--save_latest_checkpoint_only False \
--merge_lora_during_training True \
--batch_size 1 \
--grad_accumulation_steps 8 \
--learning_rate 2e-4 \
--lora_rank 64 \
--use_pro_version True \
--wandb_entity "YOUR_WANDB_ENTITY" \
--wandb_project "$data_name" \
--run_id_note VLA-Adapter--libero_spatial_no_noops--$current_time \
> "$ARTIFACT_ROOT/logs/VLA-Adapter--libero_spatial_no_noops--$current_time.log" 2>&1 &
```

多卡训练时，`CUDA_VISIBLE_DEVICES` 里的 GPU 数要和 `--nproc-per-node` 一致。例如一台 8 卡服务器前 4 张卡被占用时，可以先用后面的空闲卡：

```bash
CUDA_VISIBLE_DEVICES=4 torchrun --standalone --nnodes 1 --nproc-per-node 1 ...
CUDA_VISIBLE_DEVICES=4,5,6,7 torchrun --standalone --nnodes 1 --nproc-per-node 4 ...
```

这两行只是说明 GPU 选择方式，不是完整训练命令。真实运行时仍使用上面的完整命令，并同步调整 `batch_size`、`grad_accumulation_steps` 和 `max_steps`。

torchrun 的作用是按 `--nproc-per-node` 起对应数量的进程，并给每个进程设好 rank 和 world_size 环境变量。`finetune.py` 用 accelerate 的 `PartialState()`（`vla-scripts/finetune.py:724-726`）读取这些信息，为每个进程分配 GPU，多卡时再用 `wrap_ddp` 把模型包成 DDP。脚本没有手写 `torch.distributed.init_process_group`，也不需要读者手动设 `LOCAL_RANK`。因此单卡 `--nproc-per-node 1` 与直接 `python vla-scripts/finetune.py` 基本等价，命令统一走 torchrun 只是为了单卡和多卡之间切换时不用改启动方式。

## 如何换 suite / dataset

目前我们使用的是 LIBERO Spatial：

```bash
data_name=libero_spatial_no_noops
```

如果要换其它 LIBERO suite，可以替换为：

| suite | `data_name` |
| --- | --- |
| Spatial | `libero_spatial_no_noops` |
| Object | `libero_object_no_noops` |
| Goal | `libero_goal_no_noops` |
| Long / LIBERO-10 | `libero_10_no_noops` |

`--dataset_name $data_name`、`--wandb_project "$data_name"` 和日志文件名会跟着这个变量变化。

## 参数说明

上一节命令里的参数会进入 `FinetuneConfig`。下面按源码字段分组说明：主线取值指本教程 LIBERO Spatial LoRA 命令使用的取值；没有显式出现在命令里的字段按默认值理解，第一次训练通常不改。

`FinetuneConfig` 的部分默认值对 LIBERO 主线并不友好，命令里都显式覆盖了：`use_minivlm`、`use_proprio`、`use_lora` 默认都是 `False`，`num_images_in_input` 默认 `1`。漏掉其中任何一个，训练会退回全量微调、缺 proprio、走错模型加载分支或少一路图像，整条主线链路就走不通。

### 基础模型与配置

| 参数 | 主线取值 | 作用 | 什么时候改 |
| --- | --- | --- | --- |
| `config_file_path` | `pretrained_models/configs` | Prismatic / OpenVLA 配置和 processor 目录。 | 更换配置目录或加载其它兼容 checkpoint 时。 |
| `vlm_path` | `pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b` | 基础 VLM / backbone 权重目录。 | 更换基础 VLM 时。 |
| `use_minivlm` | `True` | 使用 VLA-Adapter 的 mini VLM 加载分支。 | 跟随所用 checkpoint / backbone 要求调整。 |
| `resum_vla_path` | 默认值，主线不改 | 源码中保留的恢复路径字段，拼写就是 `resum_vla_path`。 | 只有确认源码分支实际使用它时再改。 |

### 数据与输出

| 参数 | 主线取值 | 作用 | 什么时候改 |
| --- | --- | --- | --- |
| `data_root_dir` | `data/libero` | RLDS / TFDS 数据根目录。 | 数据放在其它位置，或换到非 LIBERO 数据时。 |
| `dataset_name` | `$data_name`，默认 `libero_spatial_no_noops` | 选择训练 suite / dataset。 | 切换 Object、Goal、LIBERO-10 或自定义数据时。 |
| `run_root_dir` | `$ARTIFACT_ROOT/runs` | run 目录和 checkpoint 目录的输出根目录。 | 想改产物目录时。 |
| `shuffle_buffer_size` | 默认 `100000`，主线不改 | dataloader shuffle buffer 大小。 | CPU 内存或数据读取压力过大时可降低。 |

### 模型结构

| 参数 | 主线取值 | 作用 | 什么时候改 |
| --- | --- | --- | --- |
| `use_l1_regression` | 默认 `True` | 使用连续 action L1 regression 目标。 | 改用离散 action token 训练时。 |
| `use_diffusion` | 默认 `False` | 使用 diffusion action head。 | 只有明确要跑 diffusion 分支时。 |
| `num_diffusion_steps` | 默认 `50` | diffusion 训练步数。 | `use_diffusion=True` 时才有意义。 |
| `use_film` | `False` | 是否用 FiLM 注入语言信息到视觉特征。 | 复现实验需要 FiLM 分支时。 |
| `num_images_in_input` | `2` | 输入图像数量。 | 相机数量或数据字段变化时。 |
| `use_proprio` | `True` | 是否使用 proprio state 和 proprio projector。 | 数据没有 proprio，或评测 checkpoint 不使用 proprio 时。 |
| `phase1_path` | 默认 `None`，主线不改 | 源码保留的阶段一路径字段。 | 只有使用对应多阶段训练流程时。 |
| `use_pro_version` | `True` | 使用 Pro 版本相关组件和配置。 | 加载非 Pro checkpoint 或对照实验时。 |

### 训练超参

| 参数 | 主线取值 | 作用 | 什么时候改 |
| --- | --- | --- | --- |
| `batch_size` | `1` | 每张 GPU 每个 step 的 batch。 | 根据显存档位调整。 |
| `learning_rate` | `2e-4` | optimizer 学习率。 | 调参或复现实验设置时。 |
| `lr_warmup_steps` | 默认 `0.1`，主线不改 | 源码字段注解为 `int`，默认值却是 `0.1`；scheduler 按绝对步数使用（`finetune.py:1061-1063`），`0.1` 会让 warmup 在第 1 步就升到满 lr，等于几乎不 warmup。 | 需要真正的 warmup 时，传一个整数步数。 |
| `num_steps_before_decay` | `400000` | 学习率衰减前的 step 数。 | 改变正式训练总步数或 schedule 时。 |
| `grad_accumulation_steps` | `8` | 梯度累积步数，用速度换显存。 | 显存不足或想调整有效 batch 时。 |
| `max_steps` | `400005`，短程验证改为 `20` | 最大训练 step 数。 | 短程验证、正式训练或调参时。 |
| `image_aug` | `True` | 是否使用图像增强。 | 做消融或复现实验要求关闭时。 |

### 验证、保存、恢复

| 参数 | 主线取值 | 作用 | 什么时候改 |
| --- | --- | --- | --- |
| `use_val_set` | 默认 `False`，主线不改 | 是否启用 validation set。 | 数据和脚本验证分支准备好时。 |
| `val_freq` | 默认 `10000`，主线不改 | validation 频率。 | `use_val_set=True` 时。 |
| `val_time_limit` | 默认 `180`，主线不改 | validation 时间限制。 | `use_val_set=True` 且验证耗时需要控制时。 |
| `save_freq` | `5000`，短程验证改为 `10` | checkpoint 保存间隔。 | 短程验证或想改变保存密度时。 |
| `save_latest_checkpoint_only` | `False` | 是否只保留最新 checkpoint。 | 磁盘紧张且不需要历史 checkpoint 时。 |
| `resume` | 默认 `False`，主线不改 | 是否从 checkpoint 恢复训练。 | 中断后续训时。 |
| `resume_step` | 默认 `None`，主线不改 | 恢复训练的 step。 | `resume=True` 时。 |
| `diffusion_sample_freq` | 默认 `50`，主线不改 | diffusion 采样和记录频率。 | `use_diffusion=True` 时。 |

### LoRA / full finetune

| 参数 | 主线取值 | 作用 | 什么时候改 |
| --- | --- | --- | --- |
| `use_lora` | `True` | 是否使用 LoRA 微调。 | 做 full finetune 或冻结对照时。 |
| `lora_rank` | `64` | LoRA rank，影响可训练参数量和显存。 | 按资源和实验设置调整。 |
| `lora_dropout` | 默认 `0.0`，主线不改 | LoRA dropout。 | 需要正则化或复现实验指定时。 |
| `merge_lora_during_training` | `True` | 默认 `False`；保持 `True` 才会在保存时同时生成 merge 后 checkpoint，`run_libero_eval.py` 可直接加载。 | 保存太慢时可关掉，但之后要用 `merge_lora_weights_and_save.py` 单独 merge 才能评测。 |
| `use_fz` | `False` | 源码中的冻结 / full finetune 相关开关。 | 只有明确跑对应分支时。 |

### W&B 与 run id

| 参数 | 主线取值 | 作用 | 什么时候改 |
| --- | --- | --- | --- |
| `wandb_entity` | `YOUR_WANDB_ENTITY` | W&B entity 名。 | 使用自己的 W&B 账号或组织时。 |
| `wandb_project` | `$data_name` | W&B project 名。 | 想按项目统一管理 run 时。 |
| `run_id_note` | `VLA-Adapter--libero_spatial_no_noops--$current_time` | 附加到 run id 末尾，区分本次运行。 | 每次训练都应避免和旧 run 混淆。 |
| `run_id_override` | 默认 `None`，主线不改 | 完全覆盖自动生成的 run id。 | 需要严格指定输出目录名时。 |
| `wandb_log_freq` | 默认 `10`，主线不改 | W&B 记录频率。 | 想减少或增加日志密度时。 |
| `phase` | 默认 `Training` | 传给 action head 的阶段标记。 | 只有源码分支要求其它 phase 时。 |

## 本页小结

- 显存紧张时，通常从降低 `batch_size` 开始，再用 `grad_accumulation_steps` 补有效 batch。
- 多卡训练时，`CUDA_VISIBLE_DEVICES` 和 `--nproc-per-node` 需要同步调整。
- 第一个 suite 推荐用 `libero_spatial_no_noops`，其它 LIBERO suite 主要替换 `data_name`。

## 导航

- 上一节：[LoRA 微调训练](../05-training.md)
- 返回上级：[LoRA 微调训练](../05-training.md)
- 下一节：[训练配置与训练循环](02-training-config-and-loop.md)
