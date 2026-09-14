# 评测框架

WorldArena 将具身世界模型放在两类结果之间检验：生成视频的感知质量，以及视频或中间表征进入数据合成、策略评估、动作规划后的任务效用。WorldArena 2.0 保留这层关系，但把世界模型的输入、运行时间和验证平台同时扩展。评测不再只问一次预测是否合理，还记录多模态接触、策略优化中的连续状态转移，以及真实机器人上的任务完成。

<figure>
  <img src="assets/worldarena2.png" alt="WorldArena 2.0 的模态、功能和平台扩展" />
  <figcaption>三条扩展轴改变的是评测条件与最终证据：触觉预测补充接触观测，RL rollout 检验递归交互，三平台任务结果检验跨环境与真实执行。</figcaption>
</figure>

## 从 WorldArena 到 WorldArena 2.0

WorldArena 1.0 的 open-loop 部分在给定初始观测和语言或动作条件后生成未来视频，并以 6 个维度、16 项指标分析画质、运动、内容一致性、物理、几何和可控性。其 functional 部分把世界模型分别作为 data engine、policy evaluator 和 action planner 使用。各角色的下游对象不同，因而不能把视频分数直接当作任务成功率。

WorldArena 2.0 没有替换这些基本角色，而是在三个位置增加新条件。触觉将接触形变加入观测和预测；RL 环境让模型在策略更新期间重复产生下一观测与奖励；跨平台协议把相同类型的感知与功能结果放到两个模拟器和一个真机本体上比较。

| 评测轴 | WorldArena 基线 | WorldArena 2.0 扩展 | 结果回答的问题 |
| --- | --- | --- | --- |
| Modality | 视觉条件视频 | RGB、触觉形变图、状态和动作的联合预测 | 接触相关状态是否被预测并支持操作 |
| Functionality | data engine、policy evaluator、action planner | world model as RL environment | 递归生成的状态和奖励能否支持策略优化 |
| Platform | 以模拟器任务为主 | RoboTwin 2.0、LIBERO、AgileX ALOHA | 模拟器中的结果能否跨任务、本体和真实观测保持有效 |

## 评测对象、条件与单位

同一“世界模型”在三条协议中承担的输出并不相同。触觉页直接比较预测信号与真实信号；RL 页把预测帧封装成环境 observation，再以 reward 和 termination 驱动训练；跨平台页则把模型生成的轨迹或动作放入策略训练和闭环执行。最终数字对应的单位也随之变化。

| 协议 | 主要条件输入 | 世界模型或其扩展的输出 | 评测单位 | 最终指标 |
| --- | --- | --- | --- | --- |
| Visuotactile | 多视角 RGB、触觉 marker image、状态、动作 | 未来视觉与触觉 latent，动作 head 的预测 | clip / task | PSNR、SSIM、动作误差、task success rate |
| RL environment | 初始 observation、策略动作块、任务描述 | 下一 observation、reward、termination | rollout / policy | simulator task success rate |
| Cross-platform | 平台观测、任务条件和模型生成结果 | synthetic trajectory 或闭环动作 | task / platform | data engine 与 action planner success rate |
| Cross-platform perception | 平台条件视频 | 未来视频 | episode / model | 沿用 6 维、16 项感知指标 |

## 结果之间的关系

感知指标定位生成结果本身的视觉、运动与物理缺陷。触觉 PSNR 或 SSIM 反映预测图与对应真值之间的像素和结构相似度；它们不能单独说明动作在环境中是否成功。RL success rate 记录由某个世界模型训练出的策略在 RoboTwin 中完成任务的比例，其中同时包含 transition 偏差、reward 方向和优化过程的影响。data engine 与 action planner 的成功率还叠加了下游策略学习或动作解码的误差。

真实平台的成功率具有最强的部署语义，但只覆盖 AgileX 上的少量任务、传感器和控制接口。RoboTwin、LIBERO 和 AgileX 的共同指标可用于比较同一协议内的趋势；跨协议、跨平台的分数没有共同量纲。

## 导航

- 返回上级：[WorldArena 2.0](../02-worldarena-2.md)
- 下一节：[Visuotactile 评测](02-visuotactile-evaluation.md)
