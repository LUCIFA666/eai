# 任务由什么组成

一个 Isaac Lab 任务不是一段单一脚本，而是一组围绕 MDP 循环协作的配置和函数。本页先建立最小结构，再沿着 Manager 展开。

## 本节目标

本节围绕下面几个问题展开：

1. 从 MDP（观测 / 动作 / 奖励 / 终止）反推，一个 Isaac Lab 任务最少由哪几块组成？
2. Scene、Observation、Action、Reward、Termination、Event 各自负责什么？
3. 看一个跑起来的例子时，怎么把这些块和代码一一对上？

在正式读文件前，可以先记住这个最小结构：

```text
一个任务 = scene + observation + action + reward + termination + event
```

其中 scene 是状态载体，其余部分负责把状态转成强化学习需要的接口。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-env-structure.svg" alt="Isaac Lab 环境结构：Scene 与各 Manager 围绕 MDP 数据流" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">Manager-based 环境的组成：InteractiveScene 提供机器人、物体和传感器；各 Manager 围绕 observation / action / reward / termination / reset 形成训练闭环。</figcaption>
</figure>

## 从 MDP 反推任务结构

强化学习算法看到的是一个标准循环：

```text
obs_t -> policy -> action_t -> env.step(action_t)
      -> obs_{t+1}, reward_t, terminated, truncated
```

Isaac Lab 要做的事，是把 Isaac Sim 里的物理世界翻译成这个循环。

| MDP 中的概念 | Isaac Lab 中通常对应 |
|---|---|
| 状态 | `InteractiveScene` 中的机器人、物体、传感器缓存 |
| 观测 | `ObservationsCfg` / Observation Manager |
| 动作 | `ActionsCfg` / Action Manager |
| 奖励 | `RewardsCfg` / Reward Manager |
| 终止 | `TerminationsCfg` / Termination Manager |
| 重置和随机化 | `EventCfg` / Event Manager |
| 目标命令 | `CommandsCfg` / Command Manager |

读任务时，先问每段代码属于哪一列。这个问题比“这一行 API 是什么”更重要。

## 运行例子

这些 Manager 不是抽象概念。启动一个 CartPole 环境时，Isaac Lab 会把每个 Manager 的内容打印出来。下面是 Action Manager 和 Observation Manager 的启动摘要：

```text
[INFO] Action Manager:  <ActionManager> contains 1 active terms.
+-----------------------------------+
|   Active Action Terms (shape: 1)  |
+-------+---------------+-----------+
| Index | Name          | Dimension |
+-------+---------------+-----------+
|   0   | joint_efforts |         1 |
+-------+---------------+-----------+

[INFO] Observation Manager: <ObservationManager> contains 1 groups.
+------------------------------------------------------+
| Active Observation Terms in Group: 'policy' (shape: (4,)) |
+------------+----------------------------+------------+
|   Index    | Name                       |   Shape    |
+------------+----------------------------+------------+
|     0      | joint_pos_rel              |    (2,)    |
|     1      | joint_vel_rel              |    (2,)    |
+------------+----------------------------+------------+
```

对照上面的 MDP 表读这段输出：

- **Action Manager** 对应“动作”：CartPole 只有 1 维动作 `joint_efforts`（给小车关节施加的力）。
- **Observation Manager** 对应“观测”：`policy` 组共 `(4,)` 维，由 `joint_pos_rel (2,)` 和 `joint_vel_rel (2,)` 拼成。
- 任务启动时，每个 Manager 都会这样“自报家门”。读任务时先看这几张表，就知道这个环境的 MDP 接口长什么样，再去翻对应的 `Cfg` 配置类。

## Scene

`InteractiveSceneCfg` 负责声明环境里有什么。它通常包括：

- 机器人，例如 Franka、UR10、ANYmal、Go2；
- 物体，例如方块、桌子、目标球；
- 地面、灯光、相机、接触传感器；
- 并行环境数量 `num_envs` 和环境间距 `env_spacing`。

示意结构：

```python
@configclass
class MySceneCfg(InteractiveSceneCfg):
    robot = FRANKA_PANDA_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
    target = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Target")
    table = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Table")
```

`{ENV_REGEX_NS}` 是理解并行环境的关键：同一套资产会被克隆到不同环境命名空间里，形成成百上千个并行副本。

## Observation

Observation Manager 把场景状态整理成策略输入。一个 observation term 通常返回形状为 `(num_envs, dim)` 的张量。

