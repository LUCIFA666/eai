# Isaac Sim

在具身智能实验里，MuJoCo 很适合快速验证控制和策略；当任务进一步依赖逼真的相机、深度、语义分割、激光雷达、ROS 2 接口或大规模合成数据时，就需要 Isaac Sim 这类更完整的机器人仿真平台。它基于 NVIDIA Omniverse，用 USD 场景、PhysX 物理和 RTX 渲染，把机器人、物体、传感器和数据接口组织成一个可被 Python 驱动的仿真环境。

阅读本单元需要基础 Python 知识，最好已经读过 [MuJoCo](02-mujoco.md) 或至少理解"模型描述 → 初始化 → step 循环 → 读取状态"这类仿真主线。不要求事先懂 USD、PhysX、Omniverse 或 ROS 2；本单元会从第一次跑通开始，把这些名词逐步放回同一条工作流里。

本单元聚焦 Isaac Sim 本身：它是什么、一个 Isaac Sim 脚本怎么运行、USD 场景怎么组织、机器人资产为什么导入后还要检查物理、怎么发出控制、怎么读取观测，以及如何把一次仿真整理成可复现的数据。大规模并行训练会交给下一页 [Isaac Lab](04-isaac-lab.md)，这里先把单个仿真世界搭稳、看清、跑通。

## 本节目标

本节围绕下面几个问题展开：

1. Isaac Sim 在本章仿真平台地图里的定位是什么？
2. 它和 MuJoCo、Isaac Lab、SAPIEN / ManiSkill 的职责边界在哪里？
3. 学 Isaac Sim 时，为什么要按脚本、USD、物理、控制、观测、任务数据这条线推进？
4. 初学者第一轮应该先跑什么，暂时不要急着做什么？

## 这一单元想解决什么

Isaac Sim 学习路上最容易卡住新手的，不是窗口和扩展多，而是三道和轻量物理引擎不一样的门槛：

1. **SimulationApp / World / reset / step 的运行顺序**：Isaac Sim 不是 `import` 一个库就能用。你要先启动 Kit 运行时，再导入 Isaac Sim API，创建 World，`reset` 初始化物理，最后在循环里 `step`。顺序写反，常见结果不是小错误，而是模块找不到、状态读不到或仿真不推进。
2. **USD Stage / Prim / 引用这套场景组织方式**：MuJoCo 常把模型写在一个 MJCF 文件里；Isaac Sim 的世界更像一棵 USD 场景树。地面、灯光、机器人、传感器都是 Prim，靠路径、引用和分层组合起来。理解这棵树，后面才能定位资产、相机和关节体。
3. **显示出来不等于能可信仿真**：URDF、Mesh 或 CAD 导入后，往往只是把形状放进了场景。要让机器人稳定运动，还要检查碰撞体、质量、摩擦、关节 Drive 和 articulation root。否则看起来有机器人，实际可能穿地板、抖动、失控或读不到关节。

本单元按"先建运行主线，再逐层下钻，最后串成任务与数据"的顺序展开。读完整个单元，应该能从跑通一个最小脚本开始，一步一步走到搭场景、加载机器人、发出控制、读取观测，再把仿真过程变成可复现的数据和合成样本。

## 本单元边界

本单元聚焦 Isaac Sim 本身的使用。以下内容不在本单元展开：

- **大规模并行 RL 训练**：环境批量化、Manager 系统、训练库接入等内容，见 [Isaac Lab](04-isaac-lab.md)。
- **深入的机器人学算法**：坐标系、运动学、动力学、控制器理论，见 [03 机器人基础](../02-robotics-foundations/README.md)。
- **Sim2Real 真机迁移**：从仿真到真机部署的完整流程，留给后续真机章节。
- **不同仿真器选型**：MuJoCo、Isaac Sim、SAPIEN、Genesis 等平台的比较，见 [平台选择](01-platform-selection.md)。

这里的目标更具体：把一个 Isaac Sim 世界搭可信，让机器人能动、能被观测，并能产出可复现的数据。

## 运行环境

本单元的示例和截图以 **Isaac Sim 5.1.0 + Python 3.11** 为课程锁定环境，写法统一使用 `isaacsim.*` 命名空间。阅读时可以先按下面这套环境建立直觉，遇到版本差异再回到安装页查对照：

