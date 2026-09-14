# WBench

WBench 将视频世界模型置于连续交互中评测。每个 case 从一张初始图像和一组 world setting 开始，模型根据后续的导航、主体动作、环境编辑或视角切换生成多段视频；后一轮以前一轮的末帧或连续视频状态为条件。评测因而能够同时观察单段视频的观感、动作是否被执行，以及多轮之后场景、主体、相机和物理过程是否仍然相互一致。

基准包含 289 个 case、1,058 个 interaction turn，每个 case 有 2–9 轮交互，平均为 3.7 轮。22 项分项指标覆盖 video quality、setting adherence、interaction adherence、consistency 和 physical 五个维度。它们把 Renderer、Director、Controller、Memory 与 Engine 分别落实为可测量的视频质量、初始世界设定、控制响应、跨轮状态保持和物理演化，而不是用单一视频分数替代这些不同对象。

<figure>
  <img src="05-wbench/assets/teaser.png" alt="WBench 将初始图像、世界设定和多轮交互输入视频世界模型，并从视频质量、设定遵循、交互遵循、一致性和物理五个维度评分" />
  <figcaption>WBench 的评测对象是多轮生成的视频序列。初始帧确定起点，world setting 描述场景、风格、视角和主体，交互序列规定后续变化；五个维度分别保留视觉、语义控制、长期一致性和物理错误的信号。</figcaption>
</figure>

模型接口分为三类。text-conditioned 模型使用文字提示和首帧，可覆盖四类交互；camera-conditioned 模型接收首帧和每轮的 6-DoF 相机位姿；action-conditioned 模型接收首帧和离散动作。后两类接口只与 navigation 的 158 个 case 对应，因而其分数只反映该子集中的相机或动作控制，不能与覆盖全部 case 的 text-conditioned 结果直接合并为统一排名。

WBench 的输出仍是视频和对视频的诊断分数。它没有把模型接入机器人策略优化、奖励反馈或真实平台执行，因此适合判断开放域视频世界模型在多轮条件生成中的控制和记忆表现，不足以单独说明机器人闭环控制、策略训练收益或 sim-to-real 可靠性。

## 章节内容

| 页面 | 主要内容 |
| --- | --- |
| [数据与多轮交互协议](05-wbench/01-data-and-multiturn-protocol.md) | world setting、四类交互、case 字段与多轮统计 |
| [视频、设定与交互指标](05-wbench/02-video-setting-and-interaction-metrics.md) | 6 项 video quality、2 项 setting adherence 和 4 项 interaction adherence |
| [一致性与物理指标](05-wbench/03-consistency-and-physical-metrics.md) | 8 项 consistency、2 项 physical 指标及其辅助模型 |
| [评测器数据流与模型接口](05-wbench/04-evaluator-dataflow-and-interfaces.md) | `case_*.json`、按轮视频切分、预计算结果、聚合报告和三类条件接口 |
| [结果与解释](05-wbench/05-results-and-interpretation.md) | 范式差异、跨维度诊断、人工偏好验证与适用范围 |

## References

- Project page: [WBench](https://meituan-longcat.github.io/WBench/)
- Paper: [WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation](https://arxiv.org/abs/2605.25874)
- GitHub repository: [meituan-longcat/WBench](https://github.com/meituan-longcat/WBench)
- Dataset: [WBench](https://huggingface.co/datasets/meituan-longcat/WBench)

## 导航

- 返回上级：[世界模型评测](../03-world-model-benchmarks.md)
- 上一节：[WorldScore](04-worldscore.md)
- 下一节：[WorldBench](06-worldbench.md)
