# Scene 与 Entity

本页讲 Genesis 中最基础的场景组织方式：`Scene` 是仿真世界，`Entity` 是加入世界的物理对象。机器人资产、刚体物体、多物理对象和并行环境里的对象会通过 `Entity` 进入场景；camera / sensor 也由 `Scene` 管理，但通常使用 `add_camera()` 或 `add_sensor(...)` 这类接口，不等同于普通 `add_entity()` 对象。

## 本节目标

本节围绕下面几个问题展开：

1. `Scene` 在 Genesis 中承担什么职责？
2. `Entity` 可以来自哪些对象类型或资产格式？
3. `scene.add_entity()` 和 `scene.build()` 的边界在哪里？
4. 初学时如何检查一个对象是否真的加入了场景？

## Scene 是世界，Entity 是对象

在 Genesis 里，`Scene` 是仿真世界的容器，`Entity` 是加入世界的对象。地面、机器人、方块、球、网格资产，甚至后面多物理对象，都会通过场景组织起来。

本页代码片段默认已经完成 `import genesis as gs`。它们用于解释 `Scene / Entity / build` 的顺序；完整可运行脚本见 `labs/06_genesis/01_first_simulation.py` 和 `labs/06_genesis/02_multi_object_rigid.py`。

最小结构是：

```python
scene = gs.Scene(show_viewer=False)
plane = scene.add_entity(gs.morphs.Plane())
robot = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
scene.build()
```

`add_entity()` 仍然是在 Python 层描述世界；`build()` 之后，Genesis 才把这些描述变成可推进的底层数据结构。初学者最常见的错误，是加完对象后直接 `step()`，或者 `build()` 之后又随意改场景结构。

## 常见实体入口

| 入口 | 典型用途 |
|---|---|
| `gs.morphs.Plane()` | 地面和碰撞基准 |
| `gs.morphs.Box()` / `Sphere()` / `Cylinder()` | 刚体对象和接触测试 |
| `gs.morphs.MJCF(...)` | 官方 Franka、MuJoCo 风格机器人资产 |
| `gs.morphs.URDF(...)` | URDF 机器人资产 |
| `gs.morphs.Mesh(...)` | GLB / OBJ 等网格对象 |

官方 showcase 中从刚体到多物理对象都在反复使用这个思路：先把物理对象加入 `Scene`，再构建，再推进。相机和传感器同样挂在 `Scene` 上，但它们的 API 会在观察与渲染组单独处理。

配套的官方资产取景脚本也能说明 `Entity` 的宽度。它不是只加载 Franka，而是把 12 个官方资产都作为实体放进简单场景里：

- MJCF 机器人：`franka_mjcf`、`ur5e_mjcf`；
- URDF 机器人：`go2_urdf`、`cf2x_drone_urdf`、`kuka_iiwa_urdf`、`shadow_hand_urdf`；
- mesh 物体：`duck_mesh`、`dragon_mesh`、`bunny_mesh`、`boat_mesh`、`bathtub_mesh`、`tank_mesh`。

这些对象格式和用途不同，但第一轮都先用同一个问题检查：能否加入场景、能否 `build()`、能否被相机拍到。

对应证据目录是：

```text
runs/genesis_official_assets_20260608_020235/
  RUN_SUMMARY.json
  RUN_MANIFEST.jsonl
  artifacts/
```

这组证据适合放在 `Scene / Entity` 页，而不是机器人控制页。它证明的是“资产可以作为实体进入简单场景并被固定相机取景”，不证明 URDF / MJCF 的关节命名、控制目标、碰撞参数或任务奖励已经可用。初学者读资产图时要先问：这是一个能被看见的 `Entity`，还是一个已经能被控制和验收的 `Robot`？

## 如何检查对象加入成功

第一轮不用追求复杂 introspection。建议检查四件事：

1. `scene.build()` 是否成功；
2. 日志里是否出现资产加载或碰撞体 warning；
3. 运行后是否能读取对象状态或保存图像；
4. 如果是机器人资产，是否另有 dof、joint name 和控制摘要。

配套脚本 `02_multi_object_rigid.py` 会把方块、球、圆柱的位置样本写入 JSON，这比只看 viewer 更可靠。

## 从官方素材反推 Scene / Entity

官方 README 的很多素材看起来差别很大，但第一步都绕不开 `Scene` 和 `Entity`。可以用三类素材反推这个共同入口：

| 素材 | 表面上在展示什么 | 回到本页要看什么 |
|---|---|---|
| `physics_00_franka_cube` | Franka 和方块接触 | 机器人、方块、地面都先作为实体加入场景 |
| `sim_02_heterogeneous_envs` | 一批环境里对象不同 | 每个环境复制的是构建后的场景结构 |
| `render_00_follow_entity` | 相机跟随对象 | 相机跟随的目标仍然是场景里的实体 |

所以本页虽然朴素，却是后面所有内容的共同底座。多物理对象、传感器、机器人和批量环境只是实体类型、求解器和输出方式不同，场景组织的基本动作没有变。

## 读完应能回答

1. `scene.add_entity(...)` 和 `scene.build()` 分别发生在什么阶段？
2. 为什么 `build()` 后再随意添加对象容易导致排错困难？
3. 如果 viewer 里看见了物体，但摘要里没有对象状态或图像产物，这算不算可靠验收？

## 小结

- `Scene` 组织世界，`Entity` 是世界里的对象。
- `add_entity()` 是描述阶段，`build()` 是进入可运行阶段。
- 初学先用 Plane、Box、Sphere、MJCF，不要第一步就导入复杂自定义资产。

## 导航

- 上一页：[场景、实体与机器人](../02-scene-entity-robot.md)
- 返回目录：[场景、实体与机器人](../02-scene-entity-robot.md)
- 下一页：[机器人资产加载](02-robot-assets.md)
