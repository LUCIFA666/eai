# 训练库对接

RSL-RL、RL-Games、SKRL、SB3 是训练库，不是四种强化学习算法。PPO、SAC、TD3、A2C、AMP 才是算法或算法家族。Isaac Lab 的职责是定义机器人任务：场景、观测、动作、奖励、终止和 reset；训练库的职责是采样轨迹、估计优势、更新策略、记录日志和保存 checkpoint。

## 本节目标

本节围绕下面几个问题展开：

1. 「训练库」和「算法」是两回事吗？Isaac Lab 对接了哪四个库（RSL-RL / RL-Games / SKRL / SB3）？
2. 这四个库怎么选，它们在 `train.py` 里的入口和 VecEnv wrapper 有什么共性？
3. 切换训练库时，机器人任务需要重写吗，checkpoint 怎么复用？

因此，切换训练库时，通常不需要重写机器人任务。真正变化的是 agent 配置入口、VecEnv wrapper 和 runner / trainer。

```text
task id
  -> gym.register 找到 env_cfg 和 agent_cfg
  -> train.py 解析命令行与 Hydra 配置
  -> gym.make 创建 Isaac Lab 环境
  -> VecEnv wrapper 转成训练库接口
  -> runner / trainer 执行 rollout 与 policy update
  -> logs / checkpoints / videos
  -> play.py 加载 checkpoint 回放策略
```

## 先分清库和算法

训练库像是“训练工作台”。它规定配置文件怎么写、并行环境怎么接、日志怎么打、checkpoint 怎么保存。算法是工作台里真正用来更新策略的方法。

| 名称 | 层级 | 例子 |
|---|---|---|
| 训练库 | 负责训练流程和工程接口 | RSL-RL、RL-Games、SKRL、SB3 |
| 算法 | 负责如何更新策略 | PPO、SAC、TD3、A2C |
| 任务 | 负责机器人交互闭环 | `Isaac-Reach-Franka-v0`、`Isaac-Cartpole-v0` |
| 配置入口 | 连接任务和训练库 | `rsl_rl_cfg_entry_point`、`skrl_cfg_entry_point` |

同一个任务可以给不同训练库使用。比如一个机械臂 reaching 任务，环境配置仍然描述机械臂、目标点、观测项、动作尺度、奖励和终止条件；切到另一个训练库时，变化的是训练超参、wrapper 和日志格式。

## 共同代码地图

四个训练库在 Isaac Lab 中的入口形态高度相似：

| 层级 | RSL-RL | RL-Games | SKRL | SB3 |
|---|---|---|---|---|
| 训练入口 | `scripts/reinforcement_learning/rsl_rl/train.py` | `scripts/reinforcement_learning/rl_games/train.py` | `scripts/reinforcement_learning/skrl/train.py` | `scripts/reinforcement_learning/sb3/train.py` |
| 回放入口 | `scripts/reinforcement_learning/rsl_rl/play.py` | `scripts/reinforcement_learning/rl_games/play.py` | `scripts/reinforcement_learning/skrl/play.py` | `scripts/reinforcement_learning/sb3/play.py` |
| 配置入口键 | `rsl_rl_cfg_entry_point` | `rl_games_cfg_entry_point` | `skrl_cfg_entry_point` | `sb3_cfg_entry_point` |
| wrapper | `RslRlVecEnvWrapper` | `RlGamesVecEnvWrapper` | `SkrlVecEnvWrapper` | `Sb3VecEnvWrapper` |
| 常见配置形态 | Python cfg class | YAML / dict | YAML / dict | YAML / dict |

任务注册通常写在 `source/isaaclab_tasks/isaaclab_tasks/.../__init__.py`。一个任务可以同时挂多套 agent 配置：

```python
gym.register(
    id="Isaac-Lift-Cube-Franka-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": "...:FrankaCubeLiftEnvCfg",
        "rsl_rl_cfg_entry_point": "...rsl_rl_ppo_cfg:LiftCubePPORunnerCfg",
        "rl_games_cfg_entry_point": "...:rl_games_ppo_cfg.yaml",
        "skrl_cfg_entry_point": "...:skrl_ppo_cfg.yaml",
        "sb3_cfg_entry_point": "...:sb3_ppo_cfg.yaml",
    },
)
```

