# Action Tokenizer

目标：读懂 OpenVLA 如何把连续动作写成 Llama 可以生成的 action tokens。

OpenVLA 把动作预测做成 token prediction。训练样本里的连续动作会先进入 action tokenizer，变成一串 token；推理时，模型生成这些 token，再把 token id 解码回连续动作。这里的动作是归一化后的动作，具体数据集尺度由后面的反归一化统计量处理。

## 归一化动作区间

`ActionTokenizer` 默认处理 `[-1, 1]` 区间内的动作值。这个类本身不读取数据集的 `q01` 和 `q99`。训练数据进入 tokenizer 前已经经过归一化；推理时 decode 得到的也是归一化动作。

这里要把两个环节分开：action tokenizer 决定 token 表示，`norm_stats` / `dataset_statistics.json` 提供动作尺度统计量。后面排查动作幅度异常时，可以分别检查 token decode 和统计量。

## `n_bins=256` 和词表末尾 token

OpenVLA 的 `ActionTokenizer` 默认使用 `n_bins=256`。源码用 256 个边界值建立离散化区间，decode 时再用相邻边界的中心值恢复归一化动作。OpenVLA 沿用 RT-2 风格的做法，把词表末尾的一组低频 token 重新解释为动作 token。

源码里先建立 uniform bins，再计算动作 token 在词表中的起始位置：

```python
self.bins = np.linspace(min_action, max_action, self.n_bins)
self.bin_centers = (self.bins[:-1] + self.bins[1:]) / 2.0

self.action_token_begin_idx: int = int(
    self.tokenizer.vocab_size - (self.n_bins + 1)
)
```

`self.bins` 有 256 个边界值，`self.bin_centers` 来自相邻边界的中点。`action_token_begin_idx` 是一个检查入口：tokenizer 词表大小、`n_bins` 和 checkpoint config 对不上时，动作 token 的 id 区间就会错。

## 编码：连续值到 token 字符串

编码时，源码先把动作裁剪到 `[-1, 1]`，再用 `np.digitize` 找到每个动作值对应的 bin。最后一步用 `tokenizer.vocab_size - discretized_action` 把 bin 编号映射到词表末尾的 token id。

```python
action = np.clip(action, a_min=float(self.min_action), a_max=float(self.max_action))
discretized_action = np.digitize(action, self.bins)

return self.tokenizer.decode(list(self.tokenizer.vocab_size - discretized_action))
```

这段代码说明 action token 来自 tokenizer 词表中的真实 token id。这些 token 在 OpenVLA 训练里承担了动作 bin 的含义。

## 解码：token id 回到归一化动作

推理阶段会走反方向。模型生成的 action token ids 先转成离散编号，再查对应的 bin center：

```python
discretized_actions = self.tokenizer.vocab_size - action_token_ids
discretized_actions = np.clip(
    discretized_actions - 1,
    a_min=0,
    a_max=self.bin_centers.shape[0] - 1,
)

return self.bin_centers[discretized_actions]
```

decode 时会先把编号减 1，再 clip 到 `bin_centers` 的有效范围。这样即使 `np.digitize` 得到最后一个边界索引，也会落到最后一个 center 上。decode 的输出仍然在归一化动作区间；目标机器人最终执行前，还要用 `unnorm_key` 找到 `q01`、`q99` 和 `mask`，再把归一化动作恢复到对应数据集的尺度。

## 对推理速度的影响

action token 路线复用了语言模型的自回归生成接口。动作维度越长，需要生成的 action tokens 越多，单步推理时间也会随之增加。具体生成长度会在下一页结合 `predict_action()` 再看。

## 本页小结

- `ActionTokenizer` 处理归一化动作，默认区间是 `[-1, 1]`。
- `n_bins=256` 建立离散化边界，动作 token 映射到 Llama tokenizer 词表末尾。
- 编码使用 `np.digitize`，解码时把 token id 转成编号并查 `bin_centers`。
- 动作尺度恢复发生在 `predict_action` 的反归一化阶段。

## 导航

- 上一节：[Prismatic Backbone](01-prismatic-backbone.md)
- 返回上级：[模型结构与动作推理](../03-model-and-action-inference.md)
- 下一节：[`predict_action` 动作推理](03-predict-action.md)
