# RoboArena

RoboArena 是面向 generalist robot policy 的分布式真机 benchmark。真实机器人 evaluation 分散在多个 DROID evaluator 站点：每次评测由 evaluator 设定现场任务和初始场景，central server 随机分配两条远程 policy server，evaluator 在同一任务下连续运行 Policy A 和 Policy B，再提交后端保存为 `partial_success` 的 progress feedback、pairwise preference 和文字反馈。RoboArena 不要求所有策略在同一组固定任务和固定实验室场景中测试。

这种组织方式把真机可比较性放在单次 A/B comparison 内部。两个策略在同一个语言指令、同一个现场复位目标和相近初始条件下比较；不同 A/B session 之间允许任务、物体、光照、相机视角和机构环境变化。RoboArena 因此更适合回答 policy pool 内 generalist policies 在开放任务分布下的相对顺序和行为差异，而不是给出某个固定任务集上的绝对成功率。

## benchmark 定位

RoboChallenge 和 RoboArena 都把真机 rollout 材料作为结果解释的基础，但两者处理真实世界变量的方式不同。RoboChallenge 倾向于集中管理机器人、任务、复位和评分协议，用固定任务集上的 `success rate` 与 `progress score` 描述策略完成度。RoboArena 接受多机构、多场景和开放任务带来的分布变化，把可比较性集中在同一次 A/B comparison 中，再用 preference ranking 聚合大量 pairwise comparisons。

这个差异直接影响分数含义。RoboChallenge 的一个任务级分数需要回到任务版本、机器人平台、动作接口和复位协议中解释；RoboArena 的一个 leaderboard 排名需要回到 policy pool、evaluator 网络、任务分布和 preference aggregation 中解释。前者强调固定协议下的完成程度，后者强调开放真实场景中的相对偏好。

## 数据口径

RoboArena 的论文实验和本地数据快照属于不同口径。论文实验口径覆盖 7 个 DROID generalist policies、7 所参与机构、612 次 pairwise comparisons 和 4284 个 policy rollouts，用于比较 RoboArena ranking 与 conventional centralized evaluation 的相关性。本地 `DataDump_02-03-2026` 是后续数据快照，`global_metadata.yaml` 记录了 3284 个 sessions、9589 个 policy episodes 和 15 个 policy 条目。

论文实验的 612 次 pairwise comparisons 和 DataDump 的 3284 个 sessions 属于不同统计对象。论文实验数字支撑 ranking 方法和样本效率结论；DataDump 数字说明 benchmark 长期运行后保留的 session、episode、video、proprioception/action 和 policy metadata 规模。解释某个结果时，`pairwise preference`、`partial_success`、long-form feedback、video path 和 policy action space 都应和对应数据来源一起出现。

## 章节内容

| 页面 | 定位 | 主要内容 |
|---|---|---|
| [分布式评测协议](02-roboarena-benchmark/01-decentralized-protocol.md) | RoboArena 如何组织 A/B 真机比较 | evaluator 设定任务、central server 分配策略、双盲、单次 comparison 内的初始条件匹配、`partial_success` / preference / feedback |
| [系统与策略接口](02-roboarena-benchmark/02-system-and-policy-interface.md) | 策略和 evaluator 如何接入 RoboArena | policy server、evaluation client、central server、database/storage、websocket observation/action contract、session 与 credit |
| [preference ranking 与分数口径](02-roboarena-benchmark/03-preference-ranking-and-scores.md) | A/B preference 如何转成 leaderboard | `partial_success`、pairwise preference、Elo、Bradley-Terry、task-aware ranking、preference 与 partial success 的差异 |
| [数据快照与 policy analysis](02-roboarena-benchmark/04-data-snapshot-and-policy-analysis.md) | rollout 材料如何支撑结果解释 | DataDump 目录、episode artifacts、policy reports、VLM/LLM 辅助分析、任务类别与失败现象 |
| [适用边界与结果解释](02-roboarena-benchmark/05-scope-and-result-interpretation.md) | RoboArena 结果如何解释和引用 | policy pool 相对排名、任务分布漂移、DROID embodiment、远程推理、人工 preference 与安全准入 |

## 导航

- 返回上级：[真机 Benchmark](../02-real-robot-benchmarks.md)
- 上一页：[RoboChallenge](01-robochallenge-benchmark.md)
