# Mask 质量与时序稳定

> 难度：[中级] | 预计用时：55 分钟
> 先修：[GroundingDINO 与 SAM](02-groundingdino-sam.md)

目标：为分割结果建立质量门禁、时序稳定器和失败码，而不是把每一张 mask 都直接交给规划器。

## 1. 先抓住问题：机器人对物体边界的判断不是一次性的

把 mask 想成”机器人对物体边界的一次下注”。下注可以赢，但也会混入桌面、漏掉把手、把两个实例连成一个块，或者在相邻帧里不断抖动。对人眼来说，这种瑕疵可能只是”边界有点毛”；对机器人来说，它会直接改变点云、碰撞体和抓取中心。mask 质量控制的目标**不是让图更漂亮**，而是让下游**只消费足够可信的区域**。

## 先看“好 mask”和“坏 mask”差在哪

| 现象 | 图像上看起来 | 机器人上会出什么问题 |
|--- | --- | --- |
| mask 泄漏到桌面 | 边界外多了一圈区域 | 点云中心偏低，抓取高度出错 |
| 漏掉杯把手 | 看起来还算像杯子 | 碰撞体过小，侧抓失败 |
| 两个盒子并成一个 | 图像里像”一大片白色” | 规划器把两个物体当成一个障碍 |
| 帧间抖动 | 连续帧边界轻微闪烁 | 目标 pose 乱跳，抓取目标不稳定 |

```text
高质量 mask
  -> 与 depth 边界一致
  -> 面积在合理范围内
  -> 连续帧 IoU 稳定
  -> 单实例拓扑清晰

低质量 mask
  -> 一帧看似正确
  -> 但时序不稳定 / 深度不一致 / 面积异常
  -> 应拒绝执行或触发重观察
```

## 四类最常用质量指标

| 指标 | 计算方式 | 作用 |
|--- | --- | --- |
| 面积与长宽比 | 像素面积、bbox ratio | 去掉太小碎片和不合理形状 |
| 深度一致性 | mask 内深度方差、有效深度比例 | 判断是否混入背景或空洞 |
| 边界贴合 | mask 边界与 RGB/depth 边缘的重合度 | 判断是否明显漏分或越界 |
| 时序稳定性 | 当前帧与上一帧 IoU、中心漂移 | 检查抖动与 id 切换 |

不要把这四项揉成一个“万能分数”。工程上更好用的做法是保留分项，再由 gate 决定是否放行。

## 一个最小 quality gate

```python
# 对 mask 做机器人执行前的快速门禁
def gate_mask(mask_area_px, valid_depth_ratio, temporal_iou, component_count):
    failures = []
    if mask_area_px < 800:
        failures.append("mask_too_small")
    if valid_depth_ratio < 0.85:
        failures.append("bad_depth_alignment")
    if temporal_iou < 0.60:
        failures.append("temporal_flicker")
    if component_count > 3:
        failures.append("fragmented_mask")
    return failures or None

# 预期输出:
# None                    -> 可以放行
# ['bad_depth_alignment'] -> 应要求重新观察或换视角
```

这个 gate 的意义不是追求学术最优，而是给下游一个明确边界：什么样的结果可以继续规划，什么样的结果必须先停下来。

## 为什么深度一致性特别重要

同样一张 2D mask，在 RGB 上看起来没问题，但一旦投到 depth 上就可能暴露问题：

| 情况 | depth 信号 | 结论 |
|--- | --- | --- |
| 目标是实心盒子 | 深度变化平滑 | 可以稳定裁点云 |
| 混入桌面 | 大量点落在平面上 | mask 泄漏，建议做 plane removal |
| 反光杯子 | 大片无效深度 | 不应直接输出物理尺寸 |
| 遮挡严重 | 前后景深度双峰 | pose 不可信，宜重观察 |

所以 mask 质量不是纯视觉问题，它必须和 [RGB-D 与点云](../01-geometric-perception-foundations/03-rgbd-pointcloud.md) 联动。

## 跟踪为什么不是“锦上添花”

