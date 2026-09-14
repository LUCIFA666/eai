# Qwen-FAST

目标：理解 `QwenFast` 怎样把连续动作变成离散 token，并用 VLM 的自回归生成能力预测动作。

FAST 的核心思路是：先把动作序列压缩成一串离散 token，再让 VLM 像生成文本一样生成这些动作 token。生成完成后，再把 token 解码回连续动作。

它的链路可以写成：

```text
训练时：
continuous actions
  -> FAST tokenizer
  -> <robot_action_*> tokens
  -> Qwen-VL next-token loss

推理时：
Qwen-VL generate()
  -> <robot_action_*> tokens
  -> FAST tokenizer decode
  -> continuous action chunk
```

所以 FAST 的关键在于把动作预测改造成语言模型熟悉的自回归生成问题。

代码路径：

```text
starVLA/model/framework/VLM4A/QwenFast.py
starVLA/model/modules/action_model/fast_ActionHeader.py
```

## 流程

```text
连续动作
  -> FAST tokenizer
  -> <robot_action_*> token 序列
  -> Qwen next-token prediction
  -> 生成动作 token
  -> 解码回连续动作
```

## 模型要求

FAST 需要 VLM 词表里包含动作 token。常见模型包括：

| 模型 | 作用 |
|---|---|
| `Qwen2.5-VL-3B-Action` | 带 FAST action tokens 的 Qwen2.5-VL |
| `Qwen3-VL-4B-Action` | 带 FAST action tokens 的 Qwen3-VL |
| `pi-fast` | FAST 动作 tokenizer 权重 |

如果用普通 instruct 模型跑 FAST，模型可能无法正确表示 `<robot_action_*>`。

这也是 FAST 最容易报错的地方。OFT、PI、GR00T 可以用普通 VLM hidden state 接动作头；FAST 必须让 VLM 的 tokenizer 和 embedding 知道 action tokens。如果词表里没有 `<robot_action_*>`，生成阶段就没有稳定的动作符号空间。

## 动作 token 化是什么意思

机器人动作本来是连续数值，例如：

```text
[0.12, -0.03, 0.44, 0.01, ...]
```

FAST 会把一段连续动作压成一串离散编号：

```text
[153, 28, 402, 17, ...]
```

再映射成 VLM 能看到的特殊 token：

```text
<robot_action_153><robot_action_28><robot_action_402><robot_action_17>...
```

训练时，这串 token 就像 assistant response。模型学到的是：“看到这张图和这句指令后，下一串 token 应该是什么。”推理时再把生成出来的 token 解码回动作数值。

## forward 流程

训练时先读取样本：

```python
batch_images = [example["image"] for example in examples]
instructions = [example["lang"] for example in examples]
actions = [example["action"] for example in examples]
```

然后把连续动作编码成 FAST token：

```python
batch_fast_tokens = self.action_model.encoder_action2fastoken(actions)
```

FAST token 会进一步转成 VLM 词表里的动作 token 字符串：

```python
def map_fast_token_to_vlm_action(tokens):
    return "".join([f"<robot_action_{token}>" for token in tokens])
```

例如 FAST token `[12, 5]` 会变成：

```text
<robot_action_12><robot_action_5>
```

训练时，这串动作 token 作为 assistant solution 交给 Qwen：

```python
qwen_inputs = self.qwen_vl_interface.build_qwenvl_inputs(
    images=batch_images,
    instructions=instructions,
    solutions=vlm_action_tokens,
)
outputs = self.qwen_vl_interface(**qwen_inputs)
return {"action_loss": outputs.loss}
```

因此 FAST 的训练 loss 本质上是 token prediction loss。

## predict_action 流程

推理时，模型根据图像和指令生成 token：

```python
generated_ids = self.qwen_vl_interface.model.generate(
    **qwen_inputs,
    max_length=2048,
)
```

然后提取动作 token，并映射回 FAST token id：

```python
vlm_action_token_ids = self._extract_action_token_ids(generated_ids)
fast_token_ids = self._decode_action_tokens(vlm_action_token_ids)
normalized_actions = self.action_model.fast_tokenizer.decode(fast_token_ids)
```

这里有两个 token 空间：

| token 空间 | 含义 |
|---|---|
| VLM token id | Qwen 词表中的 `<robot_action_*>` token id |
| FAST token id | FAST tokenizer 的动作离散 token id |

`_decode_action_tokens()` 会处理两者之间的 offset。

## 优点和限制

FAST 的优点：

- 动作预测形式和语言生成一致。
- 可以复用 VLM 的自回归建模能力。
- 适合研究动作 token 化和语言模型统一建模。

需要注意的限制：

- 必须使用带 action token 的 VLM。
- 自回归生成通常比 MLP 回归慢。
- 连续动作精度受 tokenizer 粒度影响。
- 生成序列中缺少动作 token 时，解码会失败或输出无效动作。

## 和其他 framework 的区别

| 对比对象 | FAST 的区别 |
|---|---|
| OFT | FAST 生成离散 token，OFT 直接回归连续动作 |
| PI/GR00T | FAST 不做 flow matching，不需要扩散采样步骤 |
| 普通 VLM 对话 | FAST 的 assistant response 改为 action token 序列 |
| WM4A | FAST 仍然是 VLM4A 路线，backbone 是 VLM，不是 world model |

FAST 适合用来理解“动作即语言 token”的路线。它的工程重点是词表、token offset、生成序列截取和解码；这些问题和连续动作头的 shape 调试不太一样。

## 常见问题

| 现象 | 原因 | 检查 |
|---|---|---|
| 生成结果没有动作 token | base VLM 缺少 Action token 扩展，或训练不足 | `base_vlm`、训练步数 |
| token id offset 错 | 动作 token 范围和模型词表不匹配 | `_ACTION_TOKEN_MIN/MAX` |
| decode 返回空 | 没从生成序列里提取到动作 token | `_extract_action_token_ids()` |
| 动作粗糙 | FAST 离散化粒度有限 | tokenizer 配置和训练数据 |

## 小结

- Qwen-FAST 把连续动作转成 token，再用 VLM 预测 token。
- 它需要带 action token 扩展词表的 VLM。
- 训练时监督目标是 `<robot_action_*>` 序列。
- 推理时要从生成结果里提取动作 token，再解码成连续动作。

## 动手练习

1. 运行 `rg -n "map_fast_token_to_vlm_action|robot_action" starVLA/model/framework/VLM4A/QwenFast.py`，写出 token `12, 5` 对应的字符串序列。
2. 运行 `rg -n -- "-Action|action_token_min|fast_tokens" starVLA/model/framework/VLM4A/QwenFast.py starVLA/model/modules/vlm`，确认 FAST 为什么需要带动作 token 的 VLM。
3. 准备好 Action 版本模型后运行 QwenFast 推理测试，成功输出应包含 `normalized_actions` 的 shape；没有模型时先用第 1、2 条完成代码证据检查。

## 导航

- 上一节：[02 Qwen-OFT](02-qwen-oft.md)
- 返回上级：[模型框架](../04-frameworks.md)
- 下一节：[04 Qwen-PI](04-qwen-pi.md)
