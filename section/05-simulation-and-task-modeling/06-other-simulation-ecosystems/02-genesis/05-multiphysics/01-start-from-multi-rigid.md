# 从多刚体开始

前面几页已经跑过机器人、相机和批量环境。现在回到 Genesis 最容易被记住、也最容易被误解的特点：多物理。

“支持多物理”听起来很强，但学习时不能只停在这句话。对初学者来说，更重要的是先建立一个刚体基线：当前场景里有哪些对象，它们的状态如何记录，哪些现象可以用刚体模型解释，哪些问题必须等进入软体、布料、颗粒或流体后再讨论。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么学习 Genesis 多物理时不应该第一步就写软体或流体？
2. 如何从多个刚体对象开始，练习实体、状态和时间步记录？
3. 官方 Physics showcase 里的刚体素材应该怎样作为对照？
4. 进入软体、布料、颗粒或流体前，刚体基线应该验收什么？

## 先从多物体刚体开始

Genesis 的亮点是多物理，但第一步不建议直接上软体、颗粒或流体。原因不是它们不重要，而是它们会同时引入更多变量：材料参数、求解器、分辨率、时间步、耦合方式、渲染方式和稳定性。

更稳的第一步是：在同一个场景里放多个刚体对象，让它们在重力下落地，并记录每个对象的位置。这样已经开始处理“多个实体共享同一个世界”的问题，但还没有把求解器复杂度拉满。

最小场景可以包含：

| 实体 | 作用 |
|---|---|
| `Plane` | 地面，提供碰撞支撑 |
| `Box` | 方块，检查尺寸、位置和落地高度 |
| `Sphere` | 球，检查半径和接触稳定性 |
| `Cylinder` | 圆柱，检查不同形状的刚体接触 |

这一步仍然是刚体仿真。它的价值在于：开始关心不同实体的初始位置、几何尺寸、接触、最终状态和记录方式。后面换成布料、颗粒或流体时，这些习惯会直接决定排错效率。

## 一个可验收脚本

配套脚本是：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 GENESIS_STEPS=500 \
  python labs/06_genesis/02_multi_object_rigid.py
```

上面是 bash / WSL / Linux shell 写法。脚本会读取 `GENESIS_BACKEND`、`GENESIS_VIEWER` 和 `GENESIS_STEPS`；下面片段只展示核心物理结构，省略环境变量解析和输出保存：

```python
import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005, substeps=10),
    show_viewer=False,
)
scene.add_entity(gs.morphs.Plane())
box = scene.add_entity(gs.morphs.Box(size=(0.1, 0.1, 0.1), pos=(0.0, 0.0, 0.5)))
sphere = scene.add_entity(gs.morphs.Sphere(pos=(0.0, 0.2, 0.8), radius=0.06))
cylinder = scene.add_entity(
    gs.morphs.Cylinder(pos=(0.15, -0.1, 0.6), radius=0.04, height=0.12)
)

scene.build()

for _ in range(500):
    scene.step()
