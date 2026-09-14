# 10.4.8 SimpleVLA-RL 实战：轻量级 VLA 强化学习

前面几节已经从代码层面看过 SimpleVLA-RL：启动脚本负责配置实验，Dataset 提供任务索引，Trainer 调度 rollout、reward 和 PPO 更新，Actor 最终更新 VLA 模型。

这一节换成实战视角：如何把代码真正跑起来。需要注意的是，VLA-RL 对 GPU、显存、磁盘和仿真环境都比较敏感，所以这里给出的命令不是唯一答案。初学者可以根据自己的机器资源，调整训练方式、GPU 数量、验证频率和保存频率。

如果只是学习流程，可以先用较少 epoch、较低验证频率跑小规模实验；如果要复现实验结果，再使用更多 GPU 和更完整的训练配置。

## 目录结构

在导读部分，我们在simplevla-rl_stack目录下载了SimpleVLA-RL、OpenVLA-OFT、LIBERO 和 veRL，同时也创建了checkpoint目录。

接下来我们会先创建运行环境并安装依赖，然后下载已经监督微调后的 VLA 模型。最终的目录结构应该如下：

```text
simplevla-rl_stack/
├── SimpleVLA-RL/
├── openvla-oft/
├── LIBERO/
├── verl/
├── Embodied_models/
│   └── openvla-oft-sft-libero10-trajall/
├── checkpoints/
└── libero_config/
```


## 创建环境

```bash
conda create -n simplevla python=3.10 -y
conda activate simplevla
```

安装 PyTorch：

```bash
pip install torch==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu124
```

安装 Hugging Face 下载工具：

```bash
pip install -U huggingface_hub hf_transfer
```

安装 veRL：

```bash
cd "$SIMPLEVLA_ROOT/verl"
pip install -e .
```

安装 OpenVLA-OFT：

```bash
cd "$SIMPLEVLA_ROOT/openvla-oft"
pip install -e .
pip install packaging ninja
```

`flash-attn` 需要和当前 PyTorch 版本匹配。这里使用已经验证过的版本：

```bash
pip uninstall -y flash-attn || true
pip install --no-cache-dir --no-build-isolation "flash-attn==2.7.0.post2"
```

安装 LIBERO：

```bash
cd "$SIMPLEVLA_ROOT"
pip install -e LIBERO
```

安装 LIBERO 依赖：

```bash
cd "$SIMPLEVLA_ROOT/openvla-oft"
pip install -r experiments/robot/libero/libero_requirements.txt
```

这一步可能会把 `numpy`、`opencv-python`、`tokenizers` 等包升级到不兼容的版本。安装后统一把关键版本 pin 回当前验证过的组合：

```bash
pip install "numpy==1.26.4" "transformers==4.40.1" "tokenizers==0.19.1"
pip install "tensordict==0.5.0" --no-deps
python -c "import torch, torchvision, transformers, tokenizers, numpy, cv2, tensordict, flash_attn; print(torch.__version__, torchvision.__version__, transformers.__version__, tokenizers.__version__, numpy.__version__, cv2.__version__, tensordict.__version__, flash_attn.__version__)"
```

`pip check` 可能仍会提示 `openvla-oft` 想要 `torch==2.2.0`、`vllm` 想要更新的 `transformers`。当前训练脚本使用 `actor_rollout_ref.rollout.name=hf`，不走 vLLM；这个冲突可以先保留，不影响已验证的 LIBERO 训练链路。

## 下载 VLA 模型

SimpleVLA-RL 官方主要推荐下载 OpenVLA-OFT SFT 模型。`libero_10` 常见有 `traj1` 和 `trajall` 两个版本：`traj1` 每个任务只使用 1 条示范轨迹，更适合快速检查流程；`trajall` 使用更多示范轨迹做 SFT，初始策略通常更稳，rollout 时更容易采到成功和部分成功样本。RL 需要成功/失败样本形成对比信号，所以正式训练建议下载 `libero_10 trajall` 版本。

本节使用的模型为：

```text
Haozhan72/Openvla-oft-SFT-libero10-trajall
```
其中，模型名称中的关键部分含义如下：

