# Proprio Projector

目标：理解 `use_proprio=True` 时，机器人状态如何进入 VLA 模型。

LIBERO-Pro checkpoint 主线使用 proprio state。`proprio_projector` 的作用是把 8D proprio 向量投影到模型 hidden dim，再作为 action prediction 的条件之一。只要 `use_proprio=True`，训练、评测和部署都要提供对应输入和权重。

相关源码：

```text
prismatic/models/projectors.py
prismatic/models/action_heads.py
experiments/robot/openvla_utils.py
```

## 开启 proprio 后会多出哪些依赖

如果训练时使用：

```bash
--use_proprio True
```

评测和部署时也应保持 `use_proprio=True`，并确保 checkpoint 中有 proprio projector 权重。否则可能出现两类问题：加载阶段找不到 `proprio_projector--...` 文件，或者模型输入结构与训练时不一致。

源码里的 projector 很小，是两层 MLP：

```python
class ProprioProjector(nn.Module):
    def __init__(self, llm_dim: int, proprio_dim: int) -> None:
        super().__init__()
        self.llm_dim = llm_dim
        self.proprio_dim = proprio_dim
        self.fc1 = nn.Linear(self.proprio_dim, self.llm_dim, bias=True)
        self.fc2 = nn.Linear(self.llm_dim, self.llm_dim, bias=True)
        self.act_fn1 = nn.GELU()

    def forward(self, proprio: torch.Tensor = None) -> torch.Tensor:
        projected_features = self.fc1(proprio)
        projected_features = self.act_fn1(projected_features)
        projected_features = self.fc2(projected_features)
        return projected_features
```

这段代码说明 projector 对输入维度很敏感。LIBERO 主线是 8D proprio；如果换成 ALOHA、BRIDGE 或自定义机器人，`PROPRIO_DIM`、数据 transform、client payload 和 checkpoint 组件都要一起调整。

## 归一化

评测时 `openvla_utils.normalize_proprio()` 会根据 checkpoint 的 statistics 归一化 proprio。即使 projector 权重加载成功，如果 statistics 或 `unnorm_key` 不匹配，进入 projector 的 state 分布也可能偏离训练条件。

这个归一化发生在 projector 前面。projector 看到的是按 `dataset_statistics.json` 中对应 key 处理后的 state。动作尺度异常时，可以同时检查 projector 权重和 statistics 是否来自同一组训练数据。

LIBERO 主线同时受这几个值约束：

| 项 | 主线含义 |
| --- | --- |
| `PROPRIO_DIM=8` | LIBERO proprio state 维度。 |
| `use_proprio=True` | 模型需要 proprio projector 和 state 输入。 |
| `dataset_statistics.json` | 提供 proprio normalization 统计。 |
| `num_images_in_input=2` | 和 proprio 一起决定 action head 条件输入。 |

## 检查项

```bash
find outputs/LIBERO-Spatial-Pro -maxdepth 1 -type f | sort | rg 'proprio_projector|dataset_statistics'
```

本地微调 checkpoint 也应有同类组件文件，具体文件名以训练保存逻辑为准。

## 导航

- 上一节：[Action Head 与 Action Chunk](02-action-head-and-action-chunk.md)
- 返回上级：[模型组件](../04-model.md)
- 下一节：[Pro Version Flags](04-pro-version-flags.md)
