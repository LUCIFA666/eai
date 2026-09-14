# 可交互感知

目标：把对象级结果继续压缩成“哪里能碰、怎样接近、接触是否成功”的交互级 observation。

这一节开始从“认出对象”走向“知道怎么碰对象”。很多系统在对象检测和 pose 之后就急着进入动作，但真正的交互往往还差几层关键感知：

- 物体表面哪些区域更适合抓、推、拉、按。
- 2D 可供性结果怎样落到 3D 接触点和接近方向。
- 候选抓取位姿怎样经过碰撞、可达性和稳定性筛选。
- 真正接触之后，视觉看不到的成功/失败证据从哪里来。

## 这一节的主线

可以把这一节理解成从对象记录继续走到接触证据链：

```text
object record
  -> affordance
  -> 3D contact
  -> grasp candidate
  -> tactile / force evidence
  -> slip / failure diagnosis
  -> visuo-tactile fusion
```

对应页面分工如下：

- [可供性与交互区域](04-interactive-perception/01-affordance-grounding.md) 负责建立“对象级结果”和“交互级区域”之间的中间层。
- [Affordance Heatmap](04-interactive-perception/02-affordance-heatmap.md) 负责把可供性变成 2D 可消费输出。
- [3D Contact Point](04-interactive-perception/03-contact-point.md) 负责把 2D 交互区域落到 3D 几何与法向。
- [抓取位姿生成](04-interactive-perception/04-grasp-pose-generation.md) 负责把候选接触点变成可执行抓取姿态。
- [触觉、力觉与接触观测](04-interactive-perception/05-tactile-force-sensing.md) 负责建立接触观测层。
- [接触事件与滑移检测](04-interactive-perception/06-contact-slip.md) 负责把连续观测转成离散事件和稳定性判断。
- [力控证据链](04-interactive-perception/07-force-control-evidence.md) 负责把连续力数据整理成可复盘证据。
- [视触融合](04-interactive-perception/08-visuo-tactile-fusion.md) 负责把视觉与触觉组合成更稳定的交互状态估计。

## 这一节和前后几节怎么分工

这一节不再重新讲：

- 对象是谁、bbox 和 pose 怎么来，这属于 [对象感知](02-object-perception.md)。
- 统一 observation schema 怎么定义，这属于 [感知接口与闭环](06-perception-interface-and-closed-loop.md)。

这一节的工作是把对象结果转换成“可交互结果”，也就是从“看见”推进到“能安全碰、能复盘接触后发生了什么”。

## 学完这一节，最好能带走什么

- 能区分可供性、接触点、抓取位姿、接触事件、滑移事件各自负责什么。
- 能解释为什么 `pose` 还不等于 `grasp pose`。
- 能给接触或抓取候选设计最小 contract，至少包含 `frame_id`、`confidence`、`failure_code`。
- 能在抓取失败时反查：问题出在对象边界、接触点、姿态选择，还是接触后滑移与过载。

## 建议阅读顺序

1. 先读 [可供性与交互区域](04-interactive-perception/01-affordance-grounding.md)、[Affordance Heatmap](04-interactive-perception/02-affordance-heatmap.md)。
2. 再读 [3D Contact Point](04-interactive-perception/03-contact-point.md)、[抓取位姿生成](04-interactive-perception/04-grasp-pose-generation.md)。
3. 然后读 [触觉、力觉与接触观测](04-interactive-perception/05-tactile-force-sensing.md)、[接触事件与滑移检测](04-interactive-perception/06-contact-slip.md)、[力控证据链](04-interactive-perception/07-force-control-evidence.md)。
4. 最后用 [视触融合](04-interactive-perception/08-visuo-tactile-fusion.md) 把“看见”和“接触到”合起来。

## 导航

- 上一节：[不同模型的差异与选型](03-vision-foundation-models/05-model-selection-and-comparison.md)
- 下一节：[可供性与交互区域](04-interactive-perception/01-affordance-grounding.md)
- 返回本章：[感知与三维视觉](README.md)
