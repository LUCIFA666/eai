# 概览与定位

MIKASA-Robo-VLA 是一套 90 个桌面操作任务的 benchmark，在部分可观测环境下评测 Vision-Language-Action（VLA）模型的记忆能力。每个任务里，决定动作所需的信息在做决策时已经不再直接可见：可能是之前看到的物体颜色、目标出现的先后顺序、洗牌后隐藏物体的位置，或到当前为止累积的事件次数。策略要把这些线索保留、更新或持续追踪下来，才能正确完成任务。

## 要评测的能力

桌面操作 benchmark 通常在全可观测下评测，当前一帧观测就足以决定动作。MIKASA-Robo-VLA 针对相反的情形：任务被设计成非马尔可夫的，当前观测不足以推出正确动作，模型必须依赖历史观测与动作，这样才能把有记忆的策略和纯反应式的策略区分开。

任务覆盖 10 类记忆，横跨 25 到 2160 步的时间跨度和多个难度档，记忆需求也拉得很开：短的只需回忆一个刚看过的线索，长的要在整段 episode 里持续追踪被移动的物体，或者先记住一个目标、做完中间步骤后再回来达成。这些需求在真实操作里很常见，比如物体被遮挡、动作要按要求重复固定次数、步骤之间有先后依赖，而以当前观测直接映射动作的反应式策略难以覆盖。

## 底座与配套材料

MIKASA-Robo-VLA 建立在 ManiSkill 上，仿真在 GPU 上并行运行，机器人是带腕部相机的 Franka Panda。除了 90 个任务本身，它还提供配套的训练与评测材料：每个任务附一条自然语言指令，供 VLA 按文本条件化；每个环境都有标定过的 dense 与 normalized-dense 奖励，既支持离线模仿学习、也支持在线 RL；任务按时间跨度分成 Short、Medium、Long 三档，便于多任务训练与评测；另有 22500 条由 PPO oracle 和运动规划采集的轨迹、合计六百多万个 timestep，以 RLDS 与 LeRobotDataset v3 格式发布。

## 与 MIKASA-Robo（RL 原版）的关系

MIKASA-Robo-VLA 扩展自 MIKASA-Robo，后者是一套面向记忆 RL 的桌面操作 benchmark。相比 RL 原版，VLA 版的变化是：

- 任务从 32 个增加到 90 个，记忆类型从 4 类扩到 10 类。
- 每个任务附一条自然语言指令 `LANGUAGE_INSTRUCTION`，供 VLA 按文本条件化。
- 按时间跨度分成 Short / Medium / Long 三档，便于多任务训练与评测。
- 放出 22500 条 oracle 轨迹（RLDS 与 LeRobotDataset v3 格式），并为每个任务标定 dense 奖励。

RL 原版仍保留在 `mikasa-robo-rl` 分支和 `mikasa_robo_suite/rl/` 下。

## 导航

- 返回上级：[MIKASA-Robo-VLA](../01-mikasa.md)
- 下一节：[记忆类型体系](02-memory-taxonomy.md)
