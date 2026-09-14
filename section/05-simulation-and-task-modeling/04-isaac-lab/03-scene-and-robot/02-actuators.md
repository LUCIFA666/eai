# 执行器模型

上一页把机器人放进了 scene，但机器人不会因为存在就自然服从策略。策略输出只是一个动作张量，它必须经过 Action Manager 和 actuator，最后才会变成关节目标、关节速度或关节力矩。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么关节之外还要单独建模 actuator（执行器）？
2. implicit 和 explicit 执行器有什么区别，几种 ActuatorCfg 分别适合什么？
3. stiffness / damping 怎么理解，执行器又怎么和 ActionCfg 对接？

可以把这一层理解为：

```text
policy action -> ActionCfg 解释动作含义 -> actuator 计算/约束关节控制 -> PhysX 推进物理
```

## 为什么需要 actuator

真实机器人里的电机不是“给多少就有多少”。它有力矩上限、速度上限、控制带宽、摩擦、延迟、齿轮箱损耗。仿真里如果完全使用理想关节，策略可能学会真机做不到的动作。

| 现象 | 可能和 actuator 有关 |
|---|---|
| 机器人动作过猛、抖动 | `stiffness` 太高或动作尺度过大 |
| 机器人反应很慢 | `stiffness` 太低或 `damping` 太高 |
| 四足高速跑时突然失控 | 电机力矩-速度限制没有建模 |
| 夹爪夹不住物体 | 夹爪关节刚度或力矩限制太低 |
| 训练仿真很好，真机很差 | actuator 过于理想化，Sim2Real 差距大 |

因此，actuator 不是可有可无的参数表，而是策略动作和真实物理能力之间的接口。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-dexterous-hands.png" alt="Allegro Hand 和 Shadow Hand" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">灵巧手任务里，每根手指的关节通常要分组配置执行器。关节多、接触密、动作细，执行器参数会显著影响训练稳定性。</figcaption>
</figure>

## actuator 放在哪里

执行器通常写在 `ArticulationCfg` 里：

```python
from isaaclab.actuators import ImplicitActuatorCfg

robot = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Robot",
    spawn=sim_utils.UsdFileCfg(usd_path="path/to/robot.usd"),
    actuators={
        "arm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint.*"],
            stiffness=400.0,
            damping=80.0,
        ),
        "gripper": ImplicitActuatorCfg(
            joint_names_expr=["panda_finger.*"],
            stiffness=1e5,
            damping=1e3,
        ),
    },
)
```

这里有两个重要点：

- actuator 是按关节名分组的，不是按 body 分组；
- `joint_names_expr` 是正则表达式，必须能匹配到真实关节名。

不同组之间不要匹配到同一个关节，否则控制权会冲突。

## implicit 和 explicit

Isaac Lab 中常见执行器可以先分成两类：

| 类型 | 核心思想 | 代表配置 |
|---|---|---|
| Implicit | 把 PD 控制交给 PhysX 内部求解 | `ImplicitActuatorCfg` |
| Explicit | Isaac Lab 在物理步前计算力矩，再写入仿真 | `IdealPDActuatorCfg`、`DCMotorCfg`、`ActuatorNet*Cfg` |

Implicit 简单、快、适合快速原型；explicit 能加入更真实的力矩限制、电机曲线和学习型模型，适合更接近真机的任务。

## ImplicitActuatorCfg

`ImplicitActuatorCfg` 使用 PhysX 内置 drive。它通常用于机械臂、夹爪和入门任务。

```python
from isaaclab.actuators import ImplicitActuatorCfg

arm = ImplicitActuatorCfg(
    joint_names_expr=["panda_joint.*"],
    stiffness=400.0,
    damping=80.0,
)
```

可以把它近似理解为 PD 控制：

```text
torque = stiffness * position_error + damping * velocity_error
```

在实际实现中，implicit drive 由物理求解器内部处理。优点是稳定、简单；缺点是对真实电机的力矩-速度曲线、延迟和传动非线性表达有限。

## IdealPDActuatorCfg

`IdealPDActuatorCfg` 在 Isaac Lab 侧计算 PD 力矩，并加入力矩 / 速度限制。

```python
from isaaclab.actuators import IdealPDActuatorCfg

legs = IdealPDActuatorCfg(
    joint_names_expr=[".*_hip_joint", ".*_thigh_joint", ".*_calf_joint"],
    effort_limit=33.5,
    velocity_limit=21.0,
    stiffness=25.0,
    damping=0.5,
)
```

它比 implicit 更适合需要明确电机上限的任务。四足、轮足、人形这类运动任务通常不能只依赖“无限强”的理想关节。

## DCMotorCfg

直流电机高速旋转时，可用力矩会下降。`DCMotorCfg` 用简单模型表达这种关系。

```python
from isaaclab.actuators import DCMotorCfg

motor = DCMotorCfg(
    joint_names_expr=[".*"],
    saturation_effort=120.0,
    effort_limit=80.0,
    velocity_limit=7.5,
    stiffness=40.0,
    damping=5.0,
)
```

