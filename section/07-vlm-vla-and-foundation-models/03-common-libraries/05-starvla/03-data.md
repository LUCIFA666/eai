# 数据接口

目标：理解 StarVLA 如何把机器人轨迹整理成模型能使用的样本字典，并看清字段映射、数据配置、数据混合和归一化各自负责什么。

VLA 数据可以先想成四类信息：图像、语言、状态和动作。

```python
example = {
    "image": [primary_image, wrist_image],
    "lang": "pick up the bowl",
    "state": robot_state,
    "action": future_actions,
}
```

StarVLA 的数据层围绕 LeRobot 格式组织。不同 benchmark 的原始字段会先通过 `modality.json` 和 `DataConfig` 映射成统一样本，再交给 framework。这样同一份 LIBERO 数据可以训练 OFT、FAST、PI 或 GR00T 等不同模型变体。

## 本节目标

本节围绕下面几个问题展开：

1. dataloader 输出的样本字典长什么样？
2. `modality.json` 和 Python `DataConfig` 分别管理什么？
3. 多个子数据集怎样通过 `data_mix` 组合成训练集？
4. VLM 图文数据怎样加入协同训练？
5. `dataset_statistics.json` 为什么训练和部署都需要？

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [01 LeRobot 格式约定](03-data/01-lerobot-contract.md) | VLA 样本字典如何产生 | `get_vla_dataset()`、`collate_fn`、样本 key |
| [02 modality 与 DataConfig](03-data/02-modality-and-dataconfig.md) | 字段映射在哪里定义 | `modality.json`、`DataConfig` |
| [03 mixture 注册表](03-data/03-mixture-registry.md) | 多数据集如何混合 | `DATASET_NAMED_MIXTURES`、robot type、数据权重 |
| [04 VLM 协同训练数据](03-data/04-vlm-cotrain-data.md) | 图文数据如何并入训练 | LLaVA JSON、VLM dataloader、损失权重 |
| [05 统计与归一化](03-data/05-statistics-and-normalization.md) | 动作如何归一化和还原 | transform、`dataset_statistics.json`、反归一化 |

## 导航

- 上一节：[安装与链路验证](02-setup.md)
- 返回上级：[StarVLA](../05-starvla.md)
- 下一节：[01 LeRobot 格式约定](03-data/01-lerobot-contract.md)
