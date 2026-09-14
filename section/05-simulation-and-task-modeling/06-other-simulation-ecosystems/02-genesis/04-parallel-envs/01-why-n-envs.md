# 为什么需要 n_envs

前面几页默认都在讲一个场景、一个机器人、一条控制循环。但机器人学习通常不是这样训练的。强化学习、模仿学习和大规模采样需要很多环境一起跑，Genesis 的一个重要入口就是批量环境。

这一页只讲并行环境的第一层：`scene.build(n_envs=...)` 做了什么，为什么 action 要多一个批量维度，以及初学者如何验证批量控制是否真的发生。本页暂不展开 reward、reset、训练库和最高吞吐，这些放到后面的并行记录页和任务章节里再处理。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么机器人学习需要一批环境，而不是一个环境？
2. `scene.build(n_envs=...)` 在概念上做了什么？
3. 批量动作（batch action）的形状应该怎样理解？
4. 官方 showcase 里的批量素材能证明什么、不能证明什么？
5. 第一次写批量脚本应该怎样验收？

## 为什么要一批环境

单环境适合调试。只盯着一个机器人，就能观察它有没有穿模、有没有抖动、动作方向对不对。

训练策略时，单环境就太慢了。一个策略需要看到大量状态、动作和结果，才能估计哪些动作更好。并行环境的核心思路是：**用同一套规则，同时跑很多份任务**。这些任务结构相同，但初始状态、随机扰动、目标位置或进度可以不同。训练算法需要的不是一个故事，而是一批样本。

## n_envs 是批量环境入口

Genesis 的并行环境入口很直接：

```python
B = 20
scene.build(n_envs=B, env_spacing=(1.0, 1.0))
```

这里的 `B` 是环境数量。可先把它理解成：同一个场景被复制成 `B` 份，每份都有独立状态，可以一起推进。它和向量化环境里的 `num_envs` 在学习直觉上相通，都是从“一个环境”切换到“一批环境”。

`env_spacing` 主要是为了可视化时把环境摆开，避免它们在画面里重叠。它不是任务本身的物理参数。真正影响训练吞吐的是环境数量、物理复杂度、后端、渲染开销和控制逻辑。

第一次实验不要直接上千环境。建议从小批量开始：

```python
B = 4
```

或：

```python
B = 8
```

小批量更容易看清形状错误，也更容易确认每个环境是否真的收到了不同动作。

## 动作多一个批量维度

本页后面的 `torch.*` 片段默认已经在脚本顶部写过 `import genesis as gs` 和 `import torch`，并且前面已经执行过 `gs.init(...)`，所以可以使用 `gs.device`。第一次练习时，可以先把批量大小固定为 `B = 8`。

单环境里，一个 9 dof Franka 的位置目标可以是：

```python
target = torch.zeros(9, device=gs.device)
```

批量环境里，需要给每个环境一份目标，所以形状变成：

```python
B = 8
targets = torch.zeros(B, 9, device=gs.device)
```

如果所有环境先用同一个目标，可以复制：

```python
B = 8
one_target = torch.tensor([0, 0, 0, -1.0, 0, 1.0, 0, 0.02, 0.02], device=gs.device)
targets = torch.tile(one_target, (B, 1))
franka.control_dofs_position(targets)
```

这个 `[B, 9]` 是并行环境最重要的直觉。以后读取状态、组织 observation，以及在任务封装层计算 reward / done，也会围绕类似的环境维展开。

```text
单环境 action: [num_actions]
批量 action: [num_envs, num_actions]
```

如果已经熟悉 Gymnasium vector env、Brax 或其他批量环境，可以把它和 `num_envs` 对齐理解：第一维通常是环境数量。但这里还没有进入完整 RL 任务框架，Genesis 只是先给出了批量仿真的场景接口。

有时只需要控制其中几个环境。Genesis 里可以用 `envs_idx` 表示“被选中的环境编号”。这时目标张量的第一维不是总环境数，而是被选中环境的数量。具体写法放到 [envs_idx 与部分环境控制](03-envs-idx.md) 单独讲；本页先记住这个关系：目标数量要和 `len(envs_idx)` 对齐。

## 每个环境可以有不同目标

批量环境不是只能复制完全一样的动作。更常见的是每个环境的目标也可以不同。

