# 观测设计

设计观测，首先要想清楚一件事：策略每一步到底能看到什么。看不到的信息，策略就无法利用；塞进太多无关信息，又会加大学习难度和部署风险。

## 本节目标

本节围绕下面几个问题展开：

1. 观测和 scene 的完整状态有什么区别，该给策略看什么？
2. `ObservationsCfg` / `ObsTerm` 怎么组织观测，每项形状是什么？
3. 怎么写自定义观测函数、用 `SceneEntityCfg` 解析 body / joint？
4. policy 和 critic 为什么可以看不同信息（privileged）？
5. 噪声、裁剪、拼接顺序为什么影响训练和部署一致性？

## 术语速查

进入正文前，先把本节反复出现的配置类名和术语对齐。命名规律：`XxxCfg` 是配置容器，`XxxTerm` 是其中一个最小配置项。

| 术语 | 中文名 | 一句话含义 |
|---|---|---|
| observation | 观测 | 策略每步能看到的状态子集，≠ 场景全部状态 |
| `ObservationsCfg` | 观测配置 | 声明全部观测组的配置类 |
| observation group（`policy` / `critic`） | 观测组 | 打包给某个网络的一组观测 |
| `ObsTerm`（`ObservationTermCfg`） | 观测项 | 单个观测项，返回 `(num_envs, dim)` 张量 |
| `num_envs` / `dim` | 并行环境数 / 维度 | 张量第 0 维是环境数，第 1 维是该项维度 |
| `concatenate_terms` | 拼接观测项 | 为 True 时把组内各项按顺序拼成一个向量 |
| `enable_corruption` | 启用噪声 | 为 True，`noise=` 才真正生效 |
| noise / clip / scale | 噪声 / 裁剪 / 缩放 | 加扰动提鲁棒、截断异常值、调数值尺度 |
| actor / critic | 演员 / 评论家 | 输出动作的策略网络 / 估计价值的网络 |
| privileged observation | 特权观测 | 只给 critic、部署时拿不到的额外信息 |
| `SceneEntityCfg` | 场景实体配置 | 按名字解析 body / joint，避免硬编码索引 |

## 观测不是 scene 本身

Scene 里有完整物理状态，但策略通常只能看到其中一部分。

| scene 中的状态 | 是否纳入观测 | 说明 |
|---|---|---|
| 关节位置、关节速度 | 通常纳入 | 机器人本体状态 |
| 目标命令 | 任务相关时必须纳入 | reach 目标、速度命令等 |
| 物体位姿 | 操作任务通常纳入 | 若真机无法测量，部署时要谨慎 |
| 接触力、深度图 | 视任务而定 | 传感器观测 |
| 完整 simulator state | actor 通常不纳入 | 可纳入 critic 做 privileged observation |

观测设计的关键不是“越多越好”，而是让策略看到完成任务所需、部署时也能获得的信息。

## ObservationsCfg 基本结构

Manager-based 环境用 `ObservationsCfg` 声明观测组。最常见的组叫 `policy`，作为 actor 输入。

```python
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.utils import configclass
import isaaclab.envs.mdp as mdp

@configclass
class ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        target = ObsTerm(func=mdp.generated_commands, params={"command_name": "ee_pose"})
        actions = ObsTerm(func=mdp.last_action)

        def __post_init__(self):
            self.enable_corruption = True
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()
```

每个 `ObsTerm` 返回形状为 `(num_envs, dim)` 的张量。`concatenate_terms=True` 时，这些项按顺序拼成一个大向量。

## CartPole 观测结构

上面是写法，下面是 Isaac Lab 真正跑起来时打印的东西。启动内置 CartPole 环境（`scripts/tutorials/03_envs/create_cartpole_base_env.py`），控制台会打印 Observation Manager 的实际摘要：

