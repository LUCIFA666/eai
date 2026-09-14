# 对象感知

目标：把“场景里有什么”整理成“哪个对象是目标、边界是否可信、位姿能否执行”的对象级 observation。

这一节是从场景级几何走向对象级结果的主线。前一节已经把像素、深度和点云放进统一几何世界里；这一节开始回答更接近任务的问题：

- 当前场景里哪些区域是任务相关对象。
- 这些对象的边界和实例划分是否足够可信。
- 同一个对象在连续帧里是不是还被稳定跟住。
- 最终能不能得到可执行的 6D pose。

## 这一节的主线

对象感知不是“跑一个 detector 就结束”，而是一条逐步收缩不确定性的链：

```text
image / point cloud
  -> object candidate
  -> bbox / mask
  -> quality gate
  -> temporal tracking
  -> 6D pose
  -> planner-consumable object record
```

这条链里每一页负责的事情不同：

- [检测与分割](02-object-perception/01-detection-segmentation.md) 负责把场景切成对象候选。
- [GroundingDINO 与 SAM](02-object-perception/02-groundingdino-sam.md) 负责把自然语言目标和开放词汇对象提取接起来。
- [Mask 质量与时序稳定](02-object-perception/03-mask-quality.md) 负责给边界加 gate，并维护最基本的跨帧稳定性。
- [点跟踪](02-object-perception/04-point-tracking.md) 负责补上跨帧对应和局部运动轨迹这条时序线。
- [位姿估计](02-object-perception/05-pose-estimation.md) 负责把对象候选变成 6D pose。
- [PnP 与 ICP](02-object-perception/06-pnp-icp.md) 负责讲透传统可解释 pose 管线。
- [FoundationPose 类方法](02-object-perception/07-foundationpose.md) 负责说明集成式 pose 模型在工程里怎样落点。

## 这一节和前后几节怎么分工

这一节不负责：

- 多帧几何融合和场景底图构建，那是 [几何感知基础](01-geometric-perception-foundations.md) 的事情。
- 从对象进一步推导抓取点、可供性和接触验证，那是 [可交互感知](04-interactive-perception.md) 的事情。
- 定义统一 observation schema，那是 [感知接口与闭环](06-perception-interface-and-closed-loop.md) 的事情。

更准确地说，这一节负责把场景感知压缩成“对象级事实”，后面几节再把它们变成动作可执行事实。

## 学完这一节，最好能带走什么

- 能区分 detection、segmentation、tracking、pose estimation 各自负责什么。
- 能解释为什么高分 bbox 不等于可执行 pose。
- 能给一份对象结果补齐 `frame_id`、`timestamp`、`confidence`、`staleness_ms`、`failure_code`。
- 能在对象级失败时区分：是没看见、边界不稳、时序丢失，还是姿态不可信。

## 建议阅读顺序

1. 先读 [检测与分割](02-object-perception/01-detection-segmentation.md) 和 [GroundingDINO 与 SAM](02-object-perception/02-groundingdino-sam.md)。
2. 再读 [Mask 质量与时序稳定](02-object-perception/03-mask-quality.md) 和 [点跟踪](02-object-perception/04-point-tracking.md)。
3. 然后进入 [位姿估计](02-object-perception/05-pose-estimation.md)。
4. 最后对照 [PnP 与 ICP](02-object-perception/06-pnp-icp.md) 和 [FoundationPose 类方法](02-object-perception/07-foundationpose.md)。

## 导航

- 上一节：[NeRF / 3DGS 在机器人中的应用](01-geometric-perception-foundations/06-nerf-3dgs-robotics.md)
- 下一节：[检测与分割](02-object-perception/01-detection-segmentation.md)
- 返回本章：[感知与三维视觉](README.md)
