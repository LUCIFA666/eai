# 安装与环境检查

本页集中讲 Genesis 的安装、Python 环境、PyTorch 后端、viewer 环境和配套验收脚本。安装放在“认识 Genesis”的后半段，是为了先认识平台和最小链路，再集中处理环境细节；这样读者不会在第一段代码之前就被 CUDA、viewer 和缓存问题打散。

## 本节目标

本节围绕下面几个问题展开：

1. Genesis 对 Python、PyTorch 和操作系统有哪些基本要求？
2. 为什么要先确认 `python`、`pip`、`torch` 和 `genesis` 属于同一个环境？
3. CPU / CUDA 后端应该怎样选择？
4. `GENESIS_BACKEND`、`GENESIS_VIEWER`、`GENESIS_STEPS` 这些环境变量分别控制什么？
5. 如何用 `labs/06_genesis/run_all.sh` 保存可复现的环境检查结果？

## 最小安装和扩展安装分开

先核对官方最低要求，再安装包：

| 项 | 要求 / 写法 |
|---|---|
| Python | `>=3.10,<3.14` |
| 操作系统 | Linux、macOS、Windows 均可；本书服务器复现以 Linux shell 为准 |
| PyTorch | 先按当前平台和 CUDA 版本，从 PyTorch 官方安装页选择命令 |
| Genesis | PyTorch 安装完成后再安装 `genesis-world` |

只跑 `00_env_check.py` 和 `01_first_simulation.py` 时，核心依赖是 PyTorch 和 `genesis-world`。如果要继续跑 `00` 到 `05` 的 codecheck，再保留图像输出依赖：

```bash
# 先按 PyTorch 官网为本机 CUDA / CPU 组合选择安装命令
python -m pip install genesis-world
python -m pip install imageio imageio-ffmpeg
```

如果要跑官方 Rendering / Nyx showcase，才需要额外装：

```bash
python -m pip install gs-nyx gs-nyx-plugin av
```

不要一开始就把所有可选依赖装进来。安装越大，排错面越宽。先让 `00_env_check.py` 和 `01_first_simulation.py` 通过，再决定是否进入 Nyx、IPC 或其他高级示例。

## 环境检查命令

每次换机器或换环境，先跑。下面命令默认在 bash / WSL / Linux shell 中运行：

```bash
which python
python -m pip -V
python - <<'PY'
import torch
import genesis as gs
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("genesis", getattr(gs, "__version__", "unknown"))
PY
```

如果 `python` 和 `pip` 不属于同一个环境，后面的任何报错都可能是假的。先修环境，再修代码。

## 配套环境变量

`labs/06_genesis/` 脚本统一使用下面几个环境变量：

| 变量 | 作用 |
|---|---|
| `GENESIS_BACKEND` | 选择 `cpu`、`gpu` 或 `cuda` |
| `GENESIS_VIEWER` | `0` 关闭 viewer，`1` 打开 viewer |
| `GENESIS_STEPS` | 覆盖脚本 step 数 |
| `GENESIS_BATCH` | 设置并行环境数量 |
| `GENESIS_RUN_DIR` | 指定输出目录 |
| `GENESIS_REPO_ROOT` | Genesis 官方仓库路径，供 showcase runner 使用 |
| `GENESIS_NYX_ROOT` | `genesis-nyx` 仓库路径，供 Nyx runner 使用 |

远程服务器第一轮建议先跑最小入门链路：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 python labs/06_genesis/00_env_check.py
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 GENESIS_STEPS=1000 python labs/06_genesis/01_first_simulation.py
```

这样先排除 viewer 和 GPU 变量。如果 CPU 无界面链路通过，再逐步打开 GPU、viewer、Nyx 或更复杂的官方示例。需要一次性跑完 `00` 到 `05` 的配套 codecheck 时，再使用：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 bash labs/06_genesis/run_all.sh
```

注意：`GENESIS_STEPS` 会影响后续所有读取该环境变量的脚本。只验收第一次仿真时，不要把 `run_all.sh` 和 `GENESIS_STEPS=1000` 混在一起当作最小入口。

## 先读 00_env_check

`00_env_check.py` 不创建场景，只回答“当前 Python 环境是不是可信”。通过后会生成：

```text
runs/genesis_codecheck_YYYYmmdd_HHMMSS/
  summaries/
    00_env_check.json
```

重点看这些字段：

| 字段 | 怎么解读 |
|---|---|
| `python_executable` | 是否是预期的 conda / venv Python |
| `torch_version` | PyTorch 是否成功导入 |
| `torch_cuda_available` | 当前环境是否能看到 CUDA |
| `torch_device_count` | GPU 数量是否符合预期 |
| `genesis_import` | `ok` 才说明 Genesis 包能导入 |
| `genesis_version` | 后续和官方示例版本边界对齐 |
| `nvidia_smi` | 服务器上驱动和显卡信息的原始证据 |

如果 `genesis_import` 失败，先不要调 viewer、相机或机器人资产。此时问题还停留在 Python 包层。只有 `00_env_check.py` 和 `01_first_simulation.py` 都通过，才进入后面的控制、渲染和并行脚本。

## 环境判读

看到一份 `00_env_check.json` 后，先用下面几题自查：

| 现象 | 应该怎样判断 |
|---|---|
| `genesis_import` 是 `failed` | 还没进入 Genesis 代码层，先修安装环境 |
| `torch_cuda_available` 是 `False`，但 `GENESIS_BACKEND=cpu` | 入门脚本仍然可以继续跑，不必先修 CUDA |
| `torch_cuda_available` 是 `False`，但需要跑 Nyx 或 CUDA showcase | 先检查 PyTorch CUDA wheel、驱动和服务器 GPU 暴露 |
| `python_executable` 指向 home 下另一个环境 | 不要继续排 Genesis，先确认当前 shell 激活了正确环境 |
| `nvidia_smi` 能看到 GPU，但 `torch_device_count` 是 0 | 驱动存在不代表当前 PyTorch 环境能用 CUDA |

这几题的目的，是把“环境问题”和“仿真问题”切开。很多初学者会把 `ModuleNotFoundError`、CUDA 不可见、viewer 打不开都混成“Genesis 有问题”，这样排错会非常慢。

## 共享服务器的空间设置

在共享服务器上，建议把环境、缓存、临时目录和 runs 都放在数据盘。例如：

```bash
BASE=/data/project/genesis-study
export TMPDIR=$BASE/tmp
export PIP_CACHE_DIR=$BASE/pip-cache
export XDG_CACHE_HOME=$BASE/cache
```

这不是 Genesis 特有要求，而是大 CUDA wheel、渲染插件和 Hugging Face 资产下载时的工程习惯。不要把大包和缓存默认写进 home。

## 读完应能回答

1. `python -m pip -V` 和 `which python` 为什么要一起看？
2. CPU 无界面链路通过以后，什么时候再切到 CUDA 或 viewer？
3. 共享服务器上，`TMPDIR`、`PIP_CACHE_DIR` 和 `XDG_CACHE_HOME` 为什么应该指向数据盘？

## 小结

- 最小 Genesis 安装和 Nyx / IPC 等扩展安装要分开。
- 先确认 `python`、`pip`、`torch`、`genesis` 属于同一环境。
- 远程服务器第一轮关闭 viewer，用 CPU 跑通核心链路。
- 大包下载和临时文件建议放数据盘，避免 home 或系统盘被占满。

## 导航

- 上一页：[三个理解视角](03-three-mental-models.md)
- 返回目录：[认识 Genesis](../01-getting-started.md)
- 下一页：[场景、实体与机器人](../02-scene-entity-robot.md)
