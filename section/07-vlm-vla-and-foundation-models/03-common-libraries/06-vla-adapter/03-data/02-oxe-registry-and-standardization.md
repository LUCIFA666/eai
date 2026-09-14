# OXE Registry 与字段标准化

目标：理解 `dataset_name` 如何在 VLA-Adapter 中找到数据 mixture、字段配置、标准化函数和 action / proprio 归一化规则。

`dataset_name` 是 VLA-Adapter 数据接口与管线中的主键。它从 `FinetuneConfig.dataset_name` 进入 `RLDSDataset`，随后依次经过 `OXE_NAMED_MIXTURES`、`OXE_DATASET_CONFIGS` 和 `OXE_STANDARDIZATION_TRANSFORMS`。这三处源码共同回答一个问题：给定一个 RLDS 数据集，VLA-Adapter 应该读哪些图像、怎样解释状态、怎样处理 action，以及最终把哪些字段交给 transform。

## 从训练参数到 mixture

`prismatic/vla/datasets/datasets.py` 会先判断 `data_mix` 是否是一个命名 mixture。如果没有命中，源码会把它当成单数据集训练。

```python
# prismatic/vla/datasets/datasets.py
if self.data_mix in OXE_NAMED_MIXTURES:
    mixture_spec = OXE_NAMED_MIXTURES[self.data_mix]
else:
    mixture_spec = [(self.data_mix, 1.0)]

load_camera_views = ("primary", "wrist")
per_dataset_kwargs, weights = get_oxe_dataset_kwargs_and_weights(
    self.data_root_dir,
    mixture_spec,
    load_camera_views=load_camera_views,
    load_proprio=True,
    load_language=True,
    action_proprio_normalization_type=ACTION_PROPRIO_NORMALIZATION_TYPE,
)
```

LIBERO 的四个训练集在 `prismatic/vla/datasets/rlds/oxe/mixtures.py` 中注册为单数据集 mixture；`libero_4_task_suites_no_noops` 则把四个 suite 放到同一个 mixture 里。

```python
OXE_NAMED_MIXTURES = {
    "libero_spatial_no_noops": [("libero_spatial_no_noops", 1.0)],
    "libero_object_no_noops": [("libero_object_no_noops", 1.0)],
    "libero_goal_no_noops": [("libero_goal_no_noops", 1.0)],
    "libero_10_no_noops": [("libero_10_no_noops", 1.0)],
    "libero_4_task_suites_no_noops": [
        ("libero_spatial_no_noops", 1.0),
        ("libero_object_no_noops", 1.0),
        ("libero_goal_no_noops", 1.0),
        ("libero_10_no_noops", 1.0),
    ],
}
```

训练参数中的 `dataset_name=libero_spatial_no_noops` 和评测参数中的 `task_suite_name=libero_spatial` 指向同一个 suite，但用途不同。前者决定 RLDS 读取和 statistics key，后者交给 LIBERO benchmark 创建任务和初始状态。

## OXE 配置定义字段解释方式

LIBERO 四个 modified 数据集在 `prismatic/vla/datasets/rlds/oxe/configs.py` 中共享同一类配置：

```python
"libero_spatial_no_noops": {
    "image_obs_keys": {"primary": "image", "secondary": None, "wrist": "wrist_image"},
    "depth_obs_keys": {"primary": None, "secondary": None, "wrist": None},
    "state_obs_keys": ["EEF_state", "gripper_state"],
    "state_encoding": StateEncoding.POS_EULER,
    "action_encoding": ActionEncoding.EEF_POS,
}
```

这段配置把原始 TFDS 字段和 VLA-Adapter 的内部字段接起来：

| 配置项 | LIBERO 主线含义 | 影响位置 |
| --- | --- | --- |
| `image_obs_keys.primary = "image"` | 第三人称图像来自原始 `image` 字段 | 生成 `observation["image_primary"]` |
| `image_obs_keys.wrist = "wrist_image"` | wrist 图像来自原始 `wrist_image` 字段 | 生成 `observation["image_wrist"]` |
| `state_obs_keys = ["EEF_state", "gripper_state"]` | 使用末端位姿与 gripper state 合成 proprio | 生成 `observation["proprio"]` |
| `action_encoding = EEF_POS` | action 是 6D 末端控制 + gripper | 设置 action mask 和归一化规则 |

`make_oxe_dataset_kwargs()` 会检查请求的 camera view 是否存在，并为 `EEF_POS` action 设置 mask：前 6 维参与归一化，最后一维 gripper 保留自己的绝对语义。

```python
# prismatic/vla/datasets/rlds/oxe/materialize.py
dataset_kwargs = deepcopy(OXE_DATASET_CONFIGS[dataset_name])

if dataset_kwargs["action_encoding"] is ActionEncoding.EEF_POS:
    dataset_kwargs["absolute_action_mask"] = [False] * 6 + [True]
    dataset_kwargs["action_normalization_mask"] = [True] * 6 + [False]

dataset_kwargs["standardize_fn"] = OXE_STANDARDIZATION_TRANSFORMS[dataset_name]
```

因此，action 维度相同并不代表数据可以直接互换。gripper 语义、mask、statistics 和评测动作还原都跟 `dataset_name` 绑定在一起。

## LIBERO 标准化函数

`prismatic/vla/datasets/rlds/oxe/transforms.py` 把四个 LIBERO 数据集注册到 `libero_dataset_transform`。这个函数处理两件事：修正 gripper action 的开合方向，并从原始 `state` 中拆出 VLA-Adapter 需要的 proprio 字段。

```python
def libero_dataset_transform(trajectory):
    gripper_action = trajectory["action"][:, -1:]
    gripper_action = invert_gripper_actions(tf.clip_by_value(gripper_action, 0, 1))

    trajectory["action"] = tf.concat(
        [trajectory["action"][:, :6], gripper_action],
        axis=1,
    )
    trajectory["observation"]["EEF_state"] = trajectory["observation"]["state"][:, :6]
    trajectory["observation"]["gripper_state"] = trajectory["observation"]["state"][:, -2:]
    return trajectory
```

标准化函数运行后，`state_obs_keys` 才能找到 `EEF_state` 和 `gripper_state`。如果自定义数据已经提供了不同名字的 proprio 字段，也需要在对应的 `standardize_fn` 里整理成 OXE 配置中声明的字段。

## 名字、字段和 statistics 的连接

`dataset_name` 最后还会变成 `dataset_statistics.json` 的顶层 key。训练用 `libero_spatial_no_noops` 时，statistics 往往以这个字符串保存；评测用 `libero_spatial` 时，`run_libero_eval.py::check_unnorm_key()` 会在找不到 `libero_spatial` 的情况下回退到 `libero_spatial_no_noops`。

```text
train dataset_name:  libero_spatial_no_noops
OXE config key:      libero_spatial_no_noops
stats key:           libero_spatial_no_noops
eval task_suite:     libero_spatial
eval unnorm_key:     libero_spatial_no_noops when fallback is needed
```

如果训练还没进入第一个 step，可以先区分错误发生在哪一层：TFDS 找不到目录时看 `data_root_dir`；camera view 或 state key 报错时看 `configs.py` 和 `transforms.py`；action mask 或归一化维度不对时看 `materialize.py`、`constants.py` 和 statistics。

## 导航

- 上一节：[数据接口与字段约束](01-data-interface-and-field-constraints.md)
- 返回上级：[数据接口与管线](../03-data.md)
- 下一节：[RLDSBatchTransform 与 Collator](03-rlds-batch-transform-and-collator.md)
