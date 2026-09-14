# preference ranking 与分数口径

RoboArena 的核心结果是 policy pool 内由 pairwise preference 聚合出的相对排名；固定任务表上的 `success rate` 不作为主指标。每次 A/B comparison 都发生在一个 evaluator 设置的真实任务和场景中，两个策略得到各自的 `partial_success`，同时得到一个 A、B 或 tie 的 preference label。ranking 方法把这些 preference labels 汇总为 policy scores，并用 `partial_success`、文字反馈和视频解释 ranking 背后的行为差异。

## preference 与 progress

`partial_success` 描述单个 rollout 对任务目标的最大进展。它可以区分完全失败、部分完成和完成任务，适合保留真机操作中常见的中间状态。例如策略接近目标但没有释放物体、打开抽屉但没有取出物体、完成抓取但没有放入容器，都可以得到介于 0 和 1 之间的分数。

`pairwise preference` 描述同一任务下 evaluator 更认可哪个策略。preference 可以吸收 `partial_success` 没有表达的因素：第一次抓取是否成功、轨迹是否平滑、是否减少碰撞、完成后是否停止、是否多次无效重试、是否把物体放在更合理的位置。两个策略拿到相同 `partial_success` 时，preference 仍可能不同；一个策略即使都完成任务，也可能因为动作更慢、扰动更多或释放不稳定而被排在后面。

RoboArena 因此把 `partial_success` 和 preference 作为互补信号。`partial_success` 能直接衡量任务完成程度，preference label 更适合二元比较中的行为质量判断。long-form feedback 则解释 preference 的原因，让 ranking 结论可以回到 episode 级现象，而不是只停留在分数表。

## Elo 与 Bradley-Terry

Elo 和 Bradley-Terry 都把 pairwise outcome 转成 policy strength。Elo 更像在线更新：每次 A/B 结果让胜者 score 上升、败者 score 下降，更新幅度取决于两者当前分差。Bradley-Terry 是概率模型：policy A 相对 policy B 的胜率由两个 log-ability 的差决定，离线拟合可以在完整 preference dataset 上求出一组强度参数。

普通 Bradley-Terry 的最小形式如下：

```text
p(policy_A preferred over policy_B) = sigmoid(theta_A - theta_B)
```

`theta_A` 和 `theta_B` 是两个策略的 log-ability。`theta_A - theta_B` 越大，A 被偏好的概率越高。这个公式没有任务项，因此一次简单 pick-and-place 上的胜负和一次工具使用任务上的胜负都会进入同一组 `theta` 参数。

这两种方法的共同假设是比较条件足够一致，或者任务差异可以当作随机噪声处理。RoboArena 的开放任务设置不满足这个假设。不同 evaluator 会设置不同物体、场景、语言目标和难度；同一对策略在 pick-and-place、tool use、cloth manipulation 或 multi-step task 上可能有不同相对关系。把所有 A/B comparison 当成同分布样本，会让任务难度和策略专长混入 policy ability。

## task-aware ranking

RoboArena 的 task-aware Bradley-Terry 变体把开放任务差异显式放入 ranking 模型。模型保留每个 policy 的全局 ability，同时引入 latent task buckets、bucket difficulty 和 policy-task offsets。每次 A/B comparison 不需要人工标注真实任务类别；模型从 preference data 中估计某个 comparison 更像哪个 latent bucket，并让 policy 在不同 bucket 上有不同偏移。

task-aware 版本可以用下面的简化公式理解：

```text
p(A > B) = sum_t nu_t
         * sigmoid(theta_A + psi_A,t - tau_t)
         * (1 - sigmoid(theta_B + psi_B,t - tau_t))
```

| 参数 | 含义 | 对 RoboArena 的作用 |
|---|---|---|
| `theta` | policy 的全局强度 | 表示跨任务的总体相对强度 |
| `tau_t` | latent task bucket 的难度 | 表示某类任务整体更难或更易产生完成差异 |
| `psi_p,t` | policy 在某个 bucket 上的偏移 | 表示某个策略对工具使用、布料、直接抓放等任务可能有专长或短板 |
| `nu_t` | comparison 属于 bucket `t` 的概率 | 表示当前开放任务分布中各类难度/任务模式的权重 |

task-aware ranking 处理的是任务难度和策略专长随任务类型变化的问题。一个任务过难或过易时，两个策略都可能表现接近，preference signal 会变弱；一个策略可能在直接物体操作中强于对手，却在工具使用或精细语义任务中弱于对手。task-aware ranking 不把这些差异全部归为噪声，而是让 ranking 同时表示全局相对强度和任务条件对比较结果的影响。

关键判断是：普通 BT 把所有 comparison 放进同一难度口径，task-aware BT 用 latent buckets 吸收开放任务分布差异，因此更贴近 RoboArena 的分布式真实评测形态。

下面的小型例子说明任务项为什么会改变解释。假设 policy pool 里有 A、B、C 三条策略，收集到 6 次 pairwise comparisons：