| 名称片段 | 含义 | 在本实验中的作用 |
| --- | --- | --- |
| `OpenVLA-OFT` | 基于 OpenVLA 的高效微调版本 | 作为视觉-语言-动作模型主体，接收图像和语言指令，并输出机器人动作 |
| `SFT` | Supervised Fine-Tuning，即监督微调 | 表示模型已经通过专家示范轨迹进行过监督学习，可作为 RL 阶段的初始策略 |
| `libero10` | 面向 LIBERO-10 任务套件 | 表示该 checkpoint 的动作归一化统计和任务设置与 LIBERO-10 对齐 |
| `trajall` | 使用全部示范轨迹训练得到的版本 | 相比 `traj1` 初始策略通常更稳定，更适合作为后续强化学习训练的起点 |

模型文件建议统一放在工作目录的 `Embodied_models/` 下：

```bash
mkdir -p "$SIMPLEVLA_ROOT/Embodied_models"
cd "$SIMPLEVLA_ROOT/Embodied_models"
```

如果网络直连不稳定，可以使用镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

现在 `huggingface-cli` 已经过时，推荐使用 `hf download`：

```bash
hf download Haozhan72/Openvla-oft-SFT-libero10-trajall \
  --local-dir "$SIMPLEVLA_ROOT/Embodied_models/openvla-oft-sft-libero10-trajall"
```

下载完成后，检查模型是否完整：

```bash
ls "$SIMPLEVLA_ROOT/Embodied_models/openvla-oft-sft-libero10-trajall"/model-*.safetensors
```

应该看到：

```text
model-00001-of-00004.safetensors
model-00002-of-00004.safetensors
model-00003-of-00004.safetensors
model-00004-of-00004.safetensors
```

继续检查关键配置文件：

```bash
ls "$SIMPLEVLA_ROOT/Embodied_models/openvla-oft-sft-libero10-trajall" | head -40
```

该目录中应包含模型配置、tokenizer、processor、数据统计文件和 OpenVLA-OFT 自定义模型代码，例如：

```text
config.json
configuration_prismatic.py
dataset_statistics.json
model.safetensors.index.json
modeling_prismatic.py
preprocessor_config.json
processing_prismatic.py
processor_config.json
tokenizer_config.json
tokenizer.json
tokenizer.model
```



## 配置 LIBERO

创建 LIBERO 本地配置目录：

```bash
mkdir -p "$SIMPLEVLA_ROOT/libero_config"
cat > "$SIMPLEVLA_ROOT/libero_config/config.yaml" <<EOF
assets: $SIMPLEVLA_ROOT/LIBERO/libero/libero/assets
bddl_files: $SIMPLEVLA_ROOT/LIBERO/libero/libero/bddl_files
benchmark_root: $SIMPLEVLA_ROOT/LIBERO/libero/libero
datasets: $SIMPLEVLA_ROOT/LIBERO/libero/datasets
init_states: $SIMPLEVLA_ROOT/LIBERO/libero/libero/init_files
EOF
```

创建 Ray runtime 环境配置 `align.json`。这里不要把 WandB API key 写进文件，避免日志或 git 记录泄露：

```bash
cat > "$SIMPLEVLA_ROOT/SimpleVLA-RL/align.json" <<EOF
{
  "env_vars": {
    "NCCL_DEBUG": "WARN",
    "RAY_memory_monitor_refresh_ms": "0",
    "VLLM_ATTENTION_BACKEND": "XFORMERS",
    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    "TOKENIZERS_PARALLELISM": "true",
    "PYTHONPATH": "$SIMPLEVLA_ROOT/LIBERO:$SIMPLEVLA_ROOT/SimpleVLA-RL",
    "LIBERO_CONFIG_PATH": "$SIMPLEVLA_ROOT/libero_config",
    "MUJOCO_GL": "egl",
    "NUMBA_DISABLE_JIT": "1",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1"
  },
  "excludes": ["*"]
}
EOF
```
如果运行时看到 `datasets path ... does not exist` 的 warning，不一定表示程序失败。对于本节的 LIBERO rollout / validation 流程，关键是 `assets`、`bddl_files` 和 `init_states` 能被正确找到；如果后续需要读取离线示范数据，再单独配置 datasets 目录。

