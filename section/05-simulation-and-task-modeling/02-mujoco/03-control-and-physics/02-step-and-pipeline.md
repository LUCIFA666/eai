# step 与流水线

上一节我们给 `data.ctrl` 写了目标、关节就动了；但从“写下去”到“真正生效”，中间隔着一次 `mj_step`。下面这段 Panda 沿正弦轨迹运动的视频，就是第 1 章 `mujoco_first_sim.py` 跑出来的：它的循环很简单，每帧写一次 `data.ctrl[:]`、再调几次 `mj_step`（这里每渲染 1 帧、物理走 5 步）。

<video src="../assets/mujoco-first-sim.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

可真照着自己写这种循环，新手常撞上两个困惑：“设了 `ctrl`，`qpos` 怎么没动？”“状态和 sensor 到底该在 `mj_step` 之前读、还是之后读？”要解开这些，得拆开 `mj_step`，看清它内部那条流水线的顺序。

## 本节目标

本节拆开 `mj_step`，回答几个问题：

1. `mj_step` 一次调用，内部按什么顺序跑完一条流水线？
2. 它和 `mj_forward` 分工有什么不同，各自什么时候用？
3. 积分器怎么选，`timestep` 多大合适？

## mj_step 内部做了什么

`mj_step(model, data)` 是一个很“厚”的函数。想抓主干，看后面那张 6 格流程图就够；想要精确顺序，它内部按下面 11 步进行：

1. **检查位置和速度**：如果检测到 NaN 或无穷大，自动重置仿真。
2. **正向运动学**（`mj_fwdPosition`）：从 `qpos` 算出各 body 的世界位置和朝向。
3. **传感器（位置相关）**（`mj_sensorPos`）：更新只依赖位置的传感器。
4. **正向速度**（`mj_fwdVelocity`）：从 `qvel` 算出各 body 的世界线速度和角速度。
5. **传感器（速度相关）**（`mj_sensorVel`）：更新依赖速度的传感器。
6. **控制回调**（如果有的话）：调用用户注册的控制回调，计算 `ctrl`。
7. **驱动**（`mj_fwdActuation`）：把 `ctrl` 转成关节力。
8. **正向加速度**（`mj_fwdAcceleration`）：计算加速度。
9. **约束求解**（`mj_fwdConstraint`）：求解接触、限位、等式约束等。
10. **传感器（加速度相关）**（`mj_sensorAcc`）：更新依赖加速度的传感器。
11. **数值积分**：根据选定的积分器，把状态推进一个 `timestep`。

用一张简化的流程图来表示：

<figure class="doc-figure figure-pipeline" aria-label="mj_step 内部流水线">
  <p class="doc-figure-title">mj_step 的内部流水线</p>
  <div class="figure-pipeline">
    <div class="figure-node tone-green">
      <strong>检查</strong>
      <span>验证 qpos / qvel 合法性</span>
    </div>
    <div class="figure-node tone-blue">
      <strong>正向运动学</strong>
      <span>qpos → body 位姿</span>
    </div>
    <div class="figure-node tone-gold">
      <strong>传感器</strong>
      <span>更新位置/速度相关 sensor</span>
    </div>
    <div class="figure-node tone-rose">
      <strong>驱动 + 加速度</strong>
      <span>ctrl → 力 → 加速度</span>
    </div>
    <div class="figure-node tone-green">
      <strong>约束求解</strong>
      <span>接触/限位/等式约束</span>
    </div>
    <div class="figure-node tone-blue">
      <strong>积分</strong>
      <span>qpos / qvel / time 前进一步</span>
    </div>
  </div>
  <div class="figure-note">记住这条主线就够：先用 <code>mj_step</code> 让它跑完一整遍，再去读 <code>qpos</code>、sensor、接触，拿到的才是当前这一步的最新值。</div>
</figure>

理解这个顺序有一个很实际的意义：**接触和传感器读数要等仿真推进时才更新**。在 `mj_step` 之前读到的可能还是旧值，所以一般先 `mj_step`、再读观测。

## mj_forward 与派生量

`mj_forward(model, data)` 等价于 `mj_step` 去掉最后的“积分”那一步：上面流水线里的检查、正向运动学、传感器、驱动、加速度、约束求解它**都会算一遍**，唯独不做数值积分，所以时间和状态不往前推进。

典型使用场景：

