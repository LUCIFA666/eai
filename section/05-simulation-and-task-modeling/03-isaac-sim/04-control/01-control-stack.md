# 控制链路与 API 边界

机器人资产已经能加载、物理也基本可信之后，不要急着写 IK 或策略。Isaac Sim 的控制链路比“给变量赋值”多几层：你发出的 action 不是直接把机器人摆到某个姿势，而是交给 articulation controller、joint drive 和 PhysX，在一帧帧仿真里执行出来。先把这条链路看清，后面的关节控制和运动生成才不会混成一团。

## 本节目标

本节围绕下面几个问题展开：

1. 一个动作命令从代码意图到物理运动，中间要经过哪些层？
2. 控制相关的三类 API 各管什么，为什么不能混用？
3. 为什么要把控制和观测拆成两部分分别讲？

## 从意图到物理运动

在 Isaac Sim 里，“让机器人动一下”通常会经过这条链：

<figure class="doc-figure">
<p class="doc-figure-title">Isaac Sim 控制链路</p>
<div class="figure-flow">
<div class="figure-node"><strong>任务意图：</strong>抓杯子、移动到目标点、打开夹爪</div>
<div class="figure-node"><strong>运动目标：</strong>末端位姿、关节目标、速度目标、力矩目标</div>
<div class="figure-node"><strong>ArticulationAction：</strong>把目标装进 <code>joint_positions</code> / <code>joint_velocities</code> / <code>joint_efforts</code></div>
<div class="figure-node"><strong>Articulation Controller：</strong>把 action 分发到对应关节</div>
<div class="figure-node"><strong>Joint Drive：</strong>按 stiffness / damping / max force 产生约束力</div>
<div class="figure-node"><strong>PhysX step：</strong>推进动力学、接触、重力和约束</div>
</div>
<p class="doc-figure-subtitle">action 是目标，drive 是执行器，PhysX step 才让运动真正发生。</p>
</figure>

所以控制问题要分层看：

| 层级 | 你写的东西 | 负责什么 | 常见错误 |
|---|---|---|---|
| 任务层 | “去杯子上方”“关节转到某角度” | 说清目标 | 目标本身不可达或不合理 |
| 运动生成层 | IK / RMPflow / 轨迹 | 把空间目标变成关节 action | frame 配错、解跳变、避障配置不对 |
| action 层 | `ArticulationAction(...)` | 指定位置 / 速度 / 力矩目标 | DOF 数量不对、单位不对、关节顺序错 |
| drive 层 | stiffness / damping / max force | 把目标变成力和约束 | 太软、太硬、力不够、抖动 |
| 物理层 | mass / collision / friction / timestep | 决定接触和动力学结果 | 穿模、滑动、弹跳、失稳 |

后面几页就是顺着这个层级展开：先讲 action 怎么发，再讲空间目标怎么变成 action，最后讲出问题怎么沿链路查。

## 三类 API 不要混用

初学 Isaac Sim 时，最容易把“设置状态”和“控制运动”混在一起。

| API / 参数 | 属于哪一层 | 用在什么时候 | 不适合做什么 |
|---|---|---|---|
| `set_joint_positions(...)` | 状态设置 | reset、初始化、把机器人摆到已知姿态 | 不适合在控制循环里当作“运动” |
| `apply_action(ArticulationAction(...))` | 控制输入 | 每帧或每段控制里发目标 | 不会让机器人瞬间到位 |
| Drive stiffness / damping / max force | 执行器属性 | 配置关节如何追目标 | 不负责决定“目标去哪” |
| `world.step(...)` | 仿真推进 | 让 drive、接触、重力真正生效 | 不能省略，也不能只发 action 不 step |

一句话记住：**reset 时可以 set，运行时要 apply，运动发生靠 step，执行质量看 drive。**

如果在控制循环里反复 `set_joint_positions`，你看到的是“瞬移”或“强行覆盖状态”，不是物理意义上的控制。它可以用于初始化和调试，但不能说明控制器真的能工作。

## 最小控制循环长什么样

不管上层是手写关节目标、IK、RMPflow，还是策略网络，落到底层都长得差不多：

```python
world.reset()

for step in range(num_steps):
    action = make_action(step)          # 关节目标 / 运动生成 / 策略输出
    robot.apply_action(action)          # 发给 articulation
    world.step(render=False)            # 让 PhysX 推进一步
    q = robot.get_joint_positions()     # 读回状态，用于检查误差
```

这段循环里有三个检查点：

| 检查点 | 看什么 | 说明什么 |
|---|---|---|
| action 发出前 | 目标长度、单位、关节顺序 | action 是否和机器人 DOF 对得上 |
| `world.step()` 后 | 关节位置 / 速度是否变化 | drive 和物理是否真的执行 |
| 多步之后 | 误差是否收敛、是否抖动 | drive 参数和目标是否合理 |

不要只看视频，也不要只看最后一帧。控制是否可靠，先看“目标和实际状态之间的误差是否按预期变化”。

## 为什么控制和观测拆开讲

具身智能最后一定会变成 observation → action 闭环，但学习时最好先拆开。原因很简单：如果机器人没动，或者动错了，此时把相机、深度、分割、时间戳都加进来，只会让问题更难定位。

控制章只回答一个问题：**我发出的动作，是否让机器人按预期运动？**

观测章再回答另一个问题：**机器人和世界运动之后，我能不能稳定、对齐地读回状态和传感器数据？**

把这两件事分开，调试路径会清楚很多：

```text
先让 action -> motion 可信，
再让 motion -> observation 可信，
最后才把 observation -> action 串成闭环。
```

## 小结

- 控制链路是“目标 → action → controller → drive → PhysX step”，不是直接改变量。
- `set_joint_positions` 适合初始化，`apply_action` 才是运行时控制，`world.step()` 让控制真正发生。
- 控制问题要分层排查：目标、action、drive、物理，哪一层错了就在哪一层修。
- 本部分先把 action → motion 调通，下一部分再讲 observation 和时间对齐。

## 导航

- 返回目录：[控制](../04-control.md)
- 上一页：[机器人资产与物理配置](../03-robot-and-physics.md)
- 下一页：[关节控制基础](02-joint-control.md)
