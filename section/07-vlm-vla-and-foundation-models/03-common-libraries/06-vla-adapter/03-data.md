# 数据接口与管线

目标：理解 VLA-Adapter 如何用 RLDS / OXE 定义数据接口，并把 LIBERO 数据一路接到训练、评测和部署。

本章沿着源码链路梳理 VLA-Adapter 如何读取和使用这批数据：`--data_root_dir data/libero` 指向 TFDS / RLDS 根目录，`--dataset_name libero_spatial_no_noops` 选择 OXE registry 中的数据定义，`--num_images_in_input 2` 打开 primary + wrist 两路图像，`--use_proprio True` 让 proprio 字段进入训练和评测。

论文附录中的 LIBERO 设置使用第三人称图像、wrist 图像、语言指令和 7D Franka action；源码里的 LIBERO-Pro 主线进一步把动作组织成 `NUM_ACTIONS_CHUNK=8` 的连续动作块，并使用 `PROPRIO_DIM=8` 的状态输入。本章重点看这些字段如何从 RLDS 样本进入 batch，又如何通过 `dataset_statistics.json` 连接训练、评测和 policy server。

## 数据接口与处理主线

```text
FinetuneConfig
  -> data_root_dir + dataset_name
  -> RLDSDataset
  -> OXE_NAMED_MIXTURES / OXE_DATASET_CONFIGS / OXE_STANDARDIZATION_TRANSFORMS
  -> standardize_fn + trajectory transform
  -> RLDSBatchTransform
  -> PaddedCollatorForActionPrediction
  -> training batch + dataset_statistics.json
  -> eval / deploy unnorm_key
```

这条链路把 VLA-Adapter 的数据接口与管线分成五个层次：字段约束、注册与标准化、batch 生成、statistics 共享、自定义数据接入。读源码时可以沿着这五层定位问题：找不到数据通常在 `data_root_dir` 或 `dataset_name`，字段或 shape 报错通常在 OXE 配置和标准化函数，forward 阶段报错通常在 transform / collator，评测动作尺度异常通常回到 statistics 和 `unnorm_key`。

## 学习路径

| 页面 | 关注点 | 源码入口 | 适用场景 |
| --- | --- | --- | --- |
| [数据接口与字段约束](03-data/01-data-interface-and-field-constraints.md) | VLA-Adapter 期望一条样本和一个 batch 长什么样 | `finetune.py`、`RLDSDataset`、`PaddedCollatorForActionPrediction` | 先对齐 image、language、action、proprio、statistics 的共同边界 |
| [OXE Registry 与字段标准化](03-data/02-oxe-registry-and-standardization.md) | `dataset_name` 如何找到 LIBERO 字段、mixture 和标准化函数 | `oxe/mixtures.py`、`oxe/configs.py`、`oxe/transforms.py`、`oxe/materialize.py` | 排查数据名、camera view、state key、action encoding |
| [RLDSBatchTransform 与 Collator](03-data/03-rlds-batch-transform-and-collator.md) | 标准化后的 RLDS 样本如何变成模型 batch | `prismatic/vla/datasets/datasets.py`、`prismatic/util/data_utils.py` | 排查 prompt、wrist image、action chunk、proprio、batch shape |
| [Statistics 与归一化](03-data/04-statistics-and-normalization.md) | `dataset_statistics.json` 如何贯穿训练、评测和部署 | `rlds/utils/data_utils.py`、`openvla_utils.py`、`run_libero_eval.py` | 排查 action / proprio 尺度、checkpoint statistics、`unnorm_key` |
| [自定义数据接入](03-data/05-custom-data-format.md) | 改数据格式、接自定义 RLDS、换 action / proprio 时的改动面 | OXE registry、constants、batch transform、eval / deploy 入口 | 从 LIBERO-Pro 主线扩展到新的数据来源或机器人字段 |

## 导航

- 上一节：[路径与环境变量](02-setup/06-paths-and-env.md)
- 返回上级：[VLA-Adapter](../06-vla-adapter.md)
- 下一节：[数据接口与字段约束](03-data/01-data-interface-and-field-constraints.md)
