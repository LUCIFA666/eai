# 场景与资产配置

上一部分读任务时，scene 只是表格里的一个配置块。真正动手写任务时，scene 是第一块要落地的东西：机器人在哪里、物体在哪里、地面和桌子怎么放、相机或接触传感器挂在哪里、这些东西是否要在每个环境里各有一份。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么 Scene 只管「物理舞台」，不掺任务逻辑？
2. Isaac Lab 有哪五类常见资产，分别用什么 Cfg 声明？
3. `InteractiveSceneCfg`、`{ENV_REGEX_NS}` 和 `num_envs` 怎么把一个场景复制成成百上千个并行环境？

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-robot-gallery.png" alt="Isaac Lab 内置机器人资产总览" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">机械臂、四足、人形和飞行器在 Isaac Lab 里都可以作为资产加入 scene。差异在机器人模型和执行器配置，场景组织方式是一致的。</figcaption>
</figure>

## Scene 不是任务逻辑

Scene 的职责是声明物理世界里有哪些实体。它通常不直接写 reward，也不直接决定策略看到什么。可以先建立一个分工：

| 层次 | 负责什么 | 典型配置 |
|---|---|---|
| Asset | 一个机器人、一个物体、一块地面、一台相机 | `ArticulationCfg`、`RigidObjectCfg`、`DeformableObjectCfg`、`AssetBaseCfg`、`CameraCfg` |
| Scene | 把多个 asset 组织成一个并行环境模板 | `InteractiveSceneCfg` |
| Manager | 把 scene 中的状态转成观测、动作、奖励、终止等 | `ObservationsCfg`、`ActionsCfg`、`RewardsCfg` |

因此，写 scene 时先问“世界里有什么”，不要急着问“策略怎么学”。

## 五类常见资产

| 资产类型 | 配置类 | 特征 | 常见用途 |
|---|---|---|---|
| 关节体 | `ArticulationCfg` | 多个刚体由关节连接 | 机械臂、四足、人形、灵巧手 |
| 刚体 | `RigidObjectCfg` | 单个刚体，没有可控关节 | 方块、杯子、球、目标物 |
| 可变形物体 | `DeformableObjectCfg` | 形状会随接触和材料属性变化 | 软块、布料、海绵、软质食物 |
| 静态资产 | `AssetBaseCfg` | 不被策略控制，通常不主动运动 | 地面、墙、桌面、灯光 |
| 传感器 | `CameraCfg`、`ContactSensorCfg` 等 | 从场景中读取视觉、接触、射线等信息 | RGB-D、接触力、height scanner |

这一页先聚焦机器人、物体和静态资产。传感器会在下一部分“任务逻辑配置”里继续展开，因为传感器通常要进入 observation。

## Articulation

`ArticulationCfg` 用来声明有关节的机器人。它的三个核心字段是 `spawn`、`init_state`、`actuators`。

```python
from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
import isaaclab.sim as sim_utils

robot = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Robot",
    spawn=sim_utils.UsdFileCfg(
        usd_path="path/to/franka.usd",
        activate_contact_sensors=True,
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
        joint_pos={
            "panda_joint1": 0.0,
            "panda_joint2": -0.569,
            "panda_joint4": -2.810,
            "panda_joint6": 3.037,
        },
    ),
    actuators={
        "arm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint.*"],
            stiffness=400.0,
            damping=80.0,
        ),
    },
)
```

读一个 `ArticulationCfg` 时按下面顺序看：

| 字段 | 读什么 |
|---|---|
| `prim_path` | 这个机器人在 USD stage 中挂在哪里，是否带 `{ENV_REGEX_NS}` |
| `spawn` | 从 USD 加载，还是由几何体生成；是否启用接触传感器 |
| `init_state` | 初始根位姿和默认关节角是否合理 |
| `actuators` | 哪些关节被哪个执行器组控制 |

如果一个机器人在画面里存在但完全不动，常见原因不是 scene 没加载，而是 `actuators` 的 `joint_names_expr` 没匹配到关节。

## RigidObject

`RigidObjectCfg` 用来声明没有关节的刚体。方块、球、杯子、目标物都属于这一类。

```python
from isaaclab.assets import RigidObjectCfg
import isaaclab.sim as sim_utils

cube = RigidObjectCfg(
    prim_path="{ENV_REGEX_NS}/Cube",
    spawn=sim_utils.CuboidCfg(
        size=(0.05, 0.05, 0.05),
        rigid_props=sim_utils.RigidBodyPropertiesCfg(),
        mass_props=sim_utils.MassPropertiesCfg(mass=0.1),
        collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 0.8, 0.2)),
    ),
    init_state=RigidObjectCfg.InitialStateCfg(pos=(0.5, 0.0, 0.025)),
)
```

刚体没有关节状态，最常读写的是根位姿和速度：

