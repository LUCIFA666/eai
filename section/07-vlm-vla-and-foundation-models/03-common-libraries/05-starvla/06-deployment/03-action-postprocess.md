# 动作后处理

目标：区分动作反归一化、动作 chunk 缓存、动作集成、gripper 处理分别在哪里发生。

模型推理结束后，动作数值还不能直接发给机器人执行。它需要经过反归一化才能还原成环境动作，还需要 benchmark 侧按环境要求做格式转换。StarVLA 把这些处理分成两层：server 负责反归一化，client 负责其余的 benchmark 特定逻辑。

## 代码分工

| 处理 | 角色 | 文件 |
|---|---|---|
| 模型推理 | server | `policy_wrapper.py` |
| 动作反归一化 | server | `PolicyNormProcessor` |
| action chunk size 发现 | server metadata | `PolicyServerWrapper.metadata` |
| chunk cache | client | `model2*_interface.py` |
| action ensemble | client | `AdaptiveEnsembler` |
| gripper 二值化/环境适配 | client | `model2*_interface.py`、`eval_*.py` |
| delta-to-absolute | client 或环境 adapter | benchmark 相关 |

## 服务端反归一化

`PolicyServerWrapper.predict_action()`：

```python
out = self._framework.predict_action(examples=examples, **kwargs)
normalized = np.asarray(out["normalized_actions"])

unnorm = np.stack(
    [proc.unapply_actions(normalized[b]) for b in range(normalized.shape[0])],
    axis=0,
)
return {"actions": unnorm}
```

这里 `proc.unapply_actions()` 会使用训练期 transform 和 `dataset_statistics.json`。这避免了每个 benchmark 自己手写一套动作还原公式。

## chunk cache

VLA 模型通常一次预测一段未来动作，例如 8 步或 16 步。client 不需要每个环境步都请求一次 server。LIBERO client 中：

```python
if step % self.action_chunk_size == 0 or self.raw_actions is None:
    response = self.client.predict_action(vla_input)
    actions_batch = response["data"]["actions"]
    self.raw_actions = np.asarray(actions_batch)[0]

raw_actions = self.raw_actions[step % self.action_chunk_size][None]
```

这就是 chunk cache：每隔一个 chunk 请求一次模型，其余环境步复用上次预测。

## gripper 处理

LIBERO 环境需要的 gripper 值和模型输出语义不完全一样。`eval_libero.py` 中有：

```python
def _binarize_gripper_open(open_val):
    v = float(arr[0])
    bin_val = 1.0 - 2.0 * (v > 0.5)
    return np.asarray([bin_val], dtype=np.float32)
```

模型侧输出 `open_gripper`，环境侧需要把它变成 LIBERO action 的 gripper 通道。这类逻辑和具体 benchmark 强相关，所以留在 client 或 eval 脚本中。

## action ensemble

某些 benchmark client 会使用 `AdaptiveEnsembler`。它的作用是对多次预测中重叠的动作步做加权平均，减少 chunk 边界处的抖动。

这属于控制策略后处理，不属于模型通用推理。因此即使 server 统一反归一化，action ensemble 仍然应该留在 benchmark client。

## 版本差异提醒

如果看到旧文档或旧脚本里写：

```python
action = result["normalized_actions"][0]
```

要检查当前 server 返回格式。当前 `PolicyServerWrapper` 返回的是：

```python
response["data"]["actions"]
```

如果 client 还在读 `normalized_actions`，会报 KeyError 或把动作解释错。

## 小结

- 当前代码中，server 负责反归一化，client 接收 `actions`。
- client 仍负责 benchmark 特定逻辑：chunk cache、gripper、action ensemble、delta-to-absolute。
- 文档和代码有版本差异时，以当前 `policy_wrapper.py` 和 `model2*_interface.py` 为准。

## 动手练习

1. 运行 `rg -n 'normalized_actions|unapply_actions|return \"actions\"' deployment/model_server/policy_wrapper.py`，找到 server 返回环境动作的位置。
2. 运行 `rg -n "step % self.action_chunk_size|raw_actions|action_chunk_size" examples/LIBERO/eval_files/model2libero_interface.py`，解释 LIBERO client 的 chunk cache。
3. 运行 `rg -n "def _binarize_gripper_open|open_gripper|raw_action\[6:7\]" examples/LIBERO/eval_files/eval_libero.py`，说明 gripper 处理为什么放在 benchmark 适配层。

## 导航

- 上一节：[02 websocket 协议](02-websocket-protocol.md)
- 返回上级：[部署与推理服务](../06-deployment.md)
- 下一节：[04 调试部署](04-debug-deployment.md)
