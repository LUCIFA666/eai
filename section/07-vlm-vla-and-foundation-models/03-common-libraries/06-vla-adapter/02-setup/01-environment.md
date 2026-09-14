# 环境安装

目标：搭好 VLA-Adapter 的 Python 环境，确认 PyTorch、FlashAttention、VLA-Adapter package 和 LIBERO 都能被当前解释器正确加载。

这一页的命令来自 VLA-Adapter 官方安装说明。除创建 conda 环境外，后续安装和验证命令默认在 VLA-Adapter 源码仓库根目录下运行。

## 准备 conda 环境

VLA-Adapter 官方安装说明使用 Python 3.10.16 创建 conda 环境：

```bash
conda create -n vla-adapter python=3.10.16 -y
conda activate vla-adapter
```

## 安装 PyTorch

本节使用的 PyTorch 版本组合是 `torch==2.2.0`、`torchvision==0.17.0`、`torchaudio==2.2.0`。

```bash
pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0
```

安装后可以做一次 GPU 验证：

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')
PY
```

由于 NumPy 兼容处理会放到 LIBERO requirements 安装之后，这一步可能会先看到 NumPy ABI warning。这里先看脚本最后三行输出，判断 PyTorch CUDA wheel 是否已经能识别 GPU。

最后三行参考输出如下：

```text
2.2.0+cu121
True
NVIDIA A100-SXM4-80GB
```

第一行是 PyTorch CUDA wheel 版本，第二行 `True` 表示 CUDA 可用，第三行是当前 GPU 名称。不同机器的 GPU 名称可能不同，关键是第二行输出为 `True`。

这一步同时可能看到下面这类 NumPy warning：

```text
A module that was compiled using NumPy 1.x cannot be run in
NumPy 2.2.6 as it may crash. To support both 1.x and 2.x
versions of NumPy, modules must be compiled with NumPy 2.0.
Some module may need to rebuild instead e.g. with 'pybind11>=2.12'.

If you are a user of the module, the easiest solution will be to
downgrade to 'numpy<2' or try to upgrade the affected module.
We expect that some modules will need time to support NumPy 2.
```

这个 warning 来自 PyTorch 2.2.0 与 NumPy 2.x 的 ABI 兼容问题，后面会通过 `numpy==1.26.4` 统一处理。

## 安装 VLA-Adapter

VLA-Adapter 源码安装采用 clone 仓库后 editable install 的方式：

```bash
git clone https://github.com/OpenHelix-Team/VLA-Adapter.git
cd VLA-Adapter
pip install -e .
```

如果源码已经放在某个目录，可以进入已有源码目录执行 `pip install -e .`，无需重复 clone。

安装完成后，可以用下面这段最小导入脚本确认当前环境已经能找到 VLA-Adapter 的 `prismatic` package：

```bash
python - <<'PY'
import prismatic
print('prismatic import ok')
PY
```

最后一行参考输出如下：

```text
prismatic import ok
```

导入时可能出现 TensorFlow / XLA / TensorRT 相关日志；如果最后一行是 `prismatic import ok`，且前面没有 Python exception，可以认为 VLA-Adapter package 已经安装到当前环境。

## 安装 Ninja

FlashAttention 安装前，先安装 `packaging` 和 `ninja`：

```bash
pip install packaging ninja
ninja --version; echo $?
```

参考输出如下：

```text
1.13.0.git.kitware.jobserver-pipe-1
0
```

第二行 `0` 表示 `ninja --version` 正常退出。

## 安装 FlashAttention

```bash
pip install "flash-attn==2.5.5" --no-build-isolation
```

安装日志的最后一行参考输出如下：

```text
Successfully installed flash-attn-2.5.5
```

FlashAttention 对 PyTorch、CUDA、Python ABI 很敏感；如果源码编译失败，可以清理 pip 缓存，或从 FlashAttention release 页面下载与 `nvidia-smi`、PyTorch 版本匹配的 wheel。

## 安装 LIBERO benchmark 依赖

这里安装的是 LIBERO benchmark 的 Python 依赖，用于创建仿真任务和运行评测；RLDS 训练数据会在下一页单独准备。下面三行命令默认都在 VLA-Adapter 源码根目录下运行。第一行会把 LIBERO 仓库 clone 到当前目录；第二行安装刚 clone 下来的 `LIBERO/`；第三行安装 VLA-Adapter 自带的 LIBERO 评测 requirements。

```bash
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git
pip install -e LIBERO
pip install -r experiments/robot/libero/libero_requirements.txt
```

`experiments/robot/libero/libero_requirements.txt` 在参考验证环境中会把 NumPy 升到 2.2.6，而 `tensorflow==2.15.0` 仍要求 `numpy<2.0.0`，所以安装日志里会出现下面这类 dependency conflict 提示。这里的 `ERROR:` 是 pip resolver 报出的依赖冲突信息；只要最后仍显示 `Successfully installed ...`，这一步安装已经完成，后面再把 NumPy 固定回 1.x 即可。

```text
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
tensorflow 2.15.0 requires numpy<2.0.0,>=1.23.5, but you have numpy 2.2.6 which is incompatible.
Successfully installed numpy-2.2.6
```

`torch==2.2.0` 和 `tensorflow==2.15.0` 与 NumPy 1.x 组合更稳。VLA-Adapter 官方参考环境 `our_envs.txt` 中使用的是 `numpy==1.26.4`，因此这里直接把 NumPy 和几个容易随 pip resolver 漂移的关键包同步到官方参考版本：

```bash
pip install \
  numpy==1.26.4 \
  opencv-python==4.11.0.86 \
  protobuf==3.20.3 \
  tensorflow-metadata==1.16.1 \
  wandb==0.19.8
