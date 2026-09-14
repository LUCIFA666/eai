# 读评测日志

目标：读懂 VLA-Adapter LIBERO 完整 eval log 和 rollout 视频，判断完整评测是否有效，并提取后续复查需要的字段。

完整评测结束后，最后一个成功率数字只是结果的一部分。一个可复现结果通常还要能回答：跑的是哪个 checkpoint、哪个 suite、多少 episodes、成功多少、日志在哪里、视频有没有保存、是否出现中途崩溃。

## 日志在哪里

评测日志会放在 `eval_logs`，rollout 视频会放在 `rollouts/vla-adapter`。如果沿用上一页命令，本地微调 checkpoint 的 Spatial 完整评测日志是：

```bash
tail -120 eval_logs/Spatial--finetuned-40000--full--*.log
```

如果另外补跑了官方 Pro checkpoint 的完整 baseline，也可以用同样方式读：

```bash
tail -120 eval_logs/Spatial--chkpt.log
```

smoke test 日志只适合作为链路检查；它可以证明模型加载、EGL、日志和视频保存链路可用，但不建议当作完整评测成功率。

## `Final results`

日志里最值得关注的是 `Final results` 附近的汇总。建议记录：

| 字段 | 怎么填 |
| --- | --- |
| suite | `libero_spatial` / `libero_object` / `libero_goal` / `libero_10` |
| episodes | 完整评测通常是 500 |
| successes | 日志里的成功次数 |
| success rate | 成功次数除以 episodes |
| seed | `GenerateConfig` 默认是 7，若改过适合记录 |
| checkpoint | 本地微调 checkpoint 路径，例如 `$ARTIFACT_ROOT/runs/<run_id>--40000_chkpt` |

如果日志没有 `Final results`，这次评测更适合作为失败案例记录，不建议写成成功率结果。

## 本次 Spatial Pro 结果

本教程实测对同一次 4×A100 Spatial Pro 正式训练中的多个 checkpoint 做了完整 eval。每次完整 eval 都是 `num_trials_per_task=50`，共 500 episodes。

| checkpoint | successes / episodes | success rate | eval 用时 | 结论 |
| --- | ---: | ---: | ---: | --- |
| `30000_chkpt` | 491/500 | 98.2% | 1:08:47 | 已接近平台区。 |
| `40000_chkpt` | 493/500 | 98.6% | 1:09:03 | 本轮采用。 |
| `45000_chkpt` | 493/500 | 98.6% | 1:05:55 | 与 40k 持平。 |
| `50000_chkpt` | 486/500 | 97.2% | 1:04:33 | 出现回落。 |

`40000_chkpt` 和 `45000_chkpt` 的总成功率相同。这里选择 `40000_chkpt`，原因是它更早达到本轮最佳成功率，而 `50000_chkpt` 已经回落。这个例子说明 checkpoint 选择不能简单取最后一步，也不能只看训练 loss。

本轮每个 checkpoint 只做了一次完整 eval，每次是固定配置下的 500 episodes。这个粒度适合课程复现和工程选择；如果要做论文式或更严格的统计结论，应对关键 checkpoint 跑多个 seeds 或 repeats，并报告均值和波动范围。

30k 还跑过一次 smoke eval：第一次因为没有设置 `PYTHONPATH` 出现 `ModuleNotFoundError: No module named 'libero'`；补上环境变量后，`num_trials_per_task=1` 的 smoke eval 完成 `10/10`。这个结果只证明链路可用，不进入上面的正式成功率表。

## 再看每任务成功率

LIBERO suite 通常包含 10 个任务。整体成功率高，但某个任务特别低时，说明模型可能在特定物体、空间关系或长程任务上失败。把每个任务的成功次数单独摘出来，通常比只写平均值更有解释力。

记录模板：

| task index | task name | trials | successes | success rate | 观察 |
| --- | --- | --- | --- | --- | --- |
| 0 | 待填写 | 50 | 待填写 | 待填写 | 待填写 |
| 1 | 待填写 | 50 | 待填写 | 待填写 | 待填写 |

## 看 rollout 视频

视频的价值不只是“证明有画面”，还在于帮助判断失败类型：

| 现象 | 可能含义 |
| --- | --- |
| 机械臂完全不动 | 动作输出、反归一化或环境 step 可能有问题。 |
| 机械臂动但方向离谱 | checkpoint flags、动作尺度或图像输入可能不一致。 |
| 能接近物体但抓取失败 | 策略能力问题或该任务本身更难。 |
| 前几步正常，后面漂移 | open-loop chunk 累积误差或状态反馈不足。 |

如果需要可视化证据，可以从失败和成功 episode 中各选一段 rollout 视频截图，说明策略行为。

## EGL cleanup warning 怎么看

无显示器服务器上，评测结束阶段可能出现 EGL cleanup 相关 exception。可以按下面两个信号判断：

- 如果已经打印 `Final results`，且视频和日志已经保存，这类 cleanup warning 通常不等于评测失败。
- 如果 rollout 中途崩溃且没有 `Final results`，当前日志更适合作为渲染问题排查材料，不建议当作评测结果。

## Tokenizer fork warning

`huggingface/tokenizers` 的 fork warning 常见于多进程环境。它一般不影响 rollout，可以用下面环境变量减少噪声：

```bash
export TOKENIZERS_PARALLELISM=false
```

## 本页小结

- 正式评测成功率以完整 eval 的 `Final results` 为准。
- smoke test 是链路检查，不建议写成正式成功率。
- 多个 checkpoint 应统一用完整 eval 对比；成功率持平时，优先选择更早达到平台区的 checkpoint。
- rollout 视频适合用来分析失败模式，而不只是截图装饰。

## 回看问题

1. 没有 `Final results` 的日志适合用来记录成功率吗？
2. 如果整体成功率高但某个任务低，适合补充哪类观察？
3. smoke test 和完整评测的日志在后续记录里分别承担什么角色？

## 导航

- 上一节：[微调 Checkpoint 评测](01-finetuned-checkpoint-eval.md)
- 返回上级：[评测](../06-evaluation.md)
- 下一节：[官方 Baseline 评测](03-official-baseline-eval.md)
