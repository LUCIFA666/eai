# 拆解 reach 任务

Reach 是最基础的机械臂操作任务：给定一个目标位姿，让机械臂末端执行器移动过去。它比 CartPole 更接近机器人任务，又比 lift、stack、cabinet 简单，适合作为第一个 Manager-based 操作任务样本。

本页以 Isaac Lab 2.3.2 中的 `Isaac-Reach-Franka-v0` 为主线。这个任务的默认版本使用关节位置动作；IK 和 OSC 是另外注册的任务 ID，不要把几个变体混成同一个配置来读。

## 本节目标

本节围绕下面几个问题展开：

1. 以 reach 任务为例，怎么从任务注册入口一路读到各配置块？
2. 它的 Scene、Command、Observation、Action、Reward 具体是怎么配的？
3. 读完能不能总结出一条可复用的「最小阅读路线」？

<figure class="doc-figure">
<video src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-task-reach-franka.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.5em 0"></video>
<figcaption class="doc-figure-subtitle">Franka reach：绿色目标点由命令系统生成，策略控制机械臂末端靠近目标。</figcaption>
</figure>

## 任务一句话

```text
任务目标是让 Franka 末端执行器到达随机采样的目标位姿。
观测：关节状态 + 目标命令 + 上一步动作等。
动作：默认是关节位置目标；IK / OSC 变体另有任务 ID。
奖励：末端位置误差、姿态误差、细粒度接近奖励，以及动作变化和关节速度惩罚。
终止：通常以时间上限为主。
```

这句话就是读源码前的“任务卡”。之后所有代码都应该能放回这张卡里。

## 找任务注册入口

Isaac Lab 任务通常先在 `__init__.py` 中注册成 Gymnasium ID。典型结构如下：

```python
gym.register(
    id="Isaac-Reach-Franka-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": "isaaclab_tasks.manager_based.manipulation.reach.config.franka.joint_pos_env_cfg:FrankaReachEnvCfg",
        "rl_games_cfg_entry_point": "isaaclab_tasks.manager_based.manipulation.reach.config.franka.agents:rl_games_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": "isaaclab_tasks.manager_based.manipulation.reach.config.franka.agents.rsl_rl_ppo_cfg:FrankaReachPPORunnerCfg",
        "skrl_cfg_entry_point": "isaaclab_tasks.manager_based.manipulation.reach.config.franka.agents:skrl_ppo_cfg.yaml",
    },
)
```

读这一段要抓三件事：

| 字段 | 含义 |
|---|---|
| `id` | 训练命令里 `--task` 使用的名字 |
| `entry_point` | 这个任务走 Manager-based 还是 Direct |
| `env_cfg_entry_point` | 真正的环境配置类从哪里来 |

一旦找到 `env_cfg_entry_point`，就能顺着进入任务主体。

## 看 env cfg

Manager-based reach 任务的配置通常可以拆成：

```python
@configclass
class FrankaReachEnvCfg(ManagerBasedRLEnvCfg):
    scene = FrankaReachSceneCfg()
    observations = ObservationsCfg()
    actions = ActionsCfg()
    commands = CommandsCfg()
    rewards = RewardsCfg()
    terminations = TerminationsCfg()
    events = EventCfg()
    curriculum = CurriculumCfg()
```

读的时候不要急着看函数实现，先确认这些块是否齐全。

| 配置块 | 在 reach 里回答什么问题 |
|---|---|
| `scene` | 机械臂、地面、桌子和灯光在哪里 |
| `commands` | 目标末端位姿如何随机生成 |
| `observations` | 策略能看到哪些关节状态和目标信息 |
| `actions` | 策略输出如何变成关节或末端控制 |
| `rewards` | 末端到目标的误差如何变成训练信号 |
| `terminations` | 什么时候结束一个 episode |
| `events` | reset 时机器人和目标如何重置 |
| `curriculum` | 训练若干步之后是否调整惩罚权重 |

