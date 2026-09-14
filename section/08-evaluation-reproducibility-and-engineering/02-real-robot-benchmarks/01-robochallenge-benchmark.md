# RoboChallenge

RoboChallenge 是集中式真机 benchmark。评测侧提供真实机器人、任务道具、复位流程和低层机器人接口，策略侧保留模型权重、推理代码和算力环境。参评策略在本地环境中运行，通过 RoboChallenge 的机器人接口轮询状态，接收多视角图像和本体状态，再把动作片段提交到真实机器人的动作队列。

这种组织方式把真机评测拆成两组对象。远程控制侧包括任务排期、观测时间戳、动作队列、机器人状态和安全中断；结果比较侧包括物体复位、人工 tester、成功率、阶段分和 episode 级视频记录。RoboChallenge 的 Table30 和 Table30 v2 都围绕这些对象展开，只是任务集合、机器人平台和数据 schema 有版本差异。

## 系统位置

RoboChallenge 的核心假设是固定任务集适合衡量策略在受控桌面操作任务上的完成度。Table30 使用一组桌面和桌边 manipulation 任务，把任务成功率与 `progress score` 绑定到同一套复位和评分协议中。Table30 v2 保留 Table30 的固定任务集思路，同时更新任务列表、机器人平台和数据字段，使任务数据更接近后续训练与 LeRobot 转换流程。

这个定位和 RoboArena 不同。RoboArena 更强调开放场景中的策略相对偏好和分布式 evaluator 网络；RoboChallenge 更强调集中维护的机器人、固定任务集、受控复位和可追溯的 rollout 材料。两者都是真机 benchmark，但 RoboChallenge 的分数更适合回答同一协议下某个策略把固定任务做到什么程度，RoboArena 的排名更适合回答某个 policy pool 中策略相对排序如何变化。

## 评测流程

RoboChallenge 的评测流程从任务数据开始。任务描述、示教 episode、相机视频、机器人状态和任务级 metadata 定义了训练材料和测试场景。策略完成训练后，通过 RoboChallengeInference 一类客户端接入在线评测系统。评测运行时，客户端按 job scheduling 信息准备模型，从机器人接口获取观测，把观测送入本地策略，再把动作序列提交给评测侧的真实机器人。

结果记录和控制流程同样重要。每个 rollout 的视频、状态、动作队列和人工评分共同解释一次成功或失败。`success rate` 给出完整完成比例，`progress score` 保留阶段性完成信息；两者都依赖具体任务的阶段划分、复位方式和 tester 操作。跨版本或跨机器人比较时，任务集、状态字段、动作空间和相机配置先于分数进入解释。

RoboChallenge 的单个分数由四类对象共同限定：任务版本决定物体、语言目标和阶段定义；机器人平台决定状态字段、动作维度和相机视角；推理接口决定观测分辨率、动作类型和队列节奏；评分协议决定成功判定、阶段分和 retry 扣分。缺少其中任意一类信息时，同一个 `43.7%` success rate 或 `62.2` progress score 都无法还原成可比较的真机结果。

## 章节内容

| 页面 | 定位 | 主要内容 |
|---|---|---|
| [系统与评测协议](01-robochallenge-benchmark/01-system-protocol.md) | RoboChallenge 的在线真机系统视角 | remote robot 范式、机器人平台、异步观测动作、视觉复位、stability 与 fairness |
| [Table30 任务与数据](01-robochallenge-benchmark/02-table30-task-data.md) | 固定任务集和示教数据说明 | Table30 / Table30 v2 任务集合、机器人平台、视频命名、metadata、状态字段和 LeRobot 转换 |
| [推理接口与运行循环](01-robochallenge-benchmark/03-inference-interface.md) | 参评策略接入在线机器人服务的接口 | job scheduling、`state.pkl`、`/action`、`action_type`、动作队列和机器人平台差异 |
| [评分与复现口径](01-robochallenge-benchmark/04-scoring-reproducibility.md) | 真机分数如何产生和比较 | `success rate`、`progress score`、阶段分、retry 扣分、rollout 记录和复位变量 |
| [结果分析与限制](01-robochallenge-benchmark/05-results-and-limitations.md) | Table30 结果如何解释 | 模型设置、平均结果、任务 tag、失败因素、接口诚信和固定测试分布限制 |

任务数据、推理接口、评分复现口径、结果分析和限制条件共同限定 RoboChallenge 分数。任务版本决定训练材料和测试场景，推理接口决定观测与动作如何进入真实机器人，评分协议决定 rollout 记录如何转成 `success rate` 和 `progress score`。

## 导航

- 返回上级：[真机 Benchmark](../02-real-robot-benchmarks.md)
- 下一页：[系统与评测协议](01-robochallenge-benchmark/01-system-protocol.md)