| 项目 | 版本 / 配置 |
|---|---|
| Python | 使用安装了 Isaac Sim 的那个 Python：pip 安装时是当前 conda / venv 的 `python`，预编译包 / 工作站版则是安装目录里的 `./python.sh` |
| Isaac Sim | 5.1.0 API，示例使用 `isaacsim.*` 命名空间 |
| 运行方式 | standalone Python 脚本为主，GUI 用于观察和调试 |
| 服务器运行 | 支持 headless；渲染、录制和传感器输出需要按页内说明预热 |
| 后续衔接 | Isaac Lab 负责大规模并行任务与 RL 训练 |

## 学习路径

| 页面 | 学习者此刻在问 | 重点 |
|---|---|---|
| [认识 Isaac Sim](03-isaac-sim/01-getting-started.md) | 这是什么？怎么先跑起来？跑完怎么理解？ | 平台定位、headless 最小闭环、三个理解视角、安装版本 |
| [场景构建与坐标约定](03-isaac-sim/02-building-a-world.md) | 场景到底怎么组织？ | USD / Stage / Prim 组合思维、动手搭场景、坐标与单位 |
| [机器人资产与物理配置](03-isaac-sim/03-robot-and-physics.md) | 机器人资产如何导入，并配置到可仿真状态？ | URDF→USD、Articulation、碰撞 / 材质 / Drive 检查、其它导入器 |
| [控制](03-isaac-sim/04-control.md) | 如何让机器人按目标运动？ | 关节控制、Drive、`ArticulationAction`、IK / RMPflow |
| [观测与传感器](03-isaac-sim/05-observation.md) | 如何读取相机、Lidar、IMU、接触和状态，并与动作对齐？ | 相机、RTX Lidar、IMU / 接触、obs→action 闭环 |
| [任务、数据采集与合成数据](03-isaac-sim/06-task-and-data.md) | 怎么把一次运行变成任务数据，或批量产带标注感知数据？ | episode、采集 / 回放 / 质检、headless、Replicator |
| [仿真接口](03-isaac-sim/07-ecosystem.md) | 什么时候需要把仿真数据接到外部节点？ | OmniGraph、ROS 2 topic、clock / joint_states / TF / camera |

## 怎么读这一单元

**方案 A：完整通读（推荐初次学习）**

按目录顺序从第一章读到第六章：认识 Isaac Sim → 场景构建 → 机器人资产与物理配置 → 控制 → 观测与传感器 → 任务、数据采集与合成数据。这样读完后，你会得到一条完整闭环：搭出世界、放进机器人、让它动、读回观测、记录成任务数据，必要时再批量生成带标注感知数据。第七章作为可选仿真接口，在需要 OmniGraph 或 ROS 2 Bridge 时再读。

**方案 B：资产调试速通**

如果你手里已经有 URDF、USD 或 Mesh，主要问题是"导进 Isaac Sim 后为什么不能动 / 会穿模 / 关节读不到"，可以走这条路径：第一章快速扫一遍 → 第二章看 Stage / Prim → 第三章重点读机器人资产、articulation 和物理检查 → 第四章读关节控制。

**方案 C：数据采集速通**

如果目标是采集图像、深度、分割或任务轨迹，可以走：第一章 → 第二章 → 第五章观测与传感器 → 第六章任务、数据采集与合成数据。遇到机器人运动问题时，再回第三章补物理和 articulation，或回第四章补关节控制；只有需要外部 ROS 2 节点或 RViz 时，再读第七章。

## Isaac Sim 在课程里的职责

Isaac Sim 负责把场景、物理和传感器统一到同一个仿真环境中：USD 场景组织与资产加载、RGB / 深度 / 分割 / 位姿等传感器输出、PhysX 物理与接触反馈、可视化调试与合成数据接口。如果目标是大规模训练 RL，本章会继续进入 [Isaac Lab](04-isaac-lab.md)；如果目标是检查资产、相机和物理，Isaac Sim 本身就是独立的学习对象。

## 导航

- 上一页：[MuJoCo](02-mujoco.md)
- 返回目录：[06 仿真建模](README.md)
- 下一页：[Isaac Lab](04-isaac-lab.md)

## 延伸阅读

- NVIDIA Isaac Sim Documentation. https://docs.isaacsim.omniverse.nvidia.com/
- NVIDIA Isaac Sim, Python Scripting and Tutorials. https://docs.isaacsim.omniverse.nvidia.com/latest/python_scripting/index.html
- NVIDIA Isaac Sim, Workflows. https://docs.isaacsim.omniverse.nvidia.com/latest/introduction/workflows.html
