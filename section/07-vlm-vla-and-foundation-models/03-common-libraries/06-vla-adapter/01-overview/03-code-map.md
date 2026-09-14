# 代码地图

目标：按数据、模型、训练、评测、部署和工具脚本定位 VLA-Adapter 的主要源码入口。

读 VLA-Adapter 源码时，可以先判断当前问题属于哪一层，再进入对应文件。下面按问题类型列出主线入口，每个文件只说明职责和适合查看的场景；具体训练、评测和部署流程会在后续页面展开。

## 数据与 RLDS / OXE

| 文件 | 什么时候看 | 负责什么 |
| --- | --- | --- |
| `prismatic/vla/datasets/datasets.py` | `dataset_name`、batch 字段或 wrist/proprio 输入不清楚 | 定义 `RLDSBatchTransform`、`RLDSDataset`，把 RLDS 样本转成模型训练 batch。 |
| `prismatic/vla/datasets/rlds/dataset.py` | TFDS / RLDS 读取、trajectory transform、interleaved dataset 行为异常 | 创建 single / interleaved RLDS dataset，并串起 trajectory / frame transforms。 |
| `prismatic/vla/datasets/rlds/oxe/configs.py` | 数据集 image keys、state keys、action encoding 不确定 | 维护 OXE dataset 配置和 `StateEncoding` / `ActionEncoding`。 |
| `prismatic/vla/datasets/rlds/oxe/mixtures.py` | `libero_spatial_no_noops` 等 mixture 名称需要确认 | 定义 OXE named mixtures。 |
| `prismatic/vla/datasets/rlds/oxe/materialize.py` | mixture 如何变成 per-dataset kwargs 和权重 | 提供 `get_oxe_dataset_kwargs_and_weights`。 |
| `prismatic/vla/datasets/rlds/oxe/transforms.py` | LIBERO、CALVIN、ALOHA 等数据字段如何标准化 | 定义各 dataset transform，包括 `libero_dataset_transform`、`calvin_dataset_transform`、`aloha_dataset_transform`。 |
| `prismatic/vla/datasets/rlds/traj_transforms.py` | action chunk、future action window 或 pad mask 异常 | 定义 trajectory 级别的 chunk / subsample / pad transforms。 |
| `prismatic/vla/datasets/rlds/obs_transforms.py` | 图像 decode、resize、augmentation 异常 | 定义 observation 级别图像处理。 |
| `prismatic/vla/datasets/rlds/utils/data_utils.py` | statistics 生成、normalization 或线程分配问题 | 定义 normalization、dataset statistics 读取和 `save_dataset_statistics`。 |
| `prismatic/vla/action_tokenizer.py` | action token 边界或 minivlm action token 行为需要核对 | 把连续动作映射到 tokenizer 可处理的 action token 表示。 |
| `prismatic/util/data_utils.py` | collator、padding、`pixel_values_wrist`、`actions`、`proprio` 组 batch 出错 | 定义 `PaddedCollatorForActionPrediction`。 |

## 模型组件与 backbone

| 文件 | 什么时候看 | 负责什么 |
| --- | --- | --- |
| `prismatic/vla/constants.py` | action / proprio / chunk 维度和平台识别需要确认 | 扫描整个 `sys.argv` 匹配 `libero`、`aloha`、`calvin`、`bridge`，选择 `ACTION_DIM`、`PROPRIO_DIM`、`NUM_ACTIONS_CHUNK`；未匹配时默认 LIBERO。 |
| `prismatic/models/action_heads.py` | L1 action head、Bridge Attention、Pro block、action chunk 输出异常 | 定义 `L1RegressionActionHead`、`MLPResNetBlock`、`MLPResNetBlock_Pro`；当前 `predict_action()` 会直接使用 `proprio` 和 `proprio_projector`。 |
| `prismatic/models/projectors.py` | proprio projector 或 diffusion noisy action projector shape 不匹配 | 定义 `ProprioProjector` 和 `NoisyActionProjector`。 |
| `prismatic/models/film_vit_wrapper.py` | `use_film=True` 或 vision backbone FiLM wrapper 相关问题 | 定义 FiLM vision wrapper。 |
| `prismatic/models/materialize.py` | backbone、tokenizer、VLM 如何由 config materialize | 创建 vision backbone、LLM backbone 和 VLM。 |
| `prismatic/models/load.py` | Prismatic / VLA model registry 加载路径不清楚 | 提供模型列表和 `load_vla`。 |
| `prismatic/models/backbones/vision/dinosiglip_vit.py` | DINO + SigLIP 视觉 backbone 或 image transform 需要核对 | 定义 DinoSigLIP vision backbone。 |
| `prismatic/models/backbones/llm/qwen25.py` | Qwen2.5 backbone、tokenizer 或 prompt builder 相关问题 | 定义 Qwen2.5 LLM backbone。 |
| `prismatic/models/vlms/prismatic.py` | Prismatic VLM 主体结构需要追踪 | 定义 Prismatic VLM 的训练与推理逻辑。 |
| `prismatic/models/vlas/openvla.py` | OpenVLA 风格 action prediction 模型需要追踪 | 定义 VLA 模型类。 |
| `prismatic/conf/models.py` | model id、vision / LLM backbone 配置来源不清楚 | 维护 model config registry。 |
| `prismatic/conf/vla.py` | VLA experiment config、Prismatic tiny VLM 配置名称需要确认 | 维护 VLA config registry。 |

