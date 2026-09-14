# 统计与归一化

目标：理解动作为什么要归一化，`dataset_statistics.json` 怎样产生，以及部署时怎样把模型输出还原成环境动作。

机器人动作的每一维尺度可能差很多。位置可能是米，姿态可能是弧度，夹爪可能是开合信号。训练时通常会把连续动作缩放到更稳定的范围；评测时再把模型输出还原回环境需要的尺度。

## 训练时保存 statistics

构建数据集后，StarVLA 会保存数据统计：

```python
vla_dataset.save_dataset_statistics(output_dir / "dataset_statistics.json")
```

文件大致长这样：

```json
{
  "libero_franka": {
    "action": {
      "min": [...],
      "max": [...],
      "q01": [...],
      "q99": [...]
    },
    "state": {
      "min": [...],
      "max": [...]
    }
  }
}
```

具体 key 会随数据集和 transform 实现变化。**它记录了训练数据中动作和状态的尺度。**

## 模型输出是什么

framework 的推理接口通常返回标准化动作：

```python
{
    "normalized_actions": np.ndarray(shape=(B, T, action_dim))
}
```

`normalized_actions` 适合模型训练和推理，但环境不能直接执行它。部署服务需要把它还原成 `actions`。

## 部署时怎么还原

推理服务大致做三步：

```text
framework.predict_action()
  -> normalized_actions
  -> PolicyNormProcessor 读取训练统计
  -> actions
```

`PolicyNormProcessor` 会读取 checkpoint 所在运行目录里的文件：

```text
<RUN_DIR>/<run_id>/
├── checkpoints/
│   └── steps_*.pt
├── config.yaml
└── dataset_statistics.json
```

`config.yaml` 提供 `data_mix` 和 framework 配置，`dataset_statistics.json` 提供动作尺度。两者缺一项，部署阶段都很容易失败。

## 统一在 server 侧处理

动作还原如果分散到每个 benchmark client 里，容易出现多套逻辑：有的维度归一化，有的维度不归一化，gripper 还有自己的开合约定。StarVLA 在 server 侧重建训练时的 transform，尽量让训练和部署使用同一套动作尺度规则。

不过， benchmark client 仍然会保留环境专属处理，例如 LIBERO 里的夹爪二值化、action chunk 缓存、视频保存等。

## unnorm_key

如果 checkpoint 只对应一种机器人，server 通常能自动选择 statistics key。多机器人或多数据集混训时，需要明确告诉 server 用哪套统计：

```python
request = {
    "examples": [example],
    "unnorm_key": "libero_franka",
}
```

server metadata 会暴露可用 key：

```python
{
    "available_unnorm_keys": [...],
    "default_unnorm_key": ...,
    "action_chunk_size": ...,
}
```

client 可以先读 metadata，再决定是否传 `unnorm_key`。

## 常见问题

| 现象 | 可能原因 | 检查点 |
|---|---|---|
| server 找不到 statistics | 只拷贝了 checkpoint 文件 | 保留完整运行目录 |
| 动作幅度极大或极小 | statistics 和当前 benchmark 不匹配 | `data_mix`、`unnorm_key` |
| gripper 总是反向 | 环境专属 gripper 后处理不匹配 | `model2*_interface.py` |
| 多机器人 checkpoint 报 ambiguous | 没有传 `unnorm_key` | server metadata |
| 训练 loss 正常评测失败 | 字段顺序或归一化配置错 | `DataConfig`、`modality.json` |

## 小结

- 训练时动作会按数据统计归一化。
- framework 推理输出通常是 `normalized_actions`。
- 部署服务把标准化动作还原成环境可执行的 `actions`。
- `dataset_statistics.json` 和 `config.yaml` 都是部署必需文件。
- 多机器人部署时要关注 `unnorm_key`。

## 动手练习

1. 打开一个真实 `dataset_statistics.json`，用 `python -m json.tool <path>` 检查 JSON 是否能解析，再数出 action 统计长度是否等于 `action_dim`。
2. 运行 `rg -n 'normalized_actions|unapply_actions|return \"actions\"' deployment/model_server/policy_wrapper.py deployment/model_server/policy_norm_processor.py`，找到归一化动作转成环境动作的位置。
3. 运行 `rg -n "gripper|_binarize_gripper_open|raw_action\[6:7\]" examples/LIBERO/eval_files/eval_libero.py examples/LIBERO/eval_files/model2libero_interface.py`，说明 gripper 后处理和 server 反归一化的分工。

## 导航

- 上一节：[04 VLM 协同训练数据](04-vlm-cotrain-data.md)
- 返回上级：[数据接口](../03-data.md)
- 下一节：[模型框架](../04-frameworks.md)
