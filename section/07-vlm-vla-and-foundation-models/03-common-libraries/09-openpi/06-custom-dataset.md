# 8.5.1.6 自定义数据集训练

## 学习目标

- 将自己的机器人数据转换为 OpenPI 可用的 LeRobot 格式。
- 编写自定义 TrainConfig，替换数据集路径和 action / state 维度。
- 理解 `DataConfig` 中各字段的含义，以及如何适配不同机器人平台。

## 为什么需要自定义数据集

前几章使用的 LIBERO 是 OpenPI 预置的仿真数据集，数据格式、action 维度、相机配置都已经在 `LeRobotLiberoDataConfig` 中写死。真实机器人的数据集通常有：

- 不同的 action 维度（如 ALOHA 双臂 14 维 vs LIBERO 单臂 7 维）
- 不同的相机数量和命名（如 `cam_high` / `cam_left_wrist` vs `frontview` / `wrist`）
- 不同的 state 维度（如包含关节角度、夹爪位置等）
- 没有语言指令（`task` 字段为空），需要手动设置 prompt

本章以 ALOHA 双臂数据集为例，展示如何从零配置一个自定义训练任务。

## 准备工作
确保数据已是 LeRobot 格式

OpenPI 的数据加载层基于 LeRobot，自定义数据必须符合 LeRobotDataset v2.1 或 v3.0 格式。如果你的数据是其他格式（ROS bag、HDF5、NPZ 等），需要先转换为 LeRobot 格式。具体转换方法参见 [LeRobot 数据格式及转换](../08-lerobot/03-data-format.md)。

转换完成后，你的数据集目录结构应类似：

```text
/path/to/my_aloha_dataset/
├── meta/
│   ├── info.json          # codebase_version + features 定义
│   ├── stats.json          # 归一化统计量
│   ├── episodes.jsonl      # episode 元信息
│   └── tasks.jsonl         # 任务文本
├── data/
│   └── chunk-000/
│       └── episode_*.parquet
└── videos/
    └── ...
```


## 方案一：直接使用 LeRobotDataConfig

适用场景： 数据集的相机 key、action/state 维度与模型默认期望基本一致，仅需更换数据集路径和 prompt。

### 编写 TrainConfig

以 π0 模型 + 自定义 ALOHA 数据集为例，在 `config.py` 中新增：

```python
# config.py
TrainConfig(
    name="pi0_my_aloha",
    model=pi0_config.Pi0Config(),
    data=LeRobotDataConfig(             # 注意：通用 DataConfig，非 LeRobotLiberoDataConfig
        repo_id="/path/to/my_aloha_dataset",
        base_config=DataConfig(
            obs_horizon=2,
            action_horizon=10,
            prompt_from_task=False,     # 自定义数据集通常无 task 字段
            prompt="do something",      # 手动指定固定语言指令
            action_normalizer="normalizer",
            use_delta_action=False,     # ALOHA 用绝对位置控制
        ),
        extra_delta_transform=False,
    ),
    weight_loader=weight_loaders.CheckpointWeightLoader(
        "gs://openpi-assets/checkpoints/pi0_base/params"
    ),
    num_train_steps=20_000,
),
```

各字段含义：

| 字段 | 作用 | 说明 |
|---|---|---|
| `name` | 配置名称 | 自定义唯一标识，如 `"pi0_my_aloha"` |
| `data` | 数据集配置 | 使用通用 `LeRobotDataConfig`（非 LIBERO 专用） |
| `data.repo_id` | 数据集路径 | 可以是 Hub ID 或本地绝对路径 |
| `data.obs_horizon` | 观测帧数 | 模型输入使用过去多少帧图像和状态 |
| `data.action_horizon` | 动作预测帧数 | 模型一次预测未来多少步动作 |
| `data.prompt_from_task` | 从 task 字段读取指令 | 无 language annotation 时设为 `False` |
| `data.prompt` | 固定语言指令 | `prompt_from_task=False` 时使用 |
| `data.action_dim` / `data.state_dim` | 维度覆盖 | 可选，不写则从 stats 自动推断 |
| `data.action_normalizer` | 归一化方式 | `"normalizer"` 或 `"quantiles"` |
| `data.use_delta_action` | delta 动作 | 绝对控制设为 `False`，delta 控制设为 `True` |

