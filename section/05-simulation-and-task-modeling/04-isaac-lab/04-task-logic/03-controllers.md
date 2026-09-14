# 动作与控制器

前两页讲策略能看到什么。本页讲策略能做什么。动作设计决定了策略输出的维度、物理含义和学习难度。

## 本节目标

本节围绕下面几个问题展开：

1. 策略输出怎么被 Action Manager 解释成控制命令？
2. 关节空间动作、差分 IK、OSC 各适合什么任务？
3. 动作尺度 `scale` 为什么要和 actuator 参数一起调？
4. 为什么坐标系（基座 / 环境局部）是控制器的常见坑？

## 术语速查

进入正文前，先把本节的动作 / 控制器术语对齐（`XxxCfg` 是配置容器）。

| 术语 | 中文名 | 一句话含义 |
|---|---|---|
| action | 动作 | 策略每步输出、作用到机器人的量 |
| Action Manager / `ActionsCfg` | 动作管理器 / 动作配置 | 把策略输出解释成关节目标或末端命令 |
| joint-space action | 关节空间动作 | 直接控制各关节的位置 / 速度 / 力矩 |
| `BinaryJointPositionActionCfg` | 二值关节动作配置 | 开 / 合两态，常用于夹爪 |
| Differential IK | 差分逆运动学 | 把末端位姿增量转成关节目标 |
| IK | 逆运动学 | 由末端目标反解关节角 |
| Jacobian | 雅可比矩阵 | 关节速度到末端速度的映射 |
| DLS（`dls`）/ `lambda` | 阻尼最小二乘 / 阻尼系数 | 带阻尼项的稳定 IK 解法，`lambda` 越大越平滑 |
| OSC | 操作空间控制 | 在任务空间算力再映射到关节力矩，适合力控 |
| scale | 动作尺度 | 策略输出放大到物理动作的比例 |
| actuator | 执行器 | 关节驱动模型，含 stiffness / damping 等参数 |
| `env_origin(s)` | 环境原点 | 每个并行环境在世界中的偏移原点 |

## 动作不等于电机力矩

策略输出通常是一个无量纲张量，例如 `[-1, 1]` 范围内的数。Action Manager 会把它解释成关节位置目标、关节速度、力矩，或末端位姿增量。

```text
policy output
  -> ActionCfg 解释动作语义和 scale
  -> controller / actuator 计算关节目标或力矩
  -> PhysX 推进物理
```

动作设计不合理时，奖励写得再好也可能学不起来。

## 关节空间动作

最直接的动作是关节空间控制。

```python
@configclass
class ActionsCfg:
    arm_action = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["panda_joint.*"],
        scale=0.5,
    )
```

常见类型：

| 动作类型 | 含义 | 常见场景 |
|---|---|---|
| `JointPositionActionCfg` | 输出关节位置目标或增量 | 机械臂、四足 |
| `JointVelocityActionCfg` | 输出关节速度目标 | 速度控制实验 |
| `JointEffortActionCfg` | 输出关节力矩 | 低层控制、研究任务 |
| `BinaryJointPositionActionCfg` | 二值开合 | 夹爪 |

关节空间动作保留了机器人全部自由度，但对操作任务不够直观。策略需要自己学会“关节怎么动才能让手到目标点”。

<video src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-task-go2-rough.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

四足运动任务通常采用关节空间动作。策略输出不是“向前走”这个语义命令，而是一组关节目标；机器人能否走稳，取决于动作尺度、执行器参数、奖励项和终止条件是否共同约束出了合理步态。

## 动作尺度 scale

`scale` 控制策略输出到物理动作的放大比例。

```text
target = default_joint_pos + scale * policy_action
```

如果 `scale` 太大，动作会猛烈、抖动、撞限位；如果太小，机器人几乎不动，奖励变化很弱。动作尺度要和上一部分的 actuator 参数一起看。

## 差分 IK

机械臂操作任务里，策略直接输出末端增量有时比直接输出每个关节目标更容易探索。`DifferentialInverseKinematicsActionCfg` 会把末端位姿增量转成关节目标，但它同时要求 body 名、关节名、坐标系和 IK 参数都对齐。

在 Isaac Lab 2.3.2 的 reach 系列里，`Isaac-Reach-Franka-v0` 默认是关节位置动作；`Isaac-Reach-Franka-IK-Rel-v0` 才是相对差分 IK 动作。读源码时先看 task id，不要只凭任务名称判断控制方式。

```python
from isaaclab.controllers import DifferentialIKControllerCfg
from isaaclab.envs.mdp.actions.actions_cfg import DifferentialInverseKinematicsActionCfg

@configclass
class ActionsCfg:
    arm_action = DifferentialInverseKinematicsActionCfg(
        asset_name="robot",
        joint_names=["panda_joint.*"],
        body_name="panda_hand",
        scale=0.5,
        controller=DifferentialIKControllerCfg(
            command_type="pose",
            use_relative_mode=True,
            ik_method="dls",
        ),
        body_offset=DifferentialInverseKinematicsActionCfg.OffsetCfg(pos=[0.0, 0.0, 0.107]),
    )
```

