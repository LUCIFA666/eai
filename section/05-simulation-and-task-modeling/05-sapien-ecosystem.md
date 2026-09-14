# SAPIEN 生态

在具身智能里，“仿真器”和“任务环境”不是同一个概念。仿真器回答的是世界如何运行：刚体怎样碰撞，关节怎样受力，相机怎样成像，渲染怎样输出。任务环境回答的是学习算法如何与这个世界交互：策略看到什么，动作怎样解释，奖励从哪里来，什么时候算成功。

SAPIEN 生态正好可以用来区分这两层。SAPIEN 提供物理、机器人、关节物体、相机和渲染等底层能力；ManiSkill 则把这些能力组织成一组可以直接训练、评测和复现的机器人操作任务。

因此，读这一节时可以先抓住一个判断：**SAPIEN 更接近仿真基础设施，ManiSkill 更接近任务环境。** 学 ManiSkill 的重点不是从零搭一个世界，而是理解一个标准操作任务如何暴露观测、动作、奖励、成功判定和并行接口。

## 从 PickCube 进入任务层

后面的 ManiSkill 页面会用 ManiSkill 自带的标准任务 `PickCube-v1` 做贯穿例子。它是一个可以被 `gym.make()` 创建的环境 ID：任务内容是抓起桌面方块并放到目标附近。

这个例子小到适合第一次动手，大到足够承载关键概念。它让我们在一个任务里同时看到机械臂、夹爪、物体、目标、观测、动作、奖励和成功条件。读懂这个任务，再去看开抽屉、插销、堆叠、多物体搬运等任务，就会自然很多。

![PickCube-v1 reset 后的任务画面](assets/maniskill_pickcube_reset.png)

## 本节要回答的问题

本节围绕下面几个问题展开：

1. SAPIEN 和 ManiSkill 各自负责什么？
2. 一个 ManiSkill 任务为什么可以用 Gymnasium 风格的 `reset()` / `step()` 交互？
3. `obs_mode`、`control_mode`、`reward_mode` 和 `info["success"]` 分别改变什么？
4. `state`、`rgbd`、`sensor_data` 和 `env.render()` 有什么区别？
5. 一个 ManiSkill 任务内部通常由哪些部分组成？
6. ManiSkill 和 Genesis、Isaac Sim、Isaac Lab 的边界在哪里？

## 阅读路径

本节以“ManiSkill 任务接口与 PickCube 实战”为主线。这条路线会把安装自检、最小闭环、任务五件套、观测渲染、batch、wrapper、下游边界、任务内部读法和练习完整走一遍。

| 页面 | 适合什么时候读 |
|---|---|
| [ManiSkill 任务接口与 PickCube 实战](05-sapien-ecosystem/01-maniskill-task-interfaces.md) | 想系统读懂一个标准操作任务如何接到训练、数据、评测和自定义任务 |

## 和其他平台的关系

ManiSkill 适合用来学习标准化操作任务接口：任务 ID、观测模式、控制模式、奖励模式、成功判定、批量环境和 Gymnasium 兼容层。它很适合做 benchmark、RL / IL 入门和任务接口对照。

它不替代 Genesis 的自定义实验后端，也不替代 Isaac Sim 的 USD 资产、高保真传感器和系统工程生态。读懂 ManiSkill 的价值，是让后续自建任务、迁移后端、写评测脚本时有一套清楚的任务接口参照。

## 导航

- 上一节：[Isaac Lab](04-isaac-lab.md)
- 返回本章：[仿真与任务建模](README.md)
- 下一节：[其他仿真生态](06-other-simulation-ecosystems.md)