```python
cube = scene["cube"]

pos_w = cube.data.root_pos_w
quat_w = cube.data.root_quat_w
lin_vel_w = cube.data.root_lin_vel_w
ang_vel_w = cube.data.root_ang_vel_w

cube.write_root_pose_to_sim(new_pose, env_ids=env_ids)
```

`write_*_to_sim` 只应该用于 reset 或状态直接改写。正常控制阶段应让物体通过物理接触自然运动。

## DeformableObject

不是所有被操作物体都适合建成刚体。软块、布料、海绵、软质食物这类对象会在接触中变形，通常需要用 `DeformableObjectCfg` 表达。

Isaac Lab 官方给了一个最小示例，位置在：

```bash
./isaaclab.sh -p scripts/tutorials/01_assets/run_deformable_object.py
```

这个脚本会生成四个 soft cube，其中两个自由下落，另外两个通过 nodal kinematic target 拉动网格节点：

<figure class="doc-figure">
<video src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-deformable-object.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.5em 0"></video>
<figcaption class="doc-figure-subtitle">DeformableObject 示例：可变形物体不是用单个根位姿描述，而是通过软体网格节点参与仿真。</figcaption>
</figure>

核心配置形态如下：

```python
from isaaclab.assets import DeformableObjectCfg
import isaaclab.sim as sim_utils

soft_cube = DeformableObjectCfg(
    prim_path="/World/Origin.*/Cube",
    spawn=sim_utils.MeshCuboidCfg(
        size=(0.2, 0.2, 0.2),
        deformable_props=sim_utils.DeformableBodyPropertiesCfg(
            rest_offset=0.0,
            contact_offset=0.001,
        ),
        physics_material=sim_utils.DeformableBodyMaterialCfg(
            poissons_ratio=0.4,
            youngs_modulus=1e5,
        ),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.3, 0.2)),
    ),
    init_state=DeformableObjectCfg.InitialStateCfg(pos=(0.0, 0.0, 1.0)),
)
```

可变形物体和刚体最重要的区别在状态表示。刚体主要看根位姿和速度；可变形物体的状态由网格节点的位置、速度和运动学目标组成。因此，读写软体状态时不要再套用 `root_pos_w` 这一套理解视角，而要关注 nodal state：

```python
nodal_state = soft_object.data.default_nodal_state_w.clone()
soft_object.write_nodal_state_to_sim(nodal_state)

nodal_kinematic_target = soft_object.data.nodal_kinematic_target.clone()
nodal_kinematic_target[..., 3] = 1.0  # 1 表示节点自由，0 表示节点受 kinematic target 约束
soft_object.write_nodal_kinematic_target_to_sim(nodal_kinematic_target)
```

可变形物体需要 mesh，并且通常依赖 GPU simulation。机器人学习任务里，软体还会带来三类额外成本：仿真更慢、观测更复杂、成功判据更难写。只有当任务目标真的依赖形变时，才值得把物体建成 `DeformableObjectCfg`；普通抓取、推移、堆叠任务通常先用 `RigidObjectCfg` 更清晰。

## AssetBase

地面、灯光、墙体、桌面这类对象通常不需要每个环境单独控制。它们常用 `AssetBaseCfg` 声明：

```python
from isaaclab.assets import AssetBaseCfg
import isaaclab.sim as sim_utils

ground = AssetBaseCfg(
    prim_path="/World/defaultGroundPlane",
    spawn=sim_utils.GroundPlaneCfg(),
)

light = AssetBaseCfg(
    prim_path="/World/Light",
    spawn=sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75)),
)
```

注意这里没有 `{ENV_REGEX_NS}`。这表示它们是全局共享资产，不会为每个环境复制一份。共享地面很常见，因为所有环境虽然摆在不同位置，但可以共用同一个大地面。

## InteractiveSceneCfg

`InteractiveSceneCfg` 是 scene 的入口。它把 robot、object、ground、light 等资产放进一个可克隆的环境模板。

```python
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass

@configclass
class MySceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(
        prim_path="/World/defaultGroundPlane",
        spawn=sim_utils.GroundPlaneCfg(),
    )

    robot = robot.replace(prim_path="{ENV_REGEX_NS}/Robot")

    cube = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Cube",
        spawn=sim_utils.CuboidCfg(size=(0.05, 0.05, 0.05)),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.5, 0.0, 0.025)),
    )
```

Manager-based 任务通常会在环境配置里引用它：

```python
@configclass
class MyTaskEnvCfg(ManagerBasedRLEnvCfg):
    scene: MySceneCfg = MySceneCfg(num_envs=4096, env_spacing=2.5)
```

这行的意思是：每个环境都按 `MySceneCfg` 搭一份，但环境之间相隔 2.5 米，并由 Isaac Lab 批量管理。

## `{ENV_REGEX_NS}` 是并行环境的入口

`{ENV_REGEX_NS}` 会在运行时展开成每个环境自己的命名空间：