下面这段继续沿用本页默认上下文：脚本顶部已经 `import genesis as gs` 和 `import torch`，`gs.device` 已经由 `gs.init(...)` 设置好。

```python
B = 8
targets = torch.zeros(B, 9, device=gs.device)
targets[:, 3] = -1.0
targets[:, 5] = 1.0
targets[:, 0] = torch.linspace(-0.4, 0.4, B, device=gs.device)

franka.control_dofs_position(targets)
```

这段代码让不同环境的 `joint1` 目标不同。可视化时，应能看到一排机器人动作略有差异；保存状态时，也应该看到批量维度里的值不同。

这一步很适合做验收，因为它能确认脚本不是只把同一个单环境脚本跑了很多次，而是真的在用批量张量表达多环境动作。

官方 showcase 里，`sim_02_heterogeneous_envs` 和 `sim_15_batched_ik` 都可以作为这一直觉的视觉入口：前者展示批量环境中对象可以不同，后者展示 IK 也能批量化。它们在 `runs/genesis_readme_showcase_canonical_20260608_055500/` 里都有 `1060x580` 预览、视频、summary 和日志。

这些素材能证明“官方批量示例可以被真实跑出动态结果”，但不能单独证明配套脚本已经正确组织了 action、状态读取、任务封装层 observation / reward / done 和 reset。本页的 `targets.shape == [B, 9]` 才是第一层结构证据：画面负责建立直觉，张量形状负责解释语义。

## 第一轮只验收形状和语义

初学者容易把 `n_envs` 理解成“开了很多线程”。更准确地说，`n_envs` 是仿真 API 层面的批量环境概念。底层怎么调度到 CPU、GPU、编译后端和设备内存，是实现细节。

第一轮验收更应该强调形状和语义：

| 概念 | 重点 |
|---|---|
| `n_envs` | 有多少份环境状态 |
| 批量动作（batch action） | 每个环境一行动作 |
| 批量状态读取 | 每个环境一行状态或一组状态 |
| 任务封装层 observation | 每个环境一行任务观测 |
| 任务封装层 reward | 每个环境一个奖励 |
| 部分环境 reset | 通过结束环境的索引或 mask 重置对应环境 |

理解这些，比一开始追求最高 steps/s 更重要。本页的验收只需要五项：

| 验收项 | 通过标准 |
|---|---|
| 小批量能 build | `n_envs=4` 或 `8` 能完成 `scene.build()` |
| 批量动作形状正确 | 9 dof 机器人目标是 `[B, 9]` |
| 不同环境可不同动作 | 给不同环境不同 `joint1` 目标，结果能区分 |
| 能关闭 viewer 跑 | 无界面批量 step 不依赖窗口 |
| 记录运行配置 | 保存环境数、步数、后端和是否渲染 |

后面做正式训练时，才逐步增加 `n_envs`、换 GPU 后端、减少渲染开销、组织任务封装层的 observation / reward / reset，并考虑是否接到具体的 RL 任务框架。

## 读完应能回答

1. 为什么 `[B, 9]` 里的 `B` 是环境维，而不是时间维或机器人数量？
2. `sim_15_batched_ik` 的视频能证明什么，为什么还不能替代 `05_parallel_envs.json`？
3. 如果所有环境收到完全相同动作，如何证明脚本真的按批量环境运行？
4. 第一轮并行实验为什么先用 `n_envs=4` 或 `8`，而不是直接追求最大吞吐？

## 小结

- `n_envs` 表示一批环境，不是一个环境。
- 批量动作的第一维是环境数量，例如 Franka 位置目标可以是 `[B, 9]`。
- 第一次并行实验用小批量，先验证形状、动作差异和无界面 step。
- showcase 视频只能证明官方批量示例能跑出动态素材，配套脚本还要用张量形状证明语义。
- Genesis 的并行直觉和向量化环境的 `num_envs` 相通，但 Genesis 本身不等于完整 RL 任务框架。

## 参考资料

- Genesis World Documentation, Parallel Simulation. https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/parallel_simulation.html

## 导航

- 上一页：[并行环境](../04-parallel-envs.md)
- 返回目录：[并行环境](../04-parallel-envs.md)
- 下一页：[批量动作与批量状态](02-batched-action-state.md)
