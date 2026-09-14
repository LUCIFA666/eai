# 扩展调试顺序

目标：给新增数据集、新模型或新 benchmark 时的调试顺序。按这个顺序做，可以避免把数据问题误判成模型问题。

## 验证数据

第一步永远是验证数据：

```bash
python starVLA/dataloader/lerobot_datasets.py \
  --config_yaml examples/MyRobot/train_files/starvla_my_robot.yaml \
  --data_mix my_dataset \
  --data_root_dir <DATA_ROOT>/MY_DATA_ROOT
```

检查：

- 能否取到 batch。
- 每个样本是否有 `image/lang/action/state`。
- action shape 是否等于 `[action_horizon, action_dim]`。
- 图像视角数量和顺序是否正确。
- `dataset_statistics.json` 是否能保存。

## 验证 framework

数据通后，跑 framework 单文件验证：

```bash
python starVLA/model/framework/VLM4A/MyFramework.py \
  --config_yaml examples/MyRobot/train_files/starvla_my_robot.yaml
```

检查：

- 模型能否加载。
- `forward()` 是否返回 `action_loss`。
- `predict_action()` 是否返回 `normalized_actions`。
- shape 是否为 `[B, action_horizon, action_dim]`。

## 小步数训练

再跑 10 到 100 步训练：

```bash
accelerate launch \
  --config_file starVLA/config/deepseeds/deepspeed_zero2.yaml \
  --num_processes 1 \
  starVLA/training/train_starvla.py \
  --config_yaml examples/MyRobot/train_files/starvla_my_robot.yaml \
  --trainer.max_train_steps 20 \
  --trainer.save_interval 10 \
  --datasets.vla_data.per_device_batch_size 1
```

检查输出目录是否包含：

```text
checkpoints/
config.yaml
config.full.yaml
dataset_statistics.json
summary.jsonl
```

## server 测试

用刚保存的 checkpoint 启动 server：

```bash
python deployment/model_server/server_policy.py \
  --ckpt_path <RUN_DIR>/my_run/checkpoints/steps_10_pytorch_model.pt \
  --port 10093
```

再用最小 websocket client 发送随机图像，确认返回 `actions`。

## benchmark 接入

最后才接环境：

1. 先跑 1 个 task、1 个 episode。
2. 保存输入图像。
3. 打印动作 min/max。
4. 打印 gripper 通道。
5. 保存失败视频。

如果这一步失败，不要马上改模型。先判断是图像、动作尺度、gripper 还是环境控制器问题。

## 常见问题

| 阶段 | 失败说明 |
|---|---|
| dataloader 失败 | 字段映射、数据目录、video backend |
| framework 失败 | 模型路径、shape、VLM processor |
| 小步训练失败 | loss、显存、学习率组、冻结路径 |
| server 失败 | checkpoint 结构、config、statistics、state dict |
| benchmark 失败 | 图像预处理、动作适配、gripper、环境依赖 |

## 小结

- 扩展时按数据、framework、小步训练、server、benchmark 的顺序排查。
- 每一步只验证一个边界，不要跨太多模块。
- 保存图像和动作分布是评测调试最有效的证据。

## 动手练习

1. 参考 `starVLA/dataloader/lerobot_datasets.py`、`starVLA/training/train_starvla.py` 和 `deployment/model_server/server_policy.py`，为自己的数据集写一份 5 步调试 checklist。
2. 在小步训练输出目录中执行 `ls config.yaml dataset_statistics.json checkpoints`。成功输出说明部署所需文件齐全。
3. 启动自定义 checkpoint 的 server 后发送最小 websocket 请求。成功输出应包含 `actions`，shape 应为 `[B, action_chunk_size, action_dim]`。

## 导航

- 上一节：[03 新 backbone 或 action head](03-new-backbone-or-head.md)
- 返回上级：[扩展 StarVLA](../09-extension.md)
- 下一节：[速查表](../99-cheat-sheet.md)
