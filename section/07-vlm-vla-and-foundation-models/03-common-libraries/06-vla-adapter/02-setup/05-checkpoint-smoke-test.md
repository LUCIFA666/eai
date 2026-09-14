# 官方 Checkpoint 链路检查

目标：用官方 LIBERO-Pro Spatial checkpoint 跑一个最小 smoke test，确认模型加载、EGL 离屏渲染、动作输出、日志和 rollout 视频链路可用。

这里的 smoke test 是链路检查，不是正式成功率；官方 checkpoint 的完整 500 rollout 更适合作为可选 baseline，主线可以先用 smoke test 确认评测链路，再进入 LoRA 微调。

先跑 smoke test 的价值在于把评测链路问题提前暴露出来：如果模型加载、LIBERO 环境、EGL 渲染、动作维度或视频保存有问题，可以在训练前先排查。否则等 LoRA 训练结束后才发现评测跑不通，很难判断问题来自训练结果，还是来自评测环境和参数配置。

## 日志和 rollout 视频目录

VLA-Adapter 官方仓库根目录已经自带 `eval_logs/`，其中是官方参考评测日志，例如：

```text
Inference--Spatial_Pro--99.6.log
Inference--Object_Pro--99.6.log
Inference--Goal_Pro--98.2.log
Inference--Long_Pro--96.4.log
Inference-Spatial--97.8.log
Inference-Object--99.2.log
Inference-Goal--97.2.log
Inference-Long--95.0.log
Inference--CALVIN_Pro--4.50.log
```

这些文件是官方参考日志，不代表当前运行环境已经完成过评测。教程里的 smoke test 会写入 `eval_logs/Spatial--smoke.log`，文件名不同于官方参考日志名，因此按教程命令运行不会覆盖官方日志。如果修改重定向文件名，应避免使用官方已有的 `Inference...log` 文件名。如果仓库副本缺少 `eval_logs/`，可以再执行 `mkdir -p eval_logs`。

评测脚本默认还会在 `./experiments/logs/` 写一份 `EVAL-...txt` 内部日志。rollout 视频写到 `./rollouts/`（相对源码根目录，已被 gitignore），smoke test 会在这里保存 mp4；这个目录由脚本自动创建，不需要提前建目录，也没有对应参数。

`rollouts/` 里的 mp4 属于临时文件，可以随时清理或重跑覆盖。如果某些 episode 需要长期保留，评测结束后可以把对应视频复制到另一个专门存放实验产物的目录。

## 运行前环境变量

```bash
export PYTHONPATH=$PWD/LIBERO:$PYTHONPATH
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export TOKENIZERS_PARALLELISM=false
```

`PYTHONPATH=$PWD/LIBERO:$PYTHONPATH` 用于让评测脚本找到 `libero.libero`；如果省略，可能在启动时遇到 `ModuleNotFoundError: No module named 'libero'`。无显示器服务器上，`MUJOCO_GL=egl` 和 `PYOPENGL_PLATFORM=egl` 能减少渲染初始化错误。`TOKENIZERS_PARALLELISM=false` 只是减少 tokenizer fork warning 噪声，不改变模型结果。

## Spatial smoke test

smoke test 可以把每个任务的 rollout 数降到 1。LIBERO Spatial 有 10 个任务，因此 smoke test 大约是 10 个 episodes，更适合作为链路检查记录，不建议写成完整评测结果。命令默认在 VLA-Adapter 源码根目录运行；多卡服务器可以把 `CUDA_VISIBLE_DEVICES=0` 换成空闲 GPU，例如 `CUDA_VISIBLE_DEVICES=4`。

```bash
CUDA_VISIBLE_DEVICES=0 python experiments/robot/libero/run_libero_eval.py \
  --use_proprio True \
  --num_images_in_input 2 \
  --use_film False \
  --pretrained_checkpoint outputs/LIBERO-Spatial-Pro \
  --task_suite_name libero_spatial \
  --use_pro_version True \
  --num_trials_per_task 1 \
  --run_id_note smoke \
  > eval_logs/Spatial--smoke.log 2>&1
```

