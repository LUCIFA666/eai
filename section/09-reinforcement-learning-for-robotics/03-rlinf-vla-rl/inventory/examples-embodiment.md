# RLINF 文件索引：examples-embodiment

覆盖 `examples-embodiment` 分组，共 `5` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `examples/embodiment/collect_real_data.py` | 225 | 具身训练示例和启动入口；数据读取/组织 | DataCollector | main | hydra, numpy, os, rlinf, torch, tqdm |
| `examples/embodiment/eval_embodied_agent.py` | 64 | 具身训练示例和启动入口 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/embodiment/train_async.py` | 113 | 具身训练示例和启动入口；训练流程入口 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/embodiment/train_embodied_agent.py` | 104 | 具身训练示例和启动入口；训练流程入口 | - | main | hydra, json, omegaconf, rlinf, torch |
| `examples/embodiment/train_offline_rl.py` | 92 | 具身训练示例和启动入口；训练流程入口 | - | main | hydra, json, omegaconf, rlinf |
