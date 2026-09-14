# Qwen-GR00T

目标：理解 `QwenGR00T` 如何用 Qwen-VL 最后一层 hidden state 条件化 flow matching DiT 动作头，并掌握它在训练、推理和配置中的关键接口。

`QwenGR00T` 是 StarVLA 中常见的连续动作生成 baseline 之一。它和 `QwenPI` 一样使用 flow matching 思路，但结构更直接：VLM 负责把图像和语言编码成 token hidden states，动作头使用最后一层 hidden state 作为 cross attention 条件，生成一段连续动作 chunk。

它的链路可以写成：

```text
image + instruction
  -> Qwen-VL
  -> last hidden state
  -> flow matching DiT action head
  -> continuous action chunk
```

GR00T 这个名字容易让人误以为它只和 NVIDIA GR00T 模型绑定。StarVLA 里的 `QwenGR00T` 更准确地说是“借鉴 GR00T 风格的双系统动作生成框架”：VLM 是慢系统，负责理解场景和任务；DiT/flow matching action head 是快系统，负责生成连续控制动作。

代码路径：

```text
starVLA/model/framework/VLM4A/QwenGR00T.py
starVLA/model/modules/action_model/GR00T_ActionHeader.py
```

## 注册名和默认配置

`QwenGR00T.py` 只注册一个名字：

```python
@FRAMEWORK_REGISTRY.register("QwenGR00T")
class Qwen_GR00T(baseframework):
    ...
```

训练配置中选择它时，只需要：

```yaml
framework:
  name: QwenGR00T
```

默认 action head 配置如下：

```python
action_model: dict = field(
    default_factory=lambda: {
        "action_model_type": "DiT-B",
        "action_hidden_dim": 1024,
        "hidden_size": 1024,
        "action_dim": 7,
        "state_dim": 7,
        "action_horizon": 8,
        "repeated_diffusion_steps": 8,
        "num_inference_timesteps": 4,
        "num_target_vision_tokens": 32,
        "diffusion_model_cfg": {
            "cross_attention_dim": 2048,
            "num_layers": 16,
            "dropout": 0.2,
            "interleave_self_attention": True,
            "norm_type": "ada_norm",
        },
    }
)
```

这里要特别注意 `action_horizon`、`action_dim` 和 `state_dim`。它们必须和 dataloader 侧的 `DataConfig`、`modality.json`、动作切片规则一致。

## cross attention 维度自动对齐

`QwenGR00T` 构造函数中会先加载 VLM：

```python
self.qwen_vl_interface = get_vlm_model(config=self.config)
```

然后把 action head 的 cross attention 维度改成实际 VLM hidden size：

```python
self.config.framework.action_model.diffusion_model_cfg.cross_attention_dim = (
    self.qwen_vl_interface.model.config.hidden_size
)
self.action_model = get_action_model(config=self.config)
```

这一步很重要：不同 Qwen-VL 版本的 hidden size 可能不同，如果 YAML 中的 `cross_attention_dim` 和 VLM 输出不一致，DiT action head 的 cross attention 会在矩阵乘法处报 shape 有问题。

因此，读 `QwenGR00T` 时要把配置理解成两层：

| 来源 | 作用 |
|---|---|
| YAML/default config | 给出默认动作维度、chunk 长度、DiT 层数等 |
| 实际 VLM config | 决定 action head 的 cross attention 输入维度 |

## flow matching 和 DiT 的直觉

在 GR00T 里，动作头学习一个“把噪声动作变成真实动作”的过程。可以把它理解成：

```text
随机动作 x0
  -> 根据图像/语言 hidden state 判断应该往哪里改
  -> 经过若干步
  -> 合理动作 x1
```

DiT 是这个过程里的 Transformer 主体。它处理动作 token、时间步 embedding、状态 embedding 和来自 VLM 的条件 token。`num_inference_timesteps` 控制推理时采样几步；步数越多，通常越慢，也可能更稳定。

`repeated_diffusion_steps` 是训练时的重复采样次数。它会让同一个真实动作在不同噪声时间步上学习多次，增强训练信号，但也会增加显存和计算开销。

## forward 训练流程

`forward()` 先从 StarVLA 样本字典中取出图像、语言、动作和状态：

```python
batch_images = [example["image"] for example in examples]
instructions = [example["lang"] for example in examples]
actions = [example["action"] for example in examples]
state = [example["state"] for example in examples] if "state" in examples[0] else None
```

然后通过 VLM wrapper 构造 Qwen 输入：

```python
qwen_inputs = self.qwen_vl_interface.build_qwenvl_inputs(
    images=batch_images,
    instructions=instructions,
)
backbone_attention_mask = qwen_inputs.get("attention_mask", None)
```

运行 VLM 时必须打开 hidden states：

```python
qwenvl_outputs = self.qwen_vl_interface(
    **qwen_inputs,
    output_hidden_states=True,
    return_dict=True,
)
last_hidden = qwenvl_outputs.hidden_states[-1]
```

`last_hidden` 形状约为：

```text
[batch_size, sequence_length, vlm_hidden_size]
```

其中 `sequence_length` 同时包含视觉 token 和文本 token。动作头会通过 attention mask 判断哪些 token 有效。

## 动作标签和重复采样

训练标签只取最后一个动作 chunk：

```python
actions = torch.tensor(np.array(actions), device=last_hidden.device, dtype=last_hidden.dtype)
actions_target = actions[:, -self.action_horizon:, :]
```

