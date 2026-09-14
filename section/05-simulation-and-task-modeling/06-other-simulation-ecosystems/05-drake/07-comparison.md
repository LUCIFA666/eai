# Drake vs 其他仿真工具

目标：理解 Drake 和 MuJoCo、Isaac Sim、Isaac Lab、Habitat、ManiSkill、Gazebo 等工具的差异，能判断什么时候该选 Drake，什么时候不该选。

Drake 经常被拿来和其他仿真器比较，但直接问“哪个更好”没有意义。它们解决的问题不同。Drake 的核心优势是模型化设计、系统组合、优化和验证；其他工具可能在高保真渲染、大规模 RL、ROS 工程联调或轻量仿真上更合适。

## 总览对比

| 工具 | 更适合 | 不适合直接替代 |
|---|---|---|
| Drake | 模型化设计、系统框图、轨迹优化、逆运动学、约束验证 | 大规模视觉 RL、RTX 场景渲染、纯黑盒 benchmark |
| MuJoCo | 轻量动力学、控制、接触、RL 原型 | 复杂系统框图和通用优化建模 |
| Isaac Sim | 高保真场景、传感器、ROS 2、合成数据 | 快速写数学规划和证明式约束分析 |
| Isaac Lab | Isaac Sim 上的大规模并行训练任务 | Drake 式模型分析和优化工具链 |
| Habitat | 室内导航、ObjectNav、VLN、EQA benchmark | 机械臂动力学和轨迹优化 |
| ManiSkill | 操作任务 benchmark、RL / IL 数据和环境 | 形式化系统建模和通用数学规划 |
| Gazebo | ROS / ROS 2 系统联调 | 优化驱动规划和 white-box 模型分析 |

## 什么时候选 Drake

适合选 Drake 的信号：

| 信号 | 说明 |
|---|---|
| 需要写 IK / 轨迹优化 | Drake 的 MathematicalProgram 和机器人模型结合紧密 |
| 需要系统框图 | Systems Framework 能清楚连接 plant、controller、estimator |
| 需要解释约束和代价 | Drake 比黑盒仿真更透明 |
| 需要模型化控制 | LQR、MPC、trajectory tracking 等更自然 |
| 需要生成专家轨迹 | 可用于 IL / VLA 数据和验证 |

不适合优先选 Drake 的信号：

| 信号 | 更应该看什么 |
|---|---|
| 主要任务是大规模端到端 RL benchmark | Isaac Lab、MuJoCo、ManiSkill |
| 需要高保真 RTX 图像和 ROS 2 工程接口 | Isaac Sim |
| 需要室内导航和语言导航 benchmark | Habitat |
| 只想快速教学演示物体下落 | PyBullet、MuJoCo |
| 重点是多物理流体软体 | Genesis 或专门多物理工具 |

## 本页小结

Drake 的优势不是“跑得最像游戏引擎”，也不是“最适合直接训练大规模策略”。它的价值是把机器人问题写成可解释的模型、系统和优化问题。选平台时先问自己：我需要的是高保真传感器、大规模训练、室内导航 benchmark，还是模型化规划控制？如果答案是后者，Drake 就很合适。

## 导航

- 上一页：[机械臂轨迹优化例子](06-arm-trajectory-optimization.md)
- 返回：[Drake](../05-drake.md)
- 下一页：[入门学习路径](08-learning-path.md)

## 进一步阅读可以看：

- [Drake 官网](https://drake.mit.edu/)
- [MuJoCo](../../02-mujoco.md)
- [Isaac Sim](../../03-isaac-sim.md)
- [Habitat 简介](../01-habitat-simulation.md)