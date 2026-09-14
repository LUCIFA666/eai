# RLINF 文件索引：workers

覆盖 `workers` 分组，共 `50` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/workers/__init__.py` | 13 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | - | - |
| `rlinf/workers/actor/__init__.py` | 30 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | get_actor_worker | omegaconf, rlinf |
| `rlinf/workers/actor/async_fsdp_dagger_policy_worker.py` | 126 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；策略/actor 逻辑 | AsyncEmbodiedDAGGERFSDPPolicy | - | asyncio, queue, rlinf, threading, torch |
| `rlinf/workers/actor/async_fsdp_sac_policy_worker.py` | 138 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；策略/actor 逻辑 | AsyncEmbodiedSACFSDPPolicy | - | asyncio, queue, rlinf, threading, torch |
| `rlinf/workers/actor/async_ppo_fsdp_worker.py` | 366 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | AsyncPPOEmbodiedFSDPActor | flatten_rollout_batch_for_train | numpy, os, rlinf, torch, typing |
| `rlinf/workers/actor/fsdp_actor_worker.py` | 1510 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；策略/actor 逻辑 | FSDPActor, EmbodiedFSDPActor | process_nested_dict_for_adv, process_nested_dict_for_train | functools, numpy, omegaconf, os, rlinf, time, torch, typing |
| `rlinf/workers/actor/fsdp_dagger_policy_worker.py` | 268 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；策略/actor 逻辑 | EmbodiedDAGGERFSDPPolicy | - | numpy, omegaconf, os, rlinf, torch |
| `rlinf/workers/actor/fsdp_iql_policy_worker.py` | 1008 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；策略/actor 逻辑 | EmbodiedIQLFSDPPolicy | iql_expectile_loss | numpy, omegaconf, os, rlinf, torch, typing |
| `rlinf/workers/actor/fsdp_nft_policy_worker.py` | 622 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；策略/actor 逻辑 | EmbodiedNFTFSDPPolicy | - | numpy, omegaconf, os, rlinf, torch |
| `rlinf/workers/actor/fsdp_sac_policy_worker.py` | 841 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；策略/actor 逻辑 | EmbodiedSACFSDPPolicy | - | numpy, omegaconf, os, rlinf, torch, typing |
| `rlinf/workers/actor/ma_megatron_actor_worker.py` | 605 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；策略/actor 逻辑 | MAMegatronActor | - | copy, megatron, omegaconf, rlinf, torch, typing |
| `rlinf/workers/actor/megatron_actor_worker.py` | 408 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；策略/actor 逻辑 | MegatronActor | - | copy, megatron, omegaconf, rlinf, torch |
| `rlinf/workers/agent/__init__.py` | 13 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | - | - |
| `rlinf/workers/agent/agent_loop.py` | 740 | actor、env、rollout、reward、sft 等 worker | AgentLoopOutput, MultiAgentLoopOutput, AgentLoopWorker, MultiAgentLoopWorker | - | asyncio, copy, dataclasses, json, omegaconf, rlinf, transformers, typing |
| `rlinf/workers/agent/agentlightning_rollout_worker.py` | 515 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | AgentLightningRolloutWorker | - | __future__, logging, numpy, omegaconf, os, rlinf, torch, typing |
| `rlinf/workers/agent/tool_worker.py` | 43 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | ToolWorkerInfo, ToolChannelInfo, ToolWorker | - | dataclasses, rlinf |
| `rlinf/workers/critic/__init__.py` | 26 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | get_critic_worker | omegaconf, rlinf |
| `rlinf/workers/critic/megatron_critic_worker.py` | 112 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | MegatronCritic | - | copy, megatron, omegaconf, rlinf |
| `rlinf/workers/env/__init__.py` | 13 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | - | - |
| `rlinf/workers/env/async_env_worker.py` | 85 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；环境适配 | AsyncEnvWorker | - | asyncio, omegaconf, rlinf |
| `rlinf/workers/env/env_worker.py` | 1286 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；环境适配 | EnvWorker | - | asyncio, collections, gc, numpy, omegaconf, rlinf, torch, typing |
| `rlinf/workers/env/history_manager.py` | 200 | actor、env、rollout、reward、sft 等 worker | HistoryManager | - | __future__, logging, omegaconf, rlinf, torch, typing |
| `rlinf/workers/inference/__init__.py` | 13 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | - | - |
| `rlinf/workers/inference/fsdp_inference_worker.py` | 146 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | FSDPInference | - | omegaconf, rlinf, torch |
| `rlinf/workers/inference/megatron_inference_worker.py` | 129 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | - | make_megatron_inference | actor, copy, critic, omegaconf, rlinf |
| `rlinf/workers/inference/utils.py` | 73 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | get_inference_backend_worker | omegaconf, typing |
| `rlinf/workers/megatron_worker.py` | 1341 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | MegatronWorker | - | functools, megatron, omegaconf, rlinf, time, torch, typing |
| `rlinf/workers/reward/__init__.py` | 27 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | - | rlinf |
| `rlinf/workers/reward/reward_worker.py` | 660 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元；奖励计算或奖励模型 | RewardWorker, EmbodiedRewardWorker, FSDPRewardWorker | - | asyncio, numpy, omegaconf, os, rlinf, torch, typing |
| `rlinf/workers/rollout/__init__.py` | 13 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | - | - |
| `rlinf/workers/rollout/hf/__init__.py` | 13 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | - | - |
| `rlinf/workers/rollout/hf/async_huggingface_worker.py` | 143 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | AsyncMultiStepRolloutWorker | - | asyncio, omegaconf, rlinf |
| `rlinf/workers/rollout/hf/huggingface_worker.py` | 685 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | MultiStepRolloutWorker | - | copy, gc, numpy, omegaconf, rlinf, torch, tqdm, typing |
| `rlinf/workers/rollout/server/__init__.py` | 13 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | - | - |
| `rlinf/workers/rollout/server/online_router_worker.py` | 259 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | CompleteRequest, CompleteResponse, OnlineRouterWorker | - | asyncio, copy, fastapi, json, omegaconf, pydantic, random, rlinf |
| `rlinf/workers/rollout/server/server_rollout_worker.py` | 378 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | TrainingDataStorage, ServerRolloutWorker | - | asyncio, datetime, fastapi, json, omegaconf, pathlib, rlinf, time |
| `rlinf/workers/rollout/sglang/__init__.py` | 43 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | get_version | importlib, packaging |
| `rlinf/workers/rollout/sglang/sglang_worker.py` | 511 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | SGLangWorker | - | asyncio, copy, dataclasses, omegaconf, rlinf, sglang, transformers, typing |
| `rlinf/workers/rollout/sglang/sglang_worker_server.py` | 265 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | SGLangWorkerWithHTTPServer | _patch_chat_body_assistant_content | asyncio, fastapi, omegaconf, rlinf, starlette, time, typing, uvicorn |
| `rlinf/workers/rollout/utils.py` | 577 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | RankMapper, CollocateRankMapper, DisaggRankMapper, RunningStatusManager, RolloutEngineStats, MetaInfoStatsCollector | green, sharp_cover, print_vllm_outputs, print_multi_outputs, print_sglang_outputs, print_multi_sglang_outputs, get_rollout_backend_worker | asyncio, contextlib, dataclasses, json, omegaconf, os, rlinf, time |
| `rlinf/workers/rollout/vllm/__init__.py` | 41 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | get_version | importlib, packaging |
| `rlinf/workers/rollout/vllm/vllm_worker.py` | 508 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | VLLMWorker | - | PIL, asyncio, copy, functools, omegaconf, os, rlinf, transformers |
| `rlinf/workers/sft/__init__.py` | 13 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | - | - |
| `rlinf/workers/sft/fsdp_cfg_worker.py` | 566 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | FSDPCfgWorker | - | __future__, numpy, omegaconf, os, pathlib, rlinf, torch, typing |
| `rlinf/workers/sft/fsdp_sft_worker.py` | 218 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | FSDPSftWorker | - | abc, logging, numpy, omegaconf, os, rlinf, torch, tqdm |
| `rlinf/workers/sft/fsdp_value_sft_worker.py` | 751 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | FSDPValueSftWorker | - | numpy, omegaconf, os, pathlib, rlinf, torch |
| `rlinf/workers/sft/fsdp_vla_sft_worker.py` | 196 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | FSDPVlaSftWorker | - | omegaconf, os, rlinf, torch, torchdata, typing |
| `rlinf/workers/sft/fsdp_vlm_sft_worker.py` | 237 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | FSDPVlmSftWorker | - | json, logging, omegaconf, os, rlinf, torch, typing |
| `rlinf/workers/sft/megatron_vlm_sft_worker.py` | 450 | actor、env、rollout、reward、sft 等 worker；远程 worker 执行单元 | MegatronSftWorker, MegatronVlmSftWorker | - | abc, json, logging, omegaconf, os, rlinf, torch, typing |
| `rlinf/workers/sft/utils.py` | 111 | actor、env、rollout、reward、sft 等 worker；公共入口/工具 | - | _extract_boxed, vlm_extract_answer, vlm_normalize_text | re, rlinf |
