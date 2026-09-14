# 下载代码与 checkpoint

目标：把 OpenVLA 源码和常用 checkpoint 放到本地，并知道在线下载、缓存目录和离线加载分别影响哪一步。

OpenVLA 的最小推理可以直接从 Hugging Face model id 开始，但实际复现时最好先安排好源码目录和 checkpoint 缓存。模型权重体积较大，下载失败、缓存目录不对或本地目录缺文件，都会在 `from_pretrained(...)` 阶段暴露出来。

## 源码目录

官方仓库可以直接克隆：

```bash
git clone https://github.com/openvla/openvla.git
cd openvla
```

如果已经有这份源码，先确认当前 shell 进入的是 OpenVLA 仓库根目录。后面的安装命令、`requirements-min.txt`、`pyproject.toml` 和 `vla-scripts/` 都默认从这个目录查看。

## 自动下载和预下载

`AutoProcessor.from_pretrained(...)` 和 `AutoModelForVision2Seq.from_pretrained(...)` 都可以接收 Hugging Face model id。第一次运行时，Transformers 会联网下载 config、processor、tokenizer、远程代码和权重文件，并写入本地缓存。

```python
from transformers import AutoModelForVision2Seq, AutoProcessor

model_id = "openvla/openvla-7b"

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
vla = AutoModelForVision2Seq.from_pretrained(model_id, trust_remote_code=True)
```

这种方式适合在线机器上的最小验证。实验机器网络不稳定时，可以先用 Hugging Face CLI 把 checkpoint 拉到缓存里：

```bash
huggingface-cli download openvla/openvla-7b
```

预下载不会改变后面的 Python 写法。它的作用是把下载过程提前暴露出来，后面运行 smoke test 时主要检查模型加载和 `predict_action`。

## 常用 checkpoint

setup 阶段先认识这几类 checkpoint，具体训练和评测命令放到对应章节。

| Checkpoint | 什么时候下载 |
| --- | --- |
| `openvla/openvla-7b` | 最小 HF 推理、LoRA 微调起点、BridgeData V2 风格的 `bridge_orig` smoke test。 |
| `openvla/openvla-7b-finetuned-libero-spatial` | 想先用官方 LIBERO-Spatial 微调权重做加载或评测检查时下载。 |
| `openvla/openvla-7b-finetuned-libero-object` | LIBERO-Object 评测使用。 |
| `openvla/openvla-7b-finetuned-libero-goal` | LIBERO-Goal 评测使用。 |
| `openvla/openvla-7b-finetuned-libero-10` | LIBERO-10 / LIBERO-Long 评测使用。 |
| `openvla/openvla-7b-prismatic` | full fine-tuning 使用，走 Prismatic 训练路径，体积和加载方式都和 HF 推理 checkpoint 不同。 |

Prismatic checkpoint 常见有两种下载方式：按官方说明用 Hugging Face 的 git/LFS 仓库拉取，或用 Hugging Face CLI 下载到本地目录。

```bash
git clone git@hf.co:openvla/openvla-7b-prismatic
cd openvla-7b-prismatic
git lfs fetch --all
```

```bash
hf download openvla/openvla-7b-prismatic \
  --local-dir <LOCAL_PRISMATIC_CKPT_DIR>
```

git/LFS 路线更贴近官方仓库工作流；`hf download` 更适合直接把整个模型仓库放到指定本地目录。

这类 checkpoint 面向 `vla-scripts/train.py` 的 full fine-tuning。最小 `predict_action` 和 LoRA 微调通常从 `openvla/openvla-7b` 开始。

## 缓存目录

默认缓存目录可能落在系统盘。OpenVLA 权重大，建议在下载前把 Hugging Face 缓存放到空间充足的位置：

```bash
export HF_HOME=<HF_CACHE_DIR>
```

OpenVLA 的 full fine-tuning 脚本也提示可以用 `HF_HOME` 统一放置 HF / TIMM artifacts。这个变量应在下载和运行 Python 脚本前设置，避免同一个 checkpoint 分散到多个缓存目录。

网络受限时，可以先切换 Hugging Face endpoint：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

镜像只影响下载请求；已经下载到本地的 checkpoint 仍然按本地缓存或本地目录读取。

## 本地目录和离线加载

如果 checkpoint 已经下载成一个本地目录，可以直接把目录传给 AutoClasses：

```python
from transformers import AutoModelForVision2Seq, AutoProcessor

ckpt = "<LOCAL_OPENVLA_CHECKPOINT_DIR>"

processor = AutoProcessor.from_pretrained(ckpt, trust_remote_code=True)
vla = AutoModelForVision2Seq.from_pretrained(ckpt, trust_remote_code=True)
```

这个目录至少要能提供 `config.json`、processor / tokenizer 文件和模型权重。fine-tuned checkpoint 还要关注 `dataset_statistics.json`，部署脚本会从本地目录读取它，并写入 `vla.norm_stats`。

离线机器上可以设置：

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

设置离线变量后，加载过程只看本地缓存或本地目录。此时传 model id 仍然依赖缓存是否完整；更稳妥的做法是把 `vla_path`、`openvla_path` 或 Python 里的 `ckpt` 指向含完整文件的本地目录。

## 本页小结

下载问题一般发生在 `from_pretrained(...)` 之前或刚开始加载时。先确认源码目录、缓存位置、checkpoint 类型和本地目录文件，再进入下一页检查 HF 主模型、Prismatic checkpoint 和 fine-tuned checkpoint 的加载差异。

## 导航

- 上一节：[准备环境](01-environment.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[Checkpoint 与模型加载](03-checkpoints-and-model-loading.md)
