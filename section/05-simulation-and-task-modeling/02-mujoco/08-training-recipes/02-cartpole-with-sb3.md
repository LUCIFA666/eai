# CartPole + SB3：最简 CPU 路径

这一页给一个成本较低、能跑通一次完整训练的配方：dm_control 的 cartpole，加上 Gymnasium 包装，再加上 Stable-Baselines3 的 PPO。一台普通笔记本大致十分钟内就能跑完。

## 本节目标

本节把这条最简训练链走通：怎么把 dm_control 任务接进 SB3、训练曲线里哪几个指标值得看、训完又怎么评估和回放。

## 把 dm_control 包成 gym env

SB3 需要 Gymnasium 接口。dm_control 的任务用 [shimmy](https://github.com/Farama-Foundation/Shimmy)（Farama 官方的兼容层）包一层就能用。注意 `gymnasium` 本身并没有 `DmControlWrapper`，凭印象去 import 会失败：

```python
from dm_control import suite
from shimmy import DmControlCompatibilityV0
from gymnasium.wrappers import FlattenObservation

# 加载 cartpole swingup（底层就是 MuJoCo 物理）
dm_env = suite.load("cartpole", "swingup")
env = DmControlCompatibilityV0(dm_env, render_mode="rgb_array")
env = FlattenObservation(env)   # dm_control 的观测是 dict，拉平成向量给 MlpPolicy
```

需要先装 shimmy：`pip install shimmy`。

> 一个容易踩的坑：看到 cartpole 容易顺手写成 `gym.make("CartPole-v1")`。注意 **CartPole-v1 是经典控制里的离散小车，用的是自带的简化物理，跟 MuJoCo 没有关系**。如果想要 gymnasium 内置、底层确实是 MuJoCo 的环境，可以用 `gym.make("InvertedPendulum-v5")`（连续动作）这类，而不是 CartPole。本页用 dm_control 的 cartpole swingup，是更贴合本章 MuJoCo 主题、动作连续、也更有挑战的版本。

## PPO 一句话定义

PPO（Proximal Policy Optimization）的核心思路是：**每次更新策略时，限制新旧策略之间的差异不要太大，避免一次"学歪了"导致后续收集的数据大多作废。** 它是目前很常用的 on-policy RL 算法之一。深入见 [10 强化学习](../../../09-reinforcement-learning-for-robotics/README.md)。

## SB3 PPO 最小训练

接着上面的 `env` 往下写（cartpole swingup 是连续动作，`MlpPolicy` 直接适用）：

```python
from stable_baselines3 import PPO

# 创建 PPO 模型（默认超参通常够用）
model = PPO("MlpPolicy", env, verbose=1, device="cpu")

# 训练（swingup 比经典 cartpole 难，建议跑久一点）
model.learn(total_timesteps=200_000)

# 保存
model.save("ppo_cartpole_swingup")

print("Training done!")
```

输出类似下面这样（示意值，随种子和机器浮动；这是训练中段的样子，不是 200k 步的保证终值；swingup 单步奖励在 0–1 之间，一个 1000 步的 episode 满分约 1000）：

```text
------------------------------------
| rollout/              |          |
|    ep_len_mean        | 1000     |
|    ep_rew_mean        | 420      |
| time/                 |          |
|    fps                | 1500     |
| train/                |          |
|    approx_kl          | 0.008    |
|    entropy_loss       | -1.2     |
|    explained_variance | 0.7      |
------------------------------------
```

> 想先快速验证整条链路跑得通，把 `total_timesteps` 调成 `10_000` 做冒烟测试即可（几十秒），这时奖励还很低是正常的。本页这条链路的完整可跑脚本是 `labs/04-simulation/sb3_cartpole.py`，默认就是 1 万步的冒烟配置，把 `total_timesteps` 调大即可正式训练。

## 读训练曲线

关键指标：

| 指标 | 含义 | 什么算"好" |
|---|---|---|
| `ep_rew_mean` | 平均 episode 奖励 | 持续上升并稳定 → 学到了 |
| `explained_variance` | 价值函数对实际回报的解释程度 | 接近 1.0 → 价值估计准确 |
| `entropy_loss` | 策略的随机程度 | 训练中逐渐降低是正常的（策略越来越确定） |
| `approx_kl` | 每次更新的策略变化幅度 | 稳定在 0.01-0.02 → 更新平滑 |

如果 `ep_rew_mean` 随训练（swingup 通常需要十万量级的步数）持续上升并趋于平稳，说明训练在收敛。

## 评估与回放

```python
from stable_baselines3.common.evaluation import evaluate_policy

# 评估
mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
print(f"Mean reward: {mean_reward:.1f} +/- {std_reward:.1f}")
```

录一段视频：上面建 `env` 时传了 `render_mode="rgb_array"`，所以 `env.render()` 直接返回画面帧。配合第 4 章讲过的 `imageio` 拼成 mp4（注意 gymnasium 的 `step` 返回 5 元组 `obs, reward, terminated, truncated, info`）：

```python
import imageio

frames = []
obs, _ = env.reset()
for _ in range(500):
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, _ = env.step(action)
    frames.append(env.render())
    if terminated or truncated:
        obs, _ = env.reset()

imageio.mimsave("cartpole_swingup.mp4", frames, fps=30)
```

## 小结

- 把 dm_control 任务接进 SB3，常用的一条路径是 `dm_control.suite` + `shimmy` + `FlattenObservation`，而不是并不存在的 `gymnasium.wrappers.DmControlWrapper`。
- cartpole swingup 是连续动作、底层 MuJoCo 的任务，比经典的离散 `CartPole-v1` 更贴合本章主题，也更有挑战。
- 关注 `ep_rew_mean` 和 `explained_variance` 两个核心指标。
- 训完后用 `evaluate_policy` 做评估、`env.render()` + `imageio` 录视频做直观检查。

## 参考资料

- [Shimmy（Farama Foundation，DmControlCompatibilityV0）](https://github.com/Farama-Foundation/Shimmy)
- [Stable-Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [Raffin et al., "Stable-Baselines3: Reliable Reinforcement Learning Implementations", JMLR 2021](https://jmlr.org/papers/v22/20-1364.html)
- [dm_control（GitHub）](https://github.com/google-deepmind/dm_control)

## 导航

- 上一节：[训练总览](01-overview.md)
- 返回上级：[训练教程](../08-training-recipes.md)
- 下一节：[MJX + Brax 管线](03-mjx-brax-pipeline.md)
