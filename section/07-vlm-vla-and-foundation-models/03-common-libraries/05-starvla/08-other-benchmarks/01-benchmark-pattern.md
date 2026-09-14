# benchmark 目录模式

目标：掌握 StarVLA 中 benchmark 目录的通用结构。理解这个模式后，从 LIBERO 切到 RoboCasa 或 RoboTwin 就不会重新迷路。

一个完整 benchmark 目录通常长这样：

```text
examples/<Benchmark>/
├── README.md
├── data_preparation.sh                 # 可选，准备数据
├── train_files/
│   ├── run_*.sh                        # 训练脚本
│   ├── *.yaml                          # 训练配置
│   ├── modality.json                   # 字段映射
│   └── data_registry/data_config.py    # DataConfig 和 mixture
└── eval_files/
    ├── run_policy_server.sh            # 启动 StarVLA server
    ├── eval_*.sh / simulation_env.py    # 启动环境评测
    └── model2*_interface.py            # 环境到模型的 client adapter
```

不同 benchmark 的文件会有差异，这几个角色通常都会出现。

## train_files

`train_files` 定义训练侧：

| 文件 | 作用 |
|---|---|
| `*.yaml` | framework、数据、训练超参 |
| `run_*.sh` | 把模型路径和命令行覆盖项组织起来 |
| `modality.json` | LeRobot 原始字段映射 |
| `data_registry/data_config.py` | robot type、action keys、mixture |

如果训练报数据错误，先看 `modality.json` 和 `data_config.py`；如果训练找不到路径，先看 `run_*.sh` 顶部变量。

## eval_files

`eval_files` 定义评测侧：

| 文件 | 作用 |
|---|---|
| `run_policy_server.sh` | StarVLA 环境启动 server |
| `eval_*.sh` | benchmark 环境启动仿真 |
| `model2*_interface.py` | 把 observation 变成 StarVLA `example`，把 action 拆回环境格式 |
| `adaptive_ensemble.py` | 可选动作集成 |
| `wrappers/` | 可选环境 wrapper |

如果 server 已经返回动作但环境执行不对，重点看 `model2*_interface.py` 和环境 eval 文件。

## 训练和评测的共同数据契约

训练时 framework 消费：

```python
{
    "image": [...],
    "lang": "...",
    "action": np.ndarray,
    "state": np.ndarray,
}
```

评测时 client 发送：

```python
{
    "image": [...],
    "lang": "...",
}
```

可选带 `state`。这个契约让不同 benchmark 可以共用同一个 server。

## 新 benchmark 的最小文件

如果要加一个新 benchmark，最小集合通常是：

```text
examples/MyBench/train_files/modality.json
examples/MyBench/train_files/data_registry/data_config.py
examples/MyBench/train_files/starvla_mybench.yaml
examples/MyBench/train_files/run_mybench_train.sh
examples/MyBench/eval_files/model2mybench_interface.py
examples/MyBench/eval_files/eval_mybench.py
```

如果只评测已有 checkpoint，训练文件可以少一些；如果要训练新数据，就必须有 data registry。

## 小结

- `train_files` 管训练数据和训练配置。
- `eval_files` 管环境适配和评测流程。
- `model2*_interface.py` 是 benchmark 特异性最强的文件。
- 新 benchmark 优先复制已有结构，再替换字段映射、DataConfig 和环境 step 逻辑。

## 动手练习

1. 运行 `find examples/LIBERO examples/Robocasa_tabletop -maxdepth 2 -type f | sort`，比较两个 benchmark 目录里的训练、评测和接口文件。
2. 运行 `rg -n "WebsocketClientPolicy|action_chunk_size|predict_action" examples/SimplerEnv/eval_files/model2simpler_interface.py examples/Robocasa_tabletop/eval_files/model2robocasa_interface.py`，找到 websocket client 初始化和动作请求位置。
3. 为一个新 benchmark 列出最小文件清单，并用现有目录证明每个文件的角色：训练 YAML、data registry、policy interface、eval 脚本和可选 server 启动脚本。

## 导航

- 上一节：[其他 Benchmark](../08-other-benchmarks.md)
- 返回上级：[其他 Benchmark](../08-other-benchmarks.md)
- 下一节：[02 SimplerEnv 与 RoboCasa](02-simplerenv-and-robocasa.md)
