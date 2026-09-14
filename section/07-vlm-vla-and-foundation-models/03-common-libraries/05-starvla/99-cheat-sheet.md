# StarVLA 速查表

目标：快速查找 StarVLA 常用命令、配置字段、文件位置和排错入口。

## 路径占位符

| 占位符 | 含义 |
|---|---|
| `<STARVLA_ROOT>` | StarVLA 仓库根目录 |
| `<DATA_ROOT>` | 数据集根目录 |
| `<MODEL_ROOT>` | 预训练模型根目录 |
| `<RUN_DIR>` | 训练输出根目录 |
| `<CKPT_PATH>` | 具体 checkpoint 文件 |

## 常用命令

安装：

```bash
cd <STARVLA_ROOT>
conda create -n starvla python=3.10 -y
conda activate starvla
pip install -v torch==2.6.0 torchvision==0.21.0 \
  --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
pip install flash-attn==2.7.4.post1 --no-build-isolation
pip install -e .
```

下载基础模型：

```bash
huggingface-cli download Qwen/Qwen3-VL-4B-Instruct \
  --local-dir <MODEL_ROOT>/Qwen3-VL-4B-Instruct
```

准备 LIBERO 数据：

```bash
cd <STARVLA_ROOT>
export DEST=<DATA_ROOT>
bash examples/LIBERO/data_preparation.sh
```

framework 链路验证：

```bash
cd <STARVLA_ROOT>
python starVLA/model/framework/VLM4A/QwenGR00T.py \
  --config_yaml examples/LIBERO/train_files/starvla_cotrain_libero.yaml \
  --framework.qwenvl.base_vlm <MODEL_ROOT>/Qwen3-VL-4B-Instruct
```

dataloader 链路验证：

```bash
cd <STARVLA_ROOT>
python starVLA/dataloader/lerobot_datasets.py \
  --config_yaml examples/LIBERO/train_files/starvla_cotrain_libero.yaml \
  --data_root_dir <DATA_ROOT>/LEROBOT_LIBERO_DATA \
  --data_mix libero_goal
```

单卡小步训练：

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
  --run_id smoke_test
```

启动 policy server：

```bash
cd <STARVLA_ROOT>
python deployment/model_server/server_policy.py \
  --ckpt_path <CKPT_PATH> \
  --port 10093 \
  --use_bf16
```

LIBERO 最小评测：

```bash
cd <STARVLA_ROOT>
python examples/LIBERO/eval_files/eval_libero.py \
  --host 127.0.0.1 \
  --port 10093 \
  --task_suite_name libero_goal \
  --num_trials_per_task 1 \
  --max_tasks 1 \
  --video_out_path <RUN_DIR>/libero_eval_videos
```

## 关键文件

| 想做什么 | 文件 |
|---|---|
| 构建 framework | `starVLA/model/framework/base_framework.py` |
| 查看 QwenGR00T | `starVLA/model/framework/VLM4A/QwenGR00T.py` |
| 查看 QwenOFT | `starVLA/model/framework/VLM4A/QwenOFT.py` |
| 查看 VLA dataloader | `starVLA/dataloader/lerobot_datasets.py` |
| 查看训练循环 | `starVLA/training/train_starvla.py` |
| 查看协同训练 | `starVLA/training/train_starvla_cotrain.py` |
| 查看学习率/冻结 | `starVLA/training/trainer_utils/trainer_tools.py` |
| 查看 server | `deployment/model_server/server_policy.py` |
| 查看 server wrapper | `deployment/model_server/policy_wrapper.py` |
| 查看反归一化 | `deployment/model_server/policy_norm_processor.py` |
| 查看 LIBERO 适配 | `examples/LIBERO/eval_files/model2libero_interface.py` |

## 关键配置字段

| 字段 | 含义 |
|---|---|
| `framework.name` | 模型框架名 |
| `framework.qwenvl.base_vlm` | 基础 VLM 路径 |
| `framework.qwenvl.attn_implementation` | attention 后端 |
| `framework.action_model.action_dim` | 动作维度 |
| `framework.action_model.state_dim` | 状态维度 |
| `framework.action_model.action_horizon` | 动作 chunk 长度 |
| `datasets.vla_data.data_root_dir` | VLA 数据根目录 |
| `datasets.vla_data.data_mix` | 数据混合注册名 |
| `datasets.vla_data.per_device_batch_size` | 每卡 batch size |
| `trainer.learning_rate` | 学习率分组 |
| `trainer.freeze_modules` | 冻结模块路径 |
| `trainer.max_train_steps` | 训练步数上限 |
| `trainer.save_interval` | checkpoint 间隔 |

## 常见错误定位

| 现象 | 优先检查 |
|---|---|
| `Framework ... is not implemented` | `framework.name`、registry import |
| 找不到数据 | `data_root_dir + dataset_name` 拼接路径 |
| 缺少字段 | `modality.json`、`DataConfig` |
| action shape mismatch | `action_indices`、`action_horizon`、`action_dim` |
| CUDA OOM | batch size、模型大小、bf16、freeze |
| 学习率组没生效 | 模块属性名是否匹配 |
| server 缺 config/statistics | checkpoint run 目录结构 |
| client 连不上 | host、port、server 是否启动 |
| 返回 key 不对 | 当前代码使用 `response["data"]["actions"]` |
| 评测动作异常 | 图像顺序、反归一化、gripper、delta/absolute |

## 图片说明

本教程优先使用 StarVLA 官方仓库中的图片：

- `starVLA_overview.png`
- `starVLA_dataflow.png`
- `starvla_variants.png`
- `starVLA_PolicyServer.png`
- `starVLA_PolicyInterface.png`
- `starvla_LIBERO.png`
- `starvla_simpleEnv.png`
- `stavla_RoboCasa.png`
- `calvin.png`
- `libero-example.gif`

当前没有新增手绘占位图。后续如果需要训练循环或自有数据接入流程图，优先参考官方论文和仓库图，再考虑补充新的示意图。

## 导航

- 上一节：[扩展 StarVLA](09-extension.md)
- 返回上级：[StarVLA](../05-starvla.md)
