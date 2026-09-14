# Genesis

前面几节已经介绍了几种不同风格的仿真工具：MuJoCo 更像一个轻量、成熟、可以直接 `import` 的物理引擎；Isaac Sim 更像一个带 USD 场景、RTX 渲染和传感器生态的机器人仿真平台；Isaac Lab 则建在 Isaac Sim 之上，负责任务与训练。

Genesis 要放在这张地图里理解。它不是“新版 MuJoCo”，也不是“轻量版 Isaac Sim”。更准确地说，Genesis World 是一个面向 Physical AI / 具身智能研究的 **Python-first 多物理仿真平台**：把机器人、刚体、软体、布料、颗粒、流体、渲染、传感器和并行环境放进一套统一的 Python 接口里。

阅读本单元不要求预先掌握 Genesis，也不要求理解软体或流体仿真，但最好已经读过 [MuJoCo](../02-mujoco.md)，或至少理解“模型描述 → 初始化 → step 循环 → 读取状态”这条仿真主线。安装、运行和写代码都放到子页，本页只建立定位和学习路线。

## 本节目标

本节围绕下面几个问题展开：

1. Genesis 在本章仿真平台地图里的定位是什么？为什么不能只把它理解成另一个 MuJoCo？
2. 它和 MuJoCo、Isaac Sim、Isaac Lab、SAPIEN / ManiSkill 的职责边界在哪里？
3. 学 Genesis 时，为什么要先抓 `Scene / Entity / build / step` 主线，再逐层推进到多物理和并行？
4. 初学者第一轮应该先跑什么，暂时不要急着做什么？

## 这一单元想解决什么

Genesis 入门最容易卡住新手的，不是 API 多，而是它把多种能力放进同一套接口，初学时容易一次碰太多层：

1. **多物理不是“更多刚体”**：除了刚体，Genesis 还覆盖软体、布料、颗粒、流体以及它们之间的耦合。不同物理对象的状态表示、求解器和验收方式都不一样，必须分清当前在学哪一层。
2. **一套接口跨越接口、物理、渲染传感和后端**：`Scene / Entity / build / step` 是入口，多物理求解、渲染传感和 CPU / CUDA 后端是逐层展开的能力，不要第一轮就全部打开。
3. **能跑通不等于能被无头相机完整记录**：viewer 叠加层、传感器读数、Nyx 渲染插件各有边界，写实验时要分清画面来自物理、相机、叠加层还是后处理。

本单元按“先建运行主线，再逐层下钻，最后讨论适用边界”的顺序展开：先用最小刚体场景跑通 `init → Scene → add_entity → build → step`，再进入场景与机器人、观察与传感、并行环境、多物理，最后做任务级选型。

## 本单元边界

本单元聚焦 Genesis 本身的入门使用。以下内容不在本页展开：

- **安装、环境变量与配套脚本**：放在入门组的 [认识 Genesis](02-genesis/01-getting-started.md)。
- **每个 showcase 素材的运行细节**：preview、summary、log、adapter 说明分散在对应主题子页，不在父页罗列。
- **大规模 RL 训练**：Genesis 提供可批量推进的环境基础，强化学习算法本身属于强化学习专题，本单元不展开。
- **不同仿真器选型对比**：见 [平台选择](../01-platform-selection.md)。

## 运行环境

本单元代码入口在 `labs/06_genesis/`。Genesis 版本变化较快，本书只固定 `Scene / Entity / build / step / control / render / n_envs` 这条入门主线；安装命令、后端名称和相机返回值如遇差异，回官方文档核对。

| 项目 | 配置 |
|---|---|
| 语言入口 | Python-first，`import genesis as gs` |
| 入门主线 | `init → Scene → add_entity → build → step` |
| 后端 | CPU / CUDA，第一轮建议 CPU、关闭 viewer |
| 配套脚本 | `labs/06_genesis/`，保存环境信息、日志、JSON 摘要和渲染产物 |

## 学习路径

| 页面 | 学习者此刻在问 | 重点 |
|---|---|---|
| [认识 Genesis](02-genesis/01-getting-started.md) | 这是什么？怎么先跑起来？ | 定位、第一次仿真、三个理解视角、安装与环境检查 |
| [场景、实体与机器人](02-genesis/02-scene-entity-robot.md) | 世界怎么搭，机器人怎么控制？ | `Scene / Entity`、机器人资产、关节自由度、reset 与 control |
| [观察、渲染与传感器](02-genesis/03-observation-rendering-sensors.md) | 画面和观测怎么读、怎么存？ | viewer、camera、Genesis 1.x sensor API、渲染验收 |
| [并行环境](02-genesis/04-parallel-envs.md) | 一批环境怎么一起跑？ | `n_envs`、批量动作、`envs_idx`、并行实验记录 |
| [多物理入门](02-genesis/05-multiphysics.md) | 软体、布料、颗粒、流体怎么处理？ | 多刚体、solver、material、SPH / MPM / PBD、非刚体验收 |
| [Genesis 适用边界](02-genesis/06-when-to-use-what.md) | 什么时候该用 Genesis？ | 和 MuJoCo、Isaac Sim、Isaac Lab、ManiSkill 做任务级选型 |

这条路线沿着“是什么 → 怎么跑 → 怎么理解 → 怎么用 → 什么时候用”推进：先把最小世界搭稳，再逐层展开多物理和并行，不必一开始就把所有官方示例全量铺开。

## Genesis 在课程里的职责

Genesis 负责搭出一个**可计算、可观察、可批量复制的物理世界**：用 Python 组织实体，统一接入多物理、渲染、传感器和并行环境。如果研究问题是“机器人和复杂物理对象怎么交互”，Genesis 的定位很自然；如果只是验证一个关节 PD 控制器，MuJoCo 更直接；如果要高保真相机数据和 ROS 2 工程集成，Isaac Sim 更合适。

## 导航

- 上一页：[Habitat 仿真生态](01-habitat-simulation.md)
- 返回目录：[其他仿真生态](../06-other-simulation-ecosystems.md)
- 下一页：[认识 Genesis](02-genesis/01-getting-started.md)

## 延伸阅读

- Genesis World GitHub README. https://github.com/Genesis-Embodied-AI/genesis-world
- Genesis World Documentation. https://genesis-world.readthedocs.io/en/latest/
- Genesis World Documentation, Hello, Genesis World. https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/hello_genesis.html
- Genesis World Documentation, Parallel Simulation. https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/parallel_simulation.html
