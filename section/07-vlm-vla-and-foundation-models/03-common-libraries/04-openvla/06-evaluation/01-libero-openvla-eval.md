# LIBERO OpenVLA 评测

目标：读懂 OpenVLA 的 LIBERO rollout 评测命令，以及 `center_crop`、`unnorm_key`、gripper 处理和日志保存怎样影响结果。

LIBERO 评测把 checkpoint 放进仿真闭环里。每个 episode 开始时，环境 reset 到指定初始状态；模型根据当前图像和任务描述输出 7D action；环境执行 action 后返回下一帧。episode 在任务成功或达到最大步数时结束。

## 参考命令

下面的命令保留 OpenVLA LIBERO 评测的核心参数。`PRETRAINED_CHECKPOINT` 可以是 Hugging Face model id，也可以是本地 merged checkpoint 目录。

```bash
export PRETRAINED_CHECKPOINT="<checkpoint_or_model_id>"
export EVAL_LOG_DIR="<eval_log_dir>"

python experiments/robot/libero/run_libero_eval.py \
  --model_family openvla \
  --pretrained_checkpoint "${PRETRAINED_CHECKPOINT}" \
  --task_suite_name libero_spatial \
  --center_crop True \
  --num_trials_per_task 50 \
  --seed 7 \
  --local_log_dir "${EVAL_LOG_DIR}" \
  --run_id_note local
```

`num_trials_per_task=50` 时，`libero_spatial` 的 10 个任务会产生 500 次 rollout。正式统计前可以先用 `num_trials_per_task=1` 跑 smoke eval：每个任务只跑 1 次，主要检查模型加载、MuJoCo / robosuite 渲染、图像预处理、action 执行、日志和视频保存。

## `center_crop`

OpenVLA 的 LIBERO checkpoint 按带图像增强的数据微调。评测时设置 `center_crop=True`，会把输入图像做中心裁剪再 resize 回模型需要的尺寸，用来对齐训练时的随机裁剪分布。

源码里还有一个直接保护：如果 checkpoint 路径里带 `image_aug`，但 `center_crop` 没有打开，脚本会直接报错。官方 LIBERO checkpoint 路径未必带这个字符串，评测命令仍建议显式设置 `--center_crop True`。

## `unnorm_key`

LIBERO eval 脚本会先把 `unnorm_key` 设成 `task_suite_name`：

```text
libero_spatial -> unnorm_key = "libero_spatial"
```

OpenVLA 的 modified LIBERO 数据常带 `_no_noops` 后缀。源码会检查 checkpoint 的 `norm_stats`，如果找不到 `libero_spatial`，但存在 `libero_spatial_no_noops`，就自动切到后者。这个 fallback 很重要：`unnorm_key` 命中错误会让 action 尺度失真，评测可能仍能运行，但动作幅度会不对。

## Rollout 过程

`run_libero_eval.py` 的一条 episode 主要做这些事：

| 步骤 | 作用 |
| --- | --- |
| `env.reset()` 和 `set_init_state()` | 把环境放到当前任务的指定初始状态。 |
| `num_steps_wait=10` | 开头执行空动作，等待物体在仿真中稳定。 |
| `get_libero_image()` | 取当前图像，并按模型需要的尺寸处理。 |
| `get_action()` | 调用 OpenVLA，使用任务描述和当前图像预测 action。 |
| `normalize_gripper_action()` | 把 gripper 维度从 `[0, 1]` 转到 LIBERO 环境使用的 `[-1, 1]`。 |
| `invert_gripper_action()` | 对 OpenVLA 翻回 gripper 符号，和环境约定对齐。 |
| `env.step(action)` | 在仿真中执行动作，直到成功或超时。 |

不同 suite 的最大步数不同。`libero_spatial` 是 220 个控制步，再加开头等待步；`libero_10` 更长，最多 520 个控制步。失败 episode 通常会跑满最大步数，因此 full eval 会明显耗时。

## 日志和视频

脚本会在 `local_log_dir` 下写本地日志，记录每个 task、episode、成功与否、累计成功数和当前成功率。每条 rollout 还会保存 MP4，文件名里带 episode 编号、success 标记和任务描述。

读日志时重点看三类行：

| 日志字段 | 用途 |
| --- | --- |
| `Success: True/False` | 当前 episode 是否完成任务。 |
| `# episodes completed so far` | 当前累计 rollout 数。 |
| `# successes` | 当前累计成功数和成功率。 |

这些日志能支撑成功率和失败样例分析。失败原因的细分需要结合 rollout 视频观察，脚本本身不会自动把失败归类为抓取失败、放置失败或目标识别错误。

## 本页小结

- LIBERO eval 是闭环 rollout，能验证 checkpoint 在仿真任务中的成功率。
- `center_crop=True`、`unnorm_key` 和 gripper 处理都会直接影响动作执行。
- `num_trials_per_task=1` 适合 smoke eval，`50` 才进入较完整的单 seed 成功率统计。
- 日志给出成功率，视频用于回看失败过程。

## 导航

- 上一节：[评测](../06-evaluation.md)
- 返回上级：[评测](../06-evaluation.md)
- 下一节：[Bridge WidowX 评测入口](02-bridge-widowx-eval.md)
