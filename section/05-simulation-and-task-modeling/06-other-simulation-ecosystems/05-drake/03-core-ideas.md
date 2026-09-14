# Drake 的核心思想（white-box + systems + optimization）

目标：理解 Drake 的三个核心思想：white-box、systems 和 optimization。只有把这三件事连起来，才不会把 Drake 误读成普通仿真器。

它的核心思想可以概括成三句话：

```text
white-box：尽量暴露模型和方程结构。
systems：把机器人、控制器、估计器、传感器都看成可连接的系统。
optimization：把规划、控制、逆运动学和验证写成变量、约束和代价。
```

这三件事合起来，构成 Drake 的独特定位。

## White-box：不是只看输入输出

很多仿真环境像黑盒：给动作，拿观测。这样很适合训练策略，但不适合做结构化分析。

Drake 更强调 white-box。这里的 white-box 不是说所有东西都简单，而是说它尽量把系统内部结构暴露给你：状态、参数、输入输出端口、动力学、几何、约束、梯度和优化变量。

| 黑盒思路 | Drake 思路 |
|---|---|
| 只看 `action -> observation` | 看 state、input、output、context 和 dynamics |
| 碰撞后再发现失败 | 尽量把碰撞距离写成约束或检查项 |
| 轨迹不好就继续采样 | 把轨迹写成优化变量，调整代价和约束 |
| 控制器藏在环境内部 | 控制器是一个 System，端口连接是显式的 |
| 结果主要靠大量 rollouts | 结果可以结合模型、约束和求解器解释 |

white-box 的好处是可解释、可调试、可验证。坏处是你需要理解更多结构，入门不会像随机跑一个 Gym 环境那么快。

## Systems：机器人程序是系统图

Drake 的 Systems Framework 受 Simulink 一类框图建模思想影响。每个模块都是一个 `System`，有自己的状态、输入端口、输出端口、参数和计算逻辑。多个 System 可以连接成 `Diagram`。

例如一个机械臂仿真可以拆成：

```text
trajectory source
  -> controller
  -> MultibodyPlant
  -> state output
  -> visualizer / logger / estimator
```

在 Drake 里，这些不是随便写在一个 while 循环里的函数，而是可以显式声明端口并连接起来的系统模块。这样做的好处是：模块边界清楚，输入输出清楚，仿真和调试更可控。

常见对象可以这样看：

| 对象 | 作用 |
|---|---|
| `System` | 一个动态或静态模块 |
| `Context` | 这个系统在某一时刻的状态和参数 |
| `InputPort` / `OutputPort` | 系统之间传递信息的接口 |
| `DiagramBuilder` | 负责把多个系统连接起来 |
| `Diagram` | 连接完成后的整体系统 |
| `Simulator` | 推进系统随时间变化 |

Systems 思想对具身智能很有用，因为真实机器人不是一个单函数。它由 perception、state estimation、planning、control、plant、logging、visualization 等模块组成。Drake 的系统框架让这些模块的连接关系更显式。

## Optimization：把机器人问题写成数学程序

Drake 另一个核心是优化。`MathematicalProgram` 是 Drake 里组织优化问题的核心容器。你把决策变量、约束和代价加进去，Drake 再调用合适的求解器。

一个优化问题通常长这样：

```text
decision variables: x
minimize:           cost(x)
subject to:         constraints(x)
```

对应到机器人任务，可以是：

| 机器人问题 | 优化变量 | 约束 | 代价 |
|---|---|---|---|
| 逆运动学 | 关节角 q | 末端位姿、关节限位、碰撞距离 | 离参考姿态近 |
| 轨迹优化 | 每个时间点的 q、v、u | 动力学、速度、加速度、碰撞 | 平滑、时间、能量 |
| 抓取规划 | 物体位姿、接触点、手爪姿态 | 几何接触、力闭合、碰撞 | 稳定性、可达性 |
| 控制设计 | feedback gain 或控制输入 | 系统动力学、稳定性条件 | 跟踪误差、控制代价 |

Drake 的优化不是只为“求最小值”。它是把机器人问题变成可检查的结构：哪些变量能动，哪些条件必须满足，哪些目标是偏好。

## 三个思想怎么合起来

真正使用 Drake 时，这三件事不是分开的。

一个机械臂轨迹优化例子可以这样看：

```text
white-box
  机械臂的关节、几何、运动学和约束都能被访问

systems
  机械臂 plant、控制器、轨迹源和可视化组成 Diagram

optimization
  起点、终点、碰撞距离、速度限制和平滑性写成 MathematicalProgram
```

这就是 Drake 的风格：不是只把 robot 放到世界里，然后看它动；而是把运动背后的模型、连接和优化问题都摆出来。

## 本页小结

Drake 的核心思想是 white-box、systems 和 optimization。white-box 让模型结构可见，systems 让模块连接清楚，optimization 让规划和控制能写成变量、约束和代价。理解这三点后，再看 MultibodyPlant、DiagramBuilder、MathematicalProgram，就不会觉得它们是零散 API。

## 导航

- 上一页：[Drake 是什么](02-what-is-drake.md)
- 返回：[Drake](../05-drake.md)
- 下一页：[三大模块](04-three-modules.md)

## 进一步阅读可以看：

- [Modeling Dynamical Systems](https://drake.mit.edu/doxygen_cxx/group__systems.html)
- [Formulating and Solving Optimization Problems](https://drake.mit.edu/doxygen_cxx/group__solvers.html)
- [Multibody Kinematics and Dynamics](https://drake.mit.edu/doxygen_cxx/group__multibody.html)