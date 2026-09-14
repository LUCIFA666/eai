# 环境和模型怎么配

目标：明确最小复现需要哪些模型、环境里最常见的版本坑是什么，以及如何优先把第一阶段推理链路跑通。

## 最小复现需要哪些模型

如果你只想做最小复现，不训练，最少只需要四个模型目录：

1. `clip-vit-base-patch32`
2. `svd-robot`
3. `svd-robot-calvin`
4. `dp-calvin`

建议本地统一放成这样：

```text
models/vpp/
├── clip-vit-base-patch32/
├── svd-robot/
├── svd-robot-calvin/
└── dp-calvin/
```

其中：

- `svd-robot`：第一阶段视频推理示例更常用
- `svd-robot-calvin`：第二阶段 CALVIN 评测更常用
- `dp-calvin`：第二阶段动作模型

## 这些模型从哪里下载

原仓库 README 已经给出了这 4 个模型的官方来源，分别是：

| 本地目录名 | 官方来源 | 用途 |
|---|---|---|
| `clip-vit-base-patch32` | `openai/clip-vit-base-patch32` | 文本编码器 |
| `svd-robot` | `yjguo/svd-robot` | 第一阶段视频预测模型 |
| `svd-robot-calvin` | `yjguo/svd-robot-calvin-ft` | CALVIN 路线的视频模型 |
| `dp-calvin` | `yjguo/dp-calvin` | CALVIN 路线的动作模型 |

如果只是想看第一阶段视频预测，最少需要：

- `clip-vit-base-patch32`
- `svd-robot`

如果要跑第二阶段 CALVIN 评测，还需要：

- `svd-robot-calvin`
- `dp-calvin`

## 模型下载命令

### 方式一：直接使用 `huggingface_hub`

先安装下载工具：

```bash
pip install -U huggingface_hub
```

然后执行：

```bash
huggingface-cli download openai/clip-vit-base-patch32 \
  --local-dir models/vpp/clip-vit-base-patch32

huggingface-cli download yjguo/svd-robot \
  --local-dir models/vpp/svd-robot

huggingface-cli download yjguo/svd-robot-calvin-ft \
  --local-dir models/vpp/svd-robot-calvin

huggingface-cli download yjguo/dp-calvin \
  --local-dir models/vpp/dp-calvin
```

### 方式二：在无法直连 Hugging Face 时使用镜像

有些服务器无法稳定访问 `huggingface.co`。这种情况下，可以先设置镜像环境变量，再执行相同的下载命令：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

```bash
huggingface-cli download openai/clip-vit-base-patch32 \
  --local-dir models/vpp/clip-vit-base-patch32

huggingface-cli download yjguo/svd-robot \
  --local-dir models/vpp/svd-robot

huggingface-cli download yjguo/svd-robot-calvin-ft \
  --local-dir models/vpp/svd-robot-calvin

huggingface-cli download yjguo/dp-calvin \
  --local-dir models/vpp/dp-calvin
```

### 方式三：用 Python 脚本下载