```python
# 手动设好初始姿态后，刷新一次所有派生量
data.qpos[:] = home_qpos
mujoco.mj_forward(model, data)
# 现在 data.body("hand").xpos 等派生量就对应新的 qpos 了
```

另一个常见场景是：只改了 `qpos` 想看看末端位置，而不想让仿真真的往前走。这时用 `mj_forward` 就够了，用 `mj_step` 反而会让状态推进一个步长。

**混用的典型 bug**：在初始化时调了 `mj_step` 而不是 `mj_forward`。后果是时间被推进了 `timestep`，而本意只是想让派生量和姿态对齐。

## 积分器：euler / implicitfast / implicit / RK4

积分器和后面的 `timestep` 都属于引擎设置，第一遍读可以先跳过，遇到仿真不稳定再回来调。MuJoCo 提供了四种积分器，由 `model.opt.integrator` 控制：

| 积分器 | 每步计算量 | 稳定性 | 适合场景 |
|---|---|---|---|
| `mjINT_EULER`（欧拉） | 低 | 一般 | 快速原型、简单场景 |
| `mjINT_IMPLICITFAST`（隐式快速） | 中 | 好 | 官方推荐，Panda 等模型常显式选用 |
| `mjINT_IMPLICIT`（隐式） | 中 | 更好 | 对稳定性要求更高的场景 |
| `mjINT_RK4`（四阶龙格-库塔） | 高 | 很好 | 需要高精度积分，但会慢不少 |

需要说明的是，MuJoCo 引擎的全局默认其实是 `Euler`；`IMPLICITFAST` 是官方推荐、许多 menagerie 模型（如 Panda）会在 `<option>` 里显式选用的一种，它在速度和稳定性之间有不错的平衡。如果发现仿真“抖动”或者关节位置异常，第一步可以试着把积分器切换到 `IMPLICIT` 看看是否改善；如果还不行，再考虑减小 `timestep`。

RK4 每步要评估 4 次动力学，所以比隐式方法慢，但精度更高。在多数机器人仿真场景里，`IMPLICITFAST` 配合合适的 `timestep` 已经足够了。

## timestep 选取的权衡

`timestep` 决定了每次 `mj_step` 推进多少仿真时间。这是一个经典的“速度 vs 稳定性”权衡：

- **太小（如 0.0001）**：仿真非常稳定，但要跑很多很多步才能覆盖 1 秒的仿真时间，墙钟时间很长。
- **太大（如 0.05）**：墙钟时间短，但数值积分误差大，容易不稳定甚至发散（状态变成 NaN）。
- **常见区间**：机械臂仿真通常用 `0.001 ~ 0.005`，Panda 没单独设 `timestep`、沿用 MuJoCo 默认的 `0.002`。

把同一座方块塔用两种步长各跑一遍，差别立刻显出来：左边 `dt=0.002` 塔稳稳立着，右边只把步长放大到 `0.04`，接触和积分就跟不上，整座塔晃散塌掉。

<video src="../assets/mujoco-timestep-compare.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

一个实用的调试顺序：如果仿真不稳定，先试试把 `timestep` 减半（比如从 0.002 改成 0.001），而不是上来就调积分器或求解器参数。很多时候减半步长就能稳定下来。

## 小结

- `mj_step` 是一条固定顺序的流水线：检查 → 正向运动学 → 传感器 → 驱动 → 加速度 → 约束 → 积分。
- `mj_forward` 等价于 `mj_step` 但跳过最后的积分（不推进时间），驱动、加速度、约束、传感器都照常计算，适合初始化姿态后刷新派生量。
- 引擎默认是 `Euler`，但实践中常用、也更推荐 `IMPLICITFAST`；遇到不稳定优先减半步长。
- `timestep` 越小越稳定但越慢，需要按任务权衡。

## 动手练习

分别用 `mj_step` 和 `mj_forward` 跑一段循环，每次循环后打印 `data.time`，对比哪个会让时间前进，体会两者的分工。

## 参考资料

- [MuJoCo Documentation: Computation（simulation pipeline）](https://mujoco.readthedocs.io/en/stable/computation/index.html)
- [MuJoCo Documentation: XML Reference（option / integrator）](https://mujoco.readthedocs.io/en/stable/XMLreference.html)

## 导航

- 上一节：[三类 actuator](01-actuator-types.md)
- 返回上级：[控制与物理](../03-control-and-physics.md)
- 下一节：[tendon 与 equality](03-tendon-and-equality.md)