```text
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

这张表把前面抽象的概念落到了具体数字上：

- `policy` 组的最终形状是 `(4,)`，正是两个 ObsTerm 拼接的结果：`joint_pos_rel (2,)` + `joint_vel_rel (2,)` = `(4,)`。
- CartPole 有 2 个关节（小车在滑轨上的平移 + 摆杆的转动），所以每个 term 都是 `(2,)`。
- 这 4 个数就是策略每一步唯一能看到的东西——没有图像、没有全局坐标，只有相对关节位置和速度。

环境跑起来后还可以逐步打印某个具体观测分量，例如摆杆角度：

```text
[Env 0]: Pole joint:  0.27883270382881165
[Env 0]: Pole joint:  0.2807479202747345
[Env 0]: Pole joint:  0.28593990206718445
[Env 0]: Pole joint:  0.295279324054718
[Env 0]: Pole joint:  0.30883559584617615
```

没有动作干预时，摆杆角度在一步步增大——杆子正在倒下。策略要学的，就是根据这 `(4,)` 维观测，每步输出合适的力把杆子稳住。

## 常见观测项

| 观测项 | 典型函数 | 用途 |
|---|---|---|
| 相对关节位置 | `mdp.joint_pos_rel` | 机器人姿态 |
| 关节速度 | `mdp.joint_vel_rel` | 动态状态 |
| 上一步动作 | `mdp.last_action` | 平滑控制、减少震荡 |
| 目标命令 | `mdp.generated_commands` | 告诉策略目标是什么 |
| 基座角速度 | `mdp.base_ang_vel` | locomotion 常用 |
| 重力投影 | `mdp.projected_gravity` | 姿态感知 |
| 高度扫描 | 自定义函数或内置项 | 粗糙地形感知 |

CartPole 这类低维任务只需要少量状态；四足和操作任务通常需要关节状态、目标命令、上一动作和传感器信息。

## 自定义观测函数

观测函数接收环境对象，返回 `(num_envs, dim)` 张量。

```python
import torch
from isaaclab.managers import SceneEntityCfg

