# SimpleVLA-RL 文件索引：third-party

覆盖 `third-party` 分组，共 `55` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/third_party/__init__.py` | 13 | 内置 vLLM 兼容代码；公共入口/工具 | - | - | - |
| `verl/third_party/vllm/__init__.py` | 51 | 内置 vLLM 兼容代码；公共入口/工具 | - | get_version | importlib |
| `verl/third_party/vllm/vllm_v_0_3_1/__init__.py` | 13 | 内置 vLLM 兼容代码；公共入口/工具 | - | - | - |
| `verl/third_party/vllm/vllm_v_0_3_1/arg_utils.py` | 228 | 内置 vLLM 兼容代码；公共入口/工具 | EngineArgs, AsyncEngineArgs | - | argparse, config, dataclasses, torch, transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_3_1/config.py` | 577 | 内置 vLLM 兼容代码；配置/参数定义 | ModelConfig, CacheConfig, ParallelConfig, SchedulerConfig, DeviceConfig, LoRAConfig | _get_and_verify_dtype, _get_and_verify_max_len | dataclasses, packaging, torch, transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_3_1/llm.py` | 275 | 内置 vLLM 兼容代码 | LLM | - | arg_utils, llm_engine_sp, torch, tqdm, transformers, typing, verl, vllm |
| `verl/third_party/vllm/vllm_v_0_3_1/llm_engine_sp.py` | 765 | 内置 vLLM 兼容代码 | LLMEngine | initialize_cluster, get_open_port | arg_utils, os, socket, time, tokenizer, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_3_1/model_loader.py` | 275 | 内置 vLLM 兼容代码 | - | _set_default_torch_dtype, _get_model_architecture, vocab_init, _get_model_weight_loader, get_model, load_weights, _get_logits, forward | config, contextlib, megatron, torch, transformers, typing, vllm, weight_loaders |
| `verl/third_party/vllm/vllm_v_0_3_1/model_runner.py` | 285 | 内置 vLLM 兼容代码；训练流程入口 | ModelRunner | - | contextlib, model_loader, numpy, time, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_3_1/parallel_state.py` | 147 | 内置 vLLM 兼容代码 | - | initialize_model_parallel_from_megatron, get_tensor_model_parallel_group, get_tensor_model_parallel_world_size, get_tensor_model_parallel_rank, get_tensor_model_parallel_src_rank, get_micro_data_parallel_group, get_micro_data_parallel_world_size, get_micro_data_parallel_rank | torch, vllm |
| `verl/third_party/vllm/vllm_v_0_3_1/tokenizer.py` | 72 | 内置 vLLM 兼容代码 | TokenizerGroup | - | transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_3_1/weight_loaders.py` | 95 | 内置 vLLM 兼容代码 | - | parallel_weight_loader, default_weight_loader, gpt2_weight_loader, llama_weight_loader, mistral_weight_loader | torch, typing |
| `verl/third_party/vllm/vllm_v_0_3_1/worker.py` | 314 | 内置 vLLM 兼容代码；远程 worker 执行单元 | Worker | _init_distributed_environment, _pad_to_alignment, _pad_to_max, _check_if_gpu_supports_dtype | gc, model_loader, model_runner, os, parallel_state, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/__init__.py` | 13 | 内置 vLLM 兼容代码；公共入口/工具 | - | - | - |
| `verl/third_party/vllm/vllm_v_0_4_2/arg_utils.py` | 320 | 内置 vLLM 兼容代码；公共入口/工具 | EngineArgs | nullable_str | argparse, config, dataclasses, os, torch, transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/config.py` | 200 | 内置 vLLM 兼容代码；配置/参数定义 | ModelConfig, LoadFormat, LoadConfig | - | dataclasses, enum, json, transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/dtensor_weight_loaders.py` | 269 | 内置 vLLM 兼容代码 | - | gemma_dtensor_weight_loader, gptbigcode_dtensor_load_weights, starcoder2_dtensor_load_weights, llama_dtensor_weight_loader, qwen2_dtensor_weight_loader, gpt2_dtensor_weight_loader, redistribute_dtensor, _process_parameter_names, load_dtensor_weights, _get_model_weight_loader | torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/hf_weight_loader.py` | 91 | 内置 vLLM 兼容代码 | - | update_hf_weight_loader, gemma_load_weights, load_hf_weights | torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/llm.py` | 306 | 内置 vLLM 兼容代码 | LLM | - | arg_utils, llm_engine_sp, torch, tqdm, transformers, typing, verl, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/llm_engine_sp.py` | 283 | 内置 vLLM 兼容代码 | LLMEngine | - | arg_utils, config, tokenizer, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/megatron_weight_loaders.py` | 348 | 内置 vLLM 兼容代码 | - | parallel_weight_loader, default_weight_loader, gpt2_weight_loader, llama_megatron_weight_loader, llama_megatron_core_te_weight_loader, llama_megatron_core_weight_loader, _replace_name, llama_megatron_core_te_weight_loader, llama_megatron_core_weight_loader, _replace_name | torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/model_loader.py` | 265 | 内置 vLLM 兼容代码 | DummyModelLoader, MegatronLoader, HFLoader, DTensorLoader | get_model, get_model_loader, _get_logits | config, dtensor_weight_loaders, hf_weight_loader, megatron_weight_loaders, torch, transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/model_runner.py` | 281 | 内置 vLLM 兼容代码；训练流程入口 | BatchType, ModelRunner | - | config, enum, model_loader, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/parallel_state.py` | 294 | 内置 vLLM 兼容代码 | - | initialize_parallel_state, ensure_model_parallel_initialized, model_parallel_is_initialized, initialize_model_parallel_for_vllm, initialize_model_parallel, get_device_mesh, get_tensor_model_parallel_group, get_tensor_model_parallel_world_size, get_tensor_model_parallel_rank, get_tensor_model_parallel_src_rank | os, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/spmd_gpu_executor.py` | 218 | 内置 vLLM 兼容代码 | SPMDGPUExecutor, SPMDGPUExecutorAsync | initialize_cluster, get_open_port | config, os, socket, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/tokenizer.py` | 77 | 内置 vLLM 兼容代码 | TokenizerGroup | - | transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_4_2/worker.py` | 292 | 内置 vLLM 兼容代码；远程 worker 执行单元 | Worker | init_worker_distributed_environment | config, dtensor_weight_loaders, gc, hf_weight_loader, megatron_weight_loaders, model_runner, os, parallel_state |
| `verl/third_party/vllm/vllm_v_0_5_4/__init__.py` | 13 | 内置 vLLM 兼容代码；公共入口/工具 | - | - | - |
| `verl/third_party/vllm/vllm_v_0_5_4/arg_utils.py` | 453 | 内置 vLLM 兼容代码；公共入口/工具 | EngineArgs | nullable_str | argparse, config, dataclasses, json, os, torch, transformers, typing |
| `verl/third_party/vllm/vllm_v_0_5_4/config.py` | 246 | 内置 vLLM 兼容代码；配置/参数定义 | ModelConfig, LoadFormat, LoadConfig | - | dataclasses, enum, json, torch, transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_5_4/dtensor_weight_loaders.py` | 340 | 内置 vLLM 兼容代码 | - | gemma_dtensor_weight_loader, gptbigcode_dtensor_load_weights, starcoder2_dtensor_load_weights, llama_dtensor_weight_loader, qwen2_dtensor_weight_loader, deepseekv2_dtensor_weight_loader, gpt2_dtensor_weight_loader, redistribute_dtensor, _process_parameter_names, load_dtensor_weights | torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_5_4/hf_weight_loader.py` | 44 | 内置 vLLM 兼容代码 | - | update_hf_weight_loader, load_hf_weights | torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_5_4/llm.py` | 239 | 内置 vLLM 兼容代码 | LLM | - | arg_utils, contextlib, llm_engine_sp, torch, tqdm, transformers, typing, verl |
| `verl/third_party/vllm/vllm_v_0_5_4/llm_engine_sp.py` | 328 | 内置 vLLM 兼容代码 | LLMEngine | - | arg_utils, config, tokenizer, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_5_4/megatron_weight_loaders.py` | 307 | 内置 vLLM 兼容代码 | - | parallel_weight_loader, default_weight_loader, gpt2_weight_loader, llama_megatron_weight_loader, llama_megatron_core_te_weight_loader, llama_megatron_core_weight_loader, _replace_name, llama_megatron_core_te_weight_loader, llama_megatron_core_weight_loader, _replace_name | torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_5_4/model_loader.py` | 302 | 内置 vLLM 兼容代码 | DummyModelLoader, MegatronLoader, HFLoader, DTensorLoader | get_model, get_model_loader, _get_logits, logitsprocessor_init | config, dtensor_weight_loaders, hf_weight_loader, megatron_weight_loaders, torch, transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_5_4/model_runner.py` | 150 | 内置 vLLM 兼容代码；训练流程入口 | BatchType, ModelRunner | - | config, enum, model_loader, torch, typing, vllm, warnings |
| `verl/third_party/vllm/vllm_v_0_5_4/parallel_state.py` | 303 | 内置 vLLM 兼容代码 | - | initialize_parallel_state, ensure_model_parallel_initialized, model_parallel_is_initialized, initialize_model_parallel_for_vllm, initialize_model_parallel, get_device_mesh, get_tensor_model_parallel_group, get_tensor_model_parallel_world_size, get_tensor_model_parallel_rank, get_tensor_model_parallel_src_rank | os, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_5_4/spmd_gpu_executor.py` | 253 | 内置 vLLM 兼容代码 | SPMDGPUExecutor, SPMDGPUExecutorAsync | initialize_cluster, get_open_port | config, os, socket, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_5_4/tokenizer.py` | 77 | 内置 vLLM 兼容代码 | TokenizerGroup | - | transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_5_4/worker.py` | 323 | 内置 vLLM 兼容代码；远程 worker 执行单元 | Worker | init_worker_distributed_environment | config, dtensor_weight_loaders, gc, hf_weight_loader, megatron_weight_loaders, model_runner, os, parallel_state |
| `verl/third_party/vllm/vllm_v_0_6_3/__init__.py` | 13 | 内置 vLLM 兼容代码；公共入口/工具 | - | - | - |
| `verl/third_party/vllm/vllm_v_0_6_3/arg_utils.py` | 78 | 内置 vLLM 兼容代码；公共入口/工具 | EngineArgs | - | config, dataclasses, os, transformers, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/config.py` | 105 | 内置 vLLM 兼容代码；配置/参数定义 | LoadFormat, ModelConfig, LoadConfig | - | dataclasses, enum, json, transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/dtensor_weight_loaders.py` | 380 | 内置 vLLM 兼容代码 | - | gemma_dtensor_weight_loader, gptbigcode_dtensor_load_weights, starcoder2_dtensor_load_weights, llama_dtensor_weight_loader, qwen2_dtensor_weight_loader, qwen2vl_dtensor_weight_loader, deepseekv2_dtensor_weight_loader, gpt2_dtensor_weight_loader, redistribute_dtensor, _process_parameter_names | torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/hf_weight_loader.py` | 41 | 内置 vLLM 兼容代码 | - | update_hf_weight_loader, load_hf_weights | torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/llm.py` | 200 | 内置 vLLM 兼容代码 | LLM | - | arg_utils, llm_engine_sp, torch, transformers, typing, verl, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/llm_engine_sp.py` | 408 | 内置 vLLM 兼容代码 | LLMEngine | - | arg_utils, config, functools, tokenizer, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/megatron_weight_loaders.py` | 308 | 内置 vLLM 兼容代码 | - | parallel_weight_loader, default_weight_loader, gpt2_weight_loader, llama_megatron_weight_loader, llama_megatron_core_te_weight_loader, llama_megatron_core_weight_loader, _replace_name, llama_megatron_core_te_weight_loader, llama_megatron_core_weight_loader, _replace_name | torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/model_loader.py` | 332 | 内置 vLLM 兼容代码 | DummyModelLoader, MegatronLoader, HFLoader, DTensorLoader | get_model, get_model_loader, _get_logits, logitsprocessor_init | config, dtensor_weight_loaders, hf_weight_loader, megatron_weight_loaders, torch, transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/model_runner.py` | 182 | 内置 vLLM 兼容代码；训练流程入口 | BatchType, ModelRunner | - | config, enum, model_loader, torch, typing, vllm, warnings |
| `verl/third_party/vllm/vllm_v_0_6_3/parallel_state.py` | 312 | 内置 vLLM 兼容代码 | - | initialize_parallel_state, ensure_model_parallel_initialized, model_parallel_is_initialized, initialize_model_parallel_for_vllm, initialize_model_parallel, get_device_mesh, get_tensor_model_parallel_group, get_tensor_model_parallel_world_size, get_tensor_model_parallel_rank, get_tensor_model_parallel_src_rank | os, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/spmd_gpu_executor.py` | 256 | 内置 vLLM 兼容代码 | SPMDGPUExecutor, SPMDGPUExecutorAsync | initialize_cluster, get_open_port | config, os, socket, torch, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/tokenizer.py` | 40 | 内置 vLLM 兼容代码 | TokenizerGroup | - | transformers, typing, vllm |
| `verl/third_party/vllm/vllm_v_0_6_3/worker.py` | 333 | 内置 vLLM 兼容代码；远程 worker 执行单元 | Worker | init_worker_distributed_environment | config, dtensor_weight_loaders, gc, hf_weight_loader, megatron_weight_loaders, model_runner, os, parallel_state |