```python
@configclass
class ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        target_pos = ObsTerm(func=mdp.generated_commands, params={"command_name": "ee_pose"})

    policy: PolicyCfg = PolicyCfg()
```

读 observation 时要关注三件事：

| 问题 | 为什么重要 |
|---|---|
| 策略到底能看到哪些状态？ | 看不到的信息不能指望策略利用。 |
| 是否包含目标命令？ | reach、locomotion 这类任务通常需要把目标作为观测。 |
| 是否做了噪声、裁剪、历史堆叠？ | 这些会影响训练稳定性和 Sim2Real 泛化。 |

## Action

Action Manager 把神经网络输出解释成机器人控制目标。常见类型包括：

| Action 类型 | 含义 |
|---|---|
| `JointPositionActionCfg` | 输出关节位置目标或增量 |
| `JointVelocityActionCfg` | 输出关节速度目标 |
| `JointEffortActionCfg` | 输出关节力矩 |
| `DifferentialInverseKinematicsActionCfg` | 输出末端位姿增量，由 IK 转成关节目标 |
| `BinaryJointPositionActionCfg` | 夹爪开合这类二值动作 |

示意：

```python
@configclass
class ActionsCfg:
    arm_action = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["panda_joint.*"],
        scale=0.5,
    )
```

读 action 时要看动作维度、缩放系数和控制对象。许多“训练不稳定”其实来自动作尺度不合适，而不是算法本身。

## Reward

Reward Manager 把多个奖励项加权求和。每个 `RewTerm` 通常返回 `(num_envs,)`。

```python
@configclass
class RewardsCfg:
    reaching = RewTerm(func=mdp.position_command_error, weight=-1.0)
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-0.01)
```

读 reward 时按下面顺序检查：

| 检查点 | 解释 |
|---|---|
| 主任务奖励是什么？ | 例如到目标距离、速度跟踪误差、物体高度。 |
| 惩罚项是什么？ | 动作变化、关节速度、能耗、碰撞等。 |
| 权重大小是否合理？ | 后段目标奖励应能压过前段 shaping。 |
| 是否可能 reward hacking？ | 策略是否能钻规则漏洞拿高分。 |

## Termination

Termination Manager 判断一个环境是否结束。它通常返回两个概念：

- `terminated`：真正失败或成功，例如摔倒、出界、任务成功；
- `truncated`：因为时间上限结束，例如 `time_out=True`。

```python
@configclass
class TerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    # CartPole 用关节位置超限判断小车出界
    cart_out_of_bounds = DoneTerm(
        func=mdp.joint_pos_out_of_manual_limit,
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=["slider_to_cart"]), "bounds": (-3.0, 3.0)},
    )
```

这两个概念不能混用。RL 算法对“自然结束”和“被时间截断”的 bootstrap 处理不同。

## Event

Event Manager 负责启动、重置、周期触发的事件。典型模式：

| 模式 | 触发时机 | 例子 |
|---|---|---|
| `startup` | 仿真启动时 | 随机质量、摩擦、材质 |
| `reset` | 每个环境重置时 | 随机初始姿态、目标位置 |
| `interval` | 每隔一段时间 | 外力扰动、推机器人 |

示意：

```python
@configclass
class EventCfg:
    reset_robot = EventTerm(
        func=mdp.reset_joints_by_offset,
        mode="reset",
        params={"position_range": (-0.25, 0.25), "velocity_range": (-0.1, 0.1)},
    )
```

如果一个任务训练时表现很好、换个初始状态就失败，通常要回来看 event 和 domain randomization 是否太弱。

## 小结

- 读 Isaac Lab 任务时，先把代码放回 MDP 循环：状态、观测、动作、奖励、终止、重置。
- `InteractiveScene` 是状态载体，不是 Manager；它提供机器人、物体和传感器。
- Observation / Action / Reward / Termination / Event 分别对应策略输入、策略输出、评分、结束和重置。
- 下一页会把这些块扩展成完整 Manager 系统，再说明 Command、Curriculum、Recorder 等额外模块。

## 参考资料

- Isaac Lab Core Concepts. https://isaac-sim.github.io/IsaacLab/
- Gymnasium API. https://gymnasium.farama.org/

## 导航

- 返回目录：[任务结构与 Manager 系统](../02-reading-a-task.md)
- 下一页：[八大 Manager 系统](02-manager-system.md)
