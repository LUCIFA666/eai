# 机器人资产与物理配置

场景搭好后，下一步是把机器人真正放进这个世界里。这里的难点不只是“导入一个模型”，而是把来自 URDF / xacro / MJCF / CAD / mesh 的资产，变成 Isaac Sim 里能加载、能被识别成 articulation、能读关节、能驱动、物理属性也可信的 USD 资产。

## 本节目标

本节围绕下面几个问题展开：

1. 机器人资产从文件到可仿真的对象，中间要经过哪些检查？
2. 关节、执行器、碰撞体、质量和限位分别会影响什么行为？
3. 如何判断机器人是资产问题、物理配置问题，还是控制问题？
4. 换成自定义机器人时，哪些地方必须重新核对？

这一部分按一条资产流水线展开：**源资产 → USD → articulation → 物理体检 → 其它导入路径**。读完后，你应该能判断一台机器人到底是“只是显示出来了”，还是已经具备进入控制、观测和任务脚本的基本条件。

## 前置概念

读这一部分前，最好已经理解上一部分里的 Stage / Prim / prim path、`reset` 后才能读物理状态，以及世界坐标和米制单位。你不需要精通 USD 内部格式，也不要求已经会 ROS；但如果见过 URDF / xacro / RViz / MoveIt，会更容易理解第一节。

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [URDF 到 USD](03-robot-and-physics/01-urdf-to-usd.md) | 为什么不能把 URDF 当成 Isaac Sim 的最终资产？xacro、URDF、USD 怎么分层？ | URDF / xacro 导入、生成可复用 USD |
| [Articulation 关节体](03-robot-and-physics/02-articulation.md) | 导入后的 link / joint 什么时候算一台可驱动机器人？ | articulation root、DOF 名称、关节状态读写 |
| [物理属性配置与检查](03-robot-and-physics/03-physics-audit.md) | 为什么能显示还会穿地、发抖、夹不住、跟不上？ | collision、mass、friction、joint drive 体检 |
| [其它导入器](03-robot-and-physics/04-other-importers.md) | 不是 URDF 的资产怎么进 Isaac Sim？哪些东西导入后仍要重调？ | MJCF / CAD / mesh 导入路径与取舍 |

## 读完这一部分应该具备的判断力

| 看到的现象 | 你应该先想到 |
|---|---|
| 机器人能显示，但 `get_joint_positions()` 失败 | articulation root 或 reset 时机有问题 |
| 机器人一启动就掉下去 | 固定基座 / `fix_base` / 根 link 配置要查 |
| 物体穿过机器人或桌面 | collision 是否缺失、太粗或位置不对 |
| 夹爪闭合了但抓不住 | 指尖 collision、物理材质摩擦、夹爪 drive |
| 关节目标发了但跟不上 | drive stiffness / damping / max force / limit |
| 从 MuJoCo 迁移后行为不一样 | actuator、接触模型、站姿、单位需要按 PhysX 重设 |

## 导航

- 返回上级：[Isaac Sim](../03-isaac-sim.md)
- 上一页：[场景构建与坐标约定](02-building-a-world.md)
- 下一页：[控制](04-control.md)