这段注册关系说明：`env_cfg_entry_point` 决定机器人任务本身，几个 `*_cfg_entry_point` 决定不同训练库如何训练这个任务。

## 四个库怎么选

| 库 | 课程定位 | 适合场景 | 注意点 |
|---|---|---|---|
| RSL-RL | 默认主线 | Isaac Lab 常见机器人 PPO 训练、策略蒸馏、多 GPU 训练 | 配置多为 Python cfg class，适合顺着源码读 |
| RL-Games | 高吞吐传统 | Isaac Gym 传统任务、大规模并行 PPO、AMP 相关经验迁移 | 配置层级偏 YAML / dict，需区分 task id 和库内部环境名 |
| SKRL | 多算法入口 | 想比较 PPO、SAC、TD3 等算法，或尝试 Torch / JAX | 算法选择更灵活，配置项也更多 |
| SB3 | Gymnasium 风格实验 | 熟悉 Stable-Baselines3 API 的小规模教学和对比实验 | 社区资料多，但不适合作为大规模 GPU 并行训练主线 |

课程主线优先使用 RSL-RL。它在 Isaac Lab 机器人任务中出现频率高，训练、回放、日志和 checkpoint 路径也比较适合教学。其他三个库用于说明：同一个 MDP 可以交给不同训练工作台处理。

## RSL-RL

RSL-RL 常用于 Isaac Lab 的机器人 PPO 训练。它的优点是入口清晰、和任务配置结合紧密、日志字段适合观察机器人训练过程。读 RSL-RL 训练代码时，优先看三处：

1. `--task` 选择哪个 Isaac Lab 任务。
2. `rsl_rl_cfg_entry_point` 加载哪套 runner 配置。
3. `RslRlVecEnvWrapper` 如何把 Isaac Lab 环境转成 RSL-RL 能读取的向量化环境。

典型训练和回放命令如下：

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
  --task Isaac-Reach-Franka-v0 --headless

./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
  --task Isaac-Reach-Franka-v0 --num_envs 32 \
  --load_run <run_folder_name> --checkpoint <model.pt>
```

如果刚开始学习 Isaac Lab 强化学习，优先把 RSL-RL 跑通，再去比较其他训练库。

## RL-Games

RL-Games 延续了 Isaac Gym 时代的高吞吐训练经验，常见于大规模并行 PPO、类人或四足运动控制、AMP 等场景。它和 RSL-RL 一样适合 GPU 并行环境，但配置形态更偏 YAML / dict。

读 RL-Games 时要抓住两件事：第一，Isaac Lab 的任务仍然由 `task id` 决定；第二，RL-Games 内部还有自己的 runner 和环境注册习惯。若报错出现在 batch、minibatch、horizon、network input 这些字段，通常要回到 RL-Games 配置里检查，而不是只改 Isaac Lab 任务文件。

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rl_games/train.py \
  --task Isaac-Ant-v0 --headless

./isaaclab.sh -p scripts/reinforcement_learning/rl_games/play.py \
  --task Isaac-Ant-v0 --num_envs 32 --checkpoint <model.pth>
```

## SKRL

SKRL 的优势是算法覆盖面更宽，并支持 PyTorch 和 JAX 两类后端。它适合做算法对比：同一个 Isaac Lab 任务，换不同 agent 配置，观察 PPO、SAC、TD3 等方法在采样效率、稳定性和动作平滑度上的差异。

对初学者来说，SKRL 的重点不是“先学更多算法”，而是理解 Isaac Lab 的任务定义和训练库之间有一层明确边界：任务输出 observation、reward、done、extras；SKRL wrapper 把这些张量整理成 SKRL trainer 期待的格式。

```bash
./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
  --task Isaac-Cartpole-v0 --headless

./isaaclab.sh -p scripts/reinforcement_learning/skrl/play.py \
  --task Isaac-Cartpole-v0 --num_envs 32 --checkpoint <agent.pt>
```

## SB3

