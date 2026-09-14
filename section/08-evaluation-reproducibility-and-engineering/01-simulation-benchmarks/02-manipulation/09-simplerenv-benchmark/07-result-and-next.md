# 结果解读与下一步

视频能看，但只靠视频还不够。`result.json` 才是后续自动化评测、统计和复现的入口。这一节先学怎么读 `result.json`，再讲清楚 smoke test 和正式 benchmark 之间的区别，以及下一步要怎么走。

## 前置概念

读这一节前，建议先理解（详见 [多步 rollout 与视频](06-rollout-and-video.md)）：

- **三组实验** 分别产出了各自的 `result.json`。
- **动作来源** 是 `zero` 或 `small-random`，不是策略模型。

## 本节目标

读完本节后，你应该能回答：

1. `result.json` 里每个字段分别是什么意思？
2. 为什么本节所有 `success=false` 都不是失败？
3. 从 smoke test 走向正式评测，需要替换哪几样东西？
4. 正式 benchmark 报告至少应记录哪些字段？

## result.json 字段解读

以 0.08 小随机动作版本为例，核心字段如下：

```json
{
  "task": "google_robot_pick_coke_can",
  "seed": 0,
  "instruction": "pick coke can",
  "action_mode": "small-random",
  "action_scale": 0.08,
  "num_frames": 21,
  "video": "runs/11-eval/simplerenv_rollout_video_small_008/rollout.mp4"
}
```

逐字段解释：

- **`task`**：任务名，必须能对应到 `simpler_env.ENVIRONMENTS`。
- **`seed`**：随机种子。复现实验时不要省略。
- **`instruction`**：语言指令。本例为 `pick coke can`。
- **`action_mode`**：动作来源。本节用的是 `zero` 或 `small-random`，不是策略模型。
- **`action_scale`**：小随机动作的幅度。
- **`num_frames`**：保存的视频帧数。20 步 rollout 会得到 21 帧，因为包含 reset 后的第 0 帧。
- **`records`**：每一步的动作、奖励、终止标志和 `episode_stats`。

## 实验汇总

本次三组实验的结果可以概括为：

| 实验 | 步数 | 帧数 | reward | success | 解释 |
|---|---|---:|---:|---:|---|---|
| 单步零动作 | 1 | 2 | 0.0 | false | 验证 `env.step()` 能执行 |
| 10 步零动作 | 10 | 11 | 0.0 | false | 验证连续 step、渲染和视频保存 |
| 10 步 small-random 0.02 | 10 | 11 | 0.0 | false | 验证非零动作接口 |
| 20 步 small-random 0.08 | 20 | 21 | 0.0 | false | 展示更明显的机械臂移动 |

这里的 `success=false` 不是失败，而是实验设计本身决定的：我们没有接入抓取策略，也没有控制夹爪完成任务，只是在做环境和接口验证。正式 benchmark 才应该报告 success rate。

## 从 smoke test 走向正式评测

本节完成的是最小闭环：

```text
安装成功
  -> 能列出任务
  -> 能创建环境
  -> 能 reset
  -> 能取 RGB 图像
  -> 能 step
  -> 能保存视频和 JSON
```

下一步如果要做正式评测，需要替换动作来源：

```python
action = env.action_space.sample()        # 本节不推荐用于正式结果
action = policy.infer(obs, instruction)   # 正式评测时应由策略给出动作
obs, reward, terminated, truncated, info = env.step(action)
```

官方仓库中可以继续看的入口有：

- `simpler_env/simple_inference_visual_matching_prepackaged_envs.py`：预打包 visual matching 环境的简单策略推理脚本。
- `simpler_env/evaluation/`：更完整的评测和日志逻辑。
- `scripts/`：官方用于复现实验结果的 bash 脚本。
- `tools/calc_metrics.py`：用于计算 real-to-sim 评测相关指标。

正式报告时，建议至少保存：

```text
task
seed
policy_name
checkpoint
max_steps
success
episode_stats
video_path
result_json
```

这样同学或助教才能复查：策略到底跑了哪个任务、用了哪个 checkpoint、在哪个 seed 下失败或成功。

## 小结

- `result.json` 是自动化复现和评测统计的入口，视频只适合作为直观证据。
- `task`、`seed`、`instruction`、`action_mode`、`action_scale`、`num_frames` 和 `records` 是本节最重要的记录字段。
- 本节所有 `success=false` 都不代表环境失败，因为动作不是策略，只是 smoke test 输入。
- 正式 benchmark 应报告策略名称、checkpoint、episode 设置、success rate 和失败统计。

## 导航

- 上一节：[多步 rollout 与视频](06-rollout-and-video.md)
- 返回上级：[SimplerEnv](../09-simplerenv-benchmark.md)
- 下一节：[动手练习](08-practice.md)
