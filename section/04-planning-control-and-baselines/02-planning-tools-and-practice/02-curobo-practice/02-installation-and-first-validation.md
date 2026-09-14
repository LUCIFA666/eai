# 环境实战：用 Conda 安装 cuRoboV2 并完成 GPU 自检

目标：在 Ubuntu 单 GPU 环境中创建隔离的 cuRoboV2 Conda 环境，正确选择 CUDA 12/13 安装 extra，并用四层检查确认驱动、PyTorch、cuRobo 和官方测试都可用。

## 本页成功标准

不要用“`pip install` 没报错”判断安装成功。本页完成后应同时满足：

1. `nvidia-smi` 能看到目标 GPU；
2. PyTorch 的 `torch.cuda.is_available()` 为 `True`；
3. `import curobo` 成功且能打印版本；
4. `pytest --pyargs curobo.tests` 通过，或失败项能明确归因；
5. `python -m curobo.examples.getting_started.forward_kinematics` 能创建 CUDA tensor 并完成 FK。

## 官方环境要求

以 cuRoboV2 最新安装页为准，当前官方基线是：

| 项目 | 官方要求/建议 | 本教程选择 |
|---|---|---|
| 系统 | Ubuntu 20.04+ | Ubuntu 22.04 |
| GPU | Turing 之后的 NVIDIA GPU，至少 4 GB VRAM | Ampere 或更新，建议 8 GB+ |
| 驱动 | `>= 580.65.06`，至少支持 CUDA 12 | 先检查再选 extra |
| Python | `>= 3.10`，高于 3.13 未验证 | Python 3.11 |
| 环境管理 | 官方推荐 `uv` | Conda 隔离环境 + `uv pip` 安装 |
| GPU 数量 | 单卡即可 | `CUDA_VISIBLE_DEVICES=0` |

cuRobo 的入门实验不需要多 GPU。多卡不会自动让单次 FK、IK 或 MotionPlanner 更快；除非应用自己把多个独立请求分发到不同进程，否则只暴露一张卡更容易排错。

## 先理解三种“CUDA 版本”

安装失败时，人们经常说“我的 CUDA 是 12.8”，但这个数字可能指三件不同的事：

- `nvidia-smi` 顶部的 CUDA Version：**驱动最多支持的 CUDA runtime 版本**；
- `nvcc --version`：本机 CUDA Toolkit 编译器版本；
- `torch.version.cuda`：当前 PyTorch wheel 编译时绑定的 CUDA 版本。

三者不必完全相同。最关键的是驱动必须足够新，PyTorch CUDA wheel 必须能在该驱动上运行，而 cuRobo 安装 extra 要与选择的 PyTorch/CUDA 大版本匹配。

## 第一步：检查宿主机

```bash
nvidia-smi
nvcc --version || true
uname -a
lsb_release -a
```

重点看：

- GPU 型号、显存和驱动版本；
- 是否有其他进程占满显存；
- 系统是否真的是原生 Ubuntu/受支持环境；
- `nvcc` 不存在不一定意味着 PyTorch 不能用 GPU，但涉及本地 CUDA 扩展编译时需要进一步确认。

如果机器有多张卡，先固定一张：

```bash
export CUDA_VISIBLE_DEVICES=0
```

此后 Python 中的 `cuda:0` 指的是“被暴露出来的第一张卡”，不一定是物理编号 0。

## 第二步：创建 Conda 环境

```bash
conda create -n curobo-v2 python=3.11 uv git git-lfs -c conda-forge -y
conda activate curobo-v2
git lfs install

which python
python --version
uv --version
```

期望 `which python` 指向类似：

```text
.../envs/curobo-v2/bin/python
```

如果仍指向系统 Python，先不要继续。常见原因是 shell 没有执行 `conda init`，或当前终端还未重新加载。

## 第三步：克隆并固定版本

```bash
git clone https://github.com/NVlabs/curobo.git
cd curobo
git fetch --tags
git checkout v0.8.0
git status --short
```

本组正文按 cuRoboV2 v0.8.x API 编写，代码同时核对过官方提交 `a35a708ecfbb26eb9ab2d7ef22c65919c4fae4a9`。教学复现优先固定 release tag，不建议直接跟随不断变化的 `main`。

<div class="concept-note concept-orange">如果官方已发布更新的 v0.8.x 补丁版本，应优先固定最新补丁 tag，并确认官方 getting-started 示例没有改变 API。不要一边使用 latest 文档，一边检出 v0.7.x 代码。</div>

## 第四步：选择 CUDA extra

cuRoboV2 的 `pyproject.toml` 提供互斥的 extras。新环境还没有 PyTorch时，选择带 `-torch` 的版本：

### 驱动支持 CUDA 12

```bash
uv pip install --python "$CONDA_PREFIX/bin/python" '.[cu12-torch]'
```

### 驱动支持 CUDA 13

```bash
uv pip install --python "$CONDA_PREFIX/bin/python" '.[cu13-torch]'
```

如果环境中已经安装了经过验证的 GPU PyTorch，可选择不带 `-torch` 的 `.[cu12]` 或 `.[cu13]`。初学者不建议这样做，因为原有 PyTorch 可能是 CPU wheel，或 CUDA 大版本不匹配。

为什么命令里要加引号？在某些 shell 中，方括号会参与 glob 展开。写成 `'.[cu12-torch]'` 可以避免 extra 名称被 shell 改写。

## 第五步：四层验证

### 层 1：Python 包

```bash
python -c "import curobo; print('curobo:', curobo.__version__)"
```

### 层 2：PyTorch 与 GPU

