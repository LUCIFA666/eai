# 什么时候用 Isaac Sim / Isaac Lab

本页讲什么时候应该转向 Isaac Sim 或 Isaac Lab：USD 资产、RTX 渲染、传感器生态、ROS 2、合成数据和成熟 RL 任务组织。

## 本节目标

本节围绕下面几个问题展开：

1. Isaac Sim 相比 Genesis 的工程生态优势在哪里？
2. Isaac Lab 相比 Genesis 的任务与训练组织优势在哪里？
3. 什么需求更接近 USD / RTX / ROS 2 / 合成数据？
4. 什么需求更接近大规模机器人 RL 任务框架？

## 什么时候用 Isaac Sim

如果任务核心是工程级机器人仿真和高保真传感器，Isaac Sim 更自然：

| 需求 | Isaac Sim 的优势 |
|---|---|
| USD 资产和大型场景 | Omniverse / USD 工作流成熟 |
| RTX 相机和传感器 | 视觉、深度、分割、LiDAR 生态完整 |
| ROS 2 集成 | 更贴近机器人系统工程 |
| 合成数据 | Replicator 等工具链更直接 |

Genesis 有渲染和 Nyx，但它不等于 Isaac Sim 的工程生态。

## 不要把 Nyx 等同于 Isaac Sim

Rendering showcase 已经说明，Genesis 可以通过 Nyx 展示 PBR 材质、灯光、Gaussian splat、object picking 和多相机多环境。但这类能力更像“渲染插件探索”，不等同于 Isaac Sim 的 USD 资产工作流、Replicator、ROS 2 Bridge 和完整传感器工程生态。

如果项目目标是训练策略理解多物理交互，Genesis 很自然；如果目标是构建一个接近真实机器人系统的数字孪生，Isaac Sim 往往更自然。判断差别时可以看交付物：

| 交付物 | 更接近 |
|---|---|
| 多物理接触视频、solver 参数、耦合稳定性报告 | Genesis |
| USD 场景、ROS 2 topic、RTX 相机、合成数据集 | Isaac Sim |
| 大规模 RL 任务配置、训练曲线、checkpoint、play 录像 | Isaac Lab |

## 什么时候用 Isaac Lab

如果任务核心是机器人学习任务组织，Isaac Lab 更适合：

| 需求 | Isaac Lab 的优势 |
|---|---|
| observation / action / reward / reset 管理 | Manager-based 任务结构成熟 |
| 大规模 RL 训练 | 训练、play、checkpoint、日志工作流完整 |
| 多训练库对接 | RSL-RL、RL-Games、SKRL、SB3 等 |
| 标准机器人任务 | 任务模板和配置体系更成熟 |

Genesis 可以帮助理解 `n_envs`，但它本身不是完整 Isaac Lab 式任务框架。

## 用 Nyx 渲染划边界

Rendering showcase 很适合拿来说明 Genesis 和 Isaac Sim 的边界。Nyx 能渲染 PBR 材质、灯光、Gaussian splat、object picking、多相机多环境，也能生成统一的 `1060x580` 预览；其中 `render_03_nyx_attached_camera` 还保留了完整 MP4 和 no-adapter 失败日志。但它仍然需要单独插件、单独版本组合和 adapter 记录。Isaac Sim 的重点则是把渲染、资产、传感器、合成数据和机器人系统工程放进更完整的 Omniverse / USD 工作流里。

可以按交付物判断更需要哪边：

| 交付物 | 更可能选择 |
|---|---|
| 多物理现象、solver 说明、adapter 日志 | Genesis |
| 高保真 RGB-D / segmentation / LiDAR 数据集 | Isaac Sim |
| ROS 2 topic、真实机器人接口、USD 场景资产 | Isaac Sim |
| 标准化 RL task、训练配置、checkpoint、play 录像 | Isaac Lab |
| 小规模脚本验证 `n_envs`、sensor read、camera 落盘 | Genesis |

本书把 Nyx 写进 Genesis，不是为了说它已经覆盖 Isaac Sim，而是为了说明：渲染能力可以通过插件扩展，但工程生态、资产工作流和任务框架仍然是另一层问题。

## 从 Genesis 迁移到 Isaac 的时机

一个常见路线是：先用 Genesis 做小规模多物理原型，确认任务现象存在；再决定是否迁移到 Isaac Sim / Isaac Lab 做工程化任务。迁移通常发生在这几种时刻：

1. 需要真实机器人资产、传感器和 ROS 2 系统联调；
2. 需要高保真 RGB-D / segmentation / LiDAR 数据进入感知模型；
3. 需要把任务变成长期训练 benchmark，有标准化 reward、reset、logging 和 checkpoint；
4. 需要团队多人维护场景资产和任务配置，而不是单人脚本探索。

因此，Genesis 和 Isaac 不必互斥。Genesis 可以负责快速暴露物理问题，Isaac 负责后续工程化和训练体系。

## 读完应能回答

1. 为什么 `render_03_nyx_attached_camera` 的 adapter 日志反而能帮助做平台选型？
2. 如果项目目标是 ROS 2 联调和合成数据，为什么不应该只因为 Genesis 能渲染就选 Genesis？
3. 如果项目目标是布料和机器人接触的最小原型，为什么可以先不进 Isaac Sim？

## 小结

- Nyx 展示 Genesis 的渲染扩展能力，但不等同于 Isaac Sim 的 USD / RTX / ROS 2 工程生态。
- Isaac Sim 更适合高保真传感器、合成数据和机器人系统工程。
- Isaac Lab 更适合完整机器人学习任务、训练配置、checkpoint 和 play 工作流。
- Genesis 与 Isaac 不必互斥，可以先用 Genesis 暴露物理问题，再决定是否工程化迁移。

## 导航

- 上一页：[什么时候继续用 MuJoCo](02-when-mujoco.md)
- 返回目录：[Genesis 适用边界](../06-when-to-use-what.md)
- 下一页：[项目选型模板](04-project-selection-template.md)
