# 下游衔接与边界

学完 PickCube 的最小闭环之后，读者应该已经能看懂一个 ManiSkill 任务的基本形状：环境 ID 指定任务，`obs_mode` 指定策略输入，`control_mode` 指定动作语义，reward 提供训练信号，`info["success"]` 提供完成判定，batch 维让同一套接口可以扩展到并行训练。

这正是 ManiSkill 对后续学习的价值。它不只是一个 demo 集合，而是一套标准操作任务接口。读懂这套接口之后，再去接 RL、IL、VLA、benchmark 或其他仿真平台时，才知道哪些信息必须保留下来。

## 接到 RL

强化学习首先需要环境、动作空间、观测空间和 reward。ManiSkill 已经把这些整理成 Gymnasium 风格的接口，并提供批量环境能力。接 RL 库时，最先要确认的是：训练库期待单环境接口还是批量张量接口，是否需要 `CPUGymWrapper`，以及 reward、terminated、truncated、success 的 shape 是否符合预期。

但 ManiSkill 不会替你完成完整训练工程。日志、评估协议、多 seed 统计、模型保存和失败分析，仍然要由下游训练代码负责。

## 接到 IL 和 VLA

模仿学习和 VLA 更关心数据。一个 episode 里应该记录什么，不只取决于视频是否好看，还取决于策略输入和动作语义是否完整：

```text
env_id
seed
obs_mode
control_mode
action_space
observation_space
sensor_data / sensor_param
success 和子条件
```

对于 IL，专家轨迹、动作对齐和回放检查很重要。对于 VLA，还要额外处理语言指令、多模态输入格式和数据组织方式。ManiSkill 提供的是任务和观测入口，不等于完整数据集规范。

## 接到 benchmark

评测时不能只保存视频。视频可以告诉我们任务现象是否可见，但不能单独说明策略成功率、观测 shape、tensor device 或失败原因。

更可靠的证据应该分层保存：

| 证据 | 能说明什么 | 不能说明什么 |
|---|---|---|
| rollout 视频 | 任务现象可见、渲染链路可用 | 策略成功、观测 shape 正确 |
| summary JSON | 配置、shape、reward、success、版本 | 画面是否符合直觉 |
| vector JSON | batch shape、device、并行接口 | 单个 episode 成功率 |
| wrapper 输出 | 传统 Gym 兼容接口 | GPU 并行性能 |

训练时可以优化 reward；评测时应该记录 success。保存 `success` 的子条件，能帮助区分“没抓住”“没放到目标”“机器人没停稳”等不同失败。

## 和其他平台的边界

ManiSkill、Genesis、Isaac Sim 和 Isaac Lab 都和机器人仿真有关，但它们的重点不同。

| 平台 | 更适合 |
|---|---|
| ManiSkill | 标准化物体操作任务、benchmark、RL / IL 入门、GPU batch |
| Genesis | 自定义实验任务、多物理、原子动作和后端探索 |
| Isaac Sim | USD 资产、高保真相机 / 传感器、ROS 2、合成数据和系统工程 |
| Isaac Lab | Isaac Sim 之上的机器人学习任务、并行训练、Manager 工作流 |

如果目标是学习标准任务接口，ManiSkill 很合适。如果目标是构建自定义实验场景、迁移复杂资产或研究多物理，Genesis 更自然。如果目标是 USD 资产、高保真传感器和 ROS 2 系统集成，Isaac Sim 更合适。

换句话说，ManiSkill 帮我们把“一个任务应该怎样暴露给学习算法”讲清楚，但它不会自动解决所有后端迁移问题。换到 Genesis、Isaac Sim 或其他系统时，仍然要重新核对资产、坐标、控制器、相机、接触行为和成功判定来源。

## 小结

- ManiSkill 是学习标准操作任务接口的好入口。
- RL、IL、VLA 和 benchmark 都要先把观测、动作、成功判定和日志记录清楚。
- 视频不是完整证据；shape、device、success 和子条件同样重要。
- ManiSkill 不替代 Genesis 或 Isaac Sim，它们解决的是不同层级的问题。

## 导航

- 上一页：[Batch、GPU 与 Wrapper](06-batch-gpu-wrapper.md)
- 返回上级：[ManiSkill 任务接口与 PickCube 实战](../01-maniskill-task-interfaces.md)
- 下一页：[任务内部怎么读](08-read-a-task.md)
