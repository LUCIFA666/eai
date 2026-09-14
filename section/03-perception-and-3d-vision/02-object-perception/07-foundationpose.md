# FoundationPose 类方法

> 难度：[高级] | 预计用时：65 分钟
> 先修：[PnP 与 ICP](06-pnp-icp.md)

目标：理解 FoundationPose 类方法在机器人系统里的工程落点，以及它与传统 `PnP + ICP` 管线的边界。

## 先建立直觉

把 FoundationPose 类方法想成“会看图、会看深度、还知道物体网格长什么样的 pose 专家”。传统 pipeline 往往把检测、分割、初值估计、跟踪和 refinement 拆成多个模块；FoundationPose 类方法试图把其中一大段变成统一推理器，用 RGB、depth、mask、CAD 和历史状态一起推断当前姿态。它的价值不是神奇地绕过几何，而是把几何先验、视觉特征和时序信息揉进同一套推理逻辑里。

## 本页目标

这一页读完后，我们希望能一起把下面几件事说明白：

- 解释 FoundationPose 类方法通常需要哪些输入，以及这些输入各自约束什么。
- 区分它取代了传统 pipeline 的哪一段，哪一段仍然需要系统工程补齐。
- 判断它适合离线评测、在线 tracking，还是直接做 planner target。
- 为一个桌面抓取任务写出最小集成计划和风险清单。

## 先看它解决的到底是什么问题

```text
传统路线:
detection -> mask -> coarse pose -> ICP -> temporal tracking

FoundationPose 类路线:
RGB + depth + mask + CAD + prev pose
          -> unified pose estimation / tracking
          -> pose + score + update state
```

它最擅长处理的不是“有没有这个物体”，而是“已知目标实例后，它当前的 6D 姿态在哪里”。

## 典型输入清单

**CAD（计算机辅助设计模型）**：物体几何形状的数字化描述，通常由3D建模软件生成。包含物体的精确尺寸和形状。

**mesh（网格模型）**：用三角形或多边形面片表示物体表面的3D模型。CAD通常导出为mesh格式。mesh比点云包含更多拓扑信息（面片连接关系）。

| 输入 | 是否常见必需 | 作用 |
|---|---|---|
| RGB | 是 | 提供纹理和边界信息 |
| depth | 常见 | 约束几何形状与尺度 |
| object mask | 常见 | 指定当前要估计哪一个实例 |
| CAD / mesh | 常见 | 提供物体几何先验 |
| camera intrinsics | 是 | 把像素与射线对应起来 |
| initial pose / previous pose | 在线 tracking 时常见 | 让迭代或时序更新更稳定 |

注意这说明它不是”从零识别一切”的万能模型。大多数情况下，你仍然需要前端检测或分割先把实例圈出来。

## 与传统管线的职责切分

| 模块 | 传统路线负责 | FoundationPose 类方法是否覆盖 |
|---|---|---|
| 开放词汇目标选择 | GroundingDINO / CLIP 等 | 通常不覆盖 |
| 实例区域定位 | detector / segmenter | 常依赖外部提供 mask |
| 初始 6D pose | PnP / template / heuristic | 常可部分覆盖 |
| pose refinement | ICP | 常可覆盖或替代 |
| 多帧 tracking | 额外 tracker | 通常更擅长 |

所以最实际的落地方式往往不是“全替换”，而是：

```text
GroundingDINO/SAM 负责找对象
FoundationPose 负责估姿与跟踪
planner/supervisor 负责用或不用
```

## 为什么它对输入质量更敏感

FoundationPose 类方法集成度更高，但也意味着它更依赖“整条输入链都干净”：

| 输入脏在哪里 | 造成什么后果 |
|---|---|
| mask 漏掉把手或边缘 | 几何先验与观测对不上 |
| depth 空洞多 | 物体表面拟合不稳定 |
| CAD 尺寸与实物不一致 | 输出姿态和尺度一起偏 |
| intrinsics 错 | 全部几何投影关系变形 |
| previous pose 错很多 | 跟踪可能锁进错误局部最小 |

这和 `PnP + ICP` 的差别是：传统 pipeline 的问题更容易按模块切开排查，而集成模型的问题更容易“整块发散”。

## 最小集成计划

