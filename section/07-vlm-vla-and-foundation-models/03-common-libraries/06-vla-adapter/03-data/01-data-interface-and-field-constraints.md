# 数据接口与字段约束

目标：理解 VLA-Adapter 对 LIBERO 数据样本、训练 batch、statistics 和评测输入的共同约束。

VLA-Adapter 的数据接口围绕一条 LIBERO-Pro 主线组织：第三人称图像、wrist 图像、语言指令、7D action、8-step action chunk 和 8D proprio。`vla-scripts/finetune.py` 把这些约束从训练参数接到数据加载器，后续的 OXE registry、`RLDSBatchTransform`、collator、评测脚本和 policy server 都沿用同一套字段含义。

```python
# vla-scripts/finetune.py
use_wrist_image = cfg.num_images_in_input > 1

batch_transform = RLDSBatchTransform(
    action_tokenizer,
    processor.tokenizer,
    image_transform=processor.image_processor.apply_transform,
    prompt_builder_fn=PurePromptBuilder,
    use_wrist_image=use_wrist_image,
    use_proprio=cfg.use_proprio,
    use_minivlm=cfg.use_minivlm,
)
train_dataset = RLDSDataset(
    cfg.data_root_dir,
    cfg.dataset_name,
    batch_transform,
    resize_resolution=tuple(vla.module.config.image_sizes),
    image_aug=cfg.image_aug,
)
```

这里的 `data_root_dir` 只负责定位 TFDS / RLDS 数据目录；`dataset_name` 才决定字段映射、标准化函数、action mask 和 statistics key。`num_images_in_input` 与 `use_proprio` 会继续影响 transform、模型组件和评测输入。

## 样本字段约束

进入 `RLDSBatchTransform.__call__()` 时，样本已经经过 OXE 的标准化和 trajectory transform。LIBERO 主线里，transform 关心的字段可以简化成下面这组结构：

```python
rlds_batch = {
    "dataset_name": "libero_spatial_no_noops",
    "observation": {
        "image_primary": ...,      # primary camera sequence
        "image_wrist": ...,        # wrist camera sequence
        "proprio": ...,            # 8D state after OXE standardization
    },
    "task": {
        "language_instruction": ...,
    },
    "action": ...,                 # [NUM_ACTIONS_CHUNK, ACTION_DIM]
}
```

`image_primary` 和 `image_wrist` 由 OXE pipeline 依据 `image_obs_keys` 生成，不直接沿用原始 TFDS schema 中的字段名。LIBERO 的 `proprio` 来自 `state` 拆分出的 `EEF_state` 与 `gripper_state`；action 维度由 `ACTION_DIM=7` 约束，动作块长度由 `NUM_ACTIONS_CHUNK=8` 约束。

## Batch 字段约束

`PaddedCollatorForActionPrediction` 把多条 transform 输出合成 PyTorch batch。训练 step 看到的字段如下：

```python
batch = {
    "pixel_values": ...,       # primary / wrist image tensors after processor transform
    "input_ids": ...,          # tokenized prompt and action-token region
    "attention_mask": ...,
    "labels": ...,             # non-action region is masked by IGNORE_INDEX
    "actions": ...,            # [B, NUM_ACTIONS_CHUNK, ACTION_DIM]
    "proprio": ...,            # [B, PROPRIO_DIM] when use_proprio=True
    "dataset_names": ...,      # kept for records and mixed datasets
}
```

`pixel_values` 的具体 channel 数由 processor 的 image transform 和输入图像数量共同决定；collator 在存在 wrist 图像时会把 primary 和 wrist 的图像张量沿 channel 维拼接。`actions` 进入 L1 action head 的监督目标，`proprio` 在 `use_proprio=True` 时进入 `ProprioProjector`。

## 训练、评测和部署共用的字段含义

训练阶段，RLDS pipeline 用 dataset statistics 归一化 action 和 proprio，`finetune.py` 会把 `train_dataset.dataset_statistics` 保存为 `dataset_statistics.json`。评测和部署阶段，`openvla_utils._load_dataset_stats()` 再把同一个文件加载到 `model.norm_stats`，用于两件事：

| 使用点 | 字段 | 影响 |
| --- | --- | --- |
| proprio normalization | `model.norm_stats[cfg.unnorm_key]["proprio"]` | 当前观测里的 `obs["state"]` 被映射到训练分布。 |
| action unnormalization | `model.norm_stats[cfg.unnorm_key]["action"]` | action head 输出被还原到 LIBERO 环境动作空间。 |

这也是数据接口和模型组件之间最容易配错的位置：`dataset_name`、`ACTION_DIM`、`PROPRIO_DIM`、`NUM_ACTIONS_CHUNK`、`num_images_in_input`、`use_proprio`、`dataset_statistics.json` 和 `unnorm_key` 需要对应到同一条训练链路，这样后续的 batch、statistics 和动作还原才会一致。某个字段配错时，错误可能在 TFDS 读取阶段暴露，也可能等到 rollout 时表现为动作尺度异常。

## 定位边界

| 现象 | 更适合先看的位置 |
| --- | --- |
| TFDS builder 或目录找不到 | `data_root_dir`、数据目录版本、setup 章节的数据体检。 |
| 缺少 `image_wrist`、`proprio` 或 language 字段 | `OXE_DATASET_CONFIGS` 和 `OXE_STANDARDIZATION_TRANSFORMS`。 |
| 第一个 batch 生成失败 | `RLDSBatchTransform`、`PaddedCollatorForActionPrediction`、`num_images_in_input`。 |
| forward 阶段 action / proprio shape 不一致 | `ACTION_DIM`、`PROPRIO_DIM`、`NUM_ACTIONS_CHUNK`、action head、proprio projector。 |
| eval / deploy 返回 action shape 正常但动作不可信 | `dataset_statistics.json`、`unnorm_key`、checkpoint 组件来源。 |

## 导航

- 上一节：[数据接口与管线](../03-data.md)
- 返回上级：[数据接口与管线](../03-data.md)
- 下一节：[OXE Registry 与字段标准化](02-oxe-registry-and-standardization.md)
