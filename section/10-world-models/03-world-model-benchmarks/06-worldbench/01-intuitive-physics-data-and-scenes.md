# 直觉物理数据与场景

直觉物理子集以物体在有限时段内的可见运动为评测单位。每条视频长 132 帧，场景在一个主要物理概念上变化，同时随机化对象种类、位置、材料等非核心因素。这样的控制使得模型在某类场景中出现的物体漂移、遮挡遗忘或支撑错误可以与相应概念关联，而不必把所有问题折叠为一个二元的接触预测结果。

子集共有 469 段视频，其中 425 段为合成视频、44 段为真实视频。合成部分由 Kubric 组织场景，PyBullet 计算物理演化，Blender 渲染图像。每段合成视频附带对象分割、深度、表面法线和光流；真实视频用于在同类概念上比较模型对实拍输入的预测。对象网格取自 ShapeNet，随机化覆盖不同类别、形状、纹理、尺寸与材料。

## 四类概念与 13 个场景

| 概念 | 场景 | 主要受检关系 |
| --- | --- | --- |
| Motion physics | Bouncing Ball、Two Object Fall、Two Object Parabolic Motion | 重力、自由落体、抛体轨迹、碰撞后的运动 |
| Object permanence | Block & Object、Columns、Raised Block Bounce、Wall Bouncing、Two Ball Bounce | 对象被遮挡后仍保持身份、位置和既有运动状态 |
| Support relations | Dominoes、Ramp Block、Table Drop | 接触、承重、平衡、障碍物停止运动和连锁倾倒 |
| Scale / Perspective | Object / Sphere Moving Towards Camera、Object / Sphere Moving Away From Camera | 距离变化引起的图像尺度和位置变化 |

Motion physics 的场景将重力和接触放在可观察的轨迹中。Bouncing Ball 在给定帧中已经包含反弹信息，后续轨迹仍取决于初始高度和反弹属性；Two Object Fall 与 Two Object Parabolic Motion 则加入两个对象的相对位置和潜在碰撞。它们考察的不只是物体向下运动，也包括两个对象在相同场景中保持各自的动力学关系。

Object permanence 场景把视觉不可见与状态消失分开。Block & Object 和 Columns 让对象在线性运动中被墙体或多根立柱反复遮挡；Raised Block Bounce、Wall Bouncing 与 Two Ball Bounce 将周期运动、碰壁或前后遮挡加入同一要求。生成视频若在对象重现时改变其身份、位置、速度方向或直接遗漏对象，都会破坏这类关系。

Support relations 关注几何接触何时足以支撑物体。Dominoes 将初始速度传递为连锁倾倒；Ramp Block 要求球沿斜面运动并被末端障碍物停止；Table Drop 通过改变物体越过桌边的比例，区分稳定支撑与重心越界后的下落。Scale / Perspective 使用单个物体接近或远离相机的轨迹，使图像上的放大、缩小和位置变化具有明确的参考演化。

## 场景构造的作用

随机化不会取消物理约束。以墙后运动为例，对象类别和初始速度可以变化，但遮挡前后的连续轨迹仍受同一运动规律约束；以 Table Drop 为例，物体形状和放置位置变化，但稳定性仍由支撑面相对质量分布决定。场景因此保留了外观多样性，同时避免把模型未见过某类物体与模型未保持物理关系完全混为一谈。

合成标注使对象级评测成为可能。深度、法线和光流记录了场景演化的附加参照，主评测使用对象分割以比较模型续写结果中的前景位置和轮廓。真实部分不具备合成流水线的完整辅助标注，却能检验模型在相同概念的实拍条件下是否出现明显不同的趋势。

## 导航

- 返回上级：[WorldBench](../06-worldbench.md)
- 下一节：[视频预测评测协议](02-video-prediction-protocol.md)
