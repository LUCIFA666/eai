# 感知接口

> 难度：[中级] | 预计用时：60 分钟
> 先修：[触觉、力觉与接触观测](../04-interactive-perception/05-tactile-force-sensing.md)
> 建议：把本页当成整个第四章的收束页来看。

目标：把标定、点云、语义、位姿、可供性和触觉结果封装成下游规划器、控制器、策略模型和评测系统都能稳定消费的统一接口。

## 先建立直觉

前面这些章节做的事情，都是在产生各种类型的观测结果：

- 相机内参和外参
- 点云和深度
- 场景重建与地图
- bbox 和 mask
- 6D pose
- affordance 区域和接触点
- 触觉事件和力觉证据
- 机器人在环境中的定位状态

如果这些结果各自为政，系统很快就会陷入一种常见混乱：

- 有的结果在 `camera` frame，有的在 `base` frame。
- 有的字段有时间戳，有的没有。
- 有的失败返回空值，有的失败继续输出旧结果。
- 有的模块说 `score`，有的模块说 `confidence`，但没人知道它们能不能比较。

感知接口这一节做的，就是把前面所有结果统一翻译成一种“上下游都能达成一致”的数据语言。

## 什么叫 contract，什么叫 schema

**contract** 可以理解成接口契约，也就是上下游之间对“输入输出必须长什么样”的共同约定。  
**schema** 是这个约定的具体结构定义。

为什么这在机器人里特别重要？因为机器人不是单模型系统，而是多模块协作系统。只要接口语义不稳定，错误就会从局部变成系统级问题。

比如：

- 检测输出的是当前帧 bbox，但 pose 还是上一帧的旧结果。
- 规划器默认 pose 在 `base` frame，感知实际给的是 `camera` frame。
- 失败时上游返回 `null`，下游却把上一次缓存结果继续当新结果使用。

这些问题通常不是算法本身不够强，而是接口没有设计清楚。

## 一份好的 observation 至少要回答什么

从下游视角看，一份感知 observation 至少应该能回答：

- 这条观测是什么时候生成的？
- 它来自哪个传感器或哪个坐标系？
- 它描述的是哪个对象或哪个接触事件？
- 结果的质量如何？
- 如果它不可用，原因是什么？
- 下游应该继续执行、重观察、降级还是终止？

如果回答不完整，下游就只能“猜”，而机器人系统最不该依赖的就是猜。

## 一个最小 observation schema

```yaml
perception_observation:
  schema_version: perception_observation_v1
  timestamp: 2026-05-29T10:50:00.000Z
  frame_graph:
    world: world
    robot_base: panda_link0
    camera: wrist_color_optical_frame
    gripper: gripper_tcp
  objects:
    - object_id: mug_01
      label: red mug
      bbox_xyxy: [412, 208, 610, 470]
      mask_ref: runs/04-perception/masks/mug_01.png
      pose:
        frame_id: panda_link0
        xyz_m: [0.43, -0.12, 0.08]
        quat_xyzw: [0.0, 0.0, 0.71, 0.70]
      confidence: 0.84
      staleness_ms: 37
      failure_code: null
  contacts:
    - type: grasp_contact
      frame_id: gripper_tcp
      force_norm_n: 12.4
      confidence: 0.83
```

沿着这份结构往回看，会发现本章前面的内容几乎都在这里汇合。也就是说，第四章真正的终点不是“记住更多模型名”，而是“学会如何组织一份机器人可用的 observation”。

## 哪些字段最容易被漏掉，但最不能漏

| 字段 | 常见漏法 | 后果 |
|---|---|---|
| `frame_id` | 默认大家都知道在哪个坐标系里 | 直接导致执行方向错误 |
| `timestamp` | 只在日志外层记，不写到对象级结果里 | 无法判断观测是否过时 |
| `schema_version` | 不写版本 | 历史数据难以回放和比较 |
| `failure_code` | 失败直接留空或静默复用旧值 | 风险会被悄悄传给下游 |
| `confidence` 语义说明 | 只给一个分数，不解释含义 | 阈值无法统一制定 |

很多系统前期能跑起来，但一旦开始做真机实验、回放训练或大规模评测，就会被这些“当初省掉的小字段”拖住。

## 最小代码：看看一份完整 observation 长什么样

仓库里的 [labs/04-perception/perception_observation_demo.py](../../../labs/04-perception/perception_observation_demo.py) 会构造一份合成 observation，并输出：

- 两个对象
- 各自的 pose、置信度、陈旧度和失败码
- 一个接触事件
- 一个简单的上层决策映射

其中很值得注意的部分是：

```python
if obj.get("failure_code") in ("frame_mismatch", "extrinsic_missing"):
    return "abort"
if obj.get("failure_code") in ("no_detection", "track_lost"):
    return "reobserve"
```

这说明感知接口不仅是在“存数据”，也是在为上层动作决策提供稳定输入。

## 为什么这一节和规划、策略、评测都直接相关

同一份 observation 会被很多模块消费，但它们关注的重点不同：

| 下游模块 | 最关心什么 |
|---|---|
| 规划器 | pose、collision object、可供性、frame |
| 控制器 | 接近目标、接触事件、力学状态 |
| 策略模型 | 对象列表、视觉状态、历史观测 |
| 数据系统 | 一致结构、可回放、可训练 |
| 评测系统 | 成功证据、失败码、时序可追溯性 |

如果没有统一 contract，不同模块就会各自发明一套字段，最后很难复用。


## 为什么版本化不是“形式主义”

当系统开始迭代后，你几乎一定会遇到这些情况：

- 加了新字段，比如 `staleness_ms`。
- 改了 `pose` 的表示方式。
- 对 `confidence` 的含义重新定义。
- 把 `mask_ref` 从相对路径改成对象内嵌索引。

如果没有 `schema_version`，那你以后根本无法判断：

- 一份旧日志还能不能被新评测脚本正确读取。
- 一批历史训练样本和现在的在线结果是不是同一种结构。
- 某次性能波动是模型变化引起的，还是接口变化引起的。

所以版本化不是文档癖好，而是让系统能持续演化的基本条件。

## 本节和两个子页面的关系

- [感知输出规范](02-perception-output-schema.md) 负责给出更完整的结构化定义。
- [置信度与失败码](03-confidence-failure-code.md) 负责讲清“结果不确定”时系统应该怎样表达和决策。

## 自检问题

- 为什么说感知接口是整个本章的“收束页”？
- 为什么 `frame_id`、`timestamp` 和 `failure_code` 往往比某个单独模型分数更重要？
- 为什么版本化对真机实验、回放和评测都很关键？

## 练习

### [观察] 跑一次 observation demo

运行：

```bash
python labs/04-perception/perception_observation_demo.py
```

观察对象、接触事件以及最终动作建议。

读到这里时，我们最好已经能指出 demo 里“感知结果”和“上层决策”之间的连接点。

### [复现] 设计一份你自己的最小感知 schema

以“抓取桌面红杯子”为例，写一份最小 observation，至少包含：

- 对象语义
- 几何位置
- 坐标系
- 时间戳
- 置信度
- 失败状态

读到这里时，写出的结构最好已经可以被一个 planner 安全消费，而不只是适合人眼查看。

## 导航

- 上一节：[语义地图与 3D 场景图](../05-spatial-localization-and-semantic-maps/02-semantic-scene-graphs.md)
- 下一节：[感知输出规范](02-perception-output-schema.md)
- 返回本章：[感知与三维视觉](../README.md)