## Hugging Face 入口与 processor

| 文件 | 什么时候看 | 负责什么 |
| --- | --- | --- |
| `prismatic/extern/hf/configuration_prismatic.py` | HF config 字段或 `AutoConfig` 注册问题 | 定义 `PrismaticConfig` / `OpenVLAConfig`。 |
| `prismatic/extern/hf/processing_prismatic.py` | processor、image processor、prompt processor 行为需要确认 | 定义 `PrismaticImageProcessor` 和 `PrismaticProcessor`。 |
| `prismatic/extern/hf/modeling_prismatic.py` | `predict_action()`、multi-image 输入、hidden states 或 `_unnormalize_actions()` 异常 | 定义 HF 版本的 Prismatic / OpenVLA action prediction 模型。 |
| `pretrained_models/configs/` | 本地 tiny Prismatic config / processor / tokenizer 文件是否完整 | 保存课程使用的 HF config、processor 和 tokenizer 文件。 |

## 训练与 checkpoint 保存

`vla-scripts/finetune.py` 是 LoRA 微调入口。它的核心配置类是 `FinetuneConfig`，负责把命令参数变成数据加载、模型构造、LoRA 注入、action head loss 和 checkpoint 保存。

| 文件或入口 | 什么时候看 | 负责什么 |
| --- | --- | --- |
| `vla-scripts/finetune.py::FinetuneConfig` | 训练命令参数、run 目录、LoRA、图像数量或 Pro flags 不清楚 | 定义 fine-tuning 参数。 |
| `vla-scripts/finetune.py::finetune` | 命令参数如何进入模型、数据和 optimizer | 串起 model、processor、LoRA、projector、action head、dataset、dataloader。 |
| `vla-scripts/finetune.py::run_forward_pass` | loss、action prediction 或 proprio 输入异常 | 组织 VLM forward、action head prediction 和 L1 loss。 |
| `vla-scripts/finetune.py::save_training_checkpoint` | eval 找不到组件文件 | 保存 LoRA / merged model、action head、proprio projector、dataset statistics。 |
| `vla-scripts/merge_lora_weights_and_save.py` | 需要离线合并 LoRA 权重 | 将 LoRA adapter 合并到 base model。 |
| `vla-scripts/train.py` | 查看原始训练脚本或 dataset statistics 保存逻辑 | 提供另一条训练入口，保留 Prismatic 训练流程。 |
| `prismatic/training/train_utils.py` | action token mask 或 token-level 训练工具需要确认 | 定义 action token mask 工具。 |
| `prismatic/training/materialize.py` | train strategy / FSDP 等训练策略来源不清楚 | 创建训练策略。 |

## checkpoint、statistics 与推理工具

