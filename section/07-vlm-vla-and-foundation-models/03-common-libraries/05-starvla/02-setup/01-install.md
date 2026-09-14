# 环境安装

目标：搭建能训练和加载 StarVLA 模型的 Python 环境，并理解几个容易出错的依赖点。

在 [代码结构](../01-overview.md/02-code-struct.md) 中，我们已经克隆了官方仓库，约定这个仓库路径为 `<STARVLA_ROOT>`。

```bash
cd <STARVLA_ROOT>

conda create -n starvla python=3.10 -y
conda activate starvla

pip install -v torch==2.6.0 torchvision==0.21.0 \
  --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
pip install flash-attn==2.7.4.post1 --no-build-isolation
pip install -e .
```
下载 CUDA wheel 体积很大，网络慢时建议保留 `-v`，这样能看到当前正在下载哪个包。

## Python 版本

StarVLA 官方示例主要使用 Python 3.10。LIBERO 等 benchmark 可能有自己的版本约束，第一次上手可以先按下面方式分开：

| 环境 | 推荐版本 | 用途 |
|---|---|---|
| `starvla` | Python 3.10 | 训练、加载模型、启动推理服务 |
| `libero` 或其它 benchmark 环境 | 按 benchmark README | 运行仿真和评测脚本 |

如果 LIBERO 环境也能顺利使用 Python 3.10，可以减少跨环境问题。

## PyTorch、CUDA 和 flash-attn

`flash-attn` 需要和本机 CUDA、PyTorch 版本匹配。安装前先检查：

```bash
nvcc -V
python -c "import torch; print(torch.__version__, torch.version.cuda)"
pip list | grep -E "torch|transformers|flash-attn"
```

如果 `pip install flash-attn==2.7.4.post1 --no-build-isolation` 失败，优先检查三件事：

1. 当前环境是否已经安装 PyTorch。
2. `torch.version.cuda` 和 `nvcc -V` 显示的 CUDA 版本是否匹配。
3. 当前机器是否需要安装预编译 wheel，或者切换到 `sdpa` attention 后端。

ROCm 或其它非 CUDA 环境通常不能直接使用 `flash_attention_2`。这类环境可以尝试在训练命令里设置：

```bash
--framework.qwenvl.attn_implementation sdpa
```

这个设置只改变 VLM attention 后端，不改变 StarVLA 的数据、训练和部署主线。

## 开发模式安装源码

`pip install -e .` 会把当前源码目录安装到 Python 环境中。这样从仓库根目录运行训练脚本时，下面这些 import 才能稳定找到：

```python
from starVLA.dataloader import build_dataloader
from starVLA.model.framework.base_framework import build_framework
```

安装后做一个环境检查：

```bash
cd <STARVLA_ROOT>
python -c "import torch, torchvision; print(torch.__version__, torch.version.cuda, torchvision.__version__, torch.cuda.is_available())"
python -c "import starVLA; print(starVLA.__file__)"
python -c "from starVLA.dataloader import build_dataloader; print(build_dataloader)"
python -c "from starVLA.model.framework.base_framework import build_framework; print(build_framework)"
```

第一条命令的输出应包含 `2.6.0`、`12.4` 和一个布尔值。安装在 GPU 机器上时，最后通常应为 `True`；在没有 GPU 的节点上可以先允许它为 `False`，训练和推理再换到 GPU 节点运行。

## benchmark 依赖分开装

LIBERO、RoboCasa、SimplerEnv 等环境往往有自己的 MuJoCo、robosuite、numpy 版本要求。评测时建议分两个终端：

```text
Terminal A: conda activate starvla
  cd <STARVLA_ROOT>
  python deployment/model_server/server_policy.py ...

Terminal B: conda activate libero
  cd <STARVLA_ROOT>
  python examples/LIBERO/eval_files/eval_libero.py ...
```

两边通过推理服务通信，StarVLA 环境负责模型，benchmark 环境负责仿真。

## 小结

- StarVLA 训练环境建议使用 Python 3.10。
- `flash-attn` 要和 PyTorch/CUDA 对齐，不适配时可以尝试 `sdpa`。
- `pip install -e .` 是本地源码运行的关键步骤。
- 评测时可以把模型环境和仿真环境分开。

## 动手练习

1. 运行上面的 PyTorch 检查命令，记录 `torch.__version__`、`torch.version.cuda` 和 `torch.cuda.is_available()`。成功输出应能直接看到版本号和 CUDA 是否可用。
2. 从 `<STARVLA_ROOT>` 执行 `python -c "from starVLA.dataloader import build_dataloader; print(build_dataloader)"`。成功输出会打印一个函数对象。
3. 执行 `export WANDB_MODE=disabled`，再执行 `python -c "import os; print(os.environ.get('WANDB_MODE'))"`。成功输出应为 `disabled`。

## 导航

- 上一节：[安装与链路验证](../02-setup.md)
- 返回上级：[安装与链路验证](../02-setup.md)
- 下一节：[02 链路验证](02-link-validation.md)
