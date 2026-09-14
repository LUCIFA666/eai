# Action Head 与 Action Chunk

目标：理解 VLA-Adapter 的 LIBERO-Pro 主线如何用 L1 action head 输出 7D x 8-step 连续动作。

VLA-Adapter 主线保持 `use_l1_regression=True`。这时 VLM 不直接输出离散 action token，而是把 hidden states 交给 L1 action head，再由 action head 预测连续 action chunk。相关源码入口：

```text
prismatic/models/action_heads.py
prismatic/vla/constants.py
experiments/robot/openvla_utils.py
```

## 关键常量

LIBERO 主线通常使用：

| 常量 | 含义 |
| --- | --- |
| `ACTION_DIM=7` | 末端执行器位姿和 gripper 动作维度。 |
| `NUM_ACTIONS_CHUNK=8` | 一次预测的 action chunk 长度。 |
| `PROPRIO_DIM=8` | LIBERO proprio state 维度。 |

评测时 `num_open_loop_steps` 通常与 action chunk 对齐。模型一次输出 8 步动作，LIBERO 环境按 open-loop 方式执行若干步后再重新查询策略。若 eval 的 open-loop 步数和 checkpoint 训练时使用的 chunk 假设不一致，rollout 行为会失真。

这些值来自 `prismatic/vla/constants.py` 的平台选择。脚本会扫描命令行参数里的 `libero`、`aloha`、`bridge`、`calvin` 等字符串，匹配不到时默认使用 LIBERO。因此这里的 7D x 8-step 是 LIBERO 主线取值，不是所有机器人平台共享的固定形状。同一套默认回退在部署脚本上会把 ALOHA 误判成 LIBERO 常量，导致维度和归一化取错，见 [Policy Server](../07-deployment/01-policy-server.md)。

## action head 如何得到动作块

`L1RegressionActionHead.predict_action()` 会把 action hidden states 和 proprio embedding 一起送进内部网络。下面这段保留了最关键的 shape 变化：

```python
proprio = proprio.reshape(batch_size, -1).to(torch.bfloat16)
proprio_features = proprio_projector(proprio)
proprio_features = proprio_features.unsqueeze(dim=1)

cond_actions_hidden_states = torch.zeros(
    (batch_size, self.action_dim * NUM_ACTIONS_CHUNK, self.hidden_dim),
    device=device, dtype=actions_hidden_states.dtype
).detach()

rearranged_actions_hidden_states = cond_actions_hidden_states.reshape(
    batch_size, NUM_ACTIONS_CHUNK, -1
)
```

这里可以看到两件事：`NUM_ACTIONS_CHUNK` 决定一次预测多少个未来动作，`self.action_dim` 决定每个动作的维度；开启 proprio 后，action head 还会使用 `proprio_projector` 生成的状态条件。shape 报错时，可以先检查这几个值是否和数据、checkpoint、评测命令一致。

## action head 加载

评测脚本会通过 `get_action_head(cfg, model.llm_dim)` 初始化 action head，再从 checkpoint 目录中查找 `action_head--...` 文件加载权重。`use_pro_version` 会影响 action head 相关配置，因此 Pro checkpoint 通常需要保持：

```bash
--use_l1_regression True
--use_pro_version True
```

本地 LoRA checkpoint 也需要保存 action head 权重。只保存 backbone 或 LoRA adapter，不足以支撑 LIBERO eval。

## 训练 loss 对应的动作

`finetune.py` 的 L1 主线会从 batch 中读取连续 `actions`，并根据 action token mask 取出对应 hidden states。训练日志里的当前动作 L1、后续动作 L1 和总 loss，最终都要通过完整 rollout 验证；loss 下降不等于动作 chunk 在环境里一定成功。

## 常见现象

| 现象 | 优先检查 |
| --- | --- |
| action shape mismatch | 当前命令触发的平台常量、数据 action 维度、`num_open_loop_steps`。 |
| rollout 能跑但动作幅度异常 | `dataset_statistics.json`、`unnorm_key`、Pro / Non-Pro 配置。 |
| 找不到 action head 文件 | checkpoint 目录是否包含 `action_head--checkpoint.pt` 或训练保存的同类文件。 |

## 导航

- 上一节：[Prismatic Backbone](01-prismatic-backbone.md)
- 返回上级：[模型组件](../04-model.md)
- 下一节：[Proprio Projector](03-proprio-projector.md)
