# 评测协议与指标

RoboMemArena 用分阶段的成功检查评测长时程任务：把每个任务拆成有序的验证阶段，逐帧检查阶段是否达成，再据此算两个指标。代码在 `evaluation_benchmark/scripts/`。

## 两个指标

两个指标都建立在阶段成功检查（各阶段的指示函数）之上：

- TSR（Task Success Rate）：一个 episode 只有全部阶段都完成才算成功，等价于所有阶段指示函数的乘积。它衡量端到端把整条长任务做对的能力。
- CSR（Completion Success Rate）：完成阶段数占总阶段数的比例，是更细粒度的过程完成度。

需要提醒的是，仓库不同位置的字段命名和论文并不统一：`scripts/` 里代码把全阶段成功记作 `tsr_success`、把按比例的过程完成度记作 `average_score_pct`；而评测参考实现的 README 又把过程完成度叫 `CSR`、把最终 BDDL 目标成功率叫 `TSR`。这里一律以论文的公式为准。每帧的阶段检查与最终打分核心如下：

```python
# eval_common.py：逐帧更新阶段完成状态
if stage_checks_sequential:
    for i, (name, check_fn) in enumerate(stage_checks):
        if stage_done[name]:
            continue
        prev_all_done = all(stage_done[n] for n, _ in stage_checks[:i])
        if prev_all_done and check_fn(env):
            stage_done[name] = True
...
num_done = sum(1 for name, _ in stage_checks if stage_done[name])
score = 100.0 * num_done / len(stage_checks)   # 过程完成度（论文 CSR）
```

```python
# run_eval：全阶段成功即 TSR 成功
tsr_success = bool(stage_done) and all(stage_done.values())
```

阶段默认按顺序判定（`stage_checks_sequential=True`）：第 i 个阶段只有在它之前的阶段都完成后才会被检查，符合长任务的先后依赖。

## 各任务的验证阶段

每个任务在 `eval_tasks2_26.py` 的 `_task_specs(task_id)` 里给出一组有序的 `StageSpec`（阶段名 + 检查函数），阶段数通常在三到九个之间，与任务的 `primitive_order` 对应。任务名 `4` 的九阶段就是把它的九步子任务逐一变成检查：

```python
# 任务 4：把 butter 放进非空（顶层）抽屉
StageSpec("01_Open_Top_Drawer",      _drawer_open_abs("wooden_cabinet_1_top_region", None, 0.10)),
StageSpec("02_Close_Top_Drawer",     _drawer_closed_abs(...)),
StageSpec("03_Open_Middle_Drawer",   _drawer_open_abs("wooden_cabinet_1_middle_region", None, 0.10)),
...
StageSpec("07_Open_Top_Drawer_Again",_drawer_open_abs("wooden_cabinet_1_top_region", None, 0.10)),
StageSpec("08_Put_Butter_Top_Drawer",_in_drawer_radius("butter_1", "wooden_cabinet_1_top_region", 0.25, 0.15)),
StageSpec("09_Close_Top_Drawer_Final", _drawer_closed_abs(...)),
```

各检查函数是几何判据：`_drawer_open_abs(region, _, 0.10)` 判抽屉相对初始位置拉开超过 0.10，`_in_drawer_radius(obj, region, 0.25, 0.15)` 判物体落在抽屉区域 0.25 的水平半径、0.15 的高度差内，`_in_container_body(obj, target, xy, z_low, z_high)` 判物体在目标容器的水平阈值与高度区间内，微波炉用 `_microwave_open` / `_microwave_closed` 判关节角。倒水任务用 `_pour_stage`：

```python
def _pour_stage(range_thresh, min_steps, hold_angle=None, hold_frames=None):
    def check(env, state, stage_start):
        tilts = _segment_tilts(state, stage_start)      # 本阶段以来的末端倾角序列
        if len(tilts) < min_steps:
            return False
        if float(tilts.max() - tilts.min()) <= range_thresh:
            return False
        if hold_angle is not None and hold_frames is not None:
            return int(np.sum(tilts > hold_angle)) > hold_frames
        return True
    return check
```

