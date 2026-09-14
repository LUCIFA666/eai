# RLINF 文件索引：examples-agent

覆盖 `examples-agent` 分组，共 `19` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `examples/agent/agentlightning/calc_x/calc_agent.py` | 122 | Agentic RL 示例 | MathProblem | autogen_assistant_agent, calc_agent | agentlightning, asyncio, autogen_agentchat, autogen_core, autogen_ext, eval_utils, logging, os |
| `examples/agent/agentlightning/calc_x/eval_utils.py` | 78 | Agentic RL 示例；公共入口/工具 | - | normalize_option, is_option_result, float_eval, compare_are_results_same, evaluate | math, re, string, sympy |
| `examples/agent/agentlightning/calc_x/main.py` | 85 | Agentic RL 示例 | - | _find_available_port, train, main | agentlightning, calc_agent, datasets, hydra, rlinf, socket, typing |
| `examples/agent/coding_online_rl/main_coding_online_rl.py` | 106 | Agentic RL 示例 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/agent/coding_online_rl/main_coding_rl_llm_judge.py` | 105 | Agentic RL 示例 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/agent/coding_online_rl/simple_online_coding_client.py` | 110 | Agentic RL 示例 | - | agenerate, atrack, single_iteration, loop | asyncio, datetime, httpx, uuid |
| `examples/agent/rstar2/data_process/process_train_dataset.py` | 67 | Agentic RL 示例；训练流程入口；数据读取/组织 | - | - | datasets, json, os |
| `examples/agent/rstar2/main_rstar2.py` | 142 | Agentic RL 示例 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/agent/searchr1/__init__.py` | 13 | Agentic RL 示例；公共入口/工具 | - | - | - |
| `examples/agent/searchr1/download.py` | 45 | Agentic RL 示例 | - | - | argparse, huggingface_hub |
| `examples/agent/searchr1/eval.py` | 103 | Agentic RL 示例 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/agent/searchr1/train.py` | 127 | Agentic RL 示例；训练流程入口 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/agent/tools/search_local_server_faiss/index_builder.py` | 364 | Agentic RL 示例 | Index_Builder | load_model, pooling, load_corpus, main | argparse, datasets, faiss, numpy, os, shutil, subprocess, torch |
| `examples/agent/tools/search_local_server_faiss/local_retrieval_server.py` | 547 | Agentic RL 示例 | Encoder, BaseRetriever, BM25Retriever, DenseRetriever, PageAccess, Config, QueryRequest, AccessRequest | load_corpus, read_jsonl, load_docs, load_model, pooling, get_retriever, retrieve_endpoint, access_endpoint | argparse, datasets, faiss, fastapi, json, numpy, os, pydantic |
| `examples/agent/tools/search_local_server_qdrant/build_index.py` | 387 | Agentic RL 示例 | QdrantIndexBuilder, Config | set_global, load_corpus, read_jsonl, load_docs | argparse, datasets, json, logging, qdrant_client, qdrant_encoder, queue, time |
| `examples/agent/tools/search_local_server_qdrant/local_retrieval_server.py` | 491 | Agentic RL 示例 | AsyncEncoderPool, AsyncBaseRetriever, AsyncDenseRetriever, PageAccess, Config, QueryRequest, AccessRequest | get_retriever, retrieve_endpoint, access_endpoint | argparse, asyncio, concurrent, fastapi, json, logging, multiprocessing, numpy |
| `examples/agent/tools/search_local_server_qdrant/qdrant_encoder.py` | 121 | Agentic RL 示例 | Encoder | load_model, pooling | numpy, torch, transformers, typing |
| `examples/agent/wideseek_r1/eval.py` | 204 | Agentic RL 示例 | - | main | hydra, json, logging, omegaconf, rlinf, torch |
| `examples/agent/wideseek_r1/train.py` | 153 | Agentic RL 示例；训练流程入口 | - | main | hydra, json, logging, omegaconf, rlinf, torch |
