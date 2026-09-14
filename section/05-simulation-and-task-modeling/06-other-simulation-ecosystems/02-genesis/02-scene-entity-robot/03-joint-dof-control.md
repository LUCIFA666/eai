# 关节、自由度与控制

前两页已经验证了最小场景，也建立了 `Scene / Entity / build / step` 的理解视角。现在进入机器人控制。

这一页只讲最基础的一层：加载一个机器人，找到它的关节自由度，给关节发目标，让它动起来。本页暂时不讲运动规划、逆运动学、抓取策略或强化学习。先把一个核心区别说明清楚：**设置状态不是控制机器人**。

## 本节目标

本节围绕下面几个问题展开：

1. Genesis 里机器人通常怎么作为 `Entity` 加入场景？
2. 为什么要先找到关节对应的 dof 索引？
3. `set_dofs_position()` 和 `control_dofs_position()` 的第一层区别是什么？
4. 初学时需要先知道哪些控制参数会影响效果？
5. 怎样验证一个控制脚本至少没有把 dof 和目标写错？

## 机器人也是 Entity

在 Genesis 里，机器人不是一个特殊的外部系统，而是场景里的一个 `Entity`。可控机器人入门优先使用 MJCF 或 URDF 这类带关节、dof 和控制语义的资产；mesh 更适合作为物体或机器人描述内部的视觉 / 碰撞资源，单独 mesh 不等于可控机器人。以 Franka 为例：

本页前半部分的短代码默认已经完成 `import numpy as np`、`import genesis as gs`，并且 `scene`、`franka`、`dofs_idx` 会按上下文逐步创建。页面后半段会给出一个更完整的最小控制脚本。

```python
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)
```

这个写法有两个含义：

- 从场景角度看，Franka 和地面、方块一样，都是 `Scene` 里的实体；
- 从控制角度看，Franka 这个实体会暴露关节、dof、控制器和状态接口。

初学时建议先使用官方示例里的 Franka，不要第一步就换成自定义 URDF。自定义机器人会带来惯量、关节轴、碰撞体、限位、命名等一串额外问题。

## 先找到要控制的 dof

控制机器人前，先要知道控制的是哪些自由度。Genesis 官方示例会通过关节名找到局部 dof 索引：

```python
jnt_names = [
    "joint1",
    "joint2",
    "joint3",
    "joint4",
    "joint5",
    "joint6",
    "joint7",
    "finger_joint1",
    "finger_joint2",
]
dofs_idx = [franka.get_joint(name).dof_idx_local for name in jnt_names]
```

这一步看起来只是取索引，实际很重要。机器人控制最怕“以为命令在控制 A 关节，实际上发到了 B 关节”。所以第一条验收不是让机器人动，而是打印和核对关节名：

```python
for name, idx in zip(jnt_names, dofs_idx):
    print(name, idx)
```

如果换机器人，首先要重新核对关节名和 dof 数量。不要把 Franka 的 9 维目标向量直接套到别的机器人上。

这也是为什么配套摘要要保存 `joint_names` 和 `dofs_idx`。canonical run 中的 `runs/genesis_readme_showcase_canonical_20260608_055500/summaries/sim_00_control_your_robot.json` 及对应视频能说明官方机器人控制示例已经可运行，但它不能替代本地目标向量与关节索引之间的核对。对初学者来说，关节索引表本身就是控制实验的第一份证据。

<figure class="doc-figure">
<p class="doc-figure-title">机器人基础控制</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_00_control_your_robot.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_00_control_your_robot.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/tutorials/control_your_robot.py</code>。控制示例能生成可见运动，但仍要回到 dof 摘要核对关节索引与目标，视频不能替代结构化证据。</p>
</figure>

## 状态设置和控制命令

控制页先抓住一个区别：`set_*` 是直接写状态，`control_*` 是发送控制目标。下一页会专门拆 reset、action 和 observe；这里先看最小控制动作：

```python
target = np.array([0, 0, 0, -1.0, 0, 1.0, 0, 0.04, 0.04])
franka.control_dofs_position(target, dofs_idx)
for _ in range(200):
    scene.step()
```

这时机器人不会被瞬间写到目标位置，而是由控制器和物理系统逐步推动过去。中间会受到增益、阻尼、关节限制、力限制和接触的影响。

| 接口 | 第一层判断 |
|---|---|
| `set_*` | 适合准备初始状态，不能单独证明执行过程 |
| `control_* + scene.step()` | 才能说明目标通过控制器进入物理循环 |

## 增益和力限制

位置控制不是只给一个目标角度就结束。控制器还需要知道追目标时有多“用力”、多“阻尼”、最大力能到哪里。第一遍不必背具体数值，只要知道这些参数会改变运动过程：

初学时可以这样理解：

| 参数 | 直觉 |
|---|---|
| `kp` | 离目标越远，拉回来的趋势越强 |
| `kv` | 抑制速度，减少抖动和过冲 |
| `force_range` | 控制器能施加的力或力矩范围 |

