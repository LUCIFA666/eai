# 启动训练并读懂训练曲线

训练的最小闭环不是“跑完命令”就结束，而是：

```text
train -> 看日志 / 曲线 -> 找 checkpoint -> play 回放 -> 判断行为是否符合任务定义
```

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-cartpole-real-training-curves.png" alt="CartPole 训练日志生成的训练曲线" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">CartPole 训练曲线来自一次完整的 Isaac-Cartpole-v0 运行：150 次 PPO 迭代、4096 个并行环境。平均奖励和回合长度快速上升，动作标准差逐步下降，采样吞吐稳定在较高水平。</figcaption>
</figure>

## 本节目标

本节围绕下面几个问题展开：

1. 一次完整训练闭环包含哪几步（train → 看曲线 → checkpoint → play）？
2. 训练日志和 TensorBoard 里重点看哪些字段和曲线？
3. 为什么“不要只看 reward”，episode length / action std 各说明什么？
4. checkpoint 在哪里，怎么回放和续训（`--resume`）？

## 启动训练

以 RSL-RL 为例，训练命令通常长这样：

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-Cartpole-v0 \
    --num_envs 4096 \
    --headless
```

常用参数：

| 参数 | 含义 |
|---|---|
| `--task` | 训练哪个注册任务 |
| `--num_envs` | 并行环境数 |
| `--headless` | 不打开 GUI，正式训练常用 |
| `--max_iterations` | 最大训练迭代数 |
| `--seed` | 随机种子 |
| `--video` | 训练中定期录视频 |
| `--enable_cameras` | 无头模式下启用相机 / 录像 |

## 日志里看什么

训练日志通常会周期性输出：

| 字段 | 读法 |
|---|---|
| learning iteration | PPO 更新迭代数，不是物理 step |
| total timesteps | 已采样总步数 |
| steps per second | 采样吞吐，受 `num_envs`、传感器和 GPU 影响 |
| mean reward | 平均回合奖励，趋势比单点更重要 |
| mean episode length | 平均回合长度，存活型任务越长通常越好 |
| value loss / surrogate loss | PPO 优化信号，异常发散时需关注 |
| mean action std | 策略探索噪声，过早接近 0 可能探索不足 |

不要只看 reward。比如 CartPole 中，episode length 增长到时间上限，比单个 reward 数值更直观。

## 一次训练的曲线长什么样

下面是课程记录的一次 `Isaac-Cartpole-v0` 训练（4096 环境、150 迭代）里，几个关键迭代点的日志数值。具体耗时和吞吐会随 GPU、驱动、渲染开关和系统负载变化，不应作为固定结果记忆：

| iteration | Mean reward | episode length | action std | 这一阶段发生了什么 |
|---:|---:|---:|---:|---|
| 0 | 0.13 | 12.78 | 1.00 | 起步：策略随机，杆子几乎立刻倒下 |
| 9 | -5.05 | 111.05 | 0.91 | 谷底：大幅试探，单步 reward 最低，但回合已被拖长 |
| 15 | 0.06 | 84.80 | 0.73 | reward 由负转正 |
| 30 | 2.41 | 153.92 | 0.64 | 稳步上升 |
| 39 | 4.89 | 300.00 | 0.54 | 第一次站满整个回合（300 步上限） |
| 50 | 4.92 | 300.00 | 0.36 | reward 到顶后，继续收紧动作噪声 |
| 149 | 4.95 | 300.00 | 0.07 | 收敛：近似确定性控制 |

这张表正好说明前面那句“不要只看 reward”：

- **Mean reward 不是单调的**——它先从 0.13 跌到 -5.05，再爬到 4.95。只看头几轮 reward，你可能误以为训练在变差。
- **episode length 几乎单调变长**（12.78 → 300），更早、更稳地告诉你“策略在学会让杆子活得更久”。
- **action std 单调下降**（1.00 → 0.07），说明策略从“到处乱试”逐渐收敛到“稳定确定的控制”。

三条线一起看，才能判断训练是否健康。完整的逐字段日志（iteration 0 与 149 两整块）见 [第一次训练](../01-getting-started/02-first-run-cartpole.md)。

## TensorBoard

训练产物通常放在 `logs/<library>/<experiment_name>/<timestamp>/` 下。用 TensorBoard 查看：

```bash
tensorboard --logdir logs/rsl_rl
```

重点看四类曲线：

| 曲线 | 含义 |
|---|---|
| `Train/mean_reward` | 总体是否在学 |
| `Train/mean_episode_length` | 是否更稳定、更久存活 |
| `Episode_Reward/<term>` | 各奖励项是否按预期变化 |
| `Episode_Termination/<term>` | 回合结束原因是否合理 |

如果总 reward 上升，但视频中行为奇怪，要看分项奖励是否被策略利用。

## 训练产物

典型目录结构：

```text
logs/rsl_rl/<experiment_name>/<timestamp>/
├── params/
│   ├── env.yaml
│   └── agent.yaml
├── git/
│   └── IsaacLab.diff
├── events.out.tfevents...
├── model_0.pt
├── model_50.pt
└── model_<last>.pt
```

| 文件 | 用途 |
|---|---|
| `env.yaml` | 环境配置快照 |
| `agent.yaml` | 算法配置快照 |
| `model_*.pt` | checkpoint |
| `events.out...` | TensorBoard 日志 |
| `git/*.diff` | 实验时的代码差异记录 |

训练可复现的前提，是日志目录里能找到配置、权重和代码差异。

## 回放策略

训练后用 `play.py` 回放：

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
    --task Isaac-Cartpole-v0 \
    --num_envs 16 \
    --checkpoint logs/rsl_rl/cartpole/<timestamp>/model_149.pt
```

回放时要看：

```text
[ ] 策略行为是否符合任务目标？
[ ] 是否只在训练初始状态附近有效？
[ ] 是否出现抖动、撞限位、穿模等异常？
[ ] episode 结束原因是否合理？
[ ] 换 seed 或增加随机化后是否仍然稳定？
```

## 续训

续训需要显式加 `--resume`：

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-Cartpole-v0 \
    --resume \
    --load_run <timestamp> \
    --checkpoint model_100.pt
```

只指定 checkpoint 不等于续训。`--resume` 会恢复 runner 状态和优化器状态。

## 训练回放闭环

本页命令跑通后，应该至少看到三个信号：训练产生 checkpoint，`play.py` 能加载 checkpoint 回放，`--resume` 能恢复 runner 状态继续训练。

```text
Learning iteration 19/20
Training time: 5.23 seconds
model_0.pt
model_19.pt
```

续训时不要只传 checkpoint 文件名，还要显式加 `--resume`，并让 `--load_run` 指向对应 run 目录：

```text
--resume --load_run <run_folder_name> --checkpoint model_19.pt
[INFO]: Loading model checkpoint from: .../<run_folder_name>/model_19.pt
Learning iteration 19/20
Training time: 1.12 seconds
```

排错时先分清两件事：`play.py` 只需要加载策略权重做回放；`train.py --resume` 需要恢复训练状态，包含优化器和 runner 状态。两者不是同一个验收目标。

## 小结

- 一次训练闭环包括 train、看曲线、找 checkpoint、play 回放。
- 日志要同时看 reward、episode length、action std、termination 和分项奖励。
- TensorBoard 分项曲线能帮助判断策略是否钻了奖励漏洞。
- 续训必须显式 `--resume`。

## 导航

- 返回目录：[训练与评测](../05-training.md)
- 下一页：[配置系统与 CLI](02-config-and-cli.md)
