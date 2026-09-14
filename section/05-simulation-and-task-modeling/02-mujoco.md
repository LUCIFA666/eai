# 6.2 MuJoCo

在具身智能的实验里，我们通常先在仿真中把想法跑通，再考虑真机。MuJoCo 是这类仿真器中很常用的一个：它轻量、启动快，一台没有独立显卡的笔记本也能驱动机械臂运动，因此很适合入门和快速迭代。

本节面向已经会写基础 Python、但还没接触过物理仿真的读者。我们会从整体上认识 MuJoCo：它是什么、一个 MuJoCo 程序是怎么运行的、模型文件长什么样、怎么让机器人按指令运动、怎么把仿真过程变成可记录的观测，以及它周边那些能帮我们少造轮子的现成资产和任务库。

本节聚焦 MuJoCo 本身。与之相关、但更为通用的主题会指向其他章节，不在此重复：不同仿真平台的比较与取舍见 [平台选择](01-platform-selection.md)，坐标系、运动链和控制接口等机器人基础见 [03 机器人基础](../02-robotics-foundations/README.md)，观测数据的组织与评测见 [07 数据](../06-data-teleoperation-and-imitation-learning/README.md) 与 [09 评测](../08-evaluation-reproducibility-and-engineering/README.md)。具体安装环境以本节和各平台页面的运行环境说明为准。

## 这一单元想讲清楚什么

刚上手 MuJoCo 时，有三个地方比较容易卡住，本单元会围绕它们展开：

1. **MJCF / mjModel / mjData 三层抽象**：模型描述文件（XML）、编译后的静态结构、每步变化的动态状态。把这三者分清楚、理清它们怎么配合，是读懂后面内容的基础。
2. **从模型到能动的机器人**：在 MuJoCo 里不能直接设定关节角度让机器人"摆"到某个姿势，而要通过 actuator（驱动）给力或给目标，让物理去推动关节。actuator、tendon、contact 这套机制，第一次接触时常会觉得和习惯的写法不太一样。
3. **从仿真到训练**：观测怎么取、渲染怎么搭，dm_control / Gymnasium / MJX 这些上层接口各自解决什么问题，以及"一个 MJCF 模型怎么变成可训练的 gym env"。把这条拼装链的每一层看清楚，从"跑通 demo"走到"改出自己的实验"会顺很多。

整个单元顺着一条线走：先对 MuJoCo 有个整体印象，再一块块深入（建模、控制、观测、生态），最后用一个抓取任务把它们串起来。顺着读下来，能从加载一个模型文件，一直做到训练出一个策略。

## 本单元边界

本单元聚焦 MuJoCo 本身的使用。以下内容不在本单元展开：

- **深入的 RL 算法**：PPO、SAC 等算法的数学原理与调参技巧，见 [10 强化学习](../09-reinforcement-learning-for-robotics/README.md)。
- **Sim2Real 真机迁移**：从仿真策略到真机部署的完整流程，见 [12 真机实战](../11-real-robot-practice/README.md)。
- **不同仿真器对比**：MuJoCo、Isaac Sim、SAPIEN 等的定位差异与选型建议，见 [平台选择](01-platform-selection.md)。

配套脚本统一放在 `labs/04-simulation/`，运行输出在 `runs/04-simulation/`。

## 运行环境

下面是一套可行的参考环境：

| 项目 | 版本 / 配置 |
|---|---|
| Python | 3.10 |
| MuJoCo | 3.8.1 |
| dm_control | 1.0.41 |
| gymnasium | 1.2.3 |
| 渲染后端 | EGL（通过 `MUJOCO_GL=egl`，无需显示器） |
| 机器人模型 | `mujoco_menagerie` 的 Franka Emika Panda |

## 学习路径

| 章节 | 这一章回答的问题 | 重点 |
|---|---|---|
| [认识 MuJoCo](02-mujoco/01-overview.md) | 这是什么？怎么先跑起来？ | 定义、运转主线、第一次跑通 |
| [建模](02-mujoco/02-modeling.md) | 模型文件长什么样？怎么读、怎么改？ | MJCF、body 树、坐标系、mjModel/mjData 字段 |
| [控制与物理](02-mujoco/03-control-and-physics.md) | 怎么让机器人按指令动？接触怎么算？ | 仿真流水线、actuator、tendon、接触与摩擦 |
| [观测与渲染](02-mujoco/04-observation-and-rendering.md) | 怎么从仿真里拿数据、拿图？ | 状态读取、sensor、相机、Renderer、headless |
| [接口与生态](02-mujoco/05-interfaces-and-ecosystem.md) | menagerie / dm_control / Gymnasium 之间什么关系？ | Python API、现成资产、上层任务接口、选型 |
| [抓取实战](02-mujoco/06-grasping-walkthrough.md) | 前面学的怎么串成真实任务？ | 场景、末端控制、夹爪、reach → grasp → lift |
| [MJX 与 GPU 并行](02-mujoco/07-mjx-and-gpu.md) | 怎么用 GPU 加速、训练用得上吗？ | MJX、最小迁移、速度对比、Warp 简介 |
| [训练教程](02-mujoco/08-training-recipes.md) | 在 MuJoCo 里训一个策略是什么样？ | dm_control + SB3、MJX + Brax、IL、Sim2Real 指路 |
| [附录：速查表](02-mujoco/99-cheat-sheet.md) | 用的时候 API、字段忘了怎么办？ | 常用 API / 字段 / 代码片段速查 |

## 怎么读这一单元

第 1、2 章是基础，最好按顺序读完；第 3、4、5 章相对独立，读完第 2 章后挑感兴趣的看就行；第 6 章是抓取实战，第 7 章讲 GPU 加速，第 8 章讲训练，按需要取用。

如果时间有限，也可以挑一条路线走：

- **完整通读**（初次学习推荐）：按目录顺序从第 1 章读到第 8 章，读一遍大致就能从加载模型走到训练策略。
- **RL 速通**（已有建模基础）：第 1 章快速扫一遍 → 第 2 章重点看 mjModel/mjData 与常用字段 → 第 5 章了解上层封装 → 第 8 章直接训练；遇到控制或观测的问题，再回头查第 3、4 章。
- **改模型速通**（已有控制基础）：第 1 章 → 第 2 章（MJCF 结构与 body 树）→ 第 3 章（actuator 与 tendon）→ 第 6 章（抓取里的模型改造部分）。

## 导航

- 上一节：[平台选择](01-platform-selection.md)
- 返回本章：[06 仿真建模](README.md)
- 下一节：[Isaac Sim](03-isaac-sim.md)
