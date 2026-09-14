# ManiSkill Task 种类

本节用来理解 ManiSkill 的任务空间。前面几节主要围绕 `PickCube-v1`、`PushCube-v1` 做复现，但 ManiSkill 并不只是几个 cube 任务，它提供了从简单控制、桌面机械臂、灵巧手，到移动操作、数字孪生场景的一组任务集合。

官方任务索引：

```text
https://maniskill.readthedocs.io/en/latest/tasks/index.html
```

## 1. 官方 Task 页面怎么看

ManiSkill 的 task 页面通常会给出以下信息：

| 信息 | 含义 |
|---|---|
| `env_id` | Gymnasium 创建环境时使用的任务名，例如 `PickCube-v1` |
| 任务类别 | 任务属于 table-top、mobile manipulation、dexterous hand 等哪一类 |
| reward | 是否提供 dense reward、sparse reward |
| assets | 是否需要额外下载模型、场景、物体资产 |
| demos | 是否提供官方 demonstration 数据 |
| 控制对象 | 使用 Franka Panda、Unitree、TriFinger、SO100、WidowX 等哪类机器人 |

复现时最重要的是 `env_id`。只要知道任务名，就可以用 Gymnasium 创建：

```python
import gymnasium as gym
import mani_skill.envs

env = gym.make(
    "PickCube-v1",
    obs_mode="state",
    control_mode="pd_joint_delta_pos",
    render_mode="rgb_array",
)
```

## 2. 当前环境中有哪些任务

当前 ManiSkill 注册到 Gymnasium 的任务有这些：


```text
PickCube-v1
PushCube-v1
StackCube-v1
PegInsertionSide-v1
TurnFaucet-v1
OpenCabinetDoor-v1
OpenCabinetDrawer-v1
PickSingleYCB-v1
PickClutterYCB-v1
TriFingerRotateCubeLevel0-v1
RotateSingleObjectInHandLevel0-v1
UnitreeG1PlaceAppleInBowl-v1
RoboCasaKitchen-v1
ReplicaCAD_SceneManipulation-v1
DrawTriangle-v1
DrawSVG-v1
```



## 3. ManiSkill 任务类别

根据官方 tasks 页面和当前注册环境，可以把 ManiSkill 任务大致分成以下几类。

### 3.1 基础控制任务

这类任务更接近传统强化学习控制环境，适合理解 action、reward 和 termination，但不一定包含复杂机器人操作。

示例：

```text
MS-CartpoleBalance-v1
MS-CartpoleSwingUp-v1
MS-HopperStand-v1
MS-HopperHop-v1
MS-AntWalk-v1
MS-HumanoidWalk-v1
```

适合用途：

```text
理解连续控制
测试 RL 算法链路
不优先用于机器人 manipulation 教程主线
```

### 3.2 桌面机械臂操作任务

这是 ManiSkill 教程中最适合作为入门的任务类别。任务通常围绕桌面物体进行抓取、推动、堆叠、插入等操作。

示例：

```text
PickCube-v1
PushCube-v1
StackCube-v1
PegInsertionSide-v1
PlugCharger-v1
PullCube-v1
PokeCube-v1
PickSingleYCB-v1
PickClutterYCB-v1
```

适合用途：

```text
Gymnasium quick start
随机动作 demo
demonstration 下载
trajectory replay / convert
PPO、BC、Diffusion Policy、ACT baseline
```

本教程前面选择 `PickCube-v1` 和 `PushCube-v1`，因为它们属于这类任务，流程清晰、复现成本较低。

### 3.3 Articulated Object 任务

这类任务需要操作带关节的物体，例如柜门、抽屉、水龙头。它们比 cube 任务更接近真实场景，也更依赖资产和接触建模。

示例：

```text
OpenCabinetDoor-v1
OpenCabinetDrawer-v1
TurnFaucet-v1
```

适合用途：

```text
验证关节物体资产是否可用
测试更复杂的 manipulation
研究接触、约束和几何随机化
```


### 3.4 灵巧手与多指操作任务

这类任务使用多指手或特殊夹爪完成旋转、姿态控制等操作。它们动作维度更高，训练更难。

示例：

```text
TriFingerRotateCubeLevel0-v1
TriFingerRotateCubeLevel1-v1
RotateSingleObjectInHandLevel0-v1
RotateSingleObjectInHandLevel1-v1
RotateValveLevel0-v1
```

适合用途：

```text
研究 dexterous manipulation
测试高维 action space
评估更强的 RL / IL 算法
```


### 3.5 移动操作与类人机器人任务

这类任务涉及移动平台、四足机器人或类人机器人，不只是机械臂末端操作，通常包含更复杂的身体控制和场景交互。

示例：

```text
UnitreeGo2-Reach-v1
UnitreeG1Stand-v1
UnitreeG1TransportBox-v1
UnitreeG1PlaceAppleInBowl-v1
UnitreeH1Stand-v1
AnymalC-Reach-v1
AnymalC-Spin-v1
```

适合用途：

```text
研究 mobile manipulation
研究 humanoid / quadruped control
和 VLA、导航、长程任务结合
```


### 3.6 数字孪生与真实场景任务

这类任务使用更复杂的真实场景资产，例如厨房、室内房间、ReplicaCAD 或 RoboCasa 场景。它们更接近 embodied AI 里的长期任务和真实环境评测。

示例：

```text
RoboCasaKitchen-v1
ReplicaCAD_SceneManipulation-v1
ReplicaCADPrepareGroceriesTrain_SceneManipulation-v1
ReplicaCADSetTableTrain_SceneManipulation-v1
ArchitecTHOR_SceneManipulation-v1
SceneManipulation-v1
```

适合用途：

```text
评估复杂场景中的操作能力
研究视觉观测、语言指令、长程规划
和 VLA / embodied AI benchmark 对接
```


### 3.7 绘制与轨迹跟踪任务

这类任务要求机器人执行绘制或轨迹跟踪动作，适合观察轨迹生成和控制质量。

示例：

```text
DrawTriangle-v1
DrawSVG-v1
TableTopFreeDraw-v1
```

适合用途：

```text
可视化控制策略
检查轨迹跟踪能力
作为 manipulation 之外的补充任务
```

## 4. 换任务注意事项

换任务不是只改 `env_id`。通常还要同步检查这些内容：

| 项目 | 说明 |
|---|---|
| `env_id` | `gym.make()`、demo 下载、baseline 命令中都要一致 |
| assets | 有些任务需要额外下载资产 |
| demo | 不是所有任务都有同样类型的 demonstration |
| `obs_mode` | state、rgb、rgbd、pointcloud 的成本不同 |
| `control_mode` | 必须和 demonstration metadata 对齐 |
| `max_episode_steps` | IL 训练时通常需要按 demo 长度调整 |
| `sim_backend` | state-based 可先用 CPU/GPU；视觉和大并行更依赖 GPU/Vulkan |

例如把 `PickCube-v1` 换成 `StackCube-v1`，至少要检查：

```bash
python -m mani_skill.utils.download_demo StackCube-v1

python -m mani_skill.trajectory.replay_trajectory \
  --traj-path /path/to/env/maniskill_data/demos/StackCube-v1/motionplanning/trajectory.h5 \
  --save-traj \
  --allow-failure \
  -o state \
  -c pd_ee_delta_pose \
  --count 10
```

如果任务没有对应 demonstration，或者该任务不支持目标 `control_mode`，就需要换任务、换 demo 来源，或者调整控制模式。


## 导航

| 上一节 | 下一节 |
|---|---|
| [Overview](01-overview.md) | [安装与渲染依赖](03-installation-and-rendering-deps.md) |
