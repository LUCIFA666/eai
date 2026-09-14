# RLINF 文件索引：examples-other

覆盖 `examples-other` 分组，共 `14` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `examples/reasoning/main_grpo.py` | 158 | 示例脚本和数据处理 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/recap/cfg/train_cfg.py` | 73 | 示例脚本和数据处理；训练流程入口 | - | main | hydra, json, omegaconf, os, rlinf, torch |
| `examples/recap/process/compute_advantages.py` | 1274 | 示例脚本和数据处理 | RunningStats, ValueInferenceDataset | setup_distributed, cleanup_distributed, get_shard_indices, gather_all_advantages, to_numpy, to_scalar, _parse_value_model_kwargs, load_lerobot_dataset, build_obs, advantage_collate_fn | gc, hydra, json, lerobot, logging, numpy, omegaconf, os |
| `examples/recap/process/compute_returns.py` | 507 | 示例脚本和数据处理 | - | compute_returns_for_episode, get_episode_boundaries, _process_single_parquet, process_dataset, main | concurrent, hydra, json, logging, math, numpy, omegaconf, pathlib |
| `examples/recap/process/recompute_advantages_from_value_reward.py` | 827 | 示例脚本和数据处理；奖励计算或奖励模型 | - | _suppress_video_logging, _infer_return_range, discover_datasets_and_return_range, load_existing_advantages, compute_advantages_for_dataset, modify_episodes_with_advantage, _update_single_parquet_file, add_advantages_to_parquet_files, build_save_advantages_df, update_mixture_config | argparse, concurrent, json, logging, numpy, os, pandas, pathlib |
| `examples/recap/process/visualize_advantage_dataset.py` | 962 | 示例脚本和数据处理；数据读取/组织 | - | to_numpy, to_scalar, load_dataset, detect_image_keys, get_episode_indices, create_advantage_distribution_plot, get_episode_data, create_episode_video, create_episode_summary_plot, main | argparse, json, lerobot, matplotlib, numpy, pandas, pathlib, rlinf |
| `examples/recap/value/train_value.py` | 65 | 示例脚本和数据处理；训练流程入口 | - | main | hydra, json, omegaconf, os, rlinf, torch |
| `examples/reward/eval_realworld_teleop.py` | 263 | 示例脚本和数据处理 | RewardInjectionCfg, TeleopWorker | build_reward_injection, main | dataclasses, hydra, json, numpy, omegaconf, rlinf, signal, typing |
| `examples/reward/preprocess_qwentrend_reward_dataset.py` | 776 | 示例脚本和数据处理；奖励计算或奖励模型；数据读取/组织 | - | _compute_sample_indices, _to_scalar, _to_uint8_rgb, _extract_extra_view_image, _extract_dual_view_frames, _build_prompt, _build_messages, _build_reversed_negative_sample, load_episodes_with_labels, balance_and_split_by_episode | argparse, collections, concurrent, glob, json, numpy, os, pickle |
| `examples/reward/preprocess_reward_dataset.py` | 397 | 示例脚本和数据处理；奖励计算或奖励模型；数据读取/组织 | - | _compute_sample_indices, load_episodes_with_labels, balance_and_split_by_episode, preprocess_and_save_reward_datasets, parse_args, main | argparse, glob, json, os, pickle, random, rlinf, torch |
| `examples/reward/realworld_collect_process_dataset.py` | 304 | 示例脚本和数据处理；数据读取/组织 | FrameCollector | main | hydra, json, numpy, os, random, rlinf, torch |
| `examples/reward/train_reward_model.py` | 67 | 示例脚本和数据处理；训练流程入口；奖励计算或奖励模型 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/sft/train_vla_sft.py` | 65 | 示例脚本和数据处理；训练流程入口 | - | main | hydra, json, logging, omegaconf, os, rlinf, torch |
| `examples/sft/train_vlm_sft.py` | 69 | 示例脚本和数据处理；训练流程入口 | - | main | hydra, json, logging, omegaconf, rlinf, torch |
