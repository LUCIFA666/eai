# `dataset_statistics.json`

目标：理解 OpenVLA 如何计算、保存和使用动作统计量，以及 `unnorm_key` 为什么要和统计量 key 对齐。

OpenVLA 的 action tokenizer 只处理归一化动作。训练数据进入 tokenizer 前，会按数据统计量归一化到 `[-1, 1]`；推理时，`predict_action()` 会根据 `unnorm_key` 取出同一类统计量，把归一化动作恢复到目标数据集的尺度。

## 统计量包含什么

OpenVLA 的 RLDS 工具会为 action 和 proprio 计算均值、方差、最小最大值、1% quantile 和 99% quantile：

```python
metadata = {
    "action": {
        "mean": actions.mean(0).tolist(),
        "std": actions.std(0).tolist(),
        "max": actions.max(0).tolist(),
        "min": actions.min(0).tolist(),
        "q01": np.quantile(actions, 0.01, axis=0).tolist(),
        "q99": np.quantile(actions, 0.99, axis=0).tolist(),
    },
}
```

`q01` 和 `q99` 是 OpenVLA 主线最常遇到的字段。它们用于把动作压到 `[-1, 1]`，也用于推理时恢复动作尺度。

## `BOUNDS_Q99` 怎样归一化

OpenVLA 的 RLDSDataset 默认使用 `NormalizationType.BOUNDS_Q99`。归一化时，代码取 `q01` 和 `q99` 作为上下界，并按 `mask` 选择哪些维度参与归一化：

```python
elif normalization_type in [NormalizationType.BOUNDS, NormalizationType.BOUNDS_Q99]:
    if normalization_type == NormalizationType.BOUNDS_Q99:
        low = metadata[key]["q01"]
        high = metadata[key]["q99"]
    mask = metadata[key].get("mask", tf.ones_like(metadata[key]["min"], dtype=tf.bool))
    traj = dl.transforms.selective_tree_map(
        traj,
        match=lambda k, _: k == traj_key,
        map_fn=lambda x: tf.where(
            mask,
            tf.clip_by_value(2 * (x - low) / (high - low + 1e-8) - 1, -1, 1),
            x,
        ),
    )
```

这段代码和 `predict_action()` 的反归一化公式是对应关系。训练时从原始动作到 `[-1, 1]`；推理时从 `[-1, 1]` 回到 `q01` / `q99` 定义的动作尺度。

## `mask` 影响哪些维度

`mask` 用来跳过不应该按连续动作区间归一化的维度。OXE materialize 里对 end-effector action 的默认处理是：最后一维 gripper 是 absolute action，普通动作维度参与归一化。

```python
if dataset_kwargs["action_encoding"] is ActionEncoding.EEF_POS:
    dataset_kwargs["absolute_action_mask"] = [False] * 6 + [True]
    dataset_kwargs["action_normalization_mask"] = [True] * 6 + [False]
```

这就是 gripper 维度需要单独检查的原因。动作尺度异常时，不能只看 `q01` / `q99` 数值，也要看对应维度是否被 `mask` 覆盖。

## `dataset_statistics.json` 什么时候保存

训练和微调脚本会把 dataset statistics 写到 checkpoint 目录。LoRA fine-tuning 中，数据集初始化后会保存一次统计量：

```python
vla_dataset = RLDSDataset(
    cfg.data_root_dir,
    cfg.dataset_name,
    batch_transform,
    resize_resolution=tuple(vla.module.config.image_sizes),
    shuffle_buffer_size=cfg.shuffle_buffer_size,
    image_aug=cfg.image_aug,
)

save_dataset_statistics(vla_dataset.dataset_statistics, run_dir)
```

保存函数的核心写盘逻辑如下，实际实现还会先把 numpy 数组和计数值转成 JSON 可写格式：

```python
def save_dataset_statistics(dataset_statistics, run_dir):
    out_path = run_dir / "dataset_statistics.json"
    with open(out_path, "w") as f_json:
        json.dump(dataset_statistics, f_json, indent=2)
```

本地 fine-tuned checkpoint 如果缺少这个文件，后续部署或转换时就可能找不到反归一化统计量。这个问题属于 checkpoint 内容不完整，不是 `predict_action()` 本身的动作生成失败。

## `unnorm_key` 和统计量 key

`dataset_statistics.json` 通常是一个 dict，外层 key 对应数据集或 mixture。模型加载后，这些统计量会成为 `norm_stats`。推理时传入的 `unnorm_key` 必须能在 `norm_stats` 中找到。

前一页已经看过 `_check_unnorm_key()`：如果 checkpoint 只有一套统计量，可以省略 key；如果有多套统计量，就要显式传入。key 对上只能说明能取到统计量，任务是否匹配还要看当前图像来源、语言指令和机器人动作空间。

## 本页小结

- OpenVLA 使用 `q01` / `q99` 把动作压到 `[-1, 1]`，推理时再按同一组统计量恢复尺度。
- `mask` 决定哪些动作维度参与归一化，gripper 通常需要单独看。
- `dataset_statistics.json` 会随训练或微调 checkpoint 保存，加载后进入模型的 `norm_stats`。
- `unnorm_key` 要对到统计量 key；key 对上后，还要检查任务和动作空间是否匹配。

## 导航

- 上一节：[Mixture 与 Transform](02-mixtures-and-transforms.md)
- 返回上级：[数据与动作统计量](../04-data-and-statistics.md)
- 下一节：[自定义数据接入](04-custom-data.md)
