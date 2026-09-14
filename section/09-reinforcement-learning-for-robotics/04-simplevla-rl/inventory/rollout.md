# SimpleVLA-RL 文件索引：rollout

覆盖 `rollout` 分组，共 `10` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/workers/rollout/__init__.py` | 20 | VLA rollout、环境交互和采样；公共入口/工具 | - | - | base, hf_rollout, naive, rob_rollout |
| `verl/workers/rollout/base.py` | 37 | VLA rollout、环境交互和采样 | BaseRollout | - | abc, typing |
| `verl/workers/rollout/hf_rollout.py` | 140 | VLA rollout、环境交互和采样 | HFRollout | - | base, contextlib, tensordict, torch, transformers, verl |
| `verl/workers/rollout/naive/__init__.py` | 15 | VLA rollout、环境交互和采样；公共入口/工具 | - | - | naive_rollout |
| `verl/workers/rollout/naive/naive_rollout.py` | 119 | VLA rollout、环境交互和采样 | NaiveRollout | - | base, tensordict, torch, typing, verl |
| `verl/workers/rollout/pre_collect_twin2_seed.py` | 485 | VLA rollout、环境交互和采样 | - | get_robotwin2_task, collect_success_seeds_worker, collect_success_seeds_for_task_parallel, save_results, main, print_final_summary | PIL, codetiming, contextlib, datetime, importlib, json, numpy, os |
| `verl/workers/rollout/rob_rollout.py` | 1131 | VLA rollout、环境交互和采样 | RobotwinEnvWrapper, RobHFRollout | crop_and_resize, center_crop_image, normalize_proprio, get_robotwin2_task, encode_obs, env_worker | PIL, base, codetiming, collections, concurrent, contextlib, gc, importlib |
| `verl/workers/rollout/tokenizer.py` | 162 | VLA rollout、环境交互和采样 | HybridEngineBaseTokenizer | - | abc, typing |
| `verl/workers/rollout/vllm_rollout/__init__.py` | 15 | VLA rollout、环境交互和采样；公共入口/工具 | - | - | vllm_rollout |
| `verl/workers/rollout/vllm_rollout/vllm_rollout.py` | 219 | VLA rollout、环境交互和采样 | vLLMRollout | _pre_process_inputs | contextlib, omegaconf, tensordict, torch, typing, verl, vllm |
