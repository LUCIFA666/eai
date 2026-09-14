# 结果与解释

WBench 的结果呈现出明显的范式分工。text-conditioned 模型拥有更广的语义条件接口，因而在 setting adherence、event editing 和 subject action 上更具优势；camera-conditioned 与 action-conditioned 世界模型在 navigation 上更接近原生控制接口。五类维度的相对排序并不稳定，单项领先不能代表模型在所有多轮行为上都更可靠。

## 模型范式与维度差异

论文的 navigation split 比较显示，camera-conditioned 与 action-conditioned 模型的平均 navigation 分数分别为 76.0 和 77.7，高于 text-conditioned 模型的 67.6。文本模型通过将离散动作翻译成自然语言提示来生成视频，较难稳定保留精确的空间参考；显式位姿或动作输入直接把控制信号送入模型，因此更容易遵循移动方向和相对路径。

文本模型在 setting adherence 与 physical 上占优。以公开结果为例，Wan 2.7 的 setting adherence 为 91.4、physical 为 71.8，Kling 3.0 的 setting adherence 为 91.0；它们的广泛视觉生成先验有利于遵循场景语义和产生较可信的物理外观。world model 的控制训练不会自动补齐开放域场景和主体描述能力，因而导航领先与 scene adherence 领先可以属于不同模型。

| 维度 | 结果中出现的主要差异 | 分数解释 |
| --- | --- | --- |
| Video quality | 多数模型在 flickering 和 smoothness 上接近饱和 | 画面稳定不表示动作响应正确 |
| Setting adherence | text-conditioned 模型明显领先，差距主要出现在 scene | 开放域语言与图像先验影响场景和离屏元素 |
| Interaction | 原生相机/动作接口在 navigation 上领先；文本模型覆盖语义交互 | 不同接口覆盖的任务集合不同 |
| Consistency | LingBot-World 的总体 consistency 领先，但各子项并不同步 | 几何、空间、主体和视角稳定性不是同一个性质 |
| Physical | text-conditioned 模型整体较高 | 生成先验可改善物理外观和因果合理性，但不保证控制精度 |

## 跨维度诊断

navigation 与 video quality、consistency、physical 的相关性接近零。论文在 navigation split 上报告 navigation 与 video quality 的 Pearson 相关为 -0.12，与 consistency 为 -0.05，与 physical 为 -0.15。视频可以具有稳定纹理、连续运动和较少可见物理错误，却在连续转向后偏离目标轨迹；反过来，精确执行键盘控制的世界模型也可能生成较弱的开放域外观。

第三人称 case 增加了主体与相机的耦合约束。第一人称中，动作直接映射到相机的平移或朝向；第三人称还要使相机相对于移动主体保持合理位置。结果中的第一人称 navigation 难度较低，而体育/游戏场景和动物主体的 navigation 更困难，原因是快速运动、非刚性形变和相机跟随同时提高了几何控制复杂度。

空间一致性的 gated 分数说明静止输出可能造成误判。camera-conditioned 模型从普通 spatial consistency 到 gated spatial consistency 的平均下降为 15.3 分，text-conditioned 模型的下降为 4.5 分。普通回程比较只检查回到初始视角后是否相似；当视频几乎不移动时，这一条件容易满足。gated 版本要求中间帧出现足够变化，因而将实际运动和表面稳定性同时纳入结果。

按 turn 统计时，navigation 从第一轮到第四轮及之后下降约 33 分，明显快于 event editing 的约 13 分和 subject action 的约 9 分。连续导航需要维护可累积的空间坐标系，早期的方向或尺度误差会改变后续起点。perspective switching 的平均分约为 30.7，已经处于较低水平，跨轮变化较小并不表示该任务稳定完成。

## 自动指标与人工偏好

人工验证采用盲测 pairwise comparison。400 名众包标注者围绕十个评测方面，在模型对之间选择 A 胜、B 胜或平局；平局为双方各记 0.5，再由每个模型的胜率与自动分数计算 Spearman 排序相关。十个方面的相关系数均不低于 0.94，其中 event editing、subject action、perspective switching 和 spatial consistency 达到 1.00。

该结果支持自动指标在这组模型、样本和评价颗粒度下复现模型排序。它并不证明单个 case 的 VLM 判定必然正确，也不意味着所有真实用户偏好、机器人任务成功率或未覆盖场景都与 0–100 分线性一致。人工偏好验证与分项定义共同约束了分数能够支持的结论范围。

## 适用范围

WBench 的视频协议覆盖从初始图像出发的开放域多轮条件生成，能够定位画面、语义控制、空间记忆和可见物理的失效。它不包含环境奖励、策略更新、机器人本体状态闭环或真实执行结果，因而不能据此推断模型作为 RL environment 的稳定性、data engine 对策略的训练收益或 sim-to-real 成功率。

结果表还受到接口与子集的约束。text-conditioned 模型在完整 289 个 case 上评测，camera-conditioned 和 action-conditioned 模型在 158 个 navigation case 上评测。完整集的语义交互分数、navigation split 的轨迹分数和不同模型类别的 leaderboard 位置对应不同的输入契约；跨表比较时应保留这些条件，而不应将它们压缩为脱离任务范围的单一世界模型能力排序。

## 导航

- 返回上级：[WBench](../05-wbench.md)
- 上一节：[评测器数据流与模型接口](04-evaluator-dataflow-and-interfaces.md)