### 计算 stats 并训练

```bash
# 计算归一化统计量
python scripts/compute_norm_stats.py --config_name pi0_my_aloha

# 启动训练
HF_HUB_OFFLINE=1 \
CUDA_VISIBLE_DEVICES=4,5,6,7 \
python scripts/train.py pi0_my_aloha \
    --exp_name my_aloha_exp \
    --fsdp_devices 4 \
    --weight_loader.load_path=/path/to/models/openpi/pi0_base
```


## 方案二：新建 policy + DataConfigFactory

适用场景： 已有 `DataConfigFactory` 都不适用——相机数不同、action 需 pad/截断、prompt 字段名不同、delta mask 需自定义。

### 数据集准备

以 `LabUtopia/Level3_TransportBeaker` 为例（三相机、8 维 action）。

### Step 1 — 新建 policy 文件

创建 `src/openpi/policies/labsim_policy.py`，做三件事：重命名相机、pad 维度、task → prompt。

```python
import dataclasses
import einops
import numpy as np
from openpi import transforms
from openpi.models import model as _model


def _parse_image(image) -> np.ndarray:
    image = np.asarray(image)
    if np.issubdtype(image.dtype, np.floating):
        image = (255 * image).astype(np.uint8)
    if image.shape[0] == 3:
        image = einops.rearrange(image, "c h w -> h w c")
    return image


@dataclasses.dataclass(frozen=True)
class LabSimInputs(transforms.DataTransformFn):
    """将 LabSim 原始数据映射到 OpenPI 内部格式。"""
    action_dim: int
    model_type: _model.ModelType = _model.ModelType.PI0

    def __call__(self, data: dict) -> dict:
        state = transforms.pad_to_dim(data["state"], self.action_dim)
        inputs = {
            "state": state,
            "image": {
                "base_0_rgb": _parse_image(data["camera_1_rgb"]),
                "left_wrist_0_rgb": _parse_image(data["camera_2_rgb"]),
                "right_wrist_0_rgb": _parse_image(data["camera_3_rgb"]),
            },
            "image_mask": {
                "base_0_rgb": np.True_,
                "left_wrist_0_rgb": np.True_,
                "right_wrist_0_rgb": np.True_,
            },
        }
        if "actions" in data:
            inputs["actions"] = transforms.pad_to_dim(data["actions"], self.action_dim)
        if "task" in data:
            inputs["prompt"] = data["task"]
        elif "prompt" in data:
            inputs["prompt"] = data["prompt"]
        return inputs


@dataclasses.dataclass(frozen=True)
class LabSimOutputs(transforms.DataTransformFn):
    """推理时截断回真实的 action 维度。"""
    action_dim: int = 8

    def __call__(self, data: dict) -> dict:
        if "actions" in data:
            data["actions"] = data["actions"][..., :self.action_dim]
        if "state" in data:
            data["state"] = data["state"][..., :self.action_dim]
        return data
```

 设计意图：`LabSimInputs` 同时承担键名映射和语义处理，不分 repack + data 两层，因为 pad/截断与键名映射耦合在一起。

### Step 2 — 修改 config.py

修改点 1 — import 区域新增：

```python
import openpi.policies.labsim_policy as labsim_policy
```

修改点 2 — 插入新的 `DataConfigFactory`：