```bash
python - <<'PY'
import torch

print("torch:", torch.__version__)
print("torch CUDA build:", torch.version.cuda)
print("CUDA available:", torch.cuda.is_available())
print("visible devices:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("device 0:", torch.cuda.get_device_name(0))
    x = torch.ones(1024, device="cuda")
    print("CUDA tensor sum:", x.sum().item())
PY
```

这里应看到 `visible devices: 1` 和正确的 GPU 名称。若 `curobo` 能 import 但 `CUDA available: False`，问题在 PyTorch/驱动层，不要继续调 cuRobo 规划参数。

### 层 3：官方单元测试

```bash
pytest --pyargs curobo.tests
```

首次运行可能需要编译/加载 CUDA 相关组件和建立缓存，明显慢于后续运行。不要在第一次运行时因为几分钟没有输出就强制中断；另开终端检查 GPU、CPU、磁盘和编译进程。

### 层 4：最小 GPU 功能

```bash
python -m curobo.examples.getting_started.forward_kinematics
```

官方示例会加载 Franka 配置、计算单次 FK、批量计算 1000 个关节状态，并验证 FK 可微。成功时应看到机器人自由度、tool frame、末端位置/四元数和批量输出 shape。具体数值受版本与配置影响，不应逐字符对比。

本课程也提供更短的检查脚本：

```bash
python labs/04-curobo/check_install.py
```

## 首次运行为什么慢

cuRobo 会使用 PyTorch、CUDA/Warp 和 CUDA Graph。第一次 import 或第一次调用某类求解器时，可能发生：

- 下载/加载依赖；
- 编译针对当前 GPU 架构的代码；
- 创建缓存；
- 预分配求解器 buffer；
- `warmup()` 捕获 CUDA Graph。

因此性能比较必须分开记录：

```text
cold-start time = 进程启动 + import + 编译/加载 + solver 初始化
warm solve time  = 已初始化求解器上的后续请求
```

把两者混在一起，会得出“GPU 规划比 CPU 还慢”的错误结论。

## 为什么本页没有 batch size

安装阶段没有训练，因此没有训练 batch size。批量规模会在后续脚本中明确给出：

| 实验 | 默认规模 |
|---|---:|
| FK | 1000 组关节状态 |
| IK | 100 个目标，每目标 32 个 seed |
| 无碰撞 IK | 50 个目标，每目标 32 个 seed |
| MotionPlanner warmup | 5 次 warmup iteration |

显存较小的机器先把目标 batch 减半，再考虑减少 seed。每次只改一个参数，并记录成功率和最大显存。

## 常见问题

### `torch.cuda.is_available()` 为 `False`

排查顺序：

1. `nvidia-smi` 是否正常；
2. 当前 Python 是否来自 `curobo-v2` 环境；
3. `pip show torch` / `uv pip show torch` 是否安装了 CPU wheel；
4. `torch.version.cuda` 是否为 `None`；
5. 是否在容器中忘记传入 GPU。

### `no kernel image is available`

通常表示已编译代码不包含当前 GPU compute capability。确认 GPU 架构是否满足官方要求，清理对应扩展缓存后重装；不要随意复制别人的编译缓存。

### `CUDA driver version is insufficient`

驱动比 PyTorch/CUDA runtime 需求旧。升级驱动或选择与当前驱动兼容的官方 extra；单独安装一个更高版本 Toolkit 不能替代驱动升级。

### 安装后导入了旧 cuRobo

```bash
python - <<'PY'
import curobo
print(curobo.__file__)
print(curobo.__version__)
PY
```

如果路径指向另一个环境或旧 editable install，先移除旧包。不要让 `PYTHONPATH` 同时包含 v0.7.x 与 v0.8.x 源码。

### `git-lfs` 文件只是小文本指针

```bash
git lfs install
git lfs pull
```

检查素材文件头部是否出现 `version https://git-lfs.github.com/spec/v1`。出现这个文本说明实际大文件没有拉取。

### Out of memory

先确认是否有其他进程占用显存：

```bash
nvidia-smi
```

后续实验中逐步降低目标 batch、seed 或缓存容量。不要在没有理解含义时直接把所有参数设成 1；那可能让成功率大幅下降。

### Windows / WSL

旧文档曾提到实验性 Windows 支持，但 cuRoboV2 当前安装页以 Ubuntu 为保证路径。本教程不把 Windows 原生环境作为主线。WSL2 也应单独验证 GPU passthrough、驱动、文件系统性能和可视化端口；遇到问题时先在官方 Ubuntu 路径复现。

## 保存环境证据

后续在 GPU 机器上复现时，建议把下面输出保存到 `runs/04-curobo/environment.txt`：

```bash
{
  date -Iseconds
  git rev-parse HEAD
  python --version
  uv pip freeze
  nvidia-smi
  python -c "import torch, curobo; print(torch.__version__, torch.version.cuda, curobo.__version__)"
} | tee runs/04-curobo/environment.txt
```

环境证据比一句“在 4090 上跑通”更有用：驱动、PyTorch wheel、cuRobo commit 和 Python 版本缺一不可。

## 自查问题

1. `nvidia-smi` 显示的 CUDA Version 和 `torch.version.cuda` 有什么不同？
2. 为什么本教程使用 Conda 创建环境，却用 `uv pip` 安装项目？
3. 新环境应选择 `cu12-torch` 还是 `cu12`？
4. 为什么第一次求解时间不能直接作为在线规划延迟？
5. 多卡机器为什么仍建议从 `CUDA_VISIBLE_DEVICES=0` 开始？

## 参考资料

- [cuRoboV2 Installation](https://nvlabs.github.io/curobo/latest/getting-started/installation.html)
- [NVlabs/curobo pyproject.toml](https://github.com/NVlabs/curobo/blob/main/pyproject.toml)
- [NVlabs/curobo releases](https://github.com/NVlabs/curobo/releases)
