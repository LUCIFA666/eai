# 视频质量评测

视频质量评测将具身世界模型视为条件视频生成器，检查未来视频在外观、运动、时间一致性、交互物理、三维结构和条件响应上的质量。文本驱动模型根据首帧与指令生成操作过程，动作驱动模型根据首帧与动作轨迹生成环境响应。两类模型共享视频评测框架，但条件输入与时间对齐方式不同。

## 六个评测维度

16 项指标按六个维度组织。每个维度保留不同类型的证据，单项高分不能替代其他维度。

| 维度 | 指标 | 主要参照 | 测量对象 |
| --- | --- | --- | --- |
| [Visual Quality](03-video-quality-evaluation/01-visual-quality.md) | Image Quality、Aesthetic Quality、JEPA Similarity | 生成视频自身或 GT 集合 | 帧级画质、审美预测和集合级时空分布 |
| [Motion Quality](03-video-quality-evaluation/02-motion-quality.md) | Dynamic Degree、Flow Score、Motion Smoothness | 生成视频自身 | 局部/全局运动强度和时间连续性 |
| [Content Consistency](03-video-quality-evaluation/03-content-consistency.md) | Subject Consistency、Background Consistency、Photometric Consistency | 生成视频自身 | 主体、场景和运动循环的时间稳定性 |
| [Physics Adherence](03-video-quality-evaluation/04-physics-adherence.md) | Interaction Quality、Trajectory Accuracy | 指令或配对 GT | 可见交互合理性和机械臂路径 |
| [3D Accuracy](03-video-quality-evaluation/05-3d-accuracy.md) | Depth Accuracy、Perspectivity | 配对 GT 或指令 | 相对深度与可见三维关系 |
| [Controllability](03-video-quality-evaluation/06-controllability.md) | Instruction Following、Semantic Alignment、Action Following | 指令、配对 GT 或多路生成 | 任务正确性、参考语义和条件敏感性 |

## 评测器的四条数据流

视频质量评测器将 16 项指标组织为四条数据流：

| 评测器 | 输入 | 覆盖对象 | 输出层级 |
| --- | --- | --- | --- |
| 标准指标 | 生成帧，部分指标加入 GT、指令或目标跟踪结果 | 图像、运动、一致性、深度、轨迹、语义 | 回合级分数 |
| VLM 判别器 | 指令与均匀抽取的视频帧 | Interaction Quality、Perspectivity、Instruction Following | 回合级 1–5 分及缩放结果 |
| JEPA | 生成视频与 GT 视频集合 | 高层时空特征分布 | 模型级集合分数 |
| Action Following | 共享初始帧的多路指令视频 | 条件响应差异 | 回合级多样性分数 |

标准指标先按任务、回合和帧组织视频。有参考指标在生成视频与 GT 视频之间建立严格配对；无参考指标只读取生成视频，但仍受分辨率、帧率与抽帧方式影响。VLM 判别器一次返回三项语义级结果，输出还受提示词、判别器版本和 JSON 解析方式影响。

JEPA 将整组视频映射为 V-JEPA 特征分布，分数描述模型集合，不能还原为单个回合的判断。Action Following 比较同一起点下多路生成结果的特征差异，测量条件敏感性，不直接测量动作正确性。

## 四类参照

- 无参考指标根据生成视频自身判断清晰度、美学、运动和时间稳定性，适用于一对多未来，但无法确认任务路径是否正确。
- 有参考指标比较生成视频与 GT 视频的特征、深度、轨迹或描述，能够检查与示范的一致性，也会惩罚不同于 GT 但仍有效的替代未来。
- 基于指令的指标以任务文本为参照，检查动作类型、目标对象、终态和交互合理性，可靠性依赖 VLM 对视频证据的识别。
- 基于多样性的指标比较相同初态下的多个条件输出，检查模型是否忽略指令；差异较大不表示每条指令都执行正确。

## 统计层级与综合分数

多数指标从帧或帧对开始，在回合内形成逐视频分数，再对有效回合聚合。JEPA Similarity 的统计单位是整个视频集合。把集合分数复制到逐视频 CSV 行不会改变其统计含义。

16 项指标经过方向与尺度对齐后形成 [EWMScore](03-video-quality-evaluation/07-score-human-results.md)。完整总分要求所有分项均有效；缺失回合、集合成员或指标会改变聚合对象与实际权重。

视频质量结果只支持固定数据划分、生成规格、评测器版本和归一化边界下的比较，不能直接表示世界模型作为 Data Engine、Policy Evaluator 或 Action Planner 的功能效用。

## 导航

- 返回上级：[WorldArena](../01-worldarena.md)
- 上一节：[数据与任务协议](02-data-and-task-protocol.md)
- 下一节：[Visual Quality](03-video-quality-evaluation/01-visual-quality.md)
