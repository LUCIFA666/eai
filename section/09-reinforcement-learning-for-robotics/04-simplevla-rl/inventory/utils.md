# SimpleVLA-RL 文件索引：utils

覆盖 `utils` 分组，共 `36` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/utils/__init__.py` | 18 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | - | tokenizer |
| `verl/utils/config.py` | 23 | 配置、日志、分布式、FSDP、调试和工具函数；配置/参数定义 | - | update_dict_with_config | omegaconf, typing |
| `verl/utils/debug/__init__.py` | 15 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | - | performance |
| `verl/utils/debug/performance.py` | 30 | 配置、日志、分布式、FSDP、调试和工具函数 | - | log_gpu_memory_usage | logging, torch |
| `verl/utils/debug/trajectory_tracker.py` | 108 | 配置、日志、分布式、FSDP、调试和工具函数 | TrajectoryTracker | save_to_hdfs, dump_data, get_trajectory_tracker | collections, io, os, ray, tempfile, torch, verl |
| `verl/utils/distributed.py` | 28 | 配置、日志、分布式、FSDP、调试和工具函数 | - | initialize_global_process_group | os |
| `verl/utils/flops_counter.py` | 123 | 配置、日志、分布式、FSDP、调试和工具函数 | FlopsCounter | get_device_flops | torch, transformers |
| `verl/utils/fs.py` | 88 | 配置、日志、分布式、FSDP、调试和工具函数 | - | _is_non_local, md5_encode, get_local_temp_path, copy_local_path_from_hdfs | hashlib, hdfs_io, os, tempfile |
| `verl/utils/fsdp_utils.py` | 209 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | init_fn, get_init_weight_context_manager, get_fsdp_wrap_policy, get_fsdp_wrap_policy_vla, offload_fsdp_grad, load_fsdp_grad, offload_fsdp_param_and_grad, load_fsdp_param_and_grad, offload_fsdp_optimizer, load_fsdp_optimizer | functools, torch, transformers, verl |
| `verl/utils/hdfs_io.py` | 144 | 配置、日志、分布式、FSDP、调试和工具函数 | - | exists, _exists, makedirs, _mkdir, copy, _copy, _run_cmd, _hdfs_cmd, _is_non_local | logging, os, shutil |
| `verl/utils/import_utils.py` | 56 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | is_megatron_core_available, is_vllm_available, import_external_libs | functools, typing |
| `verl/utils/libero_utils.py` | 229 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | get_libero_env, get_libero_dummy_action, resize_image, get_libero_image, get_libero_wrist_image, quat2axisangle, get_image_resize_size, normalize_gripper_action, invert_gripper_action, save_rollout_video | imageio, math, numpy, os, random, tensorflow |
| `verl/utils/logger/__init__.py` | 13 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | - | - |
| `verl/utils/logger/aggregate_logger.py` | 113 | 配置、日志、分布式、FSDP、调试和工具函数 | LocalLogger | concat_dict_to_str | datetime, json, numbers, os, typing |
| `verl/utils/logging_utils.py` | 22 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | set_basic_config | logging |
| `verl/utils/megatron/__init__.py` | 13 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | - | - |
| `verl/utils/megatron/memory.py` | 41 | 配置、日志、分布式、FSDP、调试和工具函数 | MemoryBuffer | - | torch |
| `verl/utils/megatron/optimizer.py` | 92 | 配置、日志、分布式、FSDP、调试和工具函数 | - | get_megatron_optimizer | apex, megatron, verl |
| `verl/utils/megatron/optimizer_config.py` | 129 | 配置、日志、分布式、FSDP、调试和工具函数；配置/参数定义 | OptimizerConfig | - | dataclasses, torch, typing |
| `verl/utils/megatron/pipeline_parallel.py` | 51 | 配置、日志、分布式、FSDP、调试和工具函数 | - | compute_transformers_input_shapes, make_batch_generator | megatron, sequence_parallel, torch |
| `verl/utils/megatron/sequence_parallel.py` | 54 | 配置、日志、分布式、FSDP、调试和工具函数 | - | mark_parameter_as_sequence_parallel, is_sequence_parallel_param, pad_to_sequence_parallel | megatron, torch |
| `verl/utils/megatron/tensor_parallel.py` | 185 | 配置、日志、分布式、FSDP、调试和工具函数 | _VocabParallelEntropy | update_kwargs_with_config, get_default_kwargs_for_model_parallel_config, get_default_model_parallel_config, get_common_default_kwargs_for_parallel_linear, get_default_kwargs_for_column_parallel_linear, get_default_kwargs_for_row_parallel_linear, get_default_kwargs_for_parallel_embedding, is_tensor_parallel_param, get_tensor_parallel_partition_dim, get_tensor_parallel_partition_stride | megatron, torch, typing, verl |
| `verl/utils/megatron_utils.py` | 253 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | FakeTimers | get_model, unwrap_model, convert_config, init_megatron_optim_config, init_model_parallel_config, offload_megatron_param_and_grad, load_megatron_param_and_grad | megatron, omegaconf, time, torch, transformers, typing, verl |
| `verl/utils/memory_buffer.py` | 214 | 配置、日志、分布式、FSDP、调试和工具函数 | MemoryBuffer, MemoryBufferModuleWrapper, MegatronMemoryBufferForRollout | calc_padded_numel, get_weight_buffer_meta_from_module, build_memory_buffer, build_memory_reference_from_module, build_memory_reference | torch, typing |
| `verl/utils/model.py` | 321 | 配置、日志、分布式、FSDP、调试和工具函数 | LambdaLayer | squeeze, update_model_config, get_huggingface_actor_config, create_huggingface_actor, create_huggingface_critic, get_model_size, print_model_size, create_random_mask, compute_position_id_with_mask, normalize_pp_vpp_params | numpy, os, torch, transformers, typing, verl, warnings |
| `verl/utils/openvla_utils.py` | 175 | 配置、日志、分布式、FSDP、调试和工具函数；环境适配；公共入口/工具 | - | update_auto_map, check_identical_files, _handle_file_sync, check_model_logic_mismatch | PIL, datetime, filecmp, json, json_numpy, numpy, os, pathlib |
| `verl/utils/py_functional.py` | 56 | 配置、日志、分布式、FSDP、调试和工具函数 | NestedNamespace | union_two_dict, append_to_dict | types, typing |
| `verl/utils/ray_utils.py` | 43 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | parallel_put | concurrent, ray |
| `verl/utils/rendezvous/__init__.py` | 13 | 配置、日志、分布式、FSDP、调试和工具函数；公共入口/工具 | - | - | - |
| `verl/utils/rendezvous/ray_backend.py` | 77 | 配置、日志、分布式、FSDP、调试和工具函数 | NCCLIDStore | get_nccl_id_store_by_name, create_nccl_communicator_in_ray | cupy, logging, ray, time |
| `verl/utils/seqlen_balancing.py` | 265 | 配置、日志、分布式、FSDP、调试和工具函数 | - | karmarkar_karp, greedy_partition, get_seqlen_balanced_partitions, log_seqlen_unbalance, ceildiv, rearrange_micro_batches, get_reverse_idx | copy, heapq, tensordict, torch, typing |
| `verl/utils/tokenizer.py` | 79 | 配置、日志、分布式、FSDP、调试和工具函数 | - | set_pad_token_id, hf_tokenizer | warnings |
| `verl/utils/torch_dtypes.py` | 82 | 配置、日志、分布式、FSDP、调试和工具函数 | PrecisionType | - | torch, typing |
| `verl/utils/torch_functional.py` | 535 | 配置、日志、分布式、FSDP、调试和工具函数 | - | gather_from_labels, logprobs_from_logits, logprobs_from_logits_flash_attn, logprobs_from_logits_naive, logprobs_of_labels_v2, clip_by_value, entropy_from_logits, masked_sum, masked_mean, masked_var | math, os, tensordict, torch, transformers, typing |
| `verl/utils/tracking.py` | 50 | 配置、日志、分布式、FSDP、调试和工具函数 | Tracking | - | typing |
| `verl/utils/ulysses.py` | 288 | 配置、日志、分布式、FSDP、调试和工具函数 | SeqAllToAll, Gather | set_ulysses_sequence_parallel_group, get_ulysses_sequence_parallel_group, get_ulysses_sequence_parallel_world_size, get_ulysses_sequence_parallel_rank, gather_seq_scatter_heads, gather_heads_scatter_seq, _pad_tensor, _unpad_tensor, slice_input_tensor, all_to_all_tensor | torch, typing |
