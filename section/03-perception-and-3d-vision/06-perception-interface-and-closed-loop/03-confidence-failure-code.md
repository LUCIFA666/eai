# 置信度与失败码

> 难度：[中级] | 预计用时：60 分钟
> 先修：[感知输出规范](02-perception-output-schema.md)
> 建议：这一页最好从“上层要怎么决策”这个角度来读。

目标：让感知模块能够显式表达“不确定”“已失败”“建议重试”这三类不同状态，而不是把坏结果静默传给下游。

## 先建立直觉

这一页最重要的一句话是：

**置信度和失败码不是一回事，而且谁也不能替代谁。**

我们可以把它们粗略类比成：

- `confidence`：天气预报里的“降雨概率”。
- `failure_code`：医生写下的“具体诊断结论”。

前者告诉你“我有多大把握”。  
后者告诉你“具体坏在哪”。

机器人系统如果只有其中一个，都会很难做对决策：

- 只有分数，没有原因：不知道该重试、降级还是中止。
- 只有失败标签，没有置信信息：不知道边界样本能否保留作候选。

## 先弄懂 staleness 和 degrade

这两个词经常和置信度一起出现，但语义并不一样。

### `staleness_ms`

表示这条感知结果从生成到当前控制时刻已经过去多久。

它回答的问题不是“对不对”，而是：

> “这条结果现在还新鲜吗？”

即使一份 pose 非常准确，只要它太旧了，在动态系统里也可能不该继续执行。

### `degrade`

表示下游不把这条结果当成“已确认可执行”，而是降级成“可以参考的候选”。

例如：

- 可以保留它做下一轮重观察的候选。
- 可以保留它做多视角排序。
- 但不直接用它驱动危险动作。

所以 `degrade` 常常是介于“继续执行”和“彻底中止”之间的一种折中动作。

## 先分清五种常被混在一起的量

| 字段 | 它真正表达什么 |
|---|---|
| `confidence` | 我有多确信这个结果是对的 |
| `covariance` | 如果是几何量，它的不确定性分布是什么 |
| `valid_ratio` | 原始观测里有多少有效证据 |
| `staleness_ms` | 这条结果是不是已经过期 |
| `failure_code` | 如果它不可用，具体坏在哪里 |

把这些量全部挤进一个 `score=0.72`，几乎一定会让下游决策变得含糊。

## 为什么高风险错误必须有 failure code

设想下面两种情况：

1. `confidence=0.45`，但所有坐标系都正确。
2. `confidence=0.92`，但 `frame_mismatch` 被触发。

你觉得哪一个更危险？

在大多数机器人系统里，第二种更危险。因为：

- 第一种也许只是“不够确定”，还可以重观察或降级。
- 第二种则意味着几何语义已经坏了，继续执行可能直接朝错误位置动作。

这就是为什么某些错误不能只靠低置信度表达，而必须有明确失败码：

- `frame_mismatch`
- `extrinsic_missing`
- `intrinsic_resolution_mismatch`

这些都属于“几何语义层损坏”，通常应优先触发阻塞逻辑。

## 推荐的失败码分层

建议至少按链路来源分层：

```text
failure_code
├── detection/*
├── segmentation/*
├── depth/*
├── pose/*
├── tracking/*
└── calibration/*
```

这样日志一眼就能看出问题来自哪一层，而不是所有失败都叫 `perception_failed`。

## 一个建议清单

| 模块 | 失败码 | 含义 | 上层建议 |
|---|---|---|---|
| detection | `no_detection` | 没找到目标 | `reobserve` |
| detection | `ambiguous_target` | 找到多个相似目标 | `degrade` 或请求消歧 |
| segmentation | `mask_fragmented` | mask 碎裂严重 | `reobserve` |
| depth | `depth_invalid` | 有效深度比例过低 | `reobserve` 或换视角 |
| pose | `pose_unstable` | 连续帧姿态抖动大 | `refresh` 或延迟执行 |
| tracking | `track_lost` | 时序关联丢失 | `reobserve` |
| calibration | `frame_mismatch` | 坐标关系损坏 | `abort` |

## 阈值为什么不能一刀切

同样是 `confidence=0.65`，在不同任务里的含义完全不同：

