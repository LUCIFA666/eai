# envs_idx 与部分环境控制

本页讲如何只控制批量环境中的一部分环境。`envs_idx` 的关键点是：目标张量的 batch 维度要和被选中的环境数量一致。

## 本节目标

本节围绕下面几个问题展开：

1. `envs_idx` 表示什么？
2. 只控制 3 个环境时，为什么目标张量应该是 `[3, action_dim]`？
3. `envs_idx` 和总环境数量 `n_envs` 有什么区别？
4. 部分环境 reset 或控制时容易出现哪些 shape 错误？

## envs_idx 是被选中的环境编号

如果场景有 `B=8` 个环境，有时只需要控制其中 3 个。此时可以传 `envs_idx`：

下面片段默认已经完成 `import genesis as gs` 和 `scene.build(n_envs=8, ...)`，`franka` 是批量场景里的机器人实体；它是部分环境控制的扩展片段，不是当前 `05_parallel_envs.py` 的完整源码。

```python
import torch

envs_idx = torch.tensor([1, 5, 7], device=gs.device)
targets = torch.zeros(3, 9, device=gs.device)
franka.control_dofs_position(targets, envs_idx=envs_idx)
```

这里最关键的是：`targets` 的第一维是 3，不是 8。因为只给 3 个被选中的环境发目标。

## 常见 shape 错误

| 错误 | 原因 |
|---|---|
| `envs_idx=[1,5,7]`，目标却是 `[8,9]` | 目标数量和被选环境数量不一致 |
| `envs_idx` 在 CPU，目标在 GPU | device 不一致 |
| 只 reset 了部分环境，但观测仍按全部环境处理 | mask / index 没同步 |
| 把环境编号当成 batch 大小 | `envs_idx` 是编号列表，不是数量 |

部分环境控制是并行训练里的常见操作，比如只 reset done 的环境。初学时先用固定 `envs_idx` 练 shape，再进入完整 RL loop。

## 为什么 showcase 不能替代 envs_idx 检查

官方 `sim_02_heterogeneous_envs` 和 `sim_15_batched_ik` 能帮助建立批量环境直觉，但它们的预览图不能直接证明本地 `envs_idx` 写对了。部分环境控制的问题通常不在画面第一眼，而在索引、device 和目标张量形状。

因此，涉及 `envs_idx` 的脚本最好额外保存这些字段：

| 字段 | 例子 | 用途 |
|---|---|---|
| `batch` | `8` | 总环境数量 |
| `envs_idx` | `[1, 5, 7]` | 被控制或 reset 的环境编号 |
| `target_shape` | `[3, 9]` | 目标数量是否等于 `len(envs_idx)` |
| `device` | `cuda:0` 或 `cpu` | 索引和目标是否在同一设备 |
| `operation` | `control_dofs_position` | 记录这组索引用在哪个动作上 |

这类字段看起来很小，但比一张截图更能定位错误。比如画面里 8 个机器人都在动，不代表脚本成功只控制了 3 个环境；也可能是上一轮控制残留、默认目标或 viewer 视角造成的错觉。

## 把部分环境控制写进摘要

本页的 `envs_idx` 示例不是官方 showcase 直接给出的 summary 字段，而是扩展实验应该补上的结构化记录。建议把一次部分环境控制写成下面这种摘要：

```json
{
  "batch": 8,
  "envs_idx": [1, 5, 7],
  "target_shape": [3, 9],
  "target_device": "cuda:0",
  "operation": "control_dofs_position",
  "result": "passed"
}
```

这份摘要的关键关系是 `target_shape[0] == len(envs_idx)`。如果 `envs_idx` 有 3 个编号，目标张量第一维就应该是 3。总环境数 `batch=8` 仍然要记录，但它不是当前目标张量的第一维。这个字段设计可以直接放进项目报告，作为“确实理解了部分环境控制”的证据。

当前配套脚本 `labs/06_genesis/05_parallel_envs.py` 验证的是“控制全部环境”的最小并行链路，输出落在 `runs/genesis_codecheck_*/summaries/05_parallel_envs.json`。如果把本页做成扩展实验，不建议只改画面，而是新增或补充一份结构化摘要，例如：

```text
runs/genesis_codecheck_*/summaries/05_parallel_envs_envs_idx.json
```

报告里至少要同时引用两类证据：

| 证据 | 证明什么 |
|---|---|
| `05_parallel_envs.json` | 全环境批量动作的 `batch`、`action_shape`、`joint1_targets` 正确 |
| `05_parallel_envs_envs_idx.json` | 部分环境控制时 `target_shape[0] == len(envs_idx)`，device 和 operation 已记录 |

这样就不会把 `sim_15_batched_ik` 的公开视频误当作已经掌握 `envs_idx` 的证明。官方素材负责建立直觉，扩展摘要负责证明索引语义。

## shape 判读

下面几题可以直接用来检查是否真正理解 `envs_idx`：

| 场景 | 正确目标 shape | 原因 |
|---|---|---|
| `B=8`，控制全部环境 | `[8, 9]` | 每个环境一组 Franka 目标 |
| `B=8`，`envs_idx=[1, 5, 7]` | `[3, 9]` | 只给 3 个被选中的环境发目标 |
| `B=8`，只 reset done 的 2 个环境 | `scene.reset(envs_idx=done_envs)`；reset 后读取对应状态时第一维为 2 | 选择入口是 `envs_idx`，读取结果的 batch 维度才等于 done 环境数量 |
| `B=1`，不传 `envs_idx` | `[1, 9]` 或按 API 接受的单环境形状 | 单环境也要分清是否已经 build 成 batch |

如果把 `envs_idx` 的最大编号当成 batch 大小，说明概念还没稳。`envs_idx=[1,5,7]` 的 batch 大小是 3，不是 7，也不是 8。

## 读完应能回答

1. `envs_idx=[1, 5, 7]` 时，目标张量第一维为什么是 3？
2. 为什么 `batch=8` 和 `len(envs_idx)=3` 都应该写进摘要？
3. 官方 batched IK 素材为什么不能替代本地 `envs_idx` 结构化记录？

## 小结

- `envs_idx` 是环境编号列表。
- 目标张量的 batch 维度必须等于 `len(envs_idx)`。
- device、shape 和 mask 是部分环境控制的三大排错点。
- 官方批量素材负责建立直觉，扩展 `envs_idx` 脚本必须保存索引和目标 shape。

## 导航

- 上一页：[批量动作与批量状态](02-batched-action-state.md)
- 返回目录：[并行环境](../04-parallel-envs.md)
- 下一页：[并行实验的记录与排错](04-parallel-record-debug.md)
