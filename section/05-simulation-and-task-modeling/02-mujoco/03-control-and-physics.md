# 控制与物理

模型能加载、字段也读懂了，自然要问：怎么让它真正动起来？在 MuJoCo 里，答案不是直接把关节“掰”到某个角度，而是给 actuator 一个控制量，让物理把关节推过去。这一章就讲清楚这条“控制量 → 力 → 运动”的链路，以及一路上绕不开的接触与摩擦。

## 本章分两条线

为了不把“怎么让它动”和“物理怎么算”搅在一起，本章顺着两条线走：

- **控制线（怎么让它动）**：先弄清 actuator，也就是给 `data.ctrl` 写的那个数到底代表力、目标角度还是目标速度；再看 `mj_step` 怎么把这个数一步步变成运动；最后是 tendon / equality 这类“一个驱动带多个关节”的耦合。
- **物理线（接触怎么算）**：物体之间怎么判定接触、接触力怎么解，以及 friction / solref / solimp 这几组参数各管什么。

两条线最后汇到收尾两页：一张“现象 → 参数”的调参速查表，和一个从零写 PD 控制器的动手练习。

## 前置概念

读这一章前，建议先理解（详见 [mjModel vs mjData](02-modeling/06-mjmodel-vs-mjdata.md) 与 [常用字段速查](02-modeling/07-common-fields.md)）：

- **mjModel / mjData**：静态结构 vs 动态状态。
- **data.ctrl**：写给 actuator 的控制信号数组（本章会详讲它的语义）。
- **nq / nv / nu**：自由度数、速度维度、actuator 数。

## 本章代码怎么对照着跑

为讲清概念，本章正文里给的多是**说明性片段**：一段 MJCF，或几行调用，而不是完整脚本。想看它们真正跑起来，有几个落地的地方：

- 第 1 章那个正弦控制的 `mujoco_first_sim.py`（在 `labs/04-simulation/` 下）就是“写 `ctrl` → 反复 `mj_step`”的完整循环；
- 本章第一页会给一个**可以直接复制运行**的最小 actuator 例子，最后一页 [动手：写一个 PD 控制器](03-control-and-physics/07-hands-on-control.md) 是一份从零可跑的脚本；
- 凡是带 `class="panda"` 的 XML 片段，都来自真实的 `panda.xml`，可以用 `mjcf_inspect.py` 加载 Panda 自己核对。

## 学习路径

| 小节 | 读完能回答 | 重点 |
|---|---|---|
| [三类 actuator](03-control-and-physics/01-actuator-types.md) | 写进 `data.ctrl` 的数到底代表什么？ | ctrl 语义、motor/position/velocity、ctrlrange、general |
| [step 与流水线](03-control-and-physics/02-step-and-pipeline.md) | `ctrl` 写下去之后，`mj_step` 做了什么？ | forward vs step、内部流水线、积分器 |
| [tendon 与 equality](03-control-and-physics/03-tendon-and-equality.md) | 1 个 actuator 怎么管 2 个关节？ | tendon、equality |
| [接触模型](03-control-and-physics/04-contact-model.md) | MuJoCo 怎么判断、怎么解算接触？ | 凸接触、contype/conaffinity、`data.contact` |
| [摩擦与求解器参数](03-control-and-physics/05-friction-and-solver.md) | friction / solref / solimp 怎么调？ | 三类参数的真实示例 |
| [调参与排错](03-control-and-physics/06-tuning-and-debug.md) | 振荡 / 过冲 / 穿模 / 滑落怎么处理？ | 现象 → 参数速查表 |
| [动手：写一个 PD 控制器](03-control-and-physics/07-hands-on-control.md) | 不用现成 actuator 自己控关节是什么体验？ | 自定义 PD、轨迹跟踪、调参 |

## 导航

- 上一节：[建模](02-modeling.md)
- 返回上级：[MuJoCo](../02-mujoco.md)
- 下一节：[观测与渲染](04-observation-and-rendering.md)
