# 批量动作与批量状态

本页讲并行环境中最重要的形状变化：单环境动作从 `[num_actions]` 变成 `[num_envs, num_actions]`。Genesis 原生场景会先体现为批量控制和批量状态读取；observation、reward 和 done 通常属于后续任务封装层，也要按环境维组织。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么批量动作第一维是环境数量？
2. Franka 的 `[B, 9]` 位置目标应该怎样理解？
3. 批量状态读取和任务封装层的 observation / reward / done 会怎样对应到每个环境？
4. 初学时如何用 shape 检查并行脚本是否写对？

## 第一维是环境

单环境里，Franka 位置目标可以是 `[9]`。批量环境里，目标变成 `[B, 9]`：

下面片段默认已经完成 `import genesis as gs` 和 `scene.build(n_envs=B, ...)`，`franka` 是场景里的机器人实体。完整可运行脚本见 `labs/06_genesis/05_parallel_envs.py`。

```python
import torch

B = 8
targets = torch.zeros(B, 9, device=gs.device)
franka.control_dofs_position(targets)
```

这里的 `B` 就是 `n_envs`。第 `i` 行对应第 `i` 个环境。不要把它理解成时间维，也不要把它理解成机器人数量；它是并行环境维度。

## 用不同目标证明真的批量

配套脚本 `05_parallel_envs.py` 会给不同环境设置不同的第一个关节目标：

下面的片段沿用上一段里的 `import genesis as gs`、`import torch`、`targets`、`B` 和 `gs.device`。

```python
targets[:, 0] = torch.linspace(-0.4, 0.4, B, device=gs.device)
```

摘要里会保存：

```json
{
  "action_shape": [8, 9],
  "joint1_targets": [-0.4, -0.2857, -0.1714, -0.0571, 0.0571, 0.1714, 0.2857, 0.4]
}
```

这比只记录 `n_envs=8` 更有用，因为它证明每个环境不是收到完全相同的动作。

## 和官方 batched IK 对照

`sim_15_batched_ik` 是官方 showcase 里最适合对照本页的素材。它在运行摘要中记录为：

```json
{
  "id": "sim_15_batched_ik",
  "title": "Batched IK",
  "captured_frames": 166,
  "resolution": [1060, 580],
  "duration_seconds": 38.81966059003025,
  "stopped_after_max_frames": true,
  "result": "passed"
}
```

这个结果说明官方 batched IK 示例已经生成可用预览和视频，但它还没有解释 batch 维度。配套脚本 `05_parallel_envs.py` 要补上这部分结构化证据：`action_shape` 证明目标张量是 `[B, 9]`，`joint1_targets` 证明不同环境真的收到不同目标。

<figure class="doc-figure">
<p class="doc-figure-title">并行：批量 IK（batched IK）</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_15_batched_ik.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_15_batched_ik.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/tutorials/batched_IK.py</code>。批量 IK 把 IK 也并行化，建立直觉；但本地脚本仍要用 <code>action_shape=[B, 9]</code> 与不同的 <code>joint1_targets</code> 证明批量语义。</p>
</figure>

所以读 `sim_15_batched_ik` 时要分两层：

| 证据 | 它证明什么 |
|---|---|
| 官方视频和预览图 | 批量 IK 示例可视化跑通 |
| `05_parallel_envs.json` 的 shape 字段 | 证明批量动作的张量语义已经说清楚 |

这两层缺一不可。只有视频，容易停在“看起来很多机器人在动”；只有 shape，没有画面，又缺少直觉。

写报告时可以这样落笔：`sim_15_batched_ik` 证明官方批量 IK 示例能跑到 166 帧，并生成 `1060x580` 预览和视频；`05_parallel_envs.json` 则证明本地脚本生成了 `[8, 9]` 的动作张量，并且 8 个环境的第一个关节目标不同。前者是官方素材运行结果，后者是本地代码验收。

## shape 是第一排错工具

并行环境里，先看 shape：

| 对象 | 单环境 | 批量环境 |
|---|---|---|
| action | `[A]` | `[B, A]` |
| state | `[S]` | `[B, S]` |
| task observation | `[O]` | `[B, O]` |
| task reward | 标量 | `[B]` |
| task done | 布尔值 | `[B]` |

如果 shape 错了，先不要怀疑物理。先把 batch 维度修对。

## 读完应能回答

1. `B=8`、Franka 有 9 个 dof 时，位置目标 shape 应该是什么？
2. 为什么 `joint1_targets` 里保存不同数值，比只保存 `batch=8` 更能说明问题？
3. `sim_15_batched_ik` 的视频能不能单独证明本地批量控制脚本写对了？

## 小结

- 批量环境的第一维是环境数量 `B`。
- `[B, 9]` 表示每个环境一组 Franka dof 目标。
- 官方 batched IK 素材提供直觉，配套摘要里的 `action_shape` 和不同目标负责证明并行逻辑真的生效。

## 导航

- 上一页：[为什么需要 n_envs](01-why-n-envs.md)
- 返回目录：[并行环境](../04-parallel-envs.md)
- 下一页：[envs_idx 与部分环境控制](03-envs-idx.md)
