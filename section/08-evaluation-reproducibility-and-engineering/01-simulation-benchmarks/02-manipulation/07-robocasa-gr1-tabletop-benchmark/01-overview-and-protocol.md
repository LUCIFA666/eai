# 9.1.6.1 Benchmark 概览

目标：建立对 RoboCasa-GR1 Tabletop 评测协议的整体认识，知道该benchmark在测什么、怎么测、结果如何解读。

RoboCasa-GR1 Tabletop Tasks 是 RoboCasa / robosuite 生态中的一组 GR-1 人形机器人桌面操作仿真环境。官方仓库将其定位为 GR00T-N1.5-3B 等通用机器人策略的 simulation environments，用于在闭环交互中评估策略在家庭桌面任务上的行为表现。在给定任务环境、机器人本体、观测接口、动作接口、模型 checkpoint 和运行参数后，策略能否通过连续决策完成指定桌面操作目标。

## Benchmark 对象

RoboCasa-GR1 Tabletop 可以拆成四个评测对象：

| 组成 | 含义 | 对应 |
|---|---|---|
| 任务集合 | 24 个 tabletop manipulation tasks | README 中列出的 `gr1_unified/..._Env` 环境名 |
| 机器人本体 | GR-1 人形机器人，上肢、腰部与 Fourier Hands | 环境名中的 `GR1ArmsAndWaistFourierHands` |
| 仿真环境 | 基于 RoboCasa / robosuite / MuJoCo 的桌面家居场景 | `robocasa-gr1-tabletop-tasks` 仓库与 assets |
| 策略模型 | 根据观测输出动作的 policy | `GR00T-N1.5-3B` 或其 post-training checkpoint |


## 评测问题

该 benchmark 主要考察闭环控制能力，而不是单步预测精度。一次 episode 中，环境在每一步给出当前观测，策略根据观测输出动作，动作被仿真器执行后产生新的状态。这个过程持续到任务成功、失败终止，或达到最大步数。

可以把一次 rollout 写成如下形式：

```text
o_t = observation(env_t)
a_t = policy(o_t, instruction)
env_{t+1} = step(env_t, a_t)
```

其中：

| 符号 | 含义 |
|---|---|
| `o_t` | 当前时刻观测，通常包含视觉、机器人状态和任务相关条件 |
| `instruction` | 任务语言或任务条件，用于指定当前目标 |
| `a_t` | 策略输出的机器人动作 |
| `env_t` | 仿真环境在第 `t` 步的状态 |

这种设置会暴露离线指标不容易体现的问题，比如接触误差、物体位姿偏移、动作抖动、早期小错误在长程任务中的累积。

## 具体任务介绍

README 中的最小评测单位是一个环境名，共有24种任务，以其中一种举例：

```text
gr1_unified/PnPCupToDrawerClose_GR1ArmsAndWaistFourierHands_Env
```

这个名字可以拆成几层信息：

| 字段 | 例子 | 说明 |
|---|---|---|
| 任务域 | `gr1_unified` | GR-1 统一任务集合 |
| 任务目标 | `PnPCupToDrawerClose` | pick-and-place cup to drawer，并关闭抽屉 |
| 机器人配置 | `GR1ArmsAndWaistFourierHands` | 使用 GR-1 双臂、腰部与 Fourier Hands |
| 环境类型 | `_Env` | robosuite / gym 风格环境类 |


## 24 个 Tabletop 任务

官方给出的任务一共有 24 个，全部位于 `gr1_unified` 任务域下。它们可以粗略分成两类：前 6 个是比较直接的 pick-and-place 后关闭容器任务；后 18 个带有 `PosttrainPnPNovel...SplitA` 命名，主要覆盖不同起点、目标容器和新物体组合。从命名上看，`PnP` 表示 pick-and-place；`From...To...` 表示物体从某类起始区域移动到目标容器或目标表面；`Close` 表示任务还包含关闭抽屉、柜门或微波炉等后续动作。

