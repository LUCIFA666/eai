# RT-1 实践：跑通 action tokenizer 最小源码测试

本页目标是把 RT-1 落到一条最小源码验证路径：搭好 TF1 源码环境，跑通官方仓库的 `action_tokenizer_test`，并说明这个测试能证明什么、不能证明什么。

## 学习目标

- 搭建环境（Python 3.7 + TensorFlow 1.15.5），跑通 `action_tokenizer_test`。
- 理解 `tensor2robot`、`t2r_pb2` 和 `tensorflow.contrib` 为什么会影响这个最小测试。
- 分清 `action_tokenizer_test` 验证的是 action tokenizer 最小链路，不是完整 RT-1 模型。

## RT-1 在工程里起什么作用

RT-1 是一个高层视觉语言机器人策略模型：

```txt
图像 + 语言指令 / 语言 embedding + 机器人状态
  -> RT-1 policy
  -> 末端位移 / 旋转增量 / 夹爪动作 / 终止标志
```

它在系统里扮演的是“高层大脑”：真实项目里把 RT-1 放在策略层，外面再接相机采集、图像预处理、语言 embedding、action adapter（把模型动作转换成机器人控制命令）、以及安全限制和急停，由这些模块把它的决策落到具体电机上。因此本节不尝试复现论文指标或跑完整策略，只做 action tokenizer 的最小源码测试。

## 官方仓库结构

RT-1 官方仓库提供的是一组核心模型组件、tokenizer 和测试工具。第一次读时，可以按下面顺序理解关键文件。

| 文件 | 重点 | 功能 |
|---|---|---|
| `README.md` | Features | 确认 RT-1 由 FiLM EfficientNet、TokenLearner、Transformer 组成 |
| `tokenizers/action_tokenizer.py` | `RT1ActionTokenizer` | 连续动作 ↔ 离散动作 token |
| `transformer_network.py` | `TransformerNetwork.__init__` 的参数 | vocab size、token embedding、层数、heads、是否使用 TokenLearner |
| `transformer.py` | Decoder-only Transformer | 对 token 序列建模并预测 action token |
| `film_efficientnet/` | 图像 tokenizer backbone | 图像 + 语言条件化 |

## 跑通源码单元测试

### 硬件与系统准备

本次实验使用的服务器环境如下：

| 项目 | 配置 |
|---|---|
| GPU | NVIDIA A100-SXM4-80GB × 8 |
| 显存 | 单卡 80 GB |
| 操作系统 | Ubuntu 24.04.3 LTS |
| 内核 | Linux 6.8 |
| NVIDIA 驱动 | 580.x |

### 环境搭建

源码依赖 `tensorflow.contrib`，因此需要 TensorFlow 1.x；而 TensorFlow 1.15.x 更稳妥的 Python 版本是 Python 3.7。

| 依赖 | 推荐版本 | 原因 |
|---|---:|---|
| Python | 3.7 | 兼容 TensorFlow 1.15.x |
| TensorFlow | 1.15.5 | 保留 `tensorflow.contrib` |
| protobuf | 3.19.6 | 避免新 protobuf 与老生成代码不兼容 |
| pip | <24 | 减少老包 metadata 构建问题 |
| setuptools | 57.5.0 | 避免旧包触发 `build_py_2to3` 错误 |

创建环境并降级构建工具，再装核心依赖：

```bash
conda create -n rt1 python=3.7 -y
conda activate rt1

pip install "pip<24" "setuptools==57.5.0" "wheel==0.37.1"
pip install \
  "numpy==1.18.5" \
  "protobuf==3.19.6" \
  "tensorflow==1.15.5" \
  "tensorflow-serving-api==1.15.0" \
  "absl-py>=0.5.0" \
  "gin-config>=0.1.4" \
  "tf-slim>=1.0"
```

验证 TensorFlow：

```bash
python -c "import tensorflow as tf; print(tf.__version__); print(hasattr(tf, 'contrib'))"
# 期望输出：1.15.5  /  True
```

如果这里输出 TensorFlow 2.x，后面大概率会继续遇到 `tensorflow.contrib` 缺失。

### 代码准备

原始 `requirements.txt` 里这一行会报错，因为 pip 会把 `tensor2robot` 当标准包装，但它根目录没有可用的 `setup.py` / `pyproject.toml`：

```txt
git+https://github.com/google-research/tensor2robot#tensor2robot
```

更稳妥的做法是手动 clone，并通过 `PYTHONPATH` 暴露源码。先建一个 workspace 目录，把两个仓库放在一起：

```bash
mkdir rt1-workspace && cd rt1-workspace
git clone https://github.com/google-research/robotics_transformer.git
git clone https://github.com/google-research/tensor2robot.git
```

`tensor2robot/proto/t2r.proto` 需要生成对应的 `t2r_pb2.py`，否则导入时报 `ImportError: cannot import name 't2r_pb2'`。注意下面的命令都在 workspace 目录（两个仓库的父目录）下执行，这样生成的 `t2r_pb2.py` 才能落在正确的 import 路径上：

```bash
# 仍在 rt1-workspace 目录下
protoc --python_out=. tensor2robot/proto/t2r.proto   # 没有 protoc 可先 conda install -c conda-forge protobuf=3.19.6
touch tensor2robot/proto/__init__.py
export PYTHONPATH=$PWD
python -c "from tensor2robot.proto import t2r_pb2; print('proto OK')"
```

