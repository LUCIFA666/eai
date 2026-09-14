# RLINF 文件索引：hybrid-engines

覆盖 `hybrid-engines` 分组，共 `28` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/hybrid_engines/__init__.py` | 13 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；公共入口/工具 | - | - | - |
| `rlinf/hybrid_engines/fsdp/__init__.py` | 54 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；公共入口/工具 | - | - | packaging, torch |
| `rlinf/hybrid_engines/fsdp/fsdp_model_manager.py` | 687 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | FSDPModelManager | - | omegaconf, os, rlinf, torch, transformers, typing, warnings |
| `rlinf/hybrid_engines/fsdp/strategy/__init__.py` | 13 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；公共入口/工具 | - | - | - |
| `rlinf/hybrid_engines/fsdp/strategy/base.py` | 547 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | - | - | - |
| `rlinf/hybrid_engines/fsdp/strategy/checkpoint.py` | 132 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | Checkpoint | - | collections, rlinf, torch, typing |
| `rlinf/hybrid_engines/fsdp/strategy/fsdp.py` | 468 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | FSDPStrategy | - | contextlib, os, rlinf, torch, typing |
| `rlinf/hybrid_engines/fsdp/strategy/fsdp2.py` | 203 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | FSDP2Strategy | - | contextlib, rlinf, torch, typing |
| `rlinf/hybrid_engines/fsdp/utils.py` | 1153 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；公共入口/工具 | FSDPVersion | create_device_mesh, init_fn, get_init_weight_context_manager, _normalize_wrap_targets, _resolve_module_classes_to_wrap, _fsdp2_fully_shard_supports_ignored_params, _collect_ignored_params_for_fsdp2, get_fsdp_wrap_policy, apply_fsdp2_to_model, get_fsdp2_full_state_dict_all_ranks | accelerate, enum, functools, packaging, rlinf, torch, transformers, typing |
| `rlinf/hybrid_engines/megatron/__init__.py` | 13 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；公共入口/工具 | - | - | - |
| `rlinf/hybrid_engines/megatron/megatron_model_manager.py` | 1006 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | LinearForLastLayer, MegatronModelManager | get_specs, patch_load_checkpoint_to_be_non_strict | contextlib, functools, gc, itertools, megatron, omegaconf, rlinf, torch |
| `rlinf/hybrid_engines/megatron/token_dispatcher.py` | 600 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | FuscoInfo, FuscoDispatch, FuscoCombine, MoEAlltoAllTokenDispatcher | gather_along_first_dim, dispatch_raw, combine_raw | megatron, os, rlinf, torch, typing |
| `rlinf/hybrid_engines/megatron/utils.py` | 437 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；公共入口/工具 | - | preprocess_packed_seqs, postprocess_packed_seqs, remove_left_padding, recover_left_padding, tensor_rm_left_padding, get_rope_index | torch, typing |
| `rlinf/hybrid_engines/sglang/common/__init__.py` | 13 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；公共入口/工具 | - | - | - |
| `rlinf/hybrid_engines/sglang/common/detokenizer_manager.py` | 61 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | DetokenizerManager | run_detokenizer_process | sglang |
| `rlinf/hybrid_engines/sglang/common/io_struct.py` | 52 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | AbortGenerationInput, AbortGenerationOutput, TaskMethodInput, TaskMethodOutput, SyncHFWeightInput, SyncHFWeightOutput | - | dataclasses, sglang, typing |
| `rlinf/hybrid_engines/sglang/common/sgl_engine.py` | 138 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | Engine | _set_envs_and_config | asyncio, importlib, io_struct, logging, multiprocessing, os, packaging, rlinf |
| `rlinf/hybrid_engines/sglang/common/sgl_scheduler.py` | 598 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | Scheduler | posi_norm, validate_weight_init, validate_weight_diff, run_scheduler_process | importlib, io_struct, logging, omegaconf, packaging, rlinf, sglang, torch |
| `rlinf/hybrid_engines/sglang/common/tokenizer_manager.py` | 240 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | TokenizerManager | - | fastapi, importlib, io_struct, packaging, sglang, typing |
| `rlinf/hybrid_engines/vllm/vllm_0_8_5/__init__.py` | 13 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；公共入口/工具 | - | - | - |
| `rlinf/hybrid_engines/vllm/vllm_0_8_5/executor.py` | 313 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | VLLMExecutor, VLLMWorkerProc | - | omegaconf, os, psutil, rlinf, signal, sys, threading, typing |
| `rlinf/hybrid_engines/vllm/vllm_0_8_5/weight_loader.py` | 43 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | - | vocab_loader | torch, vllm |
| `rlinf/hybrid_engines/vllm/vllm_0_8_5/worker.py` | 161 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；远程 worker 执行单元 | VLLMWorker | - | omegaconf, rlinf, torch, typing, vllm |
| `rlinf/hybrid_engines/weight_syncer/__init__.py` | 35 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端；公共入口/工具 | - | - | base, bucket_syncer, compressor, patch_syncer |
| `rlinf/hybrid_engines/weight_syncer/base.py` | 204 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | WeightSyncer | materialize_tensor, normalize_dtype, normalize_device | __future__, abc, omegaconf, rlinf, torch, typing |
| `rlinf/hybrid_engines/weight_syncer/bucket_syncer.py` | 203 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | BucketWeightSyncer | iter_named_tensor_buckets | __future__, base, collections, torch |
| `rlinf/hybrid_engines/weight_syncer/compressor.py` | 251 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | PatchCompressor, IdentityCompressor, NVCompCompressor | - | __future__, abc, base, rlinf, torch, typing |
| `rlinf/hybrid_engines/weight_syncer/patch_syncer.py` | 918 | FSDP/Megatron/vLLM/SGLang 混合推理训练后端 | EmptyWeightPatch, WeightPatch, CompressedWeightPatch, PatchBuilder, _PrefetchedCPUSnapshot, _PendingSnapshotUpdate, CPUSnapshotPatchBuilder, GPUSnapshotPatchBuilder | downscale_nonnegative_indices, as_coo_2d_view | __future__, abc, base, bucket_syncer, compressor, concurrent, dataclasses, rlinf |