def ee_position_in_world(env, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot", body_names="panda_hand")):
    robot = env.scene[asset_cfg.name]
    body_id = asset_cfg.body_ids[0]
    return robot.data.body_pos_w[:, body_id, :]
```

再挂到配置里：

```python
ee_pos = ObsTerm(
    func=ee_position_in_world,
    params={"asset_cfg": SceneEntityCfg("robot", body_names="panda_hand")},
)
```

`SceneEntityCfg` 的作用是按名字解析 body / joint，而不是在代码里硬写索引。机器人模型换了以后，名字比数字索引更稳。

## policy 和 critic 可以不同

训练时可以让 actor 和 critic 看到不同信息：

```python
@configclass
class ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        actions = ObsTerm(func=mdp.last_action)

    @configclass
    class CriticCfg(ObsGroup):
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        # 该函数来自 isaaclab_tasks 中 lift 任务自定义的 mdp 模块，不在核心 isaaclab.envs.mdp 里
        object_pose = ObsTerm(func=mdp.object_position_in_robot_root_frame)

    policy: PolicyCfg = PolicyCfg()
    critic: CriticCfg = CriticCfg()
```

这叫 privileged observation：critic 可在训练中看到更多仿真内部信息，actor 只看到部署时可获得的信息。

## 噪声、裁剪和归一化

观测噪声用于提升鲁棒性：

```python
from isaaclab.utils.noise import UniformNoiseCfg

joint_pos = ObsTerm(
    func=mdp.joint_pos_rel,
    noise=UniformNoiseCfg(n_min=-0.01, n_max=0.01),
    clip=(-3.14, 3.14),
)
```

三个常见操作：

| 操作 | 目的 |
|---|---|
| noise | 模拟传感器误差，提升 Sim2Real 鲁棒性 |
| clip | 防止异常值进入策略 |
| scale | 调整数值尺度，让各维输入范围更接近 |

噪声不是越大越好。噪声过大时，策略会学得在输入不可靠时一味保守，任务表现反而下降。

### 观测噪声的输出对照

只写 `noise=` 还不够——必须同时让观测组开启 `enable_corruption=True`，否则噪声配置不会生效，也不会报错。下面用一个最小脚本验证：给 CartPole 的 `joint_pos_rel` / `joint_vel_rel` 各加 `UniformNoiseCfg(n_min=-0.01, n_max=0.01)`，不施加动作，逐步打印「干净值 / 加噪后的观测 / 注入的噪声」。

关键配置（两处缺一不可，少任意一处注入噪声都会恒为 0）：

```python
from isaaclab.utils.noise import UniformNoiseCfg as Unoise

class PolicyCfg(ObsGroup):
    joint_pos_rel = ObsTerm(func=mdp.joint_pos_rel, noise=Unoise(n_min=-0.01, n_max=0.01))
    joint_vel_rel = ObsTerm(func=mdp.joint_vel_rel, noise=Unoise(n_min=-0.01, n_max=0.01))

    def __post_init__(self):
        self.enable_corruption = True   # 必须为 True，noise 才会真正作用
        self.concatenate_terms = True
```

控制台输出可以看到同一个环境的观测值在噪声作用下产生扰动。下面节选 env 0 的若干步：

```text
[step 00] clean joint_pos_rel = [0.0, 0.0]
[step 00] noisy obs[:2]       = [-0.00872, 0.00536]
[step 00] injected noise      = [-0.00872, 0.00536]   (应在 ±0.01 内)
[step 01] injected noise      = [ 0.0023,  -0.00134]
[step 02] injected noise      = [ 0.00906, -0.00329]
[step 05] injected noise      = [ 0.00249,  0.0069 ]
[step 09] injected noise      = [-0.00415, -2e-05  ]
[step 11] injected noise      = [ 0.00735, -0.00499]
```

- `clean` 是未加噪声前的相对关节位置；因为不施力且刚 reset，所以是 `0`。
- `noisy` 是策略每步实际看到的观测，被加上了一个不同的随机扰动。
- `injected = noisy - clean` 全部落在 `±0.01` 内，正是 `UniformNoiseCfg(-0.01, 0.01)` 的范围——说明噪声确实作用在了观测上。

> 复现提示：Isaac Lab 用 `simulation_app.close()` 硬退出，把 `print()` 重定向到文件时会因块缓冲而丢失输出。重定向到文件时加 `PYTHONUNBUFFERED=1`（或 `print(..., flush=True)`），否则会看到「只有启动日志、没有 step 输出」的假象，误以为脚本崩了。

## 观测顺序很重要

当 `concatenate_terms=True` 时，拼接顺序就是配置里的 term 顺序。部署时如果手动构造观测，顺序、维度、归一化都要和训练时保持一致。

```text
policy obs =
  [joint_pos, joint_vel, target_command, last_action]
```

如果训练时是 `[joint_pos, joint_vel, target, action]`，部署时写成 `[target, joint_pos, joint_vel, action]`，策略不会报错，但行为会完全错乱。

## 最小检查清单

```text
[ ] 策略是否能看到完成任务所需的目标？
[ ] 观测是否包含真机部署时拿不到的信息？
[ ] 每个 ObsTerm 输出是否都是 (num_envs, dim)？
[ ] 拼接顺序是否有明确记录下来？
[ ] 噪声、裁剪、scale 是否符合传感器量级？
[ ] critic 的 privileged observation 是否只在训练中使用？
```

## 观测噪声检查

给观测项加 noise cfg 后，不要只看配置文件。写一个最小检查脚本，固定 4 个左右并行环境，分别打印干净的 `joint_pos_rel`、加噪后的 observation，以及两者差值。若噪声配置是 `UniformNoiseCfg(n_min=-0.01, n_max=0.01)`，差值应该稳定落在这个范围内。

```text
[INFO] Observation Manager: <ObservationManager> contains 1 groups.
Active Observation Terms in Group: 'policy' (shape: (4,))
0 joint_pos_rel (2,)
1 joint_vel_rel (2,)

[step 00] clean joint_pos_rel = [0.0, 0.0]
[step 00] noisy obs[:2]       = [-0.00229, 0.00875]
[step 00] injected noise      = [-0.00229, 0.00875]  (在 +/-0.01 内)
[step 05] injected noise      = [0.00995, 0.00808]   (在 +/-0.01 内)
```

如果差值总是 0，通常是 noise cfg 没挂到对应 `ObsTerm`；如果差值维度不对，先查 observation group 的拼接顺序和 term 输出 shape。

## 小结

- 观测是策略看到的状态子集，不等于 scene 的全部物理状态。
- `ObservationsCfg` 用观测组组织输入，`ObsTerm` 每项返回 `(num_envs, dim)` 张量。
- `SceneEntityCfg` 用名字解析 joint / body，避免硬编码索引。
- 观测顺序、维度、噪声和裁剪会直接影响训练与部署一致性。

## 参考资料

- Isaac Lab Observation Manager. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab MDP observation terms. `source/isaaclab/isaaclab/envs/mdp/observations.py`

## 导航

- 返回目录：[任务逻辑配置](../04-task-logic.md)
- 下一页：[传感器](02-sensors.md)
