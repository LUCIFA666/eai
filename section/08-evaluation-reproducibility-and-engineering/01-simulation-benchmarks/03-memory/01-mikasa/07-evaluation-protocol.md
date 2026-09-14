# 评测协议与指标

MIKASA-Robo-VLA 的规范评测按 horizon 分档进行：在一个分档上多任务训练，再在该分档的每个任务上跑固定协议。实现见 `mikasa_robo_suite/vla/benchmarking.py`。

## 协议一览

下表的取值即 `BenchmarkConfig` 的默认值。

| 参数 | 规范取值 |
|---|---|
| 分档 | 由用户显式选择（`short` / `medium` / `long` / `all`），不从 checkpoint 自动推断 |
| 每任务 episode 数 | 50 |
| seed | `4242424242 + i`，`i` 取 0 到 49，每个任务用同一串 |
| 并行环境 | `num_envs=1`（默认），允许 `num_envs>1` 作为提速项 |
| `obs_mode` | `rgb` |
| `control_mode` | `pd_ee_delta_pose` |
| `reward_mode` | `normalized_dense` |
| wrapper | `apply_mikasa_vla_wrappers(env, include_overlays=False)` |
| 主指标 | 每 episode 的 `success_once` |
| 调试指标 | 每任务 `mean_return`，不汇总到分档 |

## 单 episode 的评测循环

`run_episode` 每个 episode 用 `seed = start_seed + i` 重置环境，并新建一个空的动作队列，避免上一个 episode 没消费完的动作块串到下一个。策略一次前向输出 `K` 个动作压入队列，每步弹出一个执行；`success` 一旦出现就用 OR 锁存下来：

```python
# benchmarking.py，run_episode() 主循环（简化）
obs, _ = env.reset(seed=episode_seed)
action_queue = deque()                      # 每个 episode 全新，防止动作块泄漏
success_once = False
for _ in range(max_steps):
    if not action_queue:
        action_queue.extend(_chunk_actions(policy.forward(obs), action_shape))
    obs, reward, terminated, truncated, info = env.step(action_queue.popleft())
    total_return += float(reward)
    success_once = success_once or bool(info["success"])   # OR 锁存
    if terminated or truncated:
        break
```

`K=1` 时退化成逐步推理，每步都调用一次 `policy.forward`。

## 主指标 success_once

`success_once` 是布尔锁存而非计数：任务第一次成功就从 `False` 翻成 `True` 并保持。这样，中途就能成功的任务（如 ShellGameTouch）和只在最后一步给成功信号的任务（如 TimedTransfer）被统一成同一个二元结果。

## 三级 SR 口径

一次评测要报三个数：

| 指标 | 定义 |
|---|---|
| 每任务 SR | 50 个 episode 上 `success_once` 的均值 |
| 每分档 SR（主） | 分档内所有任务 SR 的无权重均值 |
| 每记忆类型 SR | 分档内某记忆类型任务 SR 的均值 |

## 结果文件

`evaluate_benchmark` 遍历任务，每完成一个任务就写一个 `<env_id>.json` 并重写 `summary.json`，因此中途中断也留下可读的部分结果。每任务文件含逐 episode 的 `successes`、`returns`，以及 `sr`、`mean_return`、`start_seed`、`memory_type`、`action_chunk_size`、`benchmark_commit`（`git rev-parse HEAD`）等；`summary.json` 含 `sr_split`、`sr_per_memory_type`、`per_task_sr`、`per_task_mean_return`。运行目录带时间戳（`YYYY-MM-DD_HH-MM-SS`），多次运行不互相覆盖。

## 策略接口

runner 只要求策略对象有一个 `chunk_size` 属性和一个 `forward(obs)` 方法，对单环境返回形状 `(chunk_size, 7)`、取值 `[-1, 1]` 的动作：

```python
class MyPolicy:
    chunk_size = 8
    def forward(self, obs: dict) -> torch.Tensor:
        # obs["rgb"] (1,128,128,6) uint8；obs["proprio"] (1,7) float32
        # info["language_instruction"] str
        ...  # 返回 (chunk_size, 7) float32，∈[-1,1]
```

仓库自带 `DummyChunkPolicy`（输出随机动作）用于在接入真实模型前跑通整条评测管线，入口是 `examples/eval_demo.py`。

## 断点续跑

整档评测可能要数小时。`--resume <run_dir>` 会读取该目录下已有的 `<env_id>.json`，把已完成的任务从任务列表里减掉，只评剩下的，并把新结果写回同一目录、更新 `summary.json`。续跑要用与原运行相同的 `--start-seed` 和 `--num-episodes`，否则结果不可比。

## 特权字段不得读取

规范排行榜下，策略只能消费相机图像、`obs["proprio"]` 和 `info["language_instruction"]`。`oracle_info` 已从 VLA 观测里剥掉；`task_cue` 只为 Rotate* 的 RL 训练存在，且同样的角度已写进语言指令。读取其中任何一个都会使该次运行失去规范排行榜资格。

## 导航

- 返回上级：[MIKASA-Robo-VLA](../01-mikasa.md)
- 上一节：[观测与动作接口](06-observation-and-action.md)
- 下一节：[数据集](08-datasets.md)
