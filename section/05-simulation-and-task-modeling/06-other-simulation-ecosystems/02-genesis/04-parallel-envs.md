# 并行环境

有了单环境、机器人控制和相机观测以后，Genesis 的并行环境才值得展开。这里先只讲 `n_envs`、批量动作、部分环境控制和并行实验记录，多物理会放到下一组。

这一组容易写空，因为“并行”和“多物理”都很容易变成宣传词。这里把它们落回两个学习问题：数据形状怎么变化，物理对象怎么变复杂。前者服务机器人学习采样，后者服务更复杂的物理交互。它们都重要，但不能混在一起讲。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么机器人学习需要从单环境切换到批量环境？
2. `n_envs` 对动作、状态读取和任务封装层的观测 / 奖励 / done 张量形状意味着什么？
3. 官方并行素材能证明什么、不能证明什么？
4. 第一轮并行实验应该保存哪些结构化字段？
5. 为什么不要把并行环境和多物理复杂度第一天就叠在一起？

## 先把并行单独学清楚

并行环境和多物理经常同时出现在 Genesis 的介绍里，但它们解决的是两类问题：

| 线索 | 核心问题 | 第一轮怎么学 |
|---|---|---|
| 并行环境 | 同一类任务如何一次跑很多份 | 从 `n_envs=4` 或 `8` 开始，看动作张量形状 |
| 多物理 | 场景里有哪些物理对象和求解方式 | 从多个刚体对象开始，记录每个实体的位置 |

这一组只负责第一条线：一个刚体机器人场景，复制成多份环境，再用批量动作控制。多物理对象会放到下一组单独讲。初学时不要第一步就写“4096 个环境 + GPU + 相机 + 软体 + 训练算法”。这类组合看起来接近研究 demo，但排错面非常宽。一个报错可能来自 CUDA、显存、viewer、相机、材料、时间步、批量维度、控制目标或训练接口，很难知道该从哪里下手。

本组路线是：

```text
一个刚体机器人场景
  -> n_envs 多份环境
  -> [B, action_dim] 批量动作
  -> summary 记录 batch、shape、目标差异和吞吐
```

## 并行先看形状

并行环境不是一句“更快”。在机器人学习里，它首先意味着数据从单条变成批量：

```text
单环境 action: [num_actions]
批量 action: [num_envs, num_actions]
```

对 Franka 来说，单环境位置目标可以理解成 `[9]`；如果 `B=8`，批量位置目标就是 `[8, 9]`。这个形状比速度更重要。如果解释不清 `[B, 9]` 的含义，就算脚本跑得很快，也还没真正理解并行环境。

配套脚本是：

```bash
GENESIS_BACKEND=cpu GENESIS_VIEWER=0 GENESIS_BATCH=8 \
  python labs/06_genesis/05_parallel_envs.py
```

通过后看终端里 `[genesis-check] wrote ...` 指向的 summary；默认路径是 `runs/genesis_codecheck_*/summaries/05_parallel_envs.json`：

| 字段 | 要看什么 |
|---|---|
| `batch` | 环境数量是不是设定值 |
| `action_shape` | 是否类似 `[8, 9]` |
| `joint1_targets` | 不同环境是否真的给了不同目标 |
| `simulated_frames` | 是否等于 `batch * steps` |
| `frames_per_second` | 作为性能参考，不作为第一优先级 |

并行环境的第一课不是调最大吞吐，而是确认批量语义正确。

## 官方并行素材怎么读

官方 `Simulation Interface` showcase 里有几项很容易被误读成“只是画面里东西多”。这里要把它们重新读成批量语义：

| 素材 | 运行摘要 | 读法 |
|---|---|---|
| `sim_02_heterogeneous_envs` | `captured_frames: 133`，`duration_seconds: 40.7801`，`result: passed` | 批量环境不一定每份完全同质，重点是场景结构和环境维度如何对应 |
| `sim_03_domain_randomization` | `captured_frames: 1`，`duration_seconds: 12.8885`，`result: passed` | 随机化素材不靠长视频证明，关键是记录参数和差异 |
| `sim_15_batched_ik` | `captured_frames: 166`，`duration_seconds: 38.8197`，`result: passed` | 批量 IK 是高层应用，入门仍要先解释 `[B, action_dim]` |

这三条都保存在 `runs/genesis_readme_showcase_canonical_20260608_055500/summaries/`。它们适合做入门引子，但第一轮实验仍然应该用 `05_parallel_envs.py` 保存 `batch`、`action_shape`、`joint1_targets` 和 `simulated_frames`。官方示例说明“能展示什么”，配套脚本负责证明“是否理解了批量维度”。

