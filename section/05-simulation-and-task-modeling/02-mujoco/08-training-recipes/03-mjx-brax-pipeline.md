# MJX + Brax 管线

CPU 训 CartPole 已经够快，但到 Humanoid 这种规模就比较吃力了。GPU 路径用 MJX 当仿真后端、Brax（Google 的 JAX 原生 RL 训练库）当训练框架，能在一张显卡上把成千上万个环境一起推进。

## 本节目标

本节回答几个问题：

1. Brax 是什么，和 MJX 是什么关系？
2. 怎么把一个 MJX 环境接入 Brax PPO 训练？
3. GPU 训练的耗时量级和常见的坑有哪些？

## Brax 简介

Brax 是 Google 开发的一个 JAX 原生物理仿真和 RL 训练库。它的核心思路和 MJX 一样，用 JAX 让仿真和训练都可以被 jit 编译和 vmap 向量化，从而在 GPU/TPU 上大规模并行。

Brax 和 MJX 的关系：**Brax 既是一个训练框架（内置 PPO/SAC 等算法），也可以接入 MJX 作为其仿真后端。** 简单说，Brax 管训练，MJX 管仿真。

> 时效提示：按 Brax 官方说明，目前只有训练部分（`brax/training`）仍在积极维护，自带的环境（`brax/envs`）已不再主推，新项目建议改用 `mujoco_playground`（同样基于 MJX、维护更活跃的环境集合，仍然配合 `brax/training` 训练）。下面这条 PPO 入门流程属于 `brax/training`，依旧完全可用。

```bash
pip install brax
```

## MJX + Brax 最小配置

```python
import jax
from brax import envs
from brax.training.agents.ppo import train as ppo
from brax.io import model

# 取 MJX 后端的原始环境，交给 ppo.train（训练所需的 episode/vmap 等包装由它内部完成）
env_name = "ant"  # 或 "humanoid", "halfcheetah" 等
env = envs.get_environment(env_name, backend="mjx")

# 训练：ppo.train 内部完成 jit 编译和 GPU 批量 rollout。
# 这组超参与 labs/04-simulation/mjx_brax_ppo_ant.py 一致，也就是后文展示日志所用的配置；
# 那份逐次 eval 的 reward 日志，是 lab 脚本额外传了一个 progress_fn 回调打印出来的。
make_policy, params, metrics = ppo.train(
    environment=env,
    num_timesteps=50_000_000,    # 5000 万步
    num_evals=10,
    reward_scaling=0.1,
    episode_length=1000,
    normalize_observations=True,
    action_repeat=1,
    unroll_length=5,             # 每次 rollout 收集多少步再更新
    num_minibatches=32,
    num_updates_per_batch=4,
    discounting=0.97,
    learning_rate=3e-4,
    entropy_cost=1e-2,
    num_envs=4096,               # 关键参数：并行环境数
    batch_size=1024,
    seed=0,
)

# 保存策略
model.save_params("policy.params", params)
```

> Brax 的训练 API 随版本有调整（例如 PPO 从早期的 `brax.training.ppo` 迁到了 `brax.training.agents.ppo`，模型读写在 `brax.io.model`）。import 报错时，以官方 Brax 示例为准。

Brax 的 API 参数较多，但大多数有合理的默认值。核心是需要理解几个关键参数：
- `num_envs`：并行环境数（GPU 上可以开 4096+）。
- `num_timesteps`：总训练步数（注意是环境交互的总步数，不是 wall-clock 步数）。
- `unroll_length`：每次 rollout 收集多少步再更新一次。
- `normalize_observations`：是否对观测做滑动归一化。大 batch 训练里通常开启，对收敛帮助明显，这条管线就是开着的。

## 训练时间参考

| 任务 | 训练步数 | GPU（单卡，4096 envs） | CPU (32 cores) |
|---|---|---|---|
| Ant | 50M | ~2.5 分钟 | ~2 小时 |
| Humanoid | 100M | ~15 分钟 | ~6-8 小时 |
| HalfCheetah | 30M | ~2 分钟 | ~1 小时 |

