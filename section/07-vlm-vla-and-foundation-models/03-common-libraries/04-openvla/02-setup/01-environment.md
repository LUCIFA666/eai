# 准备环境

目标：按最小推理、LoRA 微调、评测与部署三个层级准备 OpenVLA 环境，并知道每层依赖服务哪一段代码。

OpenVLA 的环境可以分层准备。先让 HF 最小推理能跑起来，再安装完整源码依赖；评测和真实机器人相关依赖放到对应章节处理。这样排查时更容易判断问题来自模型加载、训练数据，还是仿真和机器人侧。

## 三层环境

| 层级 | 用途 | 主要依据 |
| --- | --- | --- |
| 最小推理 | 加载 `openvla/openvla-7b`，调用 `AutoProcessor` 和 `predict_action`。 | `requirements-min.txt`、README Getting Started。 |
| 完整源码环境 | 运行 LoRA、RLDS 数据、训练脚本和本地 checkpoint 保存。 | `pyproject.toml`、`vla-scripts/finetune.py`。 |
| 评测与部署 | LIBERO / Bridge rollout、REST server、视频和机器人接口。 | README Evaluating OpenVLA、`experiments/robot/`、`vla-scripts/deploy.py`。 |

## 最小推理环境

OpenVLA README 的 quickstart 使用 Hugging Face AutoClasses 加载模型。这个路径只依赖一小组包：PyTorch、Transformers、Tokenizers、timm 和图像处理相关依赖。官方 `requirements-min.txt` 当前固定了下面几项：

| 依赖 | 版本 |
| --- | --- |
| `torch` | `>=2.2.0` |
| `torchvision` | `>=0.16.0` |
| `transformers` | `4.40.1` |
| `tokenizers` | `0.19.1` |
| `timm` | `0.9.10` |

可以从一个干净的 conda 环境开始：

```bash
conda create -n openvla python=3.10 -y
conda activate openvla
pip install -r requirements-min.txt
```

README 的完整安装说明使用 Python 3.10，并说明代码可兼容 Python 3.8 及以上版本。后续复现实验尽量贴近官方测试组合：PyTorch 2.2.0、torchvision 0.17.0、Transformers 4.40.1、Tokenizers 0.19.1、timm 0.9.10 和 FlashAttention 2.5.5。

## FlashAttention

最小脚本可以去掉 `attn_implementation="flash_attention_2"` 先验证模型加载；安装好 FlashAttention 后再打开这个参数。官方安装说明给出的命令是：

```bash
pip install packaging ninja
ninja --version; echo $?
pip install "flash-attn==2.5.5" --no-build-isolation
```

`ninja --version; echo $?` 的第二行应为 `0`。如果 FlashAttention 编译失败，先确认 PyTorch、CUDA、Python ABI 是否匹配；最小推理也可以先用普通 attention 跑通。

## 完整源码环境

LoRA、RLDS 数据、训练和评测脚本走 OpenVLA 源码安装。进入本地 OpenVLA 仓库后执行：

```bash
pip install -e .
```

`pyproject.toml` 会安装 `accelerate`、`draccus`、`peft==0.11.1`、`tensorflow==2.15.0`、`tensorflow_datasets==4.9.3`、`dlimp`、`wandb` 等依赖。这一层面向训练和数据管线，比最小推理重得多。

LIBERO 评测还会安装 `experiments/robot/libero/libero_requirements.txt`，Bridge WidowX 评测还依赖外部机器人控制仓库。它们属于评测章节的环境内容，本页只保留入口。

## 环境检查

先检查 GPU 和核心包版本：

```bash
python - <<'PY'
import torch
import transformers
import tokenizers
import timm

print("cuda", torch.cuda.is_available())
print("gpu", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
print("torch", torch.__version__)
print("transformers", transformers.__version__)
print("tokenizers", tokenizers.__version__)
print("timm", timm.__version__)
PY
```

如果安装了 FlashAttention，再单独检查：

```bash
python - <<'PY'
import flash_attn
print("flash_attn", flash_attn.__version__)
PY
```

这两段检查只说明 Python 环境和 CUDA 后端能被当前解释器看到。下一页先处理源码目录、checkpoint 下载和本地缓存，再进入模型加载。

## 导航

- 上一节：[安装与第一次跑通](../02-setup.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[下载代码与 checkpoint](02-download-and-cache.md)
