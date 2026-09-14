# SimplerEnv 与 RoboCasa

目标：理解 SimplerEnv 和 RoboCasa 在 StarVLA 中的评测差异。它们都走 policy server，但机器人、任务和环境适配不同。

## SimplerEnv

SimplerEnv 常用于 Bridge/RT-1 系列桌面操作泛化评测，典型机器人是 WidowX。StarVLA 模型库中有多组 Bridge + Fractal 训练 checkpoint，例如：

| 模型 | 框架 | 基座 VLM | WidowX 成功率参考 |
|---|---|---|---|
| Qwen2.5-FAST-Bridge-RT-1 | QwenFast | Qwen2.5-VL-3B | 58.6 |
| Qwen2.5-OFT-Bridge-RT-1 | QwenOFT | Qwen2.5-VL-3B | 41.8 |
| Qwen2.5-PI-Bridge-RT-1 | QwenPI | Qwen2.5-VL-3B | 62.5 |
| Qwen2.5-GR00T-Bridge-RT-1 | QwenGR00T | Qwen2.5-VL-3B | 63.6 |
| Qwen3VL-GR00T-Bridge-RT-1 | QwenGR00T | Qwen3-VL-4B | 65.3 |

这些数值来自官方模型库 ref，用于理解相对量级；实际复现会受环境版本和 checkpoint 影响。

### 目录结构

```text
examples/SimplerEnv/
├── train_files/
│   ├── starvla_cotrain_oxe.yaml
│   ├── run_oxe_train.sh
│   ├── modality.json
│   └── data_registry/data_config.py
└── eval_files/
    ├── model2simpler_interface.py
    ├── run_policy_server.sh
    ├── start_simpler_env.py
    └── auto_eval_scripts/
```

SimplerEnv 的自动评测脚本较多，按任务类型拆分，例如 drawer、move near、pick coke can 等。调试时建议先跑单任务，再跑批量脚本。

## RoboCasa

RoboCasa 是家庭场景仿真 benchmark。StarVLA 文档中使用的是 GR1 Tabletop Tasks 子集，包含 24 个桌面 pick-and-place 任务，使用 Fourier GR1 人形机器人的上半身双臂。

官方 ref 中 RoboCasa 平均结果示例：

| 模型 | 平均成功率参考 |
|---|---|
| GR00T-N1.6 | 47.6 |
| StarVLA-GR00T-Qwen3 | 47.8 |
| StarVLA-π-Qwen3 | 43.9 |
| StarVLA-OFT-Qwen3 | 48.8 |
| StarVLA-FAST-Qwen3 | 39.0 |

这些结果基于 24 个任务、每任务 50 次 rollout。

### 目录结构

```text
examples/Robocasa_tabletop/
├── train_files/
│   ├── starvla_cotrain_robocasa_gr1.yaml
│   ├── run_robocasa.sh
│   └── data_registry/data_config.py
└── eval_files/
    ├── simulation_env.py
    ├── model2robocasa_interface.py
    ├── wrappers/
    └── batch_eval_args.sh
```

评测启动示例：

```bash
# Terminal A: StarVLA server
python deployment/model_server/server_policy.py \
  --ckpt_path ${your_ckpt} \
  --port 5678 \
  --use_bf16
```

```bash
# Terminal B: RoboCasa env
python examples/Robocasa_tabletop/eval_files/simulation_env.py \
  --args.env_name ${env_name} \
  --args.port 5678 \
  --args.n_episodes 50 \
  --args.n_envs 1 \
  --args.max_episode_steps 720 \
  --args.n_action_steps 12 \
  --args.video_out_path ${video_out_path} \
  --args.pretrained_path ${your_ckpt}
```

## 关键差异

| 维度 | SimplerEnv | RoboCasa |
|---|---|---|
| 典型机器人 | WidowX | GR1 上半身双臂 |
| 数据来源 | Bridge/Fractal/OXE | PhysicalAI-Robotics-GR00T-X |
| 任务类型 | 桌面泛化任务 | 24 个 tabletop pick-and-place |
| 评测脚本 | 多个 auto eval shell | `simulation_env.py` + batch 脚本 |
| 动作适配 | WidowX 动作格式 | GR1 双臂动作格式 |

## 小结

- SimplerEnv 更关注 Bridge/RT-1 风格泛化，RoboCasa 更关注家庭桌面双臂操作。
- 两者都复用 StarVLA policy server，但 `model2*_interface.py` 差异很大。
- RoboCasa 的 episode 更长，环境 wrapper 更多，调试时要先跑少量 episode。

## 动手练习

1. 运行 `rg -n "raw_action|action_chunk_size|gripper|WebsocketClientPolicy" examples/SimplerEnv/eval_files/model2simpler_interface.py examples/Robocasa_tabletop/eval_files/model2robocasa_interface.py`，比较两个接口如何拆分动作。
2. 在安装好 RoboCasa 环境并启动 policy server 后，把 RoboCasa 命令中的 episode 数设为 1 做最小测试。成功输出应包含一个 episode 的日志或视频。
3. 运行 `rg -n "ckpt|server_policy|port" examples/SimplerEnv/eval_files/run_policy_server.sh examples/SimplerEnv/eval_files/start_simpler_env.sh`，写出 SimplerEnv checkpoint 启动 server 的命令依据。

## 导航

- 上一节：[01 benchmark 目录模式](01-benchmark-pattern.md)
- 返回上级：[其他 Benchmark](../08-other-benchmarks.md)
- 下一节：[03 RoboTwin 与 BEHAVIOR](03-robotwin-and-behavior.md)
