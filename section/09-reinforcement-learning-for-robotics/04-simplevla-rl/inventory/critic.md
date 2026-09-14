# SimpleVLA-RL 文件索引：critic

覆盖 `critic` 分组，共 `4` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/workers/critic/__init__.py` | 18 | critic/value 更新 worker；公共入口/工具 | - | - | base, dp_critic |
| `verl/workers/critic/base.py` | 40 | critic/value 更新 worker | BasePPOCritic | - | abc, torch, verl |
| `verl/workers/critic/dp_critic.py` | 139 | critic/value 更新 worker | DataParallelPPOCritic | - | torch, typing, verl |
| `verl/workers/critic/megatron_critic.py` | 229 | critic/value 更新 worker | MegatronPPOCritic | - | functools, megatron, omegaconf, torch, typing, verl |
