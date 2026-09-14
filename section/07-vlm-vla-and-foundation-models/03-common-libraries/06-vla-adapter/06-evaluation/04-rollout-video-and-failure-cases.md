# Rollout 视频与失败案例

目标：知道如何从 rollout mp4 中观察策略行为，并把失败归因到数据、模型、评测或环境。

完整评测的成功率只告诉你“成了多少次”。视频能帮助解释“为什么失败”。

## 看视频时关注什么

| 观察点 | 可能对应的问题 |
| --- | --- |
| 初始移动方向就错 | 语言理解、图像视角或动作坐标问题。 |
| 接近目标但抓取失败 | gripper 通道、动作尺度或数据覆盖问题。 |
| 动作幅度异常大 | action un-normalization 或 statistics 不匹配。 |
| 前几步正常后漂移 | open-loop chunk、环境状态反馈或任务长程依赖问题。 |
| 视频保存不完整 | rollout 中途异常、渲染或磁盘问题。 |

## 记录失败案例

每次完整 eval 可以保留：

```text
suite:
task id:
episode id:
checkpoint:
log file:
video path:
failure summary:
next check:
```

这样后续调参时能比较同一类失败是否减少，而不是只看整体成功率波动。

## 本次 40000 checkpoint 视频案例

下面的视频来自本教程最终采用的 `40000_chkpt`。40k 的 7 个失败主要集中在 `on_the_ramekin` 和 `in_the_top_drawer`，同时包含少量 cookie box 相关失败。因此这里选取 top drawer 的成功/失败对照、ramekin 失败、cookie box 失败，以及一个 wooden cabinet 成功案例，用来覆盖主要失败簇和正常成功行为。

这些视频是代表性观察，不替代完整 500 episodes 的统计结果；它们的作用是帮助读者把成功率数字和具体策略行为对应起来。

### 成功：top drawer

```text
checkpoint: 40000_chkpt
episode: 214
task: pick up the black bowl in the top drawer
success: True
观察重点：机械臂能处理抽屉附近的空间关系，抓取目标碗，并完成放置。
```

<figure>
  <video src="../assets/vla-adapter-spatial-40k-success-top-drawer.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>
  <figcaption>视频 1：40000 checkpoint 在 top drawer 任务中的成功案例。</figcaption>
</figure>

### 失败：top drawer

```text
checkpoint: 40000_chkpt
episode: 230
task: pick up the black bowl in the top drawer
success: False
观察重点：同一类任务中也会失败，因此不能只看单个成功视频判断 checkpoint。
```

<figure>
  <video src="../assets/vla-adapter-spatial-40k-fail-top-drawer.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>
  <figcaption>视频 2：40000 checkpoint 在 top drawer 任务中的失败案例。</figcaption>
</figure>

### 失败：ramekin

```text
checkpoint: 40000_chkpt
episode: 270
task: pick up the black bowl on the ramekin
success: False
观察重点：目标和支撑物体关系更紧，失败常出现在抓取接触或放置阶段。
```

<figure>
  <video src="../assets/vla-adapter-spatial-40k-fail-ramekin.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>
  <figcaption>视频 3：40000 checkpoint 在 ramekin 相关任务中的失败案例。</figcaption>
</figure>

### 失败：cookie box

```text
checkpoint: 40000_chkpt
episode: 349
task: pick up the black bowl next to the cookie box
success: False
观察重点：这个案例覆盖 40k 中较低频的 cookie box 空间关系失败；它不是主要失败来源，但能帮助观察抓取稳定性和放置细节。
```

<figure>
  <video src="../assets/vla-adapter-spatial-40k-fail-cookie-box.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>
  <figcaption>视频 4：40000 checkpoint 在 cookie box 相关任务中的失败案例。</figcaption>
</figure>

### 成功：wooden cabinet

```text
checkpoint: 40000_chkpt
episode: 500
task: pick up the black bowl on the wooden cabinet
success: True
观察重点：这个案例展示非失败集中任务中的正常行为，机械臂能完成接近、抓取和放置动作。
```

<figure>
  <video src="../assets/vla-adapter-spatial-40k-success-wooden-cabinet.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>
  <figcaption>视频 5：40000 checkpoint 在 wooden cabinet 任务中的成功案例。</figcaption>
</figure>

## 跨 checkpoint 失败分布

本次完整 eval 的总结果是：

| checkpoint | 成功率 | 失败数 | 主要失败集中任务 |
| --- | ---: | ---: | --- |
| `40000_chkpt` | 98.6% | 7 | `on_the_ramekin`、`in_the_top_drawer` |
| `45000_chkpt` | 98.6% | 7 | `on_the_stove`、`on_the_ramekin` |
| `50000_chkpt` | 97.2% | 14 | `in_the_top_drawer`、`on_the_ramekin` |

`45000_chkpt` 和 `40000_chkpt` 总成功率相同，但失败任务分布不同；`50000_chkpt` 失败数增加。这个现象说明，checkpoint 选择不能只看 step 更大，也不能只看某一个视频。更稳妥的做法是同时看完整成功率、失败任务分布、eval 日志和代表性 rollout。

## 导航

- 上一节：[官方 Baseline 评测](03-official-baseline-eval.md)
- 返回上级：[评测](../06-evaluation.md)
- 下一节：[部署](../07-deployment.md)
