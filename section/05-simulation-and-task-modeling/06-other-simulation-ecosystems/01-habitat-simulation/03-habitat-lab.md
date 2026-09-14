# Habitat-Lab：任务定义、训练接口与评测指标

目标：理解 Habitat-Lab 如何把 Habitat-Sim 的场景仿真包装成可训练、可评测的具身智能任务，并能分清 config、episode、task、measure 和 baseline 的职责。

如果 Habitat-Sim 回答“世界怎么被仿真”，Habitat-Lab 回答的就是“任务怎么被定义、训练和评测”。它把底层 simulator、场景数据、episode、动作、奖励、指标和训练脚本组织在一起，让我们可以像使用 RL 环境一样和 embodied task 交互。

## Habitat-Lab 的核心对象

一个 Habitat-Lab 实验通常会涉及这些对象：

| 对象 | 作用 | 读实验时要看什么 |
|---|---|---|
| config | 统一管理 simulator、dataset、task、sensor、action、measure 等设置 | yaml 路径、override、版本 |
| dataset | episode dataset，记录任务实例 | split、scene id、目标定义 |
| episode | 单次任务样本 | 起点、目标、场景、最大步数、成功条件相关信息 |
| task | 定义动作、奖励、传感器、终止和指标 | 是 PointNav、ObjectNav 还是 Rearrangement |
| measure | 计算评测指标 | success、SPL、distance_to_goal、rearrangement metrics |
| baseline | 训练或评测策略 | PPO、IL、SensePlanAct、heuristic 等 |

这里最容易混的是 `dataset`。在 Habitat-Sim 里，dataset 常指 scene dataset；在 Habitat-Lab 任务里，dataset 往往指 episode dataset。ObjectNav 的 episode dataset 不是房间 mesh 本身，而是“在哪个房间从哪里出发找什么物体”的任务清单。

## 从 reset / step 看任务接口

Habitat-Lab 对外看起来很像 Gym 环境：

```python
import gym
import habitat.gym

env = gym.make("HabitatRenderPick-v0")
observations = env.reset()

terminal = False
while not terminal:
    action = env.action_space.sample()
    observations, reward, terminal, info = env.step(action)
```

这段代码只能说明环境接口的形状，不能说明实验已经完整。真正写实验记录时，还要说明它用的是哪个 yaml config、哪个 scene dataset、哪个 episode split、哪些 sensor、哪些 metric。

| 问题 | 为什么重要 |
|---|---|
| 这个 env 对应哪个 config？ | config 决定场景、任务、传感器、动作和指标 |
| `observations` 里有哪些键？ | RGB、depth、semantic、goal sensor 会改变策略能力 |
| `action_space` 是什么？ | 离散导航动作和连续控制不可直接比较 |
| `reward` 怎么定义？ | reward 是训练信号，不等于最终评测指标 |
| `info` 里有哪些 measure？ | 最终报告通常看 success、SPL 等指标 |

## Task：任务不是环境名字

Habitat-Lab 的 task 定义了智能体面对的目标形式和成功条件。PointNav、ObjectNav、ImageNav、Rearrangement 都是不同任务，不只是不同名字。

| 任务 | 目标 | 关键区别 |
|---|---|---|
| PointNav | 目标点或相对坐标 | 主要考察几何导航 |
| ObjectNav | 物体类别 | 需要语义探索和目标识别 |
| ImageNav | 目标图像 | 需要视觉匹配和视角理解 |
| Rearrangement | 物体状态 | 需要导航、操作和物理交互 |

Task 会影响传感器、动作空间、奖励、终止条件和指标。如果任务变了，但还沿用原来的评测解释，很容易得出错误结论。

## Measure：指标决定结果怎么被解释

| 指标 | 回答的问题 | 注意点 |
|---|---|---|
| success | 任务是否成功完成 | 只看成功率可能忽略路径效率 |
| SPL | 成功且路径是否接近最短 | 导航任务常用，依赖 shortest path |
| distance_to_goal | 离目标还有多远 | 失败 episode 中也有信息量 |
| reward | 训练时每步得到什么反馈 | 不能直接当成 benchmark 指标 |
| rearrangement success | 物体是否到目标状态 | 需要看子目标和物体状态，不只看 agent 位置 |

SPL 是新手最容易跳过的指标。它可以粗略理解为：成功到达目标当然好，但如果路径绕了很远，得分会下降。这样能避免只看 success 时出现“到是到了，但走得很差”的问题。

## Baseline：不是任务本身

Habitat-Lab 里会看到 PPO、IL、DD-PPO、SensePlanAct 等 baseline。它们是完成任务的方法，不是任务本身。

```text
ObjectNav task
  -> random policy
  -> PPO policy
  -> imitation learning policy
  -> map-based planner
  -> VLM / LLM assisted pipeline
```

因此写实验时不要说“我用了 Habitat 的 PPO，所以这是 ObjectNav”。更严谨的说法是：在某个 ObjectNav task config 和某个数据 split 上，用某种 policy 训练或评测，并报告某些指标。

## 调试 Habitat-Lab 的顺序

Habitat-Lab 出问题时，建议按下面顺序查：

1. config 是否加载的是你以为的那个文件。
2. dataset path 是否存在，episode split 是否正确。
3. episode 里的 scene id 是否能被 Habitat-Sim 找到。
4. observation keys 和 shape 是否符合 policy 输入。
5. action space 是否和 policy 输出一致。
6. measure 是否真的被启用。
7. evaluation 是否用的是正确 split，而不是训练 split。

## 本页小结

Habitat-Lab 是 Habitat 的任务和实验层。它把 scene、episode、task、measure、baseline 和训练接口组织起来。学习 Habitat-Lab 的关键不是记住某个 API，而是能读懂一个实验配置：数据从哪里来，任务目标是什么，agent 看见什么，能做什么动作，最终用什么指标判断好坏。

## 导航

- 上一页：[Habitat-Sim](02-habitat-sim.md)
- 返回：[Habitat 简介](../01-habitat-simulation.md)
- 下一页：[常见数据集](04-common-datasets.md)

## 进一步阅读可以看：

- [Habitat-Lab documentation](https://aihabitat.org/docs/habitat-lab/)
- [Habitat-Lab GitHub](https://github.com/facebookresearch/habitat-lab)
- [Habitat-Lab datasets](https://github.com/facebookresearch/habitat-lab/blob/main/DATASETS.md)