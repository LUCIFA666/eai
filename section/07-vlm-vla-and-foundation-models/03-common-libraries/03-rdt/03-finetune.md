# RDT 实践（二）：微调训练与验证

前置准备都就位后，本页主要内容为修好官方训练脚本里几处配置，跑通一次微调产出 checkpoint，再用评测脚本加载，确认整条训练链路可用。

> hint：官方 `finetune_maniskill.sh` 是按多机集群写的，单机直接跑会在多机网络变量、硬编码路径和 wandb 登录上有问题。这一页的修改需求集中在"把脚本改成单机多卡能跑"。

## 学习目标

- 用 Accelerate + DeepSpeed ZeRO-2 在单机多卡上跑通一次微调，并保存 checkpoint。
- 理解训练后保存的 DeepSpeed checkpoint 为什么能直接被评测脚本加载。
- 用评测脚本加载 checkpoint，确认整条训练链路可用。

## 修改 finetune_maniskill.sh

仓库自带的 `finetune_maniskill.sh` 是按多机集群写的，直接跑会有问题。这里逐条说明并给出修法：

| 原脚本 | 问题 | 改法 |
|---|---|---|
| `export NCCL_IB_HCA=mlx5_0:1,...`、`NCCL_SOCKET_IFNAME=bond0`、`NCCL_IB_DISABLE=0` | 这是多机 InfiniBand 网络配置，本机没有 `bond0` / `mlx5` 设备，NCCL 初始化会失败 | 单机多卡删掉这些，必要时只留 `NCCL_DEBUG=WARN` |
| `export CUTLASS_PATH="/data/lingxuan/cutlass"` | 别人机器的路径 | ZeRO-2 用不到 CUTLASS，删掉即可（DeepSpeed 的无害 warning）|
| `--pretrained_model_name_or_path="robotics-diffusion-transformer/rdt-1b"` | model id 会触发联网下载 | 改成本地目录，如 `/path/to/models/rdt-1b` |
| `--report_to=wandb` | 没登录 wandb 会卡住 | 保留 `wandb` 但加 `export WANDB_MODE=offline`（离线落盘，不需登录）；或改成 `--report_to=tensorboard` |
| `accelerate launch main.py ...`（无 GPU 配置）| 不指定进程数时不会自动用多卡 | 显式传 `--num_processes=<卡数> --num_machines=1 --mixed_precision=bf16`，并用 `CUDA_VISIBLE_DEVICES` 选空闲卡 |

下面是本次用于**微调验证**的脚本 `finetune_maniskill_verify.sh`（4 卡、每卡 batch 8、少量 step 存一个 checkpoint）。应该把它放在仓库根目录：

```bash
#!/usr/bin/env bash
set -e
NGPU="${1:-4}"
MAX_STEPS="${2:-100}"

# 只用空闲的卡（按实际情况调整）
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1,2,3}"
# 单机多卡：不要设多机 IB 变量
export NCCL_DEBUG=WARN

# 全部走本地
export TEXT_ENCODER_NAME="google/t5-v1_1-xxl"                  # 符号链接到本地 T5-XXL
export VISION_ENCODER_NAME="google/siglip-so400m-patch14-384" # 符号链接到本地 SigLIP
export PRETRAINED="/path/to/models/rdt-1b"                     # rdt-1b 本地目录
export OUTPUT_DIR="./checkpoints/rdt-finetune-1b-sim-verify"

export WANDB_MODE=offline       # 用 wandb 但离线，不需登录
export WANDB_PROJECT="robotic_diffusion_transformer"
mkdir -p "$OUTPUT_DIR"

accelerate launch \
    --num_processes="$NGPU" --num_machines=1 --mixed_precision=bf16 \
    --main_process_port=29577 \
    main.py \
    --deepspeed="./configs/zero2.json" \
    --pretrained_model_name_or_path="$PRETRAINED" \
    --pretrained_text_encoder_name_or_path="$TEXT_ENCODER_NAME" \
    --pretrained_vision_encoder_name_or_path="$VISION_ENCODER_NAME" \
    --output_dir="$OUTPUT_DIR" \
    --train_batch_size=8 \
    --sample_batch_size=8 \
    --max_train_steps="$MAX_STEPS" \
    --checkpointing_period="$MAX_STEPS" \
    --sample_period=-1 \
    --checkpoints_total_limit=2 \
    --lr_scheduler="constant" \
    --learning_rate=1e-4 \
    --mixed_precision="bf16" \
    --dataloader_num_workers=2 \
    --image_aug \
    --dataset_type="finetune" \
    --state_noise_snr=40 \
    --load_from_hdf5 \
    --report_to=wandb
```

> 想完整复现论文，可以把 `max_train_steps` 调回官方的量级（README 建议至少 150K 步），`checkpointing_period` 设成 1000~10000，`train_batch_size` 按显存上调。这里为了验证只跑 100 步。

## 启动训练

```bash
conda activate rdt
bash finetune_maniskill_verify.sh 4 100      # 4 卡，跑 100 step
```

`train/train.py` 启动后会先构建模型、打印训练规模，日志里能看到这些：

