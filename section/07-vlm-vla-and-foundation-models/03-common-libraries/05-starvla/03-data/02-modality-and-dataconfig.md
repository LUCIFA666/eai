# modality 与 DataConfig

目标：理解 `modality.json` 和 `DataConfig` 怎样把原始 LeRobot 数据变成 StarVLA 使用的字段。

- `modality.json` ：“原始字段叫什么”。
- `DataConfig` ：“训练时用哪些字段、用多少时间步、怎样归一化”。

以 LIBERO 为例，相关文件是：

```text
examples/LIBERO/train_files/modality.json
examples/LIBERO/train_files/data_registry/data_config.py
```

## modality.json

`modality.json` 把原始数据字段映射到标准名字。图像字段类似这样：

```json
{
  "video": {
    "primary_image": {
      "original_key": "observation.images.image"
    },
    "wrist_image": {
      "original_key": "observation.images.wrist_image"
    }
  }
}
```

动作字段会说明每一维代表什么：

```json
{
  "action": {
    "x": {"start": 0, "end": 1},
    "y": {"start": 1, "end": 2},
    "z": {"start": 2, "end": 3},
    "roll": {"start": 3, "end": 4},
    "pitch": {"start": 4, "end": 5},
    "yaw": {"start": 5, "end": 6},
    "gripper": {"start": 6, "end": 7}
  }
}
```

如果这里的维度顺序写错，模型会学习错位动作。训练 loss 可能会下降，但评测时输出动作会很奇怪。

## DataConfig

`DataConfig` 告诉 StarVLA 真正使用哪些字段。LIBERO 的配置大致是：

```python
class Libero4in1DataConfig:
    video_keys = [
        "video.primary_image",
        "video.wrist_image",
    ]
    state_keys = [
        "state.x", "state.y", "state.z",
        "state.roll", "state.pitch", "state.yaw",
        "state.pad", "state.gripper",
    ]
    action_keys = [
        "action.x", "action.y", "action.z",
        "action.roll", "action.pitch", "action.yaw",
        "action.gripper",
    ]
    language_keys = ["annotation.human.action.task_description"]
    observation_indices = [0]
    action_indices = list(range(8))
    state_indices = [0]
```

> LIBERO 的 state 是 8 维，action 是 7 维；`action_indices = list(range(8))` 表示一个样本使用未来 8 步动作作为监督。

| 字段 | 含义 | LIBERO 示例 |
|---|---|---|
| `observation_indices` | 使用哪些观察时间点 | `[0]` |
| `action_indices` | 监督哪些未来动作 | `list(range(8))` |
| `state_indices` | 使用哪些状态时间点 | `[0]` |

`action_indices` 要和模型配置里的 `action_horizon` 对齐：

```yaml
framework:
  action_model:
    action_horizon: 8
```

数据给 8 步，模型也预测 8 步，loss 才能正确计算。

## 归一化设置

`DataConfig` 还会定义 transform。简化后可以理解为：

```python
StateActionTransform(
    apply_to=action_keys,
    normalization_modes={
        "action.x": "min_max",
        "action.y": "min_max",
        "action.z": "min_max",
        "action.roll": "min_max",
        "action.pitch": "min_max",
        "action.yaw": "min_max",
    },
)
```

连续动作维度通常会归一化。`gripper` 常常需要单独处理，因为夹爪可能是二值开合，也可能有和环境相关的符号约定。

部署时，StarVLA 会用同一个 `DataConfig` 重建**反归一化**逻辑，把模型输出还原成动作。

## robot type

`robot_type` 用来选择对应的 `DataConfig`：

```python
ROBOT_TYPE_CONFIG_MAP = {
    "libero_franka": Libero4in1DataConfig(),
}
```

后面的 `data_mix` 会引用 `libero_franka`。如果接入新机器人，通常需要新增一个自己的 `DataConfig`，再把它注册到 `ROBOT_TYPE_CONFIG_MAP`。

## 常见错误

| 错误 | 典型表现 | 修复方向 |
|---|---|---|
| `modality.json` 没复制到数据集 | dataloader 找不到字段 | 放到每个子数据集 `meta/modality.json` |
| `action_keys` 顺序错 | 训练 loss 正常但评测动作异常 | 对齐原始动作维度定义 |
| `action_indices` 和 `action_horizon` 不一致 | loss shape mismatch | 统一数据 chunk 和模型 chunk |
| `state_keys` 含 pad 但模型 state_dim 不对 | state tensor shape 错 | 检查 `state_dim` 和 framework 是否使用 state |
| 归一化漏掉连续维度 | 动作尺度异常 | 检查 transform 和 statistics |

## 小结

- `modality.json` 负责原始字段到标准字段的映射。
- `DataConfig` 负责字段选择、时间索引、归一化和机器人类型。
- `action_indices` 要和 `framework.action_model.action_horizon` 对齐。
- transform 训练时使用，部署反归一化时也会复用。

## 动手练习

1. 运行 `rg -n "action_keys|action_indices|state_keys|state_indices" examples/LIBERO/train_files/data_registry/data_config.py`，确认 LIBERO 的状态字段、动作字段和索引长度。
2. 打开一个 LIBERO 子数据集的 `meta/modality.json`，确认 `action.gripper` 对应原始动作中的哪一维。没有数据时，可先查看 `examples/LIBERO/train_files/modality.json`。
3.运行 `rg -n "action_horizon|action_indices = list\(range\(8\)\)" examples/LIBERO/train_files/data_registry/data_config.py examples/LIBERO/train_files/starvla_cotrain_libero.yaml`，说明数据窗口和模型动作 chunk 的依据。

## 导航

- 上一节：[01 LeRobot 格式约定](01-lerobot-contract.md)
- 返回上级：[数据接口](../03-data.md)
- 下一节：[03 mixture 注册表](03-mixture-registry.md)
