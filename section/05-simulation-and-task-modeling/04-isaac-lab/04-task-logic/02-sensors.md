# 传感器

上一页讲的是如何组装观测。本页讲观测从哪里来。关节位置这类状态来自 `Articulation.data`，而视觉、地形高度、足底接触、末端相对位姿等信息通常来自传感器。

## 本节目标

本节围绕下面几个问题展开：

1. Isaac Lab 有哪几类传感器，各输出什么、用在什么任务？
2. 相机 / RayCaster / ContactSensor / FrameTransformer 怎么配、怎么读？
3. 传感器读数怎么进入 observation？
4. 各类传感器的性能代价怎么权衡？

## 术语速查

进入正文前，先把本节的传感器配置类和术语对齐（`XxxCfg` 是配置容器）。

| 术语 | 中文名 | 一句话含义 |
|---|---|---|
| sensor | 传感器 | 在 scene 中产生观测数据的部件 |
| `CameraCfg` / `TiledCameraCfg` | 相机 / 平铺相机配置 | 输出 RGB / 深度 / 分割；Tiled 版省显存、适合大批量环境 |
| RGB-D | 彩色 + 深度 | 彩色图像加每像素深度 |
| `RayCasterCfg` | 射线投射配置 | 发射射线探测，常用于地形 |
| height scan | 高度扫描 | 把地形压成一组射线命中高度 |
| `ContactSensorCfg` | 接触传感器配置 | 读接触力、接触 / 腾空时间 |
| air time | 腾空时间 | 足端离地时长，常用于步态奖励 |
| `ImuCfg` / IMU | 惯性测量单元配置 | 输出角速度、线加速度 |
| `FrameTransformerCfg` | 帧变换配置 | 计算两个坐标系（frame）间的相对位姿 |
| `prim_path` | 图元路径 | 在 USD 场景树里定位部件的路径 |

## 传感器总览

| 传感器 | 配置类 | 输出 | 常见用途 |
|---|---|---|---|
| 相机 | `CameraCfg` / `TiledCameraCfg` | RGB、深度、法线、分割 | 视觉策略、数据采集 |
| 射线投射 | `RayCasterCfg` | 高度扫描、射线命中点 | 粗糙地形 locomotion |
| 接触 | `ContactSensorCfg` | 接触力、接触时间、腾空时间 | 足端步态、抓取、碰撞检测 |
| IMU | `ImuCfg` | 角速度、线加速度 | 姿态估计、飞行器 |
| 帧变换 | `FrameTransformerCfg` | body 间相对位姿 | 末端、目标、工具坐标 |

传感器通常定义在 scene 里，读数再通过 `ObsTerm` 进入 observation。

下面的代码片段默认已经在脚本顶部准备好这些常用依赖：

```python
import torch
import isaaclab.sim as sim_utils
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.sensors import CameraCfg, ContactSensorCfg, FrameTransformerCfg, RayCasterCfg
from isaaclab.sensors.ray_caster import patterns
from isaaclab.utils import configclass
import isaaclab.envs.mdp as mdp
```

如果把下面的片段复制进自己的任务配置，先确认这些名字已经 import，并且传感器对象已经作为 scene 字段注册。

## Camera

相机可输出 RGB、深度、分割等图像。

```python
camera = CameraCfg(
    prim_path="{ENV_REGEX_NS}/Robot/base/front_cam",
    offset=CameraCfg.OffsetCfg(
        pos=(0.3, 0.0, 0.1),
        rot=(0.5, -0.5, 0.5, -0.5),
        convention="ros",
    ),
    spawn=sim_utils.PinholeCameraCfg(focal_length=24.0),
    data_types=["rgb", "distance_to_image_plane"],
    update_period=0.1,
    height=128,
    width=128,
)
```

读取方式：

```python
camera = env.scene["camera"]
rgb = camera.data.output["rgb"]                         # (num_envs, H, W, 3)
depth = camera.data.output["distance_to_image_plane"]   # (num_envs, H, W, 1)
```

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-sensor-camera-rgbd-seg.png" alt="相机 RGB 深度 语义分割输出" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">同一场景的 RGB、深度和语义分割输出。视觉任务要同时考虑信息量、分辨率和显存。</figcaption>
</figure>

大规模视觉 RL 不宜给每个环境单独配置高分辨率相机。需要大量环境时，优先考虑 `TiledCameraCfg` 或降低环境数、分辨率和更新频率。

## RayCaster

