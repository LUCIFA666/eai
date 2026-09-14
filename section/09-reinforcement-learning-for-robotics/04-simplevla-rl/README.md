# 导读与运行准备

这一组小节按真实代码路径拆解 `SimpleVLA-RL`。它和 RLINF 的定位不同：RLINF 是通用大规模 RL 基础设施，SimpleVLA-RL 是围绕 OpenVLA/OpenVLA-OFT、LIBERO、RoboTwin 的 VLA RL 改造版 veRL 流程。

SimpleVLA-RL的主线是：

`SFT checkpoint -> RayTrainer -> rollout 环境交互 -> complete/finish_step -> token reward -> GRPO advantage -> PPO clipped update`

## 小节

- [架构与算法](01-architecture-and-algorithms.md)：整体架构、GRPO/PPO 要点和与 veRL 的关系。
- [环境搭建与快速上手](02-setup-quickstart.md)：硬件需求、显存估算、依赖安装和基准环境跑通。
- [配置与数据](03-config-data.md)：训练配置体系、`LIBERO_Dataset`、`Robotwin_Dataset`、`task_id/trial_id/seed`，以及为什么不是普通的 `(image, action)`。
- [模型代码流程](04-model-code-flow.md)：集中介绍 Trainer、Rollout、Actor 三个核心模块如何串成 SimpleVLA-RL 的训练闭环。
- [Trainer 与 Reward](04-model-code-flow/01-trainer-reward.md)：`main_ppo.py`、`RobRewardManager`、`RayTrainer.fit()`，以及训练主循环如何组织 rollout、reward、advantage 和 update。
- [Rollout 与环境交互](04-model-code-flow/02-rollout-env.md)：LIBERO/RoboTwin 环境、Observation、VLA 输入、action 生成和 trajectory 收集。
- [Actor 与策略优化](04-model-code-flow/03-actor-policy.md)：FSDP worker、OpenVLA/OpenVLA-OFT、old logprob、PPO loss 和 checkpoint 保存。
- [Rollout 交互细节](05-rollout-interaction.md)、[训练优化](06-training-optimization.md)、[SFT 冷启动与 RL 训练](07-sft-rl-training.md)、[OpenArm 端到端实战](08-openarm-practice.md)、[故障排查与索引](09-troubleshooting-index.md)。


## 本地目录结构

推荐把 SimpleVLA-RL 相关代码、依赖仓库、模型和 checkpoint 都放到同一个工作目录下面。文档中用 `SIMPLEVLA_ROOT` 表示这个目录，实际路径由使用者自己决定。下面示例是将这个项目都放在`simplevla-rl_stack`目录下面：

```text
simplevla-rl_stack/
├── SimpleVLA-RL/
├── openvla-oft/
├── LIBERO/
├── verl/
├── Embodied_models/
│   └── openvla-oft-sft-libero10-trajall/
├── checkpoints/
└── libero_config/
```

先创建并进入根目录：

```bash
mkdir -p simplevla-rl_stack
cd simplevla-rl_stack
export SIMPLEVLA_ROOT="$(pwd)"
```

创建 checkpoint 目录：

```bash
mkdir -p "$SIMPLEVLA_ROOT/checkpoints"
```

`checkpoints/` 用来保存 RL 训练过程中产生的模型快照和训练状态。脚本里的 `CKPT_PATH="$SIMPLEVLA_ROOT/checkpoints"` 会把它作为 checkpoint 根目录，实际运行时通常会进一步按项目名和实验名组织，例如 `checkpoints/SimpleVLA-RL/libero10_trajall_rl_local/`。这里面会保存中间 step 的 actor/VLA 权重、配置和可能的训练状态，作用是，训练中断后可以从 checkpoint 恢复，训练结束后也可以选取某个 checkpoint 做评估或继续微调。


## 下载项目代码

首先下载 SimpleVLA-RL 主仓库：

```bash
cd "$SIMPLEVLA_ROOT"
[ ! -d SimpleVLA-RL ] && git clone https://github.com/PRIME-RL/SimpleVLA-RL.git
```


下载 OpenVLA-OFT、LIBERO 和 veRL：

```bash
cd "$SIMPLEVLA_ROOT"
[ ! -d openvla-oft ] && git clone https://github.com/moojink/openvla-oft.git
[ ! -d LIBERO ] && git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git
[ ! -d verl ] && git clone -b v0.2.x --depth 1 https://github.com/volcengine/verl.git
```

后面下载具体VLA模型和安装依赖，以及实操运行训练脚本等操作会在[SimpleVLA-RL 实战](hands-on/01-simplevla-rl.md)中继续给出。上面先下载SimpleVLA-RL 主仓库是方便在阅读接下来的小节可以对照着具体代码来理解。
