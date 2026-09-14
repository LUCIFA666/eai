# 域随机化

训练环境如果永远只有一种质量、一种摩擦、一种初始姿态，策略很容易过拟合到这一个仿真世界。域随机化就是在训练中主动制造变化，让策略学会对一族环境都有效。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-domain-randomization-map.svg" alt="域随机化覆盖物理、初始状态、扰动、观测和视觉" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">域随机化不是单个开关，而是一组覆盖物理、reset、扰动、观测和视觉外观的训练分布设计。</figcaption>
</figure>

## 本节目标

本节围绕下面几个问题展开：

1. 域随机化为什么能提升泛化，随机化哪几类（物理 / 初始 / 扰动 / 观测 / 视觉）？
2. 怎么用 Event System（startup / reset / interval）随机化物理和初始状态？
3. 观测噪声和视觉随机化分别怎么写、什么时候重要？
4. 随机化范围怎么选，怎么和课程学习配合？

## 随机化什么

| 类别 | 例子 | 目的 |
|---|---|---|
| 物理参数 | 质量、摩擦、关节阻尼、执行器增益 | 缩小 Sim2Real 差距 |
| 初始状态 | 机器人姿态、物体位置、目标位置 | 提升任务泛化 |
| 外部扰动 | 推机器人、施加外力 | 提升鲁棒性 |
| 观测噪声 | 关节角、速度、相机噪声 | 模拟传感器误差 |
| 视觉外观 | 光照、颜色、纹理、背景 | 视觉策略泛化 |

随机化不是越多越好。范围过大时，策略初期可能完全学不到稳定行为。

## Event System

大多数随机化通过 `EventCfg` 写：

```python
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass
from isaaclab.envs import mdp

@configclass
class EventCfg:
    randomize_mass = EventTerm(
        func=mdp.randomize_rigid_body_mass,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "mass_distribution_params": (0.8, 1.2),
            "operation": "scale",
        },
    )
```

四种常见触发模式：

| 模式 | 触发时机 | 典型用途 |
|---|---|---|
| `prestartup` | 仿真开始前 | USD / 材质层面的修改 |
| `startup` | 仿真创建后一次 | 质量、摩擦、执行器参数 |
| `reset` | 每个 episode 重置时 | 初始姿态、目标位置 |
| `interval` | 运行中按时间间隔触发 | 推力、周期扰动 |

## reset 随机化

```python
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.envs import mdp

reset_robot_joints = EventTerm(
    func=mdp.reset_joints_by_offset,
    mode="reset",
    params={
        "asset_cfg": SceneEntityCfg("robot"),
        "position_range": (-0.25, 0.25),
        "velocity_range": (-0.1, 0.1),
    },
)
```

reset 随机化会影响初期学习难度。范围太窄，策略泛化差；范围太宽，初期没有梯度。

## 外部扰动

```python
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.envs import mdp

push_robot = EventTerm(
    func=mdp.push_by_setting_velocity,
    mode="interval",
    interval_range_s=(5.0, 10.0),
    params={
        "asset_cfg": SceneEntityCfg("robot"),
        "velocity_range": {"x": (-1.0, 1.0), "y": (-1.0, 1.0)},
    },
)
```

四足和人形常用 push 训练抗扰动能力。机械臂操作任务通常更关注物体初始位姿、摩擦和视觉变化。

## 观测噪声

观测噪声通常直接写在 `ObsTerm` 上：

```python
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.utils.noise import UniformNoiseCfg
from isaaclab.envs import mdp

joint_pos = ObsTerm(
    func=mdp.joint_pos_rel,
    noise=UniformNoiseCfg(n_min=-0.01, n_max=0.01),
)
```

观测噪声模拟传感器误差。它和 Event 不同，不是 reset 时采一次，而是在观测生成时作用。

## 视觉随机化

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-dr-grid.png" alt="域随机化外观网格" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">视觉域随机化让同一任务呈现不同颜色、材质和光照，避免视觉策略只记住一种外观。</figcaption>
</figure>

视觉策略通常要随机化：

```text
光照强度 / 方向
物体颜色 / 材质
相机噪声
相机外参小扰动
背景和干扰物
```

如果任务只用低维状态观测，视觉随机化不是重点；如果策略直接看 RGB 或深度，视觉随机化会显著影响泛化。

## 范围怎么选

| 任务 | 初始建议 |
|---|---|
| 四足 locomotion | 质量 0.8-1.2，摩擦 0.5-1.25，小推力 |
| 机械臂 manipulation | 质量 0.9-1.1，物体位姿适度随机 |
| 灵巧手 | 小范围质量 / 摩擦 / 关节噪声 |
| 视觉策略 | 小分辨率先收敛，再加外观变化 |

原则：

```text
先小范围确认能收敛
再逐步扩大随机化
不收敛时先缩随机化范围
不要同时打开所有强随机化
```

## 和课程学习结合

域随机化负责“随机什么”，课程学习负责“什么时候变难”。

```text
训练初期：摩擦范围窄，目标位置近
训练中期：扩大摩擦，增大目标范围
训练后期：加入外力扰动和更复杂外观
```

这比一开始就全量随机化更稳。

## 小结

- 域随机化让策略适应一族环境，而不是单一仿真设置。
- 物理和 reset 随机化通常走 Event System；观测噪声写在 `ObsTerm`；视觉随机化关注光照、颜色和相机。
- 随机化范围要从小到大，和课程学习配合。

## 导航

- 上一页：[模仿学习与官方示例](04-imitation-learning.md)
- 返回目录：[训练与评测](../05-training.md)
- 下一页：[多 GPU 与分布式](06-distributed.md)
