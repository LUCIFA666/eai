# RLINF 文件索引：utils

覆盖 `utils` 分组，共 `50` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/utils/__init__.py` | 13 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | - | - |
| `rlinf/utils/ckpt_convertor/__init__.py` | 13 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | - | - |
| `rlinf/utils/ckpt_convertor/convert_openpi_jax_to_python.py` | 706 | 日志、checkpoint、placement、分布式和工具函数 | - | slice_paligemma_state_dict, slice_gemma_state_dict, slice_initial_orbax_checkpoint, load_jax_model_and_print_keys, convert_pi0_checkpoint, main | flax, json, numpy, openpi, orbax, os, pathlib, safetensors |
| `rlinf/utils/ckpt_convertor/fsdp_convertor/__init__.py` | 13 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | - | - |
| `rlinf/utils/ckpt_convertor/fsdp_convertor/convert_dcp_to_pt.py` | 58 | 日志、checkpoint、placement、分布式和工具函数 | - | parse_args | argparse, os, tempfile, torch |
| `rlinf/utils/ckpt_convertor/fsdp_convertor/convert_pt_to_hf.py` | 87 | 日志、checkpoint、placement、分布式和工具函数 | - | main | hydra, os, rlinf, torch, utils |
| `rlinf/utils/ckpt_convertor/fsdp_convertor/utils.py` | 197 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | get_model_save_helper, openvla_oft_save_helper, _tensor_nbytes, save_state_dict_sharded_safetensors, copy_model_config_and_code | concurrent, json, os, rlinf, safetensors, shutil, torch |
| `rlinf/utils/ckpt_convertor/megatron_convertor/__init__.py` | 13 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | - | - |
| `rlinf/utils/ckpt_convertor/megatron_convertor/config.py` | 208 | 日志、checkpoint、placement、分布式和工具函数；配置/参数定义 | ConvertorConfig | load_convertor_config | dataclasses, omegaconf, os, torch, transformers, typing, yaml |
| `rlinf/utils/ckpt_convertor/megatron_convertor/convert_hf_to_mg.py` | 415 | 日志、checkpoint、placement、分布式和工具函数 | OperationAwareDeviceInitializer | hf_to_middle_file, middle_file_to_mg, convert_hf_to_mg | concurrent, config, convert_hf_to_middle_file, convert_middle_file_to_mg, copy, multiprocessing, omegaconf, os |
| `rlinf/utils/ckpt_convertor/megatron_convertor/convert_hf_to_middle_file.py` | 503 | 日志、checkpoint、placement、分布式和工具函数 | Save, DictSaver | get_megatron_iteration, convert_layer_loadsave, convert_layer | config, gc, os, safetensors, torch, utils |
| `rlinf/utils/ckpt_convertor/megatron_convertor/convert_mg_to_middle_file.py` | 863 | 日志、checkpoint、placement、分布式和工具函数 | Save, DictSaver | find_only_directory, get_args, get_extra_state_check_none, get_megatron_iteration, get_hetero_pp_rank, convert_layer_loadsave, filter_keys_output_embedding, filter_keys_output_local_layer, filter_keys_output, convert_layer | argparse, concurrent, gc, os, safetensors, time, torch, tqdm |
| `rlinf/utils/ckpt_convertor/megatron_convertor/convert_middle_file_to_hf.py` | 726 | 日志、checkpoint、placement、分布式和工具函数 | Save, HFSTSaver | get_args, convert_layer_loadsave, convert_layer, main | argparse, concurrent, gc, json, os, safetensors, time, torch |
| `rlinf/utils/ckpt_convertor/megatron_convertor/convert_middle_file_to_mg.py` | 626 | 日志、checkpoint、placement、分布式和工具函数 | Save, CKPTSaver | get_megatron_iteration, get_hetero_pp_rank, merge_checkpoint_dict, convert_layer_load, convert_layer | collections, config, gc, os, shutil, torch, utils |
| `rlinf/utils/ckpt_convertor/megatron_convertor/utils/__init__.py` | 31 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | - | mp_utils, safetensors_loader, tensor_operations |
| `rlinf/utils/ckpt_convertor/megatron_convertor/utils/fp8_utils.py` | 135 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | fp8Tensor | ceil_div, per_block_cast_to_fp8_cpu, per_block_cast_to_bf16_cpu, per_block_cast_to_fp8, per_block_cast_to_bf16, dict_push | torch, typing |
| `rlinf/utils/ckpt_convertor/megatron_convertor/utils/mg_loader.py` | 171 | 日志、checkpoint、placement、分布式和工具函数 | MyPickleModule, MGLoaderGroupLazy | - | itertools, os, pickle, tensor_operations, torch, typing |
| `rlinf/utils/ckpt_convertor/megatron_convertor/utils/mg_moe_groupgemm.py` | 198 | 日志、checkpoint、placement、分布式和工具函数 | - | moe_seq_to_te_group, moe_te_group_to_seq, moe_seq_to_group, moe_group_to_seq | torch |
| `rlinf/utils/ckpt_convertor/megatron_convertor/utils/mp_utils.py` | 61 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | DeviceInitializer | get_device_initializer, single_thread_init | tensor_operations, torch |
| `rlinf/utils/ckpt_convertor/megatron_convertor/utils/safetensors_loader.py` | 116 | 日志、checkpoint、placement、分布式和工具函数 | STLoaderLazy, STLoader | - | glob, os, safetensors, tensor_operations, typing |
| `rlinf/utils/ckpt_convertor/megatron_convertor/utils/tensor_operations.py` | 402 | 日志、checkpoint、placement、分布式和工具函数 | Operation, Load, SplitTpTpe, MergeTpTpe, MergeTensors, CopyEquals, MergeGlu, SplitGlu | de_dup | fp8_utils, torch, typing |
| `rlinf/utils/comm_mapping.py` | 91 | 日志、checkpoint、placement、分布式和工具函数 | CommMapper | - | - |
| `rlinf/utils/convertor/__init__.py` | 13 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | - | - |
| `rlinf/utils/convertor/utils.py` | 637 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | TransformType, TransformFunc, ConvertorRule, BaseConvertor, Qwen25Convertor, Qwen25VLConvertor, Qwen3BaseConvertor, Qwen3DenseConvertor | get_mg2hf_convertor | dataclasses, enum, re, rlinf, torch, typing |
| `rlinf/utils/cuda_graph.py` | 274 | 日志、checkpoint、placement、分布式和工具函数 | GraphCaptureSpec, GraphSpec, CUDAGraphManager | build_kv_cache, _copy_tree_, _assert_on_cuda_tree | collections, dataclasses, gc, torch, typing |
| `rlinf/utils/data_iter_utils.py` | 718 | 日志、checkpoint、placement、分布式和工具函数；数据读取/组织；公共入口/工具 | - | concat_dict_list, split_list, merge_tensor, merge_list, get_iterator_k_split, get_last_rank, ceildiv, roundup_divisible, karmarkar_karp, get_seqlen_balanced_partitions | collections, copy, heapq, itertools, logging, numpy, torch, typing |
| `rlinf/utils/data_process.py` | 90 | 日志、checkpoint、placement、分布式和工具函数；数据读取/组织 | - | _decode_image_from_bytes, _decode_image_from_path, _decode_bytes, _decode_path, _fetch_and_decode, process_image_data | PIL, aiohttp, asyncio, io, typing |
| `rlinf/utils/distributed.py` | 1316 | 日志、checkpoint、placement、分布式和工具函数 | RolloutDataBalance, VocabUtility, _VocabParallelEntropyAndCrossEntropy, ScopedTimer | compute_rollout_metrics_dynamic, compute_rollout_metrics, rebalance_nd_tensor, broadcast_tensor, broadcast_tensor_within_mp, broadcast_tensor_within_pp, broadcast_tensor_within_dp, gather_tensor, all_reduce_int, run_if_model_parallel_src | collections, contextlib, numpy, rlinf, torch, typing, typing_extensions |
| `rlinf/utils/down_sampling.py` | 207 | 日志、checkpoint、placement、分布式和工具函数 | - | down_sample_batch | numpy, re, rlinf, torch |
| `rlinf/utils/drq.py` | 109 | 日志、checkpoint、placement、分布式和工具函数 | - | crop_bchw_fast, drq_crop_main, drq_crop_extra, apply_drq | torch |
| `rlinf/utils/flops.py` | 240 | 日志、checkpoint、placement、分布式和工具函数 | ModelConfig, FLOPSCalculator | - | dataclasses, torch, typing |
| `rlinf/utils/initialize.py` | 333 | 日志、checkpoint、placement、分布式和工具函数 | - | extract_selected_fields, set_megatron_args, initialize_megatron, _set_random_seed, _compile_dependencies, _initialize_tp_communicators, _initialize_distributed | datetime, megatron, numpy, omegaconf, os, random, rlinf, time |
| `rlinf/utils/logging.py` | 20 | 日志、checkpoint、placement、分布式和工具函数 | - | get_logger | - |
| `rlinf/utils/metric_logger.py` | 175 | 日志、checkpoint、placement、分布式和工具函数 | _TensorboardLogger, MetricLogger | - | omegaconf, os |
| `rlinf/utils/metric_utils.py` | 374 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | compute_split_num, _normalize_metric_shard, count_trajectories, compute_evaluate_metrics, compute_rollout_metrics, append_to_dict, compute_loss_mask, print_metrics_table | math, numpy, rlinf, time, torch |
| `rlinf/utils/nested_dict_process.py` | 229 | 日志、checkpoint、placement、分布式和工具函数 | - | update_nested_cfg, copy_dict_tensor, clone_nested_to_cpu, put_tensor_device, split_dict_to_chunk, concat_batch, stack_list_of_dict_tensor, cat_list_of_dict_tensor, split_dict | numpy, torch, typing |
| `rlinf/utils/omega_resolver.py` | 36 | 日志、checkpoint、placement、分布式和工具函数 | - | omegaconf_register | omegaconf, torch |
| `rlinf/utils/patcher.py` | 217 | 日志、checkpoint、placement、分布式和工具函数 | _Patcher | - | importlib, inspect, sys, types, typing |
| `rlinf/utils/placement.py` | 974 | 日志、checkpoint、placement、分布式和工具函数 | PlacementMode, RolloutSyncMode, HybridComponentPlacement, ModelParallelComponentPlacement, ModelParallelEvalComponentPlacement, MultiAgentModelParallelComponentPlacement, MultiAgentModelParallelEvalComponentPlacement | placement_mode_to_rollout_sync_mode | enum, logging, omegaconf, rlinf, typing |
| `rlinf/utils/profiler.py` | 244 | 日志、checkpoint、placement、分布式和工具函数 | PyTorchProfilerFunc, PyTorchProfiler | - | pathlib, rlinf, torch, typing |
| `rlinf/utils/pytree.py` | 63 | 日志、checkpoint、placement、分布式和工具函数 | - | register_pytree_dataclass_type, register_pytree_dataclasses | dataclasses, torch, typing |
| `rlinf/utils/resharding/__init__.py` | 13 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | - | - |
| `rlinf/utils/resharding/mcore_weight_reshard.py` | 335 | 日志、checkpoint、placement、分布式和工具函数 | MegatronCoreWeightReshard | - | megatron, reshard_config, torch |
| `rlinf/utils/resharding/reshard_config.py` | 93 | 日志、checkpoint、placement、分布式和工具函数；配置/参数定义 | ReshardConfig | - | dataclasses, megatron, rlinf, typing, utils |
| `rlinf/utils/resharding/utils.py` | 332 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | - | get_tp_reshard_fn, get_tpe_reshard_fn, get_pp_reshard_fn, _gather_tp_group_tensor_and_reshard, tp_reshard_fn_qwen2_5, tp_reshard_fn_qwen3_dense, tp_reshard_fn_qwen3_moe, tpe_reshard_fn_qwen3_moe, _gather_pp_group_tensor_and_reshard, gather_pp_group_tensor_and_reshard | megatron, rlinf, torch |
| `rlinf/utils/runner_utils.py` | 141 | 日志、checkpoint、placement、分布式和工具函数；训练流程入口；公共入口/工具 | EarlyStopController | safe_is_divisible, check_progress, local_mkdir_safe | os, rlinf, tempfile, typing |
| `rlinf/utils/timers.py` | 196 | 日志、checkpoint、placement、分布式和工具函数 | Timer, NamedTimer | - | dataclasses, datetime, numpy, rlinf, time, typing |
| `rlinf/utils/torch_functionals.py` | 32 | 日志、checkpoint、placement、分布式和工具函数 | - | pad_tensor_to_length | torch |
| `rlinf/utils/train_utils.py` | 84 | 日志、checkpoint、placement、分布式和工具函数；训练流程入口；公共入口/工具 | - | set_sync_funcs, set_train, set_eval | megatron |
| `rlinf/utils/utils.py` | 541 | 日志、checkpoint、placement、分布式和工具函数；公共入口/工具 | DualOutput | clear_memory, apply_func_to_dict, move_to_device_if_tensor, seed_everything, retrieve_model_state_dict_in_cpu, swap_dict, cpu_weight_swap, _get_nvtx_module, nvtx_range, configure_batch_sizes | atexit, contextlib, functools, gc, importlib, numpy, os, random |
