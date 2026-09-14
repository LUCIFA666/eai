# 代码地图

目标：按功能区定位 OpenVLA 官方仓库中的源码入口，知道推理、模型、数据、训练、评测、部署和工具脚本分别从哪里开始读。

本页按功能区整理 OpenVLA 官方仓库中的入口，分别对应 Hugging Face 接口、模型主体、动作 token、数据管线、训练、评测、部署和工具脚本。常见运行时入口主要分布在 HF 推理、模型主体、数据统计量、评测和部署相关文件；其余部分包含 OpenVLA 继承自 Prismatic 的通用入口。下面按仓库目录列出 Python 源码和脚本入口。包级 `__init__.py` 与 `prismatic/py.typed` 可在对应目录补查，依赖文件和 `LICENSE` 留给仓库根目录查看。

## 配置与模型注册

| 文件 | 常见入口 | 主要内容 |
| --- | --- | --- |
| `prismatic/conf/models.py` | Prismatic VLM model id、vision backbone 和 LLM backbone 配置。 | `ModelConfig`、`ModelRegistry`，以及不同 Prismatic VLM 变体的注册信息。 |
| `prismatic/conf/vla.py` | VLA experiment id、OpenX mixture 和训练超参数。 | `VLAConfig`、`VLARegistry`，以及 OpenVLA / Bridge / OXE 相关训练配置。 |
| `prismatic/conf/datasets.py` | Prismatic VLM 预训练和指令数据配置。 | LLaVA、LVIS4V、LRV 等数据配置注册。 |
| `prismatic/models/registry.py` | 预训练 VLM 名称和描述信息。 | `MODEL_REGISTRY`，用于把模型 id、别名、视觉表示、语言模型和训练数据对应起来。 |
| `prismatic/models/materialize.py` | 根据配置构建 vision backbone、LLM backbone 和 VLM。 | `get_vision_backbone_and_transform()`、`get_llm_backbone_and_tokenizer()`、`get_vlm()`。 |
| `prismatic/models/load.py` | 从 model id 或 checkpoint 加载 Prismatic / OpenVLA。 | `load()`、`load_vla()`，以及训练和推理加载路径；其中 `load_vla()` 的本地路径要求是 `checkpoints/*.pt`，不是顶层 run 目录。 |

## Hugging Face 接口

| 文件 | 常见入口 | 主要内容 |
| --- | --- | --- |
| `prismatic/extern/hf/configuration_prismatic.py` | HF `config.json`、`model_type` 和 `norm_stats` 字段。 | `PrismaticConfig`、`OpenVLAConfig`，定义 Hugging Face AutoClass 使用的配置结构。 |
| `prismatic/extern/hf/processing_prismatic.py` | `AutoProcessor`、图像输入和 padding。 | `PrismaticImageProcessor`、`PrismaticProcessor`，负责把图像和文本组织成模型输入。 |
| `prismatic/extern/hf/modeling_prismatic.py` | `AutoModelForVision2Seq`、`predict_action()` 和动作反归一化。 | HF 版 Prismatic / OpenVLA 模型，包含 vision encoder、projector、LLM 生成和 action decode。 |

最小推理通常先经过这一组文件。使用 `AutoModelForVision2Seq.from_pretrained(...)` 加载 `openvla/openvla-7b` 时，动作预测主要落在 `OpenVLAForActionPrediction.predict_action()`。如果要查 prompt 模板或 `v01` 与主线 checkpoint 的 prompt 分支，优先看 `vla-scripts/deploy.py`、`experiments/robot/openvla_utils.py` 和 `vla-scripts/extern/verify_openvla.py`。

## VLM 与 VLA 主体

