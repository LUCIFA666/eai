# RLINF 文件索引：agents

覆盖 `agents` 分组，共 `24` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/agents/__init__.py` | 13 | Agentic rollout/工具调用实现；公共入口/工具 | - | - | - |
| `rlinf/agents/agentlightning/__init__.py` | 28 | Agentic rollout/工具调用实现；公共入口/工具 | - | __getattr__ | typing |
| `rlinf/agents/agentlightning/algorithm.py` | 89 | Agentic rollout/工具调用实现 | - | _make_rlinf_class, __getattr__ | __future__, omegaconf, typing |
| `rlinf/agents/agentlightning/entrypoint.py` | 128 | Agentic rollout/工具调用实现 | - | run_rlinf_training | __future__, omegaconf, rlinf, typing |
| `rlinf/agents/rstar2/__init__.py` | 13 | Agentic rollout/工具调用实现；公共入口/工具 | - | - | - |
| `rlinf/agents/rstar2/http_code_judge_tool.py` | 331 | Agentic rollout/工具调用实现 | ToolBase, CodeJudgeToolBase, PythonTool | - | base64, rlinf, time, typing |
| `rlinf/agents/rstar2/http_tool_worker.py` | 176 | Agentic rollout/工具调用实现；远程 worker 执行单元 | HttpToolWorker | - | aiohttp, asyncio, logging, omegaconf, rlinf |
| `rlinf/agents/rstar2/rstar2_agent_loop.py` | 324 | Agentic rollout/工具调用实现 | Rstar2AgentLoopWorker | - | asyncio, json, omegaconf, rlinf, typing, uuid |
| `rlinf/agents/searchr1/__init__.py` | 13 | Agentic rollout/工具调用实现；公共入口/工具 | - | - | - |
| `rlinf/agents/searchr1/eval_runner.py` | 247 | Agentic rollout/工具调用实现；训练流程入口 | Searchr1AgentEvalRunner | - | datetime, json, logging, omegaconf, os, rlinf, torch, typing |
| `rlinf/agents/searchr1/search_tool_worker.py` | 157 | Agentic rollout/工具调用实现；远程 worker 执行单元 | AsyncSearchClient, SearchToolWorker | - | aiohttp, asyncio, omegaconf, rlinf, typing |
| `rlinf/agents/searchr1/searchr1_agent_loop.py` | 220 | Agentic rollout/工具调用实现 | Searchr1AgentLoopWorker | - | asyncio, copy, omegaconf, rlinf, typing |
| `rlinf/agents/wideseek_r1/__init__.py` | 13 | Agentic rollout/工具调用实现；公共入口/工具 | - | - | - |
| `rlinf/agents/wideseek_r1/eval_runner.py` | 609 | Agentic rollout/工具调用实现；训练流程入口 | WideSeekR1AgentEvalRunner | - | datetime, json, logging, omegaconf, os, pandas, rlinf, torch |
| `rlinf/agents/wideseek_r1/tools.py` | 784 | Agentic rollout/工具调用实现 | AsyncOnlineSearchClient, AsyncSearchClient, WideSeekR1ToolWorker | - | aiohttp, asyncio, json, logging, omegaconf, os, random, rlinf |
| `rlinf/agents/wideseek_r1/utils/__init__.py` | 13 | Agentic rollout/工具调用实现；公共入口/工具 | - | - | - |
| `rlinf/agents/wideseek_r1/utils/metrics.py` | 186 | Agentic rollout/工具调用实现 | - | _safe_max, _add_weighted_mean_metric, _compute_tool_call_metrics, _compute_mas_turn_metrics, _compute_final_answer_format_metrics, _compute_rollout_metrics | - |
| `rlinf/agents/wideseek_r1/utils/prompt.py` | 529 | Agentic rollout/工具调用实现 | - | - | - |
| `rlinf/agents/wideseek_r1/utils/prompt_utils.py` | 261 | Agentic rollout/工具调用实现；公共入口/工具 | - | get_prompt_planner, get_prompt_planner_en, get_prompt_planner_zh, get_prompt_worker, get_prompt_single_agent, get_prompt_single_agent_en, get_prompt_single_agent_zh, get_access_summary_messages, get_first_turn_hint, get_next_turn_hint | rlinf |
| `rlinf/agents/wideseek_r1/utils/reward.py` | 689 | Agentic rollout/工具调用实现；奖励计算或奖励模型 | - | credit_assignment, get_final_reward_score, verify_answer_with_llm_judge, evaluate_markdown, llm_judge_column, primary_key_preprocess, extract_final_answer | asyncio, copy, io, json, omegaconf, pandas, re, rlinf |
| `rlinf/agents/wideseek_r1/utils/sglang_client.py` | 144 | Agentic rollout/工具调用实现 | SGLangClient | _main | aiohttp, argparse, asyncio, threading |
| `rlinf/agents/wideseek_r1/utils/tool_description.py` | 285 | Agentic rollout/工具调用实现 | - | - | - |
| `rlinf/agents/wideseek_r1/utils/webpage.py` | 192 | Agentic rollout/工具调用实现 | WebPageCache | - | atexit, collections, hashlib, json, os, threading, time, typing |
| `rlinf/agents/wideseek_r1/wideseek_r1.py` | 867 | Agentic rollout/工具调用实现 | WideSeekR1AgentLoopWorker | - | asyncio, copy, omegaconf, rlinf, typing |
