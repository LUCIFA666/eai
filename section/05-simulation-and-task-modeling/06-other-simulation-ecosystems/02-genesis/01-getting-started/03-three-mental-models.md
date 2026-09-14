# 三个理解视角

上一页已经展示 Genesis 的最小脚本：`gs.init()`、创建 `Scene`、添加 `Entity`、`build()`、循环 `step()`。现在再回头解释它背后的结构。

Genesis 初学者最容易卡住的地方，不是第一段代码有多长，而是它同时包含三种理解视角：场景组织、多物理系统、批量环境。它们分别回答三个问题：世界里有什么？物理怎么算？为什么训练时要一批环境一起跑？

## 本节目标

本节围绕下面几个问题展开：

1. 为什么 Genesis 用 `Scene` 和 `Entity` 组织世界？
2. 多物理平台和普通刚体仿真器的区别在哪里？
3. 为什么 `n_envs` 是 Genesis 里很重要的入口？
4. 初学时应该先掌握哪一个理解视角，哪些可以暂时只知道存在？

## Scene 和 Entity

Genesis 的第一个理解视角是：

```text
Scene = 一个仿真世界
Entity = 世界里的一个对象
```

一个 `Scene` 里可以有地面、机器人、方块、相机、灯光和各种物理对象。Genesis 不是直接从一个完整模型文件开始，而是用 Python 往场景里逐个添加对象：

下面短片段沿用上一页的 `import genesis as gs`，只用来说明场景组装关系：

```python
scene = gs.Scene()
scene.add_entity(gs.morphs.Plane())
robot = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
```

这个写法属于“先有一个世界，再往世界里放对象”的场景图式接口。它和 MuJoCo 的单文件模型入口不一样，但学习问题没有变：仍然要知道世界里有哪些对象、它们的坐标在哪里、哪些对象会参与物理、哪些只是视觉或传感。

初学时先问四个问题：

| 问题 | 例子 |
|---|---|
| 场景里有什么？ | 平面、Franka、方块、相机 |
| 每个对象怎么来的？ | 内置几何体、MJCF、URDF、mesh |
| 它是否参与物理？ | 地面和机器人参与碰撞，相机只负责观察 |
| 它什么时候生效？ | `scene.build()` 之后进入可运行状态 |

一句话：**先别急着控制机器人，先弄清楚世界是怎么被组装出来的。**

官方 showcase 中，`physics_00_franka_cube` 就是这个模型的最小证据：它不是先讲复杂多物理，而是从 `Plane + Franka + cube` 开始，最后保存预览图和一段 `1060x580` 的预览视频。读这个示例时，第一眼看机器人和方块，第二眼就要回到场景：地面、机器人、方块分别是什么实体，它们在 `build()` 前后处于什么阶段。

<figure class="doc-figure">
<p class="doc-figure-title">Scene / Entity 的最小证据：Plane + Franka + 方块</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_00_franka_cube.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_00_franka_cube.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/rigid/franka_cube.py</code> 的真实运行：同一个 <code>Scene</code> 里，地面、Franka、方块是三个 <code>Entity</code>，<code>build()</code> 之后才进入可运行状态。看画面时第二眼要落回“世界由哪些实体组装而成”。</p>
</figure>

## 多物理

Genesis 的第二个理解视角是多物理。这里的重点不是背术语，而是理解：不同物理对象的状态表示、求解方法和稳定性问题可能完全不同。

刚体世界里，重点关心的是：

- 关节角、关节速度；
- 碰撞体、质量、摩擦；
- 接触力和约束；
- actuator 和控制目标。

多物理世界里，还可能出现：

- 软体的形变；
- 布料的折叠和拉扯；
- 颗粒的堆积和流动；
- 液体的运动；
- 刚体和这些对象之间的耦合。

所以“Genesis 支持多物理”不只是功能更多，而是问题类型变了。机械臂抓方块和机械臂抓软海绵，表面上都是“抓取”，底层物理难度并不一样。

初学时建议只做一个限制：**第一轮只用刚体**。先用刚体场景学会 `Scene`、`Entity`、`build()`、`step()` 和控制接口。等这些稳定后，再把软体、布料或颗粒作为单独专题引入。

官方 Physics 复现结果可以帮助判断哪些素材属于这个理解视角：`physics_04_mpm`、`physics_05_sand_wheel`、`physics_09_pbd_cloth`、`physics_11_ipc_cloth_teleop`、`physics_15_water_wheel` 都不是“更多刚体”，而是状态表示、材料、求解器和验收方式都变了。把它们放到入门第一天，会让学习者同时面对太多变量。

## 批量环境

Genesis 的第三个理解视角是批量环境。强化学习训练常常需要很多环境同时采样，而不是一个机器人慢慢跑。

在 Genesis 里，批量环境的入口很直接：

