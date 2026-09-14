# mixture 注册表

目标：理解 `data_mix` 怎样用一个名字代表一组数据集，以及这个名字为什么会影响训练和部署。

训练时我们常常不只用一个数据集。以 LIBERO 为例，可能只训练 `libero_goal`，也可能把 `spatial`、`object`、`goal` 和 `libero_10` 混在一起训练。StarVLA 用 `data_mix` 表示这种选择。

## YAML 里的 data_mix

训练 YAML 里通常写：

```yaml
datasets:
  vla_data:
    data_root_dir: <DATA_ROOT>/LEROBOT_LIBERO_DATA
    data_mix: libero_all
```

这里的 `data_root_dir` 是数据根目录，`data_mix` 是一个注册名。`libero_all` 的定义在 benchmark 的 `data_config.py` 里：

```python
DATASET_NAMED_MIXTURES = {
    "libero_all": [
        ("libero_object_no_noops_1.0.0_lerobot", 1.0, "libero_franka"),
        ("libero_goal_no_noops_1.0.0_lerobot", 1.0, "libero_franka"),
        ("libero_spatial_no_noops_1.0.0_lerobot", 1.0, "libero_franka"),
        ("libero_10_no_noops_1.0.0_lerobot", 1.0, "libero_franka"),
    ],
    "libero_goal": [
        ("libero_goal_no_noops_1.0.0_lerobot", 1.0, "libero_franka"),
    ],
}
```

每个三元组是：

```text
(dataset_name, weight, robot_type)
```

### dataset_name

`dataset_name` 是相对于 `data_root_dir` 的子目录名。例如：

```text
<DATA_ROOT>/LEROBOT_LIBERO_DATA/libero_goal_no_noops_1.0.0_lerobot
```

如果路径报错，先把 `data_root_dir` 和 `dataset_name` 手动拼起来，校验目录是否真的存在。

### weight

`weight` 是混合采样权重。它决定训练时不同子数据集被采到的相对频率。

```python
("libero_goal_no_noops_1.0.0_lerobot", 2.0, "libero_franka")
```

这表示 goal 数据会比权重为 1.0 的数据更常被采样。权重会改变模型看到的数据分布，因此它也是实验设计的一部分。

### robot_type

`robot_type` 决定用哪套字段和归一化配置：

```python
ROBOT_TYPE_CONFIG_MAP = {
    "libero_franka": Libero4in1DataConfig(),
}
```

同一个 mixture 里可以包含多个机器人类型。多机器人混训时，要特别关注动作维度、归一化统计和部署时的 `unnorm_key`。

## 加载流程

简化后的数据集构建流程如下：

```python
data_root_dir = cfg.datasets.vla_data.data_root_dir
data_mix = cfg.datasets.vla_data.data_mix
mixture = DATASET_NAMED_MIXTURES[data_mix]

for dataset_name, weight, robot_type in mixture:
    dataset_path = Path(data_root_dir) / dataset_name
    data_config = ROBOT_TYPE_CONFIG_MAP[robot_type]
    # 构建单个 LeRobot 数据集，再按 weight 混合
```

所以 `data_mix` 报错时，通常检查三件事：注册名是否拼对，当前 benchmark 的 `data_config.py` 是否被加载，数据目录是否存在。

## 部署也需要 data_mix

部署时模型输出的是标准化动作。StarVLA 需要知道训练时用了哪个 `robot_type`，才能找到正确的反归一化方式。这个信息来自训练配置里的 `data_mix`。

简化逻辑是：

```text
config.yaml 中的 data_mix
  -> DATASET_NAMED_MIXTURES[data_mix]
  -> robot_type
  -> ROBOT_TYPE_CONFIG_MAP[robot_type]
  -> transform 和 dataset_statistics.json
  -> 反归一化动作
```

这也是 checkpoint 目录里必须保留 `config.yaml` 和 `dataset_statistics.json` 的原因。

## 多机器人混训

多机器人 mixture 可能长这样：

```python
DATASET_NAMED_MIXTURES = {
    "multi_robot": [
        ("dataset_a", 1.0, "robot_a"),
        ("dataset_b", 1.0, "robot_b"),
    ],
}
```

这时部署请求通常要明确指定使用哪套归一化：

```python
request = {
    "examples": [example],
    "unnorm_key": "robot_a",
}
```

server metadata 会列出可用 key，client 可以据此选择。

## 小结

- `data_mix` 是一个注册名，用来代表一个或多个子数据集。
- mixture 三元组是 `(dataset_name, weight, robot_type)`。
- `dataset_name` 和 `data_root_dir` 拼成真实路径。
- `robot_type` 决定字段选择和归一化方式。
- 部署反归一化也依赖 `data_mix`。

## 动手练习

1. 运行 `rg -n "libero_all|libero_goal|libero_10|libero_spatial|libero_object" examples/LIBERO/train_files/data_registry/data_config.py`，列出 `libero_all` 包含的四个子数据集。
2. 准备好数据后，把 `data_root_dir` 和 `dataset_name` 拼成真实路径并执行 `test -d <DATA_ROOT>/LEROBOT_LIBERO_DATA/<dataset_name>`。成功时返回码为 0。
3. 运行 `rg -n "DATASET_NAMED_MIXTURES|unnorm_key|dataset_statistics" deployment/model_server/policy_norm_processor.py`，找到部署阶段如何复用数据注册信息。

## 导航

- 上一节：[02 modality 与 DataConfig](02-modality-and-dataconfig.md)
- 返回上级：[数据接口](../03-data.md)
- 下一节：[04 VLM 协同训练数据](04-vlm-cotrain-data.md)