其中 `export PYTHONPATH=$PWD` 把 workspace 目录暴露给 Python，后面 import `robotics_transformer` 和 `tensor2robot` 都依赖这一步。

顺便说明：上面的命令默认两个仓库是 **并列** 的（`robotics_transformer/` 和 `tensor2robot/` 同在 workspace 下），所以一条 `PYTHONPATH` 就够。如果你把 `tensor2robot` 放进了 `robotics_transformer` 内部（嵌套布局），两个 import 的父目录就不一样了，需要同时暴露两层，否则会遇到 `No module named 'robotics_transformer'` 或 `No module named 'tensor2robot'`：

```bash
# 嵌套布局：tensor2robot 在 robotics_transformer 里面
export PYTHONPATH=<仓库父目录>:<仓库父目录>/robotics_transformer
# 例如仓库在 /path/to/workspace/robotics_transformer 时：
# export PYTHONPATH=/path/to/workspace:/path/to/workspace/robotics_transformer
```

### Python 3.7 兼容修复

在 Python 3.7 里，源码中的 `list[str]` 这种内置泛型标注会报 `TypeError: 'type' object is not subscriptable`，需要改成 `typing.List`。`tokenizers/action_tokenizer.py` 里两处要改：

```python
from typing import List, Optional

action_order: Optional[List[str]] = None      # __init__ 参数
def action_order(self) -> List[str]: ...       # property 返回标注
```

另外，`action_tokenizer_test.py` 用了 `.numpy()`，需要启用 eager 模式；同时可以用 TensorFlow 自带的 `tensor_spec` 替代 `tf_agents`，避免为最小测试额外装一个大依赖。在 `robotics_transformer/tokenizers/action_tokenizer_test.py` 顶部做两处修改：

```python
import tensorflow as tf
from tensorflow.python.framework import tensor_spec   # 替换原来的 from tf_agents.specs import tensor_spec
tf.enable_eager_execution()                            # 紧跟在 import tensorflow 之后加一行
```

### 运行最小测试

仍在 workspace 目录下（确保 `PYTHONPATH` 已设置）：

```bash
python -m robotics_transformer.tokenizers.action_tokenizer_test
```

预计输出：

```txt
----------------------------------------------------------------------
Ran 9 tests in 0.087s

OK (skipped=1)
```

跑到这一步，说明的是一条**最小 action tokenizer 链路**已经通了：Python 能 import `robotics_transformer.tokenizers.action_tokenizer`；`tensor2robot.utils.tensorspec_utils` 能被加载，因此 `t2r_pb2` 和 `tensorflow.contrib` 这类老依赖也基本可用；`RT1ActionTokenizer` 对离散 one-hot 动作、连续动作离散化、边界值、非法 shape、带 batch / time 维的动作，以及 tokenize-detokenize 的近似往返行为都通过了测试。

它不代表完整 RT-1 模型已经跑通。这个测试不会覆盖 `TransformerNetwork`、FiLM EfficientNet、TokenLearner、训练循环、checkpoint 加载，也不会说明模型能输出有意义的机器人动作。

## 常见问题

| 报错 | 原因 | 解决方法 |
|---|---|---|
| `No module named 'tensorflow.contrib'` | 跑源码时装成了 TF2 | 源码用 TF1 环境（Python 3.7 + TF 1.15.5） |
| `cannot import name 't2r_pb2'` | 没生成 tensor2robot 的 proto | 对 `t2r.proto` 执行 `protoc --python_out=.` |
| `TypeError: 'type' object is not subscriptable` | Python 3.7 不支持 `list[str]` | 改用 `typing.List[str]` |
| `No module named 'robotics_transformer'` | `PYTHONPATH` 没含仓库父目录 | 把仓库父目录放进 `PYTHONPATH` |
| `Command 'bazel' not found` | 仓库不是 Bazel workspace | 用 Python module 方式跑测试，不用 bazel |

## 小结

- RT-1 的源码依赖 TF1（`tensorflow.contrib`），需要 Python 3.7 + TF 1.15.5；`t2r_pb2` 必须手动从 proto 生成，`tf_agents` 可用内置 `tensorflow.python.framework.tensor_spec` 替代。
- `action_tokenizer_test` 通过说明最小 action tokenizer 链路可用（import、proto、往返编解码），不代表完整 RT-1 模型可用，`TransformerNetwork` / FiLM EfficientNet / 训练循环均未覆盖。

## 动手练习

用理论页里的 `SimpleRT1ActionTokenizer`，把 `vocab_size` 依次设为 `256`、`16`、`4`，对同一个 `world_vector = [0.3, -0.7, 0.1]` 做 encode -> decode，计算 `np.abs(decoded["world_vector"] - original).max()`（即 decode 还原的值和原始值之间的最大绝对差）。观察这个差值随 `vocab_size` 缩小怎么变化，并解释为什么 token 总数（8 个）始终不变。

## References

- [RT-1: Robotics Transformer for Real-World Control at Scale](https://arxiv.org/abs/2212.06817)
- [google-research/robotics_transformer](https://github.com/google-research/robotics_transformer)
- [google-research/tensor2robot](https://github.com/google-research/tensor2robot)

## 导航

- 上一节：[RT-1 理论基础](01-theory.md)
- 返回上级：[RT-1](../01-rt1.md)
- 下一节：[Octo](../02-octo.md)