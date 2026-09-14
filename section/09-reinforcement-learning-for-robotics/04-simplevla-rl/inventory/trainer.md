# SimpleVLA-RL 文件索引：trainer

覆盖 `trainer` 分组，共 `8` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/trainer/__init__.py` | 13 | PPO/评测/SFT 训练入口和主循环；公共入口/工具 | - | - | - |
| `verl/trainer/fsdp_sft_trainer.py` | 362 | PPO/评测/SFT 训练入口和主循环；训练流程入口 | FSDPSFTTrainer | extract_step, main | hydra, logging, os, re, tensordict, torch, transformers, verl |
| `verl/trainer/main_eval.py` | 69 | PPO/评测/SFT 训练入口和主循环 | - | select_reward_fn, main | hydra, numpy, pandas, verl |
| `verl/trainer/main_generation.py` | 137 | PPO/评测/SFT 训练入口和主循环 | - | main | hydra, numpy, os, pandas, ray, transformers, verl |
| `verl/trainer/main_ppo.py` | 212 | PPO/评测/SFT 训练入口和主循环 | RobRewardManager | main, main_task | functools, hydra, json, os, ray, statistics, torch, verl |
| `verl/trainer/ppo/__init__.py` | 13 | PPO/评测/SFT 训练入口和主循环；公共入口/工具 | - | - | - |
| `verl/trainer/ppo/core_algos.py` | 407 | PPO/评测/SFT 训练入口和主循环 | AdaptiveKLController, FixedKLController | get_kl_controller, compute_gae_advantage_return, compute_reinforce_plus_plus_outcome_advantage, compute_remax_outcome_advantage, compute_grpo_outcome_advantage, compute_rloo_returns, compute_rewards, compute_policy_loss, compute_entropy_loss, compute_value_loss | collections, numpy, torch, verl |
| `verl/trainer/ppo/ray_trainer.py` | 829 | PPO/评测/SFT 训练入口和主循环；训练流程入口 | Role, ResourcePoolManager, RayTrainer | apply_kl_penalty, compute_advantage, reduce_metrics, compute_data_metrics | codetiming, collections, dataclasses, enum, functools, numpy, omegaconf, os |
