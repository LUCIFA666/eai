# SimpleVLA-RL 文件索引：actor

覆盖 `actor` 分组，共 `6` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/workers/actor/__init__.py` | 20 | PPO actor、logprob、entropy 和 policy update；公共入口/工具 | - | - | base, dp_actor, dp_prime, dp_rob |
| `verl/workers/actor/base.py` | 66 | PPO actor、logprob、entropy 和 policy update | BasePPOActor | - | abc, torch, typing, verl |
| `verl/workers/actor/dp_actor.py` | 418 | PPO actor、logprob、entropy 和 policy update；策略/actor 逻辑 | DataParallelPPOActor | - | flash_attn, itertools, torch, typing, verl |
| `verl/workers/actor/dp_prime.py` | 284 | PPO actor、logprob、entropy 和 policy update | DataParallelPRIME | - | flash_attn, itertools, torch, typing, verl |
| `verl/workers/actor/dp_rob.py` | 607 | PPO actor、logprob、entropy 和 policy update | RobDataParallelPPOActor | - | codetiming, flash_attn, itertools, torch, typing, verl |
| `verl/workers/actor/megatron_actor.py` | 368 | PPO actor、logprob、entropy 和 policy update；策略/actor 逻辑 | MegatronPPOActor | - | functools, megatron, omegaconf, torch, typing, verl |