| 文件 | 什么时候看 | 负责什么 |
| --- | --- | --- |
| `experiments/robot/openvla_utils.py` | eval / deploy 组件加载、HF Hub / 本地 checkpoint 差异、action 请求异常 | 提供 `get_vla`、`get_processor`、`get_action_head`、`get_proprio_projector`、`get_vla_action`。 |
| `experiments/robot/openvla_utils.py::find_checkpoint_file` | 本地 checkpoint 中组件文件名不确定 | 查找 `action_head`、`proprio_projector`、`vision_backbone` 等文件。 |
| `experiments/robot/openvla_utils.py::_load_dataset_stats` | `dataset_statistics.json` 没有加载进 `model.norm_stats` | 从 HF Hub 或本地 checkpoint 读取 statistics。 |
| `experiments/robot/openvla_utils.py::normalize_proprio` | proprio normalization 异常 | 使用 statistics 归一化 proprio。 |
| `experiments/robot/openvla_utils.py::prepare_images_for_vla` | 多图像输入或 image format 报错 | 检查、裁剪和组织 policy 输入图像。 |
| `experiments/robot/robot_utils.py` | LIBERO eval 中通用 action、gripper、HTTP client 工具需要确认 | 提供 `get_model`、`get_action`、gripper action 处理和 `MsgPackHttpClientPolicy`。 |

## LIBERO 评测

`experiments/robot/libero/run_libero_eval.py` 是 LIBERO 评测入口。它的核心配置类是 `GenerateConfig`，负责创建 LIBERO task suite、加载 checkpoint、执行 rollout、保存日志和视频。

| 文件或入口 | 什么时候看 | 负责什么 |
| --- | --- | --- |
| `experiments/robot/libero/run_libero_eval.py::GenerateConfig` | 评测参数、task suite、trial 数、open-loop 步数不清楚 | 定义 LIBERO eval 参数。 |
| `experiments/robot/libero/run_libero_eval.py::initialize_model` | action head 或 proprio projector 加载失败 | 加载模型、processor、action head、projector，并检查 `unnorm_key`。 |
| `experiments/robot/libero/run_libero_eval.py::prepare_observation` | observation 字段、图像或 proprio 组织异常 | 从 LIBERO obs 生成 policy 输入。 |
| `experiments/robot/libero/run_libero_eval.py::run_episode` | rollout、action queue、成功判定或视频保存异常 | 执行单个 episode。 |
| `experiments/robot/libero/run_libero_eval.py::run_task` | 单个 task 的多次 rollout 统计不清楚 | 聚合 task 内成功率。 |
| `experiments/robot/libero/libero_utils.py` | LIBERO env、图像读取、dummy action、视频保存问题 | 提供 LIBERO 环境与 rollout 工具函数。 |

## CALVIN 评测

| 文件 | 什么时候看 | 负责什么 |
| --- | --- | --- |
| `vla-scripts/evaluate_calvin.py` | CALVIN ABC->D 评测、sequence rollout 或 CALVIN checkpoint 加载 | 定义 CALVIN `GenerateConfig`、环境创建、rollout 和结果保存。 |
| `vla-scripts/vla_evaluation.py` | CALVIN dual-system evaluation action 生成细节需要追踪 | 定义 `DualSystemCalvinEvaluation`。 |
| `vla-scripts/calvin_env_wrapper.py` | CALVIN environment wrapper 行为不清楚 | 包装 CALVIN 环境 observation / info。 |

## 部署与 ALOHA client

这里有两套 `/act` server：`vla-scripts/deploy.py` 使用 JSON / `json_numpy`，`experiments/robot/server_deploy/deploy.py` 使用 MessagePack，并和 ALOHA fake / real client 的请求格式对应。

| 文件 | 什么时候看 | 负责什么 |
| --- | --- | --- |
| `vla-scripts/deploy.py` | 把 checkpoint 启动成 JSON / `json_numpy` HTTP policy server | 定义 `DeployConfig`、`OpenVLAServer` 和 JSON `/act` 接口。 |
| `experiments/robot/server_deploy/deploy.py` | ALOHA fake / real client 需要连接 MessagePack server | 定义 `VLAServer`，接收 `application/msgpack` 请求并返回 `{"actions": ...}`。 |
| `experiments/robot/aloha/run_fake_cobot_client.py` | 不接 ROS，验证 MessagePack server-client 通信和 action shape | 构造假图像、假 state 和 `/act` 请求。 |
| `experiments/robot/aloha/run_cobot_client.py` | 真实 ALOHA / Cobot Magic client 流程需要核对，或确认真机依赖是否齐全 | 读取 ROS topic、相机、joint state，并向 server 请求 action；当前 checkout 缺少 `experiments.robot.aloha.aloha_utils`，直接运行会先遇到导入依赖问题。 |
| `experiments/robot/aloha/eval_files/*.sh` | ALOHA server / client 命令模板需要参考 | 保存 deploy server、fake client、real client 的脚本入口。 |
| `experiments/robot/aloha/train_files/*.sh` | ALOHA 训练环境和本地 vision / LLM 文件准备需要参考 | 保存 ALOHA 训练相关脚本。 |

