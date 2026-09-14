# Qwen-PI

目标：理解 `QwenPI` 如何利用多层 VLM hidden states 训练 layer-wise flow matching 动作头，并弄清楚它和普通“最后层表征 + 动作头”的区别。

`QwenPI` 属于连续动作生成路线。它学习一个从噪声到动作 chunk 的生成过程。和 `QwenGR00T` 的主要区别是：`QwenPI` 会把 VLM 的多层 hidden states 交给 action head，`QwenGR00T` 通常只取最后一层。

它的链路可以写成：

```text
image + instruction
  -> Qwen-VL
  -> 多层 hidden states
  -> layer-wise flow matching action head
  -> continuous action chunk
```

如果 OFT 是“直接算答案”，PI 更像“从一个随机动作逐步变成合理动作”。训练时 action head 学习如何把噪声动作沿着正确方向推向真实动作；推理时从噪声开始采样，经过若干步得到动作 chunk。

代码路径：

```text
starVLA/model/framework/VLM4A/QwenPI.py
starVLA/model/modules/action_model/LayerwiseFM_ActionHeader.py
```

## 注册名和默认配置

`QwenPI.py` 注册了两个 framework 名字：

```python
@FRAMEWORK_REGISTRY.register("QwenFM")
@FRAMEWORK_REGISTRY.register("QwenPI")
class Qwen_PI(baseframework):
    ...
```

所以 YAML 里写 `framework.name: QwenPI` 或 `framework.name: QwenFM` 都会构建同一个类。教程里统一使用 `QwenPI`，因为这个名字和 StarVLA-PI 变体更一致。

默认配置里最关键的是 action head：

```python
action_model: dict = field(
    default_factory=lambda: {
        "action_model_type": "LayerwiseFM",
        "action_dim": 7,
        "state_dim": 7,
        "action_horizon": 16,
        "repeated_diffusion_steps": 2,
        "num_inference_timesteps": 4,
        "num_target_vision_tokens": 32,
        "diffusion_model_cfg": {
            "dropout": 0.2,
            "interleave_self_attention": True,
            "norm_type": "ada_norm",
            "attention_head_dim": 64,
        },
    }
)
```

这里的 `action_horizon` 默认是 16，和 `QwenGR00T` 常见的 8 步 chunk 不同。实际训练时以合并后的配置为准，数据里的 `action_indices` 和模型里的 `action_horizon` 必须对齐。

## 为什么是 layer-wise

构造函数里会先加载 VLM wrapper：

```python
self.qwen_vl_interface = get_vlm_model(config=self.config)
```

然后读取真实 VLM 的 hidden size 和层数：

```python
vlm_hf_cfg = self.qwen_vl_interface.model.config
text_cfg = getattr(vlm_hf_cfg, "text_config", vlm_hf_cfg)
num_vl_layers = int(text_cfg.num_hidden_layers)
llm_hidden_size = int(vlm_hf_cfg.hidden_size)
```

这些值从实际加载的 Hugging Face config 里读出，避免只依赖 YAML 中的默认值。随后 `populate_layerwise_dit_cfg()` 会把 layer-wise DiT 需要的 shape 字段写回配置：

```python
populate_layerwise_dit_cfg(
    self.config,
    dit_hidden_dim=llm_hidden_size,
    num_dit_layers=num_vl_layers,
)
```

这就是 `QwenPI` 的核心：action head 的层数和 VLM 层数绑定，输入也来自多层 hidden states。它希望 action head 能利用不同层次的视觉语言表征，减少对最后一层语义 token 的单点依赖。

从直觉上看，VLM 的不同层可能关注不同信息：

| 层级 | 可能包含的信息 |
|---|---|
| 较浅层 | 边缘、颜色、局部视觉细节 |
| 中间层 | 物体、空间关系、视角信息 |
| 较深层 | 指令语义、任务意图、跨模态融合 |

PI 会保留这些层级信息，让动作头在生成动作时可以按层使用。

## 编码 VLM 多层 hidden states

`QwenPI` 把 VLM 编码封装在 `_encode_vl_hidden_states()` 中：

```python
qwen_inputs = self.qwen_vl_interface.build_qwenvl_inputs(
    images=batch_images,
    instructions=instructions,
)
attention_mask = qwen_inputs.get("attention_mask", None)
qwenvl_outputs = self.qwen_vl_interface(
    **qwen_inputs,
    output_hidden_states=True,
    return_dict=True,
)
expected_layers = len(self.action_model.model.transformer_blocks)
vl_embs_list = list(qwenvl_outputs.hidden_states[-expected_layers:])
```

这里有两个细节：

- `output_hidden_states=True` 必须打开，否则只能拿到最后输出，layer-wise action head 没有输入。
- `expected_layers` 来自动作头的 transformer blocks 数量，因此 VLM 输出层数和 action head 层数必须匹配。

返回值是：

```text
vl_embs_list: List[Tensor]，每个 Tensor 形状约为 [B, L, H]
attention_mask: VLM 输入 token 的 mask
```

## forward 训练流程

`forward()` 读取的数据字段和其他 VLM4A framework 保持一致：

```python
batch_images = [example["image"] for example in examples]
instructions = [example["lang"] for example in examples]
actions = [example["action"] for example in examples]
state = [example["state"] for example in examples] if "state" in examples[0] else None
```

先编码多层 hidden states：

