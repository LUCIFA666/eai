# WorldArena

WorldArena 以机器人操作视频为统一观察界面，同时检查具身世界模型的生成质量与功能效用。模型接收初始观测以及语言指令或动作轨迹，生成未来视频；评测既分析画面、运动、内容、物理、几何和可控性，也把模型接入数据合成、策略评估和动作规划流程。感知结果与功能结果由此进入同一套实验框架。

视频质量部分由 6 个维度、16 项自动指标组成。各指标分别依赖无参考图像质量模型、视觉特征、光流、单目深度、目标轨迹和 VLM 判别器，测量对象与参照条件并不相同。EWMScore 对这些分项进行方向对齐和归一化，提供同一协议内的综合比较；人工评测则补充接触合理性、指令执行和整体观感等主观判断。

论文框架由视频质量评测、具身任务评测和人工评测三部分组成。具身任务评测进一步包含 Data Engine、Policy Evaluator 与 Action Planner，分别检查生成数据、环境代理和动作规划的功能价值。

## 章节内容

| 模块 | 页面 | 主要内容 |
| --- | --- | --- |
| 基础 | [评测框架](01-worldarena/01-benchmark-framework.md) | 开环评测、闭环评测、主客观评测及适用边界 |
| 基础 | [数据与任务协议](01-worldarena/02-data-and-task-protocol.md) | RoboTwin 2.0 Clean-50、条件输入、视频契约和数据划分 |
| 视频质量 | [视频质量评测](01-worldarena/03-video-quality-evaluation.md) | 六个感知维度、参照类型、评测数据流和统计层级 |
| 具身任务 | [具身任务评测](01-worldarena/04-embodied-task-evaluation.md) | Data Engine、Policy Evaluator 与 Action Planner 的系统边界 |
| 人工评测 | [综合分数、人工评测与结果](01-worldarena/03-video-quality-evaluation/07-score-human-results.md) | EWMScore、维度打分、成对偏好和结果解释 |

## References

- Project page: [WorldArena](https://world-arena.ai/)
- Paper: [WorldArena: A Unified Benchmark for Evaluating Perception and Functional Utility of Embodied World Models](https://arxiv.org/abs/2602.08971)
- GitHub repository: [tsinghua-fib-lab/WorldArena](https://github.com/tsinghua-fib-lab/WorldArena)
- Dataset: [WorldArena_Robotwin2.0](https://huggingface.co/datasets/WorldArena/WorldArena_Robotwin2.0)

## 导航

- 返回上级：[世界模型评测](../03-world-model-benchmarks.md)
- 下一节：[WorldArena 2.0](02-worldarena-2.md)
