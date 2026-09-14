# Drake

目标：理解 Drake 在机器人仿真与任务建模中的定位，能分清它和 MuJoCo、Isaac Sim、Isaac Lab、Habitat、ManiSkill 等工具的差异，并知道它为什么特别适合模型化设计、系统组合、轨迹优化和形式化分析。

Drake 不能简单理解成“又一个仿真器”。它当然能仿真多体系统，也能做接触、可视化和机器人控制；但它真正突出的地方，是把机器人的动力学、系统框图和优化问题暴露出来，让研究者可以直接使用结构化方程、梯度、约束和求解器来做规划、控制和验证。

如果把 Isaac Sim 看成高保真机器人世界，把 MuJoCo 看成轻量动力学引擎，那么 Drake 更像一个 **model-based robotics toolbox**：它关心的不只是“跑出来一段仿真”，还关心这段运动背后的方程是什么、约束是什么、优化变量是什么、系统之间如何连接，以及结果能不能被解释和验证。

## 学习路径

| 页面                                                      | 这一页回答的问题 | 重点 |
|---------------------------------------------------------|---|---|
| [为什么需要 Drake](05-drake/01-why-drake.md)                 | 已经有很多仿真器了，为什么还需要 Drake？ | black-box 仿真限制、模型化设计、可解释规划控制 |
| [Drake 是什么](05-drake/02-what-is-drake.md)               | Drake 到底是仿真器、优化库还是机器人框架？ | C++ / Python toolbox、TRI 支持、模型分析与控制 |
| [核心思想](05-drake/03-core-ideas.md)                       | white-box + systems + optimization 分别是什么意思？ | 暴露方程结构、系统框图、优化驱动规划控制 |
| [三大模块](05-drake/04-three-modules.md)                    | Multibody Dynamics、Systems Framework、Optimization 如何配合？ | MultibodyPlant、Diagram、MathematicalProgram |
| [工作流程](05-drake/05-workflow.md)                         | 一个 Drake 项目通常怎么搭？ | 建模、系统连接、仿真、优化、验证 |
| [机械臂轨迹优化例子](05-drake/06-arm-trajectory-optimization.md) | Drake 如何把机械臂规划写成优化问题？ | q 轨迹、约束、代价、IK、碰撞、安全检查 |
| [Drake vs 其他工具](05-drake/07-comparison.md)              | 什么时候选 Drake，什么时候不选？ | MuJoCo、Isaac Sim、Isaac Lab、ManiSkill、Gazebo 对比 |
| [入门学习路径](05-drake/08-learning-path.md)                  | 新手怎么学 Drake 不会乱？ | Python 入口、MultibodyPlant、Diagram、Optimization、例子 |
| [Drake 示例](05-drake/09-server-minimal-run.md)           | 在服务器上怎么真实跑通 Drake？ | pydrake、Simulator、MultibodyPlant、Meshcat、iiwa 可视化 |

## 导航

- 上一页：[Gazebo](04-gazebo.md)
- 返回：[其他仿真生态](../06-other-simulation-ecosystems.md)
- 下一页：[为什么需要 Drake](05-drake/01-why-drake.md)

## 进一步阅读可以看：

- [Drake 官网](https://drake.mit.edu/)
- [Drake GitHub](https://github.com/RobotLocomotion/drake)
- [Drake tutorials](https://drake.mit.edu/tutorials.html)
- [Modeling Dynamical Systems](https://drake.mit.edu/doxygen_cxx/group__systems.html)
- [Multibody Kinematics and Dynamics](https://drake.mit.edu/doxygen_cxx/group__multibody.html)
- [Formulating and Solving Optimization Problems](https://drake.mit.edu/doxygen_cxx/group__solvers.html)
- [Robotic Manipulation: Perception, Planning, and Control](https://manipulation.csail.mit.edu/)
