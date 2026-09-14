# Genesis 适用边界

学到这里，Genesis 的定位、第一次仿真、`Scene / Entity`、基础控制、观察渲染、批量环境和多物理入门验收都已经有了基本线索。最后要回到一个工程问题：**什么时候真的该选 Genesis？**

仿真平台不是越新越好，也不是功能越多越好。平台选择要从任务倒推：需要什么物理、什么观测、多少环境、什么训练接口、什么工程生态、什么复现要求。本页是总判断，后面几页再分别展开 Genesis、MuJoCo、Isaac Sim / Isaac Lab 和项目选型模板。

## 本节目标

本节围绕下面几个问题展开：

1. Genesis 最适合哪类实验和研究探索？
2. 什么时候应该继续用 MuJoCo？
3. 什么时候更应该用 Isaac Sim / Isaac Lab？
4. Genesis 和 SAPIEN / ManiSkill、Habitat 的边界在哪里？
5. 做项目报告时如何写一份简单的平台选择理由？

## 先从任务需求倒推

选择仿真器前，先不要问“哪个平台最强”。先问下面五个问题：

1. 当前任务主要是刚体控制，还是多物理交互？
2. 当前观测主要是状态量，还是高保真视觉 / 传感器？
3. 项目需要成熟任务库，还是需要自建任务？
4. 项目需要多少并行环境？
5. 项目需要长期稳定复现，还是做前沿探索？

这五个问题比平台宣传更重要。一个平台的强项如果和任务需求不匹配，就会变成额外负担。

官方 showcase 运行实验给了一个更具体的判断：Genesis 的亮点确实在多物理、传感器接口、并行环境和可选渲染插件，但这些能力并不是同一层难度。

| 能力 | 运行状态 | 对选型的含义 |
|---|---|---|
| 刚体 / 接触 | Physics 前三项直接 headless capture | 入门和基础控制可以稳定作为说明材料 |
| 非刚体 / 多物理 | FEM、MPM、SPH、PBD、coupler 均能生成素材 | 适合做多物理探索，但要记录 solver、material、时间步 |
| 高级耦合 | IPC、SAP 跑通但有 adapter / 依赖要求 | 适合研究探索，不适合毫无准备地作为第一课 |
| 传感器 | depth、IMU、LiDAR、ContactForce 等可复现 | 需要区分原始传感器数据和说明性可视化 overlay |
| GUI 交互 | ImGui、mouse plugin 在无界面环境要 proxy 或标 GUI 依赖 | 远程服务器不要把 GUI 当成唯一验收 |
| Rendering / Nyx | Rendering 组有 9 条 summary；`videos/` 及其子目录下保留 3 个 MP4，具体路径以 summary 字段为准；Nyx 需要额外插件和视频编码依赖 | 适合渲染专题，不应混入最小 Genesis 安装 |

这张表的意思不是“Genesis 不稳定”，而是提醒：**平台能力越宽，越要分层验收**。刚体、传感器、多物理、GUI、Nyx 不应该被写成同一个难度等级，也不应该被写成同一个环境里的无条件能力。canonical run 和 Rendering/Nyx run 使用了不同版本组合，报告引用时要把这条版本边界写清楚。

## Genesis 适合的情况

Genesis 比较适合下面几类场景。

**第一，多物理交互探索。**

如果任务不只是刚体机械臂和方块，而是涉及软体、布料、颗粒、流体或刚柔耦合，Genesis 的平台定位更贴近这类问题。

**第二，想研究新一代仿真平台 API。**

Genesis 的 Python 场景接口、`Scene / Entity` 组织方式、并行环境入口，都适合用来观察新平台如何设计机器人仿真 API。

**第三，想较早理解批量环境。**

`scene.build(n_envs=...)` 能直观展示“一个环境”如何变成“一批环境”。这对后续学习 RL 很有帮助。

**第四，探索性项目。**

如果项目目标是调研、比较、原型验证，而不是马上交付稳定实验或论文基线，Genesis 值得纳入候选。

**第五，想把官方示例变成可追溯素材。**

Genesis 官方示例覆盖面很宽，适合做“从示例到可追溯素材”的复现实验。前提是要保留日志、摘要、预览、视频、adapter 原因和失败记录，而不是只截一张官网图。

## 继续用 MuJoCo 的情况

下面这些情况，MuJoCo 通常更合适：

- 主要学习关节、actuator、contact、friction、solver 等基础概念；
- 任务是机械臂、四足、倒立摆、简单抓取等刚体控制问题；
- 需要轻量、成熟、可复现、容易在 CI 里跑的仿真；
- 希望借助 Menagerie、dm_control、Gymnasium 等成熟生态；
- 当前任务不以 MPM / SPH / FEM、多材料耦合或复杂非刚体交互为核心；小规模布料 / 软体基准也可以先核对 MuJoCo 的 deformable / flex 能力是否够用。

一句话：**如果问题是窄而深的刚体动力学和控制，MuJoCo 仍然是很稳的基准。**

## 用 Isaac Sim / Isaac Lab 的情况

Isaac Sim 和 Isaac Lab 的边界要分开看。

如果任务需要：

- USD 工程资产；
- RTX 级相机、深度、分割、Lidar 等传感器；
- ROS 2 Bridge；
- Replicator 合成数据；
- 更接近机器人系统工程的场景调试；

