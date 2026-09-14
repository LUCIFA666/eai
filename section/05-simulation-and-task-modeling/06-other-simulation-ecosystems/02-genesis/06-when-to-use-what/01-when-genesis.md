# 什么时候选 Genesis

本页讲哪些任务适合优先考虑 Genesis：多物理对象、Python-first 场景组织、批量环境和新平台探索。

## 本节目标

本节围绕下面几个问题展开：

1. 什么任务能体现 Genesis 的优势？
2. 多物理、并行和 Python 接口分别对应哪些需求？
3. 什么时候 Genesis 适合作为项目平台？
4. 选择 Genesis 时应提前接受哪些版本和调试成本？

## 适合选 Genesis 的任务

优先考虑 Genesis 的典型情况是：

| 需求 | 为什么适合 |
|---|---|
| 多物理交互 | Genesis 官方 Physics 示例覆盖刚体、FEM、MPM、SPH、PBD、IPC、SAP |
| 刚柔耦合探索 | 布料、颗粒、流体、软体与刚体对象的同场景交互是它的辨识度；涉及机器人时还要另存控制链路证据 |
| Python-first 原型 | 场景、实体、相机、传感器都可以从脚本组织 |
| 批量环境直觉 | `scene.build(n_envs=...)` 有助于理解并行采样 |
| 新平台调研 | 适合比较 API、后端和多物理能力 |

选择 Genesis 时，也要接受版本变化、可选依赖和 adapter 成本。比如 Nyx 渲染要额外插件，IPC 示例要额外依赖和材料适配，GUI 示例在无界面服务器上不一定完整可视化。

<figure class="doc-figure">
<p class="doc-figure-title">能力展示：四旋翼无人机</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_16_drone.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_16_drone.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/drone/fly.py</code>。除了机械臂，Genesis 也覆盖无人机这类带控制的刚体系统（这里是单架四旋翼按轨迹飞行）。官方 README 的 Drone 条目对应的是需要先做 RL 训练的 <code>hover_train.py</code>，本页录制用免训练的 <code>fly.py</code> 演示同一能力。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">能力展示：软体蠕虫运动</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_17_advanced_worm.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_17_advanced_worm.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/tutorials/advanced_worm.py</code>。软体蠕虫的运动代表多物理（软体 + 控制）能力，已超出纯刚体范畴。</p>
</figure>

## 从运行证据倒推

45 项官方 showcase 运行给了一个更具体的判断方法。不要只问“Genesis 支不支持某功能”，而要问这个功能在项目里属于哪一层：

| 项目需求 | 可以引用的运行证据 | 选 Genesis 的理由 |
|---|---|---|
| 布料 / 刚柔耦合现象 | `physics_09_pbd_cloth`、`physics_12_cloth_on_rigid`、`physics_11_ipc_cloth_teleop` | 任务对象已经超出纯刚体；`physics_11` 还带 robot cloth 语义，但要说明 IPC 依赖和 material adapter |
| 刚体与颗粒 / 流体现象 | `physics_05_sand_wheel`、`physics_06_sph_rigid`、`physics_15_water_wheel` | 需要 MPM / SPH / coupling 直觉；这些素材本身不直接证明机械臂任务已覆盖 |
| 传感器读数可视化 | `sim_04_depth_camera`、`sim_06_lidar`、`sim_08_contact_force` | 不只要 RGB，还要结构化 sensor 数据 |
| 批量环境理解 | `sim_02_heterogeneous_envs`、`sim_15_batched_ik` | 需要理解 `n_envs`、batch action、部分环境控制 |
| 渲染插件探索 | `render_02_nyx_hello` 到 `render_08_nyx_multi_camera_multi_env` | 研究渲染后端和 sensor plugin，而不是只做最小仿真 |

如果一个项目能在这张表里找到明确对应项，Genesis 就有充分理由进入候选。反过来，如果项目只需要单机械臂、刚体方块、固定相机和基础 RL，那么选择 Genesis 的理由就不够强。

## 不要只写素材 ID

选型说明里只写“参考了 `physics_05_sand_wheel`”还不够。这个 ID 只是索引，真正的证据要落到文件和限制条件：

| 要引用什么 | 说明 |
|---|---|
| `previews/<id>.png` 或 `videos/<id>.mp4` | canonical run 的单条素材路径；Rendering / Nyx 条目应以 `RUN_SUMMARY.json` 或 `summaries/<id>.json` 中记录的 preview / video 字段为准 |
| `summaries/<id>.json` | 证明帧数、分辨率、耗时、`result` 和可能的 metrics |
| `logs/<id>.log` | 证明依赖、warning、异常和后端信息没有被省略 |
| `STATUS.md` | 说明 adapter、proxy、短帧数、GUI 依赖或 Nyx 版本边界 |
| 本地 codecheck / 项目摘要 | 证明最小链路通过，而不是只引用官方 showcase |

例如，选择 Genesis 做颗粒介质任务时，可以引用 `physics_05_sand_wheel` 作为官方能力入口，但第一阶段仍要保存本地 `summary.json`、solver/material 参数和运行日志。选择 Genesis 做渲染插件探索时，可以引用 `render_03_nyx_attached_camera`，但必须同时说明它有 no-adapter 失败日志和 `skip_path_planner_exclude_pairs` 这个作用范围很小的 adapter。这样选型理由才是工程判断，而不是素材点名。

## 第一阶段验收要保守

选 Genesis 不是意味着第一天就把所有能力打开。项目第一阶段建议只设三类验收：

1. 最小刚体场景能无界面运行，并保存 `summary.json`；
2. 目标物理对象单独能跑，例如布料、颗粒或流体；
3. 再做机器人和目标对象的耦合，不要同时加入 Nyx、GUI、并行训练和复杂控制器。

这也是本章一直强调证据链的原因。Genesis 的优势在宽度，但项目推进要靠分层验收。

## 不要为了“新”而选

如果任务只是关节控制、简单抓取或算法原型，Genesis 不一定比 MuJoCo 更省心。选 Genesis 的理由应该来自任务需求，而不是“它支持更多功能”。

## 读完应能回答

1. 任务能否明确引用一个多物理、传感器或并行素材，例如 `physics_09_pbd_cloth`、`sim_06_lidar` 或 `sim_15_batched_ik`？
2. 如果第一阶段不使用 Nyx、GUI 和复杂耦合，Genesis 仍然比 MuJoCo 更合适吗？为什么？
3. 准备保存哪些 `runs/` 证据来证明选型成立，而不是只引用平台介绍？

## 小结

- 选 Genesis 的理由应该来自任务中的多物理、传感器、批量环境或新平台探索需求。
- 第一阶段验收要保守，先证明最小现象和证据链，再叠加 GUI、Nyx、并行训练或复杂耦合。
- 如果任务只需要刚体控制和基础算法原型，Genesis 不一定比 MuJoCo 更省心。

## 导航

- 上一页：[Genesis 适用边界](../06-when-to-use-what.md)
- 返回目录：[Genesis 适用边界](../06-when-to-use-what.md)
- 下一页：[什么时候继续用 MuJoCo](02-when-mujoco.md)
