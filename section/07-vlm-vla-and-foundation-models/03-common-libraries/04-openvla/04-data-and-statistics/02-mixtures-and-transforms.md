# Mixture 与 Transform

目标：读懂 OpenVLA 如何用 mixture、dataset config 和 standardization transform 把不同 RLDS 数据集接到统一训练字段。

OpenVLA 训练数据来自多个数据集。每个数据集的相机名称、动作编码、语言字段和文件位置可能不同。OpenVLA 用三层注册信息把它们接起来：mixture 决定采样哪些数据集，config 说明单个数据集有哪些字段，transform 把原始字段改成统一格式。

## Mixture：数据集名单和权重

`OXE_NAMED_MIXTURES` 是命名 mixture 的入口。一个 mixture 是若干 `(dataset_name, weight)` 组成的列表：

```python
OXE_NAMED_MIXTURES = {
    "bridge": [
        ("bridge_orig", 1.0),
    ],
    "oxe_magic_soup_plus": [
        ("fractal20220817_data", 0.54087122203),
        ("kuka", 0.8341046294),
        ("bridge_orig", 1.0),
        ("taco_play", 2.0),
    ],
}
```

这里的权重是采样权重，不是数据集大小。实际训练时，`RLDSDataset` 会把 mixture spec 交给 `get_oxe_dataset_kwargs_and_weights()`，再进入 interleaved RLDS dataset。

## Config：单个数据集的字段说明

单个数据集要在 `OXE_DATASET_CONFIGS` 中有配置。这里会记录 image observation key、state key、动作编码方式等信息。`materialize.py` 会先读取 config，再按训练需要裁剪字段：

```python
dataset_kwargs = deepcopy(OXE_DATASET_CONFIGS[dataset_name])
if dataset_kwargs["action_encoding"] not in [ActionEncoding.EEF_POS, ActionEncoding.EEF_R6]:
    raise ValueError(f"Cannot load `{dataset_name}`; only EEF_POS & EEF_R6 actions supported!")

if dataset_kwargs["action_encoding"] is ActionEncoding.EEF_POS:
    dataset_kwargs["absolute_action_mask"] = [False] * 6 + [True]
    dataset_kwargs["action_normalization_mask"] = [True] * 6 + [False]
```

这段代码给出了 OpenVLA 数据侧支持的动作空间：这里支持 EEF position 和 EEF R6 两类动作编码，并且默认把最后一维 gripper 当作 absolute action，不参与普通动作维度的归一化。

## Transform：统一字段和动作含义

不同 RLDS 数据集原始字段不一致，standardization transform 负责把它们变成 OpenVLA 训练可用的字段。`materialize.py` 会把 dataset name 映射到对应 transform：

```python
dataset_kwargs["standardize_fn"] = OXE_STANDARDIZATION_TRANSFORMS[dataset_name]
```

这一步让后续 pipeline 能稳定读取 `observation`、`task`、`action` 等字段。注册 custom data 时，transform 要把原始数据明确改成 OpenVLA 期待的字段和动作语义。

## 数据加载时的默认选择

OpenVLA 的 `RLDSDataset` 在训练侧默认只取 primary camera 和语言，不加载 depth / proprio：

```python
per_dataset_kwargs, weights = get_oxe_dataset_kwargs_and_weights(
    self.data_root_dir,
    mixture_spec,
    load_camera_views=("primary",),
    load_depth=False,
    load_proprio=False,
    load_language=True,
    action_proprio_normalization_type=NormalizationType.BOUNDS_Q99,
)
```

这解释了为什么 custom data 需要先对齐 primary image、language instruction 和 action。其他相机或 proprio 可以存在于原始 RLDS 中，但默认训练链路不会自动把它们喂给 OpenVLA。

## 从现象反查

| 现象 | 先看哪里 |
| --- | --- |
| `data_mix` 找不到或加载了错误数据集 | `OXE_NAMED_MIXTURES` |
| 相机 key 对不上 | `OXE_DATASET_CONFIGS` 与 `load_camera_views` |
| 动作维度或 gripper 处理异常 | `ActionEncoding`、`absolute_action_mask`、`action_normalization_mask` |
| batch 字段缺失 | `OXE_STANDARDIZATION_TRANSFORMS` |

## 本页小结

- mixture 决定数据集名单和采样权重。
- config 描述单个数据集的相机、状态和动作编码。
- transform 把原始 RLDS 字段改成 OpenVLA 训练字段。
- OpenVLA 默认训练入口使用 primary camera、语言和动作，并采用 `BOUNDS_Q99` 归一化。

## 导航

- 上一节：[OXE 与 RLDS](01-oxe-and-rlds.md)
- 返回上级：[数据与动作统计量](../04-data-and-statistics.md)
- 下一节：[`dataset_statistics.json`](03-dataset-statistics.md)