| 序号 | 任务名 | 完整环境名 |
|---|---|---|
| 1 | `PnPCupToDrawerClose` | `gr1_unified/PnPCupToDrawerClose_GR1ArmsAndWaistFourierHands_Env` |
| 2 | `PnPPotatoToMicrowaveClose` | `gr1_unified/PnPPotatoToMicrowaveClose_GR1ArmsAndWaistFourierHands_Env` |
| 3 | `PnPMilkToMicrowaveClose` | `gr1_unified/PnPMilkToMicrowaveClose_GR1ArmsAndWaistFourierHands_Env` |
| 4 | `PnPBottleToCabinetClose` | `gr1_unified/PnPBottleToCabinetClose_GR1ArmsAndWaistFourierHands_Env` |
| 5 | `PnPWineToCabinetClose` | `gr1_unified/PnPWineToCabinetClose_GR1ArmsAndWaistFourierHands_Env` |
| 6 | `PnPCanToDrawerClose` | `gr1_unified/PnPCanToDrawerClose_GR1ArmsAndWaistFourierHands_Env` |
| 7 | `PosttrainPnPNovelFromCuttingboardToBasketSplitA` | `gr1_unified/PosttrainPnPNovelFromCuttingboardToBasketSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 8 | `PosttrainPnPNovelFromCuttingboardToCardboardboxSplitA` | `gr1_unified/PosttrainPnPNovelFromCuttingboardToCardboardboxSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 9 | `PosttrainPnPNovelFromCuttingboardToPanSplitA` | `gr1_unified/PosttrainPnPNovelFromCuttingboardToPanSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 10 | `PosttrainPnPNovelFromCuttingboardToPotSplitA` | `gr1_unified/PosttrainPnPNovelFromCuttingboardToPotSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 11 | `PosttrainPnPNovelFromCuttingboardToTieredbasketSplitA` | `gr1_unified/PosttrainPnPNovelFromCuttingboardToTieredbasketSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 12 | `PosttrainPnPNovelFromPlacematToBasketSplitA` | `gr1_unified/PosttrainPnPNovelFromPlacematToBasketSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 13 | `PosttrainPnPNovelFromPlacematToBowlSplitA` | `gr1_unified/PosttrainPnPNovelFromPlacematToBowlSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 14 | `PosttrainPnPNovelFromPlacematToPlateSplitA` | `gr1_unified/PosttrainPnPNovelFromPlacematToPlateSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 15 | `PosttrainPnPNovelFromPlacematToTieredshelfSplitA` | `gr1_unified/PosttrainPnPNovelFromPlacematToTieredshelfSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 16 | `PosttrainPnPNovelFromPlateToBowlSplitA` | `gr1_unified/PosttrainPnPNovelFromPlateToBowlSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 17 | `PosttrainPnPNovelFromPlateToCardboardboxSplitA` | `gr1_unified/PosttrainPnPNovelFromPlateToCardboardboxSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 18 | `PosttrainPnPNovelFromPlateToPanSplitA` | `gr1_unified/PosttrainPnPNovelFromPlateToPanSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 19 | `PosttrainPnPNovelFromPlateToPlateSplitA` | `gr1_unified/PosttrainPnPNovelFromPlateToPlateSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 20 | `PosttrainPnPNovelFromTrayToCardboardboxSplitA` | `gr1_unified/PosttrainPnPNovelFromTrayToCardboardboxSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 21 | `PosttrainPnPNovelFromTrayToPlateSplitA` | `gr1_unified/PosttrainPnPNovelFromTrayToPlateSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 22 | `PosttrainPnPNovelFromTrayToPotSplitA` | `gr1_unified/PosttrainPnPNovelFromTrayToPotSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 23 | `PosttrainPnPNovelFromTrayToTieredbasketSplitA` | `gr1_unified/PosttrainPnPNovelFromTrayToTieredbasketSplitA_GR1ArmsAndWaistFourierHands_Env` |
| 24 | `PosttrainPnPNovelFromTrayToTieredshelfSplitA` | `gr1_unified/PosttrainPnPNovelFromTrayToTieredshelfSplitA_GR1ArmsAndWaistFourierHands_Env` |



## 数据规模

RoboCasa-GR1 Tabletop 提供了相关数据集。RoboCasa-GR1 Tabletop benchmark 是 24 个评测环境；GR00T Teleop Simulation Dataset 是这 24 个任务上的 24000 条遥操作演示；240k trajectories dataset 是用于后训练的更大规模训练数据。

| 数据 / 资源 | 规模 | 作用 |
|---|---|---|
| RoboCasa-GR1 Tabletop benchmark | 24 个 tabletop task environments | 用于闭环评测策略，统计 success rate |
| GR00T Teleop Simulation Dataset | 24 个任务 × 1000 条 demos = 24000 条 demonstration trajectories | 用于 demonstration 回放、数据检查，也可作为训练/分析数据 |
| Humanoid robot tabletop manipulation dataset | 约 240k trajectories | README 中 post-training 示例使用的更大规模训练数据 |

## 评测协议

在这一节里，评测协议只需要先理解为一组固定条件：给定任务环境、机器人本体、观测与动作接口、策略模型、episode 数和最大步数，观察策略能否在闭环交互中完成任务。


官方实现采用 inference server 和 simulation client 的结构：前者负责加载模型并输出动作，后者负责运行仿真、收集成功标记并保存 rollout 视频。具体启动命令和参数放在后面的“GR00T 闭环仿真评估”小节中展开。

## 评测指标

本 benchmark 最核心的指标是 **success rate**：

```text
success_rate = 成功 episode 数 / 总 episode 数
```



