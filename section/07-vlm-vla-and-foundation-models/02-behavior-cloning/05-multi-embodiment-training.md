# 多具身体训练（跨具身、分层与记忆）

多形态训练关注一个策略如何跨不同机器人身体、动作空间和任务接口工作。分层和记忆关注长时程任务：高层决定子目标，低层执行动作，记忆保存对象、场景、失败和历史上下文。

## 三个问题

| 问题 | 例子 |
|---|---|
| 多形态 | 单臂、双臂、移动底盘、灵巧手动作空间不同 |
| 分层 | “做咖啡”拆成找杯子、放胶囊、按按钮等子目标 |
| 记忆 | 记住物体位置、已完成步骤、失败尝试和用户偏好 |

## 工程接口

```yaml
hierarchical_policy_interface:
  high_level:
    input: language_goal_and_scene_memory
    output: subgoal_sequence
  low_level:
    input: current_observation_and_subgoal
    output: action_chunk
  memory:
    short_term: recent_observations_and_actions
    long_term: object_locations_task_history_failures
```

## 与前沿模型的关系

π0.7、MEM、WAM 等方向都在尝试让机器人从“单步反应”走向“可引导、可组合、能记忆、能规划”的策略。本页不要求初学者复现这些模型，而是要求能把论文概念翻译成系统接口和评测 case。
