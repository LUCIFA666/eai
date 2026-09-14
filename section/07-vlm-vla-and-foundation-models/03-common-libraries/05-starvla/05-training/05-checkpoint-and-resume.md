# checkpoint 与恢复

目标：理解 StarVLA 训练输出目录里每个文件的作用，以及加载 checkpoint 时真正依赖哪些文件。

StarVLA 的可部署策略由模型权重、配置和数据统计共同定义，单个 `.pt` 文件并不完整。

## 输出目录

一次训练通常输出：

```text
<run_root_dir>/<run_id>/
├── checkpoints/
│   ├── steps_5000_pytorch_model.pt
│   └── steps_10000_pytorch_model.pt
├── final_model/
│   └── pytorch_model.pt
├── config.full.yaml
├── config.yaml
├── dataset_statistics.json
├── summary.jsonl
└── wandb/
```

各文件作用：

| 文件 | 作用 |
|---|---|
| `steps_*_pytorch_model.pt` | 中间模型权重 |
| `final_model/pytorch_model.pt` | 训练结束模型权重 |
| `config.full.yaml` | 完整合并配置 |
| `config.yaml` | 访问字段配置快照，`from_pretrained()` 常用 |
| `dataset_statistics.json` | 动作/状态归一化统计 |
| `summary.jsonl` | checkpoint 步数记录 |
| `wandb/` | WandB 本地缓存 |

## 保存逻辑

中间 checkpoint：

```python
state_dict = self.accelerator.get_state_dict(self.model)
torch.save(state_dict, checkpoint_path + "_pytorch_model.pt")
```

如果配置：

```yaml
trainer:
  save_format: safetensors
```

则保存为：

```text
steps_<N>_model.safetensors
```

当前代码保存的是模型 state dict，没有使用 `accelerator.save_state()` 生成完整训练状态目录，因此不要假设 optimizer state 和 scheduler state 已经完整保存。

## 加载预训练权重

训练前加载已有权重由 `TrainerUtils.load_pretrained_backbones()` 处理：

```python
trainer:
  pretrained_checkpoint: path_to_steps_10000.pt
  reload_modules: "action_model"
```

如果 `reload_modules` 为空，会尝试加载整个模型：

```python
model.load_state_dict(checkpoint, strict=False)
```

如果指定模块，例如：

```yaml
reload_modules: "action_model"
```

则只加载 checkpoint 中以 `action_model.` 开头的参数到当前模型的 `action_model`。

这对“换 backbone 但复用动作头”或“只恢复某个子模块”很有用，但要求模块路径和参数 shape 匹配。

## 部署加载

部署加载走 `baseframework.from_pretrained(pretrained_checkpoint)`。它会从 checkpoint 路径向上找到 run 目录：

```text
<run_dir>/checkpoints/<checkpoint>.pt
<run_dir>/config.yaml
<run_dir>/dataset_statistics.json
```

然后执行：

```python
model_config, norm_stats = read_mode_config(pretrained_checkpoint)
model_config.trainer.pretrained_checkpoint = None
FrameworkModel = build_framework(cfg=model_config)
FrameworkModel.norm_stats = norm_stats
FrameworkModel.load_state_dict(model_state_dict, strict=True)
```

部署加载使用 `strict=True`，因此参数 key 不匹配会报错。训练时 `load_pretrained_backbones()` 的全量加载使用 `strict=False`，两者严格程度不同。

## optimizer state 不保存

官方 FAQ 明确说明：StarVLA 不保存 optimizer state，原因是占用大量内存和磁盘，而收益有限。`_save_checkpoint()` 只保存模型 state dict：

```python
torch.save(state_dict, checkpoint_path + "_pytorch_model.pt")
```

恢复训练时：

- 可以加载模型权重继续训练。
- 可以通过 `reload_modules` 部分加载指定模块的权重。
- optimizer 和 scheduler 会从头初始化，不会从断点恢复。

## 小结

- checkpoint 权重必须和 `config.yaml`、`dataset_statistics.json` 一起保留。
- 当前代码保存模型 state dict，只包含模型权重，未包含完整训练状态目录。
- `reload_modules` 可以按模块路径部分加载权重。
- 部署加载更严格，参数 key 必须匹配。

## 动手练习

1. 找一个训练输出目录，执行 `ls <RUN_DIR>/<run_id>/checkpoints <RUN_DIR>/<run_id>/config.yaml <RUN_DIR>/<run_id>/dataset_statistics.json`。三项都能列出，说明部署文件齐全。
2. 运行 `rg -n "load_pretrained_backbones|reload_modules|strict=True|strict=False" starVLA/training/trainer_utils/trainer_tools.py`，解释 `reload_modules` 如何筛选 key。
3. 运行 `rg -n "from_pretrained|load_state_dict|strict" starVLA/model/framework/base_framework.py starVLA/training/trainer_utils/trainer_tools.py`，对比训练加载和部署加载的严格程度。

## 导航

- 上一节：[04 优化器与冻结](04-optimizer-freeze.md)
- 返回上级：[训练机制](../05-training.md)
- 下一节：[部署与推理服务](../06-deployment.md)
