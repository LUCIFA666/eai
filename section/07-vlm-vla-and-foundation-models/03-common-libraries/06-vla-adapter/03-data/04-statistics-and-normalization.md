# Statistics 与归一化

目标：理解 `dataset_statistics.json` 如何连接 VLA-Adapter 的训练归一化、checkpoint 保存、评测动作还原和部署请求。

VLA-Adapter 的连续 action head 在归一化动作空间中训练。RLDS pipeline 会根据数据集 statistics 处理 action 和 proprio；评测和部署时，同一份 `dataset_statistics.json` 会被加载到 `model.norm_stats`，用于归一化当前 proprio，并把模型输出还原到环境动作空间。

## Statistics 生成和缓存

statistics 的核心入口在 `prismatic/vla/datasets/rlds/utils/data_utils.py`。`get_dataset_statistics()` 会遍历 trajectory，统计 action 和 proprio 的均值、标准差、最小值、最大值、`q01`、`q99`，并记录 trajectory / transition 数量。

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
    "proprio": {
        "mean": proprios.mean(0).tolist(),
        "std": proprios.std(0).tolist(),
        "max": proprios.max(0).tolist(),
        "min": proprios.min(0).tolist(),
        "q01": np.quantile(proprios, 0.01, axis=0).tolist(),
        "q99": np.quantile(proprios, 0.99, axis=0).tolist(),
    },
}
```

LIBERO 常量使用 `ACTION_PROPRIO_NORMALIZATION_TYPE=BOUNDS_Q99`，因此主线会用 `q01/q99` 把参与归一化的维度映射到 `[-1, 1]`。`make_oxe_dataset_kwargs()` 同时为 `EEF_POS` 设置 action mask，前 6 维参与归一化，gripper 维保留绝对语义。

## 训练阶段如何使用和保存

归一化发生在 RLDS pipeline 内部。`normalize_action_and_proprio()` 会按照 statistics 和 mask 处理 `traj["action"]` 与 `traj["observation"]["proprio"]`。

```python
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

`finetune.py` 创建 `train_dataset` 后会保存 statistics 到 run 目录：

```python
train_dataset = RLDSDataset(...)
save_dataset_statistics(train_dataset.dataset_statistics, run_dir)
```

`save_dataset_statistics()` 输出的文件名固定为 `dataset_statistics.json`。本地 checkpoint 评测时，`--pretrained_checkpoint` 指向的目录需要包含这份文件；官方 HF checkpoint 也会提供同名文件。

## `unnorm_key` 如何选择

评测入口 `experiments/robot/openvla_utils.py::_load_dataset_stats()` 会从本地 checkpoint 或 Hugging Face repo 读取 `dataset_statistics.json`，并赋给 `vla.norm_stats`。

```python
dataset_statistics_path = os.path.join(checkpoint_path, "dataset_statistics.json")
if os.path.isfile(dataset_statistics_path):
    with open(dataset_statistics_path, "r") as f:
        norm_stats = json.load(f)
    vla.norm_stats = norm_stats
```

随后 `experiments/robot/libero/run_libero_eval.py::check_unnorm_key()` 会用 `task_suite_name` 查 key；如果 `libero_spatial` 不存在，而 `libero_spatial_no_noops` 存在，就把 `cfg.unnorm_key` 切到后者。

```python
unnorm_key = cfg.task_suite_name
if unnorm_key not in model.norm_stats and f"{unnorm_key}_no_noops" in model.norm_stats:
    unnorm_key = f"{unnorm_key}_no_noops"

assert unnorm_key in model.norm_stats
cfg.unnorm_key = unnorm_key
```

这段逻辑解释了训练名和评测名之间的关系：训练数据名通常带 `_no_noops`，LIBERO benchmark suite 名不带这个后缀，评测脚本会在 statistics key 层面把两者接起来。

## Proprio normalization 和 action unnormalization

评测和部署里，statistics 有两个实际使用点。`openvla_utils.get_vla_action()` 会先处理输入 proprio：

```python
if cfg.use_proprio:
    proprio = obs["state"]
    proprio_norm_stats = vla.norm_stats[cfg.unnorm_key]["proprio"]
    obs["state"] = normalize_proprio(proprio, proprio_norm_stats)
```

随后模型的 `predict_action()` 会用同一个 `unnorm_key` 还原 action。也就是说，`unnorm_key` 同时决定 proprio 输入尺度和 action 输出尺度。policy server 的 `/act` 响应即使 shape 正确，如果 `unnorm_key` 指向了错误 suite，动作幅度和 gripper 行为仍可能偏离训练分布。

## 检查顺序

| 现象 | 适合检查的文件或字段 |
| --- | --- |
| 训练启动时反复计算 statistics | 数据目录缓存不可写或 hash 依赖变化，先看 statistics cache 日志。 |
| checkpoint 能加载但 eval 报缺少 `unnorm_key` | 打开 `dataset_statistics.json`，核对顶层 key 与 `task_suite_name`。 |
| proprio 输入 shape 正确但动作发散 | 核对 `proprio` statistics、`use_proprio`、`PROPRIO_DIM` 和 checkpoint 组件。 |
| action 维度正确但尺度异常 | 核对 action `q01/q99`、action mask、`ACTION_DIM` 和训练数据来源。 |

## 导航

- 上一节：[RLDSBatchTransform 与 Collator](03-rlds-batch-transform-and-collator.md)
- 返回上级：[数据接口与管线](../03-data.md)
- 下一节：[自定义数据接入](05-custom-data-format.md)