| 文件 | 常见入口 | 主要内容 |
| --- | --- | --- |
| `prismatic/models/vlms/base_vlm.py` | VLM 抽象接口和生成接口约定。 | `VLM` 基类，定义 forward、generate、prompt builder 等通用接口。 |
| `prismatic/models/vlms/prismatic.py` | Prismatic VLM 主体结构。 | 连接 vision backbone、projector 和 LLM，处理图像特征进入语言模型的流程。 |
| `prismatic/models/vlas/openvla.py` | Prismatic 训练路径里的 OpenVLA 类。 | 继承 `PrismaticVLM`，补上 action tokenizer、动作生成和反归一化。 |
| `prismatic/vla/action_tokenizer.py` | action token 边界、bin 数和 token id 映射。 | `ActionTokenizer`，负责连续动作和 action tokens 之间的转换。 |
| `prismatic/vla/materialize.py` | VLA 数据集、action tokenizer 和 collator 的组装。 | `get_vla_dataset_and_collator()`，把 RLDS 数据、prompt、图像变换和 action tokenizer 接到训练入口。 |

动作维度、token 数量和动作尺度问题通常分布在 `prismatic/vla/action_tokenizer.py`、`prismatic/extern/hf/modeling_prismatic.py` 和 `prismatic/models/vlas/openvla.py`。模型结构问题继续落在 `prismatic/models/vlms/prismatic.py`、各 backbone 文件和 config 文件。

## Backbone 与 prompt

| 文件 | 常见入口 | 主要内容 |
| --- | --- | --- |
| `prismatic/models/backbones/vision/base_vision.py` | 视觉 backbone 抽象类、图像变换和 letterbox padding。 | `VisionBackbone`、`TimmViTBackbone`、`LetterboxPad`。 |
| `prismatic/models/backbones/vision/clip_vit.py` | CLIP ViT 视觉编码器。 | `CLIPViTBackbone`。 |
| `prismatic/models/backbones/vision/dinov2_vit.py` | DINOv2 ViT 视觉编码器。 | `DinoV2ViTBackbone`。 |
| `prismatic/models/backbones/vision/siglip_vit.py` | SigLIP 视觉编码器。 | `SigLIPViTBackbone`。 |
| `prismatic/models/backbones/vision/in1k_vit.py` | ImageNet 预训练 ViT 视觉编码器。 | `IN1KViTBackbone`。 |
| `prismatic/models/backbones/vision/dinoclip_vit.py` | DINOv2 + CLIP 融合视觉编码器。 | `DinoCLIPImageTransform`、`DinoCLIPViTBackbone`。 |
| `prismatic/models/backbones/vision/dinosiglip_vit.py` | DINOv2 + SigLIP 融合视觉编码器。 | `DinoSigLIPImageTransform`、`DinoSigLIPViTBackbone`。 |
| `prismatic/models/backbones/llm/base_llm.py` | LLM backbone 抽象类和 HF causal LM 封装。 | `LLMBackbone`、`HFCausalLLMBackbone`，定义 tokenizer、embedding、generation 接口。 |
| `prismatic/models/backbones/llm/llama2.py` | Llama 2 / Vicuna 系列语言模型。 | `LLaMa2LLMBackbone`。 |
| `prismatic/models/backbones/llm/mistral.py` | Mistral 系列语言模型。 | `MistralLLMBackbone`。 |
| `prismatic/models/backbones/llm/phi.py` | Phi 系列语言模型。 | `PhiLLMBackbone`。 |
| `prismatic/models/backbones/llm/prompting/base_prompter.py` | prompt builder 抽象接口。 | `PromptBuilder`、`PurePromptBuilder`。 |
| `prismatic/models/backbones/llm/prompting/llama2_chat_prompter.py` | Llama 2 chat prompt。 | `LLaMa2ChatPromptBuilder` 和 system prompt 格式化。 |
| `prismatic/models/backbones/llm/prompting/mistral_instruct_prompter.py` | Mistral instruct prompt。 | `MistralInstructPromptBuilder`。 |
| `prismatic/models/backbones/llm/prompting/phi_prompter.py` | Phi prompt。 | `PhiPromptBuilder`。 |
| `prismatic/models/backbones/llm/prompting/vicuna_v15_prompter.py` | Vicuna v1.5 chat prompt。 | `VicunaV15ChatPromptBuilder`。 |

## RLDS / OXE 数据管线

