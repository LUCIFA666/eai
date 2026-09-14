# RDT 实践（一）：微调环境与数据准备

本页是 RDT **ManiSkill 微调** 以及 **仿真评测** 路线的前置准备：搭好训练环境、把三类大文件（`rdt-1b` 预训练权重、T5-XXL 文本编码器、178GB ManiSkill 训练数据）就位、接好数据加载器并确认数据集统计。准备完成后，下一页会真正跑训练。

> hint：仿真评测和微调的区别在于：评测需要 checkpoint 权重 + 预计算语言 embedding（~6GB）就能跑；而微调要把训练全链路搭起来。这包括 `rdt-1b` 预训练权重、`T5-XXL` 文本编码器（在线编码指令）、178GB 的 ManiSkill 训练数据、以及 DeepSpeed + Accelerate 的多卡训练。

## 学习目标

- 看懂训练脚本通过 `train/dataset.py` 引入 `data/hdf5_vla_dataset.py` 的加载链路，知道为什么用 `agilex` 当 ManiSkill 数据集的占位符。
- 理解这条路线为什么直接复用仓库自带的 `agilex` 数据集统计，而不需要用 `compute_dataset_stat_hdf5`。

## 环境搭建

本次实验使用的服务器环境如下：

| 项目 | 配置 |
|---|---|
| GPU | NVIDIA A100-SXM4-80GB × 8 |
| 显存 | 单卡 80 GB |
| 操作系统 | Ubuntu 24.04.3 LTS |
| 内核 | Linux 6.8 |
| NVIDIA 驱动 | 580.x |

依赖如下：

| 依赖 | 推荐版本 |
|---|---|
| Python | 3.10.0 |
| PyTorch | `torch==2.1.0+cu121` |
| flash-attn | `flash_attn==2.5.8` |
| DeepSpeed | `deepspeed==0.14.2` |
| Accelerate | `accelerate==0.30.1` |
| wandb | `wandb==0.17.0` |
| diffusers | `diffusers==0.27.2` |
| transformers | `transformers==4.41.0` |

训练侧的 `deepspeed / accelerate / wandb / diffusers / transformers` 全都写在官方 `requirements.txt` 里，所以按教程走即可。

```bash
# 克隆仓库
git clone git@github.com:thu-ml/RoboticsDiffusionTransformer.git
cd RoboticsDiffusionTransformer

# 建并激活环境
conda create -n rdt python=3.10 -y
conda activate rdt

# 1. RDT 官方 requirements
pip install -r requirements.txt

# 2. 按 CUDA 12.1 装对应的 PyTorch
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121
pip install packaging==24.0
```

### flash-attn 用预编译 wheel

`pip install flash-attn --no-build-isolation` 会拉到当时最新版（如 `2.8.x`），而官方 release 里**没有**和本环境（Python 3.10 / torch 2.1 / CUDA 12 / cxx11abiFALSE）匹配的预编译 wheel，于是会退回源码编译，最后又会用系统 `nvcc` 给 `sm_80/90/100/120` 等多个架构一起编，A100 其实只要 `sm_80`，结果就是编译极慢且经常失败。

这里可以直接装教程指定版本的预编译 wheel（用 `--no-deps` 避免它改动其它包），再把 NumPy 降到 1.x（`torch 2.1` 对 NumPy 2.x 有兼容警告）：

```bash
# flash-attn 声明依赖 einops，但 --no-deps 不会自动装，先补上
pip install einops

# 装匹配 torch2.1 / cp310 / CUDA12 / cxx11abiFALSE 的预编译 flash-attn。
# 注意：直接 pip install <github 链接> 在国内拉这个 ~120MB 的 wheel 容易被截断，
# 报 "ERROR: Wheel 'flash-attn' ... is invalid"。建议先用 aria2 把 wheel 下到本地、
# 确认完整（aria2 显示 OK、大小约 120MB）再装本地文件
# 文件名必须保留完整的wheel 标签（带 +cu122torch2.1... ），否则 pip 会报 "Invalid wheel filename"
WHL="flash_attn-2.5.8+cu122torch2.1cxx11abiFALSE-cp310-cp310-linux_x86_64.whl"
aria2c -x8 -c -o "$WHL" \
  "https://github.com/Dao-AILab/flash-attention/releases/download/v2.5.8/flash_attn-2.5.8%2Bcu122torch2.1cxx11abiFALSE-cp310-cp310-linux_x86_64.whl"
pip install --no-deps --force-reinstall "./$WHL"

# 把 NumPy 降到 1.x
pip install 'numpy<2'
```