```python
vl_embs_list, backbone_attention_mask = self._encode_vl_hidden_states(
    batch_images,
    instructions,
)
base_hidden = vl_embs_list[-1]
```

再把动作标签裁成最后一个 chunk：

```python
actions = torch.tensor(np.array(actions), device=base_hidden.device, dtype=base_hidden.dtype)
actions_target = actions[:, -self.action_horizon:, :]
```

训练 flow matching 时，同一批动作会重复若干次，对应不同噪声时间步：

```python
repeated_diffusion_steps = 2
actions_target_repeated = actions_target.repeat(repeated_diffusion_steps, 1, 1)
vl_embs_list_repeated = [
    h.repeat(repeated_diffusion_steps, 1, 1)
    for h in vl_embs_list
]
```

最后交给 layer-wise action head：

```python
action_loss = self.action_model(
    vl_embs_list_repeated,
    actions_target_repeated,
    state_repeated,
    encoder_attention_mask=backbone_attention_mask,
)
return {"action_loss": action_loss}
```

从 trainer 视角看，它仍然只需要拿到 `action_loss`。多层 hidden states、重复采样和 flow matching 细节都被封装在 framework 内部。

## predict_action 推理流程

推理时入口仍然是 `predict_action()`：

```python
pred_actions = self.action_model.predict_action(
    vl_embs_list,
    state,
    encoder_attention_mask=backbone_attention_mask,
)
normalized_actions = pred_actions.detach().cpu().numpy()
return {"normalized_actions": normalized_actions}
```

部署服务只关心返回的 `normalized_actions`。这些动作还是归一化空间里的动作，后续由 `PolicyNormProcessor` 根据训练时保存的 `dataset_statistics.json` 做反归一化。

## realtime 推理接口

`QwenPI` 额外提供了 `predict_action_realtime()`：

```python
pred_actions = self.action_model.predict_action_realtime(
    vl_embs_list,
    state_t,
    prev_action_chunk=prev_chunk_t,
    inference_delay=inference_delay,
    **kwargs,
)
```

这个接口用于真实控制延迟场景。模型一次预测一段 action chunk，但机器人执行时已经消耗了前几步动作。`prev_action_chunk_normalized` 和 `inference_delay` 允许 action head 固定上一段动作的前缀，再重新采样后续动作，从而减少 chunk 切换时的不连续。

## 和其他 framework 的区别

| 对比对象 | PI 的区别 |
|---|---|
| OFT | PI 是生成式 flow matching，OFT 是直接 MLP 回归 |
| FAST | PI 输出连续动作，不经过离散 action token |
| GR00T | PI 使用多层 VLM hidden states，GR00T 通常只用最后一层 |
| WM4A | PI 仍然使用 VLM backbone，WM4A 换成 world model backbone |

PI 的优势是表达能力强，尤其适合希望利用多层 VLM 表征的研究场景。代价是显存、实现复杂度和调试难度都更高。初读 PI 时，重点先看清 `vl_embs_list` 是怎么来的，不必一开始就深入每个 flow matching 公式。

## 常见问题

| 现象 | 原因 | 检查 |
|---|---|---|
| hidden states 层数不匹配 | VLM 层数和 layer-wise action head 配置不一致 | `populate_layerwise_dit_cfg()`、`transformer_blocks` |
| 显存占用高 | 多层 hidden states 都要保留并传入 action head | batch size、VLM 层数、图像分辨率 |
| action shape mismatch | `action_horizon`、`action_dim` 和数据配置不一致 | YAML、`modality.json`、`action_indices` |
| 推理动作抖动 | chunk 之间衔接不平滑 | `predict_action_realtime()`、`inference_delay` |
| state shape 错 | `state_dim` 与 DataConfig 不一致 | `state_keys`、`state_dim` |

## 小结

- `QwenPI` 使用 `LayerwiseFlowmatchingActionHead`，输入是多层 VLM hidden states。
- `QwenPI` 会从实际 VLM config 中读取 hidden size 和层数，再填充 action head 的 shape 配置。
- `forward()` 对外只返回 `action_loss`，`predict_action()` 对外只返回 `normalized_actions`。
- `predict_action_realtime()` 是 `QwenPI` 相对特殊的接口，用于处理动作 chunk 执行延迟。
- 调试 PI 时，可以先降低 batch size、图像分辨率和 `repeated_diffusion_steps`。

## 动手练习

1. 运行 `rg -n "populate_layerwise_dit_cfg|input_embedding_dim|cross_attention_dim|num_attention_heads" starVLA/model/framework/share_tools.py starVLA/model/framework/VLM4A/QwenPI.py`，查看 PI 如何补齐 DiT shape 字段。
2. 运行 `rg -n "output_hidden_states|expected_layers|vl_embs_list|predict_action_realtime" starVLA/model/framework/VLM4A/QwenPI.py`，确认多层 hidden states 和 realtime 接口在哪里使用。
3. 运行 `rg -n "repeated_diffusion_steps|num_inference_timesteps|action_horizon" starVLA/model/framework/VLM4A/QwenPI.py starVLA/model/modules/action_model`，说明采样步数和训练/推理成本相关的位置。

## 导航

- 上一节：[03 Qwen-FAST](03-qwen-fast.md)
- 返回上级：[模型框架](../04-frameworks.md)
- 下一节：[05 Qwen-GR00T](05-qwen-gr00t.md)
