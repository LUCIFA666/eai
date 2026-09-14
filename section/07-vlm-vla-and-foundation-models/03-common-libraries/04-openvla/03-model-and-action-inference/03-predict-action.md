# `predict_action` 动作推理

目标：读懂 OpenVLA 推理时如何从 generated token ids 得到连续动作，并知道 `unnorm_key` 在模型侧如何生效。

上一单元的最小推理走 Hugging Face AutoClass 路径：`AutoProcessor` 先把 prompt 和图像变成模型输入，再调用 `OpenVLAForActionPrediction.predict_action()`。这一页从这条路径开始，看生成、decode 和反归一化各自做什么。

## HF 路径从 processor 输出开始

在 HF 路径里，prompt 和图像已经由 processor 处理成 `input_ids`、`attention_mask` 和 `pixel_values`。`predict_action()` 接收这些张量后，会先检查 prompt 末尾是否带有 Llama 需要的空 token；缺失时补上 token id `29871`，让推理输入和训练时的格式对齐。

这一步影响的是 prompt token 序列。图像预处理已经在 processor 中完成，动作统计量也还没有参与。

## 生成长度和动作维度

OpenVLA 的生成长度来自当前动作维度。模型会通过 `unnorm_key` 找到当前动作统计量，再用统计量里的 `q01` 长度确定 action dim：

```python
generated_ids = self.generate(
    input_ids,
    max_new_tokens=self.get_action_dim(unnorm_key),
    **kwargs,
)
predicted_action_token_ids = generated_ids[
    0, -self.get_action_dim(unnorm_key) :
].cpu().numpy()
```

这里有两个检查点。第一，`max_new_tokens` 应该等于动作维度；OpenVLA 主线常见返回 7 维动作。第二，模型输出的最后几个 token ids 才会被当作 action tokens，前面的 prompt tokens 只提供上下文。

## token ids 到归一化动作

HF 版本的 `predict_action()` 在类初始化时已经建立了 action bins 和 bin centers。拿到 action token ids 后，它用词表大小反推 bin 编号，再查 bin center：

```python
discretized_actions = self.vocab_size - predicted_action_token_ids
discretized_actions = np.clip(
    discretized_actions - 1,
    a_min=0,
    a_max=self.bin_centers.shape[0] - 1,
)
normalized_actions = self.bin_centers[discretized_actions]
```

这段逻辑和 `ActionTokenizer.decode_token_ids_to_actions()` 对应。区别在于 HF 版本把解码逻辑直接放进 `OpenVLAForActionPrediction`，便于 `AutoModelForVision2Seq` 加载后直接调用。

## `unnorm_key` 选择哪套统计量

归一化动作还要恢复到数据集尺度。模型会根据 `unnorm_key` 取出统计量，然后用 `q01`、`q99` 和 `mask` 做反归一化：

```python
action_norm_stats = self.get_action_stats(unnorm_key)
mask = action_norm_stats.get("mask", np.ones_like(action_norm_stats["q01"], dtype=bool))
action_high, action_low = np.array(action_norm_stats["q99"]), np.array(action_norm_stats["q01"])
actions = np.where(
    mask,
    0.5 * (normalized_actions + 1) * (action_high - action_low) + action_low,
    normalized_actions,
)
```

`mask` 表示哪些维度要按统计量恢复尺度。没有被 mask 覆盖的维度会保留归一化值。动作尺度异常时，这里要和 checkpoint 里的统计量一起看。

## key 检查规则

`_check_unnorm_key()` 负责检查当前 key 是否能在 `norm_stats` 中找到：

```python
if unnorm_key is None:
    assert len(norm_stats) == 1
    unnorm_key = next(iter(norm_stats.keys()))

assert unnorm_key in norm_stats
```

checkpoint 只有一套统计量时，可以省略 `unnorm_key`。checkpoint 带多套统计量时，要显式传入其中一个 key。传入不存在的 key 会直接报错，并列出当前 checkpoint 支持的 key。

key 存在只说明接口检查通过。它还要和当前任务、图像来源和机器人动作空间匹配；否则模型仍可能返回 shape 正常的数组，但动作尺度会偏掉。

## HF 路径和 Prismatic 路径

OpenVLA 源码里有两条常见推理路径：

| 路径 | 输入 | 主要用途 |
| --- | --- | --- |
| `prismatic/extern/hf/modeling_prismatic.py` | processor 输出的张量。 | Hugging Face `AutoModelForVision2Seq` 推理、setup smoke test、本地 HF checkpoint 部署。 |
| `prismatic/models/vlas/openvla.py` | PIL 图像和 instruction 字符串。 | Prismatic 训练路径和原生 VLA 类。 |

两条路径的入口不同，动作链路一致：确定动作维度，生成 action tokens，取最后几个 token ids，解码成归一化动作，再按统计量恢复尺度。实现位置有差别，HF 路径把 decode 逻辑放在 `OpenVLAForActionPrediction` 里，Prismatic 路径会调用 `ActionTokenizer`。读 HF 推理报错时，优先看 `OpenVLAForActionPrediction.predict_action()`；读 Prismatic training / full fine-tuning 路径时，再看 `OpenVLA.predict_action()`。

## 留到数据单元的问题

本页只解释模型怎样使用统计量。`dataset_statistics.json` 什么时候保存、本地 fine-tuned checkpoint 为什么要带这个文件、LIBERO eval 怎样设置 `unnorm_key`，会放到数据与统计量单元继续讲。

## 本页小结

- `predict_action()` 生成的 token 数由 `get_action_dim(unnorm_key)` 决定。
- 模型只取生成结果末尾的 action token ids 做 decode。
- token ids 先变成归一化动作，再用 `q01`、`q99` 和 `mask` 恢复到数据集尺度。
- HF 路径和 Prismatic 路径入口不同，但都按 action token decode 和反归一化这条链路返回动作。

## 导航

- 上一节：[Action Tokenizer](02-action-tokenizer.md)
- 返回上级：[模型结构与动作推理](../03-model-and-action-inference.md)
- 下一节：[数据与动作统计量](../04-data-and-statistics.md)
