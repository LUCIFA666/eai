# MME-VLA 记忆方法

MME-VLA 是论文随 RoboMME 提出的一组记忆增强策略，都以 π0.5 为 backbone，把记忆拆成两个正交的维度来比较：记忆表示（历史信息编码成什么）和集成方式（这段记忆怎么接进策略）。

## 三类记忆表示

- 符号记忆（symbolic）：把历史压成语言子目标。SimpleSG 给简单指令（如 `pick up the red cube for the first time`），GroundSG 在同一句里嵌入目标的前视图像素坐标（如 `pick up the red cube at <134, 88> for the first time`，坐标是 256×256 前视图上的整数、范围 0 到 255）。子目标由一个辅助 VLM 逐步生成，与任务指令拼在一起送进策略（形如 `Task: ...; Current Subgoal: ...; Action:`）。生成器在评测期选择：Gemini-2.5-Pro、微调过的 Qwen3-VL-4B，或仿真真值 Oracle（作上界）。
- 感知记忆（perceptual）：用 π0.5 视觉编码器抽的视觉 token 表示历史。TokenDrop 把每帧切成 8×8 共 64 个 patch，按帧间像素 RGB 差异打分、丢掉变化极小的（差异低于阈值直接跳过），每若干步算一次差异，保留变化最大的一批 token；FrameSamp 每帧取 4×4 共 16 个 token，沿时间均匀采样，在 512 token 预算下最多约 32 帧。两者是互补的取舍：TokenDrop 偏局部的显著变化，FrameSamp 偏全局的时间覆盖。
- 循环记忆（recurrent）：把历史视觉 token 压成固定大小的隐状态，不随 episode 变长而增大。RMT（Recurrent Memory Transformer）用 512 个可学习的 memory slot（等于记忆预算），分段对输入做 cross-attention 递归更新；TTT（Test-Time Training）用一组在线更新的快权重承载记忆，靠自监督目标做 test-time 优化。

记忆预算固定在 512 个 token，与 π0.5 当前观测的视觉 token 数对齐：RMT 的 slot 数、TokenDrop 与 FrameSamp 保留的 token 数都以此为上限。

## 三种集成方式

符号记忆本身就是语言 token，直接和任务指令拼接即可。感知与循环记忆产出的是神经记忆 token，要改结构才能接进动作预测，有三种接法：

- Memory-as-Context：把记忆 token 拼在输入 token 前，一起送进 VLM expert；用注意力掩码让当前视觉 token 不去 attend 记忆 token，而动作 token 能看到记忆。最简单，但会拉长上下文、可能干扰原有表示。
- Memory-as-Modulator：在 action expert 每层前馈块之前，让动作特征对记忆 token 做多头 cross-attention（动作作 query、记忆作 key/value），再用 AdaLN 把结果投影成 scale 与 shift，调制归一化后的动作特征。记忆只作为动作通路的条件信号，VLM 主干保持不变。
- Memory-as-Expert：新增一个轻量记忆 expert（gemma_150m），三个 expert 通过块状因果注意力交互——动作 expert 同时看 VLM expert 与记忆 expert，而后两者互不 attend，从而隔离干扰、给记忆处理留出专门容量。

## 变体组合

一共 14 个 MME-VLA 变体：感知记忆的 TokenDrop、FrameSamp 各配三种集成，得 6 个；循环记忆的 TTT、RMT 各配三种集成，得 6 个；符号记忆因为本就是语言 token、只走 context 一种集成，取 SimpleSG、GroundSG 两个，得 2 个。命名按 方法+集成，例如 `FrameSamp+Modul`。符号记忆的子目标生成器（Gemini / QwenVL / Oracle）是评测期的选择、共用同一套符号记忆权重，其中 Oracle 用真值子目标，作为上界不计入这 14 个。

## 训练与评测配置

所有变体多任务训练：动作块 `action_horizon=20`，评测时执行前 16 步再重新预测；训练 80k step、batch 64，用 cosine 学习率（warmup 10k、峰值 5e-5）、AdamW（梯度裁剪 1.0）、EMA 0.999，4 卡 FSDP。VLA backbone 默认全量微调，只冻结视觉编码器；权重从 `pi05_base` 初始化。符号记忆的子目标预测器单独训练：Qwen3-VL-4B 用 LoRA（rank 16、alpha 32）、2 个 epoch、学习率 1e-4。

有两处论文与实现的口径要注意：论文提到 recurrent 变体因显存用 batch 16，但代码里 recurrent 的训练脚本仍是 batch 64；论文提到的 LoRA rank 16 指的是上面的 VLM 子目标预测器，VLA backbone 本身在代码里是全量微调、并未用 LoRA。

## 对照的先前方法

除 14 个变体外，还有 4 个已有方法作对照：π0.5（无记忆）、π0.5 加过去动作、SAM2Act+（SAM2 backbone 加记忆库，预测离散关键帧由外部运动规划执行）、MemER（VLM 从累积的关键帧图推子目标，再由 GroundSG 式策略执行，是感知与符号的混合）。

## 导航

- 返回上级：[RoboMME](../02-robomme.md)
- 上一节：[评测协议与指标](06-evaluation-protocol.md)
- 下一节：[结果与发现](08-results-and-findings.md)
