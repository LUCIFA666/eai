# 训练循环

目标：逐步拆开 `VLATrainer.train()`，看清每一步训练里数据、模型、loss、优化器和 checkpoint 如何协作。

StarVLA 的训练循环和普通 PyTorch 项目很接近，只是用 Accelerate 包装了分布式、混合精度和梯度同步。

## prepare_training

训练前准备包括：

```python
self._save_initial_configs()
self._init_checkpointing()
self._adjust_lr_scheduler_for_resume()
self.model = self.freeze_backbones(self.model, freeze_modules=freeze_modules)
self.print_trainable_parameters(self.model)
self.model, self.optimizer, self.vla_train_dataloader = self.setup_distributed_training(...)
self._init_wandb()
```

顺序为：

1. 先保存配置，避免后面崩溃时没有可排查的 run 目录。
2. 再加载或恢复 checkpoint。
3. 再冻结模块和打印参数量。
4. 最后交给 `accelerator.prepare()`。

## 数据迭代

训练开始时创建 iterator：

```python
self.vla_iter = iter(self.vla_train_dataloader)
```

每步取 batch：

```python
try:
    batch_vla = next(self.vla_iter)
except StopIteration:
    self.vla_iter, self.vla_epoch_count = TrainerUtils._reset_dataloader(...)
    batch_vla = next(self.vla_iter)
```

这表示训练按 step 驱动，epoch 只作为 dataloader 迭代边界。到达 dataloader 末尾后会重建 iterator，直到 `max_train_steps`。

## 单步训练

`_train_step()` 的核心：

```python
with self.accelerator.accumulate(self.model):
    self.optimizer.zero_grad()

    with torch.autocast("cuda", dtype=torch.bfloat16):
        output_dict = self.model.forward(batch_vla)
        action_loss = output_dict["action_loss"]
        total_loss = action_loss

    self.accelerator.backward(total_loss)

    if self.config.trainer.gradient_clipping is not None:
        self.accelerator.clip_grad_norm_(self.model.parameters(), self.config.trainer.gradient_clipping)

    self.optimizer.step()
    if self.accelerator.sync_gradients:
        self.lr_scheduler.step()
```

几个细节：

- `torch.autocast("cuda", dtype=torch.bfloat16)` 用 bf16 跑大模型前向。
- backward 通过 `accelerator.backward()`，由 Accelerate 处理分布式细节。
- scheduler 只在 `sync_gradients` 时 step，避免梯度累积时学习率走太快。
- 返回日志中 key 叫 `action_dit_loss`，OFT 等非 DiT 变体也沿用了这个日志名。

## 在线评估

每隔 `eval_interval`，训练器调用：

```python
output_dict = self.accelerator.unwrap_model(self.model).predict_action(
    examples=examples,
    use_ddim=True,
    num_ddim_steps=20,
)
normalized_actions = output_dict["normalized_actions"]
score = TrainerUtils.euclidean_distance(normalized_actions, actions)
step_metrics["mse_score"] = score / num_pots
```

这是一个训练期 sanity check，不等于 benchmark 成功率。它只是看模型预测的 normalized action 和当前 batch 标签的距离。真正的任务成功率要做部署和 benchmark 环境评测。

## 日志

`_log_metrics()` 会记录：

- action loss。
- VLM loss，协同训练时。
- data/model 时间。
- 每个学习率组当前 learning rate。
- epoch 估计值。

WandB 只在 main process 上初始化和记录。

## checkpoint 保存

每隔 `save_interval`：

```python
state_dict = self.accelerator.get_state_dict(self.model)
torch.save(state_dict, checkpoint_path + "_pytorch_model.pt")
```

最终训练结束还会保存：

```text
final_model/pytorch_model.pt
```

这类 checkpoint 是模型权重 state dict，只包含模型权重，未包含完整训练状态目录。当前代码中没有在 `_save_checkpoint()` 里保存 optimizer state。恢复训练时可加载模型权重，但 optimizer/scheduler 是否完整恢复要以当前代码为准。

## 小结

- StarVLA 训练按 step 驱动，到 dataloader 末尾会自动重建 iterator。
- 单步训练调用 `model.forward(batch_vla)` 并期望返回 `action_loss`。
- scheduler 只在梯度同步时 step，适配梯度累积。
- 训练期 `mse_score` 只是动作预测误差，不能直接代表 benchmark 成功率。
- 当前代码保存模型 state dict 和配置/统计文件，optimizer 状态目录需要单独确认。

## 动手练习

1. 运行 `rg -n "autocast|backward|clip_grad|optimizer.step|lr_scheduler.step|zero_grad" starVLA/training/train_starvla.py`，标出一次 `_train_step()` 的顺序。
2. 在准备好数据和模型后，把 `--trainer.eval_interval` 设为很小的值跑小步训练。成功日志或 `summary.jsonl` 中应出现 `mse_score`。
3. 运行 `rg -n "save_interval|steps_.*pytorch_model|final_model" starVLA/training/train_starvla.py`，说明中间 checkpoint 和 final model 的文件名依据。

## 导航

- 上一节：[02 训练入口](02-train-entrypoints.md)
- 返回上级：[训练机制](../05-training.md)
- 下一节：[04 优化器与冻结](04-optimizer-freeze.md)
