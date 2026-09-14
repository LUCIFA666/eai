# 真机 Benchmark

## 真机评测变量

真机 benchmark 的结果来自真实机器人、真实物体和现场执行过程。与仿真 benchmark 相比，真机评测很难把硬件状态、物体初始位置、光照、相机外参、人工复位和安全介入完全固定下来。同一条任务指令在不同复位方式下可能对应不同难度，同一段机器人动作也可能受到夹爪磨损、物体材质、网络延迟或安全停止策略影响。真机结果因此不只是一组任务成功率，还包含评测现场如何生成 episode、如何保存视频和动作记录、人工评分或偏好从哪里来的问题。

## 结果口径

结果口径和评测协议绑定在一起。`success rate` 适合固定任务集和固定复位协议下的比较，例如同一批 Table30 任务、同一类机器人平台和同一套初始状态控制方式。`progress score` 保留了部分完成信息，能区分完全失败、接近完成和最后一步失败，但分数含义依赖任务阶段划分，不能当作跨 benchmark 的统一表现指标。`pairwise preference` 来自同一场景中两个策略的 A/B 对比，能反映速度、动作稳定性、重试次数和执行质量等二元成功率难以表达的差异。`ranking` 则是某个 policy pool 内的相对顺序；它依赖参与比较的策略集合、任务分布和偏好聚合方法，只描述当前评测网络中这一组策略的相对位置。

## Benchmark 对照

RoboChallenge 和 RoboArena 代表两种不同的真机评测组织方式。RoboChallenge 倾向于把机器人、任务和复位流程集中管理，用固定任务集衡量策略在同一协议下的完成度。RoboArena 倾向于扩大任务和场景覆盖，通过分布式 evaluator 的双盲 A/B 比较汇总策略偏好。两者的结果都需要保留 episode 级现场材料，例如视频、观测与动作记录、人工评分或偏好说明；这些材料决定了分数和排名能否回到具体 rollout 现象中解释。

| Benchmark | 评测组织方式 | 任务 / 场景来源 | 主要结果口径 | 适合回答的问题 |
|---|---|---|---|---|
| [RoboChallenge](02-real-robot-benchmarks/01-robochallenge-benchmark.md) | 集中式在线机器人服务，评测侧提供真实机器人和低层接口 | Table30 固定任务集，覆盖 UR5、Franka、ALOHA、ARX5 等平台 | `success rate`、`progress score`、任务级得分表 | 在受控任务和复位协议下，不同 VLA 策略完成固定桌面操作任务的程度 |
| [RoboArena](02-real-robot-benchmarks/02-roboarena-benchmark.md) | 分布式 evaluator 网络，策略以远程 policy server 形式参与比较 | DROID 机器人平台上的开放任务和真实场景，由 evaluator 现场设定 | `partial_success`、`pairwise preference`、Elo / Bradley-Terry 类排名 | 在多机构、多场景和开放任务下，generalist robot policy 的相对排序和行为差异 |

RoboChallenge 的固定任务集让同一协议下的任务完成度更容易比较，RoboArena 的分布式 A/B comparison 则把开放场景中的行为差异聚合成 policy pool 内的相对排名。前者适合解释固定桌面操作任务中的阶段完成和失败原因，后者适合解释多机构真实场景中的偏好、稳定性和相对排序变化。
