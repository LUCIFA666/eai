# SPH、MPM、PBD 分别解决什么

本页用初学者视角解释 Genesis 官方文档中常见的 SPH、MPM、PBD。重点不是推公式，而是知道它们大致服务哪类物理对象和实验。

## 本节目标

本节围绕下面几个问题展开：

1. SPH 通常适合怎样理解？
2. MPM 常用于哪些连续介质或颗粒类问题？
3. PBD 为什么常和布料、形变或约束直觉相关？
4. 初学者第一次接触这些 solver 时应该避免哪些误解？

## 三个词先按对象来记

初学阶段不需要推导公式，可以先按对象类型记：

| 名称 | 可以先怎么理解 | 官方 showcase 里的影子 |
|---|---|---|
| SPH | 粒子流体，靠近邻粒子关系表达流体行为 | `physics_06_sph_rigid`、`physics_07_sph_mpm` |
| MPM | 粒子和网格混合，适合大形变、颗粒、连续介质 | `physics_04_mpm`、`physics_05_sand_wheel` |
| PBD | 位置约束，常用于布料、液体、可控形变 | `physics_08_pbd_liquid`、`physics_09_pbd_cloth` |
| Stable Fluid | 网格或体素直觉下的烟雾 / 流体可视化 | `physics_10_smoke` |

这张表不是严格分类学，只是帮助初次读代码时不迷路。看到 `SPH`，先想到粒子流体；看到 `MPM`，先想到沙、泥、连续介质和大形变；看到 `PBD`，先想到位置约束、布料和稳定形变。

读这些示例时，可以用一张轻量索引把“画面直觉”和“运行证据”连起来：

| 示例 ID | 第一眼看图 | 再看摘要 / 日志 |
|---|---|---|
| `physics_04_mpm` | 材料是否整体下落、形变或堆积 | 是否保存 75 帧、是否有 build / solver warning |
| `physics_05_sand_wheel` | 轮子和颗粒是否发生可见耦合 | 耗时和帧数，判断它比纯刚体更重 |
| `physics_06_sph_rigid` | 流体粒子是否和刚体发生交互 | camera 是否真正捕获粒子区域 |
| `physics_08_pbd_liquid` | 液体形状是否稳定 | 是否有粒子飞散、全黑图或截断帧 |
| `physics_09_pbd_cloth` | 布料是否有合理下垂和约束 | 约束、碰撞和自碰撞 warning 是否出现 |
| `physics_10_smoke` | 烟雾体积是否可见、是否居中 | summary 是否标明 slice / resize adapter |

这张表的目的不是替代公式，而是建立一种阅读顺序：先用图建立对象直觉，再用摘要或日志确认它确实按预期运行。完整的帧数、adapter 和日志路径可以在各素材的 summary 里查到。

## SPH：从粒子看流体

SPH 的直觉是：流体由许多粒子表示，每个粒子的行为受邻近粒子影响。它适合帮助初学者理解“流体不是一个刚体对象”，而是一团不断变化的粒子状态。

读 SPH 示例时，重点看：

- 粒子数量和空间分布；
- 边界和容器如何设置；
- 是否和刚体或 MPM 对象耦合；
- 输出画面是否只是渲染，还是也保存了粒子状态。

`physics_06_sph_rigid` 展示的是 SPH 和刚体交互，`physics_07_sph_mpm` 展示的是不同非刚体求解路径之间的耦合。它们比单纯“水在动”更值得分析，因为它们暴露了多物理场景最核心的问题：不同状态表示如何共享一个世界。

<figure class="doc-figure">
<p class="doc-figure-title">SPH：流体粒子与刚体交互</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_06_sph_rigid.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_06_sph_rigid.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/coupling/sph_rigid.py</code> 的真实 headless 运行（1060×580，75 帧）。流体由许多粒子表示，与刚体之间发生可见的相互作用，而不是一团贴图。</p>
</figure>

