# RoboTwin 与 BEHAVIOR

目标：理解 StarVLA 在双臂操作和人形家庭任务中的适配重点。RoboTwin 和 BEHAVIOR 都比 LIBERO 更复杂，主要复杂在动作空间、环境依赖和并行评测。

## RoboTwin

RoboTwin 2.0 是双臂机器人操作仿真 benchmark，包含 50 个任务，覆盖抓放、堆叠、工具使用等类型。官方 ref 中包含 Easy/Hard 两种场景随机化程度。

### 目录和命令

```text
examples/Robotwin/
├── train_files/
│   └── data_registry/data_config.py
└── eval_files/
    ├── run_policy_server.sh
    ├── deploy_policy.yml
    ├── eval.sh
    └── requirements.txt
```

评测流程：

```bash
# Terminal A
bash examples/Robotwin/eval_files/run_policy_server.sh
```

```bash
# Terminal B
conda activate robotwin
cd examples/Robotwin/eval_files
bash eval.sh task_name demo_clean my_test_v1 0 0
```

`eval.sh` 的 5 个位置参数：

| 位置 | 含义 | 示例 |
|---|---|---|
| 1 | 任务名称 | `adjust_bottle` |
| 2 | 数据模式 | `demo_clean` 或 `demo_randomized` |
| 3 | 实验名称 | `my_test_v1` |
| 4 | 起始 episode 编号 | `0` |
| 5 | 仿真 GPU ID | `0` |

### 调试重点

RoboTwin 是双臂任务，动作维度和控制语义通常比单臂 LIBERO 更复杂。调试时优先检查：

- 左右臂 action key 顺序。
- 双臂 gripper 通道。
- clean/randomized 数据模式是否和 checkpoint 匹配。
- `ROBOTWIN_PATH` 是否在 eval 脚本中设置正确。

## BEHAVIOR-1K

BEHAVIOR-1K 是家庭任务仿真 benchmark。StarVLA 文档中按照 2025 BEHAVIOR Challenge 的结构，在 50 个完整家庭任务上训练和评测，机器人是 R1Pro 人形机器人。

### GPU 要求

BEHAVIOR 的 OmniGibson 渲染依赖硬件光线追踪 RT Cores。官方 ref 明确提示：

- A100、H100 不适合运行 BEHAVIOR 仿真，因为没有 RT Cores。
- 推荐 RTX 3090、RTX 4090 或其他 GeForce RTX / Quadro RTX 系列。

这和训练大模型常用 A100/H100 的习惯相反。实际部署时可能需要一台机器跑模型 server，另一台 RTX 机器跑仿真 client。

### 动作维度

BEHAVIOR 的 R1Pro 动作维度是 23：

```python
"R1Pro": {
    "base": np.s_[0:3],
    "torso": np.s_[3:7],
    "left_arm": np.s_[7:14],
    "left_gripper": np.s_[14:15],
    "right_arm": np.s_[15:22],
    "right_gripper": np.s_[22:23],
}
```

这对 `action_dim`、`state_dim`、`DataConfig.action_keys` 和 `modality.json` 都提出了更高要求。任意一处维度不一致都会导致训练或评测错位。

### 评测方式

官方 ref 中提供三类运行方式：

```bash
# 并行评测
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 bash examples/Behavior/start_parallel_eval.sh
```

```bash
# 独立终端调试
bash examples/Behavior/start_server.sh
bash examples/Behavior/start_client.sh
```

```bash
# 按任务评测，减少内存压力
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 bash examples/Behavior/start_parallel_eval_per_task.sh
```

### wrapper 选择

BEHAVIOR 文档提到几种 wrapper：

| Wrapper | 观测 | 特点 |
|---|---|---|
| `RGBLowResWrapper` | 224×224 RGB | 快，适合标准赛道 |
| `DefaultWrapper` | RGB + 深度 + 分割 | 更接近默认采集，慢 |
| `RichObservationWrapper` | 法线、光流、特权任务信息 | 只能用于特权信息赛道 |

这说明 BEHAVIOR 的观测配置会显著影响速度和公平性。写教程或复现实验时必须说明使用哪个 wrapper。

## 小结

- RoboTwin 的难点在双臂动作空间和 clean/randomized 模式。
- BEHAVIOR 的难点在 23 维人形动作、OmniGibson 依赖和 RT Core GPU 要求。
- 复杂 benchmark 要先按任务或少量 episode 调试，再做批量评测。

## 动手练习

1. 运行 `rg -n "action_indices|left|right|gripper|R1Pro|slice" examples/Robotwin examples/Behavior`，从源码中数出双臂动作字段的维度依据。
2. 在安装好 RoboTwin 环境后，写一个单任务 `eval.sh` 命令并把 GPU 设为 0。成功输出应至少启动一个任务评测进程。
3. 运行 `rg -n "gpu|cuda|headless|omniverse|isaac|port" examples/Behavior`，列出判断当前机器是否适合跑 BEHAVIOR 仿真的依据。

## 导航

- 上一节：[02 SimplerEnv 与 RoboCasa](02-simplerenv-and-robocasa.md)
- 返回上级：[其他 Benchmark](../08-other-benchmarks.md)
- 下一节：[扩展 StarVLA](../09-extension.md)
