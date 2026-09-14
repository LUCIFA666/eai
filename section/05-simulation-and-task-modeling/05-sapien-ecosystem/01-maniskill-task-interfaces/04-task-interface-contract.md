# 任务接口契约

上一页的最小代码看起来只有几行，但里面已经藏着一个任务的“契约”。在机器人学习里，任务不是只由名字决定的。`PickCube-v1` 告诉我们要做抓方块任务；但策略到底看到状态还是图像，用末端位姿控制还是关节控制，用 dense reward 还是 sparse reward，这些都会改变训练和评测的含义。

因此，读 ManiSkill 任务时要抓住五件事：`env_id`、`obs_mode`、`control_mode`、`reward_mode` 和 `success`。

## 五件套

| 字段 | 回答的问题 | PickCube 里的例子 |
|---|---|---|
| `env_id` | 做什么任务？ | `PickCube-v1`，抓起方块并放到目标附近 |
| `obs_mode` | 策略看到什么？ | `state`、`rgbd` |
| `control_mode` | 动作怎样作用到机器人？ | `pd_ee_delta_pose` |
| `reward_mode` | 学习算法得到什么训练信号？ | dense / sparse 等模式 |
| `success` | 这次任务是否真的完成？ | `info["success"]` |

同一个 `env_id` 下，换 `obs_mode` 会改变观测结构；换 `control_mode` 会改变动作语义和动作维度；换 `reward_mode` 会改变训练信号。它们都应该被记录下来，不能只写“我跑了 PickCube”。

这五件事定义的是任务语义。换到别的仿真后端时，最先要对齐的也不是文件格式或渲染效果，而是这些语义是否一致：是不是同一个任务，策略是不是看到同一类信息，动作接口是不是同一种含义，成功判定是不是来自同一组条件。

## reward 和 success

reward 和 success 最容易被混用。reward 负责“怎么引导学习”，success 负责“这次任务算不算完成”。训练曲线可以看 reward，评测表格应该看 success；两者都要记录，但不能互相替代。

以 PickCube 为例，`info` 里通常不只一个最终布尔值，还会包含若干子条件：

```text
is_grasped
is_obj_placed
is_robot_static
success
```

这些子条件比最终成功值更适合排查失败。没有抓住、没有放到目标、机器人没有停稳，对应的是不同问题。一个高质量的评测记录，不应该只写“失败”，还应该尽量说明失败卡在哪一步。

## control mode 为什么重要

`control_mode` 决定 action 的含义。末端位姿增量控制、末端位置增量控制、关节位置控制，看起来都叫“动作”，但动作维度和控制直觉完全不同。写策略网络、录制数据或迁移到其他平台时，必须记录当时使用的控制模式。

一份可复盘的实验记录至少应该写清：

```text
env_id
seed
obs_mode
control_mode
reward_mode
action_space
observation_space
info keys
success 子条件
```

这份记录不是给机器看的格式，而是提醒读者：一个任务的可复现性来自接口契约，而不只是来自一个环境名。

## 小结

- 一个 ManiSkill 任务由 `env_id`、`obs_mode`、`control_mode`、`reward_mode` 和 `success` 共同定义。
- reward 是训练信号，success 是完成判定。
- 控制模式会影响 action 语义和维度。
- 记录 `info` 子条件能让失败分析更清楚。

## 导航

- 上一页：[PickCube 最小闭环](03-pickcube-minimal-loop.md)
- 返回上级：[ManiSkill 任务接口与 PickCube 实战](../01-maniskill-task-interfaces.md)
- 下一页：[观测与渲染](05-observation-rendering.md)