## 看 Scene

Reach 的 scene 至少要有机器人、地面、桌子和灯光。机器人是真实参与物理的 `Articulation`；目标位姿由 Command Manager 维护，`debug_vis=True` 时会显示可视化标记。

```python
@configclass
class FrankaReachSceneCfg(InteractiveSceneCfg):
    robot = FRANKA_PANDA_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
    ground = AssetBaseCfg(prim_path="/World/ground")
    table = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Table")
    light = AssetBaseCfg(prim_path="/World/light")
```

这里最重要的是 `prim_path="{ENV_REGEX_NS}/Robot"`。它说明每个并行环境都有自己的机器人副本，而不是所有环境共用一个机器人。

## 看 Command

Reach 的目标不是固定点，而是每隔一段时间重新采样。Command Manager 负责生成目标位姿，并把目标提供给 observation 和 reward。

```python
@configclass
class CommandsCfg:
    ee_pose = mdp.UniformPoseCommandCfg(
        asset_name="robot",
        body_name="panda_hand",
        resampling_time_range=(4.0, 4.0),
        debug_vis=True,
        ranges=mdp.UniformPoseCommandCfg.Ranges(
            pos_x=(0.35, 0.65),
            pos_y=(-0.2, 0.2),
            pos_z=(0.15, 0.5),
            roll=(0.0, 0.0),
            pitch=(3.14159, 3.14159),
            yaw=(-3.14, 3.14),
        ),
    )
```

读 command 时要看：

- 目标绑定到哪个机器人和 body；
- 多久重采样一次；
- 目标位置和姿态范围多大；
- 是否打开 `debug_vis`，方便在 GUI 里看到目标。

## 看 Observation

Reach 如果不把目标放进 observation，策略就不知道该往哪里动。

```python
@configclass
class ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        joint_pos = ObsTerm(func=mdp.joint_pos_rel, noise=Unoise(n_min=-0.01, n_max=0.01))
        joint_vel = ObsTerm(func=mdp.joint_vel_rel, noise=Unoise(n_min=-0.01, n_max=0.01))
        pose_command = ObsTerm(func=mdp.generated_commands, params={"command_name": "ee_pose"})
        actions = ObsTerm(func=mdp.last_action)

        def __post_init__(self):
            self.enable_corruption = True
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()
```

这一块回答的是“策略看见什么”。如果任务表现异常，先确认 observation 里是否真的包含目标，以及目标是在机器人坐标系还是世界坐标系表达。

## 看 Action

`Isaac-Reach-Franka-v0` 默认使用关节位置动作。IK 和 OSC 不是在同一个任务里偷偷切换，而是注册成独立任务，例如 `Isaac-Reach-Franka-IK-Rel-v0` 和 `Isaac-Reach-Franka-OSC-v0`。初学时先看动作配置的三个信息：

| 信息 | 要看什么 |
|---|---|
| 控制对象 | 是整条机械臂、夹爪，还是某几个关节 |
| 动作含义 | 关节位置、关节速度、力矩，还是末端位姿增量 |
| 缩放 | `scale` 是否过大或过小 |

示意：

```python
@configclass
class ActionsCfg:
    arm_action = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["panda_joint.*"],
        scale=0.5,
        use_default_offset=True,
    )
```

如果进入 IK 变体，`ActionsCfg` 会换成 `DifferentialInverseKinematicsActionCfg`，策略输出更接近末端运动命令，底层由 IK 转成关节目标。

## 看 Reward

Reach 的主奖励围绕末端到目标的距离和姿态误差。2.3.2 的默认配置不是只有一个距离项，而是把粗粒度位置误差、细粒度接近项、姿态误差和动作惩罚拆开：