```text
{ENV_REGEX_NS}/Robot
  -> /World/envs/env_0/Robot
  -> /World/envs/env_1/Robot
  -> /World/envs/env_2/Robot
  -> ...
```

判断一个资产是否应该带 `{ENV_REGEX_NS}`，可以用下面的规则：

| 资产 | 是否带 `{ENV_REGEX_NS}` | 原因 |
|---|---|---|
| 机器人 | 是 | 每个环境要有自己的机器人状态 |
| 被操作物体 | 是 | 每个环境要有自己的物体位置 |
| 目标标记 | 通常是 | 每个环境的目标不同 |
| 地面 | 通常否 | 可在所有环境间共享 |
| 全局灯光 | 否 | 不需要每个环境一盏 |

如果该复制的资产没有带 `{ENV_REGEX_NS}`，多个环境会抢同一个对象；如果全局资产误带了 `{ENV_REGEX_NS}`，显存和 stage 复杂度会不必要地增加。

## num_envs 与 env_spacing

`num_envs` 决定并行环境数量，`env_spacing` 决定环境之间摆多远。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-cloned-envs-grid.png" alt="克隆出的并行环境网格" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">同一份场景配置被克隆成二维网格。每个小格是一个并行环境，策略采样时一次处理整批环境状态。</figcaption>
</figure>

`env_spacing` 不是为了好看，而是为了让不同环境的物理对象在空间上分开。真正避免环境间碰撞，还需要碰撞过滤；Manager-based 工作流里 `InteractiveScene` 会自动处理常见情况。

## 状态读取

从 scene 取出资产后，状态都在 `data` 下：

```python
robot = scene["robot"]
cube = scene["cube"]

joint_pos = robot.data.joint_pos      # (num_envs, num_joints)
joint_vel = robot.data.joint_vel      # (num_envs, num_joints)
body_pos_w = robot.data.body_pos_w    # 所有 body 的世界系位置，形状 (num_envs, num_bodies, 3)

cube_pos_w = cube.data.root_pos_w     # (num_envs, 3)
```

第一维永远是 `num_envs`。这和前面 CartPole 日志里的并行吞吐对应：Isaac Lab 不是一次只推进一个环境，而是把所有环境状态作为一批 GPU 张量来读写。

## 多资产生成

如果希望每个环境里出现不同形状的物体，可以用 `MultiAssetSpawnerCfg` 在生成阶段随机选资产。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-multi-asset-grid.png" alt="多资产随机生成的并行环境" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">同一组环境中可以混合不同几何体。多资产生成用于增加任务外观和接触形态的多样性。</figcaption>
</figure>

示意配置：

```python
object_cfg = RigidObjectCfg(
    prim_path="{ENV_REGEX_NS}/Object",
    spawn=sim_utils.MultiAssetSpawnerCfg(
        assets_cfg=[
            sim_utils.CuboidCfg(size=(0.05, 0.05, 0.05)),
            sim_utils.SphereCfg(radius=0.03),
            sim_utils.CylinderCfg(radius=0.025, height=0.08),
        ],
        random_choice=True,
    ),
)
```

这里的随机发生在 spawn / clone 阶段，不等价于每次 reset 都重新抽一个形状。每次 reset 的位置、姿态、质量随机化通常交给 Event Manager。

## 最小检查清单

写完 scene 后，先不要急着训练。先检查下面几件事：

```text
[ ] 机器人、物体、目标是否都带了正确的 prim_path？
[ ] 需要并行复制的资产是否带 {ENV_REGEX_NS}？
[ ] ground / light 这类共享资产是否没有误带 {ENV_REGEX_NS}？
[ ] init_state 的高度是否合理，机器人是否穿地或悬空？
[ ] joint_names_expr 是否能匹配到真实关节名？
[ ] num_envs 和 env_spacing 是否适合当前机器显存和任务尺度？
```

## 小结

- Scene 负责声明物理世界，不负责写 reward 和 termination。
- 机器人通常是 `ArticulationCfg`，普通被操作物体通常是 `RigidObjectCfg`，软体和可变形物体使用 `DeformableObjectCfg`，地面和灯光常用 `AssetBaseCfg`。
- `{ENV_REGEX_NS}` 决定资产是否进入每个并行环境的命名空间。
- `InteractiveSceneCfg(num_envs, env_spacing)` 把一份场景模板变成批量环境。
- 所有运行时状态都是 `(num_envs, ...)` 张量，后续 observation、reward、reset 都会读取这些张量。

## 参考资料

- Isaac Lab Tutorial: Interactive Scene. `scripts/tutorials/02_scene/create_scene.py`
- Isaac Lab Tutorial: Assets. `scripts/tutorials/01_assets/`
- Isaac Lab Core Concepts: Scene and Assets. https://isaac-sim.github.io/IsaacLab/

## 导航

- 返回目录：[场景与机器人资产](../03-scene-and-robot.md)
- 下一页：[执行器模型](02-actuators.md)
