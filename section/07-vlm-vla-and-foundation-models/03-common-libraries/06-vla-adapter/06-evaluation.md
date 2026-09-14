# 评测

目标：理解 VLA-Adapter 如何用 LIBERO 完整评测验证 checkpoint，并把日志、视频和成功率整理成可信记录。

本模块区分三件事：官方 checkpoint smoke test、本地微调 checkpoint 完整评测、官方 checkpoint baseline 复现。它们都运行 `experiments/robot/libero/run_libero_eval.py`，但证据用途不同。

| 评测类型 | 作用 | 不能替代什么 |
| --- | --- | --- |
| 官方 checkpoint smoke test | 验证环境、EGL、模型加载、动作输出、日志和视频链路。 | 不能证明本地训练 checkpoint 有效。 |
| 本地微调 checkpoint 完整评测 | 验证本地 LoRA 训练产物在 LIBERO Spatial 的 rollout 表现。 | 不能替代官方 baseline 对照。 |
| 官方 checkpoint baseline 复现 | 复查官方 Pro checkpoint 在本机环境下的完整结果。 | 不能证明自训 checkpoint 达到同等水平。 |

无论哪一种评测，都要核对 `pretrained_checkpoint`、`task_suite_name`、`use_proprio`、`num_images_in_input`、`use_pro_version`、`dataset_statistics.json` 和 `unnorm_key` 是否来自同一组配置。

## 学习路径

| 页面 | 重点 |
| --- | --- |
| [微调 Checkpoint 评测](06-evaluation/01-finetuned-checkpoint-eval.md) | 本地训练产物的正式 Spatial eval 命令和参数对齐 |
| [读评测日志](06-evaluation/02-read-eval-logs.md) | `Final results`、本次 30k-50k 结果和 checkpoint 选择 |
| [官方 Baseline 评测](06-evaluation/03-official-baseline-eval.md) | 可选复现官方 Pro checkpoint 完整结果 |
| [Rollout 视频与失败案例](06-evaluation/04-rollout-video-and-failure-cases.md) | 如何从视频定位策略问题，并复查本次失败案例 |

## 导航

- 上一节：[训练日志](05-training/06-training-logs.md)
- 返回上级：[VLA-Adapter](../06-vla-adapter.md)
- 下一节：[微调 Checkpoint 评测](06-evaluation/01-finetuned-checkpoint-eval.md)