如果更习惯脚本方式，可以使用：

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="openai/clip-vit-base-patch32",
    local_dir="models/vpp/clip-vit-base-patch32",
)
snapshot_download(
    repo_id="yjguo/svd-robot",
    local_dir="models/vpp/svd-robot",
)
snapshot_download(
    repo_id="yjguo/svd-robot-calvin-ft",
    local_dir="models/vpp/svd-robot-calvin",
)
snapshot_download(
    repo_id="yjguo/dp-calvin",
    local_dir="models/vpp/dp-calvin",
)
```

如果需要镜像，可以在运行前设置：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

## 下载后先检查什么

下载结束后，建议先检查目录是否完整，而不是马上运行脚本。

对 `clip-vit-base-patch32`，通常至少应看到：

- `config.json`
- `tokenizer.json`
- `tokenizer_config.json`
- `vocab.json`
- `merges.txt`
- `pytorch_model.bin`

对 `svd-robot` 和 `svd-robot-calvin`，通常至少应看到：

- `model_index.json`
- `scheduler/`
- `unet/`
- `vae/`
- `image_encoder/`
- `feature_extractor/`

对 `dp-calvin`，至少应确认 checkpoint 文件已经下载完成，例如：

- `last.pt`

如果评测脚本默认按 `saved_models/last.pt` 查找，还需要额外整理目录结构。

## 推荐的最小环境目标

这一项目在实践中更重要的是“兼容能跑”，不是“无 warning 的完美环境”。一套相对稳妥的目标组合是：

| 项目 | 建议 |
|---|---|
| Python | 3.10 |
| PyTorch | 2.0.x 左右可工作 |
| torchvision | 与 torch 对应版本 |
| diffusers | 与仓库 requirements 尽量一致 |
| numpy | 优先 `<2` |

## 复现时最容易遇到的版本坑

### `numpy 2.x` 和旧版 `torchvision`

这是最常见的第一坑。表现通常是：

- 启动脚本时出现 `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x`
- 后面进一步触发 `RuntimeError: Numpy is not available`

根因是：

- 环境里安装了 `numpy 2.x`
- 但 `torch` / `torchvision` 这条链仍是按 `numpy 1.x` ABI 构建

对这一项目，较常见的处理方式是：

```bash
pip install "numpy<2" --force-reinstall
```

### `pkg_resources` 缺失

在跑 `calvin_evaluate.py` 时，`pytorch_lightning` 可能会通过 `lightning_fabric` 依赖 `pkg_resources`。如果你的 `setuptools` 太新，可能会出现：

```text
ModuleNotFoundError: No module named 'pkg_resources'
```

较常见的处理方式是将 `setuptools` 回退到仍保留该接口的版本。

### `pyhash` 安装失败

原项目里 `policy_evaluation/utils.py` 会 import `pyhash`。但这个包在新 Python 版本上往往直接装不上。好消息是，项目实际上只用到了一个很小的哈希子集，因此这类问题通常可以通过本地兼容实现绕过去。

## 模型下载时要注意什么

### 不要只看项目主页说明

VPP 相关项目的模型名、脚本名和实际代码路径不一定始终完全同步。下载前建议同时核对：

- 项目主页说明
- 命令行参数名
- `from_pretrained(...)` 的调用方式

### 有些环境里需要用镜像

如果服务器直连 `huggingface.co` 不稳定，可以考虑使用镜像站进行模型下载。关键不是下载方式，而是最后本地目录必须满足 `from_pretrained` 预期：

- 有 `model_index.json`
- 子模块目录完整
- 不能只下载单个权重文件

## 第二阶段还有一个隐藏目录要求

`dp-calvin` 这类动作模型目录，评测脚本经常默认按下面结构找 checkpoint：

```text
dp-calvin/
├── saved_models/
│   └── last.pt
└── ...
```

如果你本地只有：

```text
dp-calvin/last.pt
```

那脚本很可能找不到模型。可以手动整理成：

```bash
mkdir -p models/vpp/dp-calvin/saved_models
cp models/vpp/dp-calvin/last.pt models/vpp/dp-calvin/saved_models/last.pt
```

复现前最好先确认目录形状，而不是只确认“文件存在”。

## 推荐的最小复现顺序

1. 先保证 `make_prediction.py` 能加载 `svd-robot` 和 CLIP
2. 再保证 `calvin_evaluate.py` 能加载 `svd-robot-calvin` 和 `dp-calvin`
3. 只有这两步都通了，才值得继续看训练和自定义数据

## 小结

- 最小复现至少需要 4 个模型目录。
- 对这个项目，`numpy<2` 往往比追求最新版本更重要。
- 评测链路除了模型文件本身，还隐含依赖具体目录结构。

## 导航

- 上一节：[环境准备与第一次视频预测](../02-setup-and-first-prediction.md)
- 返回上级：[环境准备与第一次视频预测](../02-setup-and-first-prediction.md)
- 下一节：[怎么跑第一次视频预测](02-run-make-prediction.md)
