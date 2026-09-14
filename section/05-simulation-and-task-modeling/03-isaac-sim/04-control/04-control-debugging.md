# 控制排查

前面三页讲完了控制链路、关节目标和运动生成。到这里，最重要的能力不是再记一个 API，而是遇到问题时知道先查哪一层。控制调试的核心原则是：**先证明 action 合理，再证明 drive 能执行，最后再看物理接触和上层策略。**

## 本节目标

本节围绕下面几个问题展开：

1. 机器人不动、乱动或抖动，怎么先按症状定位到出问题的层级？
2. 一条实用的控制排查顺序应该怎么走？
3. 怎么分别判断问题出在运动生成还是 drive？

## 先看症状，再定位层级

控制问题不要一上来就“调大 stiffness”或“换规划器”。先看症状属于哪一类：

| 症状 | 优先怀疑 | 第一件要查的事 |
|---|---|---|
| 完全不动 | action 没发到 articulation | `apply_action` 是否执行，`world.step()` 是否在循环里 |
| 关节瞬间跳变 | 把状态设置当控制用了 | 是否在循环里用了 `set_joint_positions` |
| 朝反方向动 | 关节顺序 / 单位 / frame 错 | 打印 DOF 名称、目标数组、单位 |
| 慢慢动但到不了 | drive 太软或目标越限 | stiffness / damping / max force、关节限位 |
| 到目标附近来回抖 | drive 过硬、阻尼不足、步长问题 | damping、timestep、目标更新频率 |
| 末端绕偏或突然甩一下 | 运动生成层问题 | end-effector frame、IK warm start、RMPflow 配置 |
| 控制看似对，接触结果不对 | 物理层问题 | collision、质量、摩擦、接触参数 |

这张表的意思不是“每个症状只有一个原因”，而是给你一个起手式：先查最可能的层，查不通再往下走。

## 一条实用排查顺序

推荐按下面顺序做最小化验证：

```text
1. articulation 是否可读
2. DOF 名称、数量、初始关节角是否正确
3. 目标数组长度、单位、关节顺序是否正确
4. apply_action 是否被调用
5. world.step 是否持续推进
6. 关节位置误差是否逐步下降
7. drive 参数是否足够执行目标
8. collision / friction / mass 是否让接触结果可信
```

对应到代码里，至少打印这些量：

```python
print("dof names:", robot.dof_names)
print("q start:", robot.get_joint_positions())
print("q target:", target)

robot.apply_action(ArticulationAction(joint_positions=target))
for i in range(120):
    world.step(render=False)
    if i in (0, 5, 30, 60, 119):
        q = robot.get_joint_positions()
        print(i, "max_err=", np.abs(q - target).max())
```

如果 `max_err` 不下降，先别怀疑相机、策略或数据格式。控制链路本身还没通。

## 运动生成问题怎么拆

IK / RMPflow 出问题时，不要只盯着“算法不行”。它们依赖一堆前提：

| 要素 | 查什么 | 常见后果 |
|---|---|---|
| 末端 frame | frame 名称、方向、是否和夹爪实际末端一致 | 末端去错位置或姿态反了 |
| base pose | 机器人 base 是否和运动生成配置同步 | 目标整体偏移 |
| robot description / URDF | 关节名、链路、限位是否对应 USD articulation | 解不出来或动作异常 |
| 碰撞球 / 障碍 | 大小、位置、是否每帧 `update_world()` | 过度绕行、穿障碍、卡住 |
| 目标更新频率 | 是否每帧重设目标，目标是否跳变 | 末端抖动或突然抽动 |
| warm start / 上一步解 | 是否利用当前姿态连续求解 | 多解跳变、奇异附近甩动 |

运动生成层最怕“坐标看起来差不多”。只要 base frame 或 end-effector frame 差一点，目标就会系统性偏移；这类问题靠调 drive 很难救。

## Drive 问题怎么判断

目标和 action 都合理，但机器人执行不好，才进入 drive 层。直觉上可以这样看：

| 表现 | 可能原因 | 调整方向 |
|---|---|---|
| 追得很慢 | stiffness 太低、max force 太小 | 提高刚度或最大力 |
| 到目标附近晃 | damping 太低或目标更新太快 | 增加阻尼、降低目标跳变 |
| 抖得厉害 | stiffness 太高、步长太大、碰撞体不稳 | 降刚度、查 timestep / collision |
| 负载下抬不动 | max force 不够、质量过大 | 提高 max force 或检查质量 |

drive 是执行器，不是规划器。它能让合理目标被更好地执行，但不能把不可达目标变可达，也不能修正错误的末端 frame。

## 小结

- 控制排查不要同时改很多层；先确认 action 发出，再看 step 推进，再看 drive 和物理。
- 完全不动先查 `apply_action`、`world.step()`、DOF 数量和目标数组。
- 末端偏移 / 抽动优先查 frame、IK / RMPflow 配置和目标连续性。
- 执行慢、软、抖才重点查 drive 参数和 timestep。
- 控制侧可信后，再进入观测章做 observation 对齐。

## 本章自测

- 打印 DOF 名称和初始关节状态。
- 用 `apply_action` 让至少一组关节目标稳定收敛。
- 解释 `set_joint_positions` 和 `apply_action` 的差别。
- 把末端空间目标经过 IK / RMPflow 变成关节动作，或至少知道它位于哪一层。

## 导航

- 返回目录：[控制](../04-control.md)
- 上一页：[运动生成](03-motion-generation.md)
- 下一页：[观测与传感器](../05-observation.md)
