# solver、material 与时间步

本页讲多物理实验中最容易被忽略的三个变量：求解器、材料参数和时间步。它们会直接影响稳定性、速度和现象是否符合直觉。

## 本节目标

本节围绕下面几个问题展开：

1. solver 在仿真中负责什么？
2. material 参数为什么不能随意填？
3. `dt` 和 `substeps` 会怎样影响接触和稳定性？
4. 为什么多物理实验必须记录求解参数？

## solver 负责“怎么算”

在刚体入门里，通常只关心物体位姿、关节目标和接触是否稳定。但一旦进入多物理，首先要问的是：这个对象到底交给哪个 solver 来推进？

可以先这样粗略理解：

| solver / 路径 | 常见对象 | 直觉 |
|---|---|---|
| Rigid | 机器人、盒子、球、刚体网格 | 主要记录位姿、速度、关节和接触 |
| FEM | 软体、可形变实体 | 关心形变、约束和材料刚度 |
| MPM | 沙、泥、连续介质、颗粒状材料 | 用粒子/网格混合方式表达大形变 |
| SPH | 液体、粒子流体 | 用粒子近邻关系表达流体行为 |
| PBD | 布料、液体、约束型形变 | 用位置约束直觉稳定形变和接触 |
| IPC / SAP | 高级接触和耦合 | 更强调接触鲁棒性，但依赖和参数也更敏感 |

这个表不是要求背名词，而是提醒：**不同 solver 的状态和失败方式不同**。刚体失败可能是穿模或抖动；流体失败可能是粒子飞散；布料失败可能是自碰撞、拉伸或约束不稳定。

<figure class="doc-figure">
<p class="doc-figure-title">FEM：软硬约束下的形变体</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_03_fem_hard_soft.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_03_fem_hard_soft.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/fem_hard_and_soft_constraint.py</code>。FEM 关心的是形变、约束与材料刚度，而不再只是刚体位姿。</p>
</figure>

## material 负责“像什么”

material 不是颜色。颜色属于渲染表面，material 影响物理行为。多物理里常见的材料问题包括：

| 参数直觉 | 影响 |
|---|---|
| 刚度 | 软体或约束对象有多难变形 |
| 摩擦 | 接触后滑动、堆积、抓取是否稳定 |
| 密度 / 质量 | 重力、碰撞响应和惯性 |
| 耦合类型 | 对象是否参与某类 solver 或 coupler |

运行 `physics_11_ipc_cloth_teleop` 时就遇到了材料边界：官方 IPC 场景里的 Plane 需要使用 `gs.materials.Rigid(coup_type="ipc_only")` 这类适配，否则 IPC solver 报错。runner 没有把这件事藏起来，而是在 `STATUS.md` 里记录了一个作用范围很小的 plane material adapter，同时保留对应日志。

这件事对初学者很有启发：多物理报错不一定是 Python 写错，也可能是某个对象没有被放进正确的物理耦合关系里。

读这条素材时要分清三类证据：`summaries/physics_11_ipc_cloth_teleop.json` 证明它生成了 `75` 帧、`1060x580`、`result: passed` 的素材；`STATUS.md` 说明使用了 plane material adapter、`pyuipc` 和本地 cloth asset；原始日志则能看到它确实进入了 IPC 路径，而不是普通刚体示例。去掉颜色码后，关键日志信号可概括为：

```text
Adding <gs.engine.entities.FEMEntity> ... material: <gs.materials.FEM.Cloth>
Entity ... is cloth - adding to FEM solver for rendering only (physics managed by IPC)
IPC world initialized successfully
```

这三行比一张 cloth 视频更有证据价值。它们说明：场景里有 FEM cloth entity，渲染和物理解算的职责被拆开，IPC world 也确实初始化了。多物理实验要学会读这种日志信号。

<figure class="doc-figure">
<p class="doc-figure-title">IPC：机器人布料遥操（带 material adapter）</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_11_ipc_cloth_teleop.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_11_ipc_cloth_teleop.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/IPC_Solver/ipc_robot_cloth_teleop.py</code>。这段素材使用了记录在 STATUS.md 里的 plane material adapter（Plane 改为 <code>Rigid(coup_type="ipc_only")</code>），并依赖 pyuipc 与本地 cloth 资产，引用时要连同边界一起说明。</p>
</figure>

## 时间步影响稳定性

`dt` 是仿真时间步，`substeps` 是每个 step 内部再细分的求解步。粗略地说：

| 设置 | 可能现象 |
|---|---|
| `dt` 太大 | 接触穿透、震荡、形变爆炸 |
| `substeps` 太少 | 快速接触或软体约束不稳定 |
| `dt` 太小 | 更稳但更慢 |
| `substeps` 太多 | 更稳但计算成本上升 |

在刚体脚本里，这些参数可能很少改；在多物理脚本里，它们会变成实验记录的一部分。建议每次保存：

```json
{
  "sim_options": {
    "dt": 0.005,
    "substeps": 10
  },
  "solver_family": "rigid/mpm/sph/pbd/...",
  "material_notes": "..."
}
```

如果没有这些信息，别人看到一个视频也无法判断它为什么稳定，或者为什么换机器后不稳定。

## 从官方 Physics 结果读参数敏感性

18 项 Physics showcase 中，有几类特别能体现参数敏感性：

| 示例 | 为什么敏感 |
|---|---|
| `collision_tower` | 堆叠刚体对接触、摩擦和时间步敏感 |
| `pbd_cloth` | 布料对约束、碰撞厚度、自碰撞敏感 |
| `sand_wheel` | 颗粒/连续介质对分辨率和耦合敏感 |
| `water_wheel` | 流体与刚体耦合对时间步和粒子数量敏感 |
| `sap_franka_grasp_rigid_cube` | 抓取接触和 solver 设置会影响是否稳定夹持 |

所以看 showcase 时，不要只问“它是不是能跑”。更好的问题是：它依赖什么 solver？材料怎么设？时间步是什么？输出是视频、状态，还是传感器数据？

<figure class="doc-figure">
<p class="doc-figure-title">流体与刚体耦合：水车</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_15_water_wheel.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_15_water_wheel.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/coupling/water_wheel.py</code>。流体驱动刚体转动，对时间步和粒子数量都很敏感。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">抓取接触：SAP 求解器 Franka 抓方块</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_17_sap_franka_grasp_rigid_cube.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_17_sap_franka_grasp_rigid_cube.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/sap_coupling/franka_grasp_rigid_cube.py</code>（已加密采样重录为更完整的片段）。抓取接触和 solver 设置直接影响能否稳定夹持。</p>
</figure>

## 读完应能回答

1. solver、material、`dt` 和 `substeps` 分别影响什么？
2. `physics_11_ipc_cloth_teleop` 的 plane material adapter 为什么必须写进报告？
3. 如果一个布料视频看起来稳定，但没有时间步和材料记录，结论为什么要保守？

## 小结

- solver 决定物理状态如何被推进，material 决定对象的物理行为，时间步决定稳定性和速度。
- 多物理实验必须记录 `dt`、`substeps`、solver family、材料和可选依赖。
- 官方示例中的 adapter 不是缺陷标签，而是必须说明的工程边界。
- 参数越多，越要从单对象、短时间、可记录的实验开始。

## 导航

- 上一页：[从多刚体开始](01-start-from-multi-rigid.md)
- 返回目录：[多物理入门](../05-multiphysics.md)
- 下一页：[SPH、MPM、PBD 分别解决什么](03-sph-mpm-pbd.md)
