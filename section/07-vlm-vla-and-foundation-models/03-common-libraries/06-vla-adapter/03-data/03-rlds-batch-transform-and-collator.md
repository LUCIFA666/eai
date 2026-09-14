# RLDSBatchTransform 与 Collator

目标：理解标准化后的 LIBERO RLDS 样本如何变成 VLA-Adapter 模型 forward 和 action head loss 使用的 batch。

`RLDSDataset` 负责从 TFDS / RLDS pipeline 取样本，`RLDSBatchTransform` 负责把单条样本整理成训练样本，`PaddedCollatorForActionPrediction` 再把多条样本堆成 PyTorch batch。训练入口 `vla-scripts/finetune.py` 把三者串起来，核心行为集中在 `prismatic/vla/datasets/datasets.py` 和 `prismatic/util/data_utils.py`。

## Transform 读取哪些字段

`RLDSBatchTransform.__call__()` 直接读取已经标准化后的字段：

```python
dataset_name = rlds_batch["dataset_name"]
img = Image.fromarray(rlds_batch["observation"]["image_primary"][0])
lang = rlds_batch["task"]["language_instruction"].decode().lower()
actions = rlds_batch["action"]
future_actions = rlds_batch["action"][1:]
```

这里的 `actions` 已经包含当前步和未来 action window。`RLDSDataset` 构造 trajectory transform 时使用 `future_action_window_size=NUM_ACTIONS_CHUNK-1`，LIBERO 常量中 `NUM_ACTIONS_CHUNK=8`，所以 action head 看到的是 8 个时间步的连续动作块。`ACTION_DIM=7`，对应 6D 末端控制和 gripper。

## Prompt 和 `use_minivlm`

课程主线的 tiny Prismatic / Qwen backbone 使用 `--use_minivlm True`。这个 flag 会让 transform 切到 `QwenPromptBuilder`，并把 action tokenizer 产生的 action chunk token 放进输入序列。

```python
if self.use_minivlm:
    self.prompt_builder_fn = QwenPromptBuilder
    future_actions_string = self.action_tokenizer(future_actions, self.use_minivlm)
    current_action_string = self.action_tokenizer(current_action, self.use_minivlm)
    conversation = [
        {"from": "human", "value": f"What action should the robot take to {lang}?"},
        {"from": "gpt", "value": ""},
    ]
else:
    future_actions_string = "".join(self.action_tokenizer(future_actions, use_minivlm=False))
```

训练和评测侧需要落在同一套 prompt 分支上。`experiments/robot/openvla_utils.py::get_vla_action()` 在 `use_minivlm=True` 时也会构造 Qwen 风格 prompt；如果 checkpoint 来自 MiniVLM 训练，但评测走了 OpenVLA prompt 分支，模型可以完成一次 forward，动作质量仍会受影响。

## Transform 输出字典

transform 会把图像、token、action、proprio 和数据集名放进同一个字典。非 action token 的 label 会被 `IGNORE_INDEX` 屏蔽，action head 的连续监督目标则来自 `actions` 字段。

```python
return_dict = dict(
    pixel_values=pixel_values,
    input_ids=input_ids,
    labels=labels,
    dataset_name=dataset_name,
    actions=actions,
)

if self.use_wrist_image:
    return_dict["pixel_values_wrist"] = torch.cat(all_wrist_pixels, dim=0)
if self.use_proprio and "proprio" in rlds_batch["observation"]:
    return_dict["proprio"] = rlds_batch["observation"]["proprio"]
```

`use_wrist_image` 来自 `cfg.num_images_in_input > 1`。LIBERO-Pro 主线设置为 2，因此 transform 会遍历 observation 中包含 `wrist` 的图像字段。`use_proprio=True` 时，样本里存在 `observation["proprio"]` 才会把 proprio 放入返回字典；缺失 proprio 往往说明 OXE `state_obs_keys` 或标准化函数没有对齐。

## Collator 组成训练 batch

`PaddedCollatorForActionPrediction` 的工作更接近 batch 组装：padding token 序列、拼接图像、堆叠 action 和 proprio。

```python
input_ids = pad_sequence(input_ids, batch_first=True, padding_value=self.pad_token_id)
labels = pad_sequence(labels, batch_first=True, padding_value=IGNORE_INDEX)
attention_mask = input_ids.ne(self.pad_token_id)

if "pixel_values_wrist" in instances[0]:
    pixel_values = torch.cat(
        (torch.stack(pixel_values), torch.stack(pixel_values_wrist)),
        dim=1,
    )
else:
    pixel_values = torch.stack(pixel_values)

actions = torch.stack([torch.from_numpy(np.copy(instance["actions"])) for instance in instances])
```

最终 batch 中的关键字段可以按下面的方式理解：

| 字段 | 来源 | 后续使用 |
| --- | --- | --- |
| `pixel_values` | primary 图像，存在 wrist 时沿 channel 维拼接 | vision backbone，受 `num_images_in_input` 影响 |
| `input_ids` / `attention_mask` / `labels` | prompt 与 action token 区域 | VLM forward 和 language-model style loss |
| `actions` | `rlds_batch["action"]` | L1 action head 的连续动作监督 |
| `proprio` | `observation["proprio"]` | `ProprioProjector`，受 `use_proprio` 和 `PROPRIO_DIM` 影响 |
| `dataset_names` | `dataset_name` | 记录样本来源，尤其适合 mixed dataset 排查 |

训练 step 在 `run_forward_pass()` 中读取这些字段。`batch["actions"]` 与 action head 输出计算 L1 loss，`batch["proprio"]` 在 `use_proprio=True` 时随 `proprio_projector` 传入模型。图像数量、proprio 维度和 action chunk 长度如果没有和模型组件对齐，错误通常会在这个阶段暴露。

## 排查入口

| 现象 | 先看哪些实现 |
| --- | --- |
| wrist 图像缺失或拼接 shape 不对 | `num_images_in_input`、`image_obs_keys.wrist`、`RLDSBatchTransform.use_wrist_image` |
| `proprio` 为 `None` 或维度不对 | `use_proprio`、`state_obs_keys`、`libero_dataset_transform`、`PROPRIO_DIM` |
| action loss shape 不匹配 | `NUM_ACTIONS_CHUNK`、`ACTION_DIM`、`future_action_window_size` |
| token 序列和训练 checkpoint 不匹配 | `use_minivlm`、`QwenPromptBuilder`、评测侧 `get_vla_action()` |

## 导航

- 上一节：[OXE Registry 与字段标准化](02-oxe-registry-and-standardization.md)
- 返回上级：[数据接口与管线](../03-data.md)
- 下一节：[Statistics 与归一化](04-statistics-and-normalization.md)