| 文件 | 常见入口 | 主要内容 |
| --- | --- | --- |
| `prismatic/vla/datasets/datasets.py` | batch 字段、prompt 构造和 RLDS batch transform。 | `RLDSBatchTransform`、`RLDSDataset`、`EpisodicRLDSDataset`、`DummyDataset`。 |
| `prismatic/vla/datasets/rlds/dataset.py` | RLDS / TFDS 读取、trajectory transform、frame transform 和 interleaving。 | `make_single_dataset()`、`make_interleaved_dataset()`，以及 dataset / frame 级 transform 调度。 |
| `prismatic/vla/datasets/rlds/obs_transforms.py` | 图像 decode、resize 和 augmentation。 | `decode_and_resize()`、`augment()`。 |
| `prismatic/vla/datasets/rlds/traj_transforms.py` | trajectory 级窗口、subsample 和 padding mask。 | `chunk_act_obs()`、`subsample()`、`add_pad_mask_dict()`。 |
| `prismatic/vla/datasets/rlds/oxe/configs.py` | OXE dataset 字段、state encoding 和 action encoding。 | `StateEncoding`、`ActionEncoding`，以及数据集字段配置。 |
| `prismatic/vla/datasets/rlds/oxe/materialize.py` | OXE dataset kwargs 和 mixture 权重。 | `make_oxe_dataset_kwargs()`、`get_oxe_dataset_kwargs_and_weights()`。 |
| `prismatic/vla/datasets/rlds/oxe/mixtures.py` | `oxe_magic_soup_plus` 等 mixture 名称。 | OXE mixture 列表和数据集权重。 |
| `prismatic/vla/datasets/rlds/oxe/transforms.py` | 不同 OXE 数据集的字段标准化。 | Bridge、RT-1、DROID、LIBERO 等数据集 transform。 |
| `prismatic/vla/datasets/rlds/oxe/utils/droid_utils.py` | DROID action 和 wrist / base 坐标转换。 | DROID rotation、velocity、image swap 和 finetuning transform 工具。 |
| `prismatic/vla/datasets/rlds/utils/data_utils.py` | `dataset_statistics.json`、normalization、gripper 和 statistics 保存。 | `NormalizationType`、`normalize_action_and_proprio()`、`get_dataset_statistics()`、`save_dataset_statistics()`。 |
| `prismatic/vla/datasets/rlds/utils/goal_relabeling.py` | goal relabeling。 | `uniform()`。 |
| `prismatic/vla/datasets/rlds/utils/task_augmentation.py` | task conditioning augmentation。 | `delete_task_conditioning()`。 |

`unnorm_key` 对应训练或微调时保存的某组数据统计量。动作尺度异常通常分成两类入口：模型侧看 `predict_action` 的反归一化逻辑，数据侧看 `unnorm_key` 对应的统计量。

## 训练与日志

| 文件 | 常见入口 | 主要内容 |
| --- | --- | --- |
| `vla-scripts/train.py` | 原生 VLA 训练、FSDP、resume 和 `VLAConfig`。 | `TrainConfig`、`train()`，从 Prismatic VLM 出发训练 OpenVLA。 |
| `vla-scripts/finetune.py` | LoRA 微调、dataset name、batch、学习率和 checkpoint 保存。 | `FinetuneConfig`、`finetune()`，通过 HF AutoClass 加载 OpenVLA 并注入 LoRA。 |
| `prismatic/training/materialize.py` | DDP / FSDP strategy 选择。 | `get_train_strategy()`。 |
| `prismatic/training/metrics.py` | JSONL / W&B 日志和 VLA 训练指标。 | `Metrics`、`VLAMetrics`、`JSONLinesTracker`、`WeightsBiasesTracker`。 |
| `prismatic/training/strategies/base_strategy.py` | 训练策略抽象类。 | `TrainingStrategy`，定义 setup、clip、save、run 等训练接口。 |
| `prismatic/training/strategies/ddp.py` | DDP 训练策略。 | `DDPStrategy`。 |
| `prismatic/training/strategies/fsdp.py` | FSDP 训练策略、checkpoint 和分布式保存。 | `FSDPStrategy`。 |