### ManiSkill 仿真器与 huggingface_hub 版本

下一页验证 checkpoint 的时候会用评测脚本在 ManiSkill 仿真里跑几个 trial，所以这里一并把 ManiSkill 装好。装完再把 `huggingface_hub` 指定为 `0.23.5`。RDT 评测脚本用到的 `huggingface_hub` 接口在新版里会在评测加载阶段报错：

```bash
# ManiSkill 仿真器（SAPIEN + Vulkan 渲染）
pip install mani_skill==3.0.1

# 指定 huggingface_hub 版本（0.23.5）
pip install "huggingface_hub==0.23.5"
```

### 验证环境

```bash
conda activate rdt
python -c "import deepspeed, accelerate, wandb, torch, flash_attn, flash_attn_2_cuda, mani_skill, huggingface_hub; \
print('deepspeed', deepspeed.__version__); print('accelerate', accelerate.__version__); \
print('wandb', wandb.__version__); print('torch', torch.__version__, 'cuda', torch.version.cuda); \
print('flash_attn', flash_attn.__version__); print('mani_skill', mani_skill.__version__); \
print('huggingface_hub', huggingface_hub.__version__)"
```

预期版本：`deepspeed 0.14.2 / accelerate 0.30.1 / wandb 0.17.0 / torch 2.1.0+cu121 / flash_attn 2.5.8 / mani_skill 3.0.1 / huggingface_hub 0.23.5`。

> 导入时 DeepSpeed 出现几条 warning（`async_io requires libaio`、`Please specify the CUTLASS repo directory`、`sparse_attn requires torch < 2.0`、`untested triton version`）。这些只影响 DeepSpeed 的可选算子（异步 IO、稀疏注意力），ZeRO-2 训练用不到，可忽略。另外还可能看到一条 `pynvml is deprecated` 的警告，同样不影响。

### Vulkan 离屏渲染自检

ManiSkill 走 SAPIEN 的 Vulkan 渲染。无显示头的 A100 服务器要先确认系统里有 NVIDIA 的 Vulkan ICD，再做一次最小渲染自检：

```bash
ls /usr/share/vulkan/icd.d/ | grep nvidia    # 期望看到 nvidia_icd.json

python - <<'PY'
import gymnasium as gym, mani_skill
env = gym.make("PickCube-v1", obs_mode="rgb", control_mode="pd_joint_pos",
               render_mode="rgb_array", sim_backend="auto")
obs, _ = env.reset(seed=0)
img = env.render()
print("render OK, shape:", tuple(img.shape))   # 期望 (1, 512, 512, 3)
env.close()
PY
```

