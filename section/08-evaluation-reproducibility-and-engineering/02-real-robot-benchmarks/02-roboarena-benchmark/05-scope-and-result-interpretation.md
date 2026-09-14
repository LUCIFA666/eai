# 适用边界与结果解释

RoboArena 的结果来自分布式 DROID evaluator 网络、开放任务、远程 policy server、A/B preference 和 ranking model。leaderboard 名次描述当前 policy pool 中的相对顺序，policy report 描述 episode materials 中反复出现的行为模式，A/B episodes 记录具体任务下两条策略的现场比较。三类材料共同解释 RoboArena 的结果，但它们都不能作为跨所有机器人、所有任务和所有时间范围的绝对完成表现。

## ranking 的相对性

RoboArena leaderboard 描述的是一个 policy pool 内的相对顺序。新增策略、旧策略下线、open-source leaderboard 和 all-policies leaderboard 的筛选方式变化，都会改变分数解释。一个 policy 在当前 pool 中排名靠前，只说明它在当前评测网络、当前对手集合和当前 aggregation 方法下更常获得偏好；该排名不能脱离参与比较的策略集合单独使用。

policy pool 的相对性也影响纵向比较。长期运行的 benchmark 中，任务难度可能随着策略表现提升而上升，evaluator 可能主动设置更难的工具使用、细粒度语义或多步任务。早期和后期 ranking 如果直接放在一起比较，需要同时说明 policy set、任务分布、A/B comparison 数量和 ranking algorithm 是否发生变化。

一个具体情形是新增强策略进入 pool。原本排名第一的策略可能没有变差，但新策略在多数 A/B comparison 中胜出后，旧策略名次下降。这个变化说明当前 pool 的相对顺序更新，不说明旧策略在某个固定任务上的实际成功率下降。RoboArena 的名次变化应回到新增策略、comparison 分布和 episode materials 中解释。

## 任务分布漂移

RoboArena 不固定任务表，任务分布由 evaluator 网络共同产生。不同机构的 DROID setup、桌面空间、物体库、相机角度、光照和研究兴趣都会影响任务集合。一个阶段可能以简单 pick-and-place 为主，另一个阶段可能增加 cloth manipulation、tool use、drawer task 或 semantic instruction。ranking model 可以缓解这类差异，但不能把开放任务分布变成固定测试集。

任务分布漂移来自 RoboArena 的开放任务设置，也限制了结果外推。开放任务覆盖让 generalist policies 暴露更多真实失败模式；同时，任何 leaderboard 都只能说明给定时间范围和 evaluator 网络下的相对表现。报告 RoboArena 结果时，数据时间范围、session 数量、policy pool、任务类别分布和 evaluator 分布应和名次一起出现。

task-aware ranking 使用 latent task buckets 处理开放任务差异，但它不能替代 episode 级检查。一个策略在总榜中靠前，仍可能在 tool use、cloth manipulation 或细粒度语义任务中频繁失败；另一个策略总榜较低，也可能在某类任务上稳定胜出。类别化 policy report 和 A/B videos 是解释这种差异的主要材料。

## 接口与远程推理

RoboArena 让 policy server 远程运行，使策略提交方保留模型权重、推理环境和算力控制。这一设计降低 evaluator 端负担，也支持 closed-source policy 参与；同时，网络延迟、websocket 连接、端口转发、policy server liveness 和 action chunk 长度会进入 rollout。静态桌面 manipulation 对延迟较不敏感，动态任务或需要高频反馈的任务会放大远程推理风险。

接口声明同样影响表现。`PolicyServerConfig` 中的图像分辨率、wrist camera、external camera 数量、stereo image、`session_id` 和 action space 决定 evaluation client 发送哪些观测、如何执行动作。policy 如果依赖某个 evaluator 站点没有的相机配置，该 session 无法继续。结果解释因此需要保留 policy server config 和 client 运行记录。

几个常见接口限制可以直接落到运行现象：

| 限制案例 | 运行时表现 | 结果解释 |
|---|---|---|
| policy server 声明 `n_external_cameras = 2`，站点只配置一个 third-person camera | evaluation client 检查 camera ids 后终止当前 policy rollout | 该 session 反映硬件 contract 不匹配，不反映策略在任务中的完成表现 |
| evaluator 所在网络阻断 websocket 或端口转发服务 | central server liveness check 或 client connection 失败 | policy pool 的可用集合会变化，A/B sampling 不再覆盖该策略 |
| policy 返回长 action chunk | 远程调用次数下降，执行中重新观测次数也下降 | 静态任务可能更稳定，动态任务可能无法及时修正 |
| `joint_velocity` 动作未按接口尺度处理 | client 裁剪到 `[-1, 1]` 后轨迹与策略预期不一致 | rollout 失败可能来自动作后处理，不一定来自视觉语言推理或动作规划 |