Genesis 官方控制示例会设置这些参数；配套脚本先保留最小控制链路，避免第一遍把 dof 核对、reset、控制参数和任务逻辑混在一起。它和 MuJoCo 里的 position actuator、damping、forcerange 是同一类学习问题：目标只是“想去哪”，增益和力限制决定“怎么去”。

## 最小控制脚本结构

一个最小控制脚本可以按这个结构写：

```python
import numpy as np
import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(show_viewer=False)
scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
scene.build()

jnt_names = [
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
]
dofs_idx = [franka.get_joint(name).dof_idx_local for name in jnt_names]

franka.set_dofs_position(
    np.array([0, 0, 0, -1.0, 0, 1.0, 0, 0.04, 0.04]),
    dofs_idx,
)

target = np.array([0.3, 0.2, 0.0, -1.2, 0.0, 1.2, 0.2, 0.02, 0.02])
franka.control_dofs_position(target, dofs_idx)

for _ in range(300):
    scene.step()
```

这个脚本有意不加入复杂任务。它只验证三件事：

1. 机器人资产能加载；
2. 关节名能映射到 dof；
3. 位置控制命令能在 step 循环里产生运动。

## 验收标准

这一页的动手练习可以先运行配套脚本：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 GENESIS_STEPS=300 \
  python labs/06_genesis/03_robot_and_control.py
```

运行后不要只看 viewer，先打开 `summaries/03_robot_and_control.json`。这一页可以这样验收：

| 练习 | 验收标准 |
|---|---|
| 关节索引核对 | `joint_names` 和 `dofs_idx` 都有 9 项，并能解释前 7 个是机械臂、后 2 个是夹爪 |
| reset 姿态 | `reset_q` 是稳定初始姿态，不和控制目标混写 |
| 位置控制 | `target_q` 与 `reset_q` 不同，`control_steps` 记录了后续 step 数 |
| 概念区分 | 能说出 `set_*` 和 `control_*` 的区别，并知道视频不能替代 dof 核对 |

如果只能写出 `set_dofs_position()`，但没有 `scene.step()` 后的控制过程，那还没有真正进入控制。反过来，如果能解释 `reset_q`、`target_q`、增益、力限制和实际运动之间的关系，就已经跨过了第一道门槛。

可以把本页的证据分成两类：

| 证据 | 说明 |
|---|---|
| canonical run 中的 `sim_00_control_your_robot` 预览 / 视频 | 官方控制示例可以在 `1060x580` 下跑出可见运动 |
| `03_robot_and_control.json` | 本地脚本记录关节名、dof 索引、reset 目标、control 目标和 step 数 |

前者给直觉，后者给可审查的控制语义。写控制实验时，两类都要有；只放动图，很容易忽略 dof 和控制目标的对应关系。

<figure class="doc-figure">
<p class="doc-figure-title">进阶：微分 IK 控制器</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_14_diff_ik.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_14_diff_ik.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/rigid/diffik_controller.py</code>。比直接发关节目标更进一步：给末端位姿，由微分 IK 解算出关节命令。先掌握上面的关节控制，再看这一层。</p>
</figure>

## 常见误解

| 误解 | 实际 |
|---|---|
| 机器人不动就是 Genesis 坏了 | 先检查 dof 索引、目标是否变化、是否在循环里 `scene.step()` |
| `set_dofs_position()` 就是位置控制 | 它更像直接写状态，常用于 reset |
| `control_dofs_position()` 会瞬间到目标 | 它只是发目标，运动要由控制器和物理逐步产生 |
| 增益越大越好 | 过大可能抖动、不稳定或被力限制截断 |
| 换机器人只要换文件路径 | 还要重新核对关节名、dof 数、限位、控制方式和碰撞体 |

## 读完应能回答

1. 看到一段机器人运动视频时，为什么仍然要检查 `joint_names` 和 `dofs_idx`？
2. `reset_q` 和 `target_q` 如果完全相同，控制实验的结论应该怎样写得更保守？
3. `set_dofs_position()` 和 `control_dofs_position()` 分别适合放在实验流程的哪一步？
4. 如果换成新 URDF 后机器人不动，除了资产路径，还要核对哪些控制相关字段？

## 小结

- Genesis 里的机器人通常作为 `Entity` 加入 `Scene`。
- 控制前先通过关节名找到 dof 索引，避免命令发错对象。
- `set_dofs_position()` 适合 reset 或直接设置状态；`control_dofs_position()` 才是给控制器发位置目标。
- `kp`、`kv` 和 `force_range` 会影响机器人追踪目标的方式。
- 入门控制脚本的核心验收是：能加载机器人、核对 dof、发目标，并在 step 循环中看到逐步运动。
- 官方控制视频提供视觉直觉，本地 JSON 摘要负责证明 dof 和目标语义。

## 参考资料

- Genesis World Documentation, Control Your Robot. https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/control_your_robot.html

## 导航

- 上一页：[机器人资产加载](02-robot-assets.md)
- 返回目录：[场景、实体与机器人](../02-scene-entity-robot.md)
- 下一页：[reset 与 control](04-reset-and-control.md)
