# 8.5.1 π0.7

π0.7 是 Physical Intelligence 在 2026 年 4 月发布的 steerable generalist robotic foundation model。它应该放在前沿进阶里，而不是从章节里消失，也不应该混进常用库目录：这里讨论的是模型能力、训练方向和评测边界；OpenPI 页面讨论的是开源工程入口。

## 关键能力

根据 Physical Intelligence 的公开介绍，π0.7 强调：

- 在未见环境中跟随多样语言指令。
- 用视觉子目标和 steering prompt 引导行为。
- 在多阶段厨房、电器、衣物、盒子等任务上展示组合泛化。
- 在部分任务上接近或超过此前针对单任务 RL 优化的 specialist policy。
- 控制不同机器人形态，展示 out-of-the-box 的泛化能力。

## 课程里怎么学

| 学习点 | 应落到哪里 |
|---|---|
| steerable prompt | 任务语言、视觉子目标和策略控制接口 |
| compositional generalization | 第 8 章评测要设计未见组合 case |
| autonomous/RL data distillation | 第 9 章 RL 和第 7 章策略训练的交叉 |
| cross-embodiment | 动作空间、机器人形态、低层控制器适配 |
| memory/hierarchy | 长时程任务和第 11 章真机实战中的执行系统 |

## 不要过度外推

π0.7 是前沿模型，不等于课程项目可以直接复现同等能力。写课程内容时要区分：

- 官方演示/论文报告的能力。
- 开源代码可直接运行的能力。
- 课程能用小任务复现的概念。
- 仍需等待更多 benchmark 和开源接口验证的部分。

## 阅读卡片模板

```yaml
frontier_reading_card:
  model: pi0.7
  source: Physical Intelligence
  release_date: 2026-04-16
  claims:
    - steerable generalist policy
    - compositional generalization
    - out-of-the-box dexterous tasks
  course_relevance:
    - advanced_vla
    - hierarchy
    - memory
    - evaluation_case_design
  reproducibility_status: source-backed_reading_not_course_reproduction
```