那更像 Isaac Sim 的领域。

如果任务需要：

- 现成机器人 RL 任务；
- Manager-based observation / action / reward / termination / reset；
- RSL-RL、RL-Games、SKRL、SB3 等训练库对接；
- 大规模并行训练、日志、checkpoint、play / train 工作流；

那更像 Isaac Lab 的领域。

一句话：**Isaac Sim 更偏机器人仿真平台，Isaac Lab 更偏机器人学习任务框架。**

## 用 SAPIEN / ManiSkill 或 Habitat 的情况

SAPIEN / ManiSkill 和 Habitat 也有清晰边界。

| 平台 | 更适合 |
|---|---|
| SAPIEN / ManiSkill | 物体操作、抓取、任务库、benchmark、可复现实验数据 |
| Habitat | 室内导航、具身感知、大规模 3D 场景、语义地图和导航任务 |

如果任务是标准化物体操作 benchmark，ManiSkill 往往比从 Genesis 自行搭任务更省心。如果任务是室内导航和具身感知，Habitat 的场景和任务生态更直接。

## 一个简单选型表

| 任务需求 | 优先考虑 |
|---|---|
| 轻量刚体控制、接触调参、算法原型 | MuJoCo |
| 高保真视觉、ROS 2、USD、合成数据 | Isaac Sim |
| 大规模机器人 RL 任务和训练库对接 | Isaac Lab |
| 操作任务 benchmark、现成数据集式任务 | SAPIEN / ManiSkill |
| 室内导航、具身感知、大规模 3D 场景 | Habitat |
| 多物理、刚柔耦合、批量仿真 API 探索 | Genesis |

如果任务同时满足多个条件，就用“主要风险”来选。例如，机械臂抓软布并需要高保真相机，这既像 Genesis 的多物理问题，也像 Isaac Sim 的视觉问题。此时要先问：项目最容易失败的是软体接触不可信，还是相机传感器不够真实？前者更偏 Genesis，后者更偏 Isaac Sim。

这张表不是排名。它只是提醒：平台选择应该服务于任务，而不是反过来让任务迁就平台。

## 项目选型写到什么程度

项目报告不需要写成长篇平台综述，但至少要交代四件事：

| 项 | 要写清楚 |
|---|---|
| 任务需求 | 主要需要刚体、多物理、传感器、批量环境还是任务框架 |
| 平台取舍 | 为什么当前选这个平台，为什么暂时不选替代平台 |
| 第一阶段验收 | 先跑哪一个最小现象，保存哪些 `runs/` 证据 |
| 风险边界 | 版本、依赖、adapter、GUI、性能或参数敏感点 |

可以先用这个短模板：

```text
本项目选择 _______，因为任务主要需要 _______。
本项目不选择 _______，是因为当前任务暂时不需要 _______。
本项目最需要验证的仿真能力是 _______。
项目将保存 _______ 作为运行证据。
如果后续扩展到 _______，可能会重新考虑 _______。
```

例如，选择 Genesis 的项目可以这样写：

```text
本项目选择 Genesis，因为任务主要需要比较刚体和软体物体交互。
本项目不选择 Isaac Sim，是因为当前任务暂时不需要 RTX 级视觉传感器和 ROS 2 集成。
本项目最需要验证的仿真能力是刚柔耦合是否稳定，以及批量环境是否能支持采样。
项目将保存 summary、log、preview、video 和 solver/material 参数作为运行证据。
如果后续扩展到高保真相机数据合成，可能会重新考虑 Isaac Sim。
```

更完整的填写示例、审查清单和证据要求放在 [项目选型模板](06-when-to-use-what/04-project-selection-template.md)。总页只提醒一件事：选型理由必须能落到具体任务和具体证据，不要只写“因为它新”或“因为它快”。

## 读完应能回答

1. 如果任务只需要刚体机械臂和方块，为什么 Genesis 的多物理优势可能不是核心理由？
2. 如果项目需要 ROS 2、USD 和合成数据，为什么 Nyx 渲染不能直接替代 Isaac Sim？
3. 一份选型说明至少应该引用哪类 `runs/` 证据？

## 小结

- Genesis 适合多物理、刚柔耦合、批量仿真 API 和新平台探索。
- MuJoCo 仍然适合刚体动力学、控制、接触和轻量可复现原型。
- Isaac Sim 适合高保真传感器和机器人系统工程；Isaac Lab 适合完整机器人学习任务。
- ManiSkill 更适合物体操作 benchmark，Habitat 更适合导航和具身感知。
- 平台选择要从任务需求倒推，而不是从平台功能列表出发。

## 参考资料

- Genesis World Documentation. https://genesis-world.readthedocs.io/en/latest/
- MuJoCo Documentation. https://mujoco.readthedocs.io/
- Isaac Sim Documentation. https://docs.isaacsim.omniverse.nvidia.com/
- Isaac Lab Documentation. https://isaac-sim.github.io/IsaacLab/
- ManiSkill Documentation. https://maniskill.readthedocs.io/
- Habitat Documentation. https://aihabitat.org/docs/

## 导航

- 上一页：[非刚体实验为什么难验收](05-multiphysics/04-non-rigid-check.md)
- 返回目录：[Genesis](../02-genesis.md)
- 下一页：[什么时候选 Genesis](06-when-to-use-what/01-when-genesis.md)
