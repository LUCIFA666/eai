# 三种评测设置

分层评测范式的落点是三种设置：Vanilla、Decoupled、Coupled。三者共用同一套低层策略，区别只在子任务从哪来。把子任务来源换掉、其余不变，长任务的失败就能归因到规划还是执行：Vanilla 没有规划器，Decoupled 把规划和执行拆开单独看，Coupled 是完整分层在线。

论文与仓库对这三种设置的命名不完全一致，对照如下：

| 论文 | 仓库 `eval_mode` | 子任务来源 |
|---|---|---|
| Vanilla | `vanilla` | 无规划器，直接喂整条原始指令 |
| Decoupled — 规则规划器（在线） | `half` | 真值子指令 `oracle_half`，按机器人状态切换 |
| Decoupled — VLM 规划器（离线） | 离线 VQA 评测 | VLM 逐帧预测子任务，只测准确率 |
| Coupled | `vlm` | VLM 在线预测子任务，实时喂给策略 |

四个测量点合起来是一把定位失败来源的尺子。Vanilla 给出无规划器时的下限；规则规划器（在线）用真值子指令，给出规划全对时低层策略能到的执行上界；VLM 规划器（离线）撇开策略，单独量规划本身的准确率；Coupled 给出完整系统的实测值。有了这四个点，长任务失败到底是因为根本没规划、低层执行不行、还是规划器不行，就能分开看：Coupled 远低于规则规划器说明瓶颈在规划端，规则规划器也不高则说明低层执行本身就没到位。

## Vanilla：非分层

去掉规划器，低层策略直接从原始指令在线执行整条任务，作为非分层基线。它衡量的是策略不靠外部拆解、独立完成整段长任务的能力。组合任务上 Vanilla 的成功率几乎恒为 0，正是这条基线让规划器的价值显出来。

## Decoupled：规划器与策略分开评

这一档把高层规划和低层执行拆开单独看，含两个变体。

规则规划器（在线）用真值子指令在线调度，切换边界由标注给出。沿用 DeCoBench 的做法，用夹爪与物体之间的物理交互变化来判定该不该推进到下一子任务：抓取物数量变化，或夹爪动作变化，就切到下一条子指令；若切换时夹爪张开，机械臂先归位（`return_home`）再继续。

```python
# baselines/RVT-Baseline/rvt/utils/rollout_generator.py:205-213
if (cur_grasped_objects_len != prev_grasped_objects_len or 
    abs(cur_gripper_action - prev_gripper_action) > 1e-6):
    instr_index = (instr_index + 1) % len(half_descriptions)
    need_new_subtask = True
    # reset when grasped changed and gripper open
    if abs(act_result.action[-2] - 1.000) < 1e-9:
        return_home = True
        env._i = -1
```

`eval_mode=half` 时，第 `instr_index` 条真值子指令被取出、tokenize 后注入为策略的 `lang_goal_tokens`。因为子指令是真值，这一档给低层策略提供了一个强上界：规划全对时，策略能做到多好。

VLM 规划器（离线）单独评规划器。VLM 在固定间隔逐帧预测当前子任务，按 VQA 方式度量预测准确率，反映它的场景理解与任务分解能力。它不驱动策略，只出一个准确率数字，因此和在线成功率不在同一坐标系。

## Coupled：完整分层在线

完整分层架构在线部署。VLM 规划器一检测到夹爪状态切换，就生成新的子任务描述，交由低层策略执行，考的是规划与执行端到端衔接的整体表现。

仓库里 VLM 规划器（Qwen2.5-VL-7B）按固定契约输出 `reasoning` 与 `sub_task` 两个字段，分别是推理过程和最终子任务；`sub_task` 被 tokenize 成 `lang_goal_tokens` 喂给策略：

```python
# baselines/RVT-Baseline/rvt/utils/rollout_generator.py:107-123（节选）
result = self.vlm_agent.run(
    task_name="next_sub_task",
    variables=variables,
    fields=("reasoning", "sub_task"),
)[0]
sub_task = result['sub_task'][0]
prepped_data["lang_goal_tokens"] = torch.tensor(
    np.array([tokenize([sub_task])[0].numpy()]), device=self._env_device
).unsqueeze(0)
```

只有在 `need_new_subtask` 为真（即刚发生状态切换）时才重新调用 VLM，其余步沿用上一次生成的子任务，避免每步都请求规划器。三档共用同一个评测入口，靠开关切换：

```bash
# baselines/RVT-Baseline/rvt/eval.sh
bash eval.sh --tasks_type <atomic|compositional> --eval_mode <vanilla|half|vlm> ...
```

规则规划器（`half`）与 VLM 规划器（`vlm`）的成功率之差，就是把真值规划换成学到的规划所损失的部分，这个差揭示的分层瓶颈是结果页的重点。

## 导航

- 返回上级：[RoboHiMan](../04-robohiman.md)
- 上一节：[多级数据与渐进缩放](04-dataset-and-scaling.md)
- 下一节：[指标与协议](06-metrics-and-protocol.md)