关键字段：

| 字段 | 含义 |
|---|---|
| `saturation_effort` | 低速或堵转附近可达到的最大力矩 |
| `effort_limit` | 额定力矩限制 |
| `velocity_limit` | 最大速度限制 |
| `stiffness` / `damping` | 位置控制的比例和阻尼参数 |

对于腿式机器人，`DCMotorCfg` 往往比理想 PD 更接近真实执行能力。

## ActuatorNet

如果有真机数据，可以训练一个执行器网络来拟合真实电机响应。Isaac Lab 支持 MLP 和 LSTM 风格的 actuator net。

```python
from isaaclab.actuators import ActuatorNetMLPCfg

actuator = ActuatorNetMLPCfg(
    joint_names_expr=[".*"],
    network_file="path/to/actuator_net.pt",
    pos_scale=-1.0,
    vel_scale=1.0,
    torque_scale=1.0,
    input_order="pos_vel",
    input_idx=(0, 2, 4),  # 网络输入取的历史帧索引
)
```

它适合有真机电机日志的项目。课程前期不要求使用 actuator net，但需要知道它解决的是“理想仿真电机和真实电机不一致”的问题。

## stiffness 和 damping 怎么理解

`stiffness` 控制“偏离目标时拉回来的劲”，`damping` 控制“运动过程中的阻尼”。

| 参数 | 太高 | 太低 |
|---|---|---|
| `stiffness` | 抖动、冲击大、接触不稳定 | 跟踪慢、动作软、够不到目标 |
| `damping` | 动作迟缓、像被拖住 | 震荡、过冲、停不住 |

常见经验值不是绝对规则，但能帮助定位量级：

| 机器人部位 | 参数倾向 |
|---|---|
| 固定机械臂 | 较高 stiffness，中高 damping |
| 四足腿部 | 中低 stiffness，低到中等 damping |
| 夹爪 | 很高 stiffness 和 damping |
| 灵巧手 | 分关节细调，避免手指接触时抖动 |

调 actuator 时不要只看机器人是否“能动”，还要看动作是否平滑、是否频繁撞限位、是否出现非物理抖动。

## 执行器分组

复杂机器人通常不能所有关节用一套参数。可以按关节类型分组：

```python
actuators = {
    "hip": DCMotorCfg(
        joint_names_expr=[".*_hip_joint"],
        saturation_effort=120.0,
        effort_limit=80.0,
        velocity_limit=7.5,
        stiffness=40.0,
        damping=5.0,
    ),
    "knee": IdealPDActuatorCfg(
        joint_names_expr=[".*_thigh_joint", ".*_calf_joint"],
        effort_limit=33.5,
        velocity_limit=21.0,
        stiffness=25.0,
        damping=0.5,
    ),
}
```

分组的意义不是让配置变复杂，而是表达机器人真实结构：髋关节、膝关节、夹爪、手指使用的电机不同，控制能力也不同。

## 和 ActionCfg 的关系

Action Manager 决定策略输出的含义，actuator 决定关节如何追踪这个目标。

```python
@configclass
class ActionsCfg:
    arm_action = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["panda_joint.*"],
        scale=0.5,
    )
```

这里 `ActionCfg` 把策略输出解释为关节位置目标；随后 actuator 用自己的 `stiffness`、`damping`、力矩限制去追踪这个目标。

因此，动作尺度和执行器参数要一起看：

```text
策略输出太大 + stiffness 太高 -> 冲击和抖动
策略输出太小 + stiffness 太低 -> 机器人几乎不动
动作合理 + actuator 限制合理 -> 训练更稳定
```

## 选择规则

| 场景 | 建议 |
|---|---|
| 先跑通机械臂或简单任务 | `ImplicitActuatorCfg` |
| 需要显式力矩限制 | `IdealPDActuatorCfg` |
| 四足、人形、轮足等运动任务 | `DCMotorCfg` 或更真实的执行器 |
| 有真机电机数据 | `ActuatorNetMLPCfg` / `ActuatorNetLSTMCfg` |
| 不确定是否匹配关节 | 先打印 `robot.data.joint_names` |

## 小结

- actuator 是策略动作和物理关节之间的接口。
- `ImplicitActuatorCfg` 简单稳定，适合作为起点；explicit actuator 能表达更多真实电机限制。
- `stiffness` 管跟踪力度，`damping` 管阻尼；两者会直接影响训练稳定性。
- 执行器要按关节名分组，`joint_names_expr` 必须和真实关节名匹配。
- Action Manager 决定动作含义，actuator 决定关节如何实现这个动作。

## 参考资料

- Isaac Lab Actuator Models. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab Actuators API. `source/isaaclab/isaaclab/actuators/`
- Hwangbo et al., "Learning agile and dynamic motor skills for legged robots", Science Robotics, 2019.

## 导航

- 上一页：[场景与资产配置](01-scene-and-assets.md)
- 返回目录：[场景与机器人资产](../03-scene-and-robot.md)
- 下一页：[自定义机器人资产](03-custom-robot.md)