Reach 只需要控制手腕末端靠近目标，通常不需要夹爪动作。到了 lift、pick-and-place 这类任务，才会再加 `BinaryJointPositionActionCfg` 这类开合夹爪的动作项。

这类动作的直觉是：

```text
策略输出：末端往 x/y/z 方向移动一点，姿态旋转一点
IK 控制器：计算需要哪些关节一起动
执行器：让关节追踪目标
```

Reach、Lift、Pick-and-Place 这类机械臂操作任务经常会提供 IK 变体。它不一定比关节空间动作“总是更好”，但能把探索空间从关节协同问题改成末端运动问题，适合作为操作任务入门路线。

<video src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-task-reach-franka.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

Reach 任务里，差分 IK 把“末端向目标移动一点”转换成多关节协同运动。这个视频适合放在控制器页，因为它展示的不是训练库差异，而是动作语义从策略输出到机器人运动的转换。

## IK 的关键点

差分 IK 依赖 Jacobian。常见求解方法是阻尼最小二乘：

```text
q_dot = J^T (J J^T + lambda^2 I)^(-1) x_dot
```

`lambda` 越大，解越平滑，但跟踪精度下降；`lambda` 太小，在奇异位形附近容易跳变。

使用 ActionCfg 时，框架会处理很多索引细节；手写控制器时，要确保末端 body、关节索引和 Jacobian 切片一致。

## 坐标系是控制器的常见坑

并行环境共用世界坐标系，但每个环境有自己的 `env_origin`。末端控制通常要在机器人基座坐标系或环境局部坐标系里计算。

```python
from isaaclab.utils.math import subtract_frame_transforms

ee_pos_b, ee_quat_b = subtract_frame_transforms(
    robot.data.root_pos_w,
    robot.data.root_quat_w,
    robot.data.body_pos_w[:, ee_body_id],
    robot.data.body_quat_w[:, ee_body_id],
)
```

固定基座机械臂看起来可以直接用世界坐标，但一旦并行环境有不同原点，或机器人基座有旋转，坐标系错误就会让动作方向变得不可解释。

## OSC

Operational Space Control 直接在任务空间计算力，再映射成关节力矩。它适合力控和接触丰富任务。

```python
from isaaclab.controllers import OperationalSpaceControllerCfg
from isaaclab.envs.mdp.actions.actions_cfg import OperationalSpaceControllerActionCfg

arm_action = OperationalSpaceControllerActionCfg(
    asset_name="robot",
    joint_names=["panda_joint.*"],
    body_name="panda_hand",
    controller_cfg=OperationalSpaceControllerCfg(
        target_types=["pose_abs"],
        impedance_mode="variable_kp",
        inertial_dynamics_decoupling=True,
        partial_inertial_dynamics_decoupling=False,
        gravity_compensation=False,
        motion_stiffness_task=100.0,
        motion_damping_ratio_task=1.0,
        motion_stiffness_limits_task=(50.0, 200.0),
        nullspace_control="position",
    ),
    nullspace_joint_pos_target="center",
    position_scale=1.0,
    orientation_scale=1.0,
    stiffness_scale=100.0,
)
```

可以把它理解成：

```text
策略给末端绝对位姿目标，OSC 在操作空间生成关节力矩，并用可变刚度调节跟踪
```

擦拭、推门、插接、装配等任务可能需要 OSC 或带力控目标的 OSC 配置。普通 RL 操作入门任务先用关节位置或差分 IK 更合适。

## 选择规则

| 场景 | 推荐动作 |
|---|---|
| 四足 / 人形运动 | 关节空间动作 |
| 固定机械臂 reach | 差分 IK |
| 抓取、搬运、放置 | 差分 IK + 夹爪二值动作 |
| 力控装配、擦拭 | OSC |
| 研究底层控制 | 关节力矩动作 |

## 调试清单

```text
[ ] action_dim 是否和预期一致？
[ ] joint_names 是否匹配真实关节？
[ ] scale 是否过大或过小？
[ ] 差分 IK 的 body_name 是否是正确末端？
[ ] 坐标系是否统一到基座或环境局部？
[ ] actuator 的 stiffness/damping 是否和动作尺度匹配？
```

## 小结

- ActionCfg 定义策略输出的物理含义，不只是动作维度。
- 默认 Reach、IK Reach、OSC Reach 是不同任务变体，读源码时先确认 task id。
- 关节空间动作通用，差分 IK 常用于机械臂操作，OSC 适合力控接触任务。
- 动作尺度、坐标系和 actuator 参数必须一起调。

## 参考资料

- Isaac Lab Controllers. https://isaac-sim.github.io/IsaacLab/
- Tutorial: `scripts/tutorials/05_controllers/run_diff_ik.py`
- Tutorial: `scripts/tutorials/05_controllers/run_osc.py`

## 导航

- 上一页：[传感器](02-sensors.md)
- 返回目录：[任务逻辑配置](../04-task-logic.md)
- 下一页：[奖励工程](04-reward.md)
