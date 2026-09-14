# 评测

`experiments/robot/libero/run_libero_eval.py` 在 LIBERO 仿真里跑完整 rollout，统计任务成功率。本页评测上一步训出的自训 checkpoint，统计它在 LIBERO-Spatial 上的成功率并对照论文报告值，最后给出两个 rollout 展示实际执行。

## 运行评测

```bash
python experiments/robot/libero/run_libero_eval.py \
  --pretrained_checkpoint /PATH/TO/RUNS/<run-id>/<step>_chkpt \
  --task_suite_name libero_spatial \
  --center_crop True
```

几个决定结果是否可比的点：

- `--center_crop True` 必须开。训练用了 90% 面积的随机裁剪增强，评测要对应取中心 90% 裁剪，不开会导致成功率下降。
- 评测用与训练同款 GPU。跨型号会导致成功率下降，成因和 LoRA 合并设备有关。
- 脚本默认跑 500 个 trial，即 10 个任务、每个任务 50 个 episode。

评测跑完打印 `Overall success rate` 之后，可能出现几段 EGL 在进程退出时析构渲染上下文的清理信息，它出现在最终结果之后，不影响成功率数字。

## LIBERO-Spatial 成功率

| 来源 | LIBERO-Spatial 成功率 |
| --- | --- |
| 论文报告 | Spatial 约 96–97%（四套件平均 97.1%） |
| 自训 checkpoint（50K，本地复现） | 96.8%（484/500） |

自训 checkpoint 的成功率是本地一次复现的结果，仅作参考。50K 本地训练的 L1 loss 停在 0.03 附近，和论文的 0.006 差约 5 倍，但任务成功率只差约 2 个点。这说明 150K 步加学习率衰减主要继续降低已经不大的 loss，50K 步已达到大部分任务表现。时间受限时不训练满 150K，也能接近论文报告的成功率。

## rollout 示例

下面两段是自训 checkpoint 在同一个任务上的 rollout，任务指令为 pick up the black bowl on the stove and place it on the plate。

第一段成功完成任务：策略把夹爪对到灶台上的黑碗，抓起后移到盘子上方并放下。

<figure>
  <video src="assets/rollout-stove-success.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>
  <figcaption>自训 checkpoint 的成功 rollout：抓起灶台上的黑碗并放到盘子上。</figcaption>
</figure>

第二段是同一任务的失败案例：抓取或放置阶段没有完成，属于占少数的失败 trial。500 个 trial 里有 16 个失败，多集中在抓取位置更难的碗上，和 96.8% 的整体成功率一致。

<figure>
  <video src="assets/rollout-stove-failure.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>
  <figcaption>自训 checkpoint 的失败 rollout：同一任务下抓取或放置未完成。</figcaption>
</figure>

## 导航

- 上一节：[训练](06-training.md)
- 返回上级：[OpenVLA-OFT](../01-openvla-oft.md)
- 下一节：[Consistency Policy](../02-consistency-policy.md)
