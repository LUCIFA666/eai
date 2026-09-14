# 视觉基础模型

> 难度：[中级] | 预计用时：35 分钟
> 先修：[位姿估计](02-object-perception/05-pose-estimation.md)
> 阅读提示：本页只负责建立全节结构，不再把所有模型揉在一页里讲完。

目标：先把视觉基础模型在机器人感知链中的职责分开，再按“每类模型一页，最后统一比较”的方式展开后续页面。

## 先建立直觉

“视觉基础模型”最容易引发两种误解：

- 误以为只要换成更大的模型，标定、深度、位姿和接触这些问题就能自动消失。
- 误以为所有 foundation model 都只是“输出 feature”，因此彼此差别不大。

这两种理解都不适合机器人系统。

机器人感知真正关心的是一串连续问题：

- 语言目标“红色杯子”对应场景里的谁。
- 这一目标和其他候选相比，语义上谁更像。
- 连续两帧里，哪一块局部结构还是同一把手、同一个边缘、同一块交互区域。
- 单张 RGB 图像里，物体离相机大概多远。
- 点云里，哪些 3D 局部结构属于同一对象，哪些点最值得关注。

这些问题对应的并不是同一种模型，而是一组分工明确的模型族。

## 为什么这一节要按模型族拆页

从教学角度看，把 CLIP、DINO、深度模型、点云模型先堆在一页里，再在页内继续嵌套子节，会带来两个问题：

- 每个模型只能被压缩成几段概述，关键原理讲不透。
- 初学者容易把“语义模型”“局部对应模型”“深度模型”“3D 表征模型”混成同一类。

因此本节改成下面这种结构：

| 页面 | 核心问题 | 主要关注的能力 |
|---|---|---|
| [CLIP 与 SigLIP](03-vision-foundation-models/01-clip-and-siglip.md) | 文本和图像是不是在说同一个对象 | 图文对齐、embedding、zero-shot |
| [DINO 与 DINOv2](03-vision-foundation-models/02-dino-and-dinov2.md) | 哪里和哪里在局部结构上最相似 | patch feature、dense feature、局部对应 |
| [Depth Anything 与单目深度模型](03-vision-foundation-models/03-depth-foundation-models.md) | 单张 RGB 图像怎样补出距离信息 | 相对深度、度量深度、几何校验 |
| [Point Foundation Model](03-vision-foundation-models/04-point-foundation-models.md) | 点云里的 3D 表征怎样支持机器人任务 | point feature、3D 语义、对象级 observation |
| [不同模型的差异与选型](03-vision-foundation-models/05-model-selection-and-comparison.md) | 任务来了以后应该先选哪类模型 | 选型、组合、职责边界 |

这样安排后，每一页只讲一类核心能力，最后再统一做横向比较。

## 先把“本节讲什么，不讲什么”说清楚

本节主要讨论的是四类视觉基础模型：

- 图文对齐模型：例如 CLIP、SigLIP。
- 自监督视觉表征模型：例如 DINO、DINOv2。
- 单目深度基础模型：例如 Depth Anything 一类方法。
- 点云基础模型：例如 point transformer、point masked modeling 一类预训练路线。

本节不重复展开的内容有两类：

- `GroundingDINO`、`SAM` 这类检测与分割模型，已经在 [检测与分割](02-object-perception/01-detection-segmentation.md) 里详细讲过。
- `FoundationPose` 这类位姿恢复方法，已经在 [位姿估计](02-object-perception/05-pose-estimation.md) 中单独展开。

它们仍然属于整条感知链的重要环节，但这一节的重点是“通用视觉表征和中间能力”。

## 一张总表先建立角色地图

