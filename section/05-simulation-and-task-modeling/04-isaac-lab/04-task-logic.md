# 任务逻辑配置

上一部分解决“给世界放入什么”。这一部分解决“如何在这个世界执行任务”。在 Isaac Lab 里，任务逻辑通常不是写成一段大函数，而是拆成 observation、sensor、action/controller、reward、termination、curriculum 等配置块。

这部分内容是 Isaac Lab 的核心。scene 只是提供机器人、物体和状态；真正让策略能学习的是任务接口：策略能看到什么、输出什么、什么行为被奖励、什么时候 reset、随机化如何改变初始条件。把这些边界分清楚，比先写一个复杂 reward 更重要。

## 本节目标

本节围绕下面几个问题展开：

1. Isaac Lab 任务逻辑由哪些接口共同组成？
2. observation、action、reward、termination 和 curriculum 之间是什么关系？
3. 为什么先定义输入输出，再写 reward 会更稳？
4. 读一个任务时，应该按什么顺序检查这些配置块？

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [观测设计](04-task-logic/01-observation.md) | 策略输入由哪些项拼成？每一项从哪里读状态？ | `ObservationsCfg`、`ObsTerm`、观测组、噪声、裁剪、`SceneEntityCfg` |
| [传感器](04-task-logic/02-sensors.md) | 相机、射线、接触等传感器如何进入观测？ | `CameraCfg`、`TiledCameraCfg`、`RayCasterCfg`、`ContactSensorCfg` |
| [动作与控制器](04-task-logic/03-controllers.md) | 策略输出是关节目标，还是末端位姿增量？ | 关节空间、差分 IK、OSC、动作尺度 |
| [奖励工程](04-task-logic/04-reward.md) | 多个奖励项如何组合，权重怎么调？ | `RewardsCfg`、`RewTerm`、塑形、消融、日志监控 |
| [终止与课程](04-task-logic/05-termination-and-curriculum.md) | episode 何时结束？任务如何从易到难？ | `TerminationsCfg`、`EventCfg`、`CurriculumCfg`、reset 写状态 |

## 一条固定主线

配置任务逻辑时，建议按这个顺序写：

```text
1. observation：策略需要哪些信息？
2. action/controller：策略输出怎么作用到机器人？
3. reward：什么行为被鼓励，什么行为被惩罚？
4. termination：成功、失败、超时怎么判定？
5. event/curriculum：reset 怎么随机化，难度怎么变化？
```

先写 reward 往往会乱，因为 reward 需要引用 scene、command、sensor 和 action；先把输入输出定义清楚，奖励才有稳定语义。

## 读完本部分后

完成这一部分后，应该能把一个机器人任务拆成可检查的接口：观测是否包含目标，动作是否真的作用到执行器，奖励分项是否和行为一致，终止条件是否过早触发，课程和随机化是否改变了任务难度而不是破坏任务本身。

## 导航

- 上一页：[场景与机器人资产](03-scene-and-robot.md)
- 返回上级：[Isaac Lab](../04-isaac-lab.md)
- 下一页：[训练与评测](05-training.md)
