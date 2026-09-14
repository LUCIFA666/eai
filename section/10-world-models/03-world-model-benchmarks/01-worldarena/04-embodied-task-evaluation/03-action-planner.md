# Action Planner

Action Planner 把世界模型作为动作表征来源：模型根据首帧和指令预测未来结构，VPP 风格的逆动力学模型从中间特征解码可执行动作，再由 RoboTwin 仿真器判断任务是否成功。

## 从预测表征到动作

Data Engine 使用生成数据训练另一个策略，Action Planner 则直接从当前世界模型特征产生动作。其链路为

```text
first frame + instruction
        ↓
world model future representation
        ↓
IDM / VPP diffusion action head + robot state
        ↓
action sequence
        ↓
RoboTwin closed-loop execution
```

扩散动作头从噪声动作开始迭代去噪，并由视频特征、机器人状态与指令共同提供条件。最终成功率同时取决于世界模型是否保留未来状态结构、IDM 是否正确恢复动作，以及执行时状态反馈是否稳定。

## 与 Policy Evaluator 的区别

| 对象 | 动作来源 | 世界模型的角色 | 最终判断 |
| --- | --- | --- | --- |
| Policy Evaluator | 固定 π0.5 策略 | 环境代理，响应策略动作 | 能否复现策略排序 |
| Action Planner | 世界模型特征与动作头 | 预测与规划表征 | 自身动作能否完成任务 |

Policy Evaluator 中的世界模型不决定策略意图；Action Planner 中的动作本身来自世界模型表征。后者失败可能来自视觉表征、IDM 训练、动作归一化、坐标语义或闭环控制，无法用视频分数单独定位。

## 论文实验

论文 v2 在 `adjust_bottle` 和 `click_bell` 上比较六种基于世界模型的规划器，每项执行 100 次。π0.5 在两个任务上的成功率为 77% 和 66%；六种规划器的最高结果分别为 WoW 的 20% 和 TesserAct 的 35%。所有基于世界模型的规划器都明显低于 π0.5。

以 `click_bell` 为例，视频预测可以清楚展示机械臂接近按钮，但动作头若把视觉上的接近关系解码为过短位移，最终仍无法触发铃铛。反过来，较模糊的预测若保留正确接触时刻和方向，也可能产生有效动作。

## 具体失败边界

- 中间特征适合视频重建，不表示其中线性可读出精确控制量。
- 开环预测看似完成任务时，解码动作在仿真器中仍会遇到状态偏差和接触扰动。
- 动作头与世界模型联合决定结果；更换 IDM checkpoint 后的成功率不能继续视为同一规划器。
- 两个短任务上的成功率不支持长时规划、错误恢复或跨任务泛化结论。

Action Planner 的低结果说明当前预测表征尚不足以稳定支持闭环执行，但不能据此判断每个失败都来自世界模型。完整诊断还需要动作误差、执行轨迹和中间状态。

## 导航

- 返回上级：[具身任务评测](../04-embodied-task-evaluation.md)
- 上一节：[Policy Evaluator](02-policy-evaluator.md)
- 下一节：[功能结果与感知—功能差距](04-functional-results.md)
