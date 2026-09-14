# 感知输出规范

> 难度：[中级] | 预计用时：70 分钟
> 先修：[感知接口](01-perception-interface.md)
> 建议：把这一页当成“整章所有结果最终如何汇总”的正式定义页。

目标：定义感知模块向规划器、控制器、策略模型和评测系统输出什么结构化 observation，以及这些字段的单位、坐标系、时效性和可选性。

## 先建立直觉

如果前面这些章节都在生产“各种感知结果”，那么感知输出规范做的事情就是：

**把这些异构结果装进同一份可消费、可审计、可回放的数据包。**

它很像物流里的面单：

- 上游做了很多事，但下游只看面单能不能读懂。
- 面单写对了，货物才能被送到正确地点。
- 面单写错了，哪怕货物本身是好的，系统仍然会出错。

在机器人里也是一样：

- 模型名字不重要，字段语义重要。
- 局部算法细节不重要，坐标系、时效性和失败状态重要。

## 先弄懂 frame_graph 是什么

这一页想先讲透的核心概念，是 `frame_graph`。

我们可以把它理解成：  
系统当前承认的坐标系关系图。

例如：

```yaml
frame_graph:
  world: world
  robot_base: panda_link0
  camera: wrist_color_optical_frame
  gripper: gripper_tcp
```

为什么这很重要？

因为感知结果不是都在同一个坐标系里产生的：

- 像素、bbox、mask 天然属于图像或相机视角。
- 点云最初通常在相机坐标系。
- 抓取目标往往要落到 `robot_base` 或 `world`。
- 接触事件常常与 `gripper_tcp` 相关。

如果没有一份统一的坐标关系说明，下游就必须猜这些结果之间如何变换，而这通常是不安全的。

## 感知输出规范到底要解决什么问题

下面这些问题，几乎就是 contract 存在的理由：

| 没有 contract 时的混乱 | contract 要提供的约束 |
|---|---|
| `bbox` 到底是像素坐标还是归一化坐标 | 字段格式和单位必须明确 |
| pose 是 `camera` frame 还是 `base` frame | `frame_id` 必须明确 |
| `confidence` 到底是检测分数还是融合质量分 | 分数字段语义必须明确 |
| 当前结果是现在的，还是 150 ms 前的旧值 | 时间戳和时效性必须明确 |
| 失败时到底是空值、旧值还是错误状态 | 失败合同必须明确 |

很多系统一开始“能跑”，但一旦要做真机闭环、回放调试或大规模评测，就会被这些接口不清拖垮。

## 一份好的 observation 至少分几层

推荐把 observation 分成下面几个层次：

```text
perception_observation
├── header
│   ├── schema_version
│   ├── timestamp
│   └── frame_graph
├── objects[]
│   ├── 语义: label / query / bbox / mask
│   ├── 几何: pose / pointcloud_ref / covariance
│   ├── 质量: confidence / staleness_ms / failure_code
│   └── 可选: affordance / symmetry / tracking info
├── contacts[]
└── environment
    ├── planes / collision objects
    ├── calibration status
    └── depth health
```

这种分层的好处是：

- 对象级信息不会和环境级信息混在一起。
- 同一对象的语义、几何、质量字段能集中查看。
- 后续 planner、policy、evaluator 可以各取所需。

## 最小 schema 示例

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
      covariance_ref: runs/04-perception/cov/mug_01.npy
      staleness_ms: 37
      failure_code: null
  contacts:
    - type: grasp_contact
      frame_id: gripper_tcp
      force_norm_n: 12.4
      confidence: 0.83
  environment:
    table_plane_frame: panda_link0
    depth_health: nominal
```

这份结构非常重要，因为它相当于把本章前面所有内容压缩成了一次“正式交付”。

## 哪些字段是刚需

| 字段 | 为什么必须有 |
|---|---|
| `schema_version` | 保证历史样本、回放和新代码能对齐 |
| `timestamp` | 让观测可以和动作、视频、机器人状态对齐 |
| `frame_id` / `frame_graph` | 保证几何量有明确语义 |
| `confidence` 或质量量 | 让下游能做风险控制 |
| `failure_code` | 让失败不会被静默吞掉 |

如果这些字段缺失，系统也许还能“输出结果”，但很难安全、稳定、可复用。

## Planner、Policy、Evaluator 各自最关心什么

这页最重要的系统观之一是：

同一份 observation，要同时服务多个下游。

| 下游 | 它最关心的字段 |
|---|---|
| Planner | pose、pointcloud、collision objects、affordance、frame |
| Controller / Supervisor | 接触事件、力学状态、目标时效性 |
| Policy / VLA | 对象列表、视觉状态、语言条件、历史观测 |
| Evaluator | timestamp、failure_code、success evidence、版本信息 |

这也是为什么设计 contract 时不能只想着“我这个检测模块想输出什么”，而要想着“系统里的其他人如何消费”。

## 时效性为什么必须进入 contract

感知结果不是永久真值。

一个最简单的例子：

- 机器人移动中，100 ms 前的目标 pose 可能已经过时。
- 夹爪闭合时，上一帧的 mask 已经不能代表当前接触状态。

所以 contract 通常至少要表达：

| 字段 | 作用 |
|---|---|
| `timestamp` | 结果生成时间 |
| `staleness_ms` | 距离当前控制时刻已经过去多久 |
| `valid_until`（可选） | 结果建议在多久内失效 |

没有时效性字段的感知输出，在动态系统里风险很高。

## 最小代码：读懂 observation demo

直接运行：

```bash
python labs/04-perception/perception_observation_demo.py
```

会看到一份合成 observation 被写到：

`runs/04-perception/observation_demo.json`

这个 demo 最值得观察的，不是 JSON 格式本身，而是它怎样把：

- 物体语义
- 物体 pose
- 置信度
- 陈旧度
- 失败码
- 接触事件

统一放到一份 observation 里。

它还演示了一个重要事实：

同一个 observation 中，不同对象完全可能得到不同的上层动作建议。这就是 contract 的价值所在。

## 常见设计错误

| 错误 | 后果 |
|---|---|
| pose 有数值但没有 `frame_id` | 数值看起来正常，但几何语义不明 |
| `confidence` 没有定义来源 | 不同模块之间分数不可比较 |
| 失败样本被直接删掉 | 无法做失败分析和数据清洗 |
| 图像分辨率变了但 bbox 语义没同步 | 历史数据不可复现 |
| mask 和 bbox 源头不一致却没有说明 | 下游不知道该信谁 |

## 自检问题

- 为什么说 observation contract 的关键不是“字段多”，而是“字段语义稳定”？
- 为什么 `frame_id` 往往比某个模型名字更重要？
- 如果一份 observation 有 pose 但没有时间戳，在动态执行里会造成什么问题？

## 练习

### [观察] 审查现有感知输出

任选一份已有的检测、分割或 pose 输出，检查它是否具备：

- `timestamp`
- `frame_id`
- `confidence`
- `failure_code`

读到这里时，我们最好已经能说明每个缺失字段会让哪个下游难以工作。

### [复现] 写一份统一 schema

为桌面抓取任务写一份统一 observation schema，至少覆盖：

- 一个对象
- 一个环境字段
- 一个接触字段

读到这里时，这份 schema 最好已经能同时让 planner 和 evaluator 消费。

## 导航

- 上一节：[感知接口](01-perception-interface.md)
- 下一节：[置信度与失败码](03-confidence-failure-code.md)
- 返回本章：[感知与三维视觉](../README.md)

