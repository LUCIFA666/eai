# SimpleVLA-RL 文件索引：workers-other

覆盖 `workers-other` 分组，共 `11` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/workers/__init__.py` | 13 | FSDP、reward、hybrid engine 等 worker；公共入口/工具 | - | - | - |
| `verl/workers/fsdp_workers.py` | 1728 | FSDP、reward、hybrid engine 等 worker；远程 worker 执行单元 | RobActorRolloutRefWorker, ActorRolloutRefWorker, CriticWorker, RewardModelWorker, PRIMERewardModelWorker | convert_to_regular_types | codetiming, json, logging, omegaconf, os, peft, ray, torch |
| `verl/workers/hybrid_engine/__init__.py` | 32 | FSDP、reward、hybrid engine 等 worker；公共入口/工具 | - | - | base, verl |
| `verl/workers/hybrid_engine/base.py` | 33 | FSDP、reward、hybrid engine 等 worker | BaseShardingManager | - | verl |
| `verl/workers/hybrid_engine/fsdp_vllm.py` | 105 | FSDP、reward、hybrid engine 等 worker | FSDPVLLMShardingManager | - | base, logging, os, torch, verl |
| `verl/workers/hybrid_engine/megatron_vllm.py` | 428 | FSDP、reward、hybrid engine 等 worker | AllGatherPPModel, MegatronVLLMShardingManager | get_micro_data_parallel_group, get_micro_data_parallel_world_size, get_micro_data_parallel_rank | base, megatron, torch, verl |
| `verl/workers/megatron_workers.py` | 727 | FSDP、reward、hybrid engine 等 worker；远程 worker 执行单元 | ActorRolloutRefWorker, CriticWorker, RewardModelWorker | set_random_seed | logging, megatron, omegaconf, os, ray, torch, verl |
| `verl/workers/reward_model/__init__.py` | 15 | FSDP、reward、hybrid engine 等 worker；公共入口/工具 | - | - | base |
| `verl/workers/reward_model/base.py` | 45 | FSDP、reward、hybrid engine 等 worker | BasePPORewardModel | - | abc, verl |
| `verl/workers/reward_model/megatron/__init__.py` | 15 | FSDP、reward、hybrid engine 等 worker；公共入口/工具 | - | - | reward_model |
| `verl/workers/reward_model/megatron/reward_model.py` | 275 | FSDP、reward、hybrid engine 等 worker；奖励计算或奖励模型 | MegatronRewardModel | - | functools, megatron, tensordict, torch, verl |
