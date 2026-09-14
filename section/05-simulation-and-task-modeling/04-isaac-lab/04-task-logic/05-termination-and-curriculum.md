# 终止与课程

一个任务不只需要奖励，还需要定义边界：什么时候算失败、什么时候算成功、什么时候只是时间到了。对复杂任务，还要规划难度：一开始不要太难，之后逐步加难。

## 本节目标

本节围绕下面几个问题展开：

1. `terminated` 和 `truncated` 有什么区别，为什么不能混用？
2. `TerminationsCfg` 常见终止项有哪些？
3. reset 写状态时为什么要注意 `env_ids` 和 `env_origins`？
4. 课程学习（Curriculum）怎么让任务难度逐步增加？

## 术语速查

进入正文前，先把本节的终止 / 事件 / 课程术语对齐（`XxxCfg` 是配置容器，`XxxTerm` 是其中一个最小配置项）。

| 术语 | 中文名 | 一句话含义 |
|---|---|---|
| terminated / truncated | 终止 / 截断 | 任务自然成败结束 / 因时间上限被截断 |
| episode | 回合 | 从 reset 到终止的一段交互 |
| `TerminationsCfg` / `DoneTerm` | 终止配置 / 终止项 | 声明 episode 何时结束 |
| `time_out` | 超时 | 到达最大回合步数；标 `time_out=True` 不算失败 |
| `EventCfg` / Event Manager | 事件配置 / 事件管理器 | 负责 reset 与随机化 |
| startup / reset / interval | 启动时 / 重置时 / 周期 | 事件的三种触发时机 |
| domain randomization | 域随机化 | 随机质量、摩擦、外力等以提升泛化 |
| `env_ids` / `env_origins` | 环境索引 / 环境原点 | 只写指定环境 / 各环境在世界中的原点 |
| `CurriculumCfg` / `CurrTerm` | 课程配置 / 课程项 | 控制难度随训练进度变化 |
| curriculum learning | 课程学习 | 任务由易到难逐步加难 |
| `TerrainGeneratorCfg` | 地形生成配置 | 程序化生成地形并按难度分配 |
| Sim2Real | 仿真到现实 | 把仿真训练的策略迁移到真实机器人 |

## terminated 和 truncated

Gymnasium 风格里有两个结束概念：

| 概念 | 含义 | 例子 |
|---|---|---|
| `terminated` | 任务自然结束，成功或失败 | 摔倒、出界、任务成功 |
| `truncated` | 因时间限制被截断 | 达到最大 episode length |

在 Isaac Lab 的配置里，`time_out=True` 的 termination 通常表示时间截断，不等同于失败。

## TerminationsCfg

终止条件用 `TerminationsCfg` 声明：

```python
from isaaclab.managers import TerminationTermCfg as DoneTerm

@configclass
class TerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    base_contact = DoneTerm(
        func=mdp.illegal_contact,
        params={"sensor_cfg": SceneEntityCfg("contact_sensor", body_names="base"), "threshold": 1.0},
    )
```

常见终止项：

| 终止项 | 用途 |
|---|---|
| time out | 回合到达时间上限 |
| root height too low | 四足 / 人形摔倒 |
| out of bounds | 机器人或物体出界 |
| illegal contact | 身体、手臂等不该碰的部位接触 |
| success | 操作任务完成 |

终止项会影响训练目标。过早终止会让策略缺少探索；过晚终止会浪费采样并污染奖励。

## reset 写状态

episode 结束后，需要把对应环境重置。reset 通常由 Event Manager 负责。

```python
from isaaclab.managers import EventTermCfg as EventTerm

@configclass
class EventCfg:
    reset_robot_joints = EventTerm(
        func=mdp.reset_joints_by_offset,
        mode="reset",
        params={
            "position_range": (-0.25, 0.25),
            "velocity_range": (-0.1, 0.1),
        },
    )
```

底层会调用类似 `write_joint_state_to_sim`、`write_root_pose_to_sim` 的接口，直接把指定 `env_ids` 的状态写回仿真。

重置 root 位姿时要注意 `scene.env_origins`：并行环境在世界中有不同原点，reset 的世界坐标需要加回环境原点，否则多个环境可能叠在同一个位置。

## EventCfg 和随机化

Event 不只用于 reset，还常用于域随机化。

