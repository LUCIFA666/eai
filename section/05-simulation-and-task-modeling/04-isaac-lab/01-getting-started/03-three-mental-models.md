# 三个理解视角

上一页你已经看到训练命令、`steps/s`、`Mean reward`、`--task`、`--num_envs` 这些词。现在再回头解释它们背后的结构。Isaac Lab 初学者最容易卡住的地方，不是 API 多，而是它和普通单环境仿真脚本的思维方式不同。

## 本节目标

本节围绕下面几个问题展开：

1. 这一页要建立哪几个理解视角？
2. 这些模型分别对应代码里的哪些对象、配置或日志？
3. 初学者最容易把哪些概念混在一起？
4. 读后续代码时，应该按什么路线定位问题？

这里的“理解视角”不是抽象口号，而是读代码和排错时反复使用的内部地图。Isaac Lab 的起步阶段，最重要的是先建立三个这样的内部地图。

## 并行环境

普通仿真脚本里，你常常只控制一个机器人：读状态、算动作、推进一步。Isaac Lab 的默认思路不同：它同时控制很多个环境。训练时可能有 1024、4096 甚至更多个 CartPole 在 GPU 上一起运行。

所以所有核心张量的第一维通常都是 `num_envs`：

```python
obs, _ = env.reset()
obs["policy"].shape      # torch.Size([4096, 4])
action.shape             # torch.Size([4096, 1])
reward.shape             # torch.Size([4096])
```

这意味着你写 observation、reward、termination 时，不能再脑补“一个环境算一次”。你要一次性处理所有环境：

```python
# 好：一次计算所有环境的距离
distance = torch.norm(target_pos - ee_pos, dim=-1)

# 不推荐：用 Python for 逐个环境算，会破坏 GPU 并行吞吐
for env_id in range(num_envs):
    ...
```

类比一下：你不是在批一份试卷，而是在同时批 4096 份同样结构的试卷。题目一样，学生不同；计算规则一样，但数据第一维是学生数量。

**预判困惑**：第一次看到 reward 函数里全是 `torch.sum(..., dim=-1)`、`torch.norm(..., dim=-1)`，没有 `for env in ...`，这是正常的。Isaac Lab 的吞吐来自批量张量运算。

## 配置驱动

Isaac Lab 的 Manager-based 任务很少让你手写完整主循环。你更多是在写一组配置，告诉框架“场景里有什么、智能体看到什么、能做什么、什么算好、什么时候结束”。

一个简化骨架如下：

```python
from isaaclab.utils import configclass

@configclass
class MyEnvCfg(ManagerBasedRLEnvCfg):
    scene = MySceneCfg(num_envs=4096)
    observations = ObservationsCfg()
    actions = ActionsCfg()
    rewards = RewardsCfg()
    terminations = TerminationsCfg()
    events = EventCfg()
```

这些字段背后由不同 Manager 负责：

| 配置块 | 负责什么 |
|---|---|
| `scene` | 放机器人、物体、地面、传感器，并克隆环境 |
| `observations` | 从场景状态中整理策略输入 |
| `actions` | 把策略输出解释成控制命令 |
| `rewards` | 根据状态和目标计算奖励 |
| `terminations` | 判断成功、失败、超时等回合结束条件 |
| `events` | reset、随机化、外部扰动等事件 |

这就是“配置驱动 + Manager”。它牺牲了一点直觉上的直接性，换来模块复用、组合和实验管理。改 reward 时不用动 observation；换机器人时不一定要重写训练脚本；加入域随机化时也不必把主循环翻出来改一遍。

类比：命令式写法像自己下厨，每一步都亲手做；Manager-based 像填一张菜单和配方表，由厨房按标准流程做。刚开始你会觉得“主循环去哪了”，但后面读懂任务时会发现，这种结构让复杂任务更容易维护。

## 仿真到 MDP

强化学习关心的是 MDP：状态、动作、奖励、转移、终止。Isaac Sim 关心的是物理世界：机器人、刚体、关节、碰撞、传感器。Isaac Lab 的工作就是把这两种语言接起来。

| MDP 要素 | Isaac Lab 中对应什么 |
|---|---|
| 状态 | `InteractiveScene` 中的机器人、物体、传感器和缓存数据 |
| 观测 `o_t` | Observation Manager 从状态中取出并拼成策略输入 |
| 动作 `a_t` | Action Manager 把策略输出转换成关节目标或控制命令 |
| 奖励 `r_t` | Reward Manager 根据当前状态和目标计算 |
| 终止 | Termination Manager 判断超时、失败、成功 |
| 重置 | Event / reset 逻辑把环境写回初始分布 |

所以下一部分“任务结构与 Manager 系统”会反复问同一个问题：这段代码属于 MDP 的哪一块？它是在定义状态载体、观测、动作、奖励，还是回合结束？

## Manager-based 和 Direct 怎么选

现在你只需要一个初学者规则：

| 情况 | 建议 |
|---|---|
| 新写任务、课程学习、希望复用组件 | Manager-based |
| 需要组合传感器、奖励、随机化 | Manager-based |
| 从 Isaac Gym 迁移旧任务 | 可能 Direct |
| 逻辑非常特殊、Manager 表达不方便 | Direct |

**拿不准就用 Manager-based**。本课程也以 Manager-based 作为主线，因为它更容易把任务拆成可讲、可查、可复用的部分。

## 下一部分怎么读任务

带着这三个理解视角进入下一部分，读一个 Isaac Lab 任务时不要从某个 reward 函数直接钻进去。建议固定按这条线走：

```text
task id
  -> gym.register
  -> env_cfg
  -> scene
  -> observation / action / reward / termination / event
  -> mdp functions
  -> agent cfg
  -> train.py / play.py
```

这条顺序对应本页的三件事：`task id` 和 `env_cfg` 告诉你任务是怎么声明的，`scene` 和各类 Manager 告诉你物理世界如何翻译成 MDP，`agent cfg` 与训练脚本告诉你这批并行环境怎样交给算法优化。

## 小结

- 并行张量：一次不是跑一个环境，而是跑一批环境；第一维通常是 `num_envs`。
- 配置驱动 + Manager：任务由 scene、observation、action、reward、termination、event 等配置声明出来。
- 仿真到 MDP：Isaac Lab 把 Isaac Sim 的物理场景翻译成强化学习环境。
- 后面读任何任务，都可以先问：这段代码对应哪一个 Manager？它服务于 MDP 的哪一块？

## 参考资料

- Isaac Lab Documentation. https://isaac-sim.github.io/IsaacLab/
- Gymnasium API. https://gymnasium.farama.org/
- RSL-RL. https://github.com/leggedrobotics/rsl_rl

## 导航

- 上一页：[第一次训练](02-first-run-cartpole.md)
- 返回目录：[认识 Isaac Lab](../01-getting-started.md)
- 下一页：[安装与版本对照](04-install-and-versions.md)