特别注意 `sim_03_domain_randomization`。它只有 1 帧，不是因为失败，而是因为这类素材更像“随机化配置快照”。如果报告里把它当成长时序视频来解释，就会误读证据。并行环境的证据要分清：有些证明动态过程，有些证明配置差异，有些证明 batch shape。

<figure class="doc-figure">
<p class="doc-figure-title">并行：异构环境</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_02_heterogeneous_envs.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_02_heterogeneous_envs.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/rigid/heterogeneous_simulation.py</code>。批量环境里各份内容可以不同，重点是场景结构与环境维度如何对应，而不是"画面里东西多"。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">并行：域随机化（配置快照）</p>
<img src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_03_domain_randomization.png" alt="domain randomization">
<p class="doc-figure-subtitle">官方 <code>examples/rigid/domain_randomization.py</code>（仅 1 帧，用静图）。这类素材更像随机化配置快照，靠记录参数与差异说明，不按长视频判读。</p>
</figure>

## 不要第一天叠加多物理

并行和多物理都会让问题变难，但难点不同：

| 方向 | 常见问题 | 排错入口 |
|---|---|---|
| 并行 | 形状不对、某些环境没被控制、显存上涨、viewer 拥挤 | 先减小 `n_envs`，打印 action shape |
| 多物理 | 接触不稳定、物体穿透、材料参数不合理、时间步敏感 | 先回到单对象或多刚体，检查 `dt` 和状态记录 |

本组只处理左边这一列。右边那一列会在 [多物理入门](05-multiphysics.md) 里从多刚体对象开始展开。这样安排不是降低 Genesis 的特色，而是让每一轮实验只有一个主要风险：并行页先查 batch 维度，多物理页再查对象、尺度、求解参数和状态演化。

## 学习顺序

这一组是 Genesis 相比传统入门仿真器更有辨识度的地方：

| 页面 | 重点 |
|---|---|
| [为什么需要 n_envs](04-parallel-envs/01-why-n-envs.md) | `scene.build(n_envs=...)` 和批量采样直觉 |
| [批量动作与批量状态](04-parallel-envs/02-batched-action-state.md) | `[B, action_dim]`、批量状态，以及任务封装层的观测 / 奖励 / done |
| [envs_idx 与部分环境控制](04-parallel-envs/03-envs-idx.md) | 只控制部分环境时的索引和 shape |
| [并行实验的记录与排错](04-parallel-envs/04-parallel-record-debug.md) | JSON 摘要、吞吐、后端和 viewer 排错 |

读这一组时不要急着追求“更多环境”和“更复杂物理”。先确认形状语义和运行记录正确，再谈速度和复杂对象。

## 进入适用边界前

这一组读完后，读者至少应该能说清一个取舍：`n_envs` 让批量仿真更直接，但动作、状态读取，以及任务封装层的 observation / reward / done / reset 都必须按环境维组织。这个代价不是附属细节，而是并行环境最容易出错的地方。

如果只能说“Genesis 很快”，还不够。进入适用边界页之前，应该能从任务需求倒推：项目到底需要并行采样、需要多物理，还是只是需要一个稳定刚体仿真器。本组只证明并行语义；官方并行素材提供直觉，本地脚本摘要证明 shape 和索引语义。多物理是否必要，要等下一组看完对象、solver 和验收成本以后再判断。

写并行实验报告时，不要只引用 batched IK 视频。最好把官方 `sim_15_batched_ik` 素材和本地 `05_parallel_envs.json` 放在一起对照看。

## 读完应能回答

1. `action_shape[0]`、`batch` 和 `len(joint1_targets)` 三者应该满足什么关系？
2. `sim_15_batched_ik` 的视频为什么不能单独证明本地并行脚本写对了？
3. `sim_03_domain_randomization` 只有 1 帧，为什么不应该直接判失败？

## 小结

- 并行环境的第一课是 batch 语义，不是追求最大吞吐。
- 官方并行素材提供直觉，本地摘要负责证明 `action_shape` 和目标差异；`envs_idx` 需要扩展摘要单独证明索引语义。
- 短帧数和配置快照要按素材目标解释，不能按普通长视频标准判断。
- 不要第一天把并行、相机、GPU、GUI 和多物理全叠在一起；本组先把 shape 和记录跑扎实。

## 导航

- 上一页：[渲染常见问题](03-observation-rendering-sensors/04-rendering-check.md)
- 返回目录：[Genesis](../02-genesis.md)
- 下一页：[为什么需要 n_envs](04-parallel-envs/01-why-n-envs.md)
