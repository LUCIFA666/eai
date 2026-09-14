# 基线与记忆瓶颈证据

MIKASA-Robo-VLA 随仓提供的 RL 基线在一个维度上正好构成对照：是否携带记忆。无记忆的 PPO 只看当前观测，循环的 PPO-LSTM 在观测之上维护隐藏状态。因此把这两者放到同一批任务上评估，本身就是对记忆作用的直接探针，而这也正是记忆是否为瓶颈的证据来源。

## 仓库提供的基线

`baselines/ppo/` 提供两个 RL 基线：`ppo_memtasks.py` 是无记忆的 PPO，`ppo_memtasks_lstm.py` 是带循环记忆的 PPO-LSTM。

两者的观测编码共用一个 `NatureCNN`。它对 `rgb` 走三层卷积（通道 32 的 8×8 步长 4、通道 64 的 4×4 步长 2、通道 64 的 3×3 步长 1，各接 ReLU），展平后线性映射到 256 维；其余观测分支各走一层线性加 ReLU：`proprio` 到 128、`state` 到 256、`oracle_info` 与 `task_cue` 到 64；所有分支的输出拼成一个特征向量。

```python
# ppo_memtasks.py：NatureCNN 的 RGB 卷积主干
nn.Conv2d(in_channels, 32, kernel_size=8, stride=4, padding=0), nn.ReLU(),
nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=0), nn.ReLU(),
nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=0), nn.ReLU(),
nn.Flatten(),
# → nn.Linear(n_flatten, 256), nn.ReLU()
```

无记忆的 PPO 里，这个特征直接送进 actor 与 critic 两个头。动作头输出连续高斯分布：`actor_mean` 把特征经 512 维隐层映射到动作维度，配一个可学习的 `actor_logstd`，采样时用 `Normal(action_mean, exp(logstd))`；`critic` 经 512 维隐层输出标量价值。

```python
# ppo_memtasks.py：连续高斯动作头
action_mean = self.actor_mean(x)
action_std = torch.exp(self.actor_logstd.expand_as(action_mean))
probs = Normal(action_mean, action_std)   # 采样得到动作
```

PPO-LSTM 在特征与两个头之间插入循环层：`nn.LSTM(latent_size, 512, num_layers=1)`，actor 与 critic 都从 512 维的 LSTM 隐藏态出发。隐藏态在 episode 边界按 `1-done` 掩码清零，让记忆不跨 episode 泄漏；`state` 观测模式在 LSTM 版被显式禁用，避免用特权状态绕过图像记忆。

```python
# ppo_memtasks_lstm.py：episode 边界重置隐藏态
h_ = (1.0 - d).view(1, -1, 1) * lstm_state[0]
c_ = (1.0 - d).view(1, -1, 1) * lstm_state[1]
```

两者的关键超参一致：`total_timesteps=5e7`、`num_envs=1024`、`num_steps=90`、`learning_rate=3e-4`、`num_minibatches=32`、`update_epochs=4`、`gamma=0.99`、`gae_lambda=0.95`。

基线还带一个 `include_oracle` 开关（默认关闭）。打开后含正确答案的 `oracle_info`（例如 ShellGame 里球所在的杯子编号）被喂进网络，任务就退化成马尔可夫的 MDP。它不是用来刷分，而是作为可解性对照：确认任务在有答案时可解，从而把失败归因到记忆缺失、而非任务本身太难或控制不了。

有一点控制模式要分清：这两个 RL 基线跑的是经典的 `*-v0` 环境、控制模式 `pd_joint_delta_pos`；而数据集采集器复用其中纯 state 的 oracle 网络 `AgentStateOnly`，在 `*-VLA-v0` 环境上以 `pd_ee_delta_pose` 采集轨迹。训练用的控制模式和采集用的控制模式并不相同。

## 记忆是完成任务的必要条件

VLA 版尚未发布 90 任务的结果表，下面的定量证据来自任务系列一致的 32 任务 RL 原版，用同样的无记忆与有记忆基线评估，可以说明同一批任务上记忆的作用。

在线 RL 对比 PPO-MLP 与 PPO-LSTM。先用上面的可解性对照做检查：PPO-MLP 在 `state` 模式加 dense 奖励下，32 个任务全部达到 100% 成功率，说明任务本身可解。换成 RGB+joints、dense 奖励后，RememberColor 3 色时 PPO-MLP 只有 25%、PPO-LSTM 达 100%；到 5 色、9 色两者都掉到接近 0。改成 sparse 奖励，即便 3 色两者也几乎都失败。一旦线索不在当前观测里、且难度上升，无记忆的 MLP 迅速失效，带记忆的 LSTM 也只在最简单的档位撑住。

离线 RL 对比五个基线：RATE 和 DT（带记忆的 transformer）、BC 和 CQL（MLP）、DP（Diffusion Policy），都在 RGB、sparse、每任务 1000 条 oracle 成功轨迹上训练。

| 任务 | RATE | DT | BC | CQL | DP |
|---|---|---|---|---|---|
| ShellGameTouch | 0.92 | 0.53 | 0.28 | 0.16 | 0.18 |
| RememberColor3 | 0.65 | — | — | — | — |
| RememberColor9 | 0.09 | — | — | — | — |
| 全部 Capacity 与 Sequential 任务 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

RATE 在最简单的 ShellGameTouch 上能到 0.92，但 RememberColor 从 3 色到 9 色掉到 0.09；BunchOfColors、SeqOfColors、ChainOfColors 这些容量类和顺序类任务上，五个模型全是 0.00，没有一个能解。

VLA 模型评测了 Octo、OpenVLA、π0、SpatialVLA。ShellGameTouch 上 Octo 0.46、OpenVLA（K=8）0.47、π0（K=4）0.33；RememberColor 从 3 色到 9 色同样急剧衰减，例如 OpenVLA（K=8）从 0.59 掉到 0.06。较大的动作分块 K=8 会靠早期线索一次生成整段轨迹来抄近路，而 K=4 就退化成接近随机，说明这些 VLA 缺乏在长时间跨度上保留任务相关信息的能力。

评估这三组基线得到的结论一致：无记忆或弱记忆的策略在中高难度任务上失败，容量类和顺序类任务尤其难；在任务本身已被证明可解的前提下，记忆是完成这些任务的必要条件。

## 导航

- 返回上级：[MIKASA-Robo-VLA](../01-mikasa.md)
- 上一节：[数据集](08-datasets.md)
