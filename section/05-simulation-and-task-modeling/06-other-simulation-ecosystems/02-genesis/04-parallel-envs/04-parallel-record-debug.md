# 并行实验的记录与排错

本页讲并行环境的验收方式。第一轮并行实验不应只看速度，还要记录环境数量、动作形状、步数、后端、耗时和不同环境的目标差异。

## 本节目标

本节围绕下面几个问题展开：

1. 并行实验应该记录哪些字段？
2. 为什么 `frames_per_second` 不是第一优先级？
3. 如何判断不同环境真的收到了不同动作？
4. viewer、显存、shape 错误和后端问题应该怎样分开排查？

## 并行实验要记录什么

`05_parallel_envs.py` 会保存一份摘要，核心字段包括：

```json
{
  "batch": 8,
  "steps": 200,
  "action_shape": [8, 9],
  "joint1_targets": [-0.4, -0.2857, -0.1714, -0.0571, 0.0571, 0.1714, 0.2857, 0.4],
  "build_seconds": 1.2,
  "step_seconds": 3.4,
  "simulated_frames": 1600,
  "frames_per_second": 470.5,
  "result": "passed"
}
```

这里的重点不是追求最高 `frames_per_second`，而是确认并行语义正确：batch 是多少、动作 shape 是多少、不同环境是否真的收到不同目标、后端和 viewer 是否记录清楚。

几个字段要能互相对上：

| 校验 | 通过标准 |
|---|---|
| `action_shape[0] == batch` | 动作第一维就是环境数 |
| `len(joint1_targets) == batch` | 每个环境都有一个第 1 关节目标 |
| `simulated_frames == batch * steps` | 记录的是批量推进的总帧数 |
| `frames_per_second > 0` | step 循环确实执行并记录了耗时 |

如果这些关系不成立，先不要解读性能数字。并行实验的第一层成功，是语义一致；第二层才是速度。

## 和官方 summary 互补

官方 `sim_15_batched_ik`、`sim_02_heterogeneous_envs` 这类素材已经在 showcase 运行目录里留下 summary、预览图和视频。它们能证明官方并行相关示例可用，但字段更偏“素材运行结果”：示例路径、帧数、分辨率、耗时、`result`。

配套的 `05_parallel_envs.py` 要补另一类字段：`action_shape`、`joint1_targets`、`simulated_frames`。这类字段不一定适合展示在 contact sheet 上，却是判断并行语义是否写清楚的关键。

| 证据来源 | 主要证明 |
|---|---|
| 官方 showcase summary | 官方示例是否跑通，是否生成 `1060x580` 预览和视频 |
| 配套并行摘要 | batch 维度、动作 shape、不同环境目标和吞吐是否记录正确 |
| 原始日志 | 后端、warning、异常和无界面运行限制 |

所以并行实验的证据不要只有一个 MP4。最有价值的是把视频、summary 和日志放在一起，让别人既能看见现象，也能检查批量维度。

官方并行相关素材可以先按下面三行核对：

| 官方素材 | 帧数 / 耗时 | 记录解读 |
|---|---|---|
| `sim_02_heterogeneous_envs` | 133 帧，40.7801 秒 | 适合说明批量环境中对象可以不同 |
| `sim_03_domain_randomization` | 1 帧，12.8885 秒 | 适合说明随机化配置快照，不适合当长视频证据 |
| `sim_15_batched_ik` | 166 帧，38.8197 秒 | 适合说明批量 IK 的可视化直觉 |

这三行都是素材运行证据，不是本地脚本的并行语义证明。配套摘要仍要检查 `action_shape[0] == batch`、`len(joint1_targets) == batch` 和 `simulated_frames == batch * steps`。

因此，并行实验报告可以按下面这个最小证据清单写，不需要把所有视频都塞进正文：

| 证据项 | 建议路径 | 作用 |
|---|---|---|
| 本地脚本摘要 | `runs/genesis_codecheck_*/summaries/05_parallel_envs.json` | 证明 `batch`、`action_shape`、`joint1_targets` 和吞吐记录 |
| 本地脚本日志 | `runs/genesis_codecheck_*/logs/05_parallel_envs.log` | 通过 `bash labs/06_genesis/run_all.sh` 运行时保留后端、warning、异常和运行耗时上下文 |
| 官方并行素材摘要 | `runs/genesis_readme_showcase_canonical_20260608_055500/summaries/sim_15_batched_ik.json` | 证明官方 batched IK 素材在当前环境中可复现 |
| 官方并行视频 | `runs/genesis_readme_showcase_canonical_20260608_055500/videos/sim_15_batched_ik.mp4` | 建立批量 IK 的可视化直觉 |

如果单独执行 `python labs/06_genesis/05_parallel_envs.py`，默认只生成 summary，不会自动生成 `logs/05_parallel_envs.log`。需要日志时使用 `run_all.sh`，或在 shell 中自行重定向 stdout / stderr。

正文结论也要分两句写：`sim_15_batched_ik` 说明官方批量 IK 示例可见、可复现；`05_parallel_envs.json` 才说明本地批量动作张量和目标差异是正确的。把这两类证据混在一起，会削弱并行环境报告的可检验性。

## 排错顺序

并行环境失败时，按这个顺序拆：

1. `batch=1` 能不能跑；
2. `batch=8` 关闭 viewer 能不能跑；
3. `action_shape` 是否是 `[B, A]`；
4. `targets.device` 是否等于 `gs.device`；
5. 显存或内存是否足够；
6. 再考虑性能优化。

如果第一步单环境都不通，不要直接调并行。并行只会把错误复制很多份。

## viewer 不适合大 batch 验收

很多环境同时渲染时，viewer 可能拖慢或只显示部分环境。并行验收第一轮应当依赖 JSON 摘要，而不是窗口。等动作 shape 和 step 通过后，再选择少量环境做可视化。

## 读完应能回答

1. 为什么 `frames_per_second` 不能排在 `action_shape` 和 `joint1_targets` 前面？
2. 官方 `sim_15_batched_ik` summary 和本地 `05_parallel_envs.json` 分别证明什么？
3. 并行失败时，为什么要先回到 `batch=1`？

## 小结

- 并行实验要保存 batch、steps、action shape、目标差异、耗时和后端。
- `frames_per_second` 是参考指标，不是第一验收目标。
- 官方 summary 提供素材运行证据，配套摘要负责证明批量语义。
- 先单环境，再多环境；先无 viewer，再可视化。

## 导航

- 上一页：[envs_idx 与部分环境控制](03-envs-idx.md)
- 返回目录：[并行环境](../04-parallel-envs.md)
- 下一页：[多物理入门](../05-multiphysics.md)
