# 评分与复现口径

RoboChallenge 的分数依据真实机器人 rollout 计算。一次 rollout 同时包含任务初始状态、机器人观测、动作队列、执行视频、人工评分和异常记录。`success rate` 和 `progress score` 都建立在这些材料上；离开任务版本、复位协议和评分阶段定义，分数本身不能说明模型在其它任务、平台或开放场景下的完成表现。

## 结果对象

RoboChallenge 的结果对象有三层。第一层是 episode 或 rollout，记录一次真实执行的初始状态、观测、动作、视频和人工评分。第二层是 task，聚合同一任务下多次 rollout 的成功比例和阶段分。第三层是 benchmark，按 Table30 这类固定任务集汇总多个 task 的结果。

```text
rollout
  -> task result: 10 rollouts, success count, progress score
  -> benchmark result: mean success rate and mean progress score across tasks
```

这个层级决定了结果解释的方向。总分只能反映模型在任务集上的整体表现；任务级表能显示哪些任务失败；rollout 级材料才能解释失败来自物体复位、视觉误判、动作方向、夹爪接触、队列延迟还是人工终止。

## `success rate`

`success rate` 描述完整完成任务的 rollout 比例。它适合回答固定任务、固定机器人、固定复位协议下的完成率问题。例如一个任务运行 10 次，其中 4 次达到成功条件，则该任务的成功率为 40%。这个数字直观，但会丢失部分完成信息。

同一个失败结果可能包含完全没接近目标、完成前两步后失败、最后一步失败等不同情况。真实机器人任务常出现最后一步失败：模型已经抓住物体、移动到目标区域，但摆放姿态或接触力不满足成功条件。`success rate` 会把这些 rollout 都记为失败，因此 RoboChallenge 引入阶段化的 `progress score`。

## `progress score`

`progress score` 把一个任务拆成多个阶段，每个阶段分配若干分。阶段完成后获得对应分数。阶段还可以标记为 critical 或 non-critical；non-critical 阶段失败时，完整成功判断不一定被否定，但阶段分仍会反映执行质量。

`open_the_drawer` 的阶段定义可以写成下面这种形式：

| Stage | Points | Critical |
|---|---:|---|
| Arm reaches the drawer region | 2 | yes |
| Grabber is rotated towards the handle | 3 | yes |
| The drawer is pulled open | 4 | yes |
| Arm goes back to its original position | 1 | no |

单个 rollout 的阶段总分为 10。每个任务运行 10 次时，任务级 `progress score` 满分为 100。阶段分让最后一步失败和完全失败分开，也让同一成功任务中的多次重试、动作不稳或执行拖延进入分数解释。

## retry 与提前终止

真实机器人执行过程中，策略可能在同一阶段反复尝试。例如夹爪第一次抓偏后又回到物体附近进行第二次抓取。RoboChallenge 的阶段分会对 retry 扣分，单次 retry 扣 0.5 分。阶段分被扣到负数，或连续失败 retry 超过 4 次时，rollout 会提前终止以节省测试时间。

```text
stage_score = assigned_points - 0.5 * retry_count
terminate if stage_score < 0
terminate if consecutive_failed_retries > 4
```

retry 规则让 `progress score` 同时表达进度和执行质量。一个 rollout 可以成功但分数很低，因为它在多个阶段反复尝试；另一个 rollout 可以失败但分数很高，因为失败发生在最后一个 critical 阶段。

`success rate` 和 `progress score` 的组合比单个数字更接近 rollout 现象：

| 结果组合 | 常见现象 | 分数解释 |
|---|---|---|
| 高 SR / 高 Score | 多数 rollout 完整成功，retry 较少 | 任务在当前协议下基本被解决 |
| 高 SR / 低 Score | 成功次数不少，但阶段中反复修正或动作不稳 | 完整完成依赖多次尝试，执行质量仍不稳定 |
| 低 SR / 高 Score | 多数 rollout 失败在后段 critical stage | 策略能完成前半任务，但最后接触、姿态或判定条件失败 |
| 低 SR / 低 Score | 早期阶段经常失败或被提前终止 | 感知、定位、抓取或任务顺序在当前设置下尚未建立 |

