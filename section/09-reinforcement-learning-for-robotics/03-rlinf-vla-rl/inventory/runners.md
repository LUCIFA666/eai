# RLINF 文件索引：runners

覆盖 `runners` 分组，共 `13` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/runners/__init__.py` | 13 | 训练主循环和同步/异步 runner；公共入口/工具 | - | - | - |
| `rlinf/runners/agent_eval_runner.py` | 248 | 训练主循环和同步/异步 runner；训练流程入口 | AgentEvalRunner | - | itertools, logging, omegaconf, rlinf, torch, tqdm, typing |
| `rlinf/runners/agent_runner.py` | 318 | 训练主循环和同步/异步 runner；训练流程入口 | AgentRunner | - | itertools, logging, omegaconf, rlinf, torch, tqdm, typing |
| `rlinf/runners/agentlightning_runner.py` | 420 | 训练主循环和同步/异步 runner；训练流程入口 | AgentLightningRLinfRunner, AgentLightningEvalRunner | - | __future__, logging, omegaconf, os, rlinf, torch, torchdata, tqdm |
| `rlinf/runners/async_embodied_runner.py` | 280 | 训练主循环和同步/异步 runner；训练流程入口 | AsyncEmbodiedRunner | - | asyncio, omegaconf, rlinf, time, typing |
| `rlinf/runners/async_ppo_embodied_runner.py` | 260 | 训练主循环和同步/异步 runner；训练流程入口 | AsyncPPOEmbodiedRunner | - | asyncio, omegaconf, rlinf, time, typing |
| `rlinf/runners/coding_online_rl_runner.py` | 308 | 训练主循环和同步/异步 runner；训练流程入口 | CodingOnlineRLRunner | - | logging, omegaconf, os, pandas, rlinf, tqdm, typing |
| `rlinf/runners/embodied_eval_runner.py` | 83 | 训练主循环和同步/异步 runner；训练流程入口 | EmbodiedEvalRunner | - | rlinf, typing |
| `rlinf/runners/embodied_runner.py` | 488 | 训练主循环和同步/异步 runner；训练流程入口 | EmbodiedRunner | - | collections, logging, omegaconf, os, queue, rlinf, threading, time |
| `rlinf/runners/offline_runner.py` | 368 | 训练主循环和同步/异步 runner；训练流程入口 | OfflineRunner | - | collections, omegaconf, os, queue, rlinf, threading, time, typing |
| `rlinf/runners/reasoning_eval_runner.py` | 179 | 训练主循环和同步/异步 runner；训练流程入口 | ReasoningEvalRunner | - | logging, omegaconf, pandas, rlinf, torch, torchdata, typing |
| `rlinf/runners/reasoning_runner.py` | 646 | 训练主循环和同步/异步 runner；训练流程入口 | ReasoningRunner | - | logging, omegaconf, os, pandas, rlinf, torch, torchdata, tqdm |
| `rlinf/runners/sft_runner.py` | 216 | 训练主循环和同步/异步 runner；训练流程入口 | SFTRunner | - | logging, omegaconf, os, rlinf, tqdm, typing |