SB3 指 Stable-Baselines3。它的优点是 API 经典、教程资料多，适合把外部 Gymnasium 生态里的经验迁移到 Isaac Lab 小任务上。它更适合教学对照和小规模实验，不是本课程的大规模机器人训练主线。

使用 SB3 时，常见关注点是 VecNormalize、日志间隔、checkpoint 文件名和环境包装方式。若短时间训练看不到日志，不一定是任务没有学习，也可能只是日志输出间隔过大。

```bash
./isaaclab.sh -p scripts/reinforcement_learning/sb3/train.py \
  --task Isaac-Cartpole-v0 --headless

./isaaclab.sh -p scripts/reinforcement_learning/sb3/play.py \
  --task Isaac-Cartpole-v0 --num_envs 32 --checkpoint <model.zip>
```

## 读 train.py 的四个入口

第一，看命令行覆盖。`--task` 决定任务，`--num_envs` 覆盖并行环境数量，`--seed` 控制随机种子，`--max_iterations` 或同类字段控制训练长度。不同训练库还会有各自的 resume、load、checkpoint、run name 规则。

第二，看 agent 配置入口。`@hydra_task_config(args_cli.task, args_cli.agent)` 会根据任务注册信息加载对应训练库的配置。若任务没有注册某个训练库的 entry point，命令会在配置加载阶段失败。

第三，看 wrapper。wrapper 是 Isaac Lab env 和训练库之间的接口转换层。训练中很多 shape 对不上、obs group 不一致、info 字段缺失的问题，都要从 wrapper 和 env 输出结构一起查。

第四，看 runner / trainer。训练库不同，checkpoint 文件名、日志目录、TensorBoard 字段、视频目录和恢复方式都会不同。回放失败时，优先核对 `task id`、agent 配置、checkpoint 路径、normalizer 和训练时的 observation / action 结构是否一致。

## 常见排错入口

| 现象 | 优先检查 |
|---|---|
| 任务能创建，但训练库报 shape 错误 | observation group、wrapper、agent 配置里的网络输入维度 |
| reward 一直不上升 | reward term、termination、action scale、control decimation、policy std |
| episode 很快结束 | termination 条件、reset 逻辑、初始状态随机化 |
| `play.py` 加载后行为异常 | checkpoint、task id、agent cfg、normalizer 是否和训练时一致 |
| checkpoint 找不到 | 对应训练库的日志目录规则和文件名 |
| 多 GPU 或跨机器启动失败 | `--distributed`、rank、master 地址、每个节点进程数 |

## 和强化学习基础的关系

本节只解决 Isaac Lab 里“代码怎么接、配置怎么找、训练怎么跑、出错怎么查”。PPO、return、value、advantage、GAE、actor-critic 的原理不在本单元展开，放到 [第 9 章 面向机器人的强化学习](../../../09-reinforcement-learning-for-robotics/README.md)。读者可以先在这里把训练跑起来，再到那一章理解训练信号为什么这样设计。

## 四个库最小闭环

四类训练库的最小验收标准相同：环境能创建，训练能进入第一轮，日志能写出，checkpoint 能生成。RSL-RL、SKRL、SB3 可以优先用 CartPole 或 Reach 这类小任务；RL-Games 若改小 `--num_envs` 后触发 `batch_size % minibatch_size == 0` 断言失败，说明 batch / horizon / minibatch 配置没有随环境数一起调整，应回到 RL-Games 配置里改，而不是只改 Isaac Lab 的 task id。

下面只保留判断闭环是否走通的关键日志形态。具体 reward、fps 和耗时会随 GPU、环境数、渲染开关和训练步数变化，不应作为固定结果记忆。

```text
RSL-RL Reach:
[INFO]: Completed setting up the environment...
Learning iteration 0/1
Mean reward: ...

RL-Games Ant:
Started to train
fps step: ... fps total: ... epoch: ...
=> saving checkpoint '.../logs/rl_games/ant/<run_folder>/nn/...pth'

SKRL CartPole:
[skrl:INFO] Environment wrapper: Isaac Lab (single-agent)
Training time: ...

SB3 CartPole:
Using cuda:0 device
total_timesteps: ...
```

## 复用 checkpoint