## 创建本地训练脚本

复制官方 LIBERO 脚本：

```bash
cd "$SIMPLEVLA_ROOT/SimpleVLA-RL"
cp examples/run_openvla_oft_rl_libero.sh examples/run_openvla_oft_rl_libero_local.sh
```

把脚本开头改成下面这样。不要在脚本里写 `WANDB_API_KEY`，也建议去掉 `set -x`，否则 key 或长命令容易被打印到日志里。

```bash
export NCCL_DEBUG=WARN
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export TOKENIZERS_PARALLELISM=true
export CUDA_LAUNCH_BLOCKING=1
export TORCH_USE_CUDA_DSA=1
export ROBOT_PLATFORM=LIBERO

SIMPLEVLA_ROOT="${SIMPLEVLA_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

PROJECT_NAME='SimpleVLA-RL'
EXPERIMENT_NAME='libero10_trajall_rl_local'

SFT_MODEL_PATH="$SIMPLEVLA_ROOT/Embodied_models/openvla-oft-sft-libero10-trajall"
CKPT_PATH="$SIMPLEVLA_ROOT/checkpoints"

DATASET_NAME="libero_10"
VLA_NAME="openvla-oft"
NUM_GPUS=8
NUM_NODES=1

ALIGN_PATH="$SIMPLEVLA_ROOT/SimpleVLA-RL/align.json"
```

正式训练参数建议保留官方设置：

```bash
data.num_trials_per_task=50
data.n_samples=8
data.filter_accuracy=True
data.train_batch_size=64
trainer.save_freq=25
trainer.test_freq=4
trainer.total_epochs=100
trainer.wandb_mode=online
```

## 根据机器资源调整训练方式

上面的配置更接近正式训练。初学者不一定一开始就有 8 张 A100，也不一定需要直接跑满 100 个 epoch。可以先根据机器资源选择训练方式。

| 场景 | 适合目的 | 建议改法 |
| --- | --- | --- |
| 8 GPU 正式训练 | 复现实验、长时间训练 | `NUM_GPUS=8`，保留较大的 batch 和较频繁 validation |
| 4 GPU 学习 / 中等规模训练 | 课程实验、确认曲线是否上涨 | `NUM_GPUS=4`，适当减小 micro batch，减少总 epoch |
| 1-2 GPU 机器 | 只建议看代码或做极小规模检查 | 大模型可能 OOM，不建议直接跑完整 OpenVLA-OFT RL |
| 先快速检查流程 | 看环境、WandB、checkpoint 是否正常 | 减小 `trainer.total_epochs`，增大 `trainer.test_freq` |
| 磁盘空间紧张 | 避免 checkpoint 写满磁盘 | 减小保存数量，及时删除旧 checkpoint |

最直接需要改的是脚本开头的 GPU 数量：

```bash
NUM_GPUS=4
```

同时运行命令里也要指定实际使用哪几张卡，例如只用 0-3 号卡：

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 \
conda run -n simplevla env \
  PYTHONPATH="$SIMPLEVLA_ROOT/LIBERO:$SIMPLEVLA_ROOT/SimpleVLA-RL" \
  LIBERO_CONFIG_PATH="$SIMPLEVLA_ROOT/libero_config" \
  MUJOCO_GL=egl \
  NUMBA_DISABLE_JIT=1 \
  OMP_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 \
  bash examples/run_openvla_oft_rl_libero_local.sh 2>&1 | tee train_libero10_trajall.log