一次倒水被判定为：本阶段内末端倾角的幅度（最大减最小）超过阈值、且持续至少若干帧。多数倒水阶段用 `_pour_stage(0.30, 10)`（幅度 0.30、至少 10 帧），酒瓶因为要倒得更彻底用 `_pour_stage(0.78, 20, hold_angle=1.05, hold_frames=10)`（幅度 0.78、至少 20 帧，且倾角大于 1.05 的帧要多于 10 帧）。因此"倒两次"就是两个连续的 pour 阶段各被独立判定一次。

## 运行评测

官方的一键评测脚本是 `run_all_tasks1_26.py`，它扫过 1 到 26 号任务、每个任务固定若干 seed 跑若干 episode，记录每个 episode 而不重试 seed、不按分数过滤：

```bash
cd evaluation_benchmark
python scripts/run_all_tasks1_26.py \
  --adapter-spec /abs/path/to/your_adapter.py:build_adapter \
  --adapter-kwargs '{"checkpoint_dir": "/abs/path/to/your_checkpoint"}' \
  --num-trials-per-task 50 \
  --seed 100 \
  --out-root outputs/your_model_eval_1_26
```

关键默认值：`--num-trials-per-task 50`、`--seed 100`、`--max-steps 3000`、`--replan-steps 10`、`--num-steps-wait 10`、`--resize-size 256`。每个 episode 的种子按 `current_seed = seed + ep` 递增，保证不同模型在同一组种子上可比。计数类倒水任务默认开启严格的多余倒水拒绝：第二次倒完后启动一个 30 步（`--extra-pour-monitor-steps`）的后监测窗，窗内检测到第三次倒水就判该 episode 失败，用 `--no-fail-on-extra-pour` 可关掉这项检查。

跑完后 `run_all_tasks1_26.py` 写出四份产物：`episodes.tsv`（每 episode 一行）、`task_summary.tsv`（每任务一行）、`summary.json`、`aggregate.json`。`episodes.tsv` 的列包括 `task_id, ep, seed, score_pct, tsr_success, stage_success, goal, extra_pour_detected, pour_1_step, pour_2_step, ...`；`task_summary.tsv` 汇总每任务的 `average_score_pct, tsr_success_rate_pct, stage_success_rate_pct` 等。

## 评测主循环与适配器契约

benchmark 侧负责整个评测循环，被测模型只需实现一个适配器。主循环先用若干步空动作等环境稳定，然后每当动作队列空了就调用一次适配器、取回动作块的前 `replan_steps` 步执行：

```python
# eval_common.py：run_episode_with_stages 的核心步进
if t < num_steps_wait:
    obs, _, done, _ = env.step(LIBERO_DUMMY_ACTION)
    t += 1
    continue
...
if not action_plan:
    actions = ensure_action_chunk(adapter.infer_actions(obs=adapter_obs, prompt=prompt, resize_size=resize_size))
    action_plan.extend(actions[:replan_steps])
action = action_plan.popleft()
obs, _, done, _ = env.step(action.tolist())
```

适配器的契约很薄，只需继承 `BasePolicyAdapter` 并实现两个方法：

```python
class BasePolicyAdapter(ABC):
    def reset(self) -> None:
        """Reset any per-episode internal state if needed."""

    @abstractmethod
    def infer_actions(self, obs: dict, prompt: str, resize_size: int) -> np.ndarray:
        """Return an action chunk with shape [horizon, action_dim]."""
```

`infer_actions` 返回的动作块必须是二维 `[horizon, action_dim]`（`ensure_action_chunk` 会校验形状），`reset` 在每个 episode 开始时清空模型的每集内部状态。这层与模型无关的接口让单策略、VLM 规划器加 VLA、或远程策略服务都能用同一套评测。适配器由 `--adapter-spec module_or_path.py:build_adapter` 指定的工厂函数构造。

## 导航

- 返回上级：[RoboMemArena](../03-robomemarena.md)
- 上一节：[任务定义与观测/数据格式](05-task-definition-and-io.md)
- 下一节：[PrediMem 方法](07-predimem.md)
