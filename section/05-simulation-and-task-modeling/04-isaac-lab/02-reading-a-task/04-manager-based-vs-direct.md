# Manager-based vs Direct

Isaac Lab 不是只能用一种方式写环境。最常见的是 Manager-based，另一种是 Direct。两者都能训练 RL，但组织方式不同。

## 本节目标

本节围绕下面几个问题展开：

1. Manager-based 和 Direct 两种写法的根本区别是什么？
2. 各自适合什么任务，该怎么按规则选？
3. 同样要改 reward，这两种写法分别该动哪里？

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-manager-vs-direct.svg" alt="Manager-based 与 Direct 两种工作流对比" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">Manager-based 把任务拆成配置块和 Manager；Direct 把核心逻辑直接写进环境类方法。</figcaption>
</figure>

## 一句话区别

```text
Manager-based：声明任务由哪些块组成，让框架按 MDP 循环调用。
Direct：直接实现环境类的方法，手写 observation、reward、done、reset。
```

这不是“高级和低级”的区别，而是“组合式”和“手写式”的区别。

## Manager-based

Manager-based 的典型配置长这样：

```python
@configclass
class MyEnvCfg(ManagerBasedRLEnvCfg):
    scene = MySceneCfg()
    observations = ObservationsCfg()
    actions = ActionsCfg()
    commands = CommandsCfg()
    rewards = RewardsCfg()
    terminations = TerminationsCfg()
    events = EventCfg()
```

优点：

- 每个模块职责清楚，适合教学和团队协作；
- observation、reward、event 可以组合和复用；
- 命令行覆盖配置方便，适合做实验；
- 更容易加入 domain randomization、curriculum、recorder；
- 官方许多新任务都采用这种组织方式。

缺点：

- 初看时不容易找到“主循环”；
- 配置类层级多，需要习惯跳转；
- 非标准逻辑可能写起来绕。

## Direct

Direct 工作流把关键逻辑写在环境类方法里：

```python
class MyEnv(DirectRLEnv):
    def _setup_scene(self):
        ...

    def _pre_physics_step(self, actions):
        self.actions = actions

    def _apply_action(self):
        self.robot.set_joint_position_target(self.actions)

    def _get_observations(self):
        return {"policy": obs}

    def _get_rewards(self):
        return reward

    def _get_dones(self):
        return terminated, truncated

    def _reset_idx(self, env_ids):
        ...
```

优点：

- 控制流直观，所有核心逻辑在一个类里；
- 适合从 Isaac Gym / IsaacGymEnvs 迁移旧任务；
- 对特殊任务、非标准状态机、多智能体逻辑更灵活；
- 少一些 Manager 抽象层。

缺点：

- observation、reward、reset 容易耦合在一起；
- 复用和配置覆盖不如 Manager-based 顺滑；
- 大任务容易变成一个很长的环境类；
- 初学者容易把所有逻辑写成“能跑但难维护”的脚本。

## 选择规则

| 场景 | 建议 |
|---|---|
| 新写一个标准机器人学习任务 | Manager-based |
| 课程学习、想读懂官方任务结构 | Manager-based |
| 需要频繁改 observation、reward、event | Manager-based |
| 需要记录数据、做模仿学习流水线 | Manager-based 优先 |
| 从 Isaac Gym 迁移已有 Direct 风格任务 | Direct |
| 任务控制流很特殊，Manager 表达很绕 | Direct |
| 多智能体、协作/对抗、agent dict 接口 | DirectMARLEnv 或专门 MARL 工作流 |

初学阶段的规则很简单：**拿不准就用 Manager-based**。

## 两种写法如何读

读 Manager-based：

```text
gym.register -> env_cfg -> scene / observations / actions / rewards / terminations / events -> mdp 函数
```

读 Direct：

```text
gym.register -> Env 类 -> _setup_scene -> _pre_physics_step / _apply_action
             -> _get_observations / _get_rewards / _get_dones / _reset_idx
```

读法不同，关注点也不同。Manager-based 先看配置块，Direct 先看类方法。

## 修改 reward 要动哪里

如果只是增加一个奖励项：

- Manager-based：通常加一个 `RewTerm`，或写一个 reward 函数后挂到 `RewardsCfg`；
- Direct：通常进入 `_get_rewards()`，手动把新项写进 reward 计算。

如果只是增加一个 reset 随机化：

- Manager-based：通常加一个 `EventTerm`；
- Direct：通常修改 `_reset_idx()`。

如果只是增加一个 observation：

- Manager-based：加一个 `ObsTerm`；
- Direct：修改 `_get_observations()`。

这就是两种工作流的核心差异：Manager-based 把修改点分散到对应配置块，Direct 把修改点集中到环境类方法。

## 小结

- Manager-based 是声明式、组合式，适合课程主线和大多数新任务。
- Direct 是命令式、手写式，适合特殊逻辑、旧任务迁移和某些多智能体场景。
- 初学阶段优先 Manager-based，因为它能把任务拆成 scene、observation、action、reward、termination、event 等清晰部件。
- 读任务时先判断入口：`ManagerBasedRLEnv` 还是 `DirectRLEnv`，再选择对应阅读路线。

## 参考资料

- Isaac Lab Core Concepts. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab Environments API. https://isaac-sim.github.io/IsaacLab/

## 导航

- 上一页：[拆解 reach 任务](03-walkthrough-reach.md)
- 返回目录：[任务结构与 Manager 系统](../02-reading-a-task.md)
- 下一页：[场景与机器人资产](../03-scene-and-robot.md)
