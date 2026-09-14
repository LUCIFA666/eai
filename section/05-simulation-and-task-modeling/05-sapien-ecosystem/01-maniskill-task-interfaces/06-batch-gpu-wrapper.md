# Batch、GPU 与 Wrapper

传统 Gym 教程通常从单环境开始：一次只有一个世界，`obs` 是一个向量，`reward` 是一个数字，`done` 是一个布尔值。ManiSkill 的接口更偏向批量环境。即使只创建一个环境，返回值也可能保留 batch 维。

这不是多出来的错误维度，而是为了让同一套接口自然扩展到 `num_envs=16`、`num_envs=1024` 这类并行训练场景。

## batch 维从哪里来

传统单环境里，常见返回形状是：

```text
obs: (42,)
reward: float
done: bool
```

ManiSkill 批量接口下，即使 `num_envs=1`，也可能看到：

```text
obs: (1, 42)
reward: (1,)
done: (1,)
```

这里的第一维是环境数量。把 `num_envs` 改成 16，它会自然变成：

```text
obs: (16, 42)
reward: (16,)
done: (16,)
```

因此，写训练代码前不要只记住“PickCube 是 42 维状态”。更准确的说法是：单个 PickCube state 可能是 42 维，但当前环境实际返回的 tensor 还会带上并行环境维度。

## single space 和 wrapper

很多 ManiSkill 批量环境会提供 `single_observation_space` 和 `single_action_space`，用来查看单个环境的输入输出形状。它们对写策略网络很有帮助，因为策略通常关心的是单个样本的维度，而训练循环再负责 batch。

经过 wrapper 后要重新检查 space。wrapper 可能去掉 batch 维，也可能把 tensor 转成 NumPy 数组或 Python 标量。不要凭记忆写 shape，应该以当前环境实际暴露的 space 为准。

## GPU vector probe 看什么

`maniskill_pickcube_vector.json` 这类输出里，最值得看的不是视频，而是 shape 和 device：

| 字段 | 它说明什么 |
|---|---|
| `num_envs` | 实际创建了多少个并行环境 |
| `obs_shape` | 观测是否带正确 batch 维 |
| `reward_shape` | reward 是否按环境返回 |
| `done_shape` | done 是否按环境返回 |
| `reward_device` | reward 张量在哪个 device 上 |

这些字段能说明 batch 接口是否真的跑通。视频只能说明任务现象可见，不能证明训练接口的 shape 和 device 正确。

仓库随附的 vector 产物来自 `num_envs=16` 的 probe。里面的 `obs_shape` 是 `[16, 42]`，`reward_shape` 和 `done_shape` 都是 `[16]`，`reward_device` 是 `cuda:0`。这组数字比“显卡存在”更有意义：它说明这次返回值真的按 16 个环境组织，并且 reward 张量在 GPU 上。

## CPUGymWrapper 解决什么

有些下游库或旧代码只接受传统 Gym 单环境接口：NumPy 数组、Python float、Python bool。此时可以对 `num_envs=1` 的环境套 `CPUGymWrapper`，把 `(1, 42)` 变回 `(42,)`，把 reward、done、success 等张量或数组变成普通标量。

它解决的是兼容性问题，不是加速问题。想做大规模并行训练时，应该保留 ManiSkill 的批量张量接口，而不是把它包回传统单环境形态。

## 小结

- `num_envs=1` 也可能保留 batch 维，`(1, 42)` 不是状态维度错误。
- `42` 是单个环境的状态维度，前面的 `1` 或 `16` 是并行环境数量。
- GPU batch 要看 shape 和 device，不只看画面。
- `CPUGymWrapper` 适合兼容传统单环境代码，不适合并行训练。

## 导航

- 上一页：[观测与渲染](05-observation-rendering.md)
- 返回上级：[ManiSkill 任务接口与 PickCube 实战](../01-maniskill-task-interfaces.md)
- 下一页：[下游衔接与边界](07-downstream-boundaries.md)