这些数字只是近似值（Ant 的 GPU 一格有下方实测支撑，CPU 列未实测、是量级估计），实际时间因硬件和超参而异。大致可以这样理解：在 GPU 上，本来需要几小时的训练往往能压缩到几十分钟。

## 实测：Ant 训练确实收敛（单张 RTX 4090）

用上面这条管线训 brax 的 Ant（`backend="mjx"`、`num_envs=4096`、跑满 5000 万步），整段 wall-clock 约 2.5 分钟，eval reward 的进展如下（摘自逐次 eval 记录 `runs/04-simulation/mjx_brax_ppo_ant_metrics.json`，四舍五入到一位小数；脚本 `labs/04-simulation/mjx_brax_ppo_ant.py`，最终汇总见 `mjx_brax_ppo_ant.txt`）：

```text
step            0   eval_reward =   -21.5
step    5,570,560   eval_reward =   338.5
step   11,141,120   eval_reward =  1439.6
step   16,711,680   eval_reward =  2896.1
step   22,282,240   eval_reward =  3315.4
step   27,852,800   eval_reward =  3561.4
step   33,423,360   eval_reward =  3655.5
step   38,993,920   eval_reward =  3735.4
step   44,564,480   eval_reward =  3684.4
step   50,135,040   eval_reward =  3643.4
```

reward 从初始随机策略的约 -21 一路升到 3600+，说明这条 MJX + Brax 管线能正常训练、Ant 学会了稳定前进。单张 4090 上 5000 万步只要两三分钟，正是 GPU 批量仿真的价值所在。想更快冒烟可以把 `num_timesteps` 调小（如 3M）。

## GPU 路径常见问题

| 现象 | 可能原因 | 处理 |
|---|---|---|
| OOM（显存不足） | 并行环境数太多 | 减少 `num_envs`，或减小 `unroll_length` |
| 训练很慢，GPU 利用率低 | jit 频繁重新编译 | 确保不要修改任何被 jit 编译的函数签名（shape/dtype 变化会导致重编译） |
| 训练不收敛 | 超参不适合 GPU 的大 batch | GPU 训练的 batch 远大于 CPU，可能需要调整 learning rate 和 entropy coefficient |
| JAX 报错 `ConcretizationTypeError` | 在 jit 函数内部使用了 Python 控制流 | 用 `jax.lax.cond` 代替 `if`，用 `jax.lax.scan` 代替 `for` |

## 小结

- Brax 是 JAX 原生的 RL 训练库，MJX 是 MuJoCo 的 JAX 仿真后端，两者可以无缝对接。
- GPU 路径（MJX + Brax）在 Humanoid 等级别的任务上，量级上能比 CPU 快十几到几十倍（确切倍数随硬件和超参浮动，见上方训练时间表）。
- 常见问题：OOM（减环境数）、jit 重编译（保持 shape/dtype 稳定）、超参适配（GPU 大 batch 需要调 LR）。

## 参考资料

- [Brax（GitHub，brax.training.agents.ppo）](https://github.com/google/brax)
- [Brax 官方 PPO 训练 Notebook（google/brax, notebooks/training.ipynb）](https://github.com/google/brax/blob/main/notebooks/training.ipynb)
- [Freeman et al., "Brax: A Differentiable Physics Engine for Large Scale Rigid Body Simulation", 2021](https://arxiv.org/abs/2106.13281)
- [MuJoCo Documentation: MJX](https://mujoco.readthedocs.io/en/stable/mjx.html)
- [MuJoCo Playground（GitHub）](https://github.com/google-deepmind/mujoco_playground)

## 导航

- 上一节：[CartPole + SB3](02-cartpole-with-sb3.md)
- 返回上级：[训练教程](../08-training-recipes.md)
- 下一节：[行为克隆入门](04-imitation-from-demo.md)
