# 链路验证

目标：用最小代价确认 StarVLA 的模型构建、数据加载、训练循环和部署入口能运行。链路验证只检查链路是否连通，不追求策略效果。

命令里出现的占位符（`<STARVLA_ROOT>`、`<MODEL_ROOT>`、`<DATA_ROOT>`、`<RUN_DIR>`）在[代码结构](../01-overview/02-code-struct.md)一节已有说明，使用前替换成自己机器上的实际路径。

## 验证顺序

```text
import 检查
  -> framework 检查
  -> dataloader 检查
  -> 10 step 训练
  -> policy server 启动
```

## import 检查

**前置条件**：已经完成 `pip install -e .`，并且当前工作目录是 `<STARVLA_ROOT>`。

```bash
cd <STARVLA_ROOT>
conda activate starvla

python -c "import starVLA; print(starVLA.__file__)"
python -c "from starVLA.model.framework.base_framework import build_framework; print(build_framework)"
python -c "from deployment.model_server.policy_wrapper import PolicyServerWrapper; print(PolicyServerWrapper)"
```

可观测输出：第一条会打印 `starVLA` 包路径，后两条会打印函数或类对象。如果这里失败，先处理安装和工作目录问题。

## framework 检查

**前置条件**：`<MODEL_ROOT>/Qwen3-VL-4B-Instruct` 已经存在，GPU 显存足够加载模型。以 `QwenGR00T` 为例，部分 framework 文件末尾带有单文件测试入口：

```bash
cd <STARVLA_ROOT>

python starVLA/model/framework/VLM4A/QwenGR00T.py \
  --config_yaml examples/LIBERO/train_files/starvla_cotrain_libero.yaml \
  --framework.qwenvl.base_vlm <MODEL_ROOT>/Qwen3-VL-4B-Instruct
```

可观测输出：脚本会加载配置、构建模型、创建随机样本，并调用 `forward()` 和 `predict_action()`。如果模型路径不存在，报错会先指向本地模型目录；如果 attention 后端不匹配，通常会在加载或第一次 forward 时暴露。

常见问题：

| 报错 | 检查 |
|---|---|
| 模型路径不存在 | `framework.qwenvl.base_vlm` 是否指向本机模型目录 |
| attention 报错 | `flash_attention_2` 是否适配当前 GPU |
| action shape 报错 | `action_dim`、`state_dim`、`action_horizon` 是否匹配 |
| CUDA OOM | 换小模型、启用 bf16、先用更小 batch |

## dataloader 检查

**前置条件**：已经准备好 LIBERO LeRobot 数据，目录下包含 `libero_goal_no_noops_1.0.0_lerobot` 等子数据集，并且每个子数据集有 `meta/modality.json`。

```bash
cd <STARVLA_ROOT>

python starVLA/dataloader/lerobot_datasets.py \
  --config_yaml examples/LIBERO/train_files/starvla_cotrain_libero.yaml \
  --data_root_dir <DATA_ROOT>/LEROBOT_LIBERO_DATA \
  --data_mix libero_goal
```

最终会创建 dataset 和 dataloader，并把统计文件写到 `./results/debug/dataset_statistics.json`。这个输出路径来自 `lerobot_datasets.py` 的调试入口，当前脚本没有提供 `--output_dir` 参数。

常见问题：

| 报错 | 原因 |
|---|---|
| `data_mix` 不存在 | 对应 benchmark 的 `data_config.py` 没有被加载 |
| 找不到数据目录 | `<DATA_ROOT>` 或子数据集名称写错 |
| 找不到 `modality.json` | 数据集 `meta/` 下缺少字段映射文件 |
| 视频读取失败 | video backend、编码格式或依赖不匹配 |

## 最小训练检查

**前置条件**：模型和 LIBERO 数据都已准备好。大规模训练前，把步数设到 10，并关闭 WandB 上传：

```bash
cd <STARVLA_ROOT>
export WANDB_MODE=disabled

accelerate launch \
  --num_processes 1 \
  starVLA/training/train_starvla.py \
  --config_yaml examples/LIBERO/train_files/starvla_cotrain_libero.yaml \
  --framework.name QwenOFT \
  --framework.qwenvl.base_vlm <MODEL_ROOT>/Qwen3-VL-4B-Instruct \
  --datasets.vla_data.data_root_dir <DATA_ROOT>/LEROBOT_LIBERO_DATA \
  --datasets.vla_data.data_mix libero_goal \
  --datasets.vla_data.per_device_batch_size 1 \
  --trainer.max_train_steps 10 \
  --trainer.save_interval 5 \
  --run_root_dir <RUN_DIR> \
  --run_id link_test
```

训练脚本会把输出目录设置为 `<RUN_DIR>/link_test`，这个规则来自 `train_starvla.py` 中的 `cfg.output_dir = os.path.join(cfg.run_root_dir, cfg.run_id)`。

跑完后检查：

```text
<RUN_DIR>/link_test/
├── checkpoints/
│   └── steps_5_pytorch_model.pt
├── config.full.yaml
├── config.yaml
├── dataset_statistics.json
└── summary.jsonl
```

部署依赖 `config.yaml` 和 `dataset_statistics.json`，因此训练输出目录要保持完整。

## policy server 检查

**前置条件**：上一步已经产生 `<RUN_DIR>/link_test/checkpoints/steps_5_pytorch_model.pt`，并且同级运行目录里保留了 `config.yaml` 和 `dataset_statistics.json`。

```bash
cd <STARVLA_ROOT>

python deployment/model_server/server_policy.py \
  --ckpt_path <RUN_DIR>/link_test/checkpoints/steps_5_pytorch_model.pt \
  --port 10093
```

可观测输出：服务启动日志会出现 `server running ... metadata=...`，metadata 中应包含 `action_chunk_size`、`available_unnorm_keys` 和 checkpoint 路径。能启动到这一步，说明 checkpoint、配置、framework 和数据统计已经能被一起加载。

## 小结

- 链路验证按 import、framework、dataloader、最小训练、server 的顺序做。
- framework 测试主要排模型路径、attention 后端和动作 shape。
- dataloader 测试主要排数据目录、`modality.json` 和 `data_mix`。
- 部署测试会暴露 checkpoint 元数据缺失问题。

## 动手练习

1. 运行 `rg -n "parser.add_argument|dataset_statistics" starVLA/dataloader/lerobot_datasets.py`，确认 dataloader 调试入口支持 `--config_yaml`、`--data_root_dir`、`--data_mix`，并会写出 `dataset_statistics.json`。
2. 在准备好 LIBERO 数据后，用 `--data_mix libero_goal` 跑一次 dataloader 检查。成功输出应包含 `results/debug/dataset_statistics.json`。
3. 在完成 10 step 小训练后启动 policy server。成功输出应在日志 metadata 中看到 `action_chunk_size` 和 `ckpt_path`。

## 导航

- 上一节：[01 环境安装](01-install.md)
- 返回上级：[安装与链路验证](../02-setup.md)
- 下一节：[数据接口](../03-data.md)
