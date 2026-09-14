# 结果与发现

下面的结果来自 RoboMME 论文的评测：16 个任务、每任务 50 个 episode、9 次运行取平均，成功率按百分比给出。

## 主结果

| 方法 | 平均成功率 |
|---|---|
| Human（参照） | 90.50 |
| GroundSG + Oracle（符号上界） | 84.08 |
| SimpleSG + Oracle（符号上界） | 49.58 |
| FrameSamp + Modul（最佳非上界变体） | 44.51 |
| MemER（最强先前方法） | 42.38 |
| TokenDrop + Modul | 38.04 |
| TokenDrop + Expert | 34.86 |
| TokenDrop + Context | 34.50 |
| GroundSG + QwenVL（最佳符号） | 32.70 |
| FrameSamp + Expert | 36.25 |
| FrameSamp + Context | 30.68 |
| SimpleSG + QwenVL | 29.00 |
| TTT（Context / Modul / Expert） | 22.28 / 21.96 / 22.35 |
| RMT（Context / Modul / Expert） | 19.46 / 20.17 / 18.15 |
| SAM2Act+ | 21.37 |
| π0.5 w/ past actions | 19.73 |
| π0.5（无记忆） | 17.93 |

无记忆的 π0.5 只有 17.93，最好的记忆变体 FrameSamp+Modul 到 44.51，配合真值子目标的 GroundSG+Oracle 能到 84.08，而人类是 90.50。记忆机制带来明显提升，但离上界和人类都还很远，benchmark 没有饱和。

这份排名本身已经点出了失败所在：无记忆的 π0.5 停在全场最低的 17.93，给它加上过去动作也只微升到 19.73，说明单纯回看动作历史补不上记忆缺失；成功率还随难度系统性退化，遮挡容器数、计数次数、视频长度往上加时各类方法都逐档掉分。失败集中在两处：一是纯反应式策略在需要跨步保留信息的任务上几乎无从下手，二是即便有了记忆、在 StopCube、InsertPeg 这类操作密集任务上低层视觉运动控制仍会拖垮成功率。

## 谁在什么任务上强

强项高度分套件、分任务，没有一个方法全面占优：

- 符号记忆擅长计数类：SimpleSG+QwenVL 在 BinFill 77.56、PickXtimes 95.33，因为子目标能显式记住"已放几个"。
- 感知记忆擅长运动模仿与时机类：FrameSamp+Modul 在 PatternLock 53.56、RouteStick 66.67、StopCube 42.00、VideoPlaceButton 60.00 都是非上界里的最好或接近最好。
- grounding 帮助空间遮挡：GroundSG+QwenVL 在 VideoUnmask 到 88.67。
- 最强先前方法 MemER 在 ButtonUnmask 72.00、PickHighlight 70.67、MoveCube 82.67 上突出，它靠 VLM 从累积关键帧推子目标。

按 6 类功能需求分组也能看出互补：FrameSamp+Modul 在运动为主（约 54.95）、时机敏感（42.00）、长视频推理上最好；符号记忆在短程、事件显著类上最好（SimpleSG+QwenVL 约 84.96）；MemER 在动态场景变化类最好（约 54.67）。

## 主要发现

- 哪种表示/集成最强：感知记忆整体最好，memory-as-modulator 是最优集成方式（轻量、保留 π0.5 预训练表示）；循环记忆最差，浅层循环微调不稳定；符号里 GroundSG 总体强于 SimpleSG。
- 仅靠高层符号够不够：GroundSG+Oracle（84.08）能解很多任务，但在 StopCube、InsertPeg 这类操作密集任务上仍退化，低层视觉运动控制才是瓶颈。
- 人类水平：把任务改成在线 VideoQA 后人类整体 90.5，仍在 PatternLock、StopCube 上出错，benchmark 本身难。
- 记忆设计要随任务特性选：强项互补，没有通用最优。
- 效率与性能：FrameSamp+Modul 的性价比最好；GroundSG+QwenVL 约为 π0.5 的 3 倍算力，MemER 约 5 倍。
- 真机能否迁移：能，趋势与仿真一致。

## 真机迁移

真机迁移在 4 个真机任务上验证，它们分别对应仿真里的计数、遮挡追踪、重拾、路径复现（PutFruits、TrackCube、RepickBlock、DrawPattern），共 350 条演示：

| 方法 | PutFruits | TrackCube | RepickBlock | DrawPattern | 合计 |
|---|---|---|---|---|---|
| π0.5 | 2/10 | 1/10 | 1/10 | 0/10 | 4/40 |
| GroundSG + QwenVL | 9/10 | 3/10 | 5/10 | 2/10 | 19/40 |
| FrameSamp + Modul | 6/10 | 5/10 | 6/10 | 8/10 | 25/40 |

符号记忆在计数任务 PutFruits 上最好，感知记忆在运动为主的 DrawPattern 上最好，和仿真里的强项互补一致。

## 导航

- 返回上级：[RoboMME](../02-robomme.md)
- 上一节：[MME-VLA 记忆方法](07-mme-vla-methods.md)
- 下一节：[数据集](09-datasets.md)
