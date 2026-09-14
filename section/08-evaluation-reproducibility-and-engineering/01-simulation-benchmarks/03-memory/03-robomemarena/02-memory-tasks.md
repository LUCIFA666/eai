# 记忆类型与任务

RoboMemArena 的 26 个任务对应反应式策略的四类典型失败模式，按记忆需求分成四类：Transferring 4 个、Occlusion 11 个、Counting 7 个、Sequence 4 个。任务名、真值子任务序列、场景与记忆需求描述记在 `evaluation_benchmark/async_vlm26_reference/fullvlm_v2_26_memory_tasks.json`，任务定义在 `bddl/`，平均步数取自论文附录表。

## 记忆类型编码

每个任务在 JSON 里带一个 `memory_type` 字段，用单字母标出它主要考的记忆能力：

| 编码 | 记忆类型 | 核心难点 |
|---|---|---|
| S | Sequence | 后续步骤依赖此前子任务的结果，要记住哪些前置已完成 |
| O | Occlusion | 目标进抽屉/柜子/微波炉后不可见，要记住放了什么、放在哪 |
| C | Counting | 同一动作按次数重复，相邻两次场景几乎一致，只能靠记次数 |
| T | Transferring | 在外观相同的容器间搬运多物，要记住源到目标映射与已完成项 |

有些任务同时压两类记忆，编码写成组合。例如倒水任务 `6`、`7`、`16` 是 `C + O`（既数次数、又要处理容器遮挡），多抽屉分放任务 `11` 是 `O + C`。任务的四类 suite 归属按主导记忆需求划分，下面分类展开。

## Multi-Object Transferring（4 个）

在外观相同的容器（cabinet1 到 cabinet2、plate1 到 plate2）之间搬运多个物体，要记住源到目标的映射，以及哪些已经搬完，避免重复拿或漏搬。

| 编号 | 任务 | 类型 | 子任务数 | 平均步数 |
|---|---|---|---|---|
| 18 | Transfer Chocolate Butter | T | 4 | 866 |
| 19 | Transfer Sauce Milk Juice | T | 6 | 1265 |
| 25 | Transfer Butter Cream Cheese | T | 4 | 779 |
| 26 | Transfer Chocolate Pudding Cream Cheese | T | 4 | 779 |

以最长的 `19` 为例，它要把 tomato sauce、milk、orange juice 三个物体依次从 cabinet1 搬到 cabinet2，子任务序列是拿起酱料、放进 cabinet2、拿起牛奶、放进 cabinet2、拿起橙汁、放进 cabinet2。三个物体外观和搬运动作高度相似，当前画面无法告诉策略这是第几个物体、前两个是否已搬完，只能靠记住三者的完成状态来决定现在该处理谁。

## Multi-Object Occlusion（11 个，最大的一类）

把物体放进抽屉、柜子或微波炉，容器随后关上、目标离开视野，要记住放了什么、放在哪、每个容器此前的状态。这一类最大，反映家居场景里遮挡最常导致反应式策略失败。它内部又分两种子形态：探查后按记忆动作（如把 butter 放进先前探明的那个抽屉），以及多物按位置分放（如把两个物体分放到指定抽屉、或叠放到同一位置）。

| 编号 | 任务 | 类型 | 子任务数 | 平均步数 |
|---|---|---|---|---|
| 4 | Put Butter in Not-Empty Drawer | O | 9 | 1020 |
| 5 | Put Butter in Empty Drawer | O | 9 | 1806 |
| 11 | Put Cookies Chocolate into Drawers Respectively | O + C | 8 | 1835 |
| 12 | Put Cookies Chocolate into Middle Drawer | O | 6 | 1370 |
| 13 | Put Cookies Butter into Middle Drawer | O | 6 | 1377 |
| 14 | Put Cookies Chocolate into Drawer Respectively | O | 8 | 1832 |
| 17 | Put Butter Chocolate into Middle Drawer | O | 6 | 1502 |
| 20 | Put Cookies Chocolate into Microwave | O | 6 | 1195 |
| 21 | Put Butter Chocolate into Microwave | O | 6 | 1175 |
| 23 | Put Cream Popcorn into Microwave | O | 6 | 1175 |
| 24 | Put Cookies Popcorn into Microwave | O | 6 | 1195 |

