# 数据快照与 policy analysis

RoboArena 的结果材料由两层数据组成。论文实验数据用于验证分布式 A/B ranking 方法，口径是 7 个 DROID generalist policies、7 所机构、612 次 pairwise comparisons 和 4284 个 policy rollouts。本地 `DataDump_02-03-2026` 是 benchmark 长期运行后的快照，`global_metadata.yaml` 记录 3284 个 sessions、9589 个 policy episodes 和 15 个 policy 条目。论文实验数字支撑 ranking 方法验证，DataDump 快照支撑后续回放和行为分析；两层数据都以 episode 级视频、动作记录和 evaluator feedback 支撑结果解释。

## DataDump 结构

`DataDump_02-03-2026` 的顶层包含 `global_metadata.yaml` 和 `evaluation_sessions/`。`global_metadata.yaml` 保存快照创建时间、session 总数、policy episode 总数，以及每个 policy 的 open-source flag 和 action space。policy index 中同时存在 `joint_velocity` 和 `joint_position` action spaces，这说明后续数据快照已经不只覆盖论文实验中的初始 7 个策略集合。

快照 metadata 的核心字段如下。`policy_index` 的条目不是 leaderboard 结果，而是解释 episode artifacts 时需要绑定的 policy metadata。

```yaml
dump_created_at: "2026-02-03T23:18:29.429488Z"
total_sessions: 3284
total_policy_episodes: 9589
policy_index:
  pi0_fast_droid:
    open_source: false
    action_space: joint_velocity
  paligemma_fast_droid:
    open_source: true
    action_space: joint_velocity
  dam:
    open_source: true
    action_space: joint_position
```

每个 `evaluation_sessions/<session_id>/` 目录代表一次评测 session。policy rollout 以 `A_<policy_name>/`、`B_<policy_name>/` 这类子目录保存；当 session 中包含额外策略时，也可能出现 `C_<policy_name>/`。每个 policy 子目录保存第三视角视频、wrist video 和 proprioception/action 记录，例如 `right_shoulder.mp4`、`wrist.mp4` 或按时间戳命名的 video files，以及压缩的 `npz` 文件。

目录结构把一次 ranking 判断拆回现场材料：

```text
DataDump_02-03-2026/
  global_metadata.yaml
  evaluation_sessions/
    <eval_session_id>/
      A_<policy_name>/
        <third_person_video>.mp4
        <wrist_video>.mp4
        <proprio_and_actions>.npz
      B_<policy_name>/
        ...
```

## episode artifacts

视频和 `npz` 文件用于回答不同问题。第三视角视频显示机器人、工作台、目标物体和最终状态，适合解释任务是否完成、是否碰撞、是否扰动物体或是否完成后继续动作。wrist video 更接近策略可能使用的局部视觉输入，适合分析抓取时的遮挡、目标是否离开视野、物体是否被夹爪遮住。`npz` 中的 cartesian position、joint position、gripper position 和 action 序列能还原控制轨迹和动作频率。

`EpisodeModel` 中的 `command`、`partial_success`、`duration`、policy endpoint、third-person camera type 和 video paths 把这些 artifacts 和数据库记录连接起来。`SessionModel.evaluation_notes` 保存 valid session 标记、A/B preference 和 long-form feedback。完整解释一个 policy 胜负时，至少需要把任务文本、A/B 标签、两条 rollout 视频、partial success、preference 和文字反馈放在同一个 session 下看。

后端 schema 可以简化成下面的分析表。session 描述一次 A/B comparison，episode 描述其中某个 policy 的单条 rollout；preference 不在 episode 上，而在 session notes 中。

| 对象 | 字段 | 解释作用 |
|---|---|---|
| `SessionModel` | `session_uuid` | 把 A/B episodes、preference、feedback 和视频记录连成一次 comparison |
| `SessionModel` | `evaluation_location`、`evaluator_name`、`robot_name` | 解释 evaluator 网络、机构分布和 DROID embodiment |
| `SessionModel` | `policyA_name`、`policyB_name` | 把可见 A/B 标签映射回真实 policy |
| `SessionModel` | `evaluation_notes` | 保存 `VALID_SESSION`、`PREFERENCE=A/B/TIE` 和 `LONGFORM_FEEDBACK=...` |
| `EpisodeModel` | `command` | 当前 rollout 使用的自然语言任务 |
| `EpisodeModel` | `partial_success`、`binary_success`、`duration` | 记录单条 policy rollout 的进展、完成和时长 |
| `EpisodeModel` | `gcs_left_cam_path`、`gcs_right_cam_path`、`gcs_wrist_cam_path` | 连接第三视角和 wrist video |
| `EpisodeModel` | `npz_file_path` | 连接 proprioception 和 action 序列 |
| `EpisodeModel` | `third_person_camera_type` | 说明 leaderboard UI 优先展示哪个外部视角 |

## policy pool metadata

DataDump 的 policy index 同时记录 open-source flag 和 action space。open-source flag 区分策略是否提供代码和权重复现入口；action space 说明 evaluation client 使用 joint velocity 还是 joint position 等控制方式。这个 metadata 对结果解释有直接影响：closed-source policy 可以参与排名，但训练数据、模型权重和推理细节未必可核查；不同 action space 下的动作后处理和安全限制也会改变 rollout 行为。

