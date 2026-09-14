# MolmoSpaces-Bench

MolmoSpaces-Bench 将机器人策略放入固定的模拟 episode 中执行闭环 rollout。episode 指定场景、机器人与相机初始状态、物体布置和语言任务；策略持续接收观测并输出动作，任务的几何、接触或关节状态决定本次 rollout 是否成功。分数因此记录策略在规定 embodiment 和模拟条件下完成具身任务的比例，不是生成视频与参考帧之间的逐帧误差。

MolmoSpaces-Bench 从 MolmoSpaces 的大规模资产中构造评测 episode：资产池包含超过 23 万个室内环境、超过 13 万个物体模型，以及 48,000 个可交互物体上的 4,200 万个稳定抓取。八类原子任务把这些场景、对象和语言指令组合为 navigation、静态操作与移动操作的测试实例。固定 episode 使不同策略面对相同初始条件；跨场景、对象类别和实例的均衡采样使成功率反映既定评测分布中的泛化，而非少量手选场景中的表现。

<figure>
  <img src="08-molmospaces-bench/assets/ecosystem-overview.png" alt="MolmoSpaces 将大量室内环境、物体和抓取标注转换为 Isaac Sim、ManiSkill 和 MuJoCo 中的物理交互，并以基准成功率与真实世界成功率对照" />
  <figcaption>MolmoSpaces 的资产、模拟器与基准关系。右上角的相关性图将模拟成功率与真实任务成功率并列；这种对应仅覆盖图中测量的任务和策略集合。</figcaption>
</figure>

## 章节内容

| 页面 | 主要内容 |
| --- | --- |
| [基准设计与覆盖范围](08-molmospaces-bench/01-benchmark-design-and-coverage.md) | 场景、物体、抓取资产与固定 episode 如何构成评测分布 |
| [任务、成功条件与机器人 embodiment](08-molmospaces-bench/02-tasks-success-conditions-and-embodiments.md) | 八类原子任务、几何阈值、语言约束和 FR3 / RB-Y1 配置 |
| [Episode 契约与评测流水线](08-molmospaces-bench/03-episode-contract-and-evaluation-pipeline.md) | `benchmark.json`、策略接口、rollout、结果对象与控制参数 |
| [策略比较与受控变化](08-molmospaces-bench/04-policy-comparison-and-controlled-variation.md) | 零样本比较前提、终止口径、提示与传感器扰动 |
| [结果、sim-to-real 与版本演进](08-molmospaces-bench/05-results-sim-to-real-and-versioning.md) | 零样本结果、相关性解释、MS-Bench v1/v2、MolmoBot 与适用范围 |

## References

- Documentation: [MolmoSpaces](https://allenai.github.io/molmospaces/)
- Paper: [MolmoSpaces: A Large-Scale Open Ecosystem for Robot Manipulation and Navigation](https://arxiv.org/abs/2602.11337)
- GitHub repository: [allenai/molmospaces](https://github.com/allenai/molmospaces)
- Dataset: [allenai/molmospaces](https://huggingface.co/datasets/allenai/molmospaces)

## 导航

- 返回上级：[世界模型评测](../03-world-model-benchmarks.md)
- 上一节：[WoW-World-Eval](07-wow-world-eval.md)