| 模型族 | 典型输入 | 典型输出 | 最擅长回答什么 | 仍然缺什么 |
|---|---|---|---|---|
| CLIP / SigLIP | 图像、文本 | image/text embedding、相似度 | “这是不是我要找的对象” | 精确像素位置、3D 几何 |
| DINO / DINOv2 | 图像 | patch feature、dense feature | “哪里和哪里在局部结构上相似” | 文本语义、动作可执行性 |
| 单目深度模型 | 单张 RGB | 深度图 | “这一像素离相机大概多远” | 稳定语义、坐标系变换 |
| Point Foundation Model | 点云 | point feature、3D 语义表征 | “哪些三维局部结构重要或相似” | 动作接口、最终控制字段 |

最关键的一句总结是：

**这些模型大多提供的是强中间能力，而不是机器人最终动作字段。**

## 为什么机器人里不能只看模型分数

在普通图像任务里，模型输出一个标签、一个框，很多时候已经够用。但在机器人系统里，视觉结果后面还要接：

- 坐标系变换
- 深度有效性检查
- 位姿稳定性判断
- 可供性与接触约束
- 控制与失败回溯

因此，本节后续每一页都会反复强调两个边界：

- 高语义分数不等于可抓取。
- 有 feature 不等于有 pose。

## 建议阅读顺序

如果第一次接触这些模型，建议按下面顺序阅读：

1. 先看 [CLIP 与 SigLIP](03-vision-foundation-models/01-clip-and-siglip.md)，建立“文本如何进入视觉系统”的直觉。
2. 再看 [DINO 与 DINOv2](03-vision-foundation-models/02-dino-and-dinov2.md)，把“语义匹配”和“局部对应”分开。
3. 接着看 [Depth Anything 与单目深度模型](03-vision-foundation-models/03-depth-foundation-models.md)，理解单张 RGB 如何补几何。
4. 然后看 [Point Foundation Model](03-vision-foundation-models/04-point-foundation-models.md)，把 3D 表征与物理坐标区分开。
5. 最后用 [不同模型的差异与选型](03-vision-foundation-models/05-model-selection-and-comparison.md) 做横向总结。

## 常见误区

| 误区 | 为什么错 |
|---|---|
| “有了 CLIP 就能直接抓” | CLIP 提供的是语义筛选，不是几何执行结果 |
| “DINO 也是 feature，所以和 CLIP 差不多” | DINO 更偏局部结构对应，不是图文语义对齐 |
| “能出深度图，就能直接当抓取高度真值” | 单目深度仍然需要尺度校验和坐标系对齐 |
| “point feature 就是 3D 坐标” | 特征表示和物理位置不是同一种信息 |

## 自检问题

1. 为什么本节要按模型族拆成多个并列页面，而不是把所有模型堆在一页里？
2. 为什么说视觉基础模型大多提供的是“中间能力”，而不是“最终动作字段”？
3. 在机器人系统里，为什么高分语义匹配结果仍然必须继续经过几何与执行层检查？

## 练习

### [观察] 给任务分配模型族

对下面四个任务，分别判断最应该先查哪类模型页面：

- “找桌上的红色杯子”
- “在连续帧里跟住同一把抽屉把手”
- “用单张 RGB 估计物体大概离相机多远”
- “在点云里判断哪些局部结构属于同一对象”

完成后，可以先用下面几条检查这一部分是否已经到位：
- 能明确指出每个任务对应的模型族，而不是只写模型名字。

### [复现] 画一张本节的知识地图

把本节画成一张简单结构图：

```text
语义匹配 -> 局部对应 -> 深度恢复 -> 3D 表征 -> 选型比较
```

完成后，可以先用下面几条检查这一部分是否已经到位：
- 图中能看出每一页负责的一类问题。
- 不把 `GroundingDINO / SAM` 和 `pose` 页面混进本节的主线里。

## 导航

- 上一节：[FoundationPose 类方法](02-object-perception/07-foundationpose.md)
- 下一节：[CLIP 与 SigLIP](03-vision-foundation-models/01-clip-and-siglip.md)
- 返回本章：[感知与三维视觉](README.md)