不需要每次都重新长训。已有 checkpoint 后，分别用四个库的 `play.py` 验证能否加载策略并完成短回放。短验收推荐加 `--video --video_length 16`，这样 play loop 会在录完一小段视频后主动退出；不要加 `--video_interval`，当前这四个 `play.py` 入口都不接受这个参数。

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
  --task Isaac-Cartpole-v0 \
  --num_envs 16 \
  --headless \
  --video \
  --video_length 16 \
  --checkpoint logs/rsl_rl/cartpole/<run_folder>/model_1.pt \
  --device cuda:0

./isaaclab.sh -p scripts/reinforcement_learning/rl_games/play.py \
  --task Isaac-Cartpole-v0 \
  --num_envs 16 \
  --headless \
  --video \
  --video_length 16 \
  --checkpoint logs/rl_games/cartpole/<run_folder>/nn/cartpole.pth \
  --device cuda:0

./isaaclab.sh -p scripts/reinforcement_learning/skrl/play.py \
  --task Isaac-Cartpole-v0 \
  --num_envs 16 \
  --headless \
  --video \
  --video_length 16 \
  --checkpoint logs/skrl/cartpole/<run_folder>_ppo_torch/checkpoints/agent_16.pt \
  --device cuda:0

./isaaclab.sh -p scripts/reinforcement_learning/sb3/play.py \
  --task Isaac-Cartpole-v0 \
  --num_envs 16 \
  --headless \
  --video \
  --video_length 16 \
  --checkpoint logs/sb3/Isaac-Cartpole-v0/<run_folder>/model.zip \
  --device cuda:0
```

回放日志里至少要看到这些关键信号：

```text
RSL-RL:
[INFO]: Completed setting up the environment...
[INFO]: Loading model checkpoint from: .../logs/rsl_rl/cartpole/<run_folder>/model_1.pt
EXIT_CODE: 0

RL-Games:
[INFO]: Completed setting up the environment...
[INFO]: Loading model checkpoint from: .../logs/rl_games/cartpole/<run_folder>/nn/cartpole.pth
EXIT_CODE: 0

SKRL:
[INFO]: Completed setting up the environment...
[INFO] Loading model checkpoint from: .../logs/skrl/cartpole/<run_folder>_ppo_torch/checkpoints/agent_16.pt
EXIT_CODE: 0

SB3:
[INFO]: Completed setting up the environment...
Loading checkpoint from: .../logs/sb3/Isaac-Cartpole-v0/<run_folder>/model.zip
EXIT_CODE: 0
```

常见排错经验：

- RSL-RL Reach 如果把 `--checkpoint model_0.pt` 当成相对路径传入，会报 `FileNotFoundError: Unable to find the file: model_0.pt`。要传绝对路径，或确认当前工作目录和脚本的路径解析规则。
- 不带 `--video` 的 play 通常是无限回放。若用超时工具强行截断，程序可能停在 checkpoint 加载前；RSL-RL 和 SB3 在强制截断时还可能出现 IsaacSim 的 `carb.tasking.Mutex` 断言。因此短验证推荐使用 `--video --video_length 16`，让脚本自然退出。
- `--video_interval` 不是这些 play 脚本的参数，会报 `play.py: error: unrecognized arguments: --video_interval`。

复现实验时可以保存完整 stdout、stderr、checkpoint 路径和视频文件；正文只保留通用验收信号与失败模式。

## 参考资料

- Isaac Lab Documentation: Reinforcement Learning Scripts. https://isaac-sim.github.io/IsaacLab/main/source/overview/reinforcement-learning/rl_existing_scripts.html
- Isaac Lab Documentation: Reinforcement Learning Library Comparison. https://isaac-sim.github.io/IsaacLab/main/source/overview/reinforcement-learning/rl_frameworks.html
- RSL-RL. https://github.com/leggedrobotics/rsl_rl
- RL-Games. https://github.com/Denys88/rl_games
- SKRL. https://skrl.readthedocs.io/
- Stable-Baselines3. https://stable-baselines3.readthedocs.io/

## 导航

- 上一页：[配置系统与 CLI](02-config-and-cli.md)
- 返回目录：[训练与评测](../05-training.md)
- 下一页：[模仿学习与官方示例](04-imitation-learning.md)
