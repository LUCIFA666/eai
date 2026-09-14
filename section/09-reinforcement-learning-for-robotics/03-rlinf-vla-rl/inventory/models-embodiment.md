# RLINF 文件索引：models-embodiment

覆盖 `models-embodiment` 分组，共 `109` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/models/embodiment/__init__.py` | 13 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | - | - |
| `rlinf/models/embodiment/base_policy.py` | 107 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | ForwardType, BasePolicy | - | abc, enum |
| `rlinf/models/embodiment/cnn_policy/__init__.py` | 26 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | omegaconf, torch |
| `rlinf/models/embodiment/cnn_policy/cnn_policy.py` | 623 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | CNNConfig, CNNPolicy | - | dataclasses, numpy, os, rlinf, torch, typing |
| `rlinf/models/embodiment/dexbotic_dm0/__init__.py` | 171 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | glob, omegaconf, os |
| `rlinf/models/embodiment/dexbotic_dm0/dm0_policy.py` | 806 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | DexboticDM0ForRLActionPrediction | - | PIL, dexbotic, json, numpy, os, random, rlinf, torch |
| `rlinf/models/embodiment/dexbotic_pi/__init__.py` | 120 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | glob, omegaconf, os |
| `rlinf/models/embodiment/dexbotic_pi/dexbotic_pi_policy.py` | 941 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | DexboticPi0ForRLActionPrediction | - | PIL, dexbotic, json, numpy, os, random, rlinf, torch |
| `rlinf/models/embodiment/dreamzero/__init__.py` | 190 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | _promote_scalar_params_to_1d, get_model | groot, hydra, json, omegaconf, pathlib, rlinf, safetensors, torch |
| `rlinf/models/embodiment/dreamzero/dreamzero_policy.py` | 365 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | DreamZeroConfig, DreamZeroPolicy | - | cv2, dataclasses, groot, logging, numpy, rlinf, tianshou, torch |
| `rlinf/models/embodiment/dreamzero/patch/__init__.py` | 29 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | - | rlinf |
| `rlinf/models/embodiment/dreamzero/patch/dreamzero_cotrain.py` | 174 | 具身/VLA 模型、动作模型和策略网络；训练流程入口 | DreamTransform | collate | ast, einops, groot, numpy, torch |
| `rlinf/models/embodiment/dreamzero/patch/wan_causal_model_forward_train.py` | 185 | 具身/VLA 模型、动作模型和策略网络；训练流程入口 | - | _forward_train | groot, torch |
| `rlinf/models/embodiment/dreamzero/patch/wan_video_vae.py` | 397 | 具身/VLA 模型、动作模型和策略网络 | WanVideoVAE, WanVideoVAEStateDictConverter, WanVideoVAE38 | - | __future__, einops, groot, torch, tqdm |
| `rlinf/models/embodiment/flow_policy/__init__.py` | 51 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | omegaconf, torch |
| `rlinf/models/embodiment/flow_policy/flow_policy.py` | 633 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | FlowConfig, FlowPolicy, FlowStateConfig, FlowStatePolicy | - | dataclasses, os, rlinf, torch, typing |
| `rlinf/models/embodiment/gr00t/__init__.py` | 82 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | omegaconf, torch |
| `rlinf/models/embodiment/gr00t/embodiment_tags.py` | 59 | 具身/VLA 模型、动作模型和策略网络 | EmbodimentTag | - | enum |
| `rlinf/models/embodiment/gr00t/gr00t_action_model.py` | 732 | 具身/VLA 模型、动作模型和策略网络 | FlowMatchingActionHeadForRLActionPrediction, GR00T_N1_5_ForRLActionPrediction | - | gr00t, json, numpy, pathlib, random, rlinf, torch, transformers |
| `rlinf/models/embodiment/gr00t/modality_config.py` | 177 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义 | ManiskillWidowXDataConfig, LiberoFrankaDataConfig | - | gr00t |
| `rlinf/models/embodiment/gr00t/simulation_io.py` | 198 | 具身/VLA 模型、动作模型和策略网络 | - | convert_libero_obs_to_gr00t_format, convert_maniskill_obs_to_gr00t_format, convert_to_libero_action, convert_to_maniskill_action, convert_to_isaaclab_stack_cube_action, cut_and_resize_images, normalize_gripper_action | numpy, torch |
| `rlinf/models/embodiment/gr00t/utils.py` | 127 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | encode_phrases_to_2d_tensor, decode_2d_tensor_to_phrases, hash_array_or_tensor, replace_dropout_with_identity, unsqueeze_dict_values, squeeze_dict_values | hashlib, numpy, torch, typing |
| `rlinf/models/embodiment/lingbotvla/__init__.py` | 65 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | omegaconf, os, torch |
| `rlinf/models/embodiment/lingbotvla/lingbotvla_action_model.py` | 955 | 具身/VLA 模型、动作模型和策略网络 | Observation, LingbotvlaActionModel | - | dataclasses, json, lingbotvla, math, numpy, os, random, rlinf |
| `rlinf/models/embodiment/lingbotvla/sft_builder.py` | 87 | 具身/VLA 模型、动作模型和策略网络 | LingbotDataConfig | build_lingbot_sft_dataloader | dataclasses, lerobot, os, rlinf, torch, transformers, typing |
| `rlinf/models/embodiment/mlp_policy/__init__.py` | 44 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | omegaconf, torch |
| `rlinf/models/embodiment/mlp_policy/iql_mlp_policy.py` | 252 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | IQLMLPPolicy | - | math, rlinf, torch |
| `rlinf/models/embodiment/mlp_policy/mlp_policy.py` | 429 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | MLPPolicy | - | numpy, rlinf, torch |
| `rlinf/models/embodiment/modules/__init__.py` | 13 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | - | - |
| `rlinf/models/embodiment/modules/batch_renorm.py` | 132 | 具身/VLA 模型、动作模型和策略网络 | BatchRenorm, placeholder | make_batchrenorm | torch |
| `rlinf/models/embodiment/modules/compact_encoders.py` | 356 | 具身/VLA 模型、动作模型和策略网络 | LightweightImageEncoder64, LightweightImageEncoder, CompactStateEncoder, CompactQHead, CompactMultiQHead | - | math, torch |
| `rlinf/models/embodiment/modules/entropy_tunning.py` | 69 | 具身/VLA 模型、动作模型和策略网络 | EntropyTemperature | - | numpy, torch |
| `rlinf/models/embodiment/modules/explore_noise_net.py` | 168 | 具身/VLA 模型、动作模型和策略网络 | ExploreNoiseNet, MLP | - | collections, rlinf, torch |
| `rlinf/models/embodiment/modules/flow_actor.py` | 469 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | FlowTActor, JaxFlowTActor | - | batch_renorm, torch |
| `rlinf/models/embodiment/modules/gaussian_policy.py` | 317 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | TanhTransform, SquashedNormal, GaussianPolicy | - | torch |
| `rlinf/models/embodiment/modules/mlp.py` | 95 | 具身/VLA 模型、动作模型和策略网络 | MLP | - | collections, torch |
| `rlinf/models/embodiment/modules/q_head.py` | 328 | 具身/VLA 模型、动作模型和策略网络 | QHead, MultiQHead, CrossQHead, MultiCrossQHead | - | batch_renorm, torch, utils |
| `rlinf/models/embodiment/modules/resnet_utils.py` | 158 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | MyGroupNorm, ResNet10, SpatialLearnedEmbeddings, ResNetEncoder | - | functools, torch, torchvision, utils |
| `rlinf/models/embodiment/modules/utils.py` | 65 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | layer_init, get_act_func, make_mlp, init_mlp_weights | numpy, torch |
| `rlinf/models/embodiment/modules/value_head.py` | 67 | 具身/VLA 模型、动作模型和策略网络 | ValueHead | - | torch |
| `rlinf/models/embodiment/openpi/__init__.py` | 126 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | omegaconf, os, torch |
| `rlinf/models/embodiment/openpi/dataconfig/__init__.py` | 477 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | _override_with_model_path, _override_with_data_kwargs, get_openpi_config | dataclasses, difflib, openpi, rlinf, typing |
| `rlinf/models/embodiment/openpi/dataconfig/behavior_dataconfig.py` | 112 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | LeRobotBehaviorDataConfig | - | dataclasses, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/calvin_dataconfig.py` | 71 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | LeRobotCalvinDataConfig | - | dataclasses, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/franka_co_training_dataconfig.py` | 99 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；训练流程入口；数据读取/组织 | LeRobotFrankaEEDataConfig | - | dataclasses, numpy, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/franka_dataconfig.py` | 101 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | CustomDataConfig | - | dataclasses, numpy, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/gsenv_dataconfig.py` | 58 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；环境适配；数据读取/组织 | LeRobotGSEnvDataConfig | - | dataclasses, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/isaaclab_dataconfig.py` | 65 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | LeRobotIsaacLabStackCubeDataConfig | - | dataclasses, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/libero_dataconfig.py` | 102 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | LeRobotLiberoDataConfig | - | dataclasses, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/maniskill_dataconfig.py` | 103 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | LeRobotManiSkillDataConfig | - | dataclasses, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/metaworld_dataconfig.py` | 68 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | LeRobotMetaworldDataConfig | - | dataclasses, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/realworld_dataconfig.py` | 80 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | LeRobotRealworldDataConfig | - | dataclasses, numpy, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/robocasa_dataconfig.py` | 99 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | LeRobotRobocasaDataConfig | - | dataclasses, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/dataconfig/robotwin_aloha_dataconfig.py` | 106 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义；数据读取/组织 | LeRobotAlohaDataConfig | - | dataclasses, numpy, openpi, pathlib, rlinf, typing_extensions |
| `rlinf/models/embodiment/openpi/openpi_action_model.py` | 1367 | 具身/VLA 模型、动作模型和策略网络 | OpenPi0Config, OpenPi0ForRLActionPrediction | _to_numpy | collections, dataclasses, math, numpy, openpi, random, rlinf, torch |
| `rlinf/models/embodiment/openpi/policies/__init__.py` | 13 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | - | - |
| `rlinf/models/embodiment/openpi/policies/aloha_policy.py` | 241 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | AlohaInputs, AlohaOutputs | make_aloha_example, _joint_flip_mask, _normalize, _unnormalize, _gripper_to_angular, _gripper_from_angular, _gripper_from_angular_inv, convert_image, _decode_aloha, _decode_state | dataclasses, einops, numpy, openpi, typing |
| `rlinf/models/embodiment/openpi/policies/behavior_policy.py` | 165 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | BehaviorInputs, BehaviorOutputs | make_behavior_example, extract_state_from_proprio, _parse_image | dataclasses, einops, numpy, openpi |
| `rlinf/models/embodiment/openpi/policies/calvin_policy.py` | 87 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | CalvinInputs, CalvinOutputs | make_calvin_example, _parse_image | dataclasses, einops, numpy, openpi |
| `rlinf/models/embodiment/openpi/policies/franka_policy.py` | 127 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | FrankaEEOutputs, FrankaEEInputs | make_franka_example, _parse_image | dataclasses, einops, numpy, openpi, torch |
| `rlinf/models/embodiment/openpi/policies/gsenv_policy.py` | 74 | 具身/VLA 模型、动作模型和策略网络；环境适配；策略/actor 逻辑 | GSEnvInputs, GSEnvOutputs | make_gsenv_example, _parse_image | dataclasses, einops, numpy, openpi |
| `rlinf/models/embodiment/openpi/policies/isaaclab_policy.py` | 84 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | IsaacLabInputs, IsaacLabOutputs | make_isaaclab_example, _parse_image | dataclasses, einops, numpy, openpi |
| `rlinf/models/embodiment/openpi/policies/libero_policy.py` | 118 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | LiberoInputs, LiberoOutputs | make_libero_example, _parse_image | dataclasses, einops, numpy, openpi |
| `rlinf/models/embodiment/openpi/policies/maniskill_policy.py` | 114 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | ManiSkillInputs, ManiSkillOutputs | make_maniskill_example, _parse_image | dataclasses, einops, numpy, openpi |
| `rlinf/models/embodiment/openpi/policies/metaworld_policy.py` | 75 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | MetaworldInputs, MetaworldOutputs | make_metaworld_example, _parse_image | dataclasses, einops, numpy, openpi |
| `rlinf/models/embodiment/openpi/policies/realworld_policy.py` | 112 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | RealworldOutputs, RealworldInputs | make_realworld_example, _parse_image | dataclasses, einops, numpy, openpi, torch |
| `rlinf/models/embodiment/openpi/policies/robocasa_policy.py` | 227 | 具身/VLA 模型、动作模型和策略网络；策略/actor 逻辑 | RobocasaInputs, RobocasaOutputs | make_robocasa_example, _parse_image, extract_state_dict, extract_image_dict, extract_action_ids, extract_action_dict | dataclasses, einops, logging, numpy, openpi, typing_extensions |
| `rlinf/models/embodiment/openpi_cfg/__init__.py` | 100 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | omegaconf, os, torch |
| `rlinf/models/embodiment/openpi_cfg/openpi_cfg_action_model.py` | 909 | 具身/VLA 模型、动作模型和策略网络 | Observation, OpenPi0Config, OpenPi0ForCFGActionPrediction | compute_cfg_routing_masks | collections, dataclasses, flax, numpy, openpi, rlinf, torch, typing |
| `rlinf/models/embodiment/openvla/__init__.py` | 104 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model_config_and_input_processor, get_model | json, omegaconf, os, torch, transformers |
| `rlinf/models/embodiment/openvla/openvla_action_model.py` | 810 | 具身/VLA 模型、动作模型和策略网络；环境适配 | OpenVLAForBatchActionPrediction, PrismaticImageProcessor, PrismaticProcessor, VLALogitsProcessor, OpenVLAForRLActionPrediction | - | numpy, prismatic, rlinf, torch, torchvision, transformers, typing |
| `rlinf/models/embodiment/openvla_oft/__init__.py` | 32 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | omegaconf, torch |
| `rlinf/models/embodiment/openvla_oft/official/__init__.py` | 118 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | omegaconf, torch |
| `rlinf/models/embodiment/openvla_oft/official/openvla_oft_action_model.py` | 705 | 具身/VLA 模型、动作模型和策略网络；环境适配 | OpenVLAOFTRLConfig, OpenVLAOFTForRLActionPrediction | - | PIL, numpy, prismatic, rlinf, torch, transformers, typing |
| `rlinf/models/embodiment/openvla_oft/openvla_utils.py` | 193 | 具身/VLA 模型、动作模型和策略网络；环境适配；公共入口/工具 | - | normalize_proprio, find_checkpoint_file, load_component_state_dict, apply_film_to_vla, load_dataset_stats | json, numpy, omegaconf, os, prismatic, torch, typing |
| `rlinf/models/embodiment/openvla_oft/rlinf/__init__.py` | 109 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model_config_and_input_processor, get_model | json, omegaconf, os, torch, transformers |
| `rlinf/models/embodiment/openvla_oft/rlinf/openvla_oft_action_model.py` | 576 | 具身/VLA 模型、动作模型和策略网络；环境适配 | OpenVLAOFTForRLActionPrediction | - | numpy, prismatic, rlinf, torch, transformers, typing |
| `rlinf/models/embodiment/prismatic/__init__.py` | 13 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | - | - |
| `rlinf/models/embodiment/prismatic/processing_prismatic.py` | 243 | 具身/VLA 模型、动作模型和策略网络 | PrismaticImageProcessor, PrismaticProcessor, MultiInputPrismaticProcessor | - | PIL, prismatic, torch, torchvision, transformers, typing |
| `rlinf/models/embodiment/reward/__init__.py` | 44 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_reward_model_class | rlinf |
| `rlinf/models/embodiment/reward/base_image_reward_model.py` | 145 | 具身/VLA 模型、动作模型和策略网络；奖励计算或奖励模型 | BaseImageRewardModel | - | abc, omegaconf, rlinf, torch, typing |
| `rlinf/models/embodiment/reward/base_reward_model.py` | 89 | 具身/VLA 模型、动作模型和策略网络；奖励计算或奖励模型 | BaseRewardModel | - | abc, omegaconf, torch, typing |
| `rlinf/models/embodiment/reward/resnet_reward_model.py` | 248 | 具身/VLA 模型、动作模型和策略网络；奖励计算或奖励模型 | ResNetRewardModel | - | numpy, omegaconf, rlinf, torch, torchvision, typing |
| `rlinf/models/embodiment/reward/vlm_reward_model.py` | 335 | 具身/VLA 模型、动作模型和策略网络；奖励计算或奖励模型 | VLMRewardModel, HistoryVLMRewardModel | - | __future__, numpy, omegaconf, os, peft, rlinf, torch, transformers |
| `rlinf/models/embodiment/reward/vlm_reward_utils/__init__.py` | 13 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | - | - |
| `rlinf/models/embodiment/reward/vlm_reward_utils/input_builder.py` | 320 | 具身/VLA 模型、动作模型和策略网络 | BaseInputBuilder, BaseVLMInputBuilder, HistoryVLMInputBuilder, VideoVLMInputBuilder, QwentrendInputBuilder | _to_pil_images, extract_images, register_input_builder, get_input_builder | PIL, dataclasses, logging, rlinf, torch, transformers, typing |
| `rlinf/models/embodiment/reward/vlm_reward_utils/reward_parser.py` | 144 | 具身/VLA 模型、动作模型和策略网络；奖励计算或奖励模型 | BaseRewardParser, QwentrendRewardParser | register_reward_parser, get_reward_parser, _extract_json_object, _parse_qwentrend_output | json, logging, re, torch, typing |
| `rlinf/models/embodiment/starvla/__init__.py` | 117 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | get_model | __future__, omegaconf, os, rlinf, starvla_action_model, torch, utils |
| `rlinf/models/embodiment/starvla/action_heads/__init__.py` | 19 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | - | - |
| `rlinf/models/embodiment/starvla/action_heads/adapter.py` | 397 | 具身/VLA 模型、动作模型和策略网络 | - | _build_adapter_vlm_inputs, _run_adapter_pipeline, run_default_forward_adapter, run_rollout_adapter | __future__, torch, typing, utils |
| `rlinf/models/embodiment/starvla/action_heads/fast.py` | 556 | 具身/VLA 模型、动作模型和策略网络 | - | _apply_sampling_filters, _resolve_vlm_pad_token_id, _run_fast_pipeline, run_default_forward_fast, run_rollout_fast | __future__, numpy, torch, typing, utils |
| `rlinf/models/embodiment/starvla/action_heads/flowmatching.py` | 788 | 具身/VLA 模型、动作模型和策略网络 | - | _patch_timestep_encoder_for_fsdp, _build_dual_dino_features, _resolve_flowmatching_head_profile, _finalize_flowmatching_context, _predict_velocity, run_default_forward_flowmatching, run_rollout_flowmatching | __future__, contextlib, math, torch, typing, utils |
| `rlinf/models/embodiment/starvla/action_heads/oft.py` | 216 | 具身/VLA 模型、动作模型和策略网络 | - | _build_oft_vlm_inputs, _run_oft_backbone_and_head, run_default_forward_oft, run_rollout_oft | __future__, deployment, starVLA, torch, typing, utils |
| `rlinf/models/embodiment/starvla/dispatch.py` | 61 | 具身/VLA 模型、动作模型和策略网络 | - | get_default_forward_handler, get_rollout_handler | __future__, action_heads, collections, torch, typing |
| `rlinf/models/embodiment/starvla/starvla_action_model.py` | 445 | 具身/VLA 模型、动作模型和策略网络 | StarVLAForRLActionPrediction | - | __future__, dispatch, functools, logging, numpy, rlinf, torch, typing |
| `rlinf/models/embodiment/starvla/utils/__init__.py` | 20 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | - | - |
| `rlinf/models/embodiment/starvla/utils/action_space.py` | 205 | 具身/VLA 模型、动作模型和策略网络 | - | resolve_action_norm_stats, _gripper_mapping, unnormalize_actions_for_env | __future__, collections, numpy, os, typing |
| `rlinf/models/embodiment/starvla/utils/backbone_pipeline.py` | 200 | 具身/VLA 模型、动作模型和策略网络 | - | compute_values_from_hidden, run_backbone_pipeline | __future__, contextlib, profile, torch, typing |
| `rlinf/models/embodiment/starvla/utils/data_pipeline.py` | 349 | 具身/VLA 模型、动作模型和策略网络；数据读取/组织 | - | tensor_to_numpy_compatible, build_examples_from_env_obs, get_scalar, collect_tensor_inputs, forward_input_check, restore_pixel_values_for_forward, collect_default_forward_model_inputs, fetch_action_for_logprob_for_default_forward, pack_model_inputs_for_storage, normalize_model_inputs_for_storage | PIL, __future__, numpy, profile, torch, typing |
| `rlinf/models/embodiment/starvla/utils/profile.py` | 297 | 具身/VLA 模型、动作模型和策略网络 | - | resolve_vlm_interface, infer_policy_profile, infer_hidden_size, resolve_action_chunk_len, iter_gradient_checkpointing_targets | __future__, torch, typing |
| `rlinf/models/embodiment/starvla/utils/state.py` | 239 | 具身/VLA 模型、动作模型和策略网络 | - | _warned_keys_for_model, warn_state_adapt_once, infer_expected_state_dim_from_head, infer_expected_state_dim_for_state_adapter, adapt_state_for_expected_dim, prepare_state_tensor | __future__, numpy, os, torch, typing, warnings, weakref |
| `rlinf/models/embodiment/starvla/utils/vlm_preprocess.py` | 98 | 具身/VLA 模型、动作模型和策略网络 | - | get_train_image_size, build_base_vlm_inputs | __future__, deployment, profile, starVLA, torch, typing |
| `rlinf/models/embodiment/value_model/__init__.py` | 170 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | _strip_model_prefix, get_model, _load_state_dict | configuration, glob, logging, modeling_critic, omegaconf, os, safetensors, torch |
| `rlinf/models/embodiment/value_model/checkpoint_utils.py` | 188 | 具身/VLA 模型、动作模型和策略网络；公共入口/工具 | - | load_state_dict_from_checkpoint, has_tokenizer_files, load_norm_stats, build_input_transforms | glob, json, logging, numpy, pathlib, safetensors, torch, typing |
| `rlinf/models/embodiment/value_model/configuration.py` | 262 | 具身/VLA 模型、动作模型和策略网络；配置/参数定义 | Config, VLMBaseConfig, ValueCriticConfig | get_config | dataclasses, transformers, typing |
| `rlinf/models/embodiment/value_model/data_collator.py` | 245 | 具身/VLA 模型、动作模型和策略网络；数据读取/组织 | ValueDataCollator | stack_tensors | dataclasses, logging, numpy, torch, transformers, typing |
| `rlinf/models/embodiment/value_model/modeling_critic.py` | 1099 | 具身/VLA 模型、动作模型和策略网络 | CriticOutput, ValueHead, ValueCriticModel | make_att_2d_masks, prepare_target_values | configuration, dataclasses, logging, torch, transformers, typing, value_expert |
| `rlinf/models/embodiment/value_model/processing.py` | 668 | 具身/VLA 模型、动作模型和策略网络 | ValueImageProcessor, ValueProcessor | resize_with_pad, normalize_image_to_model_format | collections, logging, numpy, os, string, torch, transformers, typing |
| `rlinf/models/embodiment/value_model/value_expert.py` | 325 | 具身/VLA 模型、动作模型和策略网络 | ValueExpert | - | logging, os, torch, transformers, typing |
