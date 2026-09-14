# 动手：写一个 PD 控制器

不用模型里现成的 position actuator，而是自己用 motor 加 Python 端写 PD 控制（一种按"位置误差 + 速度"算输出力的经典控制方法）。这一练习把"ctrl 是怎么变成力""stiffness/damping 调大调小是什么感觉"从抽象变成手感。

## 本节目标

做完这三个练习，应该能够：

1. 用 motor + 一行 PD 公式，复刻出 position actuator 的效果。
2. 调 Kp / Kd，亲眼看出欠阻尼、临界阻尼、过阻尼三种行为。
3. 给关节跟踪一条正弦轨迹，体会高频跟踪为什么更难。

每个练习都给了起点和验收信号，跑出对应结果就算过关。

## 练习 1：复刻 position actuator

**目标**：理解"position actuator 本质就是内置的 PD 控制器"。

**场景**：一个 hinge 关节带一根杆（一个 body + 一个 hinge joint + 一个 motor actuator）。为专注看 PD 本身，这里先把重力关掉，免得重力静差干扰观察。

```python
import numpy as np
import mujoco

xml = """
<mujoco>
  <option gravity="0 0 0"/>
  <worldbody>
    <body pos="0 0 0">
      <joint name="hinge" type="hinge" axis="0 1 0"/>
      <geom type="capsule" size="0.03" fromto="0 0 0 0 0 -0.5" rgba="0.8 0.2 0.2 1"/>
    </body>
  </worldbody>
  <actuator>
    <motor name="motor1" joint="hinge" ctrlrange="-50 50"/>
  </actuator>
</mujoco>
"""

model = mujoco.MjModel.from_xml_string(xml)
data = mujoco.MjData(model)

Kp = 50.0   # 比例增益（刚度）
Kd = 5.0    # 微分增益（阻尼）
target = 1.0  # 目标角度 1 rad（约 57°）

for i in range(500):
    # PD 控制：力矩 = Kp * (目标 - 当前位置) - Kd * 当前速度
    error = target - data.qpos[0]
    torque = Kp * error - Kd * data.qvel[0]
    data.ctrl[0] = torque
    mujoco.mj_step(model, data)
    if i % 50 == 0:
        print(f"step {i}: qpos={data.qpos[0]:.4f}, target={target}, error={error:.4f}")
```

**验收信号**：杆从初始角度（0 rad）转向 target，最终稳定在 target 上，稳态误差很小（< 0.01 rad）。

## 练习 2：调 Kp / Kd 找临界阻尼

在上面的基础上，固定 `target=1.0`，尝试以下三组参数：

| 场景 | Kp | Kd | 预期行为 |
|---|---|---|---|
| A：欠阻尼 | 50 | 1 | 杆冲过目标（到约 1.5），来回振荡几次才稳定 |
| B：临界阻尼 | 50 | 5 | 杆快速到达目标，几乎不超调、不振荡 |
| C：过阻尼 | 50 | 20 | 杆缓慢爬向目标，不振荡但更慢 |

把练习 1 的循环分别用这三组 `Kp`/`Kd` 各跑一遍，打印每 50 步的 `qpos`。三组并排跑出来是这样（绿色细线是目标角度 1.0 rad）：

<video src="../assets/mujoco-pd-damping.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

欠阻尼（左）冲过目标再荡回来，临界（中）最快稳稳到位，过阻尼（右）慢慢爬向目标、始终不超调。对照视频和打印出来的数字，就能把曲线形状和 `Kp`/`Kd` 对上。

**验收信号**：能观察到 A 有振荡（qpos 超过 1.0 再回来）、B 最快收敛、C 缓慢逼近。

## 练习 3：关节空间的正弦轨迹跟踪

接着练习 1 的脚本继续（复用同一个 `model`、`data`），把固定目标换成一条移动的正弦轨迹。先把状态重置干净、并选用临界阻尼那组增益：

```python
import math

mujoco.mj_resetData(model, data)   # 回到干净的初始状态
Kp, Kd = 50.0, 5.0                 # 练习 2 里临界阻尼那组

for i in range(500):
    t = data.time
    target = 1.0 * math.sin(2.0 * math.pi * 0.5 * t)  # 0.5Hz 正弦波
    error = target - data.qpos[0]
    torque = Kp * error - Kd * data.qvel[0]
    data.ctrl[0] = torque
    mujoco.mj_step(model, data)
    if i % 50 == 0:
        print(f"step {i}: qpos={data.qpos[0]:.4f}, target={target:.4f}, error={error:.4f}")
```

试着把频率从 0.5 Hz 加到 2 Hz，Kp/Kd 不变的情况下，跟踪误差会怎么变化？然后再试着增大 Kp/Kd，误差能恢复吗？

**验收信号**：低频时误差峰值约 0.3 rad（PD 跟踪正弦有固有相位滞后，属正常，不是代码写错了），高频时误差进一步变大。增大 Kp/Kd 后高频跟踪通常会改善，但也可能引入振荡。

## 验收清单

| 练习 | 验收标准 |
|---|---|
| 练习 1 | 杆能稳定到达 target=1.0，最终误差 < 0.01 rad |
| 练习 2 | 能区分三种阻尼行为：欠阻尼（振荡）、临界（最快）、过阻尼（最慢） |
| 练习 3 | 能跟踪正弦轨迹，理解高频跟踪需要更高的刚度/阻尼 |

## 参考资料

- [MuJoCo Documentation: Computation（actuation / passive dynamics）](https://mujoco.readthedocs.io/en/stable/computation/index.html)
- [Kevin Zakka, mjctrl（MuJoCo 最小 IK / 控制实现）](https://github.com/kevinzakka/mjctrl)

## 导航

- 上一节：[调参与排错](06-tuning-and-debug.md)
- 返回上级：[控制与物理](../03-control-and-physics.md)
- 下一节：[观测与渲染](../04-observation-and-rendering.md)