DROID generalist policies 在论文实验的 policy pool 中可直接运行于 DROID 新环境，包括基于 PaliGemma 和 `pi0` 系列的 flow、FAST、FAST+、FSQ 和 binning action representation。表达力更强的 action representation 通常优于简单 binning，autoregressive discrete action tokenization 在语言条件任务中更有优势；这个判断属于论文实验口径，不应直接推广到 DataDump 后续所有策略。

## policy analysis pipeline

RoboArena 的 qualitative analysis pipeline 把 episode artifacts 转成 policy report。VLM 根据 rollout 首帧和任务指令判断任务类别、场景条件、光照、物体可见性和 clutter 情况；LLM 汇总同一 policy 的 preference annotations、task categories、scene descriptions、partial success 和 long-form feedback，生成比较性报告。报告中的表现和失败模式应引用具体 session 或视频材料，避免只从 leaderboard 分数推断策略行为。

task categories 包括 Pick and Place、Open / Close、Move / Slide、Knock Over / Topple、Cover / Drape / Fold、Group / Organize / Stack、Find / Search、Minimal or No Action、Object Manipulation、Sorting / Classification 和 Tool Use。类别不是 ranking 的唯一输入，但它们让 policy report 能回答某个策略在哪类任务中更常胜出，在哪类任务中更常冻结、误抓、错误释放或无法完成精细动作。

一个 policy report 可以按下面的材料顺序组织：

```text
episode video first frames + language instruction
  -> VLM task category and scene description
  -> A/B result, partial_success, preference, long-form feedback
  -> per-policy aggregation by task category
  -> report claim with session/video reference
```

这个结构把 report 从普通文字总结变成可核查材料。若 report 声称某个 policy 在 Sorting / Classification 中容易混淆颜色，支撑材料应落到多条 session：任务文本含颜色约束，视频显示抓错物体，preference 或 feedback 指出对手处理得更好。若 report 声称某个 policy 在 Pick and Place 中表现稳定，支撑材料应落到多个同类任务，而不是单次成功 rollout。

## 结果现象

RoboArena 的结果现象应写成受数据口径限制的观察。generalist policies 在直接视觉接地的物体操作中更稳定，例如简单 pick-and-place、推动、toppling 和部分 open/close；tool use、cloth manipulation、精细 alignment、多步指令、颜色或属性辨别、否定和关系语言更容易失败。常见失败包括冻结、重复微动作、抓错相似物体、拿起后不释放、完成第一步后忽略后续子目标，以及在工具或柔性物体上只产生无效接触。这些趋势来自 RoboArena 论文 appendix 的实验观察。

结果分析可以按任务类别和现场现象组织：

| 任务类别 | 常见成功现象 | 常见失败现象 | 需要回看的材料 |
|---|---|---|---|
| Pick and Place | 直接接近目标、稳定抓取、释放到目标容器 | 抓错相似物、抓起后不释放、放到目标附近但未进入容器 | 第三视角视频、wrist video、`partial_success` |
| Tool Use | 抓住工具并形成有效接触 | 推开工具、只触碰目标表面、无法形成稳定工具姿态 | wrist video、action 序列、feedback |
| Cover / Drape / Fold | 抬起 cloth 并覆盖或折叠到目标区域 | 无法抓住布料边缘、只拖动一角、冻结 | 第三视角视频、类别 report |
| Sorting / Classification | 按颜色或类别选择正确物体 | 把橙色当红色、忽略否定或关系词 | language instruction、视频、preference |
| Open / Close 与多步任务 | 完成抽屉/门操作并继续后续目标 | 只完成第一步、被 distractor 干扰、完成后继续扰动 | session feedback、duration、视频结尾 |

这些现象不能推广为所有策略在相应任务类别上的长期上限。RoboArena 的任务分布由 evaluator 网络生成，policy pool 会随时间变化，后续策略可能改进某些类别。policy report 的可靠写法是把类别、session 数量、A/B 对手、preference、partial success 和视频材料连在一起，而不是把某个单次失败写成模型家族的通用结论。

## 数据完整性

DataDump 快照适合做回放、归因和案例分析，但分析前需要检查 session 完整性。有效的 A/B comparison 应有两个 policy 子目录、可读视频、可读 `npz`、任务指令、两个 partial success、preference 和 long-form feedback。缺失任意一类材料时，ranking 仍可能保留聚合信号，但行为解释需要写得更保守。

时间口径同样重要。`DataDump_02-03-2026` 的快照时间是 2026-02-03，里面的 policy index 和 session 数量反映截至该时间点的运行状态。论文实验中的 612 次 pairwise comparisons 和 4284 个 rollouts 是方法验证口径。报告或课程正文引用数字时，应说明数字来自哪个口径。

## 小结

RoboArena 的数据价值不只在 leaderboard。session、episode、video、`npz`、partial success、preference 和 long-form feedback 共同构成可追溯的真机评测材料。论文实验数字支撑方法结论，DataDump 快照支撑后续回放和行为分析；policy analysis pipeline 则把大量 episode 转成可核查的类别化报告。任何表现或失败模式判断都应回到对应 session 和 artifacts。

## 导航

- 返回上级：[RoboArena](../02-roboarena-benchmark.md)
- 上一页：[preference ranking 与分数口径](03-preference-ranking-and-scores.md)
- 下一页：[适用边界与结果解释](05-scope-and-result-interpretation.md)
