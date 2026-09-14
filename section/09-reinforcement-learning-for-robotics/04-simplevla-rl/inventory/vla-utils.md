# SimpleVLA-RL 文件索引：vla-utils

覆盖 `vla-utils` 分组，共 `11` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/utils/vla_utils/__init__.py` | 0 | OpenVLA/OpenVLA-OFT 模型适配；公共入口/工具 | - | - | - |
| `verl/utils/vla_utils/openvla/__init__.py` | 0 | OpenVLA/OpenVLA-OFT 模型适配；公共入口/工具 | - | - | - |
| `verl/utils/vla_utils/openvla/configuration_prismatic.py` | 140 | OpenVLA/OpenVLA-OFT 模型适配；配置/参数定义 | PrismaticConfig, OpenVLAConfig | - | transformers, typing |
| `verl/utils/vla_utils/openvla/modeling_prismatic.py` | 562 | OpenVLA/OpenVLA-OFT 模型适配 | PrismaticVisionBackbone, PrismaticProjector, PrismaticCausalLMOutputWithPast, PrismaticPreTrainedModel, PrismaticForConditionalGeneration, OpenVLAForActionPrediction | unpack_tuple, _ls_new_forward, ls_apply_patch | configuration_prismatic, dataclasses, functools, logging, numpy, timm, tokenizers, torch |
| `verl/utils/vla_utils/openvla/processing_prismatic.py` | 257 | OpenVLA/OpenVLA-OFT 模型适配 | PrismaticImageProcessor, PrismaticProcessor | letterbox_pad_transform | PIL, timm, torch, torchvision, transformers, typing |
| `verl/utils/vla_utils/openvla_oft/__init__.py` | 0 | OpenVLA/OpenVLA-OFT 模型适配；公共入口/工具 | - | - | - |
| `verl/utils/vla_utils/openvla_oft/configuration_prismatic.py` | 140 | OpenVLA/OpenVLA-OFT 模型适配；配置/参数定义 | PrismaticConfig, OpenVLAConfig | - | transformers, typing |
| `verl/utils/vla_utils/openvla_oft/constants.py` | 138 | OpenVLA/OpenVLA-OFT 模型适配 | NormalizationType | detect_robot_platform | enum, os, sys |
| `verl/utils/vla_utils/openvla_oft/modeling_prismatic.py` | 2039 | OpenVLA/OpenVLA-OFT 模型适配 | ProprioProjector, PrismaticVisionBackbone, PrismaticProjector, PrismaticCausalLMOutputWithPast, PrismaticPreTrainedModel, PrismaticForConditionalGeneration, OpenVLAForActionPrediction | unpack_tuple, _ls_new_forward, ls_apply_patch | configuration_prismatic, constants, dataclasses, functools, logging, numpy, timm, tokenizers |
| `verl/utils/vla_utils/openvla_oft/processing_prismatic.py` | 252 | OpenVLA/OpenVLA-OFT 模型适配 | PrismaticImageProcessor, PrismaticProcessor | letterbox_pad_transform | PIL, timm, torch, torchvision, transformers, typing |
| `verl/utils/vla_utils/openvla_oft/train_utils.py` | 107 | OpenVLA/OpenVLA-OFT 模型适配；训练流程入口；公共入口/工具 | - | get_current_action_mask, get_next_actions_mask, compute_token_accuracy, compute_actions_l1_loss, find_checkpoint_file, load_component_state_dict | constants, os, torch |
