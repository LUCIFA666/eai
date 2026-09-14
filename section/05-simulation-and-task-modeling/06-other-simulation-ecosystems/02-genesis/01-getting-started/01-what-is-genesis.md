# Genesis 是什么

`Genesis`是 Python-first 的多物理仿真平台，不是新版 MuJoCo，也不是轻量版 Isaac Sim。

## 本节目标

本节围绕下面几个问题展开：

1. Genesis World 的平台定位是什么？
2. 它和物理引擎、任务框架、渲染平台分别有什么区别？
3. 为什么初学时不能只记住“多物理”和“并行”？
4. 本节后面的第一次仿真要验证哪条最小链路？

## 一句话定位

Genesis World 可以先理解成：**用 Python 组织场景，用统一接口连接多物理、渲染、传感器和并行环境的仿真平台**。

这句话里有四个关键词：

| 关键词 | 含义 |
|---|---|
| Python-first | 初学入口是脚本，不是复杂 GUI 工程 |
| 多物理 | 不只刚体，还覆盖软体、布料、颗粒、流体和耦合 |
| 渲染 / 传感 | 可以输出 camera、sensor，也可接 Nyx 这类渲染插件 |
| 并行环境 | 可以用 `n_envs` 把一个场景复制成一批环境 |

它不是 MuJoCo 的替代品，也不是 Isaac Sim 的轻量版。MuJoCo 更成熟、轻量、适合刚体控制和算法原型；Isaac Sim 更偏 USD / RTX / ROS 2 工程生态；Genesis 的辨识度在于把更宽的物理对象放进一个 Python 场景系统里。

## 四层结构

读 Genesis 时，可以把它分成四层：

| 层 | 常见对象 | 初学任务 |
|---|---|---|
| Simulation Interface | `gs.init()`、`Scene`、`Entity`、`build()`、`step()` | 把世界搭起来并推进 |
| Physics | Rigid、FEM、MPM、SPH、PBD、IPC、SAP | 理解物理对象和 solver |
| Render / Sensor | camera、viewer、LiDAR、IMU、Nyx | 保存观测并验收图像 |
| Compiler / Backend | CPU、CUDA、设备缓存和首次构建 | 知道代码在哪个设备上跑 |

第一次学习只抓第一层：能导入、能建场景、能加地面和机器人、能 `build()`、能 `step()`。后面的多物理和 Nyx 都是扩展，不是第一步。

## 不要被 showcase 带跑

官方 README showcase 覆盖面很宽，也确实包含视觉效果很强的条目。但初学者不宜从 Nyx 或流体例子开始。更好的学习顺序是：

```text
最小刚体场景 -> Scene / Entity -> robot control -> camera / sensor -> n_envs -> multiphysics -> Nyx / GUI / advanced coupling
```

这条路线的核心是降低变量数量。先理解一个普通刚体场景为什么能跑，再去理解为什么 MPM、SPH、PBD、IPC 和 Nyx 会额外引入依赖、参数和验收成本。

## 把 showcase 当成证据索引

官方 showcase 对初学者最有价值的地方，不是“看起来很丰富”，而是它能把 Genesis 的能力拆成可查询条目。本书已经把 45 个条目整理成两组主证据目录：canonical 目录覆盖 `Physics` 和 `Simulation Interface` 共 36 项，Rendering 目录覆盖 Genesis core rendering 2 项和 Nyx rendering 7 项。

第一次读这些素材时，可以只记下面这张小表：

| 学习目标 | 先看哪个素材 | 先确认什么 |
|---|---|---|
| 最小刚体世界 | `physics_00_franka_cube` | `Plane + Franka + cube` 能在脚本里构建、step、录制 |
| 机器人控制 | `sim_00_control_your_robot` | 控制示例能生成可见运动，但还要回到 dof 摘要 |
| 程序化相机 | `render_00_follow_entity` | camera 可以跟随场景实体，而不是只截图 viewer |
| 传感器读数 | `sim_06_lidar`、`sim_08_contact_force` | 图像只是展示，真正证据在 sensor metrics 或历史曲线 |
| 渲染插件边界 | `render_03_nyx_attached_camera` | 成功视频要和 no-adapter 失败日志一起读 |

这张表的作用是抵抗“先学视觉效果最强素材”的冲动。刚开始只要会用 `physics_00_franka_cube` 理解场景、用 `sim_00_control_your_robot` 理解控制、用 `render_00_follow_entity` 理解相机，就已经足够进入后面的页面。

证据索引表的第一行 `physics_00_franka_cube` 就是入门主线，下面先看它真实跑出来的样子：

<figure class="doc-figure">
<p class="doc-figure-title">证据索引第一项：最小刚体世界</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_00_franka_cube.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/physics_00_franka_cube.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">证据索引表第一行对应的 <code>physics_00_franka_cube</code>（官方 <code>examples/rigid/franka_cube.py</code>）：Franka 在 <code>Plane</code> 上抓取方块，是入门主线“最小刚体世界”的画面。下一页[第一次仿真](02-first-simulation.md)会动手把这条链路跑起来。</p>
</figure>

## 读完应能回答

1. 如果一个任务只有刚体机械臂推方块，为什么不一定要用 Genesis？
2. 如果一个官方示例能在 viewer 里显示，为什么仍然不等于能在无头服务器上保存 camera 视频？
3. 看到 `n_envs=8` 时，第一反应应该检查什么 shape？

## 小结

- Genesis 是 Python-first 的多物理仿真平台，不只是物理引擎。
- 入门先抓 `init -> Scene -> add_entity -> build -> step`。
- 多物理、并行和 Nyx 是它的亮点，但不应该成为第一步。
- 读官方示例时先判断它属于接口、物理、渲染还是后端问题。

## 导航

- 上一页：[认识 Genesis](../01-getting-started.md)
- 返回目录：[认识 Genesis](../01-getting-started.md)
- 下一页：[第一次仿真](02-first-simulation.md)
