# 自定义数据接入

目标：知道把新数据接入 OpenVLA 时要对齐哪些接口，以及开始训练前要检查哪些数据条件。

OpenVLA 支持在新数据上继续训练。数据侧最稳妥的路径是把数据转换成 RLDS / TFDS 格式，再注册到 OXE 数据管线中。这样可以复用已有的 mixture、transform、统计量计算和 `RLDSDataset`。

## RLDS 接入方式

README 给出的 custom data 路线优先推荐 RLDS。对应到源码，需要补齐三类注册信息：

| 需要补齐 | 作用 |
| --- | --- |
| `OXE_NAMED_MIXTURES` | 给训练命令使用的 `dataset_name` 或 mixture 名称。 |
| `OXE_DATASET_CONFIGS` | 描述相机字段、状态字段、动作编码和数据目录结构。 |
| `OXE_STANDARDIZATION_TRANSFORMS` | 把原始 RLDS 字段转成 OpenVLA 训练链路读取的字段。 |

这三处对齐后，`RLDSDataset` 才能把数据读成图像、语言指令、动作和统计量。

## 数据字段检查

接入新数据时，下面这些字段决定数据能否进入训练链路：

| 字段或配置 | 检查重点 |
| --- | --- |
| primary image | 是否能通过 `load_camera_views=("primary",)` 读到主相机图像。 |
| language instruction | 是否能进入 `task["language_instruction"]`。 |
| action | 维度、单位、相对 / 绝对含义是否和训练配置一致。 |
| action encoding | 是否属于 OpenVLA 当前支持的 EEF action 类型。 |
| normalization mask | gripper 等维度是否应跳过连续区间归一化。 |
| statistics key | 保存后的 key 是否能作为后续 `unnorm_key` 使用。 |

这些检查比直接跑长时间微调更早暴露问题。图像读不到、语言字段为空、动作维度不对，都会在 batch transform 或统计量阶段反映出来。

## 非 RLDS 数据集入口

源码里保留了 `DummyDataset` 作为非 RLDS 数据集的示例入口。它展示了非 RLDS 入口至少要准备哪些内容：dataset 对象要持有可反归一化的 statistics，`__getitem__` 生成的样本要能产出 `pixel_values`、`input_ids` 和 `labels`。

```python
self.dataset_statistics = {
    "dummy_dataset": {
        "action": {"q01": np.zeros((7,), dtype=np.float32), "q99": np.ones((7,), dtype=np.float32)}
    }
}
```

这里的 `dataset_statistics` 挂在 dataset 对象上；instruction 和 action tokens 会在样本构造过程中折进 prompt 和 target，dataloader 交给训练循环的是张量化后的 `pixel_values`、`input_ids` 和 `labels`。

这个入口适合理解接口形状，但不适合作为课程中的默认路线。非 RLDS Dataset 还要自己处理 epoch、shuffle、统计量保存和训练循环适配；这些工作容易和 fine-tuning 逻辑混在一起。

## 数据接入检查项

数据接入检查项包括：字段能读，动作维度正确，动作能按统计量归一化，checkpoint 目录能带上 `dataset_statistics.json`，推理时使用的 `unnorm_key` 能命中统计量 key。这里任何一项不对，后面的训练日志即使正常下降，也可能无法说明策略能在目标任务上闭环执行。

## 本页小结

- 新数据优先转换成 RLDS，并注册 mixture、config 和 standardization transform。
- primary image、language instruction、action、normalization mask 和 statistics key 是数据接入时的核心字段。
- `DummyDataset` 可以帮助理解接口形状，但默认路线仍然是 RLDS。
- 开始训练前要确认字段、动作维度、统计量文件和 `unnorm_key` 都能对上。

## 导航

- 上一节：[`dataset_statistics.json`](03-dataset-statistics.md)
- 返回上级：[数据与动作统计量](../04-data-and-statistics.md)
- 下一节：[LoRA 微调](../05-finetuning.md)
