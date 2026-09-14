# 语言条件任务执行与技能编排

本节介绍语言条件任务执行与技能编排：把用户指令、VLM/LLM 解析结果和机器人技能接口连接起来，形成可执行、可观测、可纠错的任务链路。

本节不恢复传统 TAMP 大章，也不把它写成抽象符号规划综述。这里关注的是动手学具身中更常见的工程问题：

```text
自然语言 / 多模态指令
  -> 任务解析
  -> 技能选择
  -> 参数绑定
  -> 执行监控
  -> 失败反馈
  -> 重新规划或降级
```

## 章节结构

| 页面 | 要写的内容 | 边界 |
|---|---|---|
| [指令到技能序列](05-language-conditioned-task-execution/01-instruction-to-skill-sequence.md) | 从自然语言或视觉语言目标解析出子任务、技能、对象、地点、约束和终止条件 | 不讲通用 prompt 工程大全 |
| [技能接口与参数绑定](05-language-conditioned-task-execution/02-skill-interface-and-parameter-binding.md) | pick、place、navigate、open、push、inspect 等技能的输入输出 schema，以及对象 id、pose、grasp、waypoint 的绑定方式 | 不重复第 2 章动作接口和第 7 章 VLA 训练 |
| [反馈纠错与重新规划](05-language-conditioned-task-execution/03-feedback-and-replanning.md) | 执行状态、感知置信度、失败码、重观察、重试、换技能、换目标和人工接管 | 不写成传统 TAMP 搜索算法 |
| [长程任务状态维护](05-language-conditioned-task-execution/04-long-horizon-task-state.md) | 任务阶段、已访问地点、已操作对象、失败历史、地图语义、记忆和日志如何进入下一步决策 | 不和世界模型章节混淆 |
| [代表工作导读](05-language-conditioned-task-execution/05-representative-works.md) | SayCan、Code as Policies、VoxPoser 三个"语言到技能"经典系统，作为上面方法论的落地锚点 | 只做导读，不复现完整系统 |
