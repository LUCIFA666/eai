# 8.5.2 World Action Model

World Action Model 可以理解为把“世界如何变化”和“动作如何生成”放进同一个学习问题。它不是普通视频预测，也不是普通 BC：机器人策略需要预测动作对未来状态、视觉和任务进展的影响，再据此选择动作。

## 和普通策略的区别

| 方法 | 学什么 |
|---|---|
| BC | 当前观测到专家动作 |
| ACT/DP | 当前观测到未来动作片段或轨迹 |
| VLA | 视觉/语言条件到动作 |
| WAM | 动作、未来状态和任务进展的联合模型 |

## 课程关注点

- 未来状态预测是否服务于动作选择，而不只是生成视频。
- 模型如何表示不确定性和多种未来。
- 是否能用于长时程任务的分层规划。
- 评测是否包含真实 rollout，而不是只看预测图像。

## 具体案例

[DreamZero](02-world-action-models/01-dreamzero.md) 是一个 World Action Model 案例。它把预训练视频生成模型改造成同时预测未来画面和动作块的机器人策略，用来观察 WAM 和普通 VLA 在建模目标、实时执行和跨本体迁移上的差异。

[Fast-WAM](02-world-action-models/03-fast-wam.md) 是另一个 World Action Model 案例。它保留训练阶段的视频/世界建模监督，但在推理阶段跳过显式未来视频生成，重点讨论 WAM 的收益究竟来自 test-time imagination，还是来自训练阶段学到的世界表征。

## 本组页面

| 三级页面 | 重点 |
|---|---|
| [DreamZero 模型原理](02-world-action-models/01-dreamzero.md) | Imagine-then-Execute WAM：视频扩散模型联合生成未来帧与动作块 |
| [DreamZero 复现](02-world-action-models/02-dreamzero-reproduction.md) | 14B 模型权重下载、推理服务部署、LoRA/全量微调 |
| [Fast-WAM 模型原理](02-world-action-models/03-fast-wam.md) | 训用分离：训练时保留世界建模，推理时跳过视频生成 |
| [Fast-WAM 复现](02-world-action-models/04-fast-wam-reproduction.md) | 三种推理模式切换、延迟对比、Direct Action 快速验证 |

## 最小分析模板

```yaml
world_action_model_card:
  inputs:
    - current_observation
    - language_goal
    - candidate_action_or_plan
  outputs:
    - future_observation
    - action_sequence
    - success_or_progress_score
  risks:
    - visual_prediction_not_actionable
    - compounding_model_error
    - missing_contact_dynamics
```