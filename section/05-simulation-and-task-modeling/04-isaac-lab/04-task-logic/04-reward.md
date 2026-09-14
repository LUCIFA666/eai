# 奖励工程

奖励定义了“什么算做得好”。在 RL 任务里，它既是训练信号，也是任务设定的一部分。奖励写错时，策略通常不会“失败”，而是认真学会一个错误目标。

## 本节目标

本节围绕下面几个问题展开：

1. 奖励怎么由多个 `RewTerm` 加权组成，`step_dt` 为什么重要？
2. 为什么先写最小奖励，再逐项加塑形？
3. Locomotion 和 manipulation 的奖励结构怎么拆？
4. 怎么看分项日志调奖励、识别常见失败模式？

## 术语速查

进入正文前，先把本节的奖励术语对齐（`XxxCfg` 是配置容器，`XxxTerm` 是其中一个最小配置项）。

| 术语 | 中文名 | 一句话含义 |
|---|---|---|
| reward | 奖励 | RL 的训练信号，也是任务定义的一部分 |
| `RewardsCfg` / Reward Manager | 奖励配置 / 奖励管理器 | 声明并加权求和各奖励项 |
| `RewTerm`（`RewardTermCfg`） | 奖励项 | 单个奖励项，返回 `(num_envs,)` 标量 |
| `step_dt` | 步长时间 | `sim.dt * decimation`，奖励按它缩放 |
| decimation | 降采样倍数 | 一个控制步包含多少个物理子步 |
| dense / sparse / mixed reward | 稠密 / 稀疏 / 混合奖励 | 每步反馈 / 仅成败反馈 / 两者结合 |
| reward shaping | 奖励塑形 | 加引导项加速学习（可能被策略钻空子） |
| ablation | 消融实验 | 把某项权重设 0，验证它的作用 |
| Locomotion / Manipulation | 运动控制 / 操作 | 行走奔跑类 / 抓取搬运类任务 |

## RewardManager 的结构

Manager-based 环境用 `RewardsCfg` 声明奖励项：

```python
from isaaclab.managers import RewardTermCfg as RewTerm

@configclass
class RewardsCfg:
    reaching = RewTerm(
        func=mdp.position_command_error,
        weight=-1.0,
        params={"command_name": "ee_pose"},
    )
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-0.01)
```

每个 `RewTerm` 返回 `(num_envs,)` 标量，Reward Manager 对各项加权求和。

```text
total_reward =
  weight_1 * term_1(env) * step_dt
  + weight_2 * term_2(env) * step_dt
  + ...
```

`step_dt = sim.dt * decimation`。因此权重不是孤立数字，改了控制频率后，奖励量级也要重新检查。

## 先写最小奖励

不要一开始就写十几个奖励项。先写能表达主任务的最小版本：

```python
@configclass
class RewardsCfg:
    reach = RewTerm(
        func=mdp.position_command_error,
        weight=-1.0,
        params={"command_name": "ee_pose"},
    )
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-0.01)
```

这个最小版本只回答两个问题：

- 离目标近不近；
- 动作是否过于剧烈。

能学到粗糙行为后，再逐项加入稳定性、能耗、成功奖励或阶段奖励。

## 稠密奖励和稀疏奖励

| 类型 | 含义 | 优点 | 风险 |
|---|---|---|---|
| 稠密奖励 | 每一步都有连续反馈 | 学得快 | 可能把策略引到捷径 |
| 稀疏奖励 | 成功或失败时才给信号 | 目标干净 | 探索困难 |
| 混合奖励 | 稠密引导 + 稀疏成功 | 常用折中 | 权重需要调 |

Isaac Lab 的大量任务使用稠密奖励或混合奖励。完全稀疏奖励即使有大规模并行，也常常需要额外探索技巧。

## Locomotion 奖励结构

四足速度跟踪任务通常由四类奖励组成：

| 类别 | 例子 | 目的 |
|---|---|---|
| 跟踪 | 线速度、角速度跟踪 | 按命令运动 |
| 稳定 | 高度、朝向、非期望接触 | 不摔、不撞 |
| 平滑 | 动作变化、关节加速度 | 动作自然 |
| 能耗 | 力矩、功率、关节速度 | 避免暴力控制 |