```

这组命令的重点不是把所有包都锁死，而是把已经遇到冲突的关键版本拉回官方参考环境：`numpy==1.26.4` 用于避开 PyTorch / TensorFlow 的 NumPy 2.x ABI 问题；`opencv-python==4.11.0.86` 可以避免新版 OpenCV 重新要求 `numpy>=2`；`protobuf==3.20.3` 和 `tensorflow-metadata==1.16.1`、`wandb==0.19.8` 成组同步，可以减少 protobuf 版本来回冲突。

## 补齐评测运行依赖

后续 smoke test 还需要补齐几个评测运行依赖：

```bash
pip install "PyOpenGL==3.1.7"
pip install msgpack
pip install msgpack-numpy
```

`PyOpenGL==3.1.7` 用于避免旧版 PyOpenGL 在 EGL 离屏渲染时缺少 `EGLDeviceEXT`。`msgpack` 和 `msgpack-numpy` 是运行 LIBERO rollout 时需要的序列化依赖。

可以用下面的脚本做一次最小导入验证：

```bash
python - <<'PY'
from OpenGL import EGL
import msgpack
import msgpack_numpy

print('has EGLDeviceEXT:', hasattr(EGL, 'EGLDeviceEXT'))
print('msgpack import ok')
print('msgpack_numpy import ok')
PY
```

预期能看到 `has EGLDeviceEXT: True`、`msgpack import ok` 和 `msgpack_numpy import ok`，之后再继续做 LIBERO 导入验证和后续 smoke test。

我们还需要临时把 `LIBERO/` 加入 `PYTHONPATH`。如果省略这一步，`pip install -e LIBERO` 之后仍可能遇到 `ModuleNotFoundError: No module named 'libero'`。

```bash
export PYTHONPATH=$PWD/LIBERO:$PYTHONPATH
```

设置好 `PYTHONPATH` 后，可以用下面的脚本确认 LIBERO benchmark 已经能被当前解释器导入：

```bash
python - <<'PY'
from libero.libero import benchmark
print('libero import ok')
print(benchmark.get_benchmark_dict().keys())
PY
```

参考输出如下：

```text
libero import ok
dict_keys(['libero_spatial', 'libero_object', 'libero_goal', 'libero_90', 'libero_10', 'libero_100'])
```

看到 `libero import ok` 和这组 benchmark key，说明当前环境已经可以导入 LIBERO benchmark。后续 LIBERO 评测主线会主要用到 `libero_spatial`、`libero_object`、`libero_goal` 和 `libero_10` 对应的任务集合。

## 导航

- 上一节：[安装与第一次跑通](../02-setup.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[LIBERO 数据](02-libero-data.md)