单帧分割只能回答“这一帧像不像目标”，不能回答“它是不是刚才那个目标”。对于抓取任务，track id 很重要，因为：

- 机械臂靠近目标时，相机视角在变。
- 物体可能短暂被机械臂遮挡。
- 两个相似实例会在连续帧里交换排序。

一个常见做法是用 `bbox IoU + mask IoU + 质心距离` 做轻量关联：

```text
上一帧 track_07  (cup, center=(520, 340), IoU ref)
          |
          v
当前帧候选 A / B / C
  -> 先按 label 过滤
  -> 再按 IoU 和中心距离匹配
  -> 匹配失败则新建 track 或标记 lost
```

## 一个可落地的跟踪记录

```yaml
tracked_mask:
  track_id: cup_track_07
  object_id: cup_candidate_01
  label: red mug
  bbox_xyxy: [410, 206, 611, 472]
  mask_ref: runs/04-perception/masks/cup_track_07_t023.png
  center_xy: [510.3, 338.7]
  temporal_iou: 0.82
  valid_depth_ratio: 0.91
  quality:
    area_px: 28431
    component_count: 1
    edge_contact_ratio: 0.77
  failure_code: null
```

只要你能把这些字段持续记下来，后面做失败分析会轻松很多。

## 何时应该拒绝执行

| 条件 | 为什么不能继续 |
|--- | --- |
| `valid_depth_ratio` 很低 | 下游没有足够 3D 证据 |
| `temporal_iou` 持续波动 | 目标位置不稳定，抓取点会抖 |
| 多实例混淆 | 可能抓错物体 |
| mask 与 bbox 互相矛盾 | 感知链内部不一致 |
| 连续多帧都失败 | 应升级为重新观察或切换策略 |

“拒绝执行”不是系统失败，而是系统在正确地表达不确定。

## 失败码建议

| 失败码 | 触发条件 | 推荐动作 |
|--- | --- | --- |
| `mask_too_small` | 面积低于最小可执行阈值 | 重观察或改视角 |
| `depth_inconsistent` | 有效深度比例低、方差异常 | 换角度或启用几何先验 |
| `instance_merge` | 一个 mask 覆盖多个物体 | 降低 prompt 范围或启用 tracker |
| `temporal_flicker` | 连续帧 IoU 过低 | 等待稳定、做平滑 |
| `occluded_target` | 遮挡比例过高 | 换视角或调整机械臂让路 |

## 自检问题

1. 为什么“单帧看起来很好”的 mask 仍然可能不适合抓取？
2. 当 mask 面积正常、置信度也高，但 `valid_depth_ratio` 很低时，会更倾向把问题归到视觉模型还是几何链路？
3. 如果两个相似盒子在相邻帧里频繁交换 id，最先需要补的是更强的分类器还是基本 tracking 逻辑？

## 练习

### [观察] 用日志区分四种失败

1. 找一段桌面抓取视频或连续图像。
2. 为每一帧记录 `area_px`、`valid_depth_ratio`、`temporal_iou`。
3. 人工挑出至少 4 帧，分别标注为误检、漏检、实例混淆、时序抖动中的一种。

完成后，可以先用下面几条检查这一部分是否已经到位：
- 能给每一类失败写出一个可观察证据，而不是只写“模型不准”。
- 能指出哪一类问题最可能通过重观察解决。

### [复现] 为分割结果加一层质量门禁

1. 任选一份 GroundingDINO + SAM 输出结果。
2. 为每个实例计算面积、组件数和有效深度比例。
3. 用本页 gate 逻辑给出 `failure_code` 或 `null`。
4. 统计被放行与被拒绝的比例，并解释原因。

完成后，可以先用下面几条检查这一部分是否已经到位：
- 每个实例都能输出质量指标与门禁结果。
- 至少有一个样本被明确拒绝，并且你能解释拒绝的工程原因。

## 导航

- 上一节：[GroundingDINO 与 SAM](02-groundingdino-sam.md)
- 返回本章：[感知与三维视觉](../README.md)
- 下一节：[位姿估计](05-pose-estimation.md)