典型跟踪项：

```python
def track_lin_vel_xy(env):
    command = env.command_manager.get_command("base_velocity")[:, :2]
    actual = env.scene["robot"].data.root_lin_vel_b[:, :2]
    error = torch.sum(torch.square(command - actual), dim=1)
    return torch.exp(-error / 0.25)
```

指数核的好处是奖励有界，误差越小奖励越接近 1。

## Manipulation 奖励结构

操作任务常按阶段拆：

```text
接近物体 -> 对齐夹爪 -> 抓住 -> 抬起 -> 移到目标 -> 放下
```

示例：

```python
def approach_object(env):
    ee_pos = env.scene["robot"].data.body_pos_w[:, env.ee_body_id]
    obj_pos = env.scene["object"].data.root_pos_w
    dist = torch.norm(ee_pos - obj_pos, dim=1)
    return 1.0 - torch.tanh(5.0 * dist)

def lift_object(env, min_height: float):
    obj_height = env.scene["object"].data.root_pos_w[:, 2]
    return (obj_height > min_height).float()

@configclass
class RewardsCfg:
    approach = RewTerm(func=approach_object, weight=1.0)
    lift = RewTerm(func=lift_object, weight=5.0, params={"min_height": 0.2})
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-0.01)
```

后段任务的权重通常更高，否则策略可能只学会“接近物体”而不真正完成任务。

## 常用塑形函数

```python
# 跟踪误差：误差越小越接近 1
reward = torch.exp(-error / sigma)

# 距离奖励：大距离时饱和，避免远距离主导梯度
reward = 1.0 - torch.tanh(scale * distance)

# 线性裁剪：简单约束
reward = torch.clamp(1.0 - error / max_error, min=0.0)
```

| 函数 | 适合 |
|---|---|
| `exp(-error / sigma)` | 速度跟踪、位置跟踪 |
| `1 - tanh(scale * distance)` | 接近、对齐 |
| `clamp` | 高度、限位、阈值型条件 |

每个奖励函数的输出尽量保持在可理解的范围内，再用 `weight` 调相对重要性。

## 看日志调奖励

训练时不要只看 mean reward。更重要的是看每个奖励项的分项曲线。

```text
Episode_Reward/track_lin_vel_xy
Episode_Reward/action_rate
Episode_Reward/joint_torques
Episode_Termination/time_out
```

如果总奖励上升但行为很奇怪，通常说明某个 shaping 项被策略利用了。此时要做消融：把可疑项权重设为 0，重新训练、跑一小段，看行为是否恢复。

## 常见失败模式

| 现象 | 可能原因 | 调整 |
|---|---|---|
| 策略站着不动 | 惩罚太大，正向奖励太弱 | 降低能耗 / 动作惩罚 |
| 策略剧烈抖动 | 缺少平滑惩罚 | 增加 `action_rate_l2` |
| 只接近不抓取 | 前段奖励太高 | 提高后段成功奖励 |
| 抓住后不移动 | lift / place 奖励缺失或太弱 | 增加阶段奖励 |
| 四足拖脚 | 缺少足端时序或接触奖励 | 加 feet air time |
| 奖励高但失败多 | reward 与 termination 目标不一致 | 对齐成功/失败定义 |

## 小结

- 奖励由多个 `RewTerm` 加权组成，每项返回 `(num_envs,)`。
- 先写最小可行奖励，再逐项增加塑形项。
- Locomotion 常拆成跟踪、稳定、平滑、能耗；manipulation 常拆成多阶段奖励。
- 调奖励要看分项日志和行为录像，必要时做消融。

## 参考资料

- Isaac Lab Reward Terms. https://isaac-sim.github.io/IsaacLab/
- Rudin et al., "Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning", CoRL 2021.

## 导航

- 上一页：[动作与控制器](03-controllers.md)
- 返回目录：[任务逻辑配置](../04-task-logic.md)
- 下一页：[终止与课程](05-termination-and-curriculum.md)