`physics_10_smoke` 也属于流体现象入口，但它的预览来自官方 smoke 输出的 slice / resize 处理，不能当作普通 camera runner 的逐帧 RGB。这里记住“烟雾是流体现象的可视化入口”就够了；写报告时再补 adapter 说明。

<figure class="doc-figure">
<p class="doc-figure-title">Stable Fluid：烟雾</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_10_smoke.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_10_smoke.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/smoke.py</code> 的运行结果。这段预览经过 slice、缩放与居中处理，是流体现象的可视化入口，不能当作逐帧原始 RGB。</p>
</figure>

## MPM：大形变和颗粒的入口

MPM 常被用来处理沙、泥、雪、软材料或大形变连续介质。它的直觉是粒子携带材料状态，网格辅助计算力和速度更新。

读 MPM 示例时，重点看：

- 材料像沙、泥、弹性体还是流体；
- 粒子分辨率是否足够；
- 与刚体接触时是否稳定；
- 时间步和 substeps 是否被记录。

`physics_05_sand_wheel` 是很适合入门观察的例子：轮子不是简单穿过一张贴图，而是和颗粒材料发生耦合。这个素材可以直观看到，多物理难点不只是“画出沙子”，而是沙子和刚体之间的作用是否可信。

<figure class="doc-figure">
<p class="doc-figure-title">MPM：轮子与颗粒材料耦合</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_05_sand_wheel.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_05_sand_wheel.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/coupling/sand_wheel.py</code> 的真实运行。轮子并非穿过一张贴图，而是与颗粒材料真实耦合，这正是多物理的难点所在。</p>
</figure>

## PBD：位置约束和布料直觉

PBD 可以先理解为“通过位置约束让对象满足某些几何关系”。它常用于布料、绳索、液体或其他更强调稳定性的形变效果。

读 PBD 示例时，重点看：

- 约束对象是什么：布料、液体还是其他；
- 布料是否有固定边界或附着点；
- 自碰撞和接触厚度如何处理；
- 画面是否稳定，是否出现拉伸爆炸或穿透。

`physics_09_pbd_cloth` 是很好的入门观察对象：布料不是刚体，它没有一个简单的单一位姿。要观察的是一整片网格或粒子集合如何在约束下运动。

<figure class="doc-figure">
<p class="doc-figure-title">PBD：布料的下垂与约束</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_09_pbd_cloth.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_09_pbd_cloth.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/tutorials/pbd_cloth.py</code> 的真实运行。布料没有单一位姿，要看的是一整片网格在位置约束下如何下垂与运动。</p>
</figure>

## 不要把 solver 当成“效果按钮”

初学者容易把 SPH、MPM、PBD 当成渲染效果按钮：想要水就开 SPH，想要沙就开 MPM，想要布就开 PBD。这样理解太浅。

更好的读法是四问：

1. 这个对象的状态是什么，位姿、网格、粒子，还是约束集合？
2. 这个 solver 每一步在更新什么？
3. 它和其他对象如何接触或耦合？
4. 可以保存哪些证据证明它不是只“看起来动了”？

如果这四问答不上来，就先不要把它接进机器人控制或 RL 训练。

## 读完应能回答

1. SPH、MPM、PBD 分别更适合从哪类对象直觉入门？
2. 为什么 `physics_10_smoke` 要说明 slice、resize 和居中处理？
3. 把 solver 当成“效果按钮”会掩盖哪些实验风险？

## 小结

- SPH、MPM、PBD 的入门重点不是公式，而是对象、状态和验收。
- SPH 更容易从粒子流体理解，MPM 更适合大形变和颗粒材料，PBD 更贴近约束和布料直觉。
- 多物理示例要关注耦合关系，不只关注画面是否好看。
- 把 solver 当成效果按钮，会掩盖真正的数值和物理问题。

## 导航

- 上一页：[solver、material 与时间步](02-solver-material-timestep.md)
- 返回目录：[多物理入门](../05-multiphysics.md)
- 下一页：[非刚体实验为什么难验收](04-non-rigid-check.md)
