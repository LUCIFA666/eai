# 训练

目标：读懂 LIBERO 训练配置，写出可复现的训练命令，知道正常训练的 loss 表现。

## 主配置文件

LIBERO 的主配置在：

```text
examples/LIBERO/train_files/starvla_cotrain_libero.yaml
```

先关注几个关键字段：

```yaml
framework:
  name: QwenGR00T
  qwenvl:
    base_vlm: <MODEL_ROOT>/Qwen3-VL-4B-Instruct
    attn_implementation: flash_attention_2
  action_model:
    action_dim: 7
    state_dim: 7
    action_horizon: 8

datasets:
  vla_data:
    dataset_py: lerobot_datasets
    data_root_dir: <DATA_ROOT>/LEROBOT_LIBERO_DATA
    data_mix: libero_all
    per_device_batch_size: 16
```

`framework.name` 决定动作头类型，`data_mix` 决定使用哪些子数据集。这两个字段可以在命令行里覆盖，不用每次改 YAML。

## 基础训练命令

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
  --run_id libero_oft_test
```

- 第一次验证链路时把 `max_train_steps` 设为 10，确认 loss 能打印再正式训练。
- `--run_id` 用来区分实验，建议写成有意义的名字（`libero_oft_30k`、`libero_pi_5k` 等）。
- 命令行里的 `--framework.name`、`--datasets.vla_data.data_mix` 等参数会覆盖 YAML 里的同名字段。

## 官方训练脚本

官方仓库也提供：

```text
examples/LIBERO/train_files/run_libero_train.sh
```

运行前需要修改：

| 变量 | 含义 |
|---|---|
| `Framework_name` | `QwenOFT`、`QwenFast`、`QwenPI` 或 `QwenGR00T` |
| `base_vlm` | `<MODEL_ROOT>` 下的 VLM 路径 |
| `libero_data_root` | `<DATA_ROOT>/LEROBOT_LIBERO_DATA` |
| `data_mix` | `libero_all` 或 `libero_goal` |
| `run_root_dir` | `<RUN_DIR>` |
| `run_id` | 实验名 |

注意：脚本顶部包含机器相关的 NCCL 网卡/IB 变量，单机测试时删除或注释掉。还要检查 `--datasets.vla_data.data_root_dir` 那一行续行符前是否有空格，避免参数和下一行粘连：

```bash
# 错误：参数和下一行粘连
--datasets.vla_data.data_root_dir ${libero_data_root}\

# 正确：续行符前有空格
--datasets.vla_data.data_root_dir ${libero_data_root} \
```

## 训练输出

训练完成后，输出目录结构：

```text
<RUN_DIR>/<run_id>/
├── checkpoints/
│   └── steps_*_pytorch_model.pt
├── config.full.yaml
├── config.yaml
├── dataset_statistics.json
└── summary.jsonl
```

`config.yaml` 和 `dataset_statistics.json` 是部署时的必要文件，不能只保留 `.pt` 权重。

## WandB 记录

需要上传时：

```bash
--wandb_project <PROJECT_NAME>
--wandb_entity <ENTITY_NAME>
```

关闭时：

```bash
export WANDB_MODE=disabled
```

## 判断训练是否正常

WandB 或本地日志里看 `mse_score` 和 `action_dit_loss`：

| 现象 | 含义 |
|---|---|
| loss 稳步下降 | 训练正常 |
| loss 震荡后趋于平稳 | 通常正常，学习率可能偏高 |
| loss 完全不动 | 检查学习率、冻结设置、数据是否加载 |
| loss NaN | 检查 bf16/fp16 溢出、数据归一化 |

loss 下降不等于闭环评测成功。评测时还需要检查图像方向、动作尺度和 gripper 方向。

## 小结

- 训练命令核心三项：`framework.name`、`data_root_dir`、`data_mix`。
- 第一次验证用 10 步，正式训练再加步数。
- 训练输出目录必须完整保留，不能只存 `.pt` 文件。

## 动手练习

1. 运行 `rg -n "run_root_dir|run_id|data_root_dir|data_mix|action_horizon" examples/LIBERO/train_files/starvla_cotrain_libero.yaml`，确认训练命令覆盖的字段都来自官方 YAML。
2. 用 `max_train_steps 10` 跑一次小步训练后，列出 `<RUN_DIR>/<run_id>/` 下的文件，确认 `config.yaml` 和 `dataset_statistics.json` 都存在。
3. 运行 `rg -n "cfg.output_dir = os.path.join" starVLA/training/train_starvla.py`，确认输出目录由 `run_root_dir/run_id` 拼出。

## 导航

- 上一节：[01 数据准备](01-data-prep.md)
- 返回上级：[LIBERO 端到端实战](../07-libero-end-to-end.md)
- 下一节：[03 部署与评测](03-deployment-eval.md)
