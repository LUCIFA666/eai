# 感知接口与闭环

目标：把前面各节产生的几何、语义、位姿、接触和地图结果统一打包成可执行、可追责、可触发重观察的 observation contract。

前面几节解决的是“能不能看见、能不能对齐、能不能估计、能不能接触”。这一节解决的是最后一个系统问题：

**这些结果怎样被下游稳定消费？**

如果没有统一接口，再强的模块也很难形成稳定闭环。常见问题包括：

- 坐标系写不清，planner 拿错 frame。
- 结果过期却没有显式时效字段。
- 失败时静默复用旧值，下游误以为一切正常。
- 需要重观察时没有明确触发机制。

## 这一节的主线

```text
heterogeneous perception results
  -> unified schema
  -> confidence and failure codes
  -> action policy for bad observations
  -> active re-observation
```

对应页面分工如下：

- [感知接口](06-perception-interface-and-closed-loop/01-perception-interface.md) 负责建立 contract 的系统视角。
- [感知输出规范](06-perception-interface-and-closed-loop/02-perception-output-schema.md) 负责把 observation 的字段正式定义清楚。
- [置信度与失败码](06-perception-interface-and-closed-loop/03-confidence-failure-code.md) 负责把质量状态和上层动作连起来。
- [主动感知与重观察](06-perception-interface-and-closed-loop/04-active-perception.md) 负责把“不够确定”的结果真正转化成下一步观察动作。

## 这一节和前后几节怎么分工

这一节不再教你：

- 怎样得到更好的 bbox、pose 或 contact。
- 怎样构建地图或场景图。

这些结果默认已经由前面各节产出。这一节负责的是把它们变成一个统一的系统接口，并在坏结果出现时决定：

- 是继续执行。
- 还是刷新观测。
- 还是主动换视角。
- 还是直接阻塞。

## 学完这一节，最好能带走什么

- 能定义一份包含 `frame_graph`、`timestamp`、`confidence`、`staleness_ms`、`failure_code` 的 observation。
- 能区分 `confidence`、`covariance`、`staleness_ms` 和 `failure_code` 的职责边界。
- 能为失败结果设计 `execute / refresh / reobserve / degrade / abort` 的动作映射。
- 能把主动感知理解成感知闭环的一部分，而不是附加功能。

## 建议阅读顺序

1. 先读 [感知接口](06-perception-interface-and-closed-loop/01-perception-interface.md)。
2. 再读 [感知输出规范](06-perception-interface-and-closed-loop/02-perception-output-schema.md)。
3. 然后读 [置信度与失败码](06-perception-interface-and-closed-loop/03-confidence-failure-code.md)。
4. 最后读 [主动感知与重观察](06-perception-interface-and-closed-loop/04-active-perception.md)。

## 导航

- 上一节：[语义地图与 3D 场景图](05-spatial-localization-and-semantic-maps/02-semantic-scene-graphs.md)
- 下一节：[感知接口](06-perception-interface-and-closed-loop/01-perception-interface.md)
- 返回本章：[感知与三维视觉](README.md)
