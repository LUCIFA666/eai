# Drake 三大模块

目标：理解 Drake 中最重要的三类能力：Multibody Dynamics、Systems Framework 和 Optimization，并知道它们在一个机器人项目中如何配合。

Drake 的 API 很多，初学者如果从函数名开始看，很容易迷路。更稳的方式是先抓三大模块：

1. **Multibody Dynamics**：机器人和物理世界怎么表示。
2. **Systems Framework**：机器人、控制器、传感器和可视化怎么连接。
3. **Optimization**：规划、逆运动学、轨迹优化和控制问题怎么求解。

这三块合在一起，就是 Drake 的主线。

## Multibody Dynamics

Multibody Dynamics 负责表示多体系统。机械臂、移动机器人、物体、关节、碰撞几何、惯量、接触力，都属于这一层。

Drake 里最核心的对象是 `MultibodyPlant`。可以把它理解成机器人和物理世界的动力学模型。它知道模型有哪些 body、joint、frame、actuator、state 和 input。

常见对象如下：

| 对象 | 作用 |
|---|---|
| `MultibodyPlant` | 多体系统模型，表示机器人、物体、关节和动力学 |
| `SceneGraph` | 管理几何、碰撞、距离查询和可视化几何 |
| `Parser` | 从 URDF、SDF 等模型文件加载机器人或物体 |
| `Frame` | 坐标系，比如 world frame、body frame、end-effector frame |
| `Joint` | 连接两个 body 的关节 |
| `Context` | plant 在某一时刻的状态、输入和参数 |

使用 Drake 做机器人建模时，常见流程是：

```text
DiagramBuilder
  -> AddMultibodyPlantSceneGraph
  -> Parser 加载 URDF / SDF
  -> plant.Finalize()
  -> 创建 Context
  -> 读取 / 设置 q、v、pose、geometry query
```

`Finalize()` 很重要。它表示模型拓扑已经固定，之后不能随便再加 body 或 joint。新手常见错误是 plant 还没 finalize 就想仿真，或者 finalize 后又想继续添加模型。

## Systems Framework

Systems Framework 负责把多个模块连接成一个整体系统。

Drake 把许多东西都看作 `System`：多体 plant 是系统，控制器是系统，轨迹源是系统，传感器和 logger 也可以是系统。每个系统有输入端口、输出端口、状态和参数。

一个简单机械臂控制图可以写成：

```text
TrajectorySource
  -> Controller
  -> MultibodyPlant
  -> StateOutput
  -> Logger / Visualizer
```

这背后的 Drake 对象通常是：

| 对象 | 作用 |
|---|---|
| `System` | 动态系统基类 |
| `DiagramBuilder` | 创建并连接多个系统 |
| `Diagram` | 连接完成后的整体系统 |
| `InputPort` / `OutputPort` | 系统之间的连接接口 |
| `Simulator` | 推进系统时间演化 |
| `Logger` / `MeshcatVisualizer` | 记录和可视化系统输出 |

Systems Framework 的好处是边界清楚。你能看到控制器输入来自哪里，输出接到哪里，plant 状态又被谁读取。对于复杂机器人系统，这比在一个大循环里混写所有逻辑更容易调试。

## Optimization

Optimization 是 Drake 的另一条主线。Drake 提供 `MathematicalProgram` 来组织优化问题。

一个 `MathematicalProgram` 通常包含：

| 部分 | 例子 |
|---|---|
| 决策变量 | 关节角 `q`、速度 `v`、控制输入 `u`、时间步 `h` |
| 约束 | 起点终点、关节限位、速度限制、碰撞距离、动力学方程 |
| 代价 | 平滑性、控制能量、路径长度、时间、离参考姿态的距离 |
| 求解器 | SNOPT、IPOPT、OSQP、Clarabel、Gurobi、MOSEK 等，具体取决于问题类型和安装 |

Drake 会根据问题结构和可用求解器调用合适的 solver，也允许你显式指定求解器。官方文档里也提醒：不同求解器覆盖范围不同，有些商业求解器需要许可证，预编译 Drake 中包含的部分求解器能力也要按当前版本核对。

在机器人里，Optimization 常见用途包括：

| 用途 | Drake 中常见形式 |
|---|---|
| 逆运动学 | `InverseKinematics`、position / orientation constraints |
| 轨迹优化 | `DirectCollocation`、`MathematicalProgram`、多段路径约束 |
| 避障 | Minimum distance / collision constraints |
| 控制 | LQR、MPC、trajectory tracking 相关问题 |
| 几何推理 | 凸集、距离、可行区域等优化问题 |

## 三大模块如何配合

三大模块不是并列摆着看的，它们会在一个项目里互相调用。

例如机械臂轨迹规划：

```text
Multibody Dynamics
  提供机械臂模型、关节限位、末端 frame、几何和碰撞查询

Systems Framework
  把 plant、控制器、轨迹源、logger 和 visualizer 接成 Diagram

Optimization
  把 q(t)、速度限制、末端目标、避障和平滑性写成优化问题
```

所以学习 Drake 时，不要只学其中一块。只学 MultibodyPlant，会停留在建模和仿真；只学 MathematicalProgram，会缺少机器人模型；只学 Systems Framework，又不知道怎么做规划和约束。三块连起来才是 Drake 的完整价值。

## 本页小结

Drake 的三大模块可以理解为：Multibody Dynamics 表示机器人和物理世界，Systems Framework 连接系统模块，Optimization 负责把规划控制写成变量、约束和代价。后面写任何 Drake 项目，基本都绕不开这三块。

## 导航

- 上一页：[核心思想](03-core-ideas.md)
- 返回：[Drake](../05-drake.md)
- 下一页：[Drake 工作流程](05-workflow.md)

## 进一步阅读可以看：

- [Multibody Kinematics and Dynamics](https://drake.mit.edu/doxygen_cxx/group__multibody.html)
- [Modeling Dynamical Systems](https://drake.mit.edu/doxygen_cxx/group__systems.html)
- [Formulating and Solving Optimization Problems](https://drake.mit.edu/doxygen_cxx/group__solvers.html)