# 接入自有 LeRobot 数据

目标：把自己的机器人数据转换成 StarVLA 能训练的 LeRobot 数据集，并完成字段映射、robot type 注册和训练配置。

## 第一步：转换成 LeRobot 格式

自有数据至少需要包含：

| 字段 | 说明 |
|---|---|
| `observation.state` | 机器人状态，例如关节位置、末端位姿 |
| `action` | 机器人动作，例如关节目标或末端增量 |
| `observation.images.*` | 一个或多个相机视频 |
| `language_instruction` 或 `task` | 任务文本 |

示例特征：

```python
FEATURES = {
    "observation.state": {
        "dtype": "float32",
        "shape": (7,),
        "names": ["state"],
    },
    "action": {
        "dtype": "float32",
        "shape": (7,),
        "names": ["action"],
    },
    "observation.images.image": {
        "dtype": "video",
        "shape": (480, 640, 3),
        "names": ["height", "width", "channels"],
    },
    "language_instruction": {
        "dtype": "string",
        "shape": (1,),
        "names": ["instruction"],
    },
}
```

转换后目录应类似：

```text
your_dataset_name/
├── meta/
│   ├── info.json
│   ├── episodes.jsonl
│   ├── stats.json
│   └── tasks.json
├── data/
│   └── chunk-000/episode_000000.parquet
└── videos/
    └── chunk-000/observation.images.image/episode_000000.mp4
```

## 第二步：写 modality.json

`modality.json` 是原始字段到 StarVLA 内部字段的翻译表：

```json
{
  "state": {
    "arm_joint": {"start": 0, "end": 6},
    "gripper_joint": {"start": 6, "end": 7}
  },
  "action": {
    "arm_joint": {"start": 0, "end": 6},
    "gripper_joint": {"start": 6, "end": 7}
  },
  "video": {
    "camera_1": {"original_key": "observation.images.camera_1"},
    "camera_2": {"original_key": "observation.images.camera_2"}
  },
  "annotation": {
    "human.action.task_description": {"original_key": "language_instruction"}
  }
}
```

如果原始 `state` 是 8 维 `[j0, ..., j6, gripper]`，就用 `start/end` 切出手臂和夹爪。不同部分可以在 `DataConfig` 中采用不同归一化策略。

## 第三步：写 Robot Type Config

创建配置类：

```python
class MyRobotDataConfig:
    video_keys = ["video.camera_1", "video.camera_2"]
    state_keys = ["state.arm_joint", "state.gripper_joint"]
    action_keys = ["action.arm_joint", "action.gripper_joint"]
    language_keys = ["annotation.human.action.task_description"]

    observation_indices = [0]
    action_indices = list(range(8))
    state_indices = [0]

    def modality_config(self):
        return {
            "video": ModalityConfig(delta_indices=self.observation_indices, modality_keys=self.video_keys),
            "state": ModalityConfig(delta_indices=self.state_indices, modality_keys=self.state_keys),
            "action": ModalityConfig(delta_indices=self.action_indices, modality_keys=self.action_keys),
            "language": ModalityConfig(delta_indices=self.observation_indices, modality_keys=self.language_keys),
        }

    def transform(self):
        return ComposedModalityTransform(transforms=[
            StateActionToTensor(apply_to=self.state_keys),
            StateActionTransform(
                apply_to=self.state_keys,
                normalization_modes={key: "min_max" for key in self.state_keys},
            ),
            StateActionToTensor(apply_to=self.action_keys),
            StateActionTransform(
                apply_to=self.action_keys,
                normalization_modes={key: "min_max" for key in self.action_keys},
            ),
        ])
```

再注册：

```python
ROBOT_TYPE_CONFIG_MAP = {
    "my_robot": MyRobotDataConfig(),
}
```

实际项目中可以参考 `examples/LIBERO/train_files/data_registry/data_config.py`，优先放在对应 benchmark 的 `examples/MyRobot/train_files/data_registry/` 下。

## 第四步：写 data mix

```python
DATASET_NAMED_MIXTURES = {
    "my_dataset": [
        ("my_dataset_name", 1.0, "my_robot"),
    ],
    "my_mixed_dataset": [
        ("my_dataset_task1", 1.0, "my_robot"),
        ("my_dataset_task2", 0.5, "my_robot"),
        ("my_dataset_task3", 2.0, "my_robot"),
    ],
}
```

数据目录：

```text
<DATA_ROOT>/MY_DATA_ROOT/
├── my_dataset_task1/
├── my_dataset_task2/
└── my_dataset_task3/
```

YAML 中：

```yaml
datasets:
  vla_data:
    data_root_dir: <DATA_ROOT>/MY_DATA_ROOT
    data_mix: my_dataset
```

## 第五步：训练配置

关键字段：

```yaml
framework:
  name: QwenOFT
  qwenvl:
    base_vlm: <MODEL_ROOT>/Qwen3-VL-4B-Instruct
  action_model:
    action_dim: 7
    state_dim: 7
    action_horizon: 8

datasets:
  vla_data:
    dataset_py: lerobot_datasets
    data_root_dir: <DATA_ROOT>/MY_DATA_ROOT
    data_mix: my_dataset
    per_device_batch_size: 16
```

`action_dim` 和 `state_dim` 必须与你的 `DataConfig` 总维度一致。单臂 7 关节 + 1 夹爪通常是 8；双臂各 7 关节通常是 14；BEHAVIOR 的 R1Pro 是 23。

## 小结

- 自有数据先转 LeRobot，再写 `modality.json`。
- `DataConfig` 定义字段、时间索引、归一化和 robot type。
- `DATASET_NAMED_MIXTURES` 把数据目录、权重和 robot type 绑定。
- `action_dim/state_dim/action_horizon` 必须和数据配置一致。

## 动手练习

1. 参考 `examples/LIBERO/train_files/modality.json`，为一个 6 轴机械臂加 1 个夹爪写出 `modality.json` 的 action 部分，并说明每个维度对应的原始字段。
2. 运行 `rg -n "video_keys|modality_config|ModalityConfig|action_indices" examples/LIBERO/train_files/data_registry/data_config.py`，写出单相机版本需要改哪些字段。
3. 准备好自定义 LeRobot 数据后运行 dataloader 调试入口。成功输出应生成 `results/debug/dataset_statistics.json`，其中 action 统计长度应等于你的 `action_dim`。

## 导航

- 上一节：[扩展 StarVLA](../09-extension.md)
- 返回上级：[扩展 StarVLA](../09-extension.md)
- 下一节：[02 新 framework](02-new-framework.md)