```python
B = 20
scene.build(n_envs=B, env_spacing=(1.0, 1.0))
```

这表示同一个场景复制出 `B` 份。可视化时，`env_spacing` 控制它们在 viewer 里的间距；计算时，很多状态和动作都要理解成带 batch 维度的数据。

单环境时，可这样理解：

```text
action: [num_actions]
state:  [state_dim]
```

批量环境时，要这样想：

```text
action: [num_envs, num_actions]
state:  [num_envs, state_dim]
```

这和许多向量化环境里的 `num_envs` 思维相通：一次不是跑一个任务，而是同时跑一批结构相同、状态不同的任务。

初学时可以先不训练策略，只做一个批量控制实验。下面的片段保留必要 import，并假设前面已经执行 `scene.build(n_envs=B, ...)`，`robot` 是场景里的机器人对象，`gs.device` 来自 `gs.init(...)` 后的 Genesis 运行设备：

```python
import genesis as gs
import torch

B = 20
target = torch.zeros(B, 9, device=gs.device)
robot.control_dofs_position(target)
```

如果能解释为什么动作张量是 `[B, 9]`，就已经抓住批量环境最重要的直觉了。

官方 `Simulation Interface` 运行结果里有几条正好对应这个理解视角：

| 素材 | 复现结果 | 它说明什么 |
|---|---|---|
| `sim_02_heterogeneous_envs` | `133` 帧，`result: passed` | 批量环境里可以放不同对象，视觉上能看到环境差异 |
| `sim_03_domain_randomization` | `1` 帧，`result: passed` | 随机化不一定需要长视频，关键是记录配置和差异 |
| `sim_15_batched_ik` | `result: passed` | IK 也可以批量化，但还要另用 shape 摘要证明张量语义 |

<figure class="doc-figure">
<p class="doc-figure-title">批量环境：一批环境同时求解 IK</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_15_batched_ik.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_15_batched_ik.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/tutorials/batched_IK.py</code> 的真实运行：同一个场景被复制成一批环境同时求解 IK。画面是“一批结构相同、状态不同的任务一起跑”，但真正的证据仍是动作张量的第一维 <code>num_envs</code>。</p>
</figure>

这张表提醒的是：showcase 视频能证明“官方示例跑出了可视化结果”，但不能替代 `action_shape`、`envs_idx` 这类结构化证据。批量环境的核心仍然要回到张量第一维。

## 学习顺序

这三个理解视角不要一起学深。建议顺序是：

1. **Scene / Entity**：先学世界怎么搭，这是所有 Genesis 脚本的入口。
2. **批量环境**：再学 `n_envs`，因为它直接关系到机器人学习。
3. **多物理**：最后再展开软体、布料、颗粒和流体，因为它会显著增加调试难度。

为什么把多物理放到后面？因为多物理是 Genesis 的亮点，但不是初学者的地基。没有刚体场景、控制、观察和批量环境的基础，直接上多物理很容易变成“画面很丰富，但不知道哪里出了问题”。

## 读代码的路线

以后读一个 Genesis 示例，不要从中间某个控制函数开始钻。建议按这条路线看：

```text
gs.init(...)
  -> Scene 配置
  -> add_entity：地面、机器人、物体、相机
  -> build：单环境还是 n_envs 批量环境
  -> reset / 初始状态
  -> control：动作或目标
  -> step：推进循环
  -> observe / render / save
```

这条路线对应本页的三个理解视角：先看世界怎么组装，再看物理对象属于哪一类，最后看是不是批量环境。

## 读完应能回答

1. `physics_00_franka_cube` 为什么适合用来说明 `Scene / Entity`，而不是直接拿来说明多物理？
2. `sim_15_batched_ik` 有视频和 `result: passed`，为什么还需要额外记录 `action_shape` 或 batch 维度？
3. 如果一个示例同时用了 Nyx、GUI、批量环境和多物理，初学者应该先把它拆成哪几层来读？

## 小结

- `Scene` 是仿真世界，`Entity` 是世界里的对象；Genesis 的第一件事是组装世界。
- 多物理不是“更多刚体”，而是不同物理系统和耦合问题；初学第一轮先用刚体。
- `n_envs` 表示一批环境，动作和状态都要带 batch 维度。
- 学习顺序建议是：先 Scene / Entity，再批量环境，最后多物理。
- 读代码时固定从 `init -> Scene -> add_entity -> build -> control -> step` 这条线往下看。

## 参考资料

- Genesis World Documentation, Hello, Genesis World. https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/hello_genesis.html
- Genesis World Documentation, Parallel Simulation. https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/parallel_simulation.html

## 导航

- 上一页：[第一次仿真](02-first-simulation.md)
- 返回目录：[认识 Genesis](../01-getting-started.md)
- 下一页：[安装与环境检查](04-install-and-env-check.md)
