# 一个完整例子：机械臂轨迹优化

目标：用一个机械臂从起点移动到目标点的例子，理解 Drake 如何把轨迹规划写成优化问题，而不是只在仿真里反复试动作。

这一页不直接承诺给出一段可以在所有机器上复制运行的完整 Drake 脚本，因为 Drake 版本、模型路径、求解器和安装方式都会影响代码细节。这里要讲清楚的是工作方式：机械臂轨迹优化在 Drake 里通常怎样拆成模型、变量、约束、代价、求解和验证。

## 任务设定

假设我们有一台 7 自由度机械臂，比如 KUKA iiwa 或 Franka Panda。任务是让机械臂从当前姿态移动到一个目标末端位姿，中间避开桌上的障碍物，并且轨迹尽量平滑。

用自然语言描述是：

```text
已知 q_start。
希望末端执行器到达 X_goal。
机械臂关节不能超过上下限。
轨迹中间不能碰到障碍物。
运动不要太抖。
最后得到一条 q(t)，可以交给控制器跟踪。
```

用 Drake 的语言描述，就是：

```text
MultibodyPlant 提供机械臂模型、关节限位和几何查询。
MathematicalProgram 保存每个时间点的 q_k。
约束保证起点、终点、限位和避障。
代价让轨迹平滑。
求解器给出离散路点。
回放和检查确保结果可用。
```

## 第一步：加载机械臂模型

先用 `MultibodyPlant` 和 `Parser` 加载机械臂。

```python
builder = DiagramBuilder()
plant, scene_graph = AddMultibodyPlantSceneGraph(builder, time_step=0.0)
Parser(plant).AddModels("iiwa.urdf")
plant.Finalize()
```

如果任务里还有桌子、物体或障碍物，也会在 `plant.Finalize()` 前一起加入模型。这里的重点是确认模型真的可用：关节数、关节名、末端 frame、碰撞几何、惯量和世界坐标都要检查。

如果这一步没确认，后面优化失败时很难判断是优化问题，还是模型本身错了。

## 第二步：选择轨迹表示

最简单的轨迹优化可以把轨迹离散成 N 个 knot points：

```text
q_0, q_1, q_2, ..., q_N
```

每个 `q_k` 是机械臂在第 k 个时间点的关节角。对于 7 自由度机械臂，`q_k` 是 7 维向量。

这里先讲 kinematic trajectory optimization，也就是优化关节位置序列，不直接把完整动力学作为约束。这比 DirectCollocation 简单，适合入门。等理解了变量、约束和代价，再进入动力学轨迹优化。

## 第三步：定义决策变量

用 `MathematicalProgram` 创建变量：

```python
prog = MathematicalProgram()
q = prog.NewContinuousVariables(N, nq, "q")
```

可以理解成：优化器要决定每个时间点的关节角。之后所有约束和代价都围绕这些变量写。

| 变量 | 含义 |
|---|---|
| `q[0]` | 起点关节角 |
| `q[k]` | 第 k 个中间路点 |
| `q[N-1]` | 终点关节角 |

## 第四步：加入起点和终点约束

起点约束通常很直接：

```text
q_0 = q_start
```

终点可以有两种写法。

第一种是关节空间终点：

```text
q_N = q_goal
```

第二种是末端位姿目标：

```text
p_WG(q_N) 接近 p_goal
R_WG(q_N) 接近 R_goal
```

第二种更接近实际任务，但也更复杂，因为它需要通过 plant 的正运动学把 `q_N` 转成末端位姿。Drake 的 `InverseKinematics` 和相关 position / orientation constraint 就是为这类问题准备的。

## 第五步：加入关节、速度和避障约束

机械臂轨迹不能只满足终点。中间点也要安全。

常见约束包括：

| 约束 | 形式 | 作用 |
|---|---|---|
| 关节限位 | `q_min <= q_k <= q_max` | 避免机械臂姿态非法 |
| 速度限制 | `|q_{k+1} - q_k| / dt <= v_max` | 避免轨迹太快 |
| 起点终点 | `q_0 = q_start`, `q_N = q_goal` | 保证任务边界 |
| 碰撞距离 | `distance(robot, obstacle) >= margin` | 保证避障 |
| 姿态约束 | 末端位置 / 姿态在容差内 | 保证抓取或放置姿态 |

避障是 Drake 的优势之一。通过 `SceneGraph` 和几何查询，可以把碰撞距离或最小距离约束引入规划问题。实际工程里，碰撞约束可能很难，求解器也可能失败，所以通常要从简单场景开始调。

## 第六步：加入平滑代价

没有代价时，只满足约束的轨迹可能很丑。常见平滑代价是让相邻路点变化不要太大：

```text
sum_k ||q_{k+1} - q_k||^2
```

也可以加入二阶差分，让速度变化更平滑：

```text
sum_k ||q_{k+2} - 2q_{k+1} + q_k||^2
```

这些代价不是物理定律，而是偏好。它告诉优化器：在满足约束的前提下，尽量选一条平滑、容易跟踪的轨迹。

## 第七步：求解并检查

求解后不能只看有没有返回结果。至少要检查：

```python
result = Solve(prog)
assert result.is_success()
q_sol = result.GetSolution(q)
```

然后继续检查：

| 检查 | 为什么重要 |
|---|---|
| 起点和终点误差 | 确认任务边界满足 |
| 关节限位 | 确认没有数值上越界 |
| 速度 / 加速度 | 确认控制器能跟踪 |
| 碰撞距离 | 确认整条轨迹安全 |
| Meshcat 回放 | 用可视化发现姿态异常 |
| plant 仿真 | 看控制器跟踪轨迹时是否稳定 |

Drake 的风格是：优化结果不是终点，验证才是终点。

## 和 DirectCollocation 的关系

上面讲的是入门版关节空间轨迹优化。它没有完整写入动力学方程。如果你要把动力学也放进轨迹优化，可以看 Drake 的 `DirectCollocation`。

`DirectCollocation` 会把连续系统的状态、输入和时间离散成多个 knot points，并添加 collocation 约束。官方文档说明它假设输入是一阶保持，状态是三次样条，并在断点和中点加入动力学约束；它只适用于系统的连续状态。

这类方法更强，但也更难。初学者建议先理解 kinematic trajectory optimization，再进入 dynamic trajectory optimization。

## 本页小结

机械臂轨迹优化体现了 Drake 的典型思路：先用 MultibodyPlant 表示机器人和几何，再用 MathematicalProgram 定义轨迹变量、约束和代价，最后求解并把结果放回系统中验证。它不是盲目 roll out 动作，而是把运动规划写成可以检查的优化问题。

## 导航

- 上一页：[Drake 工作流程](05-workflow.md)
- 返回：[Drake](../05-drake.md)
- 下一页：[Drake vs 其他仿真工具](07-comparison.md)

## 进一步阅读可以看：

- [DirectCollocation class reference](https://drake.mit.edu/doxygen_cxx/classdrake_1_1planning_1_1trajectory__optimization_1_1_direct_collocation.html)
- [Formulating and Solving Optimization Problems](https://drake.mit.edu/doxygen_cxx/group__solvers.html)
- [Robotic Manipulation](https://manipulation.csail.mit.edu/)