## Smoke Test 预期现象

smoke test 会产生两类日志。`eval_logs/Spatial--smoke.log` 是 shell 重定向日志，包含完整终端输出、warning、traceback、进度条和保存视频路径；如果 smoke test 失败，通常先从这里找最后一个报错。

脚本内部还会在 `experiments/logs/` 下写一份更干净的 `EVAL-libero_spatial-...--smoke.txt` 日志。文件名里的时间戳会随运行变化，成功时这份内部日志末尾应出现 `Final results`、`Total episodes: 10`、成功 episode 数和总体成功率。

跑通后的内部日志末尾如下：

```text
Final results:
Total episodes: 10
Total successes: 10
Overall success rate: 1.0000 (100.0%)
```

`Total episodes: 10` 对应 LIBERO Spatial 的 10 个任务、每个任务 1 次 rollout。`rollouts/vla-adapter/` 下应能看到本次生成的 mp4。这里的 100.0% 是 smoke test 链路检查结果，只说明模型加载、仿真渲染、动作输出、日志和视频保存链路已经跑通，后续正式实验结果应以完整评测页的记录为准。

如果没有看到 `Final results`，优先检查 checkpoint 路径、LIBERO 导入、EGL 渲染、动作维度或显存相关报错。

如果需要确认视频产物，可以打开 `rollouts/vla-adapter/` 下本次生成的 mp4，检查画面是否正常保存、动作过程是否完整，以及视频文件是否能正常播放。

## 可选：官方 Checkpoint 完整 Spatial 评测

如果目标是本地复现官方 Pro checkpoint 的 baseline，可以在 smoke test 通过后再跑完整 Spatial 评测。这一步更适合作为 baseline 复现，不必挡在 LoRA 微调之前；如果当前目标是尽快完成微调复现实验，可以先跳到下一页。

```bash
CUDA_VISIBLE_DEVICES=0 python experiments/robot/libero/run_libero_eval.py \
  --use_proprio True \
  --num_images_in_input 2 \
  --use_film False \
  --pretrained_checkpoint outputs/LIBERO-Spatial-Pro \
  --task_suite_name libero_spatial \
  --use_pro_version True \
  > eval_logs/Spatial--chkpt.log 2>&1
```

源码默认 `num_trials_per_task=50`，每个 suite 通常是 10 个任务，因此完整评测是 500 rollouts。文本日志通常不大，但完整评测会在 `rollouts/` 下保存约 500 个 mp4；Long suite 单个 episode 可能更长。

## 可选：其他官方 Pro Checkpoint 评测对照

| Suite | `pretrained_checkpoint` | `task_suite_name` | 日志文件 |
| --- | --- | --- | --- |
| Spatial | `outputs/LIBERO-Spatial-Pro` | `libero_spatial` | `eval_logs/Spatial--chkpt.log` |
| Object | `outputs/LIBERO-Object-Pro` | `libero_object` | `eval_logs/Object--chkpt.log` |
| Goal | `outputs/LIBERO-Goal-Pro` | `libero_goal` | `eval_logs/Goal--chkpt.log` |
| Long | `outputs/LIBERO-long-Pro` | `libero_10` | `eval_logs/Long--chkpt.log` |

Object、Goal、Long 的完整命令只需要替换上表三列，其余 flags 保持：

```bash
--use_proprio True
--num_images_in_input 2
--use_film False
--use_pro_version True
```

这些 flags 通常需要与 Pro checkpoint 配置保持一致。比如 `use_proprio` 如果与训练配置不一致，可能导致加载失败，或者让输出行为变得不可信。

## 导航

- 上一节：[Checkpoint 准备](04-checkpoint-setup.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[路径与环境变量](06-paths-and-env.md)
