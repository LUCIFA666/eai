# RLINF 文件索引：toolkits

覆盖 `toolkits` 分组，共 `28` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `toolkits/__init__.py` | 13 | 真机检查、checkpoint 转换、评估和辅助工具；公共入口/工具 | - | - | - |
| `toolkits/auto_placement/__init__.py` | 13 | 真机检查、checkpoint 转换、评估和辅助工具；公共入口/工具 | - | - | - |
| `toolkits/auto_placement/auto_placement_worker.py` | 241 | 真机检查、checkpoint 转换、评估和辅助工具；远程 worker 执行单元 | AutoPlacementWorker | get_workflow_graph, main | hydra, logging, node, placement, rlinf, typing, util, workflow |
| `toolkits/auto_placement/fitter.py` | 169 | 真机检查、checkpoint 转换、评估和辅助工具 | DataFitter | - | numpy, scipy, warnings |
| `toolkits/auto_placement/node.py` | 211 | 真机检查、checkpoint 转换、评估和辅助工具 | ComponentNode, MegatronNode, RolloutNode, EnvProfiler, EnvNode, EnvRolloutNode, SccNode | - | abc, fitter, math, typing, util |
| `toolkits/auto_placement/placement.py` | 247 | 真机检查、checkpoint 转换、评估和辅助工具 | ScheduleMode, ScheduleResult, SingleNodeScheduleResult, CollocatedScheduleResult, DisaggregatedScheduleResult | - | abc, enum, node, typing, util |
| `toolkits/auto_placement/util.py` | 132 | 真机检查、checkpoint 转换、评估和辅助工具 | - | init_global_config, init_global_config_reasoning, init_global_config_env, get_global_config, get_valid_gpu_num_list | argparse |
| `toolkits/auto_placement/workflow.py` | 234 | 真机检查、checkpoint 转换、评估和辅助工具 | Workflow | traverse_st_cuts | collections, node, typing |
| `toolkits/eval_scripts_dexbotic/__init__.py` | 288 | 真机检查、checkpoint 转换、评估和辅助工具；公共入口/工具 | BaseDexboticPolicy, DexboticPI0Policy, DM0Policy | setup_logger, setup_policy | PIL, dexbotic, json, logging, numpy, os, torch, transformers |
| `toolkits/eval_scripts_dexbotic/libero_eval.py` | 320 | 真机检查、checkpoint 转换、评估和辅助工具 | - | _quat2axisangle, _get_libero_env, main | collections, imageio, libero, math, numpy, os, pathlib, toolkits |
| `toolkits/eval_scripts_openpi/__init__.py` | 145 | 真机检查、checkpoint 转换、评估和辅助工具；公共入口/工具 | - | setup_logger, load_pytorch, create_trained_policy, setup_policy | logging, openpi, os, pathlib, rlinf, safetensors, typing |
| `toolkits/eval_scripts_openpi/calvin_eval.py` | 224 | 真机检查、checkpoint 转换、评估和辅助工具 | - | _calvin_print_performance, main | calvin_agent, calvin_env, collections, imageio, numpy, pathlib, rlinf, toolkits |
| `toolkits/eval_scripts_openpi/libero_eval.py` | 314 | 真机检查、checkpoint 转换、评估和辅助工具 | - | _quat2axisangle, _get_libero_env, main | collections, imageio, libero, math, numpy, os, pathlib, toolkits |
| `toolkits/eval_scripts_openpi/metaworld_eval.py` | 231 | 真机检查、checkpoint 转换、评估和辅助工具 | - | load_prompt_from_json, main | collections, gymnasium, imageio, json, metaworld, numpy, os, pathlib |
| `toolkits/lerobot/calculate_norm_stats.py` | 151 | 真机检查、checkpoint 转换、评估和辅助工具 | RemoveStrings | create_torch_dataloader, create_rlds_dataloader, main | numpy, openpi, os, rlinf, tqdm, tyro |
| `toolkits/lerobot/merge_lerobot_datasets.py` | 436 | 真机检查、checkpoint 转换、评估和辅助工具；数据读取/组织 | - | _is_lerobot_dataset, _discover_datasets, _read_jsonl, _write_jsonl, _reindex_episode_stats, _ensure_list, merge_lerobot_datasets, _build_parser, main | __future__, argparse, json, pathlib, sys, typing |
| `toolkits/lerobot/visualize_lerobot_dataset.py` | 339 | 真机检查、checkpoint 转换、评估和辅助工具；数据读取/组织 | - | _build_arg_parser, _require_pyarrow, _require_pillow, _load_json, _load_jsonl, _resolve_parquet_files, _build_episode_meta_map, _build_task_map, _infer_episode_index, _is_image_struct | __future__, argparse, io, json, pathlib, re, sys, typing |
| `toolkits/realworld_check/test_dosw1_controller.py` | 194 | 真机检查、checkpoint 转换、评估和辅助工具 | - | _parse_args, _build_config, _compute_teleop_targets, _fmt, main | argparse, math, numpy, rlinf, time |
| `toolkits/realworld_check/test_franka_camera.py` | 45 | 真机检查、checkpoint 转换、评估和辅助工具 | - | main | pyrealsense2, time |
| `toolkits/realworld_check/test_franka_controller.py` | 113 | 真机检查、checkpoint 转换、评估和辅助工具 | - | _parse_args, main | argparse, numpy, os, rlinf, scipy, time |
| `toolkits/realworld_check/test_gim_arm_env.py` | 265 | 真机检查、checkpoint 转换、评估和辅助工具；环境适配 | - | main | argparse, numpy, time |
| `toolkits/realworld_check/test_lumos_camera.py` | 84 | 真机检查、checkpoint 转换、评估和辅助工具 | - | main | argparse, numpy, rlinf, time |
| `toolkits/realworld_check/test_robotiq_gripper.py` | 73 | 真机检查、checkpoint 转换、评估和辅助工具 | - | main | argparse, time |
| `toolkits/realworld_check/test_turtle2_controller.py` | 53 | 真机检查、checkpoint 转换、评估和辅助工具 | - | main | rlinf, time |
| `toolkits/realworld_check/test_zed_camera.py` | 92 | 真机检查、checkpoint 转换、评估和辅助工具 | - | main | argparse, numpy, time |
| `toolkits/replay_buffer/merge_or_split_replay_buffer.py` | 297 | 真机检查、checkpoint 转换、评估和辅助工具 | - | _load_json, _find_index_path, _normalize_index_data, _resolve_trajectory_path, merge_replay_buffers, split_replay_buffer, main | argparse, glob, json, os, shutil |
| `toolkits/replay_buffer/visualize.py` | 444 | 真机检查、checkpoint 转换、评估和辅助工具 | MultiTrajectoryVisualizer | main | argparse, matplotlib, numpy, pathlib, rlinf, torch, typing |
| `toolkits/replay_buffer/visualize_headless.py` | 145 | 真机检查、checkpoint 转换、评估和辅助工具 | - | main | argparse, matplotlib, visualize |
