# 末端控制

要让 Panda 的手移动到方块上方，大致有两条路：**关节空间控制**（直接给七个关节角）和**末端空间控制**（给末端一个目标位姿，反推关节角）。两种各有各的用处。

## 本节目标

本节把这两种方式讲透：

1. 关节空间和末端空间控制，差别到底在哪？
2. 各自的最小实现怎么写？
3. 抓取任务里，哪个阶段该用哪种？

## 关节空间控制：直接给七个角

关节空间控制最直观，直接设定每个关节的目标角度，让 position actuator 去追：

```python
import mujoco
import numpy as np

# 预定义的"方块上方"关节角（可以手动试出来或从 keyframe 获取）
above_block_qpos = np.array([0.0, -0.5, 0.0, -1.8, 0.0, 1.2, -0.8])

def joint_space_control(model, data, target_qpos, duration_steps=200):
    """从当前姿态平滑过渡到目标关节角"""
    for step in range(duration_steps):
        alpha = min(step / 50.0, 1.0)  # 朝目标平滑逼近（每步以当前 qpos 为基准）
        current_target = data.qpos[:7] + alpha * (target_qpos - data.qpos[:7])
        data.ctrl[:7] = current_target  # Panda 前 7 个 actuator 对应臂关节
        mujoco.mj_step(model, data)
```

**优点**：可靠，通常能稳定到达目标角，也不依赖 IK。
**缺点**：不够直观，单看这些角度往往看不出末端落在空间中的哪个位置。每换一个抓取位，多半要重新手动调角度。

## 末端空间控制：简化伺服

末端空间控制的思路是：**定义末端在空间中的目标位置，用雅可比矩阵把“末端应该往哪移”转成“关节应该怎么转”**。雅可比矩阵就是“关节速度 → 末端速度”的线性映射；把它近似求逆，就能反过来从“末端想怎么动”推出“关节该怎么转”。

```python
def end_effector_servo(model, data, target_pos, steps=200):
    """用雅可比矩阵做末端位置伺服"""
    for _ in range(steps):
        # 当前末端位置
        ee_pos = data.body("hand").xpos.copy()
        error = target_pos - ee_pos

        if np.linalg.norm(error) < 0.001:
            break

        # 计算雅可比（平动部分）
        jacp = np.zeros((3, model.nv))
        mujoco.mj_jac(model, data, jacp, None, ee_pos, data.body("hand").id)

        # 伪逆：关节速度 = J+ * 末端速度
        desired_vel = error * 5.0  # 比例控制
        dq = np.linalg.lstsq(jacp[:, :7], desired_vel, rcond=None)[0]

        # 直接把 dq 积分进 qpos（纯运动学预览，不走 actuator）
        data.qpos[:7] += dq * model.opt.timestep
        mujoco.mj_forward(model, data)
```

**优点**：直观，给末端一个目标位置（如 (0.5, 0, 0.3)）即可，不用管关节角是多少。
**缺点**：可能遇到奇异点（雅可比不满秩）、可能超出关节限位。上面对关节限位的处理被省略了，实际使用时需要加 clamp。还要留意：这个简化版是直接把 `dq` 积分进 `qpos` 再 `mj_forward`，属于**纯运动学预览**（不经过 actuator，也没有接触和动力学），适合快速看末端够不够得到目标。用它试目标点时别直接瞄方块中心：hand 的原点在指尖上方约 10cm，纯运动学下瞄中心会让手从视觉上穿进方块，常见做法是瞄方块上方 10cm 左右。真正带接触的抓取里，更稳的做法是把规划和执行分开，见[完整抓取流程](04-full-pick-pipeline.md)。

<figure class="doc-figure" aria-label="关节空间 vs 末端空间">
  <p class="doc-figure-title">两种控制方式的对比</p>
  <table>
    <tr><th></th><th>关节空间</th><th>末端空间</th></tr>
    <tr><td>输入</td><td>7 个关节角度</td><td>末端 xyz 位置（+ 朝向）</td></tr>
    <tr><td>直观程度</td><td>低（末端在哪需要心算）</td><td>高（直接指定空间位置）</td></tr>
    <tr><td>可靠性</td><td>高（通常能稳定到达）</td><td>中（可能奇异、超限位）</td></tr>
    <tr><td>计算量</td><td>几乎为 0</td><td>每步需算伪逆</td></tr>
    <tr><td>适合阶段</td><td>预定义轨迹、初始验证</td><td>动态目标、变抓取位</td></tr>
  </table>
</figure>

## 两种方法的选择指南

在抓取任务里，一个比较实用的策略是：

- **reach 阶段**：用末端空间控制，因为方块位置可能每次不同。
- **lift 阶段**：用关节空间控制，直接抬起 joint2 或 joint4，简单可靠。
- **place 阶段**：同 reach，末端空间。

这只是一种常见分工。到了[完整抓取流程](04-full-pick-pipeline.md)，为了让四个阶段共用同一套代码，那里把 lift 也写成"解一次 IK、只是把目标点抬高"，省得为 lift 单独写关节空间逻辑。两种都行，按自己习惯选。

## 调参表

| 参数 | 太小 | 太大 | 推荐起点 |
|---|---|---|---|
| 伺服增益（error 乘的系数） | 末端移动很慢，到不了目标 | 末端抖动、过冲 | 3-5 |
| 插值步数（duration_steps） | 轨迹不平滑 | 动作太慢 | 50-100 |
| 雅可比伪逆的 rcond | 关节速度太大 | 关节几乎不动 | 1e-3 |

以推荐起点的增益 5 为例，每步大约只缩小 1% 的误差（5 × timestep 0.002 = 0.01），伺服到位通常要几百步——末端逐步逼近是正常现象，不是卡住了。

## 失败案例

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 末端不动 | 雅可比矩阵接近奇异（比如手臂完全伸直） | 把目标位稍微调整，避开奇异姿态 |
| 关节角超出限位 | 雅可比解出的 dq 把关节推到限位外 | 每步对 dq clamp：保持关节在 range 内 |
| 末端来回振荡 | 伺服增益太大 | 减小增益或加 damping |

## 小结

- 关节空间控制简单可靠但不直观；末端空间控制直观但需要处理奇异和限位。
- 简化伺服（雅可比伪逆 + 比例控制）在多数情况下就够用，不一定要上重量级 IK 库。
- 实际抓取任务里，reach 用末端空间、grasp/lift 用关节空间是一种常见的组合。

## 参考资料

- [MuJoCo Documentation: Python Bindings（mj_jac）](https://mujoco.readthedocs.io/en/stable/python.html)
- [MuJoCo least_squares.ipynb（Inverse Kinematics / Jacobian 示例）](https://github.com/google-deepmind/mujoco/blob/main/python/least_squares.ipynb)
- [Kevin Zakka, mjctrl（MuJoCo 最小 IK / 控制实现）](https://github.com/kevinzakka/mjctrl)
- [dm_control: inverse_kinematics.py（`qpos_from_site_pose`，工业级 DLS IK，想要更鲁棒的实现可参考）](https://github.com/google-deepmind/dm_control/blob/main/dm_control/utils/inverse_kinematics.py)

## 导航

- 上一节：[搭场景](01-scene-setup.md)
- 返回上级：[抓取实战](../06-grasping-walkthrough.md)
- 下一节：[夹爪控制](03-gripper-control.md)