```

如果从 8 GPU 改到 4 GPU，建议同时降低这些参数，避免显存压力太大：

```bash
actor_rollout_ref.actor.ppo_micro_batch_size=4
actor_rollout_ref.rollout.val_micro_batch_size=4
actor_rollout_ref.rollout.log_prob_micro_batch_size=8
actor_rollout_ref.ref.log_prob_micro_batch_size=8
trainer.n_gpus_per_node=4
trainer.total_epochs=20
```

如果只是想少花时间观察趋势，可以降低验证频率。`trainer.test_freq=4` 表示每 4 个 step 做一次 validation，validation 会进入环境评估并可能保存视频，通常很慢。学习阶段可以改成：

```bash
trainer.test_freq=8
# 或者
trainer.test_freq=16
```

这样 `train_verify_score/all` 仍然会每个训练 step 记录，但 `val/test_score/all` 会更少出现，训练整体会快一些。

checkpoint 也会占用大量磁盘。OpenVLA-OFT 一个完整 actor checkpoint 可能接近几十 GB。磁盘较小的机器可以减少保存频率，或者只保留最新 checkpoint：

```bash
trainer.save_freq=8
```


应用 checkpoint 工具补丁：

```bash
cd "$SIMPLEVLA_ROOT/SimpleVLA-RL"
bash examples/overwrite_vla_ckpt_utils.sh \
  "$SIMPLEVLA_ROOT/Embodied_models/openvla-oft-sft-libero10-trajall"
```

看到下面输出表示补丁应用成功：

```text
Successfully overwrite: configuration_prismatic.py
Successfully overwrite: constants.py
Successfully overwrite: modeling_prismatic.py
Successfully overwrite: processing_prismatic.py
Successfully overwrite: train_utils.py
File overwrite completed!
```

## 运行正式训练

当然你可以先看完接下来的几个小节，这样可以更了解SimpleVLA-RL之后，再开始正式训练。

先登录 WandB：

```bash
conda activate simplevla
wandb login
```
这里login之后会请你输入WandB的API key，所以建议提前创建WandB账号然后申请API key。WandB主要作用是在运行训练过程中实时画出各种结果图表，方便观测。

执行

```bash
cd /path/to/simplevla-rl_stack
export SIMPLEVLA_ROOT="$(pwd)"
cd "$SIMPLEVLA_ROOT/SimpleVLA-RL"

conda run -n simplevla env \
  PYTHONPATH="$SIMPLEVLA_ROOT/LIBERO:$SIMPLEVLA_ROOT/SimpleVLA-RL" \
  LIBERO_CONFIG_PATH="$SIMPLEVLA_ROOT/libero_config" \
  MUJOCO_GL=egl \
  NUMBA_DISABLE_JIT=1 \
  OMP_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 \
  bash examples/run_openvla_oft_rl_libero_local.sh 2>&1 | tee train_libero10_trajall.log
