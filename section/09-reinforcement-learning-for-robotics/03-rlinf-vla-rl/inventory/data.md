# RLINF 文件索引：data

覆盖 `data` 分组，共 `25` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/data/__init__.py` | 13 | 数据结构、数据集、trajectory/replay buffer；公共入口/工具 | - | - | - |
| `rlinf/data/datasets/__init__.py` | 275 | 数据结构、数据集、trajectory/replay buffer；公共入口/工具 | - | create_rl_dataset, collate_fn, sft_collate_fn | logging, omegaconf, rlinf, torch, transformers, typing |
| `rlinf/data/datasets/d4rl.py` | 349 | 数据结构、数据集、trajectory/replay buffer | D4RLDataset | build_d4rl_dataset_from_cfg | __future__, numpy, omegaconf, os, pathlib, torch, tqdm, typing |
| `rlinf/data/datasets/dreamzero.py` | 2074 | 数据结构、数据集、trajectory/replay buffer | DreamZeroLiberoDataset, DreamZeroDroidDataset, DreamZeroCollator | _infer_droid_view_hw_from_model_cfg, _load_gear_stats, q99_normalize, _resolve_advantage_parquet_path, _load_advantage_map_cached, _lookup_advantage_from_map, _probe_video_container_fps, _droid_default_state_action_slices, _empty_slice, _infer_joint_grip_slices | bisect, collections, json, numpy, pathlib, re, rlinf, time |
| `rlinf/data/datasets/item.py` | 74 | 数据结构、数据集、trajectory/replay buffer | DatasetItem, SftDatasetItem | - | dataclasses, torch, typing |
| `rlinf/data/datasets/reasoning.py` | 250 | 数据结构、数据集、trajectory/replay buffer | ReasoningDataset | - | concurrent, json, logging, omegaconf, os, rlinf, torch, traceback |
| `rlinf/data/datasets/recap/__init__.py` | 13 | 数据结构、数据集、trajectory/replay buffer；公共入口/工具 | - | - | - |
| `rlinf/data/datasets/recap/cfg_model.py` | 194 | 数据结构、数据集、trajectory/replay buffer | AdvantagePreservingDataset, CFGDataLoaderImpl, TokenizePromptWithGuidance, CfgMixtureDataset | - | __future__, common, dataclasses, logging, rlinf, torch, typing |
| `rlinf/data/datasets/recap/common.py` | 167 | 数据结构、数据集、trajectory/replay buffer | SizedDataset, BaseDataLoaderImpl, ReCapMixtureDataset | forward_set_epoch, _safe_hash | __future__, hashlib, logging, numpy, torch, typing |
| `rlinf/data/datasets/recap/utils.py` | 138 | 数据结构、数据集、trajectory/replay buffer；公共入口/工具 | - | cast_image_features, decode_image_struct_batch, load_return_stats_from_dataset, load_returns_sidecar, load_task_descriptions | PIL, __future__, io, json, lerobot, logging, numpy, pathlib |
| `rlinf/data/datasets/recap/value_model.py` | 397 | 数据结构、数据集、trajectory/replay buffer | NormStats, ReturnNormalizer, ValueDataset, ValueDataLoaderImpl, ValueMixtureDataset | _dict_to_norm_stats, load_stats | __future__, common, dataclasses, json, lerobot, logging, numpy, openpi |
| `rlinf/data/datasets/reward_model.py` | 97 | 数据结构、数据集、trajectory/replay buffer；奖励计算或奖励模型 | RewardDatasetPayload, RewardBinaryDataset | - | dataclasses, os, torch, typing |
| `rlinf/data/datasets/rstar2.py` | 100 | 数据结构、数据集、trajectory/replay buffer | Rstar2Dataset | get_tool_schemas | omegaconf, rlinf, transformers, typing |
| `rlinf/data/datasets/vlm.py` | 1055 | 数据结构、数据集、trajectory/replay buffer | VLMBaseDataset, VLMDatasetRegistry, Robo2VLMDataset, Robo2VLMSFTDataset, QwenTrendProgressSFTDataset, SimpleQwenTrendSFTDataset | _resolve_video_path | PIL, ast, io, json, logging, omegaconf, os, pandas |
| `rlinf/data/datasets/wideseek_r1.py` | 139 | 数据结构、数据集、trajectory/replay buffer | WideSeekR1Dataset | - | json, logging, omegaconf, rlinf, torch, transformers, typing |
| `rlinf/data/datasets/world_model.py` | 381 | 数据结构、数据集、trajectory/replay buffer | FuncRegistry, NpyTrajectoryDatasetWrapper | first_frame, last_frame, closest_timestamp, first_n_frames, last_n_frames | glob, numpy, os, torch, torchvision, typing |
| `rlinf/data/embodied_buffer_dataset.py` | 287 | 数据结构、数据集、trajectory/replay buffer；数据读取/组织 | ReplayBufferDataset, PreloadReplayBufferDataset | replay_buffer_collate_fn | queue, rlinf, threading, time, torch, typing |
| `rlinf/data/embodied_io_struct.py` | 818 | 数据结构、数据集、trajectory/replay buffer | EnvOutput, RolloutResult, ChunkStepResult, Trajectory, EmbodiedRolloutResult | get_model_weights_id, convert_trajectories_to_batch | dataclasses, rlinf, torch, typing, uuid |
| `rlinf/data/io_struct.py` | 1837 | 数据结构、数据集、trajectory/replay buffer | - | - | - |
| `rlinf/data/lerobot_writer.py` | 204 | 数据结构、数据集、trajectory/replay buffer | LeRobotDatasetWriter | - | gc, rlinf, typing |
| `rlinf/data/replay_buffer.py` | 1169 | 数据结构、数据集、trajectory/replay buffer | TrajectoryCache, TrajectoryReplayBuffer | clone_dict_of_tensors | concurrent, copy, json, numpy, os, pickle, rlinf, shutil |
| `rlinf/data/tokenizers.py` | 71 | 数据结构、数据集、trajectory/replay buffer | - | set_pad_token_id, hf_tokenizer | warnings |
| `rlinf/data/tool_call/__init__.py` | 13 | 数据结构、数据集、trajectory/replay buffer；公共入口/工具 | - | - | - |
| `rlinf/data/tool_call/tool_io_struct.py` | 122 | 数据结构、数据集、trajectory/replay buffer | MCPRequestType, MCPSessionState, MCPRequest, MCPResponse, ToolChannelRequest, ToolChannelResponse, ToolRequest, ToolResponse | - | dataclasses, enum, typing |
| `rlinf/data/utils.py` | 53 | 数据结构、数据集、trajectory/replay buffer；公共入口/工具 | - | batch_pad_to_fixed_len | torch |
