# 其他 Benchmark

目标：了解 StarVLA 在 LIBERO 以外支持的 benchmark，以及适配新 benchmark 时的通用目录结构。

LIBERO 之外，StarVLA 还支持或正在支持这些 benchmark：

| Benchmark | 机器人 / 场景 | 特点 |
|---|---|---|
| SimplerEnv | WidowX 桌面操作 | Bridge / RT-1 系列泛化评测 |
| RoboCasa | GR1 上半身桌面任务 | 24 个 tabletop pick-and-place 任务 |
| RoboTwin | 双臂机器人 | 50 个任务，clean/randomized 两种数据 |
| BEHAVIOR-1K | R1Pro 人形家庭任务 | 23 维动作，OmniGibson，GPU 要求特殊 |

理解 LIBERO 端到端实战之后，切换到其他 benchmark 主要是替换数据注册（`data_config.py`）、字段映射（`modality.json`）和环境适配器（`model2*_interface.py`）。

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [01 benchmark 目录模式](08-other-benchmarks/01-benchmark-pattern.md) | 各 benchmark 目录的通用结构 | `train_files`、`eval_files`、data registry |
| [02 SimplerEnv 与 RoboCasa](08-other-benchmarks/02-simplerenv-and-robocasa.md) | WidowX / GR1 评测有什么差异 | Bridge / Fractal 数据、RoboCasa tabletop |
| [03 RoboTwin 与 BEHAVIOR](08-other-benchmarks/03-robotwin-and-behavior.md) | 双臂和人形任务如何适配 | action_dim、GPU 要求、并行评测 |

## 导航

- 上一节：[LIBERO 端到端实战](07-libero-end-to-end.md)
- 返回上级：[StarVLA](../05-starvla.md)
- 下一节：[01 benchmark 目录模式](08-other-benchmarks/01-benchmark-pattern.md)
