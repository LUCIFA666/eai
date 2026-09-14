# Video Action Model

目标：理解 Video Action Model（VAM）范式——以视频生成模型为策略骨架，将机器人动作预测建模为视频生成问题。

## 与其他范式的区别

| 范式 | 建模方式 | 动作来源 |
|------|---------|---------|
| BC / ACT / DP | 观测 → 动作 | 策略网络直接输出 |
| VLA | 视觉 + 语言 → 动作 token | 自回归解码 |
| WAM | 联合预测未来状态 + 动作 | 世界模型与策略耦合 |
| **VAM** | 观测 → 生成未来视频 → 提取动作 | 视频生成 + 逆动力学或联合解码 |

VAM 的核心假设是：视频生成模型在大规模互联网视频上预训练后，已经隐式学会了物理规律、物体交互和空间变换。将这些能力迁移到机器人控制上，比从零训练策略更高效。

## 典型流程

1. 用大规模视频数据预训练视频生成模型（扩散模型或自回归模型）
2. 给定当前观测和语言指令，生成未来视频帧序列
3. 从生成的视频中提取动作：通过逆动力学模型、联合解码或光流估计

## 代表性工作

### UniPi

将策略预测直接建模为文本条件的视频生成问题。给定当前图像和语言指令，用扩散模型生成未来视频计划，再通过逆动力学模型从相邻帧提取动作。首次提出 video as universal policy interface 的概念。

[https://universal-policy.github.io/](https://universal-policy.github.io/)

### Unified Video Action Model (UVA)

在 UniPi 基础上改进，将视频生成和动作预测统一在单一模型中联合训练，避免了逆动力学模型的误差累积。在仿真和真机环境上均优于 UniPi。

[https://github.com/ShuangLI59/unified_video_action](https://github.com/ShuangLI59/unified_video_action)

### GR-2

字节跳动发布的大规模视频生成机器人模型。先在海量互联网视频上预训练视频生成能力，再在机器人数据上微调，同时生成未来视频和预测动作。展示了视频预训练规模对机器人策略质量的正向影响。

[https://gr2-manipulation.github.io/](https://gr2-manipulation.github.io/)

### SuSIE

通过视频预测模型生成子目标图像（subgoal image），再用目标条件策略执行到该子目标。将长程任务分解为"生成下一个视觉子目标 → 执行到子目标"的循环，降低了单步视频预测的难度。

[https://rail-berkeley.github.io/susie/](https://rail-berkeley.github.io/susie/)

## 优势与局限

**优势**：可以利用海量互联网视频预训练，获得丰富的视觉先验和物理常识；天然支持视觉可解释性（可以直接看模型"想象"的未来）。

**局限**：视频生成的推理延迟较高，难以满足实时控制需求；生成质量不等于控制精度——视觉上合理的视频不一定对应精确的动作；依赖逆动力学模型的方案会引入额外误差。

## 扩展阅读

Awesome Video Action Models 汇总了该方向的主要论文和代码：

[https://github.com/zhiheng-ma/awesome-video-action-models](https://github.com/zhiheng-ma/awesome-video-action-models)
