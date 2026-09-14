# 入门学习路径

目标：给初学者一条稳妥的 Drake 学习路线，避免一上来就被 C++、系统框图、求解器、动力学和轨迹优化同时卡住。

Drake 的入门难度不低。它不像一些仿真器那样只要 `import` 后写一个 `step()` 就能看到结果。Drake 要求你理解模型、系统、Context、端口、Diagram、优化变量、约束和求解器。

因此学习路线要保守：先用 Python 和教程建立直觉，再看 MultibodyPlant，再看 Systems Framework，最后进入 Optimization 和轨迹规划。

## 第一阶段：先用 Python 入门

不要一开始就从 C++ 源码读起。Drake 的 Python 绑定已经足够用于入门、教学和很多算法原型。

第一阶段目标是：

```text
能安装或打开 Drake 教程环境
能 import pydrake
能运行一个官方 tutorial
能看懂 MultibodyPlant / Diagram / Simulator 这几个词
```

如果只是学习概念，可以先在线阅读 Drake tutorials 和 Robotic Manipulation 笔记，不必马上在本地装完整环境。

## 第二阶段：理解 MultibodyPlant

接下来学机器人模型。

建议从最小问题开始：加载一个简单机械臂或小车模型，打印关节名、设置关节角，查询末端位姿。

要掌握：

| 概念 | 通过标准 |
|---|---|
| body / joint / frame | 能说清机械臂有哪些关节和坐标系 |
| q / v | 能区分位置变量和速度变量 |
| plant context | 知道为什么查询位姿需要 context |
| Parser | 能从 URDF / SDF 加载模型 |
| Finalize | 知道 finalize 前后能做什么 |

这一步不要急着做优化。先把机器人模型读清楚。

## 第三阶段：理解 Systems Framework

学完 plant 后，再看系统连接。

建议目标是搭一个小 Diagram：

```text
constant source
  -> simple controller
  -> MultibodyPlant
  -> logger / visualizer
```

要掌握：

| 概念 | 通过标准 |
|---|---|
| System | 能把 plant、controller、source 都看成系统 |
| input / output port | 能解释数据从哪个端口流向哪个端口 |
| DiagramBuilder | 能把多个系统接起来 |
| Simulator | 能推进系统时间 |
| Logger / Meshcat | 能记录和查看结果 |

这一步的关键是改变写程序的方式：不是所有逻辑都放在一个 for 循环里，而是把模块变成系统，再显式连接。

## 第四阶段：学习 MathematicalProgram

然后再学优化。

先不要直接做机械臂轨迹优化，先写一个小优化问题：

```text
minimize (x - 1)^2
subject to x >= 0
```

再逐步扩展到：

```text
变量: q
约束: q_min <= q <= q_max
代价: ||q - q_nominal||^2
```

最后再把 plant 的运动学约束加进来。这样你会更清楚每个约束和代价是怎么进入求解器的。

## 第五阶段：做逆运动学

逆运动学是 Drake 进入机器人优化的好入口。它比完整轨迹优化简单，但已经能体现 Drake 的优势。

一个 IK 问题通常是：

```text
变量: q
约束: 末端位置在目标区域内
约束: 末端姿态在容差内
约束: q 在关节限位内
代价: q 接近某个舒适姿态
```

通过 IK，你会真正理解：机器人几何、约束和求解器如何结合。

## 第六阶段：做轨迹优化

轨迹优化是进阶内容。建议先做 kinematic trajectory optimization，再做 DirectCollocation。

路线如下：

| 阶段 | 内容 |
|---|---|
| 关节空间插值 | 先能生成一条简单路径 |
| Kinematic trajopt | 加入中间点、平滑代价、关节和避障约束 |
| IK + trajopt | 终点由末端位姿约束定义 |
| DirectCollocation | 加入系统动力学和输入变量 |
| 回放验证 | 把轨迹交给控制器或 plant 仿真检查 |

不要跳过验证。轨迹优化求解成功，不等于真实控制器一定能跟踪。

## 第七阶段：再看接触、MPC 和复杂系统

Drake 能做更复杂的内容，比如接触建模、模型预测控制、混合系统、几何优化等。但这些都不适合作为第一站。

进入这些主题前，至少应该能回答：

```text
plant 里有哪些 state？
controller 和 plant 怎么连接？
context 保存了什么？
优化变量是什么？
约束和代价分别是什么？
求解失败时从哪里排查？
```

如果这些问题还不清楚，先回到 MultibodyPlant、Systems 和 MathematicalProgram。

## 推荐学习顺序

| 阶段 | 学什么 | 暂时不要急着做什么 |
|---|---|---|
| 读概念 | Drake 是 model-based toolbox | 不要先看 C++ 源码 |
| 跑教程 | Python notebook、简单例子 | 不要先搭复杂机械臂任务 |
| 学 MultibodyPlant | body、joint、frame、context | 不要先做优化 |
| 学 Systems | System、port、Diagram、Simulator | 不要把所有逻辑写成大循环 |
| 学 MathematicalProgram | variables、constraints、costs | 不要先碰复杂非凸问题 |
| 学 IK | 末端位姿约束、关节限位 | 不要直接跳到接触优化 |
| 学轨迹优化 | q(t)、平滑、避障、DirectCollocation | 不要忘记仿真回放验证 |

## 本页小结

Drake 入门要按层推进：先用 Python 建直觉，再理解 MultibodyPlant，再理解 Systems Framework，然后进入 MathematicalProgram、IK 和轨迹优化。Drake 的门槛在于结构多，但一旦这些结构清楚，它就能成为非常强的机器人规划、控制和验证工具。

## 导航

- 上一页：[Drake vs 其他仿真工具](07-comparison.md)
- 返回：[Drake](../05-drake.md)
- 下一页：[Drake 服务器最小运行流程](09-server-minimal-run.md)

## 进一步阅读可以看：

- [Drake tutorials](https://drake.mit.edu/tutorials.html)
- [Drake Python bindings](https://drake.mit.edu/python_bindings.html)
- [Robotic Manipulation](https://manipulation.csail.mit.edu/)