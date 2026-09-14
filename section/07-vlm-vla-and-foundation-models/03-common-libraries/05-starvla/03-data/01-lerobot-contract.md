# LeRobot 格式约定

目标：理解 StarVLA 的 dataloader 输出什么，以及这些输出怎样被 framework 使用。

先看一个典型 LIBERO 样本：

```python
sample = {
    "image": [primary_image, wrist_image],
    "lang": "put the bowl on the plate",
    "state": np.ndarray(shape=(1, 8)),
    "action": np.ndarray(shape=(8, 7)),
}
```

这里的 `action` 是未来 8 步动作，每一步 7 维。`state` 是当前机器人状态。不同数据集的维度可能不同，具体维度由后面的 `DataConfig` 定义。

## batch

StarVLA 的 VLA batch 通常是 `List[dict]`：

```python
batch = [sample_0, sample_1, ...]
```

PyTorch DataLoader 默认会把多个样本的字段拼成 tensor。这对图像分类没问题，但 VLA 样本里有多视角图像、变长语言和异构状态，不太好现在就拼起来。StarVLA 通过 `collate_fn` 告诉 DataLoader 不做合并，直接把原始样本列表交给 framework：

```python
def collate_fn(batch):
    return batch
```

这种形式和图像分类里常见的 `Tensor[B, C, H, W]` 不同。提前拼成 tensor 会让数据层过早绑定某个模型输入格式，而 VLA 的图像 resize、文本 prompt 和动作处理方式在不同 framework 之间差异很大，应该交给 framework 自己处理。

## 构建入口

VLA 数据入口通常从 `build_dataloader()` 开始：

```python
from starVLA.dataloader.lerobot_datasets import get_vla_dataset, collate_fn

vla_dataset = get_vla_dataset(data_cfg=cfg.datasets.vla_data)
loader = DataLoader(
    vla_dataset,
    batch_size=cfg.datasets.vla_data.per_device_batch_size,
    collate_fn=collate_fn,
)
```

`get_vla_dataset()` 会根据配置读取 LeRobot 数据，并返回单个数据集或混合数据集。

> 为什么保留字典
> 1. 多视角图像可以保持原始顺序，framework 再决定怎样 resize 和送入 VLM。
> 2. 不同 VLM 的 tokenizer、processor 和 prompt 组织方式可以放在各自 framework 内部。
> 3. 不同动作头可以使用同一份原始动作，例如 OFT 做连续回归，FAST 做动作 token，PI/GR00T 做 flow matching。

## 常见字段

| 字段 | 训练期 | 推理期 | 说明 |
|---|---|---|---|
| `image` | 需要 | 需要 | 多视角图像，例如主相机和腕部相机 |
| `lang` | 需要 | 需要 | 自然语言任务描述 |
| `state` | 视模型而定 | 视模型而定 | 本体状态，例如末端位姿或关节值 |
| `action` | 需要 | 通常不需要 | 监督信号，常见形状是 `[horizon, action_dim]` |

## data_mix

训练 YAML 通常会写：

```yaml
datasets:
  vla_data:
    data_root_dir: <DATA_ROOT>/LEROBOT_LIBERO_DATA
    data_mix: libero_goal
```

`data_root_dir` 是数据所在根目录。`data_mix` 是一个名字，用来查找具体包含哪些子数据集。比如 `libero_goal` 可能只加载 goal 任务，`libero_all` 会加载四个 LIBERO 子集。

## 常见问题

| 问题 | 常见原因 | 检查位置 |
|---|---|---|
| batch 是 `List[dict]` | StarVLA 按设计保留原始样本字典 | framework 的 `forward()` |
| 缺少 `lang` | 语言字段映射错误 | `modality.json`、`DataConfig` |
| action shape 不对 | 动作维度或 horizon 不匹配 | `action_keys`、`action_indices`、模型配置 |
| 训练能跑但评测很差 | 图像顺序、gripper 语义或归一化不一致 | `model2*_interface.py`、statistics |

## 小结

- StarVLA 的 VLA batch 通常是 `List[dict]`。
- 样本核心字段是 `image`、`lang`、`state`、`action`。
- 数据层保持通用，模型专属处理放在 framework 内部。
- `data_mix` 用一个名字代表一个或多个 LeRobot 子数据集。

## 动手练习

1. 运行 `rg -n "def collate_fn|return batch" starVLA/dataloader/lerobot_datasets.py`，确认当前 `collate_fn` 直接返回原始 batch。
2. 准备好 LIBERO 数据后运行 dataloader 调试入口，成功输出应生成 `results/debug/dataset_statistics.json`。如果需要查看 batch 字段，可在本地临时打印 `next(iter(dataloader))[0].keys()`。
3. 运行 `rg -n "\[.*image|\[.*lang|\[.*action|\[.*state" starVLA/model/framework/VLM4A/QwenOFT.py starVLA/model/framework/VLM4A/QwenGR00T.py`，比较两个 framework 读取样本字段的位置。

## 导航

- 上一节：[数据接口](../03-data.md)
- 返回上级：[数据接口](../03-data.md)
- 下一节：[02 modality 与 DataConfig](02-modality-and-dataconfig.md)
