# 第一次训练

讲再多概念，不如先跑一个看看。本页用 Isaac Lab 自带的 CartPole（小车倒立摆）任务，让你获得第一次完整体验：启动训练、看 reward 变好、保存 checkpoint、回放策略。下一页再解释你在这里看到的并行、配置和 MDP 闭环。

## 本节目标

本节围绕下面几个问题展开：

1. 第一次运行要跑通哪条最小闭环？
2. 启动脚本、环境初始化和主循环的顺序为什么重要？
3. 日志、画面、checkpoint 或输出文件应该怎么看？
4. 如果第一次运行失败，应该先排查哪几个最常见原因？

## 确认你在 Isaac Lab 根目录

下面命令假设你已经安装好 Isaac Lab，并且当前目录是 Isaac Lab 仓库根目录。如果还没有安装，可以先跳到本部分最后的 [安装与版本对照](04-install-and-versions.md)。

```bash
cd IsaacLab
./isaaclab.sh -p --version
```

如果 Python 能启动，说明 wrapper 脚本至少能找到 Isaac Lab 环境。课程里后续命令统一使用 `./isaaclab.sh` 写法。

## 一行命令开始训练

CartPole 是最适合首跑的任务：没有复杂机器人资产，没有相机渲染，不依赖长时间训练。用 RSL-RL 训练它：

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
    --task=Isaac-Cartpole-v0 \
    --headless
```

这行命令里先只记住三个点：

| 参数 | 含义 |
|---|---|
| `-p` | 让 Isaac Lab 用自己的 Python 环境执行脚本 |
| `--task=Isaac-Cartpole-v0` | 选择已经注册好的 CartPole 任务 |
| `--headless` | 不打开图形窗口，训练更快、更稳定 |

第一次跑时，你不需要先理解 CartPole 的全部配置文件。先让它动起来，建立“一个任务能被训练脚本识别并跑出曲线”的直觉。

## 读懂训练日志

运行后，控制台会滚动类似下面的日志。具体数字会随 GPU、版本和随机种子变化，重点看趋势：

下面贴出一次运行（4096 个并行环境、150 次迭代）的文本日志，可逐行对照自己的输出。`Mean reward`、`Mean episode length`、`Mean action noise std` 的变化趋势更值得看；`Computation`（steps/s）、`Training time` 这类吞吐数字会随 GPU 型号和当时负载变化。

第 0 轮（训练刚开始，杆子几乎立刻倒下）：

```text
################################################################################
                       Learning iteration 0/150

                       Computation: 147362 steps/s (collection: 0.269s, learning 0.176s)
             Mean action noise std: 1.00
          Mean value_function loss: 0.0256
               Mean surrogate loss: -0.0304
                 Mean entropy loss: 1.4178
                       Mean reward: 0.13
               Mean episode length: 12.78
           Episode_Reward/pole_pos: -0.0092
              Episode_Reward/alive: 0.0283
      Episode_Termination/time_out: 0.0267
Episode_Termination/cart_out_of_bounds: 0.0000
        Episode_Reward/terminating: 0.0000
           Episode_Reward/cart_vel: -0.0004
           Episode_Reward/pole_vel: -0.0003
--------------------------------------------------------------------------------
                   Total timesteps: 65536
                    Iteration time: 0.44s
                      Time elapsed: 00:00:00
                               ETA: 00:01:06
```

第 149 轮（训练收尾，杆子已能稳定站满整个回合）：

```text
################################################################################
                      Learning iteration 149/150

                       Computation: 381079 steps/s (collection: 0.116s, learning 0.056s)
             Mean action noise std: 0.07
          Mean value_function loss: 0.0000
               Mean surrogate loss: 0.0024
                 Mean entropy loss: -1.2377
                       Mean reward: 4.95
               Mean episode length: 300.00
           Episode_Reward/pole_pos: -0.0055
              Episode_Reward/alive: 1.0000
      Episode_Termination/time_out: 1.0000
Episode_Termination/cart_out_of_bounds: 0.0000
        Episode_Reward/terminating: 0.0000
           Episode_Reward/cart_vel: -0.0029
           Episode_Reward/pole_vel: -0.0012
--------------------------------------------------------------------------------
                   Total timesteps: 9830400
                    Iteration time: 0.17s
                      Time elapsed: 00:00:27
                               ETA: 00:00:00

