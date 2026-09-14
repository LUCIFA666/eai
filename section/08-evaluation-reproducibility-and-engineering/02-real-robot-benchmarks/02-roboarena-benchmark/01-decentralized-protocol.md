# 分布式评测协议

RoboArena 的单次评测单位是一个 A/B comparison。evaluator 在真实 DROID 站点设定任务和场景，central server 分配两条可用的 policy server，evaluation client 依次运行 Policy A 和 Policy B，并把两个 rollout 的分数、偏好和记录材料上传到中心服务。global ranking 来自大量这类 pairwise comparisons，而不是来自所有策略在同一批固定任务上的完整笛卡尔积评测。

## A/B session

一次 session 从现场任务开始。evaluator 先确认相机视角和机器人状态，再输入自然语言指令，例如把某个物体放入容器、打开抽屉、清理桌面或执行一个工具使用动作。central server 在收到指令、机构和 evaluator 信息后，从当前可用 policy pool 中选出两个策略，并只把 A/B 标签、IP 和端口返回给 evaluation client。

这个顺序让 policy assignment 发生在任务文本之后。策略无法根据即将出现的对手或 evaluator 身份改变任务，evaluator 也不会在设置任务时看到策略名称。evaluation client 随后为 Policy A 建立 websocket policy connection，按策略声明的相机、分辨率和动作空间采集观测并执行 rollout；Policy A 结束后，机器人和场景被复位到同一 A/B comparison 的参考初始状态，再运行 Policy B。

evaluation client 的控制流程可以概括为下面的伪代码。任务指令先于 `/get_policies_to_compare` 发送，A/B 策略的真实名称只保存在 central server 的 session 记录中；client 端只使用可见标签、IP 和端口运行 rollout。

```python
preview = env_preview.get_observation()
ref_reset_state = concat_left_right_images(preview)
lang_command = input_task_instruction()

session = post(
    "/get_policies_to_compare",
    eval_location=institution,
    evaluator_name=evaluator_email,
    language_instruction=lang_command,
    robot_name="DROID",
)

for policy in session["policies"]:  # [{"label": "A", ...}, {"label": "B", ...}]
    policy_client = WebsocketClientPolicy(policy["ip"], policy["port"])
    server_cfg = policy_client.get_server_metadata()
    episode = run_droid_rollout(lang_command, policy_client, server_cfg)
    upload_eval_data(session["session_id"], policy["label"], episode)
    reset_robot_and_scene(ref_reset_state)

terminate_session(
    session["session_id"],
    valid_session=True,
    preference="A" | "B" | "TIE",
    longform_feedback=feedback,
)
```

这段流程解释了 RoboArena 的几个结果字段为什么总是成组出现：`session_id` 连接 A/B 两个 policy episodes，`language_instruction` 固定同一次 comparison 的任务，`policy_letter` 只暴露 A/B 标签，`evaluation_notes` 在 session 结束时保存 valid 标记、preference 和文字反馈。

## 双盲比较

RoboArena 的双盲来自两组接口约束。evaluator 看到的是 Policy A 和 Policy B，不看到策略名称、训练方法或提交者；policy server 收到的是 DROID 观测、`prompt` 和可选 `session_id`，不直接看到对手身份或 evaluator 的 preference 选择。central server 保存真实 policy name、session uuid、A/B 标签和 evaluator metadata，用于后续 leaderboard 与数据查询。

双盲不能消除所有偏差。evaluator 仍可能从行为风格猜测某些策略家族，policy server 也可能通过 session 分布间接感知评测环境。RoboArena 的设计重点是减少单个 evaluator 或单个任务设置对结果的直接操控，并让大量机构和任务分布共同决定 ranking。

## 初始条件

RoboArena 不要求所有 session 使用同一套标准任务、同一组物体或同一间实验室。公平性要求集中在一个 A/B comparison 内：Policy A 和 Policy B 应在同一语言指令下运行，evaluator 在两次 rollout 之间把物体、机器人和相机视角尽量复位到相同初始条件。evaluation client 会保留任务开始前的左右相机参考画面，并在两个策略之间提示 evaluator 按该画面恢复场景。

这种设置承认真实世界难以完全复现。不同 session 之间的光照、背景、桌面高度、物体材质、相机外参和 evaluator 操作都可能变化；RoboArena 把这些变化当作开放任务覆盖的一部分，而不是把它们全部当作噪声排除。单个 A/B 内的相近初始条件提供相对比较信号，大量 A/B session 的汇总提供 policy pool 的整体排序。