RayCaster 从机器人附近发射射线，常用于四足机器人感知地形。

```python
height_scanner = RayCasterCfg(
    prim_path="{ENV_REGEX_NS}/Robot/base",
    offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 20.0)),
    ray_alignment="yaw",
    pattern_cfg=patterns.GridPatternCfg(resolution=0.1, size=(1.6, 1.0)),
    mesh_prim_paths=["/World/ground"],
    update_period=0.02,
)
```

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-sensor-heightscan.png" alt="RayCaster 高度扫描" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">高度扫描把崎岖地形压缩成一组射线命中高度，比相机便宜，适合 locomotion。</figcaption>
</figure>

常见观测函数：

```python
def height_scan(env):
    scanner = env.scene["height_scanner"]
    robot = env.scene["robot"]
    heights = scanner.data.ray_hits_w[..., 2]
    return heights - robot.data.root_pos_w[:, 2:3]
```

`ray_alignment="yaw"` 表示扫描网格只跟随机器人偏航角，不跟随俯仰和横滚。否则机器人一倾斜，高度图也会跟着歪。

## ContactSensor

接触传感器常用于四足足端、夹爪和碰撞检测。

```python
contact_forces = ContactSensorCfg(
    prim_path="{ENV_REGEX_NS}/Robot/.*_foot",
    update_period=0.0,
    history_length=3,
    track_air_time=True,
)
```

接触传感器能否读到力，不只取决于 `ContactSensorCfg`。对应刚体资产在 spawn 时也要允许 contact sensor；如果资产侧没有打开，配置了传感器也可能读不到预期接触信号。

读取方式：

```python
contact = env.scene["contact_forces"]
forces = contact.data.net_forces_w
air_time = contact.data.current_air_time
contact_time = contact.data.current_contact_time

in_contact = torch.norm(forces, dim=-1) > 1.0
```

用途：

| 用途 | 读什么 |
|---|---|
| 足端是否着地 | `net_forces_w` |
| 步态奖励 | `current_air_time` |
| 抓取是否接触 | 夹爪 contact force |
| 非期望碰撞 | 身体、手臂、底盘接触 |

## FrameTransformer

FrameTransformer 用于计算两个 frame 之间的相对位姿，操作任务里很常见。

```python
ee_frame = FrameTransformerCfg(
    prim_path="{ENV_REGEX_NS}/Robot/base",
    target_frames=[
        FrameTransformerCfg.FrameCfg(
            prim_path="{ENV_REGEX_NS}/Robot/panda_hand",
            name="ee",
        ),
    ],
)
```

它适合表达“末端相对基座”“相机相对工具”“目标相对末端”这类关系，能减少手写坐标变换错误。

## 传感器进入观测

传感器本身只产生数据，是否给策略看由 `ObservationsCfg` 决定。

```python
def foot_contact(env):
    contact = env.scene["contact_forces"]
    return (torch.norm(contact.data.net_forces_w, dim=-1) > 1.0).float()

@configclass
class ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        heights = ObsTerm(func=height_scan)
        contacts = ObsTerm(func=foot_contact)

    policy: PolicyCfg = PolicyCfg()
```

视觉观测如果是图像，通常不会简单拼到低维向量里，而是进入视觉 backbone 或模仿学习数据集。

## 性能取舍

| 传感器 | 代价 | 建议 |
|---|---|---|
| RGB-D 相机 | 高 | 降分辨率、降频率、少环境、用 tiled |
| RayCaster | 中低 | locomotion 首选地形观测 |
| ContactSensor | 低 | 足端和抓取任务常用 |
| FrameTransformer | 低 | 替代手写相对位姿 |
| IMU | 低 | 移动机器人、飞行器常用 |

## 小结

- 传感器定义在 scene 中，是否进入策略输入由 observation 决定。
- 相机信息丰富但昂贵；RayCaster 便宜，适合地形高度；ContactSensor 适合步态、抓取和碰撞判断。
- 传感器读数仍要保持 `(num_envs, ...)` 批量形状。

## 参考资料

- Isaac Lab Sensors API. https://isaac-sim.github.io/IsaacLab/
- Tutorial: `scripts/tutorials/04_sensors/add_sensors_on_robot.py`
- Tutorial: `scripts/tutorials/04_sensors/run_usd_camera.py`

## 导航

- 上一页：[观测设计](01-observation.md)
- 返回目录：[任务逻辑配置](../04-task-logic.md)
- 下一页：[动作与控制器](03-controllers.md)