flow matching 训练需要对噪声时间步采样。`QwenGR00T` 用 `repeated_diffusion_steps` 把同一批样本重复多次：

```python
repeated_diffusion_steps = self.config.framework.action_model.get(
    "repeated_diffusion_steps",
    4,
)
actions_target_repeated = actions_target.repeat(repeated_diffusion_steps, 1, 1)
last_hidden_repeated = last_hidden.repeat(repeated_diffusion_steps, 1, 1)
```

如果有 `state`，也要同步 repeat：

```python
state_repeated = state.repeat(repeated_diffusion_steps, 1, 1)
```

最后进入 `FlowmatchingActionHead`：

```python
action_loss = self.action_model(
    last_hidden_repeated,
    actions_target_repeated,
    state_repeated,
    encoder_attention_mask=backbone_attention_mask,
)
return {"action_loss": action_loss}
```

从训练器视角看，`QwenGR00T` 和 `QwenOFT`、`QwenFast` 的接口完全一样，都是返回一个包含 `action_loss` 的字典。复杂度藏在 framework 和 action head 内部。

## predict_action 推理流程

部署时 `PolicyServerWrapper` 最终会调用 framework 的 `predict_action()`。`QwenGR00T.predict_action()` 会：

1. 把输入图像转成 PIL。
2. 按训练配置里的 `obs_image_size` resize。
3. 用 Qwen-VL 编码图像和指令。
4. 取最后一层 hidden state。
5. 调用 action head 采样动作 chunk。

核心代码是：

```python
pred_actions = self.action_model.predict_action(
    last_hidden,
    state,
    encoder_attention_mask=backbone_attention_mask,
)
normalized_actions = pred_actions.detach().cpu().numpy()
return {"normalized_actions": normalized_actions}
```

返回值仍然是归一化动作。server 侧会再根据训练保存的 `dataset_statistics.json` 做反归一化，并把动作通过 websocket 返回给 benchmark client。

## 和 Qwen-PI 的差别

| 维度 | Qwen-GR00T | Qwen-PI |
|---|---|---|
| VLM 表征 | 最后一层 hidden state | 多层 hidden states |
| action head | `FlowmatchingActionHead` | `LayerwiseFlowmatchingActionHead` |
| DiT 层数 | 由 `diffusion_model_cfg.num_layers` 配置 | 通常和 VLM 层数对齐 |
| 调试重点 | `last_hidden`、cross attention、动作 shape | `vl_embs_list`、层数匹配、realtime 接口 |
| 开销 | 相对更低 | 相对更高 |
| 入门建议 | 更适合作为 flow matching 第一页 | 适合进阶理解多层表征 |

相比 `QwenPI`，`QwenGR00T` 少了多层 hidden states 的开销，结构更容易调试，也更适合作为复杂连续动作任务的通用 baseline。

## 和其他 framework 的区别

| 对比对象 | GR00T 的区别 |
|---|---|
| OFT | GR00T 用生成式 flow matching，OFT 用 MLP 直接回归 |
| FAST | GR00T 输出连续动作，不生成离散 action tokens |
| PI | GR00T 只用最后一层 VLM hidden state，结构更直接 |
| WM4A | GR00T 是动作头路线；WM4A 是替换 backbone 的路线，也可以组合 GR00T 头 |

## 常见问题

| 现象 | 原因 | 检查 |
|---|---|---|
| cross attention shape mismatch | VLM hidden size 和 action head 配置不一致 | 构造函数里的 `cross_attention_dim` 赋值是否执行 |
| action shape mismatch | 数据动作维度或 chunk 长度和模型配置不一致 | `action_dim`、`action_horizon`、`action_indices` |
| 显存占用高 | `repeated_diffusion_steps`、batch size、图像 token 太多 | 降低 repeat、batch、图像分辨率 |
| 推理慢 | flow matching inference steps 多 | `num_inference_timesteps` |
| 部署动作异常 | 归一化统计或图像顺序不一致 | `dataset_statistics.json`、camera key、client 输入 |

## 小结

- `QwenGR00T` 使用 Qwen-VL 最后一层 hidden state 条件化 `FlowmatchingActionHead`。
- `cross_attention_dim` 会在构造时按实际 VLM hidden size 自动改写，不能只看 YAML。
- `forward()` 返回 `action_loss`，`predict_action()` 返回 `normalized_actions`，这两个接口让它能复用 trainer 和 deployment。
- 调试 `QwenGR00T` 时优先看 action shape、state shape、attention mask 和反归一化统计。

## 动手练习

1. 运行 `rg -n "cross_attention_dim|hidden_size|qwen_vl_interface" starVLA/model/framework/VLM4A/QwenGR00T.py`，说明换 VLM 时为什么要关注 hidden size。
2. 运行 `rg -n "output_hidden_states|last_hidden|predict_action" starVLA/model/framework/VLM4A/QwenGR00T.py`，确认最后一层 hidden state 如何进入动作头。
3. 运行 `rg -n "repeated_diffusion_steps|num_inference_timesteps|action_horizon" starVLA/model/framework/VLM4A/QwenGR00T.py starVLA/model/modules/action_model`，说明采样步数和训练/推理成本相关的位置。

## 导航

- 上一节：[04 Qwen-PI](04-qwen-pi.md)
- 返回上级：[模型框架](../04-frameworks.md)
- 下一节：[06 VLM 封装与动作头](06-vlm-and-action-heads.md)