## 评测与部署

| 文件 | 常见入口 | 主要内容 |
| --- | --- | --- |
| `experiments/robot/openvla_utils.py` | eval 中 OpenVLA 加载、processor、center crop 和 action 调用。 | `get_vla()`、`get_processor()`、`crop_and_resize()`、`get_vla_action()`。 |
| `experiments/robot/robot_utils.py` | eval 通用模型加载、action 调用和 gripper 后处理。 | `get_model()`、`get_action()`、`normalize_gripper_action()`、`invert_gripper_action()`。 |
| `experiments/robot/libero/run_libero_eval.py` | LIBERO checkpoint 评测、`center_crop`、`task_suite_name` 和 `unnorm_key`。 | `GenerateConfig`、`eval_libero()`，执行 LIBERO rollout 并记录成功率。 |
| `experiments/robot/libero/libero_utils.py` | LIBERO env、图像读取、视频保存和姿态转换。 | `get_libero_env()`、`get_libero_image()`、`save_rollout_video()`、`quat2axisangle()`。 |
| `experiments/robot/libero/regenerate_libero_dataset.py` | LIBERO 数据重生成和 no-op action 过滤。 | `is_noop()`、`main()`。 |
| `experiments/robot/bridge/run_bridgev2_eval.py` | BridgeData V2 WidowX 评测。 | `GenerateConfig`、`eval_model_in_bridge_env()`。 |
| `experiments/robot/bridge/bridgev2_utils.py` | WidowX 环境参数、图像预处理、rollout 保存。 | `get_widowx_env()`、`get_preprocessed_image()`、`save_rollout_video()`、`save_rollout_data()`。 |
| `experiments/robot/bridge/widowx_env.py` | WidowX Gym 环境封装。 | `WidowXGym`、obs 转换和机器人状态转换。 |
| `vla-scripts/deploy.py` | REST policy server、`/act` payload 和本地 checkpoint statistics 加载。 | `OpenVLAServer`、`DeployConfig`、`deploy()`。 |

评测脚本负责 rollout，部署脚本负责 HTTP 接口。server 能返回 action，说明请求、processor、模型和返回格式正常；benchmark 成功率还要看环境中的闭环执行。

## 脚本、预处理与转换

| 文件 | 常见入口 | 主要内容 |
| --- | --- | --- |
| `scripts/pretrain.py` | Prismatic VLM 预训练。 | `PretrainConfig`、`pretrain()`，处理 VLM 训练配置、数据和 checkpoint。 |
| `scripts/preprocess.py` | Prismatic VLM 预处理数据。 | `PreprocessConfig`、`preprocess()`。 |
| `scripts/generate.py` | Prismatic VLM 文本生成检查。 | `GenerateConfig`、`generate()`。 |
| `scripts/extern/convert_prismatic_weights_to_hf.py` | Prismatic 权重转 Hugging Face 格式。 | `HFConvertConfig`、`convert_prismatic_weights_to_hf()`、state dict remap。 |
| `scripts/extern/verify_prismatic.py` | Prismatic HF 转换验证。 | `verify_prismatic()`。 |
| `vla-scripts/extern/convert_openvla_weights_to_hf.py` | OpenVLA 权重转 Hugging Face 格式。 | `HFConvertConfig`、`convert_openvla_weights_to_hf()`、state dict remap。 |
| `vla-scripts/extern/verify_openvla.py` | OpenVLA HF 转换验证。 | `get_openvla_prompt()`、`verify_openvla()`。 |
| `scripts/additional-datasets/lrv_instruct.py` | LRV-Instruct 数据构建。 | `build_lrv_instruct()`。 |
| `scripts/additional-datasets/lvis_instruct_4v.py` | LVIS-Instruct-4V 数据构建。 | `build_lvis_instruct_4v()`。 |
| `prismatic/preprocessing/download.py` | 数据下载、解压和图片格式转换。 | `download_extract()`、`download_with_progress()`、`extract_with_progress()`、`convert_to_jpg()`。 |
| `prismatic/preprocessing/materialize.py` | 预训练数据集和 collator 组装。 | `get_dataset_and_collator()`。 |
| `prismatic/preprocessing/datasets/datasets.py` | Prismatic VLM 对齐和微调数据集。 | `AlignDataset`、`FinetuneDataset`。 |

