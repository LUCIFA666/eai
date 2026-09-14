# 世界模型评测

## 评测对象与参照

世界模型根据当前观测和条件信息预测环境的未来。条件信息可以是语言指令、动作序列、相机轨迹、触觉信号或机器人状态；模型输出则可能表现为未来状态、潜在表征、视频序列，或能够持续接收动作并返回新观测的交互环境。输入与输出的形式决定了评测可以直接观察哪些误差，也决定了分数对应的能力范围。

条件和任务目标提供第一类参照，用于判断模型是否执行指定动作、保持目标对象并遵循相机控制。真实视频、状态轨迹和物理仿真提供第二类参照，用于比较未来预测、几何结构和动力学演化。规划质量、策略排序、训练收益与真实执行结果构成第三类参照，直接衡量模型对下游任务的作用。

开放式环境通常存在多个合理未来，同一初始状态可能对应不同但都符合条件的轨迹。逐帧像素差异难以单独表示这类预测的合理程度，因此评测通常同时使用 reference-based 与 reference-free 指标。前者比较生成结果与真实数据或仿真标注，后者从语义、视觉质量、时序一致性和物理合理性判断输出本身。

## 从感知质量到功能效用

感知质量描述生成结果能否形成稳定、可辨认的视觉观测，涉及画面清晰度、时序连续性、主体和背景一致性以及跨视角结构。此类指标能够定位闪烁、形变、身份漂移、背景变化和视角切换异常，但对动作后果和任务价值的覆盖有限。

世界规律关注环境如何随时间和动作变化。物体持续性、空间关系、运动轨迹、接触过程、因果关系、材料属性和物理约束共同决定预测是否形成连贯的世界演化。视频可以具有较高的视觉真实感，同时包含穿透、悬浮、尺度突变或错误的动作响应，因此物理与动力学需要独立的诊断维度。

功能效用把评测延伸到世界模型参与的具身任务。世界模型作为 data engine 时，生成数据对策略训练的增益构成结果依据；作为 policy evaluator 时，模型内排序与真实环境排序的一致性反映评估可靠性；作为 action planner 或 RL environment 时，规划成功率、训练稳定性和策略执行结果直接暴露模型误差。像素或特征空间中的较小误差并不必然带来更高的任务成功率。

## 评测协议

单次条件生成在固定初始状态上产生一段未来序列，适合分析局部画质、指令遵循和物理错误。多轮交互将上一轮结果继续作为后续条件，状态遗忘、误差累积和控制响应偏移会随交互轮次显现。两类协议都以生成结果为中心，但多轮设置额外检验长期状态保持和连续可控性。

Policy rollout、RL environment 与 sim-to-real 进一步提高闭环程度。Policy rollout 检查预测偏差如何改变动作选择和任务结果；RL environment 检查模型能否提供足够稳定的观测、转移和反馈，使策略优化持续进行；sim-to-real 比较模拟预测、模型内评估和真实平台执行，衡量仿真结论迁移到物理系统后的有效程度。

评测单位也影响结果含义。Frame-level 指标定位局部视觉或几何误差，clip-level 指标概括一段预测的时序表现，episode-level 结果记录一次完整交互，task-level 统计反映同类任务中的稳定性，model-level score 则对多个维度和任务进行聚合。聚合范围越大，单个失败类型在总分中的位置越不明显。

## Benchmark 对照

以下 benchmark 分别覆盖生成质量、物理概念诊断、多轮交互响应、具身功能效用和模拟器策略泛化。它们采用不同的条件接口与评测单位，共同连接离线生成、交互学习和真实执行。

| Benchmark | 主要输入 | 评测重点 | 评测层级 |
| --- | --- | --- | --- |
| [WorldArena](03-world-model-benchmarks/01-worldarena.md) | 初始帧、指令或动作、生成视频 | 感知质量、data engine、policy evaluator、action planner | 感知与具身功能 |
| [WorldArena 2.0](03-world-model-benchmarks/02-worldarena-2.md) | 视觉、触觉、动作和交互环境 | 多模态预测、RL environment、跨平台迁移 | 交互学习与 sim-to-real |
| [WorldModelBench](03-world-model-benchmarks/03-worldmodelbench.md) | 文本或图像条件、生成视频 | 指令遵循、常识和物理规律 | 单次视频生成 |
| [WorldScore](03-world-model-benchmarks/04-worldscore.md) | 3D、4D、I2V 或 T2V 的统一视频输出 | controllability、quality 和 dynamics | 世界生成 |
| [WBench](03-world-model-benchmarks/05-wbench.md) | 初始图像和多轮交互条件 | navigation、动作、事件编辑、视角切换和长期一致性 | 多轮交互 |
| [WorldBench](03-world-model-benchmarks/06-worldbench.md) | 场景初始帧和未来视频 | motion physics、object permanence、support relations、scale 和 perspective | 物理诊断 |
| [WoW-World-Eval](03-world-model-benchmarks/07-wow-world-eval.md) | 机器人操作初始帧、指令和生成视频 | perception、planning、prediction、generalization 和 execution | Embodied Turing Test |
| [MolmoSpaces-Bench](03-world-model-benchmarks/08-molmospaces-bench.md) | 模拟场景、任务指令和策略 rollout | 任务成功率、systematic variation 和策略泛化 | 模拟器策略评测 |

## 分数的解释边界

不同 benchmark 的数据域、条件接口、预测时长、指标实现和聚合方法各不相同。WorldModelBench、WorldScore 和 WBench 以生成结果为主要对象，WorldBench 与 WoW-World-Eval 分别强调物理概念诊断和 Turing Test，WorldArena 系列及 MolmoSpaces-Bench 则将模型或策略置于下游具身任务中检验。跨 benchmark 的数值缺少共同量纲，同一 leaderboard 内的模型排序也只对应其规定的数据和协议。

综合分数压缩多个任务和维度，适合在同一协议内概括整体表现；诊断性分项保留具体失败类型，更适合分析改进方向。Human evaluation 反映观察者对真实感和任务完成情况的判断，VLM judge 将语义与物理问题转化为自动评分，视觉特征指标衡量帧或视频之间的统计关系，下游任务结果则记录模型误差对行为的实际影响。这些信号的测量对象不同，结论需要与指标来源对应。

单项分数或单个 leaderboard 排名只能支持对应输入、任务和评测协议内的判断。完整的世界建模能力还涉及未覆盖的环境变化、交互时长、机器人 embodiment 和真实执行条件，因而需要结合多类 benchmark 的分项结果描述模型能力。

## 导航

- 返回上级：[世界模型](README.md)
- 上一节：[生成式世界模型](02-generative-world-models.md)
