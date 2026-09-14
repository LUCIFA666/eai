# Drake 工作流程

目标：理解一个 Drake 项目通常怎样从模型文件走到系统图、仿真、优化和验证，避免把 Drake 程序看成零散 API 调用。

Drake 的工作流程不是固定模板，但大多数机器人项目都会沿着一条类似路线展开：先建立模型，再构建系统，再检查仿真，再写规划或优化，最后把结果放回系统里验证。

## 总体流程

可以先记这条主线：

```text
准备模型
  -> 构建 MultibodyPlant + SceneGraph
  -> Finalize plant
  -> 构建 Diagram
  -> 创建 Context / Simulator
  -> 做仿真或状态查询
  -> 写 IK / trajectory optimization / controller
  -> 求解并验证结果
```

每一步解决的问题不同。

| 步骤 | 目标 | 常见检查 |
|---|---|---|
| 准备模型 | 加载 URDF / SDF / mesh | 文件路径、关节、惯量、几何、碰撞体 |
| 构建 plant | 表示机器人和世界 | body、joint、actuator、frame 是否正确 |
| Finalize | 固定模型拓扑 | finalize 后不能再添加模型 |
| 构建 Diagram | 连接 plant、controller、logger、visualizer | 端口连接是否正确 |
| 创建 Context | 设置初始状态和参数 | q、v、输入端口、时间 |
| 仿真 / 查询 | 验证模型是否正常 | 状态变化、碰撞、可视化 |
| 优化 / 控制 | 求解 IK、轨迹或控制输入 | 变量、约束、代价、求解器 |
| 验证 | 检查轨迹和约束是否真实可用 | 碰撞、限位、跟踪误差、日志 |

## 第一步：准备模型

Drake 可以通过 `Parser` 加载 URDF、SDF 等模型文件。模型文件通常包含 link、joint、visual geometry、collision geometry、inertial 参数和 actuator 相关信息。

新手要先检查模型本身。很多 Drake 问题不是 Drake 的问题，而是模型文件里惯量、坐标系、碰撞几何或关节方向不对。

建议先问：

```text
机器人有几个关节？
关节名和顺序是什么？
末端执行器 frame 叫什么？
collision geometry 是否合理？
模型单位是不是米、千克、弧度？
```

## 第二步：构建 MultibodyPlant 和 SceneGraph

典型程序会先创建 `DiagramBuilder`，再添加 `MultibodyPlant` 和 `SceneGraph`。`SceneGraph` 负责几何查询和可视化相关信息，`MultibodyPlant` 负责多体动力学。

伪代码结构大致是：

```python
builder = DiagramBuilder()
plant, scene_graph = AddMultibodyPlantSceneGraph(builder, time_step=0.0)
parser = Parser(plant)
parser.AddModels("robot.urdf")
plant.Finalize()
```

这里的 `time_step=0.0` 常表示连续时间 plant；离散时间 plant 则会使用正的 time step。正式写代码时要根据任务决定。

## 第三步：构建系统图

有了 plant，不等于有完整机器人系统。你可能还需要控制器、轨迹源、可视化器和 logger。Drake 用 `DiagramBuilder` 把它们接起来。

```text
TrajectorySource -> Controller -> Plant -> Logger
                                 -> Visualizer
```

系统图的好处是清楚。每个模块有什么输入输出，连接关系是否正确，都可以检查。大型机器人系统里，这比把所有逻辑写进一个 while 循环更稳。

## 第四步：创建 Context 并仿真

`Context` 保存系统在某个时刻的状态、参数和输入值。很多 Drake 函数都需要 context，因为同一个系统模型在不同 context 下状态不同。

比如你想算末端执行器位姿，不能只问 plant；还要告诉它当前关节角 q 是多少。

```text
plant model: 机械臂结构
context: 当前 q、v、输入和参数
query: 末端 pose、Jacobian、距离、能量等
```

仿真时，`Simulator` 会推进系统状态。对于优化和控制项目，仿真不是最终目的，而是验证模型、控制器和轨迹是否合理。

## 第五步：写优化问题

Drake 的很多规划问题会进入 `MathematicalProgram`。

例如逆运动学：

```text
变量: q
约束: 末端位置、姿态、关节限位、碰撞距离
代价: q 离参考姿态不要太远
```

例如轨迹优化：

```text
变量: q_0, q_1, ..., q_N
约束: q_0 = q_start, q_N = q_goal, 速度限制, 避障
代价: 平滑性、路径长度、控制能量
```

更复杂的动力学轨迹优化还会引入速度、输入、时间步和动力学约束。这时可以使用 Drake 的 trajectory optimization 工具，例如 DirectCollocation，但要注意它对系统状态类型有要求。

## 第六步：验证结果

优化求出一条轨迹，不等于任务完成。还要检查：

| 检查项 | 为什么重要 |
|---|---|
| 求解器是否成功 | `result.is_success()` 不是可有可无 |
| 约束是否满足 | 数值误差可能让边界约束轻微违反 |
| 碰撞距离 | 轨迹中间点也要查，不只查起点终点 |
| 速度 / 加速度 | 控制器或硬件能不能跟踪 |
| 仿真回放 | 放回 plant 里看运动是否合理 |
| 可视化 | Meshcat 能帮助发现姿态和碰撞问题 |

Drake 的优势是这些检查可以很系统地做，而不是只凭肉眼看一段动画。

## 本页小结

Drake 工作流的核心是：建模型、连系统、设状态、做仿真、写优化、验结果。不要把 Drake 代码看成一堆 API，要把它看成一个从模型到系统再到优化和验证的流程。

## 导航

- 上一页：[三大模块](04-three-modules.md)
- 返回：[Drake](../05-drake.md)
- 下一页：[机械臂轨迹优化例子](06-arm-trajectory-optimization.md)

## 进一步阅读可以看：

- [Drake tutorials](https://drake.mit.edu/tutorials.html)
- [MultibodyPlant API](https://drake.mit.edu/doxygen_cxx/classdrake_1_1multibody_1_1_multibody_plant.html)
- [Modeling Dynamical Systems](https://drake.mit.edu/doxygen_cxx/group__systems.html)