## 通用工具

| 文件 | 常见入口 | 主要内容 |
| --- | --- | --- |
| `prismatic/util/data_utils.py` | padding collator、tree map 和 action prediction batch。 | `PaddedCollatorForLanguageModeling`、`PaddedCollatorForActionPrediction`。 |
| `prismatic/util/batching_utils.py` | 多模态 batch sampler。 | `SplitModalitySampler`。 |
| `prismatic/util/nn_utils.py` | projector 模块。 | `LinearProjector`、`MLPProjector`、`FusedMLPProjector`。 |
| `prismatic/util/torch_utils.py` | seed、worker init 和 BF16 支持检查。 | `set_global_seed()`、`check_bloat16_supported()`。 |
| `prismatic/overwatch/overwatch.py` | 分布式日志封装。 | `DistributedOverwatch`、`PureOverwatch`、`initialize_overwatch()`。 |

## 从现象反查入口

| 现象 | 起始文件 |
| --- | --- |
| HF `AutoProcessor` 或图像输入异常 | `prismatic/extern/hf/processing_prismatic.py` |
| HF `AutoModelForVision2Seq` 加载异常 | `prismatic/extern/hf/configuration_prismatic.py`、`prismatic/extern/hf/modeling_prismatic.py` |
| `predict_action` 缺失或 action 维度异常 | `prismatic/extern/hf/modeling_prismatic.py`、`prismatic/vla/action_tokenizer.py` |
| `unnorm_key` 报错或动作尺度明显偏掉 | `prismatic/extern/hf/modeling_prismatic.py`、`prismatic/vla/datasets/rlds/utils/data_utils.py` |
| action token bin、token id 或动作离散化问题 | `prismatic/vla/action_tokenizer.py` |
| model id、backbone id 或 checkpoint 加载问题 | `prismatic/conf/models.py`、`prismatic/models/materialize.py`、`prismatic/models/load.py` |
| VLA experiment id 或 OXE mixture 选择问题 | `prismatic/conf/vla.py`、`prismatic/vla/datasets/rlds/oxe/mixtures.py` |
| RLDS 读取、interleaving 或数据统计量问题 | `prismatic/vla/datasets/rlds/dataset.py`、`prismatic/vla/datasets/rlds/utils/data_utils.py` |
| OXE 字段映射或 dataset transform 问题 | `prismatic/vla/datasets/rlds/oxe/configs.py`、`prismatic/vla/datasets/rlds/oxe/transforms.py` |
| LoRA checkpoint 或 `dataset_statistics.json` 保存问题 | `vla-scripts/finetune.py`、`prismatic/vla/datasets/rlds/utils/data_utils.py` |
| FSDP 训练、resume 或 checkpoint 保存问题 | `vla-scripts/train.py`、`prismatic/training/strategies/fsdp.py` |
| LIBERO rollout、`center_crop` 或 suite 参数问题 | `experiments/robot/libero/run_libero_eval.py`、`experiments/robot/openvla_utils.py` |
| Bridge WidowX 评测或图像预处理问题 | `experiments/robot/bridge/run_bridgev2_eval.py`、`experiments/robot/bridge/bridgev2_utils.py` |
| REST server payload 或 `/act` 返回异常 | `vla-scripts/deploy.py` |
| OpenVLA 权重转换或 HF 格式验证问题 | `vla-scripts/extern/convert_openvla_weights_to_hf.py`、`vla-scripts/extern/verify_openvla.py` |
| Prismatic 预训练数据或 VLM 生成检查问题 | `scripts/preprocess.py`、`scripts/pretrain.py`、`scripts/generate.py` |

## 导航

- 上一节：[架构与推理主线](02-architecture-and-inference.md)
- 返回上级：[认识 OpenVLA](../01-overview.md)
- 下一节：[阅读顺序](04-reading-order.md)
