# 结果分析与限制

Table30 的公开结果展示了固定真机任务集如何区分 VLA 策略。结果表同时给出 `success rate` 和 `progress score`：前者反映完整完成任务的比例，后者保留部分完成和 retry 信息。总榜名次只反映整体趋势；模型设置、任务类型和失败因素共同决定单个数字背后的含义。

## 模型设置

Table30 的 baseline 讨论覆盖 $\pi_0$、$\pi_{0.5}$、CogACT 和 OpenVLA / OFT 相关方法；当前平均结果表展示的是 `Pi05`、`Pi0`、`CogACT`、`Pi05/multi` 和 `Pi0/multi`。表格中带 `/multi` 后缀的条目对应 generalist 设置，其余条目对应 task-specific 设置。task-specific 设置为每个任务分别使用全部示教数据训练；generalist 设置从多个任务中混合少量样本训练，公开材料中约为每个任务 50 条，并且按机器人类型混合。

这两种设置回答的问题不同。task-specific 结果更接近“同一任务数据充分微调后能做到什么程度”；generalist 结果更接近“一个策略在同类机器人任务之间能否复用视觉、语言和动作映射”。同一个模型家族在两种设置下的差距，反映的是任务专门化、数据量和跨任务泛化共同作用后的结果。

## 平均结果

Table30 的平均结果显示强模型之间存在明显差距。公开结果的平均行如下：

| Method | SR | Score |
|---|---:|---:|
| Pi05 | 43.7 | 62.2 |
| Pi0 | 28.3 | 47.6 |
| CogACT | 11.7 | 21.8 |
| Pi05/multi | 17.7 | 31.3 |
| Pi0/multi | 9.3 | 20.6 |

`Pi05` 的 task-specific 结果在平均 `success rate` 和 `progress score` 上都领先。`Pi05/multi` 使用更少的单任务样本并混合多个任务，平均结果低于 task-specific，但在部分任务中仍能达到较高阶段分。这类结果说明 Table30 不只是成功率表，它还能显示 generalist 设置在哪些任务上已经接近可用，在哪些任务上仍停留在部分完成。

## 任务级差异

任务级表比平均值更有解释力。`stack_bowls`、`stack_color_blocks`、`put_cup_on_coaster`、`turn_on_faucet` 等任务在强模型上出现较高成功率和接近满分的 `progress score`，说明简单 pick-and-place、堆叠或明确开关类任务对当前模型更友好。

相反，`make_vegetarian_sandwich`、`press_three_buttons`、`water_potted_plant`、`arrange_paper_cups` 等任务即使在较强模型上也可能出现低成功率。低成功率不一定等于完全无法行动；例如某些任务的 `progress score` 明显高于成功率，说明策略能完成前半段，但在顺序、接触、姿态或最后一步判定上失败。

```text
high SR / high score: task mostly solved under the protocol
low SR / medium score: partial progress, failure near later stages
low SR / low score: early perception, contact, or task-logic failure
```

## 任务 tag

任务 tag 把任务失败因素从单个任务名中抽出来。公开结果中的 tag 汇总如下：

| Tag | Tasks | SR | Score |
|---|---:|---:|---:|
| temporal | 3 | 5 | 14 |
| softbody | 3 | 8 | 27 |
| precise3d | 12 | 18 | 38 |
| bimanual | 8 | 20 | 31 |
| multiview | 5 | 21 | 38 |
| repeated | 10 | 22 | 40 |
| classification | 5 | 27 | 44 |
| manipulation | 6 | 28 | 43 |
| simple-pick | 4 | 42 | 47 |
| all tasks | 30 | 22 | 37 |

`temporal` 和 `softbody` 的平均结果最低。`temporal` 任务中，相同当前图像可能对应不同历史阶段，单帧策略难以区分当前应该继续、返回还是切换子目标。`softbody` 任务涉及毛巾、纸张、胶带等形变物体，抓取点、接触状态和目标形状都会随执行改变。