## evaluator 反馈

每个策略 rollout 结束后，evaluator 给出 `partial_success`，数值范围对应 0 到 100 的任务进展，上传时保存为 0 到 1 的小数。`binary_success` 只在 partial success 为满分时标为 1，因此它比 `partial_success` 更粗。Policy B 结束后，evaluator 还要在 A、B 和 tie 中选择 preference，并提供 long-form feedback，说明偏好来自速度、稳定性、动作质量、完成程度、重试次数还是其它现场现象。

这三类反馈承担不同职责。`partial_success` 记录每个 rollout 在任务目标上的最大进展；`pairwise preference` 记录同一任务下哪个策略整体更好；long-form feedback 把 preference 落到可解释的行为差异上。两个策略可以拿到相同 partial success，但 evaluator 仍可能偏好其中一个，因为它动作更直接、碰撞更少、第一次抓取就成功，或在完成后没有继续扰动场景。

RoboArena appendix 中有一组典型偏好差异。两条策略都完成了取物任务时，evaluator 仍可能偏好第一次抓取就完成的策略，而不是先掉落、再二次抓取的策略。两条策略都没有完全完成任务时，evaluator 也可能偏好更接近目标物或目标位置的一方。下面的案例表使用论文 appendix 的案例口径转述，不把 session 编号和 DataDump 快照纳入同一统计说明。

| comparison 现象 | `partial_success` 未覆盖的差异 | preference 记录的行为差异 |
|---|---|---|
| 两条策略都接近完成 cloth 相关任务 | 同分只说明最终进展相近 | 其中一条策略把 cloth 放到更接近目标的位置 |
| 两条策略都完成取物和放置 | 满分不区分过程质量 | 其中一条策略第一次抓取成功，另一条经历掉落和重复抓取 |
| 两条策略都完成 cup 相关动作 | 结果相同但结束行为不同 | 其中一条策略释放后回到稳定状态，另一条继续重复抓取 |
| 两条策略都几乎完成 drawer task | 阶段分接近 | 其中一条策略动作更直接，另一条被 distractor 干扰后才恢复 |

## session 有效性

evaluation client 在 session 结束时要求 evaluator 标记该 session 是否有效。有效 session 会进入统计和 credit 计算；无效 session 用于处理中途网络故障、policy server 连接失败、机器人异常、安全介入、复位失败或任务设置错误等情况。central server 也会清理长时间未完成的 stale sessions，并把 timeout 写入 session notes。

valid session 标记不是结果质量的唯一过滤条件。完整解释一次 comparison 还需要检查两个 policy episodes 是否都上传成功、视频路径是否存在、`partial_success` 和 preference 是否齐全、long-form feedback 是否能对应现场行为。RoboArena 的结果材料因此以 session 为单位连接任务指令、A/B policy、`partial_success`、preference、视频和动作记录。

无效 session 的成因会影响数据是否能进入 ranking 或只作为运行日志保留：

| 现场问题 | 代码路径中的表现 | 对结果的影响 |
|---|---|---|
| policy server 连接失败 | `WebsocketClientPolicy(ip, port)` 无法完成 handshake | 当前 A/B pair 无法形成完整 comparison，session 不进入有效 ranking |
| policy 请求两个 external cameras，但 evaluator 站点只有一个 | client 检查 `n_external == 2` 和本地 camera ids 后终止 | 该策略配置与站点硬件不兼容，相关 episode 不构成公平比较 |
| rollout 中途机器人异常或安全介入 | evaluator 在 session 结束时不标记 `VALID_SESSION` | videos 可保留为排查材料，preference 不应进入 leaderboard 统计 |
| 两个 policy episodes 只上传了一个 | backend 无法在 A/B UI 中同时构造 `policyA` 和 `policyB` block | 单边 episode 可以解释故障，不能支撑 pairwise preference |

## 小结

RoboArena 的评测协议把标准化范围收缩到单次 A/B comparison：同一任务、相近初始条件、连续运行的两个策略和同一个 evaluator 的偏好反馈。不同 session 之间允许任务和环境变化，这些变化提供了 generalist policy 所需的开放覆盖。ranking 的可信度不来自某个固定任务表，而来自大量双盲 pairwise comparisons、有效 session 标记和 episode 级 rollout 材料。

## 导航

- 返回上级：[RoboArena](../02-roboarena-benchmark.md)
- 下一页：[系统与策略接口](02-system-and-policy-interface.md)