```python
@dataclasses.dataclass(frozen=True)
class LabSimDataConfig(DataConfigFactory):
    default_prompt: str | None = None
    use_delta_joint_actions: bool = True

    @override
    def create(self, assets_dirs, model_config):
        data_transforms = _transforms.Group(
            inputs=[labsim_policy.LabSimInputs(
                action_dim=model_config.action_dim,
                model_type=model_config.model_type,
            )],
            outputs=[labsim_policy.LabSimOutputs()],
        )
        if self.use_delta_joint_actions:
            delta_action_mask = _transforms.make_bool_mask(7, -1)
            data_transforms = data_transforms.push(
                inputs=[_transforms.DeltaActions(delta_action_mask)],
                outputs=[_transforms.AbsoluteActions(delta_action_mask)],
            )
        model_transforms = ModelTransformFactory(default_prompt=self.default_prompt)(model_config)
        return dataclasses.replace(
            self.create_base_config(assets_dirs, model_config),
            repack_transforms=_transforms.Group(),
            data_transforms=data_transforms,
            model_transforms=model_transforms,
        )
```

关键设计：
- `repack_transforms` 为空——键名映射在 `LabSimInputs` 中完成。
- `action_dim` 取自 `model_config.action_dim`，自动与 TrainConfig 对齐。
- `DeltaActions` mask 为 `(True*7, False)`——前 7 维关节转增量，最后 1 维夹爪保持绝对。

**修改点 3** — 在 `_CONFIGS` 末尾插入 TrainConfig：

```python
TrainConfig(
    name="pi0_fast_level3_TransportBeaker",
    model=pi0_fast.Pi0FASTConfig(action_dim=8, action_horizon=32, max_token_len=256),
    data=LabSimDataConfig(
        repo_id="/path/Level3_TransportBeaker",
        use_delta_joint_actions=True,
        base_config=DataConfig(prompt_from_task=True),
    ),
    weight_loader=weight_loaders.CheckpointWeightLoader("/path/pi0_fast_base/params"),
    batch_size=24,
    num_train_steps=40_000,
    keep_period=10000,
    resume=True,
    wandb_enabled=False,
)
```

### Step 3 — 训练

```bash
# 1. 计算 norm stats
python scripts/compute_norm_stats.py --config_name pi0_fast_level3_TransportBeaker

# 2. 训练
CUDA_VISIBLE_DEVICES=0,1,2,3 python scripts/train.py \
    --config_name pi0_fast_level3_TransportBeaker \
    --exp_name exp001
```

---

## 两种方案对比

| 维度 | 方案一：LeRobotDataConfig | 方案二：policy + DataConfigFactory |
|---|---|---|
| 修改范围 | 仅 `config.py` | `config.py` + 新建 policy 文件 |
| 相机映射 | 依赖 key 名匹配 | 自定义 `Inputs` 中显式映射 |
| 维度 pad/截断 | 不涉及 | 自定义 `pad_to_dim` / 截断 |
| delta mask | 全局 `use_delta_action` | 支持维级粒度 mask |
| 适合场景 | 相机名和维度与模型一致 | 相机数不同、维度需 pad、复杂变换 |

## 常见问题

### action 维度不匹配

**现象**：训练启动时报 shape mismatch，如 `expected 7, got 14`。

**原因**：DataConfig 默认从预训练权重的 action dim 继承，与你的数据集不一致。

**解决**：在 `DataConfig` 中显式设置 `action_dim` 和 `state_dim` 为你的实际维度。注意维度改写后，`weight_loader` 会跳过形状不匹配的层并随机初始化。

### prompt 为空导致 loss 异常

**现象**：模型 loss 能下降但实际部署时行为不正确。

**原因**：`prompt_from_task=False` 且未设置 `prompt`，模型收不到任何语言指令。

**解决**：为你的任务设置一个有意义的 `prompt`，如 `"pick up the red block and place it in the bowl"`。

### 相机 key 不匹配

**现象**：`KeyError` 提示找不到某个相机 key。

**原因**：模型期望的相机名与数据集中的不一致。

**解决**：在 `DataConfig` 中通过 `image_keys` 字段指定你的相机列表，或将数据集的相机重命名为模型期望的名称。

## 导航

- 返回父页：[OpenPI](../09-openpi.md)
- 上一节：[π0.5 训练](05-pi05.md)