```python
@configclass
class RewardsCfg:
    end_effector_position_tracking = RewTerm(
        func=mdp.position_command_error,
        weight=-0.2,
        params={"command_name": "ee_pose", "asset_cfg": SceneEntityCfg("robot", body_names="panda_hand")},
    )
    end_effector_position_tracking_fine_grained = RewTerm(
        func=mdp.position_command_error_tanh,
        weight=0.1,
        params={"command_name": "ee_pose", "std": 0.1, "asset_cfg": SceneEntityCfg("robot", body_names="panda_hand")},
    )
    end_effector_orientation_tracking = RewTerm(
        func=mdp.orientation_command_error,
        weight=-0.1,
        params={"command_name": "ee_pose", "asset_cfg": SceneEntityCfg("robot", body_names="panda_hand")},
    )
    joint_vel = RewTerm(func=mdp.joint_vel_l2, weight=-0.0001, params={"asset_cfg": SceneEntityCfg("robot")})
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-0.0001)
```

读 reward 时要注意：

- 距离项通常是负权重，距离越小惩罚越小；
- tanh 接近项用于给目标附近更细的正反馈；
- 姿态项说明 reach 不是只管末端位置，也可能管末端朝向；
- 动作变化惩罚让控制更平滑；
- `SceneEntityCfg` 用 body 名称解析索引，避免硬编码 body id。

Reach 任务的奖励不复杂，但也不是一句“距离越近越好”就结束。它适合练习“从函数名、权重和参数推断训练意图”。

## 看 Termination 和 Event

Reach 这类入门任务通常主要靠 time-out 结束：

```python
@configclass
class TerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
```

Event 负责 reset 时让机器人回到初始附近。目标重采样由 Command Manager 按 `resampling_time_range` 处理。读 event 时关注初始状态分布：如果 reset 分布太窄，训练会很快但泛化差；如果一开始太宽，策略可能学不起来。

## 看 Curriculum

Reach 默认配置还会在训练若干步后调大动作变化和关节速度惩罚：

```python
@configclass
class CurriculumCfg:
    action_rate = CurrTerm(
        func=mdp.modify_reward_weight,
        params={"term_name": "action_rate", "weight": -0.005, "num_steps": 4500},
    )
    joint_vel = CurrTerm(
        func=mdp.modify_reward_weight,
        params={"term_name": "joint_vel", "weight": -0.001, "num_steps": 4500},
    )
```

这一步容易被漏掉。只看初始 `RewardsCfg`，会误以为整个训练过程中奖励权重都不变。

## 最小阅读路线

读 reach 源码时可以按下面清单打勾：

```text
[ ] 任务 ID 是什么？入口是 ManagerBasedRLEnv 还是 DirectRLEnv？
[ ] env_cfg_entry_point 指向哪个配置类？
[ ] scene 中机器人和目标在哪里声明？
[ ] command 如何生成目标？
[ ] observation 是否包含目标和机器人状态？
[ ] action 是关节空间还是任务空间？
[ ] reward 主项是什么？惩罚项是什么？
[ ] termination 只有超时，还是有成功/失败条件？
[ ] curriculum 是否会在训练中修改奖励权重？
[ ] agent 配置使用哪个 RL 库和多少迭代？
```

## 小结

- Reach 是读 Isaac Lab 操作任务的好入口：有真实机器人、目标命令、观测、动作、奖励和 curriculum，但还没有复杂物体交互。
- 读任务先找 `gym.register`，再顺着 `env_cfg_entry_point` 进入配置主体。
- Command 生成目标，Observation 让策略看到目标，Action 定义控制接口，Reward 衡量末端是否接近目标并约束动作。
- `SceneEntityCfg` 按名字解析 body / joint，是读写机器人状态时的重要习惯。

## 参考资料

- Isaac Lab Available Environments. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab Task Source Code. `source/isaaclab_tasks/isaaclab_tasks/`

## 导航

- 上一页：[八大 Manager 系统](02-manager-system.md)
- 返回目录：[任务结构与 Manager 系统](../02-reading-a-task.md)
- 下一页：[Manager-based vs Direct](04-manager-based-vs-direct.md)
