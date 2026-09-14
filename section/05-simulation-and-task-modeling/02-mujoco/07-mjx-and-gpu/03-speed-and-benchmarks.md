# 速度与 benchmark

MJX 到底快多少？这一页直接给一组本教程在**单张 RTX 4090** 上的实测：同一个模型，CPU 多进程和 GPU（MJX）都跑 N 个并行环境，看吞吐量随 N 怎么变化，从而判断“值不值得上 GPU”。具体数字会随硬件、模型、timestep 变化，最好以自己机器上的实测为准。

## 本节目标

本节想给出一个量级感：

1. 单环境时，CPU 和 GPU 谁更快？
2. 环境数涨到多少，GPU 才开始拉开差距？
3. 哪些任务从 MJX 受益更多？

## 测量设置

- **模型**：一个内置的链式刚体（free base + 7 个 hinge，共 13 个自由度，自带与地面的接触），自包含、不依赖 menagerie。
- **CPU**：16 个进程把 N 个环境铺到多核（每进程独立 mjModel + mjData），只计 stepping、不含模型加载。
- **GPU**：MJX + `jax.jit` + `jax.vmap` 一次推进 N 个环境，预热若干步摊掉 JIT 编译后再计时。
- **公平性**：两边都跑 N 个并行环境，比的是“同样并行度下谁更快”，而不是拿 GPU 的并行去比 CPU 的单条。

脚本见 `labs/04-simulation/mjx_speed_benchmark.py`，下面是 `runs/04-simulation/mjx_speed_benchmark.txt` 的表格部分（顶部的环境信息行从略，测量设置见上）：

```text
      N     CPU env-steps/s   MJX env-steps/s   MJX/CPU
------------------------------------------------------------
      1               16383               817      0.05
    256              214029            178161      0.83
   2048              227954            662309      2.91
   8192    ~227954(plateau)            880353      3.86
```

读出来几件事：CPU 多进程涨到约 22.8 万 env-steps/s 就被核心数顶住（饱和）；MJX 随并行数持续上升，在 256 到 2048 之间反超 CPU，到 8192 约 3.9 倍。单环境（N=1）反而是 CPU 快得多：GPU 单条仿真固定开销大，要靠大批量并行才划算。绝对数值和反超点会随模型、GPU、核心数而变；在更大的 GPU（如 A100）和更多环境上，社区报告的加速比还会继续上到几十倍。

## 不同任务的受益程度

| 任务类型 | 模型复杂度 | MJX 受益程度 | 原因 |
|---|---|---|---|
| CartPole（2 DOF，~4 维观测） | 很低 | 低 | 单环境本身已经极快，GPU 并行优势不大 |
| Ant（8 驱动，27 维观测） | 中 | 高 | 较复杂 + 大量并行 → 典型受益场景 |
| Humanoid（17 驱动，高维观测） | 高 | 最高 | 模型计算密集，GPU 并行优势最明显 |
| 抓取（Panda + 物体） | 中 | 中-高 | 接触计算在 GPU 上也能并行加速 |

## 解读

从 benchmark 数据可以得到几个实用结论：

1. **单环境或少量环境时，CPU 并不慢，甚至可能更快。** 这是因为 CPU 单核频率高、没有 GPU 那份单步固定开销。调试阶段用 CPU 完全合理。

2. **几百到几千环境之间，是 GPU 开始拉开差距的“拐点”。** 上面的实测里，256 环境时 MJX 还略慢于 CPU，到 2048 已反超近 3 倍。如果训练只需要十几个并行环境，CPU 多进程就够了。

3. **环境数越大，GPU 的优势越明显。** 几千环境时 MJX 的吞吐已是 CPU 的数倍，在更大的 GPU 上还能更高。这对于需要大量 on-policy 样本的 PPO 训练来说是一个质变，原本需要几小时的 rollout 可能压缩到几分钟。

4. **模型越复杂，MJX 受益越大。** Humanoid（17 驱动、计算量大）的加速比通常比 CartPole（2 DOF）高得多，因为计算密集型任务在 GPU 上的并行度更高。

## 小结

- 单环境：CPU 通常更快。几百环境：大致打平。几千环境：MJX 明显领先。
- PPO 等需要大量样本的算法，用 MJX 有望从“小时级”降到“分钟级”。
- 不同任务的受益程度不同，模型越复杂、环境越多，受益越大。

## 参考资料

- [MuJoCo Documentation: MJX（benchmarking / performance）](https://mujoco.readthedocs.io/en/stable/mjx.html)
- [Brax（GitHub）](https://github.com/google/brax)
- [MuJoCo Playground（GitHub）](https://github.com/google-deepmind/mujoco_playground)：基于 GPU 后端的训练框架，可作为大规模并行加速的实证对照

## 导航

- 上一节：[最小迁移](02-minimal-migration.md)
- 返回上级：[MJX 与 GPU 并行](../07-mjx-and-gpu.md)
- 下一节：[局限与 Warp 简评](04-limitations-and-warp.md)
