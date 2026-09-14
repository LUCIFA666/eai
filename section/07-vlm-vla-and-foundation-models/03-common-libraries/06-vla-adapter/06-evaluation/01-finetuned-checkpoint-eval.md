# 微调 Checkpoint 评测

目标：用本地 LoRA 微调产物跑 LIBERO Spatial 完整评测，形成教程主线里的本地评测结果。

这一页默认已经完成 LoRA 微调，并从训练日志中确认了可评测的 checkpoint 目录。官方 Pro checkpoint 的 smoke test 只证明评测链路可用；本页评测的是本地训练产物。

## 确认待评测 checkpoint

先从上一页训练日志和 `$ARTIFACT_ROOT/runs` 目录确认本次训练输出（`$ARTIFACT_ROOT` 是训练时设置的产物根）。常见路径形态是：

```text
$ARTIFACT_ROOT/runs/<run_id>--40000_chkpt
```

如果训练中已经 merge LoRA 权重，应优先使用评测脚本能直接加载的 merge 后 checkpoint 目录。具体目录以训练日志和实际文件列表为准，不要只凭 run id 记忆填写。

可以先做一次只读检查：

```bash
export ARTIFACT_ROOT=<artifact-root>
FINETUNED_CKPT=$ARTIFACT_ROOT/runs/<run_id>--40000_chkpt
find "$FINETUNED_CKPT" -maxdepth 2 -type f | sort | head -80
```

预期能看到模型配置、权重文件、action head 或 proprio projector 等评测所需文件。若目录为空，或只有训练中间文件但缺少评测脚本需要的模型文件，应先回到训练日志排查保存和 merge 过程。

## Spatial 完整评测

Spatial 是本教程主线的第一个正式评测目标。命令默认在 VLA-Adapter 源码根目录运行：

```bash
export PYTHONPATH=/path/to/VLA-Adapter/LIBERO:$PYTHONPATH
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export TOKENIZERS_PARALLELISM=false
export ARTIFACT_ROOT=<artifact-root>

FINETUNED_CKPT=$ARTIFACT_ROOT/runs/<run_id>--40000_chkpt
current_time=$(date +%Y%m%d-%H%M%S)
log_file="eval_logs/Spatial--finetuned-40000--full--$current_time.log"

CUDA_VISIBLE_DEVICES=0 python experiments/robot/libero/run_libero_eval.py \
  --use_proprio True \
  --num_images_in_input 2 \
  --use_film False \
  --pretrained_checkpoint "$FINETUNED_CKPT" \
  --task_suite_name libero_spatial \
  --use_pro_version True \
  --num_trials_per_task 50 \
  --run_id_note "finetuned-40000-full--$current_time" \
  2>&1 | tee "$log_file"
```

`/path/to/VLA-Adapter` 是示例路径，按自己的环境替换即可。LIBERO Spatial 有 10 个任务，因此 `--num_trials_per_task 50` 对应 10 tasks x 50 episodes = 500 rollouts。

第一次跑完整 eval 前，可以先把 `--num_trials_per_task` 临时改成 `1` 做 smoke eval。smoke eval 只检查 checkpoint 加载、EGL 渲染、动作输出、日志和 rollout 视频链路；它不代表正式成功率。

## 参数对齐

这里的 `--use_proprio True`、`--num_images_in_input 2`、`--use_film False`、`--use_pro_version True` 应与训练命令保持一致。如果训练时改过这些配置，评测时也要同步调整，否则可能加载失败，或者得到不可信的 rollout 行为。

`run_libero_eval.py` 的 `use_pro_version` 默认是 `True`（`run_libero_eval.py:128`）。评测常规版（非 Pro）checkpoint 时要显式传 `--use_pro_version False`，否则 action head 会按 Pro block 初始化，与常规版权重不匹配，表现为加载失败或 rollout 成功率异常低。

`--task_suite_name libero_spatial` 对应训练数据 `libero_spatial_no_noops`。训练数据名和评测 suite 名不完全一样，但这两个名称需要指向同一组任务。

## 产物

评测完成后，至少保留：

| 产物 | 路径示例 | 用途 |
| --- | --- | --- |
| 终端日志 | `eval_logs/Spatial--finetuned-40000--full--<time>.log` | 读 `Final results` 和异常堆栈。 |
| 脚本本地日志 | `experiments/logs/EVAL-...txt` | 保留 run id 和脚本内部记录。 |
| rollout 视频 | `rollouts/vla-adapter/.../*.mp4` | 分析成功和失败案例。 |
| checkpoint 文件列表 | `$ARTIFACT_ROOT/runs/<run_id>--40000_chkpt/` | 证明评测的是哪个权重。 |

下一页会用这些日志和视频判断完整评测是否有效，并整理后续复查需要的字段。

## 本页小结

- 本页评测本地 LoRA 微调产物，是教程主线的正式 eval。
- `FINETUNED_CKPT=$ARTIFACT_ROOT/runs/<run_id>--40000_chkpt` 是示例路径，实际路径以训练日志和文件检查为准。
- 完整 Spatial 评测通常会产生约 500 个 rollout 视频，写到仓库内的 `rollouts/`（已被 gitignore）；确认所在盘容量充足，需要长期保留的复制到其他目录。

## 回看问题

1. 为什么 smoke test 跑通后还要确认本地 checkpoint 文件列表？
2. 训练和评测时哪些 flags 需要保持一致？
3. `libero_spatial_no_noops` 和 `libero_spatial` 分别出现在什么场景？

## 导航

- 上一节：[评测](../06-evaluation.md)
- 返回上级：[评测](../06-evaluation.md)
- 下一节：[读评测日志](02-read-eval-logs.md)
