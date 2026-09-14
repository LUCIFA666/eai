# 并行解码

并行解码是 OFT 提速的核心，它把动作生成从逐 token 串行改成一次前向解出整段。实现集中在 `prismatic/extern/hf/modeling_prismatic.py` 里 `OpenVLAForActionPrediction` 的动作预测路径：入口是 `predict_action()`，连续动作走到 `_regression_or_discrete_prediction()`，整段动作在这里一次前向解完。

## 一次前向解出整段动作

关键的几步是这样接起来的。`predict_action()` 先调用 `_prepare_input_for_action_prediction()`，往输入序列尾部拼上 `ACTION_DIM * NUM_ACTIONS_CHUNK` 个占位的动作 token，再加一个 stop token。这些占位 token 只是预留出动作要占的位置，本身不带动作信息。接着 `_process_action_masks()` 生成 `all_actions_mask`，标出哪些位置属于动作。进入 `_regression_or_discrete_prediction()` 后，第一件事就是把这些动作位置的 embedding 清零（`input_embeddings * ~all_actions_mask`）：动作位置进入主干时是空的，模型没有任何已解出的动作 token 可以参照，只能从图像、指令和本体状态这些上下文里把整段动作一次性推出来。

清零之后，`_build_multimodal_attention()` 把视觉 token、文本 token 和这些空动作位置拼成一条多模态序列，送主干做一次前向（`output_hidden_states=True`）。前向结束后，从最后一层 hidden states 里按位置切出动作那一段：

```
actions_hidden_states = last_hidden_states[
    :, NUM_PATCHES + NUM_PROMPT_TOKENS : NUM_PATCHES + NUM_PROMPT_TOKENS + ACTION_DIM * NUM_ACTIONS_CHUNK, :
]
```

这一段 hidden states 覆盖整个 action chunk 的所有维度，交给连续动作头一次性回归成动作。整个过程只有这一次主干前向，没有逐 token 的循环，原来七维动作的 7 次串行前向被压成了 1 次。

## 双向注意力让动作位置互相可见

自回归解码用因果注意力，每个位置只能看到它左边的 token，这正是串行的来源：后一个动作 token 必须等前一个生成出来才能算。并行解码把动作位置之间的注意力改成双向（非因果）：所有动作位置在同一次前向里彼此可见，不再有先后顺序。`_prepare_input_for_action_prediction()` 在序列尾部补 stop token，就是为了对齐训练时这套非因果双向自注意力的输入形状。动作位置一旦可以互相看到，一个 chunk 内不同维度、不同时间步的动作就能在一次前向里联合解出，而不是一个等一个。

代价是放弃了自回归的逐步条件依赖。论文的对照实验里，并行解码在多类任务上没有带来精度下降，反而因为打开了 action chunking 而提升了成功率；双向注意力在动作位置上的表达力损失，在这些任务上没有显现成问题。

## action chunk 的切分

占位动作 token 的个数是 `ACTION_DIM * NUM_ACTIONS_CHUNK`，这两个常量在 `prismatic/vla/constants.py` 里按机器人设定，LIBERO 是动作维度 7、chunk 长度 8，于是一次前向解出 8 个时间步、共 56 维动作。chunk 大小 K 直接决定单次推理覆盖多少控制步：K 步动作一次解出，机器人连续执行 K 步才推理一次，动作生成的有效吞吐相对不分块提高约 K 倍，而单次前向只因为序列变长略增延迟。

训练侧需要区分 chunk 内的当前步和未来步。`prismatic/training/train_utils.py` 的 `get_current_action_mask()` 用动作 token 位置的累积计数取前 `ACTION_DIM` 个，标出当前时间步那一步动作；`get_next_actions_mask()` 取累积计数超过 `ACTION_DIM` 的部分，标出 chunk 里其余未来步。两个 mask 让训练能分别统计当前步与未来步的动作精度，推理时则按同样的位置布局从 hidden states 里切出整段。chunk 多长、动作维度多大由 `constants.py` 统一决定，训练和推理共用这套设定，二者必须一致，否则从 hidden states 里切动作段的位置和动作头的输入形状都会错位。

## 本页小结

- 并行解码在 `predict_action()` 到 `_regression_or_discrete_prediction()` 里用占位动作 token、动作位置 embedding 清零、一次主干前向，把 7 次串行前向压成 1 次。
- 双向注意力去掉因果掩码，让 chunk 内所有动作位置在一次前向里互相可见，是去串行的关键。
- chunk 长度和动作维度由 `constants.py` 统一决定，训练与推理共用；吞吐随 K 提高，而单次前向只因序列变长略增延迟。

## 导航

- 上一节：[架构](02-architecture.md)
- 返回上级：[OpenVLA-OFT](../01-openvla-oft.md)
- 下一节：[推理调用链](04-inference-path.md)
