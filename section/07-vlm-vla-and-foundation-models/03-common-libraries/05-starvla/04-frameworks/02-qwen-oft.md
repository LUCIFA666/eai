# Qwen-OFT

目标：理解 `QwenOFT` 怎样用 VLM 的 hidden state 直接回归连续动作。

从最快弄懂 StarVLA 的 framework 机制，本章提供了一个很好的途径：OFT的思路很直接：在语言指令后面放一串 action placeholder，让 VLM 在这些位置产生 hidden state，再用一个 MLP 把 hidden state 变成动作。

```text
image + instruction
  -> Qwen-VL
  -> action placeholder hidden states
  -> MLP
  -> continuous action chunk
```

这里的 continuous action chunk 可以理解为“未来几步机器人控制量”。例如单臂 7 维动作时，一个长度为 8 的 chunk 形状就是 `[8, 7]`：8 个时间步，每步 7 个动作数值。

代码路径：

```text
starVLA/model/framework/VLM4A/QwenOFT.py
starVLA/model/modules/action_model/MLP_ActionHeader.py
```

## 流程

```text
图像 + 指令 + action placeholder
  -> Qwen VLM
  -> 取 placeholder 位置的 hidden state
  -> MLP action head
  -> 连续动作 chunk
```

训练时拿预测动作和数据里的 `action` 做 L1 loss。推理时返回 `normalized_actions`，再由部署服务做反归一化。

## 配置重点

OFT 需要关注这些字段：

```yaml
framework:
  name: QwenOFT
  qwenvl:
    base_vlm: <MODEL_ROOT>/Qwen3-VL-4B-Instruct
    attn_implementation: flash_attention_2
  action_model:
    action_model_type: MLP
    action_dim: 7
    action_horizon: 8
```

`action_dim` 要和数据的动作维度一致，`action_horizon` 要和 `DataConfig.action_indices` 的长度一致。

## action placeholder

`QwenOFT` 会设置一个 action token，例如：

```python
self.action_token = "🔍"
```

训练时，它会在 instruction 后面追加一段提示：

```python
action_tokens = self.action_token * self.chunk_len
prompt_suffix = (
    f" Please predict the next {self.chunk_len} robot actions: "
    f"<action>{action_tokens}<action>."
)
instructions = [instruction + prompt_suffix for instruction in instructions]
```

如果 `chunk_len` 是 8，prompt 中就会出现 8 个 action placeholder。模型随后会在这 8 个位置产生 8 个 hidden state，对应未来 8 步动作。

这和语言生成不同。普通 VLM 会在这些位置继续预测下一个文本 token；OFT 不关心生成哪个字，而是把这些位置当成“查询槽位”。每个槽位对应未来一步动作，槽位里的 hidden state 交给 MLP 后变成动作数值。

可以把它类比成表格填空：

```text
指令：把杯子拿起来
动作槽位：[槽位1] [槽位2] [槽位3] ... [槽位T]
MLP 输出：  a1     a2     a3          aT
```

`槽位1` 不需要被解码成文字，它只提供一个向量；真正输出动作的是 MLP action head。

## forward 流程

训练时先从样本里取字段：

```python
batch_images = [example["image"] for example in examples]
instructions = [example["lang"] for example in examples]
actions = [example["action"] for example in examples]
state = [example["state"] for example in examples] if "state" in examples[0] else None
```

然后构造 VLM 输入：

```python
qwen_inputs = self.qwen_vl_interface.build_qwenvl_inputs(
    images=batch_images,
    instructions=instructions,
)
qwenvl_outputs = self.qwen_vl_interface(
    **qwen_inputs,
    output_hidden_states=True,
    return_dict=True,
)
last_hidden = qwenvl_outputs.hidden_states[-1]
```

再取 action placeholder 对应的 hidden state：

```python
action_queries = self._gather_action_token_embeddings(
    last_hidden,
    input_ids,
    action_token_id=self.action_token_id,
)
pred_actions = self.action_model.predict_action(action_queries)
```

最后计算 loss：

```python
actions_target = actions[:, -self.action_horizon:, :]
action_loss = self.l1_loss(pred_actions, actions_target)
return {"action_loss": action_loss}
```

## predict_action 流程

推理时没有动作标签，前半段仍然是构造 prompt、跑 VLM、取 action hidden state：

```python
pred_actions = self.action_model.predict_action(action_queries)
normalized_actions = pred_actions.detach().cpu().numpy()
return {"normalized_actions": normalized_actions}
```

如果训练时设置了图像大小，推理时也会按同样大小 resize。图像预处理放在 framework 内部，dataloader 只提供原始图像。

## OFT 适合作为 baseline 的原因

OFT 的优点很明确：

- 结构简单，便于阅读和调试。
- 推理快，没有采样循环。
- loss 是直观的连续动作误差。
- hidden state 到动作头的 shape 容易检查。

它的表达能力也有边界。复杂任务中，同一个观察可能对应多种合理动作，简单 MLP 回归往往更难表达这种多样性。PI 和 GR00T 的 flow matching 动作头就是为这类问题准备的。

## 和其他 framework 的区别

| 对比对象 | OFT 的区别 |
|---|---|
| FAST | OFT 不把动作离散化成 token，因此没有 action token 解码误差 |
| PI | OFT 不做 flow matching，不能显式建模从噪声到动作的生成过程 |
| GR00T | OFT 用 MLP 直接回归，GR00T 用 DiT/flow matching 生成动作 chunk |
| WM4A | OFT 使用 VLM 表征，WM4A 使用 world model 表征后再接动作头 |

因此，OFT 更像一个“最小可用动作头”。它适合先跑通数据、训练、部署接口，也适合做 baseline；如果任务存在明显多解或动作分布复杂，再考虑 PI 或 GR00T。

## 常见问题

| 现象 | 原因 | 检查 |
|---|---|---|
| 找不到 action token | tokenizer 没把 placeholder 编成预期 token | 打印 `action_token_id` 和 `input_ids` |
| `action_queries` shape 不对 | prompt 中 placeholder 数量和 `action_horizon` 不一致 | `chunk_len`、`action_horizon` |
| loss shape mismatch | 数据 action chunk 和模型 horizon 不一致 | `action_indices`、`action_horizon` |
| 推理动作尺度异常 | 直接使用了标准化动作 | 走 policy server 反归一化 |

## 小结

- Qwen-OFT 用 action placeholder 的 hidden state 回归连续动作。
- 动作头是 MLP，训练 loss 通常是 L1。
- placeholder 数量要和 `action_horizon` 对齐。
- OFT 适合作为入门 baseline，再向 FAST、PI、GR00T 扩展。

## 动手练习

1. 运行 `rg -n "action_token|instruction|action_queries|action_horizon" starVLA/model/framework/VLM4A/QwenOFT.py`，确认 action token 如何进入输入序列。
2. 在准备好 Qwen 模型后运行 `QwenOFT.py` 的单文件测试，成功输出应包含 action loss 或 predicted action shape。没有模型时先完成第 1 条证据练习。
3. 运行 `rg -n "def forward|def predict_action|action_loss|normalized_actions" starVLA/model/framework/VLM4A/QwenOFT.py`，标出训练期和推理期分别出现的步骤。

## 导航

- 上一节：[01 baseframework 与 registry](01-baseframework-and-registry.md)
- 返回上级：[模型框架](../04-frameworks.md)
- 下一节：[03 Qwen-FAST](03-qwen-fast.md)
