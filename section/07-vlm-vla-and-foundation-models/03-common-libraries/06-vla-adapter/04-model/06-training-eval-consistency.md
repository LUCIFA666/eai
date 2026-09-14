# 训练、评测与部署的一致性

目标：确认 VLA-Adapter 的训练、评测和部署使用同一套输入结构、模型组件、维度常量、checkpoint 文件和 normalization 配置。

VLA-Adapter 的 LIBERO-Pro 主线依赖一组跨页面共享的配置。它们会影响数据字段、模型结构、checkpoint 组件和动作还原方式。训练能跑通、checkpoint 能加载、policy server 能返回 action，只说明各自的局部链路正常；要让 rollout 行为可信，这些入口需要使用同一组配置。

## 输入结构要保持一致

| 配置 | 主线取值 | 影响位置 |
| --- | --- | --- |
| `num_images_in_input` | `2` | `RLDSBatchTransform`、processor、`run_libero_eval.py` observation、policy server payload。 |
| `use_proprio` | `True` | batch 中的 proprio 字段、`ProprioProjector`、checkpoint 中的 projector 权重、proprio normalization。 |
| `use_film` | `False` | VLA-Adapter 的模型加载分支和 checkpoint 配置。 |

训练、评测、部署看到的图像数量和 proprio 输入需要一致。评测命令里把 `use_proprio` 打开，但 checkpoint 没有 projector 文件，会直接加载失败；payload 少传图像或 state，则会在 processor、server 或 action head 前后暴露。

## 模型组件要来自同一组配置

| 配置或文件 | 主线取值或形态 | 影响位置 |
| --- | --- | --- |
| `vlm_path` | `pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b` | 训练时加载基础 tiny Prismatic VLM。 |
| `config_file_path` | `pretrained_models/configs` | 训练时加载 Prismatic / processor 配置。 |
| `pretrained_checkpoint` | `outputs/LIBERO-*-Pro` 或本地 `$ARTIFACT_ROOT/runs/...--N_chkpt` | 评测和部署时加载模型、processor、action head、projector、statistics。 |
| `use_pro_version` | `True` | Pro checkpoint 的 action head 和相关组件加载。 |
| `dataset_statistics.json` | checkpoint / run 目录中的统计文件 | action unnormalization 和 proprio normalization。 |

`vlm_path` 主要服务训练入口，`pretrained_checkpoint` 主要服务评测和部署入口。二者含义不同：一个是基础 VLM 来源，一个是可评测策略组件目录。混用这两个路径通常会导致组件缺失或 processor 加载失败。

## 动作维度和还原方式要匹配

| 常量或参数 | 主线值 | 影响位置 |
| --- | --- | --- |
| `ACTION_DIM` | `7` | LIBERO 单步动作维度、action head 输出最后一维。 |
| `PROPRIO_DIM` | `8` | LIBERO proprio state 维度、proprio projector 输入。 |
| `NUM_ACTIONS_CHUNK` | `8` | action head 一次输出的未来动作步数。 |
| `num_open_loop_steps` | 通常与 chunk 对齐 | LIBERO rollout 中多少步后重新查询策略。 |
| `unnorm_key` | 如 `libero_spatial` | 选择 statistics 中用于动作还原的 key。 |

action shape mismatch 通常从 `ACTION_DIM`、`NUM_ACTIONS_CHUNK`、数据 action label、client action queue 四处排查。动作尺度异常通常从 `dataset_statistics.json` 和 `unnorm_key` 排查。

## 从现象反查

| 现象 | 先看哪里 |
| --- | --- |
| checkpoint 加载阶段失败 | `pretrained_checkpoint` 路径、processor 文件、`action_head--...`、`proprio_projector--...`。 |
| action shape mismatch | 当前命令触发的平台常量、`ACTION_DIM`、`NUM_ACTIONS_CHUNK`、client / eval action queue。 |
| rollout 能跑但动作幅度异常 | `dataset_statistics.json`、`unnorm_key`、训练数据名和评测 suite 是否对应。 |
| `unnorm_key` 不存在 | `model.norm_stats` 中的 key、`task_suite_name`、训练时保存的 statistics。 |

## 最小检查表

| 场景 | 建议核对 |
| --- | --- |
| 官方 Pro checkpoint smoke test | `pretrained_checkpoint`、`task_suite_name`、`use_proprio=True`、`num_images_in_input=2`、`use_pro_version=True`。 |
| 本地 LoRA checkpoint eval | step checkpoint 目录、action head 文件、proprio projector 文件、statistics、训练/评测 flags。 |
| policy server + fake client | `pretrained_checkpoint`、`unnorm_key`、payload 图像数量、state/proprio shape、server 返回 action shape。 |
| 自定义数据或机器人 | OXE registry、action/proprio 维度、statistics、projector、client action 后处理。 |

## 导航

- 上一节：[Checkpoint 组件加载](05-checkpoint-component-loading.md)
- 返回上级：[模型组件](../04-model.md)
- 下一节：[LoRA 微调训练](../05-training.md)
