# 评测协议与指标

RoboMME 在 16 个任务上多任务训练、逐任务评测，实现见 `scripts/evaluation.py` 与 `src/robomme/env_record_wrapper/`。

## 主指标:成功率与 status

主指标是任务成功率。每步 `info["status"]` 由 `DemonstrationWrapper` 计算，取四个常规值之一：`success`（`info["success"]` 为真）、`fail`（终止但未成功）、`timeout`（截断）、`ongoing`（默认）；若某一步抛异常（如 IK 失败），最外层的 `FailAwareWrapper` 会返回 `status="error"` 并带错误信息。是否成功由分阶段验证决定：走完 `task_list` 全部阶段且未触发失败才算 `success`。

成功率按两级汇总：每任务 `avg_success = success_count / num_episodes`，整体 `total_success / (16 * num_episodes)`。评测脚本用严格口径 `status == "success"`。

## split 与 seed

数据分 train / val / test 三档，每任务分别 100 / 50 / 50 个 episode，难度按比例混合（train 约 easy 50 / medium 25 / hard 25，val 与 test 约 26 / 12 / 12）。每个 episode 的 seed 与 difficulty 是固定整数，记在 `src/robomme/env_metadata/{train,val,test}/` 的 per-task metadata 里，三档 seed 区间互不重叠、完全确定；`BenchmarkEnvBuilder.resolve_episode` 读出 seed 与 difficulty 传进 `gym.make`。评测在 test 档上跑，每任务 50 个 episode。策略自身的随机 seed 与环境 seed 分开，评测要求至少 3 次运行，模型 seed 用 7 / 42 / 0，环境 seed 固定在内部不受影响。

## 评测主循环

对每个任务，`BenchmarkEnvBuilder(env_id, dataset="test", action_space=..., max_steps=1300)` 逐 episode 用 `make_env_for_episode(episode)` 构建环境并 `reset()`，从 `info["task_goal"]` 取语言指令，然后循环 `env.step(action)`，遇到 `error` 记失败、遇到 `terminated` 或 `truncated` 记 `status=="success"`。策略一次前向输出一个动作块，用一个队列消费：

```python
# 动作块用 deque 逐步消费
action_plan = collections.deque()
if not action_plan:
    action_plan.extend(policy.infer(inputs)["actions"])  # 一次预测一块
action = action_plan.popleft()
```

MME-VLA 实验里 `max_steps` 设 1300，内部还有一个 `+2` 偏移，截断按不含演示的步数计。论文的结果对最后 3 个 checkpoint × 3 个随机 seed 共 9 次运行取平均，prior methods 取 3 次。

## 模型接口与成功判定

评测循环每步把当前的前视、腕部 RGB 和 `task_goal` 交给策略、拿回动作，每个 episode 在终止时按 `status` 记一次成败。`scripts/evaluation.py` 里对应的几行如下（用占位的 `DummyModel` 代替真实策略）：

```python
# scripts/evaluation.py
dummy_action = dummy_model.predict(current_front_rgb, current_wrist_rgb, task_goal)
obs, reward, terminated, truncated, info = env.step(dummy_action)
if info.get("status") == "error":            # 常见于 ee_pose 的 IK 失败
    total_success.append(False)
    break
if terminated or truncated:
    outcome = info.get("status", "unknown")
    total_success.append(outcome == "success")
    break
...
print(f"Success rate: {sum(total_success) / len(total_success)}")
```

也就是说，模型接口是 `predict(front_rgb, wrist_rgb, task_goal) -> action`，成功由每 episode 的 `status == "success"` 判定，整体成功率是所有 episode 的均值；脚本里 `MODEL_SEED` 在 7、42、0 之间切换，用来跑三次取平均，环境 seed 固定、不受模型 seed 影响。

## 导航

- 返回上级：[RoboMME](../02-robomme.md)
- 上一节：[观测与动作接口](05-observation-and-action.md)
- 下一节：[MME-VLA 记忆方法](07-mme-vla-methods.md)
