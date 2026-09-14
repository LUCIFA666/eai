# 综合分数、人工评测与结果

## 结果聚合与统计单位

标准指标、VLM 判别器、JEPA 和 Action Following 形成不同统计层级的结果。多数指标对应单个回合，JEPA Similarity 则对应整个模型视频集合；把同一个 JEPA 值放入多行不会使它变成逐视频指标。完整 EWMScore 还需要统一指标方向和尺度，再在模型层聚合。

## 方向统一与归一化

16 项指标具有不同范围和方向。多数指标已按越高越好构造，Depth Accuracy 的原始值是越低越好的误差。论文定义的正向归一化为

$$
\tilde S=\operatorname{clip}\left(
\frac{S-S_{\min}}{S_{\max}-S_{\min}},0,1
\right),
$$

负向误差使用

$$
\tilde S=1-\operatorname{clip}\left(
\frac{S-S_{\min}}{S_{\max}-S_{\min}},0,1
\right).
$$

`clip` 把边界外的归一化值截断到 0 或 1。论文 v2 给出的 empirical bounds 为

| 指标 | 经验下界 | 经验上界 | 原始方向 |
| --- | ---: | ---: | --- |
| Photometric Consistency | 0.1257 | 6.7899 | 越高越好 |
| Motion Smoothness | 0.0000 | 2.6413 | 越高越好 |
| Trajectory Accuracy | 0.0000 | 40.8540 | 越高越好 |
| Flow Score | 0.0531 | 8.9414 | 越高越好 |
| Depth Accuracy | 0.2228 | 4.3711 | 越低越好 |

论文正文称边界来自 8 个模型的全部视频，v2 主结果表实际包含 14 个模型。基于其他模型集合重新估计的百分位具有不同尺度，不能混入同一次总分比较。其余指标通过固定缩放、判别器分数或评测器内部映射进入聚合。

## EWMScore

论文定义将 16 个归一化指标缩放到 0–100 后取算术平均：

$$
\operatorname{EWMScore}
=\frac{100}{16}\sum_{k=1}^{16}\tilde S_k.
$$

等权发生在指标层，不是六个维度层。含 3 项指标的维度对总分贡献高于含 2 项的维度；Dynamic Degree 参与三项一致性惩罚，CLIP 也被多个分项复用，指标之间并非统计独立。

完整 EWMScore 要求 16 项均有效。缺失项填 0 会把管线失败计入模型质量，填均值会改变实际权重。不完整评测只能形成分项、有效样本数和覆盖率，不能与完整总分直接排序。

## 官方 v2 感知结果

v2 主结果比较 14 个模型。感知分项没有单一模型全面领先：

- Wan 2.6 在 Image Quality、Dynamic Degree、Flow Score 和 Motion Smoothness 上取得表中最高值。
- Veo 3.1 的 Aesthetic Quality、Perspectivity 和 Instruction Following 较强。
- CogVideoX 的 JEPA Similarity 最高。
- CtrlWorld 在 Subject Consistency 和 Trajectory Accuracy 上领先。
- IRASim 的 Depth Accuracy 最高。

这些是论文官方实验结果，不是课程仓库重新运行评测器得到的数值。最优项分散在通用视频模型和具身模型之间，说明外观、参考轨迹与动作条件建模并未由同一模型共同达到最优。Action Following 的高值只表示条件响应差异，仍需与正确性分项联合解释。

## 人工评测

WorldArena v2 使用两类人工评测。第一类从整体视频质量、指令遵循和物理合理性三个方面给出 1–5 分，再转换到 0–100。第二类在同一提示词下成对展示两个模型的视频，由标注者选择较优结果并形成成对胜率。实验招募 70 名标注者，共评估 3500 段视频。

论文报告 EWMScore 与人工评测的 Pearson 相关系数为 `r=0.825`。这一模型级相关性只对应所评 14 个模型和样本，说明综合自动分数与人工排序较为一致；它不表示每项自动指标同样可靠，也不能保证更换模型分布、VLM 判别器或机器人场景后仍有相同相关性。

成对偏好依赖对手采样和展示顺序，自动分数则受辅助模型、抽帧与边界影响。两类证据相互验证，不构成逐视频等价判断。

## 解释边界

相同 EWMScore 可能来自完全不同的分项组合，超出经验边界的差异还会被截断。完整解释同时依赖原始指标、归一化指标、有效样本数、失败率和维度统计。

视频质量结论限定于 RoboTwin 双臂操作、固定视频协议和既定评测器。单项领先只支持对应测量对象内的判断，EWMScore 领先只支持同一协议下的综合生成质量，均不能证明模型已经掌握完整物理规律或能够安全部署。

## 导航

- 返回上级：[视频质量评测](../03-video-quality-evaluation.md)
- 上一节：[功能结果与感知—功能差距](../04-embodied-task-evaluation/04-functional-results.md)
- 下一节：[WorldArena 2.0](../../02-worldarena-2.md)