## DROID embodiment 约束

RoboArena 的开源实例建立在 DROID platform 上。DROID 使用 Franka Panda 7DoF 机械臂、Robotiq 2F-85 gripper、wrist stereo camera 和 external ZED cameras，并依赖 DROID 数据生态训练 generalist policies。这个平台适合桌面和移动工作台上的广泛 manipulation，但它不能代表所有机器人 embodiment。

DROID 的硬件形态会影响任务可达空间、动作维度、遮挡模式和安全约束。Franka arm 的 7 DoF 结构、parallel-jaw gripper 的接触方式、wrist camera 的遮挡模式、external cameras 的视角覆盖，都会进入 episode 行为。RoboArena ranking 因此应解释为 DROID evaluator 网络上的结果，不能自动推广到双臂机器人、移动操作平台、灵巧手或其它相机布局。

跨 embodiment 使用 RoboArena 思路时，需要重新建立 policy interface、safety protocol、evaluation client 和 episode artifacts。分布式 A/B preference 这个评测方法可以迁移，但 DROID leaderboard 本身不提供其它 embodiment 上的直接结果材料。

## 人工 preference 与安全准入

RoboArena 的 preference 来自 human evaluator。人类偏好能捕捉速度、平滑度、重试次数、碰撞、自然性和完成后行为，但也带来主观性。不同 evaluator 对 partial credit、tie、动作是否安全、完成是否足够自然的判断可能不同。long-form feedback 可以缓解这一点，因为它把 preference 的依据写成可检查的行为描述。

preference 的主观性需要通过协议和材料约束。RoboArena 的双盲 A/B、跨机构 evaluator 网络和大量 session 聚合，减少了单个 evaluator 对 leaderboard 的支配。结果解释仍应把 preference 当作人类现场判断，而不是自动 ground truth；争议案例应回到视频、partial success 和文字反馈共同判断。

真实机器人评测还受到安全准入约束。开放参与需要 policy server 格式测试、测试环境试运行、受训 evaluator 的快速介入和 credit 机制。格式测试检查 observation/action contract；测试环境运行观察策略是否存在危险动作；credit 机制让贡献 evaluator 的机构获得评测自己 policy 的机会，避免 evaluation 供需失衡。

安全准入会限制完全开放的提交速度。一个策略即使接口正确，也可能因为动作幅度、夹爪行为、碰撞风险或 reset 后状态管理不稳定而不能进入通用 pool。leaderboard 因此还反映了安全和运行资格过滤，不只反映模型在任务中的表现。

## 结果引用口径

RoboArena leaderboard 适合引用当前 DROID policy pool 中策略相对排序。引用时应同时说明数据时间范围、policy pool、A/B comparison 数量、ranking algorithm 和是否包含 closed-source policies。缺少这些条件时，单独的名次或分数只描述一个不完整的相对信号。

A/B episodes 适合解释某个具体任务下两条策略的行为差异。引用时应把 `language_instruction`、Policy A/B、`partial_success`、preference、long-form feedback 和 videos 放在同一个 session 下。单条 episode 不适合推出某个策略的整体表现，但它能支撑某个 failure mode 或 behavior pattern 的具体说明。

policy report 适合总结跨多个 episodes 的类别化行为。报告中的判断应绑定 task category、session materials 和视频引用，例如某个 policy 在 Sorting / Classification 中频繁抓错颜色相近物体，或在 Tool Use 中只能接触工具但无法形成有效操作。没有 session 或 video materials 的 report claim 应写成低置信度观察。

RoboArena 不适合单独支持三类结论。第一，它不能把 leaderboard 名次写成固定任务成功率。第二，它不能直接给出跨 embodiment 绝对完成表现。第三，它不能在缺少 episode artifacts 时解释单个排名变化。RoboArena 提供的是开放真机 A/B preference 网络中的相对行为材料。

## 小结

RoboArena 的优势来自开放任务、分布式 evaluator、pairwise preference 和 episode artifacts；结果外推也受这些对象限制。ranking 应解释为特定 policy pool、DROID evaluator 网络、时间范围、任务分布和 aggregation 方法下的相对信号。policy report 和 A/B videos 把 leaderboard 连接到具体行为，但任何表现或失败模式判断仍应回到 session、preference、partial success、feedback 和视频材料。

## 导航

- 返回上级：[RoboArena](../02-roboarena-benchmark.md)
- 上一页：[数据快照与 policy analysis](04-data-snapshot-and-policy-analysis.md)