任务 `4` 和 `5` 是最能体现遮挡记忆的一对：两者都要先逐个打开抽屉探查、再关上，然后回到某个特定抽屉放 butter。区别只在目标——`4` 要放进非空抽屉、`5` 要放进空抽屉。抽屉关上后目标不再可见，策略必须靠此前探查留下的历史关键帧才能定位该回哪个抽屉。任务 `20` 则是叠放型：先把 cookies 放进微波炉，再把 chocolate 放到 cookies 刚才所在的位置，要记住 cookies 的放置点。

## Multi-Object Counting（7 个）

把一个动作按要求做指定次数（例如倒两次），而连续两次之间场景几乎一样，次数只能靠记。部分计数任务还叠加遮挡或前置摆放。

| 编号 | 任务 | 类型 | 子任务数 | 平均步数 |
|---|---|---|---|---|
| 6 | Pour Sauce on Cookies Twice Place Sauce into Drainer | C + O | 4 | 624 |
| 7 | Pour Sauce on Frypan Twice Place Sauce into Drainer | C + O | 4 | 537 |
| 8 | Pour Sauce Twice over Chocolate in Frypan Place Sauce into Drainer | C | 6 | 910 |
| 9 | Pour Sauce Twice over Butter in Frypan Place Sauce into Drainer | C | 6 | 958 |
| 10 | Pour Wine into Mug Twice | C | 4 | 472 |
| 15 | Pour Milk Twice over Butter in Frypan | C | 6 | 1055 |
| 16 | Pour Milk Twice over Mug Place Milk into Drainer | C + O | 4 | 594 |

最纯粹的计数任务是 `10`：拿起酒瓶、往杯里倒两次、再把酒瓶放回桌上。第一次倒和第二次倒的画面几乎无差别，策略要判断当前处于第一次倒、第二次倒、还是最后放置阶段，唯一依据就是已完成的倒水次数。`8`、`9`、`15` 在计数前还叠了一步前置摆放（先把 chocolate / butter 放进平底锅再倒），要同时记住食材是否已入锅、以及倒了几次。

## Multi-Object Sequence（4 个）

下一步用哪个容器、做什么，取决于此前某个子任务的结果，还要解析跨多步操作的指代，要记住哪些前置子任务已经完成。

| 编号 | 任务 | 类型 | 子任务数 | 平均步数 |
|---|---|---|---|---|
| 1 | Put Cookies Sauce into Target Container in Order | S | 4 | 742 |
| 2 | Put Butter Popcorn into Target Container in Order | S | 4 | 708 |
| 3 | Put Cream Pudding into Target Container in Order | S | 4 | 708 |
| 22 | Pour Sauce Twice Put Cookies into Microwave | S | 8 | 1565 |

任务 `1` 要按顺序把 cookies 和 tomato sauce 放进同一个目标容器，子任务序列是拿起 cookies、放进容器、拿起 tomato sauce、放进容器。两个物体去向相同，策略要靠视觉历史判断当前还在处理第一个物体、还是已经切到第二个，不能跳过也不能重复。任务 `22` 是最复杂的顺序任务，把计数和顺序叠在一起：先往 cookies 上倒两次酱料，再打开微波炉把 cookies 放进去、关上，八个子任务里既要数够两次倒水、又要在倒完后才切到微波炉摆放阶段。

## 真值子任务序列

每个任务都带一条真值子任务序列 `primitive_order`，每个子任务同时记 `label`（可读英文，如 `open top drawer`）与 `stem`（对应 HDF5 里的原语名，如 `open_top_drawer`）。以 `4_drawer_butter` 为例，它是一条九步序列：

```text
open top drawer → close the top drawer → open middle drawer → close middle drawer
→ open bottom drawer → close bottom drawer → open top drawer again
→ place butter into top drawer → close top drawer final
```

正是这种先探查、再依据探查结果动作的结构逼出记忆——后面的子任务无法只凭当前画面决定该回哪个抽屉。`primitive_order` 既作为评测时的真值序列，也驱动数据生成阶段的自动执行，还作为语言子任务标注保留下来，一序三用。

## 导航

- 返回上级：[RoboMemArena](../03-robomemarena.md)
- 上一节：[概览与定位](01-overview.md)
- 下一节：[记忆负载与标注](03-memory-load-and-annotation.md)
