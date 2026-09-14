# 配置系统与 CLI

Isaac Lab 的训练不是手写一个固定脚本，而是由注册入口、配置树和命令行覆盖共同驱动。理解这一层，才能在不改源码的情况下调整环境数、奖励权重、动作尺度、学习率和训练迭代数。

## 本节目标

本节围绕下面几个问题展开：

1. task id 怎么找到 env cfg 和各 RL 库的 agent cfg？
2. Hydra 命令行覆盖怎么用（`env.*` / `agent.*`、增删改）？
3. 各 RL 库的 VecEnv wrapper 是干什么的，为什么通常最后包？
4. 续训、录像、归一化、特权 critic 这些训练层机制怎么用？

## 一个任务注册多个入口点

任务通常通过 `gym.register` 注册：

```python
import gymnasium as gym
from . import agents

gym.register(
    id="Isaac-Reach-Franka-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.joint_pos_env_cfg:FrankaReachEnvCfg",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:FrankaReachPPORunnerCfg",
        "skrl_cfg_entry_point": f"{agents.__name__}:skrl_ppo_cfg.yaml",
    },
)
```

这里分成两类配置：

| 配置 | 负责什么 |
|---|---|
| `env_cfg_entry_point` | scene、observation、action、reward、termination、event |
| `<lib>_cfg_entry_point` | PPO / SAC 等算法参数、网络结构、runner 设置 |

换 RL 库，本质上是换读取哪个 agent 配置入口。

## Hydra 覆盖

训练脚本会把 env cfg 和 agent cfg 合成配置树。命令行可以覆盖其中任意字段：

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-Reach-Franka-v0 \
    --headless \
    env.scene.num_envs=2048 \
    env.rewards.action_rate.weight=-0.02 \
    agent.max_iterations=1000 \
    agent.algorithm.learning_rate=5.0e-4
```

常见规则：

| 写法 | 含义 |
|---|---|
| `key=value` | 修改已有值 |
| `key=null` | 置空 |
| `+key=value` | 新增字段 |
| `~key` | 删除字段 |

环境配置通常走 `env.*`，算法配置通常走 `agent.*`。

## 传统 CLI 的优先级

有些参数是训练脚本直接解析的，优先级通常高于 Hydra 覆盖：

| 参数 | 作用 |
|---|---|
| `--num_envs` | 覆盖环境数 |
| `--seed` | 覆盖随机种子 |
| `--max_iterations` | 覆盖训练迭代数 |
| `--device` | 覆盖训练 / 仿真设备 |

例如下面两种写法都能改环境数：

```bash
--num_envs 4096
env.scene.num_envs=4096
```

写教材和实验记录时，建议优先使用脚本显式支持的 CLI；需要改深层配置时再用 Hydra 路径。

## VecEnv wrapper

`gym.make` 创建的是 Isaac Lab 环境，不同 RL 库还需要各自 wrapper 转接接口：

| 库 | Wrapper |
|---|---|
| RSL-RL | `RslRlVecEnvWrapper` |
| RL-Games | `RlGamesVecEnvWrapper` |
| SKRL | `SkrlVecEnvWrapper` |
| SB3 | `Sb3VecEnvWrapper` |

典型结构：

```python
env = gym.make(args_cli.task, cfg=env_cfg)

if args_cli.video:
    env = gym.wrappers.RecordVideo(env, video_folder=video_dir)

env = RslRlVecEnvWrapper(env)
runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
runner.learn(num_learning_iterations=agent_cfg.max_iterations)
```

库专用 wrapper 通常要最后包。因为它会把 Isaac Lab 环境接口转换成对应 RL 库需要的 VecEnv 语义。

## train.py 常用参数

| 参数 | 含义 |
|---|---|
| `--task` | 任务 ID |
| `--num_envs` | 并行环境数 |
| `--seed` | 随机种子 |
| `--max_iterations` | 训练迭代数 |
| `--headless` | 无 GUI 训练 |
| `--device` | `cuda:0` / `cpu` |
| `--video` | 训练时录视频 |
| `--video_length` | 每段视频步数 |
| `--video_interval` | 间隔多少步录一次 |
| `--enable_cameras` | 无头模式下启用相机 / 录像 |
| `--logger` | tensorboard / wandb / neptune |
| `--resume` | 续训 |
| `--load_run` | 指定 run 目录 |
| `--checkpoint` | 指定 checkpoint |

## play.py 常用参数

| 参数 | 含义 |
|---|---|
| `--task` | 任务 ID |
| `--num_envs` | 回放环境数 |
| `--checkpoint` | 权重路径 |
| `--use_pretrained_checkpoint` | 在支持该参数的 play 脚本中使用预训练权重 |
| `--video` | 录制回放 |
| `--real-time` | 尽量按真实时间回放 |

`play.py` 不只是展示效果，也是检查训练是否“真的学对了”的工具。

## 归一化和特权 critic

训练时可能启用观测归一化。归一化器必须和策略一起保存和导出，否则部署时输入分布会错。

另一种常见技巧是非对称 actor-critic：

```text
actor / policy：只看真机可获得观测
critic：训练时额外看仿真内部特权信息
```

这通常通过观测组实现：

```python
@configclass
class ObservationsCfg:
    policy: PolicyCfg = PolicyCfg()
    critic: CriticCfg = CriticCfg()
```

actor 最终会被导出部署；critic 只服务训练。

## CLI 覆盖检查

CLI override 的验收重点不是“命令能启动”，而是确认覆盖项真的进入了环境和 agent 配置。可以用一个很短的训练 run 覆盖并行环境数、训练轮数、reward 权重和学习率：

```text
--num_envs 64 --max_iterations 1 env.rewards.action_rate.weight=-0.02 agent.algorithm.learning_rate=5.0e-4
```

预期输出应包含环境、action、observation、reward manager 的初始化信息，并进入第 0 轮训练：

```text
[INFO] Logging experiment in directory: .../logs/rsl_rl/franka_reach
[INFO] Action Manager:  <ActionManager> contains 1 active terms.
[INFO] Observation Manager: <ObservationManager> contains 1 groups.
[INFO] Reward Manager:  <RewardManager> contains 5 active terms.
[INFO]: Completed setting up the environment...
Learning iteration 0/1
Mean reward: -0.27
Mean episode length: 14.00
Training time: 1.73 seconds
```

如果输出仍显示默认环境数或 reward 项没有变化，优先检查 override 路径是否写错，例如 `env.rewards.<term>.weight` 和 `agent.algorithm.learning_rate` 是否存在于当前任务/训练库配置中。

## 小结

- task id 通过 `gym.register` 找到 env cfg 和各 RL 库 agent cfg。
- Hydra 覆盖让实验参数可在命令行修改。
- RL 库 wrapper 是环境和算法之间的转接层，通常最后包。
- 续训、录像、回放、归一化和特权 critic 都属于训练脚本层面的关键机制。

## 导航

- 上一页：[启动训练并读懂训练曲线](01-train-and-read-curves.md)
- 返回目录：[训练与评测](../05-training.md)
- 下一页：[训练库对接](03-rl-libraries.md)