## 复位变量

真机评测的复现口径首先取决于复位。RoboChallenge 的 controlled tester 协议从 demonstration episode 中抽出参考初始帧，并把参考图像叠加到 tester 的实时预览画面上。tester 调整物体、道具和桌面状态，使实际输入尽量匹配参考图像。

tester 差异会显著改变成功率。experienced tester 更接近示教数据分布，ignorant tester 可能引入无意偏差，adaptive tester 可能根据模型表现寻找更容易成功的物体位置。视觉复位把目标状态从文字描述转成图像对齐任务，降低了这三类 tester 的差异，但光照、相机外参漂移、夹爪磨损和物体材质仍然会进入 rollout。

## stability 与 fairness

stability 描述同一模型在同一任务上重复测试时分数波动有多大。RoboChallenge 的 benchmark protocol 主要服务 stability：固定任务集、集中维护机器人、使用视觉复位，使某个模型的分数更容易被再次检查。

fairness 描述多个模型的相对顺序是否稳定。comparative protocol 面向 fairness：同一初始状态下随机选择模型运行，tester 不知道当前运行的是哪个模型。这种协议能减少人为复位对相对排序的影响，但它不是 Table30 初始公开结果的主要服务方式。

## 结果记录

一个可解释的 RoboChallenge 结果至少保留下面这些字段。字段名称不必固定为同一套 schema，但信息缺失会直接削弱分数的可复查性。

```yaml
task: open_the_drawer
task_version: Table30
robot: ARX5
rollouts: 10
success_count: 4
progress_score: 63
reset_protocol: visual_reference_overlay
scoring:
  max_points_per_rollout: 10
  retry_penalty: 0.5
  max_failed_retries: 4
artifacts:
  videos: saved
  robot_states: saved
  actions: saved
  human_scores: saved
```

这组字段把任务版本、机器人平台、复位协议、阶段分和 episode 材料绑定在一起。缺少 `task_version` 时，Table30 和 Table30 v2 可能被混入同一个结果；缺少 `robot` 时，动作空间和相机视角无法还原；缺少 artifacts 时，分数无法依据具体 rollout 现象解释。

## 可比较条件

RoboChallenge 分数只在协议一致时适合横向比较。任务版本、机器人平台、训练数据使用方式、复位协议、动作接口、rollout 次数和评分阶段定义都属于可比较条件。Table30 v1 的模型结果不能直接迁移到 Table30 v2；task-specific 训练和 generalist / multi-task 训练也不能只看同一列总分。

`success rate`、`progress score`、视频和状态记录应一起出现。成功率回答完成了多少次，阶段分回答完成到什么程度，视频和状态记录回答为什么成功或失败。三者分开后，真机 benchmark 很容易退化成一个难以复查的排行榜数字。

## 小结

RoboChallenge 的评分口径把真实 rollout 转成两类互补数字：`success rate` 记录完整成功比例，`progress score` 保留阶段完成、retry 和提前终止信息。一个任务的分数来自多次真实执行，阶段定义、critical 标记、retry 扣分和 10 次 rollout 的汇总方式共同决定任务级结果。

复位协议、tester 差异、机器人平台、动作接口和 artifacts 保存共同构成复现所需信息。分数只有回到任务版本、机器人、复位方式、评分阶段、视频、状态、动作和人工评分记录时，才具备横向比较和失败分析的基础。

## 导航

- 返回上级：[RoboChallenge](../01-robochallenge-benchmark.md)
- 上一页：[推理接口与运行循环](03-inference-interface.md)
- 下一页：[结果分析与限制](05-results-and-limitations.md)
