# 八大 Manager 系统

上一页把任务拆成 scene、observation、action、reward、termination、event。本页再补齐 Command、Curriculum、Recorder，并区分 `ManagerBasedEnv` 和 `ManagerBasedRLEnv`。

## 本节目标

本节围绕下面几个问题展开：

1. Isaac Lab 的八大 Manager 分别是哪些，各管一段什么逻辑？
2. ManagerBasedEnv 和 ManagerBasedRLEnv 有什么区别？
3. 这些 Manager 在一次 step 里按什么顺序被调用？

## Manager 全景

| 模块 | 是否属于 Manager | 主要职责 | 常见配置 |
|---|---|---|---|
| Scene | 否 | 机器人、物体、地面、传感器、环境克隆 | `InteractiveSceneCfg` |
| Observation | 是 | 拼装策略输入 | `ObservationsCfg` |
| Action | 是 | 把策略输出映射到执行器目标 | `ActionsCfg` |
| Reward | 是 | 计算并加权汇总奖励 | `RewardsCfg` |
| Termination | 是 | 判断成功、失败、超时 | `TerminationsCfg` |
| Event | 是 | 启动、重置、周期事件和随机化 | `EventCfg` |
| Command | 是 | 生成目标速度、目标位姿等命令 | `CommandsCfg` |
| Curriculum | 是 | 随训练进度调难度或奖励权重 | `CurriculumCfg` |
| Recorder | 是 | 记录轨迹、状态和动作到数据集 | `RecorderCfg` |

严格说是“八大 Manager + Scene”。Scene 是舞台，Manager 是规则系统。

## ManagerBasedEnv 和 ManagerBasedRLEnv

不是所有环境都用于 RL。Isaac Lab 里有两个层次：

| 能力 | `ManagerBasedEnv` | `ManagerBasedRLEnv` |
|---|:---:|:---:|
| Scene | 是 | 是 |
| Observation | 是 | 是 |
| Action | 是 | 是 |
| Event | 是 | 是 |
| Recorder | 可用 | 可用 |
| Reward | 否 | 是 |
| Termination | 否 | 是 |
| Command | 否 | 是 |
| Curriculum | 否 | 是 |

`ManagerBasedEnv` 适合遥操作、数据采集、控制器测试；`ManagerBasedRLEnv` 才是标准 RL 训练环境。

## Observation Manager

Observation Manager 决定策略看到什么。它可以分组，例如 `policy` 给 actor，`critic` 给 value function。

```python
@configclass
class ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        actions = ObsTerm(func=mdp.last_action)

    policy: PolicyCfg = PolicyCfg()
```

读 observation 时重点看：是否含目标、是否含上一动作、是否加噪声、是否裁剪、是否有 privileged critic 观测。

## Action Manager

Action Manager 决定策略输出如何下发。它处理动作缩放、裁剪和控制目标。

```python
@configclass
class ActionsCfg:
    joint_pos = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=[".*"],
        scale=0.5,
    )
```

如果策略动作很小却机器人动得很猛，或动作很大却几乎不动，优先检查 action scale、joint name 和 actuator 配置。

## Reward Manager

Reward Manager 把多个 `RewTerm` 加权求和。一个常见误区是只看 reward 总值，不看分项。RSL-RL 日志里的 `Episode_Reward/...` 就是分项反馈。

```python
@configclass
class RewardsCfg:
    alive = RewTerm(func=mdp.is_alive, weight=1.0)
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-0.01)
```

读 reward 时要问：主任务项是什么，稳定性惩罚是什么，是否存在“只拿 shaping 不完成任务”的漏洞。

## Termination Manager

Termination Manager 判断回合结束。典型项包括：

- `time_out`：达到最大回合长度；
- `out_of_bounds`：小车、机器人或物体出界；
- `root_height_below_minimum`：机器人摔倒；
- `success`：任务达成。

`time_out=True` 的项表示 truncated，不等同于失败。CartPole 训练结束时 `Episode_Termination/time_out: 1.0000` 是好信号，说明大多数 episode 撑到了时间上限。

## Event Manager

Event Manager 管 reset 和随机化。它对训练泛化很重要。

```python
@configclass
class EventCfg:
    randomize_mass = EventTerm(
        func=mdp.randomize_rigid_body_mass,
        mode="startup",
        params={"mass_distribution_params": (0.8, 1.2), "operation": "scale"},
    )
```

三种常见模式：

| 模式 | 触发时机 | 用途 |
|---|---|---|
| `startup` | 仿真启动时 | 固定一轮实验的物理随机化 |
| `reset` | 环境重置时 | 随机初始状态、目标、物体位姿 |
| `interval` | 间隔触发 | 推机器人、施加扰动 |

## Command Manager

Command Manager 负责“目标”。目标速度、目标末端位姿、目标朝向都可以由它生成和重采样。

```python
@configclass
class CommandsCfg:
    base_velocity = mdp.UniformVelocityCommandCfg(
        asset_name="robot",
        resampling_time_range=(10.0, 10.0),
        ranges=mdp.UniformVelocityCommandCfg.Ranges(
            lin_vel_x=(-1.0, 1.0),
            lin_vel_y=(-1.0, 1.0),
            ang_vel_z=(-1.0, 1.0),
        ),
    )
```

Command 通常会同时进入 observation 和 reward：策略要看到目标，奖励要衡量是否跟踪目标。

## Curriculum Manager

Curriculum Manager 负责逐步增加难度。常见方式包括：

- 地形从平地逐渐变粗糙；
- 速度命令范围逐步扩大；
- 目标位置范围逐渐变远；
- 奖励权重随训练阶段调整。

课程学习的核心思想是：不要一开始就把最难分布扔给策略，而是让策略从能学会的分布开始。

## Recorder Manager

Recorder Manager 把轨迹写成数据集。它常用于遥操作、脚本策略采集、模仿学习数据生成。

典型记录内容包括：

- 每一步 observation；
- 每一步 action；
- reset 前后的状态；
- success / failure 标记；
- 任务元数据和环境配置。

后面的模仿学习与数据采集会继续使用这个概念。

## 小结

- Scene 是舞台，Manager 是规则系统。
- `ManagerBasedEnv` 可用于控制和数据采集；`ManagerBasedRLEnv` 增加 reward、termination、command、curriculum，用于 RL。
- Observation、Action、Reward、Termination、Event 是读任务的核心五块。
- Command 负责目标，Curriculum 负责难度，Recorder 负责数据落盘。

## 参考资料

- Isaac Lab Managers API. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab Tutorials: Manager-based environments. https://isaac-sim.github.io/IsaacLab/

## 导航

- 上一页：[任务由什么组成](01-env-anatomy.md)
- 返回目录：[任务结构与 Manager 系统](../02-reading-a-task.md)
- 下一页：[拆解 reach 任务](03-walkthrough-reach.md)
