# 优化器与冻结

目标：理解 StarVLA 如何为不同模块设置不同学习率，以及如何冻结 VLM backbone 或其他子模块。

VLA 微调里常见做法是：VLM backbone 用较小学习率，action head 用较大学习率。因为 backbone 通常来自预训练模型，而 action head 往往从头训练。

## 学习率分组

YAML 中常见配置：

```yaml
trainer:
  learning_rate:
    base: 2.5e-05
    qwen_vl_interface: 1.0e-05
    action_model: 1.0e-04
```

`build_param_lr_groups()` 的逻辑：

```python
for module_name, lr in lr_cfg.items():
    if module_name == "base":
        continue
    module = model
    for attr in module_name.split("."):
        module = getattr(module, attr)
    params = [p for p in module.parameters() if id(p) not in frozen_params]
    param_groups.append({"params": params, "lr": lr, "name": module_name})
```

没有被特殊分组命中的参数会进入 `base` 组：

```python
other_params = [p for p in model.parameters() if id(p) not in used_params and id(p) not in frozen_params]
param_groups.append({"params": other_params, "lr": base_lr, "name": "base"})
```

所以模块路径必须和 framework 属性名一致。`qwen_vl_interface` 和 `action_model` 是常见的两个顶层属性。

## 冻结模块

配置：

```yaml
trainer:
  freeze_modules: "qwen_vl_interface"
```

或命令行：

```bash
--trainer.freeze_modules "qwen_vl_interface.model.model.visual,dino_encoder"
```

`TrainerUtils.freeze_backbones()` 会按逗号切分路径，然后逐级 `getattr()`：

```python
for path in patterns:
    attrs = path.split(".")
    module = model
    for attr in attrs:
        module = getattr(module, attr)
    for param in module.parameters():
        param.requires_grad = False
```

冻结按模块属性路径匹配。路径写错时会打印 warning 并跳过。

## 如何找模块路径

最直接的方法是打印模型：

```python
print(model)
```

或者打印参数名：

```python
for name, param in model.named_parameters():
    print(name, param.requires_grad)
```

官方 FAQ 也建议先 `print(your_model)`，再把要冻结的相对路径写到 `trainer.freeze_modules`。

## 常见策略

| 策略 | 配置 | 适合场景 |
|---|---|---|
| 只训 action head | `freeze_modules: "qwen_vl_interface"` | 数据少、快速适配 |
| VLM 小学习率 + action head 大学习率 | 不冻结，设置学习率组 | 数据较多，允许 backbone 轻微适配 |
| 冻结视觉塔 | `qwen_vl_interface.model.model.visual` | 想保留视觉表征 |
| 全量微调 | `freeze_modules: ""` | 数据和算力充足 |

## 梯度裁剪

YAML：

```yaml
trainer:
  gradient_clipping: 1.0
```

训练时：

```python
if self.config.trainer.gradient_clipping is not None:
    self.accelerator.clip_grad_norm_(self.model.parameters(), self.config.trainer.gradient_clipping)
```

flow matching 动作头和大 VLM 联合训练时，梯度裁剪能减少偶发梯度爆炸。

## 小结

- 学习率分组和冻结都依赖 framework 的模块属性路径。
- 特殊学习率组会排除冻结参数，剩余参数进入 `base` 组。
- 冻结路径写错不会自动报 fatal error，要看 warning。
- 常见设置是 VLM 小学习率、action head 大学习率，或直接冻结 VLM。

## 动手练习

1. 运行 `rg -n "learning_rate|freeze_modules|build_param_lr_groups|freeze_backbones" starVLA/training/trainer_utils/trainer_tools.py`，确认学习率分组和冻结逻辑的位置。
2. 在准备好模型后打印 `for name, _ in model.named_children(): print(name)`，记录 top-level module 名称。没有模型时可用第 1 条和 framework 源码先定位候选模块名。
3. 在训练 YAML 中写出 `trainer.freeze_modules` 和 `trainer.learning_rate.action_model` 的配置片段，并用 `rg -n "action_model" starVLA/model/framework/VLM4A/QwenGR00T.py` 确认模块名存在。

## 导航

- 上一节：[03 训练循环](03-training-loop.md)
- 返回上级：[训练机制](../05-training.md)
- 下一节：[05 checkpoint 与恢复](05-checkpoint-and-resume.md)