| comparison | 任务类型 | preference |
|---|---|---|
| A vs B | pick-and-place | A |
| A vs B | pick-and-place | A |
| A vs C | pick-and-place | A |
| B vs C | tool use | B |
| B vs C | tool use | B |
| A vs C | tool use | C |

普通 Elo 或 BT 会把 A 的 3 胜 1 负、B 的 2 胜 2 负、C 的 1 胜 3 负汇总为一个全局顺序，A 很可能排在最前。task-aware ranking 会保留另一个信息：A 在 pick-and-place bucket 上强，B 和 C 在 tool use bucket 上能提供额外偏好信号。真实 RoboArena 不直接使用人工任务类型作为监督，而是用 latent buckets 从 preference pattern 中吸收这类差异。

## 结果解释

RoboArena 的论文实验用 oracle ranking 作为参照。oracle ranking 来自所有 tested tasks 上对所有 policies 的 exhaustive evaluation，并按 average progress score 聚合。RoboArena ranking、普通 centralized evaluation、Elo、BT、task-aware ranking 和 progress-only ranking 都和这个 oracle 比较。论文实验中，RoboArena 的 pairwise comparisons 比 conventional fixed-task evaluation 更接近 oracle ranking，task-aware ranking 的相关性最好。

这个结论的适用范围绑定在实验设置上：7 个 DROID generalist policies、7 所机构、612 次 pairwise comparisons 和 4284 个 policy rollouts。它说明开放场景 A/B preference 可以更有效地排序这组 DROID generalist policies，不等于所有机器人、所有任务或所有 policy pool 都会得到同样 ranking 质量。新的 policy pool、不同 evaluator 网络或跨 embodiment 设置都需要重新解释结果。

## preference 的额外信息

RoboArena appendix 中的案例说明，partial success 相同并不代表两个 rollout 行为等价。有些 pairwise comparison 中，两条策略都没有完全完成任务，但其中一个更接近目标物或目标位置；有些比较中，两条策略都完成任务，但一个策略第一次尝试就完成，另一个经历掉落、重复抓取或多次修正；还有些比较中，两个策略都接近完成，但一个策略动作更直接，另一个策略靠偶然接触完成。

这些现象解释了 preference label 的价值。`partial_success` 把任务进展表示为一个连续数值，preference label 保留了 evaluator 对同一现场任务的整体判断。long-form feedback 进一步把这种判断落到行为描述上，使 policy report 可以区分速度、稳定性、语言跟随、场景理解、精细操作和失败后恢复。

约 `11%` 的 A/B evaluations 中，preference feedback 与 partial success feedback 不一致。该不一致包括 partial feedback 相同但 preference 不同，也包括 partial feedback 的高低和 preference 方向相反；这个方法验证数字来自 RoboArena 论文实验观察口径，不是 `DataDump_02-03-2026` 的快照统计。

| partial success 口径 | preference 额外记录 | 对结果解释的影响 |
|---|---|---|
| 两条策略同分且都未完成任务 | 一方更接近目标位置或目标物 | progress 只说明未完成，preference 区分失败程度 |
| 两条策略同为满分 | 一方第一次尝试成功，另一方掉落后重试 | success 无法区分过程稳定性 |
| 两条策略阶段分接近 | 一方动作直接，另一方多次修正或靠偶然接触 | preference 记录动作质量和可重复性 |
| partial success 更高的一方动作更危险或扰动更多 | evaluator 可能偏好更稳定的一方 | preference 会把安全感和执行自然性带入比较 |

## 分数边界

RoboArena leaderboard 是 policy pool 内相对排序。一个 policy 的分数会随着新增策略、旧策略下线、evaluator 任务难度变化和数据量增加而变化。它不能直接解释为跨 benchmark 的绝对成功率，也不能脱离 preference aggregation 方法比较到另一个 leaderboard。progress-only ranking 可以作为补充，但它和 preference ranking 衡量的不是同一种对象。

ranking 的最小解释单元应包含 policy pool、数据时间范围、A/B comparison 数量、evaluator 分布、ranking algorithm、是否使用 ties、是否纳入 partial success，以及可回溯的 episode artifacts。缺少这些条件时，排行榜顺序只能当作当前评测网络中的相对信号。

## 小结

RoboArena 用 pairwise preference 排序 generalist policies，是因为开放真机场景中的行为质量不容易被单一 `success rate` 或 `partial_success` 完整表达。Elo 和普通 Bradley-Terry 提供基础 pairwise ranking，task-aware Bradley-Terry 进一步处理开放任务难度和策略专长差异。ranking 结论应和 `partial_success`、long-form feedback、视频和 policy pool 一起解释，不能理解为固定任务集上的绝对完成表现。

## 导航

- 返回上级：[RoboArena](../02-roboarena-benchmark.md)
- 上一页：[系统与策略接口](02-system-and-policy-interface.md)
- 下一页：[数据快照与 policy analysis](04-data-snapshot-and-policy-analysis.md)