## 工具脚本与配置

| 文件 | 什么时候看 | 负责什么 |
| --- | --- | --- |
| `scripts/extern/verify_prismatic.py` | Prismatic checkpoint 转换或加载后需要验证 | 验证 Prismatic 权重。 |
| `scripts/extern/convert_prismatic_weights_to_hf.py` | Prismatic 权重需要转换为 HF 格式 | 转换 checkpoint 文件。 |
| `vla-scripts/extern/verify_openvla.py` | OpenVLA / VLA HF checkpoint 需要验证 | 验证 OpenVLA 格式权重。 |
| `vla-scripts/extern/convert_openvla_weights_to_hf.py` | OpenVLA 权重需要转换为 HF 格式 | 转换 OpenVLA checkpoint。 |
| `scripts/pretrain.py`、`scripts/preprocess.py`、`vla-scripts/train.py` | 追踪 Prismatic 原始训练、VLA 训练和预处理流程 | 保留基础 VLM / VLA 训练相关入口。 |
| `README.md` | 官方命令、checkpoint 列表、数据目录和 release 信息需要核对 | 提供 repo 级说明。 |

## 从现象反查入口

| 报错线索 | 优先关注哪里 |
| --- | --- |
| `dataset_name` 找不到 | `datasets.py`、`oxe/mixtures.py`、`oxe/configs.py` 和训练命令的 `data_root_dir`。 |
| batch 缺少 `pixel_values_wrist` 或 `proprio` | `RLDSBatchTransform`、`PaddedCollatorForActionPrediction`、`num_images_in_input`、`use_proprio`。 |
| action shape 不对 | `constants.py`、`action_heads.py`、当前命令是否触发正确 platform constants。 |
| checkpoint 组件缺失 | `openvla_utils.py::find_checkpoint_file`、checkpoint 目录里的 `action_head--...` / `proprio_projector--...`。 |
| `dataset_statistics.json` 没加载 | `openvla_utils.py::_load_dataset_stats`、checkpoint 目录或 HF Hub 文件。 |
| `unnorm_key` 不存在 | `experiments/robot/libero/run_libero_eval.py::check_unnorm_key`、`model.norm_stats`、训练数据名与评测 suite family。 |
| LIBERO task suite 不合法 | `experiments/robot/libero/run_libero_eval.py::TaskSuite` 和 `GenerateConfig.task_suite_name`。 |
| JSON policy server 返回 `error` | `vla-scripts/deploy.py::get_server_action`、client payload、`openvla_utils.py::get_vla_action`。 |
| MessagePack policy server 返回 415 / 500 | `experiments/robot/server_deploy/deploy.py::VLAServer.get_server_action`、`Content-Type`、client payload、`unnorm_key`。 |
| ALOHA client action shape 不对 | `experiments/robot/server_deploy/deploy.py`、`run_fake_cobot_client.py` / `run_cobot_client.py`、client payload、`unnorm_key`、`DeployConfig.num_images_in_input`、ALOHA constants。 |
| CALVIN 评测无法启动 | `evaluate_calvin.py`、`calvin_env_wrapper.py`、CALVIN dataset / env 路径。 |

## 本页小结

- 数据问题优先查 RLDS / OXE 入口；模型组件问题优先查 constants、action head、projector 和 HF modeling。
- 训练保存集中在 `vla-scripts/finetune.py`，评测加载集中在 `experiments/robot/libero/run_libero_eval.py` 和 `openvla_utils.py`。
- policy server 连通只能说明请求、响应和 action shape 正常；benchmark 成功率还取决于 rollout、checkpoint 组件和动作反归一化。

## 导航

- 上一节：[架构与组件](02-architecture-and-components.md)
- 返回上级：[认识 VLA-Adapter](../01-overview.md)
- 下一节：[学习路线图](04-roadmap.md)