| 任务 | 对低置信的容忍度 |
|---|---|
| 抓取锋利工具 | 很低，宁可不抓 |
| 普通桌面抓取 | 中等，可重观察 |
| 离线数据候选生成 | 较高，可人工复核 |
| 粗定位搜索 | 更高，可保留多个候选 |

所以不要机械地问：

> “0.7 到底够不够？”

更好的问题是：

> “误执行这类任务的代价有多高？”

## 一份更工程化的参考阈值表

| 风险等级 | 示例 | 建议阈值 | 动作倾向 |
|---|---|---|---|
| 高风险 / 不可逆 | 抓尖锐工具、拉门、开抽屉 | `>= 0.85` | 低于阈值直接拒绝或重观察 |
| 中风险 / 可恢复 | 普通抓取、放置 | `0.65 - 0.85` | 可重观察或降级 |
| 低风险 / 可人工复核 | 离线候选生成 | `0.40 - 0.65` | 保留候选，不直接执行 |
| 粗筛选 / 搜索 | 多视角区域提案 | `>= 0.30` | 用于排序，不直接动作 |

注意：这张表不是定律，只是一个工程起点。真正的阈值仍然必须通过具体设备、场景和任务验证。

## 一个简单但实用的决策表

| 条件 | 推荐动作 |
|---|---|
| `failure_code = frame_mismatch` | `abort` |
| `failure_code = no_detection` | `reobserve` |
| `staleness_ms > budget` | `refresh` |
| `confidence < min_conf` 且无严重失败 | `degrade` |
| `pose_covariance` 过大 | 允许粗动作，不允许精插入 |

会发现，真正的决策逻辑通常不是“只看一个分数”，而是“先看失败类型，再看分数和时效性”。

## 最小代码：把状态变成动作

下面这种逻辑就很接近真实系统：

```python
def choose_perception_action(confidence, failure_code, staleness_ms):
    if failure_code in {"frame_mismatch", "extrinsic_missing"}:
        return "abort"
    if failure_code in {"no_detection", "track_lost"}:
        return "reobserve"
    if staleness_ms > 100:
        return "refresh"
    if confidence < 0.70:
        return "degrade"
    return "execute"
```

这段代码最值得记住的原则是：

**失败类型优先于分数。**

## 为什么 calibration 相关失败要单独处理

下面几类问题和“模型看错了”完全不是一回事：

- `frame_mismatch`
- `extrinsic_missing`
- `intrinsic_resolution_mismatch`

它们意味着几何语义本身已经坏了。

| 错误类型 | 为什么危险 |
|---|---|
| `frame_mismatch` | pose 可能落在完全错误的位置 |
| `extrinsic_missing` | 无法把相机结果转换到机器人基座 |
| `intrinsic_resolution_mismatch` | bbox、depth、pose 可能一起偏移 |

这类错误通常不适合“再试一次看看”，而应进入阻塞和报警逻辑。

## 一份可执行的 observation 片段

```yaml
object_status:
  object_id: drawer_handle_01
  confidence: 0.68
  covariance_ref: runs/04-perception/cov/handle.npy
  staleness_ms: 24
  failure_code: pose_unstable
  retry_policy:
    action: reobserve
    max_retry: 2
```

这个例子展示了一个很重要的思想：

失败字段不是为了“写日志好看”，而是为了真正驱动上层动作。

## 自检问题

- 为什么高风险错误不能只靠低 `confidence` 来表达？
- 如果 `confidence` 很高，但触发了 `frame_mismatch`，下游应不应该继续执行？为什么？
- 为什么 `staleness_ms` 不能和 `confidence` 混成一个综合分？

## 练习

### [观察] 为失败案例贴标签

任选 5 个感知失败样本，分别判断它们属于：

- detection
- segmentation
- depth
- pose
- tracking
- calibration

并为每个样本指定：

- 一个失败码
- 一个推荐动作：`retry / degrade / abort`

读到这里时，我们最好已经能至少指出一个“应该重试”和一个“必须阻塞”的样本。

### [复现] 写一个 retry policy 表

为桌面抓取任务定义至少 6 个失败码，并给每个失败码分配：

- `retry`
- `degrade`
- `abort`

中的一种动作。

读到这里时，这份表最好已经可以直接交给 supervisor 实现。

## 导航

- 上一节：[感知输出规范](02-perception-output-schema.md)
- 返回本章：[感知与三维视觉](../README.md)

