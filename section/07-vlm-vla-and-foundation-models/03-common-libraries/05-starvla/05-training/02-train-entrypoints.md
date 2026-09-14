# 训练入口

目标：区分 StarVLA 中几个训练脚本的用途，并知道什么时候该用哪一个。

StarVLA 当前主要训练入口在 `starVLA/training/`：

| 文件 | 用途 | 数据 |
|---|---|---|
| `train_starvla.py` | 纯 VLA 训练 | 机器人动作数据 |
| `train_starvla_cotrain.py` | VLA + VLM 协同训练 | 机器人动作数据 + 图文数据 |
| `train_starvlm.py` | 纯 VLM 训练 | 图文数据 |
| `train_starvln.py` | VLN 相关训练 | 导航数据 |

日常训练 VLA，常见入口是前两个。

## train_starvla.py

纯 VLA 训练入口：

```python
output_dir = setup_directories(cfg=cfg)
vla = build_framework(cfg)
vla_train_dataloader = prepare_data(cfg=cfg, accelerator=accelerator, output_dir=output_dir)
optimizer, lr_scheduler = setup_optimizer_and_scheduler(model=vla, cfg=cfg)

trainer = VLATrainer(...)
trainer.prepare_training()
trainer.train()
```

它只创建一个 VLA dataloader：

```python
vla_train_dataloader = build_dataloader(cfg=cfg, dataset_py=cfg.datasets.vla_data.dataset_py)
```

适合：

- 快速训练动作模型。
- 调试新 action head。
- 数据和显存有限，不想引入 VLM 图文数据。
- 先验证 benchmark 链路。

## train_starvla_cotrain.py

协同训练入口：

```python
vla_train_dataloader, vlm_train_dataloader = prepare_data(...)
```

它会创建两个 dataloader：

```python
vla_train_dataloader = build_dataloader(cfg=cfg, dataset_py=cfg.datasets.vla_data.dataset_py)
vlm_train_dataloader = build_dataloader(cfg=cfg, dataset_py=cfg.datasets.vlm_data.dataset_py)
```

训练时同一步里算 action loss 和 VLM loss：

```python
output_dict = self.model.forward(batch_vla)
action_loss = output_dict["action_loss"]
self.accelerator.backward(action_loss)

vlm_output = unwrapped.qwen_vl_interface(**batch_vlm)
vlm_loss = vlm_output.loss * self.config.trainer.loss_scale.vlm
self.accelerator.backward(vlm_loss)
```

适合：

- 希望减少 VLM backbone 灾难性遗忘。
- 需要保持图文理解能力。
- 已经准备好 QwenVL conversation 格式图文数据。

## train_starvlm.py

纯 VLM 训练用于图文模型微调，不涉及机器人动作。官方 VLM 联合训练文档中提到，如果只想做 VLM 特定领域微调，可以选择这一类入口。

需要注意当前代码文件名是：

```text
starVLA/training/train_starvlm.py
```

某些文档里可能写成 `train_starvla_vlm.py`，以当前代码为准。

## DeepSpeed 配置

训练命令通常用：

```bash
accelerate launch \
  --config_file starVLA/config/deepseeds/deepspeed_zero2.yaml \
  --num_processes 8 \
  starVLA/training/train_starvla.py \
  --config_yaml ...
```

`--config_file` 属于 Accelerate/DeepSpeed 配置，StarVLA 的训练配置由 `--config_yaml` 指定。常见选项：

| 文件 | 用途 |
|---|---|
| `deepspeed_zero2.yaml` | ZeRO-2，常用训练配置 |
| `deepspeed_zero3.yaml` | ZeRO-3，更省显存但复杂度更高 |

单卡快速验证可以把 `--num_processes` 设为 1。

## 小结

- 纯动作训练用 `train_starvla.py`。
- VLA+VLM 协同训练用 `train_starvla_cotrain.py`。
- 纯图文微调用 `train_starvlm.py`。
- Accelerate 的 `--config_file` 和 StarVLA 的 `--config_yaml` 是两套配置。

## 动手练习

1. 运行 `rg -n "def prepare_data|vla_train_dataloader|vlm_train_dataloader" starVLA/training/train_starvla.py starVLA/training/train_starvla_cotrain.py`，找到两个入口的数据加载差异。
2. 按本章小步训练模板写一个单卡纯 VLA 训练命令，把 `--num_processes` 设为 1，并把 `--trainer.max_train_steps` 设为 10。成功输出应写入 `<RUN_DIR>/<run_id>/summary.jsonl`。
3. 运行 `rg -n "loss_scale.vlm|batch_vlm|qwen_vl_interface" starVLA/training/train_starvla_cotrain.py`，判断当前任务是否需要 VLM 协同训练，并说明依据。

## 导航

- 上一节：[01 配置系统](01-config-system.md)
- 返回上级：[训练机制](../05-training.md)
- 下一节：[03 训练循环](03-training-loop.md)
