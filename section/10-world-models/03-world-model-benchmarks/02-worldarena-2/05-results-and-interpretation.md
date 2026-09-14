# 结果与解释

WorldArena 2.0 的实验结果来自不同的参照对象：触觉预测对齐 UniVTAC 的真实触觉序列，RL protocol 观察在世界模型中训练后回到 RoboTwin 的策略成功率，data engine 与 action planner 则记录三平台任务结果。它们共同描述模型的可用范围，但没有可以互相换算的统一分数。

## Visuotactile：局部接触预测与长程操作

Wan2.2 在 UniVTAC 触觉预测中取得 21.26 PSNR 和 0.746 SSIM，并在 `Insert HDMI` 达到 100% success rate。这个任务需要在插接时分辨细微接触状态，预测质量与执行结果在该设置中同时改善。`Lift Bottle` 给出相反的证据：ACT baseline 达到 80%，而 Vidar、Genie Envisioner 和 Wan2.2 都为 0%。

该差异不能被解释成某个模型“没有触觉能力”。PSNR 和 SSIM 在固定长度预测上比较触觉图像；提瓶要求持续的力控制和长期动作选择，误差会随着闭环时长累积。两项任务一起表明，触觉重建分数、短程接触响应和长程操作稳定性应同时报告。

## RL environment：模型误差经优化放大

在 RoboTwin 2.0 上，SFT policy 在 `Click Bell` 与 `Adjust Bottle` 的成功率分别为 43.75% 和 55.08%。使用 ground-truth simulator 进行 RL 的 policy 在三种 reward 设计下约为 87% 与 79%。世界模型环境训练出的 policy 均未超过 simulator RL；最好的短程结果来自 WoVR 的 75.00%，最好的长程结果来自 Ctrl-World 的 70.70%。

| 比较对象 | Click Bell | Adjust Bottle | 对应结论 |
| --- | ---: | ---: | --- |
| SFT baseline | 43.75 | 55.08 | 仅有监督初始化的策略表现 |
| Simulator-based RL，proxy reward | 87.30 | 78.90 | 真实转移和奖励下的参考上限 |
| WoVR，proxy reward | 75.00 | 67.19 | 短程任务中最好的 world-model RL 结果 |
| Ctrl-World，proxy reward | 69.53 | 70.70 | 长程任务中最好的 world-model RL 结果 |

reward model 改变的不是结果展示方式，而是 policy 实际接收的优化目标。proxy-based reward 在这组实验里更稳定；VLM-based reward 缺少任务微调，similarity-based reward 依赖预测观测与目标帧之间的特征关系。因而不同 reward 列的成功率适合比较“同一 reward 下的 world model”，不适合脱离奖励定义合并排序。

## 跨平台功能结果

论文报告的功能结果覆盖 6 个世界模型、两个 RoboTwin 任务、一个 LIBERO 任务以及 AgileX 的两个真机任务。表中 `Data` 与 `Action` 分别对应 data engine 和 action planner；所有单元格均为 task success rate（%）。

| 模型 | RoboTwin Data T1/T2 | RoboTwin Action T1/T2 | LIBERO Data/Action | Real Data T1/T2 | Real Action T1/T2 |
| --- | --- | --- | --- | --- | --- |
| GigaWorld | 2 / 13 | 6 / 19 | 0 / 0 | 0 / 0 | 0 / 0 |
| Genie Envisioner | 7 / 21 | 10 / 20 | 2 / 6 | 0 / 0 | 0 / 20 |
| TesserAct | 1 / 35 | 1 / 35 | 34 / 38 | 0 / 0 | 0 / 30 |
| Vidar | 13 / 53 | 2 / 19 | 22 / 14 | 40 / 0 | 30 / 10 |
| Wan 2.2 | 15 / 41 | 12 / 20 | 10 / 24 | 10 / 0 | 10 / 0 |
| CogVideoX | 3 / 28 | 8 / 16 | 0 / 2 | 10 / 10 | 0 / 50 |

三平台中，真实任务出现大量零成功率，且非零结果随模型和协议显著变化。RoboTwin 与 LIBERO 的任务成功率存在正相关趋势，真实平台与任一模拟器的相关性明显降低。论文的跨平台感知分析也得到类似但较弱的结论：视觉质量、运动质量、物理与 3D accuracy 的平台间相关性较高；content consistency 和 controllability 对平台变化更敏感。

## 分数的解释范围

| 结果 | 可支持的判断 | 不能单独支持的判断 |
| --- | --- | --- |
| PSNR / SSIM | 在 UniVTAC 对应数据上的触觉序列重建质量 | 长程操作、真实触觉传感器或真机控制能力 |
| 16 项感知指标 | 条件视频的画面、运动、一致性、物理、几何和控制分项 | data engine、RL training 或动作规划的成功率 |
| RL task success rate | 某个 world model 与 reward 组合支持 policy optimization 的程度 | 世界模型单独的 transition fidelity 或真实机器人部署表现 |
| Data Engine / Action Planner success rate | 指定平台和任务上的下游功能效用 | 未覆盖本体、相机、控制频率和任务上的泛化能力 |
| Real-world success rate | AgileX 指定任务上的物理执行结果 | 对所有真实机器人或场景的普遍结论 |

WorldArena 2.0 因此将“生成得像”拆分为多个可检查的命题。触觉预测补充接触观测，RL 环境揭示递归交互下的优化后果，真实任务结果检验 sim-to-real 迁移。三个层面的证据共同缩小判断范围，而不构成一个可替代所有任务的总分。

## 导航

- 返回上级：[WorldArena 2.0](../02-worldarena-2.md)
- 上一节：[跨平台 sim-to-real](04-cross-platform-sim-to-real.md)