```

这段代码的重点不是物体多，而是每个对象都作为 `Entity` 加入同一个 `Scene`。`scene.build()` 之后，Genesis 会把这些实体放进同一条物理时间线上推进。

如果只想观察画面，可以把 `GENESIS_VIEWER=1`；如果是在服务器或容器里，先保持 `GENESIS_VIEWER=0`。

## 记录位置比只看画面可靠

多物体实验不能只说“看起来落地了”。脚本会把中间位置和最终位置写进当前运行目录的 `summaries/02_multi_object_rigid.json`，默认位于 `runs/genesis_codecheck_*/summaries/`：

```json
{
  "name": "02_multi_object_rigid",
  "steps": 500,
  "entities": ["Plane", "Box", "Sphere", "Cylinder"],
  "position_samples": [
    {
      "step": 100,
      "box_pos": [0.0, 0.0, 0.05],
      "sphere_pos": [0.0, 0.2, 0.06],
      "cylinder_pos": [0.15, -0.1, 0.06]
    }
  ],
  "final_positions": {
    "box": [0.0, 0.0, 0.05],
    "sphere": [0.0, 0.2, 0.06],
    "cylinder": [0.15, -0.1, 0.06]
  },
  "result": "passed"
}
```

这里的数值只是示意，不同版本和时间步设置可能略有差异。验收时更应该看三个问题：

1. 物体位置是否从初始高度下降到接近地面；
2. 最终高度是否和几何尺寸大致一致，例如 10 cm 方块中心高度接近 5 cm；
3. 输出里是否记录了每个对象，而不是只记录了场景是否运行。

这一步的好处是排错清晰。如果方块没有落下，先查重力、时间步和 `scene.step()`；如果物体穿过地面，先查尺寸、碰撞和求解参数；如果脚本没有输出位置，先查 `get_pos()` 和数据保存路径。

## 先把刚体基线跑扎实

上面的例子仍然属于刚体世界。它的价值在于建立“多实体、同场景、可记录”的习惯，而不是声称已经覆盖了软体或流体。

官方 Physics showcase 的前三项正好可以作为刚体入门参照：

| 示例 ID | 官方脚本 | 应该观察什么 |
|---|---|---|
| `physics_00_franka_cube` | `examples/rigid/franka_cube.py` | 机器人、方块、地面之间的刚体接触 |
| `physics_01_collision_tower` | `examples/collision/tower.py` | 多个刚体堆叠时是否稳定、是否穿模 |
| `physics_02_contype` | `examples/collision/contype.py` | 碰撞过滤不是画面效果，而是物理接触规则 |

这三项都被 headless camera 捕获并保存在 `runs/genesis_readme_showcase_canonical_20260608_055500/`。如果读不懂这三项，不建议直接跳到 MPM、PBD 或 IPC。刚体接触的基本直觉是后面所有耦合实验的前置条件。

<figure class="doc-figure">
<p class="doc-figure-title">刚体接触：Franka 与方块</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_00_franka_cube.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_00_franka_cube.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/rigid/franka_cube.py</code> 的真实运行。机器人、方块、地面之间的刚体接触，是后面所有耦合实验的基础。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">多刚体堆叠：碰撞塔</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_01_collision_tower.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_01_collision_tower.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/collision/tower.py</code>。多个刚体堆叠时是否稳定、是否穿模，是刚体基线的关键观察点。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">碰撞过滤：contype</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_02_contype.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_02_contype.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/collision/contype.py</code>。碰撞过滤不是画面效果，而是物理接触规则。</p>
</figure>

读这三项时，不要只看 contact sheet。比如 `physics_01_collision_tower` 和 `physics_02_contype` 的 summary 都记录了：

```json
{
  "resolution": [1060, 580],
  "captured_frames": 75,
  "capture_errors": [],
  "error": null,
  "result": "passed"
}
```

这说明它们不仅有最终截图，也有连续帧、统一分辨率和无 capture error 的记录。刚体入门阶段就要养成这种读法：先看画面建立直觉，再看 summary 确认帧数、错误字段和输出路径，最后再决定它能支撑什么结论。

## 进入非刚体前的检查清单

在写软体、颗粒或流体脚本前，先确认刚体基线已经稳定：

| 检查项 | 为什么重要 |
|---|---|
| 刚体场景能稳定 step | 先证明环境、后端和时间步没有基础问题 |
| 尺寸和单位合理 | 过大或过小都会影响接触和数值稳定 |
| 能保存状态或图像 | 后续非刚体现象不能只靠肉眼判断 |
| 单对象能跑通 | 不要第一步就让机器人、软体、流体和相机同时出现 |
| 记录求解参数 | `dt`、`substeps`、材料和分辨率会直接影响结果 |

尤其要注意 `dt` 和 `substeps`。多物理对象越复杂，时间步越不能随意设置。初学时先用官方示例或配套脚本里的保守参数，不要一边改后端、一边改材料、一边加并行环境。

真正进入非刚体后，问题会变成：软体要看形变状态，布料要看折叠和自碰撞，颗粒要看粒子数量和堆积行为，流体要看自由表面和边界，刚柔耦合还要同时考虑机器人控制和物体形变。本页先不展开这些细节，后面的 SPH / MPM / PBD 和非刚体验收页会分别拆开。

## 读完应能回答

1. 如果多刚体场景都不能稳定 step，为什么不应该直接调 MPM、PBD 或 IPC？
2. `physics_01_collision_tower` 和 `physics_02_contype` 分别更适合证明哪类刚体问题？
3. 多刚体脚本除了保存画面，为什么还要保存位置样本或最终状态？
4. 进入非刚体前，`dt`、`substeps`、材料和对象尺度中哪一项最容易被初学者忽略？

## 小结

- Genesis 的多物理能力很重要，但入门不要第一步就写软体或流体。
- 先用多个刚体对象练习 `Scene / Entity / build / step / get_pos`，把记录和验收习惯建立起来。
- 官方刚体 showcase 能作为视觉对照，但验收还要看 summary、log、帧数和错误字段。
- 进入软体、布料、颗粒或流体前，先保证刚体场景、状态记录和渲染产物稳定。

## 参考资料

- Genesis World Documentation, Beyond Rigid Bodies. https://genesis-world.readthedocs.io/en/latest/user_guide/physics/beyond_rigid_bodies.html
- Genesis World Documentation, Hello, Genesis World. https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/hello_genesis.html

## 导航

- 上一页：[多物理入门](../05-multiphysics.md)
- 返回目录：[多物理入门](../05-multiphysics.md)
- 下一页：[solver、material 与时间步](02-solver-material-timestep.md)