`precise3d` 任务也低于全局平均。当前 VLA 常以较低分辨率图像输入推理，精确抓取、插入、对齐和放置更容易受到像素定位、相机视角和动作后处理误差影响。`classification`、`manipulation` 和 `simple-pick` 的平均结果相对更高，说明语义分类和简单放置在 Table30 中不是最主要瓶颈。

## 结果解释

Table30 结果只能说明模型在固定协议下的完成表现，不能证明模型在家庭场景、未知物体或不同平台上的表现。一个模型在 Table30 上分数较低，通常说明它在真实桌面任务中的感知、动作或时序处理仍有缺口；一个模型在 Table30 上分数较高，也只能说明它在固定任务集、固定机器人和受控复位协议下表现较好。

平均值、任务级结果、tag 汇总和 SR/Score 差距解释不同层面的失败。平均值显示模型整体强弱，任务级表定位具体失败任务，tag 汇总把失败任务归因到时序、形变、精确三维定位、双臂协作或多视角使用等因素。`success rate` 与 `progress score` 的差距还可以区分完全失败和接近完成。

## 结果误读

Table30 v1 和 Table30 v2 的任务集合、机器人平台、相机命名和 metadata schema 不同，v1 平均结果不能和 v2 数据更新直接合并。即使任务名称相同，物体数量、机器人实例、状态字段和评分阶段也可能变化；跨版本数字放在同一张表中会掩盖这些差异。

task-specific 和 `/multi` 也不是同一训练条件下的模型排行。task-specific 为单个任务使用更多示教数据，`/multi` 把多个任务和机器人类型混合到同一策略中；前者更像单任务上限测试，后者更接近跨任务共享测试。平均分只能说明整体趋势，任务级表和 tag 汇总才能显示失败集中在时序、形变、精确三维定位还是多视角使用上。

## 接口诚信限制

remote robot 范式把模型和推理代码留在参评方环境中。评测侧能记录机器人观测、动作和结果，但无法直接验证实际运行的模型是否与提交名称完全一致。多任务设置中，参评方也可能在不同任务之间切换专门策略，或让人工参与推理闭环。

这个限制不会让结果失去价值，但它改变了结果可信度的来源。公开模型、代码、客户端版本、run id、动作记录和 rollout 视频越完整，结果越容易被复查。缺少这些材料时，排行榜数字只能说明评测系统记录到某个远程客户端完成了多少任务，不能单独证明某个声明模型的结果可复现。

## 固定分布限制

视觉复位提高了稳定性，也固定了测试分布。参考初始帧、道具集合、桌面布局和相机视角越稳定，模型越可能针对这些条件形成适配。Table30 结果因此不能直接外推到开放家庭场景、未知物体集合或不同机器人平台。

Table30 v2 更新任务集合、机器人平台和数据 schema 后，v1 结果也不能自动迁移。跨版本讨论以任务版本和数据版本为前提。更开放的泛化结论依赖其它评测形式补充，例如不同地点、不同 tester、不同道具分布或成对偏好比较。

## 小结

Table30 结果需要同时解释模型设置、任务级结果、tag 汇总和 rollout 记录。task-specific 与 `/multi` 代表不同训练条件，`success rate` 与 `progress score` 反映不同失败程度，任务 tag 则把低分集中到时序、形变、精确三维定位、多视角或双臂协作等因素上。

remote robot 范式和固定测试分布也限制了结果外推。评测侧能记录观测、动作和视频，但无法直接验证远程客户端实际运行的模型；视觉复位提高稳定性，同时也固定了物体、桌面和相机条件。Table30 分数适合说明固定协议下的真机表现，不能证明模型在开放家庭场景、未知物体集合或不同机器人平台上的表现。

## 导航

- 返回上级：[RoboChallenge](../01-robochallenge-benchmark.md)
- 上一页：[评分与复现口径](04-scoring-reproducibility.md)
