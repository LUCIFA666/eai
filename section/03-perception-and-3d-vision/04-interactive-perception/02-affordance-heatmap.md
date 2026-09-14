# Affordance Heatmap

> 难度：[中级] | 预计用时：55 分钟
> 先修：[可供性与交互区域](01-affordance-grounding.md)

目标：说明可供性如何从”识别物体”推进到”判断哪里能抓、按、拉、放”，并落成可消费的 2D 区域表示。

## 先弄懂 action_type 有哪些

**action_type（动作类型）**：描述要对物体做什么。常见类型：

| action_type | 动作 | 典型场景 |
|---|---|---|
| `grasp` | 抓取 | 从上方或侧面夹住物体 |
| `push` | 推动 | 把物体推到目标位置 |
| `pull` | 拉动 | 拉抽屉门、拉把手 |
| `press` | 按压 | 按按钮、压开关 |
| `place` | 放置 | 把物体放到目标位置 |
| `insert` | 插入 | 把物体插进孔或槽 |

同一个物体可以有多张 heatmap，取决于你想执行什么动作。

## 本页目标

这一页读完后，我们希望能一起把下面几件事说明白：

- 解释 affordance heatmap 与普通分割 mask 的区别。
- 为 grasp、push、pull、press、place 设计不同的 heatmap 语义。
- 判断 heatmap 输出何时足以驱动下游，何时仍需 3D 几何补充。
- 写出 heatmap 与 mask、pose、planner 之间的接口。

## heatmap 和 mask 到底差在哪

| 输出 | 回答的问题 |
|---|---|
| object mask | 哪些像素属于这个物体 |
| affordance heatmap | 物体上的哪些像素更适合当前动作 |

```text
mask = "这是杯子"
heatmap = "杯子上这一圈更适合抓"
```

同一个物体可以有多张 heatmap：

| 物体 | 动作 | 可能高亮区域 |
|---|---|---|
| 杯子 | grasp | 侧壁中段 |
| 杯子 | place | 杯底附近支撑区域 |
| 抽屉 | pull | 把手 |
| 按钮面板 | press | 按钮中心 |

## 一个最小输出结构

```yaml
affordance_heatmap:
  object_id: mug_01
  action_type: grasp
  image_size: [1280, 720]
  heatmap_ref: runs/04-perception/heatmaps/mug_grasp.npy
  topk_pixels:
    - [532, 318, 0.93]
    - [528, 321, 0.91]
  frame_id: camera_color_optical_frame
  confidence: 0.79
  failure_code: null
```

这里的 `topk_pixels` 很有用，因为很多下游并不需要完整热图，而只需要几个最高置信的候选点。

## heatmap 的输入一般有哪些

| 输入 | 作用 |
|---|---|
| RGB | 提供外观和边缘 |
| object mask / bbox | 限定作用对象 |
| action text / task id | 指明“抓”还是“按” |
| depth / pose（可选） | 让区域和几何约束更一致 |

所以 affordance 不只是视觉分类，它天然依赖“当前打算做什么动作”。

## 为什么 heatmap 不能直接替代 3D

2D 热图很适合表达“像素上哪儿更好”，但 planner 最终常常要的是：

- 3D 接触点；
- 法向与接近方向；
- gripper width 或碰撞约束。

因此最常见的组合是：

```text
heatmap peak pixel
   + depth
   + camera intrinsics
   + extrinsics
   -> 3D contact candidate
```

## 设计标签时要避免的坑

| 坑 | 后果 |
|---|---|
| 只标“目标物体”，不标动作类型 | 同一物体多动作无法区分 |
| heatmap 太平 | 下游难选出明确接触点 |
| 只看语义，不看碰撞 | 高亮区域物理上不可达 |
| 不和 mask 约束一致 | 高亮跑到物体外部 |

## 一个简单的后处理思路

```python
# 从 heatmap 选接触候选像素
def select_affordance_peaks(heatmap, mask, threshold=0.7):
    ys, xs = (heatmap >= threshold).nonzero()
    return [(int(x), int(y), float(heatmap[y, x])) for y, x in zip(ys, xs) if mask[y, x]]

# 预期输出:
# [(532, 318, 0.93), (528, 321, 0.91), ...]
```

这段逻辑强调两点：候选像素必须高于动作阈值，还必须落在目标 mask 内。

## 自检问题

1. 为什么 affordance heatmap 必须带 `action_type`？
2. 如果 heatmap 在抽屉整个面板上都很高，这对下游意味着什么问题？
3. 为什么说 heatmap 很适合人工标注和学习，但通常不是最终 planner 输入？

## 练习

### [观察] 为同一物体画两张不同动作 heatmap

1. 选择杯子或抽屉。
2. 画出该物体在两种动作下的可交互区域，例如 `grasp` 与 `place`，或 `pull` 与 `push`。

完成后，可以先用下面几条检查这一部分是否已经到位：
- 两张图的高亮区域明显不同。
- 能解释动作改变为什么会改变热图语义。

### [复现] 写一份 heatmap contract

1. 为一个任务定义 `affordance_heatmap` schema。
2. 至少包含 `object_id`、`action_type`、`heatmap_ref`、`topk_pixels`、`confidence`。
3. 补一句说明后续如何转成 3D contact point。

完成后，可以先用下面几条检查这一部分是否已经到位：
- schema 足以让下游取出候选像素。
- 能指出转 3D 还缺哪几个几何字段。

## 导航

- 上一节：[可供性与交互区域](01-affordance-grounding.md)
- 返回本章：[感知与三维视觉](../README.md)
- 下一节：[3D Contact Point](03-contact-point.md)

