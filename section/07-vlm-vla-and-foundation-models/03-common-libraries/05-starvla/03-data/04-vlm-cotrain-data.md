# VLM 协同训练数据

目标：理解 StarVLA 如何把通用图文数据和机器人动作数据放进同一次训练，以及为什么这对 VLA 可能有帮助。

StarVLA 支持三类训练入口：

| 入口 | 数据 | 目标 |
|---|---|---|
| `train_starvla.py` | VLA 数据 | 只训练动作预测 |
| `train_starvla_cotrain.py` | VLA + VLM 数据 | 同时训练动作和图文任务 |
| `train_starvlm.py` | VLM 数据 | 只训练图文模型 |

本页关注第二类，也就是 VLA+VLM 协同训练。

## 配置结构

LIBERO 的协同训练 YAML 中有两个数据段：

```yaml
datasets:
  vlm_data:
    dataset_py: vlm_datasets
    dataformat: llava_json
    dataset_use: sharegpt4v_coco
    eval_dataset: sharegpt4v_coco
    per_device_batch_size: 4

  vla_data:
    dataset_py: lerobot_datasets
    data_root_dir: <DATA_ROOT>/LEROBOT_LIBERO_DATA
    data_mix: libero_all
    per_device_batch_size: 16
```

`vla_data` 走 LeRobot；`vlm_data` 走 `starVLA/dataloader/vlm_datasets.py`。

## VLM 数据格式

`vlm_datasets.py` 支持 Qwen/LLaVA 风格图文数据。核心逻辑包括：

- 读取 JSON 或 JSONL annotation。
- 处理 `<image>`、`<video>` 占位符。
- 构建 Qwen chat template。
- 只对 assistant 回答部分计算 label，其余 token 使用 `IGNORE_INDEX=-100`。

构造消息的函数 `_build_messages()` 会检查文本中的 `<image>` 和实际图片数量是否匹配：

```python
if seg == "<image>":
    if not image_pool:
        raise ValueError("Number of <image> placeholders exceeds the number of provided images")
    content.append(image_pool.pop(0))
```

这样能避免图文数据错位。

## 协同训练循环

`train_starvla_cotrain.py` 会同时创建两个 dataloader：

```python
vla_train_dataloader = build_dataloader(cfg=cfg, dataset_py=cfg.datasets.vla_data.dataset_py)
vlm_train_dataloader = build_dataloader(cfg=cfg, dataset_py=cfg.datasets.vlm_data.dataset_py)
```

每一步取两个 batch：

```python
batch_vla, batch_vlm = self._get_next_batch()
```

然后先算动作损失：

```python
output_dict = self.model.forward(batch_vla)
action_loss = output_dict["action_loss"]
self.accelerator.backward(action_loss)
```

再算 VLM 损失：

```python
unwrapped = self.accelerator.unwrap_model(self.model)
vlm_output = unwrapped.qwen_vl_interface(**batch_vlm)
vlm_loss = vlm_output.loss * self.config.trainer.loss_scale.vlm
self.accelerator.backward(vlm_loss)
```

协同训练会在同一个模型上交替优化 VLA 动作目标和 VLM 图文目标。

## loss_scale

YAML 中有：

```yaml
trainer:
  loss_scale:
    vla: 1.0
    vlm: 0.1
```

`vlm: 0.1` 表示 VLM 损失权重较小。直觉上，动作预测是当前任务主目标，图文损失用于保持或增强语言视觉能力。如果 VLM loss 权重过大，模型可能更偏向语言生成，动作精度会受影响。

## 何时使用协同训练

协同训练适合：

- 希望 VLA 保持较强图文理解能力。
- 数据中语言指令复杂，泛化依赖 VLM 语义。
- 使用大 VLM backbone，希望动作微调不要破坏原有能力。

不一定适合：

- 只做快速动作头验证。
- GPU 显存很紧张。
- VLM 数据路径还没整理好。
- 只想在一个小 benchmark 上验证 action head。

这种情况下可以先用 `train_starvla.py` 跑纯 VLA 训练。

## 小结

- `train_starvla_cotrain.py` 同时使用 VLA dataloader 和 VLM dataloader。
- VLM 数据走 LLaVA/Qwen 风格图文格式，不伪装成机器人动作数据。
- 协同训练每步分别 backward action loss 和 VLM loss。
- `trainer.loss_scale.vlm` 控制图文目标的影响强度。

## 动手练习

1. 运行 `rg -n "def _train_step|backward|loss_scale.vlm|vlm_output" starVLA/training/train_starvla_cotrain.py`，标出 action loss 和 VLM loss 的 backward 位置。
2. 运行 `rg -n "loss_scale:|vlm:" examples/LIBERO/train_files/starvla_cotrain_libero.yaml starVLA/config/training`，找到 `loss_scale.vlm` 的配置来源，再说明把它设为 `0.0` 会影响哪一项 loss。
3. 运行 `rg -n "IGNORE_INDEX|labels" starVLA/dataloader/vlm_datasets.py starVLA/model/modules/vlm`，找到用户 prompt 不参与 loss 的代码依据。

## 导航

- 上一节：[03 mixture 注册表](03-mixture-registry.md)
- 返回上级：[数据接口](../03-data.md)
- 下一节：[05 统计与归一化](05-statistics-and-normalization.md)
