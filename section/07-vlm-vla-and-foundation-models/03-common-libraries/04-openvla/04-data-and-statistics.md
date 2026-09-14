# 数据与动作统计量

目标：理解 OpenVLA 的 RLDS / OXE 数据入口，以及 `dataset_statistics.json`、`norm_stats`、`unnorm_key` 怎样共同决定动作尺度。

上一单元已经看过 `predict_action()` 如何用 `unnorm_key` 选择统计量，把归一化动作恢复到数据集尺度。本单元回到数据侧：OpenVLA 训练时怎样读 RLDS 数据，mixture 和 transform 怎样把不同机器人数据统一成模型输入，统计量怎样生成并保存。

## 学习路径

| 页面 | 重点 |
| --- | --- |
| [OXE 与 RLDS](04-data-and-statistics/01-oxe-and-rlds.md) | OpenVLA 为什么使用 Open X-Embodiment / RLDS，以及 RLDS 数据在训练链路中的位置。 |
| [Mixture 与 Transform](04-data-and-statistics/02-mixtures-and-transforms.md) | `OXE_NAMED_MIXTURES`、dataset config 和 standardization transform 怎样配合。 |
| [`dataset_statistics.json`](04-data-and-statistics/03-dataset-statistics.md) | `q01`、`q99`、`mask`、`BOUNDS_Q99` 和 `norm_stats` 的关系。 |
| [自定义数据接入](04-data-and-statistics/04-custom-data.md) | 新数据接入时要对齐哪些字段、统计量和注册入口。 |

## 数据名和统计量 key

OpenVLA 的动作 token 只处理归一化后的动作。动作值怎样归一化、怎样从归一化区间回到原始尺度，要看数据统计量。训练时，数据加载器会按统计量把动作压到 `[-1, 1]`；推理时，`predict_action()` 再用同一组统计量做反归一化。

另一个容易混淆的点是数据集名称。`data_mix` 可以是一个命名 mixture，也可以退化成单个 dataset 名称；`unnorm_key` 指向的是 checkpoint 中保存的统计量 key。两者经常同名或相近，但它们分别出现在数据加载和模型推理两个阶段。

## 源码入口

| 源码入口 | 作用 |
| --- | --- |
| `prismatic/vla/datasets/datasets.py` | PyTorch 侧的 `RLDSDataset` 和 `RLDSBatchTransform`。 |
| `prismatic/vla/datasets/rlds/oxe/mixtures.py` | 命名 mixture 与采样权重。 |
| `prismatic/vla/datasets/rlds/oxe/configs.py` | 单个数据集的相机、状态、动作编码配置。 |
| `prismatic/vla/datasets/rlds/oxe/transforms.py` | 数据集到统一 RLDS 字段的 standardization transform。 |
| `prismatic/vla/datasets/rlds/utils/data_utils.py` | 归一化、统计量计算和 `dataset_statistics.json` 保存。 |

## 导航

- 上一节：[`predict_action` 动作推理](03-model-and-action-inference/03-predict-action.md)
- 返回上级：[OpenVLA](../04-openvla.md)
- 下一节：[OXE 与 RLDS](04-data-and-statistics/01-oxe-and-rlds.md)
