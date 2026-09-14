# 官方 Baseline 评测

目标：说明什么时候需要跑官方 Pro checkpoint 的完整 500 rollout baseline，以及它和 smoke test、本地微调结果的区别。

官方 Pro checkpoint 完整评测适合作为 baseline 复现，但不是进入 LoRA 微调的前置条件。第一次学习主线可以先用 Spatial smoke test 确认评测链路，再进入训练。

## Spatial baseline 命令

```bash
CUDA_VISIBLE_DEVICES=0 python experiments/robot/libero/run_libero_eval.py   --use_proprio True   --num_images_in_input 2   --use_film False   --pretrained_checkpoint outputs/LIBERO-Spatial-Pro   --task_suite_name libero_spatial   --use_pro_version True   > eval_logs/Spatial--chkpt.log 2>&1
```

源码默认 `num_trials_per_task=50`，LIBERO Spatial 有 10 个任务，因此完整评测是 500 rollouts，视频写到仓库内的 `rollouts/`（已被 gitignore）；需要长期保留的可以复制到其他目录。

## 其他 Pro checkpoint

| Suite | `pretrained_checkpoint` | `task_suite_name` | 日志文件 |
| --- | --- | --- | --- |
| Spatial | `outputs/LIBERO-Spatial-Pro` | `libero_spatial` | `eval_logs/Spatial--chkpt.log` |
| Object | `outputs/LIBERO-Object-Pro` | `libero_object` | `eval_logs/Object--chkpt.log` |
| Goal | `outputs/LIBERO-Goal-Pro` | `libero_goal` | `eval_logs/Goal--chkpt.log` |
| Long | `outputs/LIBERO-long-Pro` | `libero_10` | `eval_logs/Long--chkpt.log` |

## 和本地结果的关系

官方 baseline 用来确认本地环境能复现官方 checkpoint；本地微调结果用来评估自己的训练产物。二者不应混在同一行结果里。

官方 Pro Spatial checkpoint 报告值可以作为参考上限，例如 Pro Spatial baseline 可达到约 `99.6%`。本教程的本地微调结果是另一件事：在 4×A100 的 Spatial Pro 正式训练中，`40000_chkpt` 和 `45000_chkpt` 的完整 eval 都是 `493/500 = 98.6%`。这已经足够说明训练、保存、加载和评测闭环成立，不需要把继续追官方 baseline 作为教程主线目标。

## 导航

- 上一节：[读评测日志](02-read-eval-logs.md)
- 返回上级：[评测](../06-evaluation.md)
- 下一节：[Rollout 视频与失败案例](04-rollout-video-and-failure-cases.md)