```text
1. 上游提供稳定实例 mask
2. 读取目标物体 mesh / CAD
3. 准备相机内参、depth、RGB
4. 若是 tracking 模式，缓存上一帧 pose
5. 调用 pose estimator
6. 输出 T_camera_object, score, symmetry, failure_code
7. 再变换到 T_base_object 交给规划器
```

如果第 1 步没有稳定的实例定位，这类方法通常就很难直接放进开放世界桌面抓取里。

## 推荐的输出结构

```yaml
foundation_pose_result:
  object_id: mug_01
  input:
    rgb_frame: wrist_rgb_102
    depth_frame: wrist_depth_102
    mask_ref: runs/04-perception/masks/mug_01_t102.png
    cad_ref: assets/models/mug_01.obj
  pose_camera_object:
    xyz: [0.437, -0.118, 0.612]
    quat_xyzw: [0.002, 0.713, 0.004, 0.701]
  tracking_state:
    used_prev_pose: true
    prev_track_id: mug_track_02
  metrics:
    confidence: 0.78
    reprojection_score: 0.81
    depth_alignment_score: 0.74
  failure_code: null
```

比起“模型输出一个 pose 就完事”，更关键的是把依赖证据和时序状态一起记录下来。

## 在线系统里的三种常见用法

| 用法 | 说明 | 风险 |
|---|---|---|
| 单帧初始化 | 把它当高质量单帧 pose 求解器 | 遮挡和 mask 误差容易直接打爆 |
| 多帧 tracking | 利用上一帧 pose 持续更新 | 丢失后重定位要有兜底 |
| 离线标注/评测 | 提供更稳定的姿态标签 | 运行成本高，GPU 依赖重 |

对于教学和原型系统，第二种最有代表性，因为它最贴近真实机器人抓取。

## 什么时候它不值得上

| 场景 | 更简单的方法可能更好 |
|---|---|
| AprilTag、棋盘格等人工标记目标 | 直接用 PnP 更透明 |
| 只有粗抓取，不关心完整 6D 姿态 | 直接用 mask 点云或 grasp pose 更经济 |
| 没有可靠 CAD / mesh | 模型前提不成立 |
| 设备只剩 CPU、实时要求很紧 | 推理耗时可能不可接受 |

不要因为模型“更 Foundation”就默认它更适合当前系统。

## 风险与验证点

| 风险 | 需要验证什么 |
|---|---|
| 遮挡下姿态漂移 | 连续帧 pose 是否平滑 |
| 对称物体歧义 | 旋转输出是否显式降置信 |
| GPU 依赖 | 单帧延迟能否满足控制周期 |
| 上游 mask 噪声 | 是否能在轻微错误下保持可用 |
| 结果可解释性 | 日志里是否保留输入证据和质量分数 |

## 自检问题

1. 为什么说 FoundationPose 类方法通常不是 GroundingDINO 的替代品，而更像它的下游？
2. 如果一个系统没有稳定的实例 mask，直接接入 FoundationPose 类方法会卡在哪一步？
3. 与 `PnP + ICP` 相比，集成式 pose 模型在排错时最容易失去的是什么？

## 练习

### [观察] 画出一份集成边界

1. 选择一个对象级任务，例如抓杯子、抓抽屉把手、拾取盒子。
2. 画出 `检测/分割 -> pose -> 规划` 的三段式图。
3. 标出哪一段可以用 FoundationPose 类方法替代，哪一段仍保留传统模块。

完成后，可以先用下面几条检查这一部分是否已经到位：
- 能明确指出它的上游依赖和下游产物。
- 能说清为什么“开放词汇检测”通常不在它的职责里。

### [复现] 写一份最小上线清单

1. 以桌面刚体抓取为例，列出需要的输入文件、运行时输入和输出字段。
2. 给每一项输入标一个风险，例如“mask 误差”“CAD 尺寸不准”“depth 空洞”。
3. 为每个风险写一个可执行的验证动作。

完成后，可以先用下面几条检查这一部分是否已经到位：
- 清单里至少包含 `RGB`、`depth`、`mask`、`CAD`、`camera intrinsics`。
- 至少给出 3 个失败码或停机条件。

## 导航

- 上一节：[PnP 与 ICP](06-pnp-icp.md)
- 返回本章：[感知与三维视觉](../README.md)
- 下一节：[视觉基础模型](../03-vision-foundation-models.md)