| 模式 | 触发时机 | 例子 |
|---|---|---|
| `startup` | 仿真启动时 | 随机质量、摩擦 |
| `reset` | 每次环境重置时 | 随机初始关节、目标位置 |
| `interval` | 每隔一段时间 | 推机器人、外力扰动 |

示例：

```python
@configclass
class EventCfg:
    push_robot = EventTerm(
        func=mdp.push_by_setting_velocity,
        mode="interval",
        interval_range_s=(5.0, 10.0),
        params={"velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)}},
    )
```

Event 负责“每次怎么随机”，Curriculum 负责“随机范围什么时候变难”。

## 为什么需要课程学习

如果一开始就给最难任务，策略可能在初期完全拿不到有效奖励。课程学习的思想是先让任务简单，等策略能完成后再逐步加难。

典型例子：

```text
四足：平地 -> 小坡 -> 台阶 -> 粗糙地形
抓取：目标近 -> 目标远 -> 物体姿态更随机
奖励：先用稠密引导 -> 后期提高成功奖励
扰动：无外力 -> 小推力 -> 大推力
```

## CurriculumCfg

课程项可以修改奖励权重、环境参数或 term 配置。

```python
from isaaclab.managers import CurriculumTermCfg as CurrTerm

@configclass
class CurriculumCfg:
    sparse_reward_weight = CurrTerm(
        func=mdp.modify_reward_weight,
        params={"term_name": "success", "weight": 5.0, "num_steps": 200_000},
    )
```

常见工具：

| 工具 | 用途 |
|---|---|
| `modify_reward_weight` | 随训练进度调整奖励权重 |
| `modify_env_param` | 修改环境中的参数 |
| `modify_term_cfg` | 修改某个 manager term 的配置 |

课程学习不是为了“作弊”，而是为了让探索有梯度。

## 地形课程

locomotion 中常用程序化地形配合课程学习。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-terrain-grid.png" alt="Isaac Lab 程序化地形网格" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">地形网格通常按列表示类型、按行表示难度。策略表现越好，环境实例越可能被分配到更难的地形。</figcaption>
</figure>

示意配置：

```python
from isaaclab.terrains import TerrainGeneratorCfg

terrain_generator = TerrainGeneratorCfg(
    size=(8.0, 8.0),
    num_rows=10,
    num_cols=20,
    curriculum=True,
    difficulty_range=(0.0, 1.0),
    sub_terrains={
        "flat": mesh_terrains_cfg.MeshPlaneTerrainCfg(proportion=0.25),
        "rough": mesh_terrains_cfg.MeshRandomGridTerrainCfg(proportion=0.25),
        "stairs": mesh_terrains_cfg.MeshPyramidStairsTerrainCfg(proportion=0.25),
    },
)
```

地形课程和 RayCaster 常一起出现：地形变复杂后，策略需要高度扫描观测才能做出稳定落脚决策。

## 终止、奖励、课程要一致

三个部分不能互相打架：

| 如果这样写 | 后果 |
|---|---|
| 奖励鼓励速度，终止不惩罚摔倒 | 策略可能冲刺后摔倒 |
| 课程太快加难 | 策略还没学会就崩 |
| reset 分布太窄 | 训练容易，泛化差 |
| reset 分布太宽 | 初期学不到有效行为 |
| time_out 被当失败惩罚 | 能坚持到上限的策略反而受罚 |

## 最小检查清单

```text
[ ] time_out 是否标记为 time_out=True？
[ ] 失败终止是否和奖励目标一致？
[ ] reset 是否只写 env_ids 对应的环境？
[ ] root pose reset 是否加回 env_origins？
[ ] 随机化范围是否从可学习难度开始？
[ ] curriculum 加难速度是否和训练曲线匹配？
```

## 小结

- `terminated` 表示成功或失败，`truncated` 通常表示时间上限。
- Termination 定义 episode 边界，Event 定义 reset 和随机化，Curriculum 定义难度如何变化。
- reset 写状态时必须注意并行环境的 `env_ids` 和 `env_origins`。
- 课程学习让困难任务先有梯度，再逐渐接近目标难度。

## 参考资料

- Isaac Lab Termination and Event Managers. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab Curriculum Utilities. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab Terrain Generation API. https://isaac-sim.github.io/IsaacLab/

## 导航

- 上一页：[奖励工程](04-reward.md)
- 返回目录：[任务逻辑配置](../04-task-logic.md)
- 下一页：[训练与评测](../05-training.md)