Training time: 28.16 seconds
```

先按上面两段日志里的示例数值看几类信号：

| 日志字段 | iteration 0/150 | iteration 149/150 | 怎么理解 |
|---|---:|---:|---|
| `Total timesteps` | 65,536 | 9,830,400 | 训练已经从第一批采样推进到接近千万步。 |
| `Computation` | 147,362 steps/s | 381,079 steps/s | 后期采样吞吐明显更高；首轮通常包含初始化、缓存和图形/环境准备开销。 |
| `Mean reward` | 0.13 | 4.95 | 平均奖励明显上升，说明策略已经学到让杆子更稳定的动作。 |
| `Mean episode length` | 12.78 | 300.00 | 回合长度从很短变成达到 300 步上限，CartPole 基本能撑到超时结束。 |
| `Mean action noise std` | 1.00 | 0.07 | 动作分布从很随机变得很确定，说明策略收敛到稳定控制。 |
| `Episode_Termination/time_out` | 0.0267 | 1.0000 | 开头很少撑到时间上限，结尾几乎全部因为超时结束，这是好信号。 |
| `Episode_Reward/alive` | 0.0283 | 1.0000 | 存活奖励从很低到满，和 episode length 变长互相印证。 |
| `Training time` | - | 28.16 seconds | 这个小任务用 GPU 并行训练，几十秒就能跑完一次示例训练。 |

对 CartPole 来说，如果 `Mean reward` 上涨、`Mean episode length` 变长，就说明策略正在学会让杆子立住。`steps/s` 很高，是因为 Isaac Lab 同时跑了大量并行环境。下一页会专门解释为什么这要求你用 `[num_envs, ...]` 的批量张量思维。

## 训练产物在哪里

CartPole 训练会在 `logs/rsl_rl/cartpole/` 下生成一个带时间戳的实验目录。一次 RSL-RL 训练的典型结构如下：

```text
logs/rsl_rl/cartpole/
└── 2026-06-03_09-36-27/
    ├── git/
    │   └── IsaacLab.diff
    ├── params/
    │   ├── agent.yaml
    │   └── env.yaml
    ├── events.out.tfevents.1780450590.localhost.1501997.0
    ├── model_0.pt
    ├── model_50.pt
    ├── model_100.pt
    └── model_149.pt
```

先按这几类理解：

| 产物 | 用途 |
|---|---|
| `params/agent.yaml` | 训练算法和 agent 配置，例如 PPO、网络、学习率、rollout 长度等。 |
| `params/env.yaml` | 任务环境配置，例如环境数量、仿真步长、奖励项、终止条件等。 |
| `git/IsaacLab.diff` | 训练时工作区相对 Git 的改动，用来记录实验对应的代码状态。 |
| `events.out.tfevents...` | TensorBoard 日志，用来画 reward、loss、episode length 等曲线。 |
| `model_0.pt` / `model_50.pt` / `model_100.pt` / `model_149.pt` | 不同迭代保存的策略 checkpoint，`model_149.pt` 通常对应 150 轮训练的末尾结果。 |

首轮训练后，建议先看时间戳目录是否生成，再确认 `params/`、TensorBoard events 和末尾 checkpoint 是否齐全。后续调参、复现实验、回放策略都会从这里开始。

## 回放看效果

训练完想看策略表现，用同一套任务的 `play.py`：

<video src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-task-cartpole.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

这段视频展示的是 CartPole 策略回放效果：小车通过左右移动，让杆子尽量保持竖直。你在训练日志里看到的 `Mean reward` 上涨，最终应该能在这种回放里变成可见的稳定控制。

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
    --task=Isaac-Cartpole-v0 \
    --num_envs=32
```

回放时通常不需要几千个环境。`--num_envs=32` 让画面更容易观察，也减轻显存压力。如果你想指定某个 checkpoint，训练脚本对应的回放脚本通常支持从日志目录读取结果；具体路径参数在训练库对接页面再展开。

## 首跑常见问题

| 现象 | 可能原因 | 处理方式 |
|---|---|---|
| 找不到 `Isaac-Cartpole-v0` | 没在 Isaac Lab 环境里执行，或任务扩展没安装 | 重新检查安装，并用 `isaaclab.sh -p` 执行 |
| 打开窗口后很慢 | GUI 渲染占资源 | 训练时加 `--headless`，回放时再开画面 |
| 显存不够 | 并行环境太多或窗口渲染占用高 | 降低 `--num_envs`，先跑通再调大 |
| reward 不涨 | 随机种子、训练步数或配置问题 | 先确认命令无误，再看 TensorBoard 曲线 |
| 把环境数写进 `gym.make` | 误解 Gymnasium 与 Isaac Lab 配置关系 | 用 `--num_envs` 或任务配置覆盖 |

## 小结

- 首跑目标不是调出最好成绩，而是跑通 `train -> logs -> checkpoint -> play` 的闭环。
- `Mean reward` 上涨和 `episode length` 变长，是判断 CartPole 是否在学的第一信号。
- `steps/s` 很高来自并行环境；这会引出下一页的 `[num_envs, ...]` 思维。
- 训练时优先 `--headless`，回放时再用较小 `--num_envs` 看画面。

## 参考资料

- Isaac Lab Documentation. https://isaac-sim.github.io/IsaacLab/
- RSL-RL. https://github.com/leggedrobotics/rsl_rl
- Gymnasium API. https://gymnasium.farama.org/

## 导航

- 上一页：[Isaac Lab 是什么](01-what-is-isaac-lab.md)
- 返回目录：[认识 Isaac Lab](../01-getting-started.md)
- 下一页：[三个理解视角](03-three-mental-models.md)
