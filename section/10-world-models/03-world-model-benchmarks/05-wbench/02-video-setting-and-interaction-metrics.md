# 视频、设定与交互指标

WBench 的前 12 项指标分别检查视频本身、生成世界是否符合起始设定、以及多轮控制是否产生要求的变化。三组指标使用不同参照：video quality 多从视频内部提取视觉信号，setting adherence 对照 setting 中的语义条件，interaction adherence 对照每轮 action 与相应的视频片段。分项统一线性缩放到 0–100，分数越高表示在该指标定义下更好。

## Video quality

video quality 不读取动作是否正确，而是测量生成视频的可观看性和运动表现。前五项来自 VBench，`HPSv3 Quality` 是归一化的人类偏好奖励。

| 指标 | 信号或参照 | 判定对象 | 主要失败类型 |
| --- | --- | --- | --- |
| Aesthetic Quality | 美学质量模型 | 构图、风格与总体视觉观感 | 不协调构图、低美感渲染 |
| Imaging Quality | 无参考图像质量 | 清晰度、噪声和成像质量 | 模糊、噪声、压缩伪影 |
| Temporal Flickering | 相邻帧视觉稳定性 | 画面是否无意义闪烁 | 纹理跳变、亮度闪烁 |
| Dynamic Degree | 帧间运动 | 视频是否具有足够动态变化 | 几乎静止的输出 |
| Motion Smoothness | 光流与时间连续性 | 运动是否连续 | 抖动、跳帧、突变 |
| HPSv3 Quality | HPSv3 偏好奖励 | 人类偏好的总体视觉质量 | 与偏好数据不一致的观感 |

高 video quality 不证明模型服从控制。例如，镜头几乎不移动的视频可能具有较少的 flicker 和很高的 smoothness，却未执行前进或转向。`Dynamic Degree` 与其他质量指标并列，正是为了把静态输出和稳定运动区分开。

## Setting adherence

setting adherence 检查模型是否从正确的世界开始，并在后续视频中保留该世界。`Scene Adherence` 将环境提示拆为初始帧已可见的部分和应在后续出现的 offscreen 部分。VLM 同时判断前者是否持续一致、后者是否在合适的相机运动后出现。该设计避免模型只复制第一帧即可取得高分。

`Subject Adherence` 将主体提示拆成 appearance 与 motion。appearance 包括衣物、毛色或形状等可见属性，motion 描述步态、敏捷性等运动先验。两项分数回答的对象不同：scene 分数可以较高而主体身份已经漂移，主体分数也不能证明环境布局被正确保留。

| 指标 | 条件参照 | 判定对象 | 主要失败类型 |
| --- | --- | --- | --- |
| Scene Adherence | scene、style 与初始帧 | 可见环境保持，offscreen 元素出现 | 背景替换、遗漏指定地点、风格偏移 |
| Subject Adherence | perspective、subject | 外观和运动方式 | 身份漂移、错误体态、错误运动方式 |

## Interaction adherence

interaction adherence 按动作类型选择评测方法。navigation 是几何问题，评测器从生成视频估计相机位姿；其他三类是语义事件，评测器检查每一轮视频是否满足当前 case 的结构化条件。

| 指标 | 信号或参照 | 分数构成 | 主要失败类型 |
| --- | --- | --- | --- |
| Navigation Score | MegaSaM 位姿与从动作合成的目标轨迹 | Accuracy 由归一化轨迹误差得到；Consistency 比较重复或对称动作组的轨迹形状；模型级分数取两项聚合均值 | 方向错误、位移尺度偏移、转向后失去定位 |
| Event Edit Adherence | 当前轮事件规范与视频 | 变化检测、事件发生、完成度、细节准确性、无异常五项二值检查的平均 | 天气/物体未变、变化不完整、无因出现的对象 |
| Subject Action Adherence | 当前轮动作规范与视频 | 与 event edit 相同的五项逐轮检查 | 动作未发生、动作对象错误、动作过程异常 |
| Perspective Switch Adherence | 切换前后帧与目标视角类型 | 过渡可见、目标类型一致、目标视角结构合规三项全部成立才计为成功 | 视点未切换、主体错位、切换后构图不成立 |

Navigation Score 由 Accuracy 和 Consistency 等权组成。Accuracy 将预测轨迹与由 action 和 perspective 构造的目标轨迹对齐，按每轮弧长重采样后计算归一化平移与旋转误差，从而减弱不同模型绝对移动尺度的影响。Consistency 只比较属于同一对称组的 turn：相同 action 直接比较，`W/S`、`A/D`、`left/right`、`up/down` 及对应复合 action 在必要的坐标轴镜像后比较。某个 case 没有可比较动作对时，Consistency 与该 case 的 Navigation Score 记为 `null`；模型级报告分别聚合所有有效 Accuracy 和有动作对的 Consistency，再将两项均值等权合成，因此两个分量的样本数可能不同。第一人称转向对应 heading 变化，第三人称转向对应围绕主体的相机运动，因此目标轨迹由 perspective 决定。

event editing、subject action 和 perspective switching 只在 text-conditioned 模型的完整评测中出现。camera-conditioned 和 action-conditioned 模型的公开接口只接收 navigation 计划，无法表达语义事件编辑或主体行为指令；将其缺失项填为零会把接口范围误写为模型失败，因而 WBench 将它们限制在 158 个 navigation case 上比较。

## 导航

- 返回上级：[WBench](../05-wbench.md)
- 上一节：[数据与多轮交互协议](01-data-and-multiturn-protocol.md)
- 下一节：[一致性与物理指标](03-consistency-and-physical-metrics.md)