```txt
Constructing model from pretrained checkpoint.       # 从 rdt-1b 加载
***** Running training *****
  Num examples = 5000
  Instantaneous batch size per device = 8
  Total train batch size (w. parallel, distributed & accumulation) = 32
  Total optimization steps = 100
```

之后进度条按 step 推进，每步打印 `loss` 和 `lr`；到 `checkpointing_period` 时把 checkpoint 存到 `checkpoints/rdt-finetune-1b-sim-verify/checkpoint-<step>/`，为 DeepSpeed 格式：

```text
checkpoint-100/
  ├── pytorch_model/mp_rank_00_model_states.pt   # DeepSpeed 模型权重，评测脚本要的就是这个（≈2.46GB）
  ├── pytorch_model.bin                          # save_pretrained 顺带存的 HF 格式权重
  ├── ema/model.safetensors                      # EMA 权重
  ├── config.json  latest  scheduler.bin  zero_to_fp32.py
  └── random_states_{0..3}.pkl                   # 4 个进程各自的随机数状态
```

训练结束时会把最终模型保存到 `output_dir`（`pytorch_model.bin` + `config.json` + `ema/`）。

### 训练输出

```txt
***** Running training *****
  Num examples = 5000
  Total optimization steps = 100
  1%|          | 1/100   [00:03<06:00, 3.64s/it, loss=0.00934,  lr=0.0001]
 51%|█████     | 51/100  [00:54<00:49, 1.01s/it, loss=0.00136,  lr=0.0001]
100%|██████████| 100/100 [02:09<00:00, 1.29s/it, loss=0.000919, lr=0.0001]
Saved state to ./checkpoints/rdt-finetune-1b-sim-verify/checkpoint-100
Saved Model to ./checkpoints/rdt-finetune-1b-sim-verify
```

- **耗时**：100 步约 2 min，稳定在 ~1.0 s/it。
- **loss**：从首步 `0.00934` 降到收尾 `~0.0009`，下降约一个数量级（100 步只看 loss 趋势是否下降，不代表收敛）。
- **产物**：step 100 落盘 `checkpoint-100/pytorch_model/mp_rank_00_model_states.pt` ，约2.46GB。

## 验证 checkpoint 可加载推理

训练存出的 `mp_rank_00_model_states.pt` 正好是评测脚本能直接加载的格式。用仿真评测脚本加载 checkpoint，在 `PickCube` 上跑几个 trial，确认它能完成一次扩散采样并驱动环境：

```bash
export CUDA_VISIBLE_DEVICES=0
python -m eval_sim.eval_rdt_maniskill \
  --env-id PickCube-v1 \
  --pretrained_path checkpoints/rdt-finetune-1b-sim-verify/checkpoint-100/pytorch_model/mp_rank_00_model_states.pt \
  --num-traj 3 --random_seed 0 --reward-mode none
```

> 这一步需要 ManiSkill 仿真环境（`mani_skill` + Vulkan 离屏渲染 + `huggingface_hub==0.23.5`），环境配置在[上一节](02-practice.md)说明。100 步的微调远不足以学出有效策略，这里只验证 checkpoint 能被正确加载并跑通推理，不注重成功率。要评估成功率得按论文量级训到收敛（150K+ 步）。

笔者实测输出：

```txt
Diffusion params: 1.228320e+09
Loading weights from checkpoints/rdt-finetune-1b-sim-verify/checkpoint-100/pytorch_model/mp_rank_00_model_states.pt
Trial 1 finished, success: tensor([False]), steps: 400
Trial 2 finished, success: tensor([False]), steps: 400
Trial 3 finished, success: tensor([False]), steps: 400
Success rate: 0.0%
```

3 个 trial 全部 `success=False`、各跑满 400 步、成功率 0.0%。整体也算符合预期：100 步训练远不够学出有效策略，这个只证明权重能被正确加载、扩散采样能跑、Vulkan 渲染与环境步进都正常。

## 分析与说明

- **`agilex` 占位符**：ManiSkill 加载器复用了 `agilex` 这个数据集名，所以一整套 config（`finetune_datasets / sample_weights / control_freq / dataset_stat`）都不用改名，直接复用。
- **checkpoint 格式自洽**：训练用 DeepSpeed 存的 `mp_rank_00_model_states.pt`，和评测脚本 `--pretrained_path` 期望的格式一致，所以训练产物能直接用到评测上。

## 动手练习

1. 把 `max_train_steps` 设成 500、`checkpointing_period` 设成 100，跑出 5 个 checkpoint，用评测脚本分别在 `PickCube-v1` 上跑 5 个 trial，对比 step 100 / 300 / 500 的成功率，观察变化趋势。
2. 读 `train/train.py` 的训练循环，理解 `vision_encoder` / `text_encoder` 为什么都在 `torch.no_grad()` 里，只有 `rdt` 参与反传。
3. 对照 `configs/zero2.json`，解释 ZeRO-2 把哪些状态做了切分，以及为什么 1B 模型在 80GB 卡上其实不开 ZeRO 也放得下。

## References

- [RDT 官方仓库](https://github.com/thu-ml/RoboticsDiffusionTransformer)

## 导航

- 上一节：[RDT 实践（一）：微调环境与数据准备](02-practice.md)
- 返回上级：[RDT](../03-rdt.md)
- 下一节：[常用库](../../03-common-libraries.md)
