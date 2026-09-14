# Checkpoint 组件加载

目标：理解 `openvla_utils.py` 如何从 checkpoint 目录或 Hugging Face repo 中加载模型组件。

评测和部署都依赖 `experiments/robot/openvla_utils.py`。`pretrained_checkpoint` 传进去以后，脚本会围绕这个路径读取多类文件：基础模型、processor、action head、proprio projector 和 statistics。

| 函数 | 作用 |
| --- | --- |
| `get_vla` | 从 `pretrained_checkpoint` 加载 VLA backbone，并把 `dataset_statistics.json` 放到 `model.norm_stats`。 |
| `get_processor` | 用同一个 checkpoint 路径加载 processor / tokenizer。 |
| `get_action_head` | 按当前 `llm_dim` 和 flags 初始化 continuous action head，再加载权重。 |
| `get_proprio_projector` | 按 `PROPRIO_DIM` 初始化 proprio projector，再加载权重。 |
| `find_checkpoint_file` | 在本地 checkpoint 目录里查找组件文件。 |
| `get_vla_action` | 处理输入、调用模型、返回 action chunk。 |

## 加载顺序

LIBERO eval 或 policy server 读取 checkpoint 时，通常会经过下面几类加载：

| 组件 | 来自哪里 | 依赖哪些配置 |
| --- | --- | --- |
| VLA backbone / config | `pretrained_checkpoint` 或 HF repo | `use_minivlm`、模型配置文件。 |
| processor / tokenizer | checkpoint 目录或基础模型目录 | `num_images_in_input`、图像处理配置。 |
| action head | `action_head--...` 文件 | `use_l1_regression`、`use_pro_version`、`ACTION_DIM`、`NUM_ACTIONS_CHUNK`。 |
| proprio projector | `proprio_projector--...` 文件 | `use_proprio`、`PROPRIO_DIM`。 |
| statistics | `dataset_statistics.json` | `unnorm_key`、`task_suite_name`、proprio normalization。 |

## 本地路径和 HF repo id

如果 `pretrained_checkpoint` 是本地目录，工具函数会在目录里找组件文件。如果传的是 Hugging Face repo id，则可能通过 Hub 下载组件。教程主线优先使用本地 `outputs/...`，方便复查下载结果和实验记录。

本地目录里的同类组件需要唯一。`find_checkpoint_file()` 的查找规则很直接：

```python
checkpoint_files = []
for filename in os.listdir(pretrained_checkpoint):
    if file_pattern in filename and "checkpoint" in filename:
        full_path = os.path.join(pretrained_checkpoint, filename)
        checkpoint_files.append(full_path)

assert len(checkpoint_files) == 1, (
    f"Expected exactly 1 {file_pattern} checkpoint but found {len(checkpoint_files)}"
)
```

如果目录里没有 `action_head` 文件会失败；如果同一个目录里残留多个匹配文件，也会失败。清理或复制 checkpoint 时，最好保留一个明确的 step 目录，不要把多个 step 的组件混在一起。

HF Hub 分支主要覆盖官方发布的 Pro checkpoint。`get_action_head()` 和 `get_proprio_projector()` 对官方 repo id 有固定文件名映射；自定义上传的 repo 若不符合这些文件名和组件结构，需要按实际加载逻辑检查。

## 评测前可以先看这几类文件

一个可用于评测的 checkpoint 通常包含多类文件。可以先确认模型配置、模型权重、processor/tokenizer、action head、proprio projector 和 statistics 是否齐全。

```bash
find outputs/LIBERO-Spatial-Pro -maxdepth 1 -type f | sort
```

本地训练产物也按同样原则检查。若 `merge_lora_during_training=True`，step checkpoint 目录应能被 `run_libero_eval.py` 直接作为 `--pretrained_checkpoint` 使用；若关闭 merge，则需要按实际保存逻辑确认 eval 能加载哪些组件。

## 导航

- 上一节：[Pro Version Flags](04-pro-version-flags.md)
- 返回上级：[模型组件](../04-model.md)
- 下一节：[训练、评测与部署的一致性](06-training-eval-consistency.md)
