# 新 backbone 或 action head

目标：理解新增 VLM backbone、world model backbone 或 action head 时应该接在哪一层。

StarVLA 的扩展点大致分三类：

| 扩展 | 主要位置 | 是否需要新 framework |
|---|---|---|
| 新 VLM backbone | `starVLA/model/modules/vlm/` | 通常需要或至少要测试现有 framework |
| 新 world model backbone | `starVLA/model/modules/world_model/` | 通常需要 WM4A framework |
| 新 action head | `starVLA/model/modules/action_model/` | 通常需要 framework 组合它 |

## 新 VLM backbone

新增 VLM wrapper 要改：

```text
starVLA/model/modules/vlm/MyVLM.py
starVLA/model/modules/vlm/__init__.py
```

`__init__.py` 中的 `get_vlm_model(config)` 当前根据 `base_vlm` 字符串分发。新增时要加一个分支：

```python
elif "my-vlm" in vlm_name.lower():
    from .MyVLM import _MyVLM_Interface
    return _MyVLM_Interface(config)
```

wrapper 至少要支持：

- 加载模型和 processor。
- 构造图像/文本输入。
- 返回 hidden states。
- 暴露 hidden size。
- 兼容当前 framework 调用方式。

如果想在 `QwenGR00T` 中直接替换 Qwen，必须让你的 wrapper 提供类似 `build_qwenvl_inputs()` 的方法，或者新建一个 framework 来适配你的输入函数。

## 新 action head

新增动作头一般放在：

```text
starVLA/model/modules/action_model/MyActionHeader.py
```

至少要考虑两个接口：

```python
loss = self.action_model(features, actions, state, ...)
pred = self.action_model.predict_action(features, state, ...)
```

不同 framework 对 action head 的调用方式不同。OFT 的 MLP 头是：

```python
pred_actions = self.action_model.predict_action(action_queries)
```

GR00T 的 flow matching 头是：

```python
action_loss = self.action_model(last_hidden, actions_target, state_repeated, ...)
pred_actions = self.action_model.predict_action(last_hidden, state, ...)
```

因此新增 action head 通常也要新增或修改一个 framework，把特征和标签按你的 head 需要的格式传进去。

## 新 world model backbone

world model 相关文件在：

```text
starVLA/model/modules/world_model/
starVLA/model/framework/WM4A/
```

新增 world model 时要处理：

- 图像/视频到 latent 的编码。
- 文本条件编码。
- 中间层 hidden state 提取。
- hidden state reshape 到 action head 可消费的 token 序列。
- 精度和显存管理。

如果只是替换 Cosmos 为另一个视频 DiT，建议先复制 `CosmoPredict2OFT.py` 这类最简单变体，跑通 OFT，再尝试 GR00T/PI。

## 模块命名影响训练配置

新增组件时要注意属性名：

```python
self.qwen_vl_interface = ...
self.action_model = ...
```

如果改成：

```python
self.backbone = ...
self.head = ...
```

那么原来的配置：

```yaml
trainer:
  learning_rate:
    qwen_vl_interface: 1.0e-05
    action_model: 1.0e-04
```

就不会命中你的模块。可以改配置，但要明确知道学习率组和冻结路径依赖属性名。

## 小结

- 新 VLM 接 `modules/vlm` 和 `get_vlm_model()`。
- 新 action head 接 `modules/action_model`，通常需要 framework 适配。
- 新 world model 接 `modules/world_model` 和 `framework/WM4A`。
- 组件属性名会影响学习率和冻结配置。

## 动手练习

1. 运行 `sed -n '1,80p' starVLA/model/modules/vlm/__init__.py`，说明 `base_vlm` 字符串怎样被 `get_vlm_model()` 识别。
2. 运行 `rg -n "def predict_action|normalized_actions|action_horizon|action_dim" starVLA/model/framework/VLM4A/QwenGR00T.py starVLA/model/framework/VLM4A/QwenOFT.py`，写出 action head 最少需要的推理输入输出。
3. 运行 `rg -n "action_model|learning_rate|freeze_modules|reload_modules" starVLA/model/framework starVLA/training/trainer_utils`，列出把 `self.action_model` 改名为 `self.policy_head` 时要同步修改的 YAML 字段和训练配置。

## 导航

- 上一节：[02 新 framework](02-new-framework.md)
- 返回上级：[扩展 StarVLA](../09-extension.md)
- 下一节：[04 扩展调试顺序](04-extension-debug-order.md)
