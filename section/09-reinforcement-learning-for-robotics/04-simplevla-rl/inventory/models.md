# SimpleVLA-RL 文件索引：models

覆盖 `models` 分组，共 `15` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/models/__init__.py` | 13 | 语言模型/权重加载支持；公共入口/工具 | - | - | - |
| `verl/models/llama/__init__.py` | 0 | 语言模型/权重加载支持；公共入口/工具 | - | - | - |
| `verl/models/llama/megatron/__init__.py` | 24 | 语言模型/权重加载支持；公共入口/工具 | - | - | modeling_llama_megatron |
| `verl/models/llama/megatron/checkpoint_utils/__init__.py` | 13 | 语言模型/权重加载支持；公共入口/工具 | - | - | - |
| `verl/models/llama/megatron/checkpoint_utils/llama_loader.py` | 446 | 语言模型/权重加载支持 | - | _megatron_calc_layer_map, load_state_dict_to_megatron_llama | time, torch, typing |
| `verl/models/llama/megatron/checkpoint_utils/llama_saver.py` | 449 | 语言模型/权重加载支持 | - | _megatron_calc_global_rank, _megatron_calc_layer_map, merge_megatron_ckpt_llama | megatron, time, torch, typing |
| `verl/models/llama/megatron/layers/__init__.py` | 18 | 语言模型/权重加载支持；公共入口/工具 | - | - | parallel_attention, parallel_decoder, parallel_mlp, parallel_rmsnorm |
| `verl/models/llama/megatron/layers/parallel_attention.py` | 418 | 语言模型/权重加载支持 | LlamaRotaryEmbedding, LlamaLinearScalingRotaryEmbedding, LlamaDynamicNTKScalingRotaryEmbedding, ParallelLlamaAttention, ParallelLlamaAttentionRmPad | rotate_half, apply_rotary_pos_emb, repeat_kv, apply_rotary_pos_emb_rmpad, apply_rotary_pos_emb_rmpad_flash | einops, flash_attn, math, megatron, torch, transformers, typing, verl |
| `verl/models/llama/megatron/layers/parallel_decoder.py` | 146 | 语言模型/权重加载支持 | ParallelLlamaDecoderLayer, ParallelLlamaDecoderLayerRmPad | - | megatron, parallel_attention, parallel_mlp, parallel_rmsnorm, torch, transformers, typing |
| `verl/models/llama/megatron/layers/parallel_linear.py` | 74 | 语言模型/权重加载支持 | QKVParallelLinear, MergedColumnParallelLinear | - | megatron, typing |
| `verl/models/llama/megatron/layers/parallel_mlp.py` | 74 | 语言模型/权重加载支持 | ParallelLlamaMLP | - | megatron, torch, transformers, verl |
| `verl/models/llama/megatron/layers/parallel_rmsnorm.py` | 46 | 语言模型/权重加载支持 | ParallelLlamaRMSNorm | - | apex, megatron, numbers, torch, transformers, verl |
| `verl/models/llama/megatron/modeling_llama_megatron.py` | 663 | 语言模型/权重加载支持 | ParallelLlamaModel, ParallelLlamaForCausalLM, ParallelLlamaModelRmPad, ParallelLlamaForCausalLMRmPad, ParallelLlamaForValueRmPad, ParallelLlamaModelRmPadPP, ParallelLlamaForCausalLMRmPadPP, ParallelLlamaForValueRmPadPP | _make_causal_mask, _expand_mask | flash_attn, layers, megatron, torch, transformers, typing, verl |
| `verl/models/registry.py` | 66 | 语言模型/权重加载支持 | ModelRegistry | check_model_support_rmpad | importlib, torch, transformers, typing |
| `verl/models/weight_loader_registry.py` | 23 | 语言模型/权重加载支持 | - | get_weight_loader | - |
