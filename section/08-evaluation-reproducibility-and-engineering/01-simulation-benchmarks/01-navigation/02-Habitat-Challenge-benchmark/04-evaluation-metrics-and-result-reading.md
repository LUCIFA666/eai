# 2.4 评测指标与结果阅读

## 目标

Habitat Challenge 的评测指标主要用于衡量 agent 是否完成任务、路径是否高效，以及在不同任务中是否表现稳定。不同任务使用的指标不完全相同，但 Success、SPL 和 SoftSPL 是理解 Habitat 导航任务时最常见的指标。

本节主要介绍 Habitat Challenge 中常见指标的含义，以及阅读 leaderboard 或 baseline 结果时需要注意的问题。

## Success：任务是否完成

Success 表示 episode 是否成功完成。不同任务对 success 的定义不同。

在 PointNav 中，success 通常表示 agent 是否到达目标点附近并执行停止动作；在 ObjectNav 中，success 表示 agent 是否找到目标类别物体并在合适距离内停止；在 Rearrangement 中，success 则可能表示目标物体是否被移动到指定目标位置附近。

可以理解为：

```text
Success 关注的是：
任务最终是否达到成功条件
```

它是最直接的指标，但也是比较严格的指标。因为 agent 可能已经接近目标，却因为没有正确停止或没有满足细节条件而被记为失败。

## SPL：路径效率

SPL 是 Success weighted by Path Length，即考虑路径长度的成功率指标。

它不仅看 agent 是否成功，还看 agent 的路径是否接近最短路径。

可以理解为：

```text
成功并且路径短
-> SPL 高

成功但绕路严重
-> SPL 降低

没有成功
-> SPL 为低值或 0
```

SPL 的作用是避免模型只靠随机探索最终碰到目标，而忽略路径效率。

例如，一个 agent 虽然最终找到目标，但绕了很远的路，说明它的导航策略并不高效。在真实机器人中，这会带来时间成本、能耗和碰撞风险。

## SoftSPL：连续化的路径效率指标

SoftSPL 可以看作 SPL 的软化版本。普通 SPL 对成功条件比较严格，只有成功 episode 才能获得路径效率奖励；SoftSPL 则更关注 agent 与目标之间距离是否有所缩短。

可以理解为：

```text
SPL：
成功后再看路径效率

SoftSPL：
即使没有完全成功，也能反映是否接近了目标
```

这对于分析失败 episode 很有用。Agent 可能没有达到严格成功条件，但已经显著接近目标。SoftSPL 可以反映这种中间进展。

## ObjectNav 结果阅读

ObjectNav 的结果不能只看 Success，还要结合 SPL 或 SoftSPL。

常见情况包括：

| 结果现象 | 可能说明 |
| --- | --- |
| Success 高，SPL 高 | agent 能高效找到目标物体 |
| Success 高，SPL 低 | agent 能找到目标，但路径绕远 |
| Success 低，SoftSPL 较高 | agent 能接近目标，但停止判断或目标确认不稳定 |
| Success 低，SoftSPL 低 | agent 可能搜索策略、语义识别或路径规划都有问题 |

ObjectNav 的难点在于目标位置未知。Agent 需要结合物体识别、场景常识和主动探索，才能找到目标物体。

## ImageNav 结果阅读

ImageNav 的评价也关注 agent 是否到达目标实例附近，但它比 ObjectNav 更强调实例级匹配。

ObjectNav 中，找到任意符合类别的物体可能就足够；ImageNav 中，agent 需要找到目标图像对应的具体实例。

因此，如果 ImageNav 表现明显低于 ObjectNav，可能说明模型存在：

```text
实例区分能力不足
目标图像与当前视角匹配不稳定
不同视角下外观变化处理不好
场景中相似物体干扰较强
```

ImageNav 结果能够反映模型是否真正理解目标图像，而不是只识别物体类别。

## Rearrangement 结果阅读

Rearrangement 的评价比导航任务更复杂。因为 agent 不仅要到达目标位置，还要移动物体并改变环境状态。

结果分析时需要关注：

```text
是否找到目标物体
是否成功抓取
是否移动到目标区域
是否完成放置
是否打开或关闭必要容器
是否在时间限制内完成
```

一个 rearrangement 任务失败，可能不是导航失败，而是抓取失败、放置失败或任务规划失败。

例如：

```text
导航成功但没有抓到物体
抓取成功但放错位置
知道目标位置但无法打开容器
完成部分步骤但超过最大步数
```

因此，重排任务的结果更适合拆阶段分析，而不是只看最终 success。

## Leaderboard 的阅读方式

Habitat Challenge 通常会通过 EvalAI 或官方页面提供 leaderboard。阅读 leaderboard 时需要注意：

```text
任务年份是否一致
任务类型是否一致
数据集版本是否一致
是否使用相同传感器
是否使用相同机器人配置
是否是 test-standard 或 test-challenge 结果
```

不同年份的 challenge 可能修改任务定义、数据集版本、agent 配置或评测细节，因此不能直接把不同年份的分数简单比较。

例如，2023 Navigation Challenge 使用的 ObjectNav 和 ImageNav 设置与早期 PointNav / ObjectNav challenge 并不完全相同。Rearrangement Challenge 又属于移动操作任务，不能和纯导航任务直接用同一套标准比较。

## Baseline 结果的分析方式

阅读 baseline 时，不要只看最高分，而要看方法在哪些能力上表现好、在哪些任务上失败。

可以按照下面思路分析：

```text
ObjectNav 表现好：
说明语义目标搜索和基础导航较强

ImageNav 表现好：
说明实例级视觉匹配能力较强

Rearrangement 表现好：
说明移动操作、抓取放置和任务规划较强

SPL 高：
说明路径比较高效

SoftSPL 高但 Success 低：
说明 agent 能接近目标，但最终完成判断或停止动作不稳定
```

这种分析方式比单纯排名更有用。因为 Habitat Challenge 的目标不是只找一个分数最高的方法，而是帮助研究者判断 embodied agent 的具体能力边界。

## 结果与环境配置的关系

Habitat 的评测结果和环境配置密切相关。不同传感器、机器人、数据集版本和渲染设置都会影响结果。

例如：

```text
使用 RGB-D 通常比只使用 RGB 提供更多空间信息
使用 GPS+Compass 会降低定位难度
更高分辨率图像可能提升识别能力，但增加计算成本
不同场景数据集会改变视觉风格和物体分布
不同机器人配置会改变相机高度和动作空间
```

因此，在比较方法时，需要确认输入条件是否一致。如果一个方法使用了额外传感器，而另一个方法没有使用，就不能简单认为分数更高的方法一定更强。

## 本节小结

Habitat Challenge 的指标主要围绕任务完成和路径效率展开。Success 衡量任务是否完成，SPL 衡量成功路径是否高效，SoftSPL 则帮助分析未完全成功但接近目标的情况。

对于 ObjectNav、ImageNav 和 Rearrangement 等任务，结果分析需要结合任务特点。导航任务更关注目标搜索和路径效率，ImageNav 更关注实例匹配，Rearrangement 则进一步引入抓取、放置和任务规划。阅读 leaderboard 时，需要始终注意任务年份、数据集版本、传感器配置和评测协议是否一致。