如果这里报 Vulkan 相关错误（找不到设备、`failed to create instance`），参考 [ManiSkill 文档的 Vulkan 章节](https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/installation.html#vulkan) 补 ICD 配置，再往下做验证。

## 路线总览

| 资源 | 来源 | 大小 | 作用 |
|---|---|---:|---|
| `rdt-1b` 预训练权重 | `robotics-diffusion-transformer/rdt-1b` | 2.46 GB | 微调的起点（1B Diffusion Transformer 主干）|
| `google/t5-v1_1-xxl` | HuggingFace | 44.5 GB | 文本编码器，训练时在线把任务指令编码成 4096 维 embedding |
| `google/siglip-so400m-patch14-384` | HuggingFace | 3.51 GB | 视觉编码器（冻结，编码图像）|
| ManiSkill 训练数据 `demo_1k` | `maniskill-model` 仓库（17 个分卷）| **178 GB** | 5 个任务各 1000 条 motion-planning 轨迹（状态 / 动作 `.h5` + 逐帧 PNG）|

> 关于 T5-XXL：官方 `finetune_maniskill.sh` 默认不走预计算 embedding，而是在训练时把 T5-XXL 常驻显存、对每个 batch 的指令在线编码。笔者的机器放得下（T5-XXL 编码器 bf16 约 9.4GB）。如果显存吃紧，README 的 FAQ 建议改走预计算：用 `scripts/encode_lang_batch.py` 预先把指令编码成 `.pt`，训练时加 `--precomp_lang_embed` 跳过 T5。本路线按官方脚本的默认做法，走在线 T5-XXL。

## 模型与编码器

三个 HuggingFace 资源（`rdt-1b`、`t5-v1_1-xxl`、`siglip`）建议下到一块大盘上，然后用**符号链接**接到仓库目录。这样做一是避免训练脚本里写死的 `google/t5-v1_1-xxl` 触发联网下载，二是多个项目可以共用同一份权重。

```bash
# 国内服务器用镜像
export HF_ENDPOINT=https://hf-mirror.com

# 1) rdt-1b 预训练权重（2.46GB）
huggingface-cli download robotics-diffusion-transformer/rdt-1b \
  --local-dir /path/to/models/rdt-1b

# 2) T5-XXL 文本编码器（44.5GB，下载较久）
huggingface-cli download google/t5-v1_1-xxl \
  --local-dir /path/to/models/t5-v1_1-xxl

# 3) SigLIP 视觉编码器（3.51GB）
huggingface-cli download google/siglip-so400m-patch14-384 \
  --local-dir /path/to/models/siglip-so400m-patch14-384
```

然后在仓库根目录建 `google/` 符号链接（脚本里 `--pretrained_text_encoder_name_or_path=google/t5-v1_1-xxl` 这类相对路径会优先按本地目录解析，不会再去 HuggingFace 下载）：

```bash
# 在仓库根目录
mkdir -p google
ln -sfn /path/to/models/t5-v1_1-xxl                google/t5-v1_1-xxl
ln -sfn /path/to/models/siglip-so400m-patch14-384  google/siglip-so400m-patch14-384

# 验证链接目标存在
ls google/t5-v1_1-xxl/pytorch_model.bin google/siglip-so400m-patch14-384/model.safetensors
```

> `rdt-1b` 不放进 `google/`，而是在训练脚本里直接用它的本地目录路径（见下一页 `--pretrained_model_name_or_path`）。`train/train.py` 对这个参数的处理是：如果是目录就走 `RDTRunner.from_pretrained()`，是 `.pt` 文件就按 DeepSpeed checkpoint 加载，是 HuggingFace model id 就联网下载。所以用本地目录即可。

## 准备 ManiSkill 训练数据

训练数据在 `maniskill-model` 仓库里，被切成 17 个分卷 `demo_1k_part_aa … demo_1k_part_aq`（一个 zip 被 `split` 切开，**必须全下才能拼回**）。官方 README 给的拼接 / 解压命令是：

```bash
cat demo_1k_part_* > demo_1k.zip
unzip demo_1k.zip
```

解压到 `data/datasets/rdt-ft-data/` 下，最终目录结构是：

```text
data/datasets/rdt-ft-data/demo_1k/<task>/motionplanning/
    ├── *.h5                      # 每个任务的状态(qpos) / 动作轨迹
    └── <proc>/<episode>/N.png    # 逐帧渲染图（加载器按帧号读取）
```

下载用 aria2 多线程，单份真实文件、可断点续传：

```bash
export HF_ENDPOINT=https://hf-mirror.com
cd data/datasets/rdt-ft-data

BASE="$HF_ENDPOINT/robotics-diffusion-transformer/maniskill-model/resolve/main"
: > aria2_input.txt
for s in aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq; do
  echo "$BASE/demo_1k_part_$s"  >> aria2_input.txt
  echo "  out=demo_1k_part_$s"  >> aria2_input.txt
done
aria2c -i aria2_input.txt -j4 -x16 -s16 -c
```

> hint：官方命令会让分卷(178GB) + 拼出的整包 zip(178GB) + 解压结果(≈178GB)三者并存，峰值接近 **540GB**。如果空间紧张，可以改成边拼边删：拼接时每追加一个分卷就立刻删掉它，避免分卷和整包同时存在。但要注意：解压阶段整包 zip 与解压结果仍会并存（标准 `unzip` 不会边解边删源文件），所以峰值仍约 **356GB**（zip 178 + 解压 178）。

```bash
# 逐个分卷追加进 zip 后立刻删掉该分卷
for f in demo_1k_part_??; do cat "$f" >> demo_1k.zip && rm "$f"; done
unzip -q demo_1k.zip      # 解压出 demo_1k/
rm demo_1k.zip            # 解压完删掉整包，只留 demo_1k/
```

## 数据加载器

`train/dataset.py` 里是这样写的：

```python
from data.hdf5_vla_dataset import HDF5VLADataset
```

也就是说，默认训练脚本 import 的是 `data/hdf5_vla_dataset.py`，而不是 `data/hdf5_maniskill_dataset.py`。仓库默认的 `hdf5_vla_dataset.py` 是 agilex 双臂示例（读 `data/datasets/agilex/rdt_data/`），直接拿它训 ManiSkill 会找不到数据。针对我们这条 ManiSkill 微调路线，比较妥当的做法是备份原文件、再把 ManiSkill 版覆盖上去：

```bash
cp data/hdf5_vla_dataset.py data/hdf5_vla_dataset.py.agilex.bak   # 备份原 agilex 版
cp data/hdf5_maniskill_dataset.py data/hdf5_vla_dataset.py        # 换成 ManiSkill 版
```

`data/hdf5_maniskill_dataset.py` 的几个关键点，需要理解并配置妥当：

- `self.data_dir = "data/datasets/rdt-ft-data/demo_1k"`：和上一步的解压位置对齐。
- 固定 5 个任务 `['PickCube-v1','StackCube-v1','PlugCharger-v1','PushCube-v1','PegInsertionSide-v1']`，各 1000 条；从 `.h5` 读 `obs/agent/qpos` 和 `actions`，图像按 `<proc>/<episode>/N.png` 路径逐帧读。
- `self.DATASET_NAME = "agilex"`：它沿用了 `agilex` 这个名字。这就解释了为什么下面的几个 config 文件里都是 `agilex`：

```text
configs/finetune_datasets.json        -> ["agilex"]
configs/finetune_sample_weights.json  -> {"agilex": 100}
configs/dataset_control_freq.json     -> "agilex": 25
```

官方把 `agilex` 当成当前这条微调数据集的占位名，所以这三个文件不用改，直接复用即可。

- 它把 8 维的 ManiSkill 关节状态/动作（7 关节 + 1 夹爪）填进 128 维统一动作向量的右臂槽位（`right_arm_joint_{0..6}_pos` + `right_gripper_open`），动作 chunk 用线性插值补到 64 步。

> `use_hdf5=True` 时 `configs/base.yaml` 里的 `buf_path: /path/to/buffer` 占位符不影响。HDF5 微调直接从加载器取数，不读 buffer。

## 数据集统计

`VLAConsumerDataset` 在做状态条件掩码时，会从 `configs/dataset_stat.json` 按数据集名取 `state_mean` 等统计量。由于 ManiSkill 加载器沿用了 `DATASET_NAME="agilex"`，而仓库已经自带一份 `agilex` 的 128 维统计条目，这条路线直接复用即可，不需要重算。

实际上即使想重算也没有办法。通用自定义数据集指南里有一步 `python -m data.compute_dataset_stat_hdf5`，但它会调用加载器的 `get_item(..., state_only=True)`。ManiSkill 版加载器并没有实现 `state_only`，直接跑会报 `TypeError`。官方仓库里"Finetune RDT with Maniskill Data"那节也确实没有这一步。只有当你要换成自己的全新数据集时，才需要按通用指南补上 state-only 路径再重算。

> hint：仓库自带的 `agilex` 统计来自 agilex 双臂机器人，并不是 ManiSkill 的精确统计。它仅用于以 `cond_mask_prob` 概率把 state 替换成均值，不参与动作监督，微调完全够用；要做严格的论文级复现，可自行实现 state-only 路径后为 `agilex` 重算一份 ManiSkill 统计。

至此前置准备全部完成。下一页开始微调。

## References

- [RDT 官方仓库](https://github.com/thu-ml/RoboticsDiffusionTransformer)

## 导航

- 上一节：[RDT 理论基础](01-theory.md)
- 返回上级：[RDT](../03-rdt.md)
- 下一节：[RDT 实践（二）：微调训练与验证](03-finetune.md)