```

训练日志会同时输出到屏幕和本地文件：

```bash
tail -f "$SIMPLEVLA_ROOT/SimpleVLA-RL/train_libero10_trajall.log"
```


WandB 中查看：

```text
Project: SimpleVLA-RL
Run name: libero10_trajall_rl_local
```

训练日志里也会打印 `View project at ...` 和 `View run at ...` 链接，可以直接打开对应网页查看曲线。

## Validation：视频保存示范

官方给出的脚本中，每隔若干 step 会进入环境评估并保存仿真视频。视频文件名里通常会带上任务、trial 和成功状态：`success=False` 表示这次任务执行失败，`success=True` 表示执行成功。下面是第 16 个 step 后 validation 保存的部分视频。

### `libero_10_task_2`：失败与成功对照

左侧是 trial 27 的失败示例，右侧是 trial 49 的成功示例。

<video src="/section/09-reinforcement-learning-for-robotics/04-simplevla-rl/hands-on/01-simplevla-rl/assets/libero_task2_failure.mp4" controls muted playsinline preload="metadata" title="libero_10_task_2 trial 27 success=False" style="width:48%;max-width:420px;height:auto;display:inline-block;vertical-align:top;margin:0.5em 1.5% 1em 0;border-radius:6px;"></video>
<video src="/section/09-reinforcement-learning-for-robotics/04-simplevla-rl/hands-on/01-simplevla-rl/assets/libero_task2_success.mp4" controls muted playsinline preload="metadata" title="libero_10_task_2 trial 49 success=True" style="width:48%;max-width:420px;height:auto;display:inline-block;vertical-align:top;margin:0.5em 0 1em 0;border-radius:6px;"></video>

### `libero_10_task_9`：失败与成功对照

左侧是 trial 24 的失败示例，右侧是 trial 25 的成功示例。

<video src="/section/09-reinforcement-learning-for-robotics/04-simplevla-rl/hands-on/01-simplevla-rl/assets/libero_task9_failure.mp4" controls muted playsinline preload="metadata" title="libero_10_task_9 trial 24 success=False" style="width:48%;max-width:420px;height:auto;display:inline-block;vertical-align:top;margin:0.5em 1.5% 1em 0;border-radius:6px;"></video>
<video src="/section/09-reinforcement-learning-for-robotics/04-simplevla-rl/hands-on/01-simplevla-rl/assets/libero_task9_success.mp4" controls muted playsinline preload="metadata" title="libero_10_task_9 trial 25 success=True" style="width:48%;max-width:420px;height:auto;display:inline-block;vertical-align:top;margin:0.5em 0 1em 0;border-radius:6px;"></video>

看视频时可以重点观察两件事：第一，机器人是否真的按照语言指令完成了目标，而不是只在指标上变好；第二，失败样本通常失败在哪里，例如抓取位置偏了、夹爪没有闭合、移动路径不稳定，还是任务快完成时没有触发成功条件。这些现象可以帮助我们判断问题来自模型能力、动作接口、环境设置，还是训练还不充分。

## 训练与验证曲线示例

训练过程中可以重点看两个指标：`train_verify_score/all` 和 `val/test_score/all`。`train_verify_score/all` 来自训练阶段的 rollout，可以理解为当前策略在训练采样任务中的平均成功程度，适合观察 RL 更新是否让模型持续变好；`val/test_score/all` 来自定期 validation，更适合用来报告模型在评估任务上的最终效果。

<img src="/section/09-reinforcement-learning-for-robotics/04-simplevla-rl/hands-on/01-simplevla-rl/assets/train_verify_score_curve_libero10_trajall_4gpu_e20.svg" alt="SimpleVLA-RL LIBERO10 train_verify_score/all 曲线" style="max-width:100%;height:auto;display:block;margin:1em 0;">

<img src="/section/09-reinforcement-learning-for-robotics/04-simplevla-rl/hands-on/01-simplevla-rl/assets/test_score_curve_libero10_trajall_4gpu_e20.svg" alt="SimpleVLA-RL LIBERO10 val/test_score/all 曲线" style="max-width:100%;height:auto;display:block;margin:1em 0;">

这两条曲线都整体上升，说明模型通过环境交互和成功/失败反馈逐步学到了更好的动作策略。实际汇报时，可以用 `train_verify_score/all` 说明训练趋势，用 `val/test_score/all` 说明 validation 成功率提升。

## 本节小结

这一节把 SimpleVLA-RL 从代码讲解推进到了真正可运行的实验流程。完整流程可以概括为：

```text
-> 准备 simplevla-rl_stack 目录
-> 下载 OpenVLA-OFT SFT checkpoint
-> 配置 LIBERO 和 Ray runtime env
-> 按自己的 GPU 数量修改训练脚本
-> 登录 WandB 并启动训练
-> 通过日志、WandB 曲线、validation 视频和 checkpoint 观察训练结果
```

对初学者来说，最重要的不是一开始就跑满最大规模，而是先确认四件事：环境能正常启动，rollout 能采到轨迹，WandB 能看到 `train_verify_score/all` 和 `val/test_score/all`，checkpoint 能完整保存。确认这条链路打通后，再根据自己的机器资源增加 epoch、调整 GPU 数量、提高保存频率或做更长时间训练。

如果训练过程中遇到显存不足，优先减小 micro batch；如果 validation 太慢，优先增大 `trainer.test_freq`；如果磁盘压力大，优先减少 checkpoint 数量。这样调参时就不会迷失在大量配置里，而是始终围绕三件事做取舍：显存、时间和磁盘。

读完这一节后，你应该能够独立完成一次 SimpleVLA-RL 的本地训练，并且知道如何从日志、曲线、视频和 checkpoint 判断训练是否真的在向好的方向发展。
