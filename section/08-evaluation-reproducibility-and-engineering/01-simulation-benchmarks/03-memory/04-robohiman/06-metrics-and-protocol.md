# 指标与协议

## 成功率口径

在线评测报二值成功率：一个 episode 要么成功要么失败。成绩按四类任务分别取平均：原子（A）、带扰动原子（AP）、组合（C）、带扰动组合（CP）。结果表里的 `X→Y` 就是用 X 级数据训练、在 Y 类任务上取的平均成功率。四类分开报，是为了把原子执行能力和组合泛化能力分开看，不让高原子成功率掩盖低组合成功率。

成功由 RLBench 终态 reward 判定。`env.step` 只有在该任务 `success()` 的全部条件同时满足时才返回 `reward >= 1`，此时 `success=True` 并乘上 `reward_scale=100`，下游按 `reward > 99` 计成功（`utils/custom_rlbench_env_colosseum.py:324-337`、`eval.py:405-409`）。组合任务的终态复合判定就落在这里：条件里包含整条长任务的最终目标状态，中间做对几步而终态未达成时全部条件不成立，reward 停在 0，因此不给部分分。

两类情况直接判失败：运动规划抛出 `IKError` / `ConfigurationPathError` / `InvalidActionError` 时，`step` 置 `terminal=True, reward=0.0` 并计入 `_error_type_counts`（`custom_rlbench_env_colosseum.py:340-352`）；到 `--episode-length`（控制步数上限，默认 25）仍未成功，则最后一步强制 `terminal=True`，超时按失败计（`utils/rollout_generator.py:150-158`）。

## Episode 分配

原子任务共生成 720 个评测 episode，组合任务 900 个。每个任务的 episode 按扰动切分：

- 不加扰动（None）：15 个。
- 每个扰动因子：各 5 个（12 个因子）。
- 全部因子同时打开（All）：5 个。

单任务合计 $15 + 12 \times 5 + 5 = 80$ 个 episode，10 个原子任务给出 720、12 个组合任务给出 900，两个总数按任务数乘每任务 80 配出。

这套分配在仓库里由变体桶和每桶 episode 数两层决定，而非单个常量。`eval.sh` 按 `<task>_<i>`（`i` 从 0 到 17）枚举变体文件夹，目录不存在就 `[Skip]` 跳过（`eval.sh:82-90`）；每个任务实际启用哪些桶由其策略文件决定（如 `colosseum/assets/atomic_json/<task>.json`，典型每任务约 10 个启用桶，含 no_variations、各扰动因子与 all_mixed）。每桶跑多少 episode 由 `--num_episodes` 给定，None 桶 15、各因子与 All 桶各 5 就是这样配出 80 的，属于协议口径而非代码硬编码。

## 有效 episode

在线评测按离线 episode 的初始态复现：`reset_to_demo(ep)` 以 `from_episode_number=ep` 载入该 episode 的存档态（`custom_rlbench_env_colosseum.py:426-454`、`rollout_generator.py:65-66`），rollout 的 seed 也取这个 episode 索引。由于物体摆放或工作空间采样的差异，部分离线 episode 在线无法完全复现：载入、复位或摆放抛异常时，`eval.py:293-315` 直接 `continue` 跳过这一 episode。因此成功率只在能成功复现的有效 episode 上统计，有效比例约为总数的 90%，避免把环境本身没摆出来的场景算成策略失败。

## 离线规划器准确率

Decoupled 的 VLM 规划器走单独的离线口径，入口是 `src/high_level/eval.py`（独立于在线 `eval.sh`）：不驱动策略，只测子任务预测的准确率。按 `--frame_interval` 采帧，原子默认 10、组合 30，每个采样帧连同完整任务指令建成一个 VQA 实例，让规划器预测当前子任务。打分用 exact-match：预测与真值都 `strip().lower()` 后逐字比对，真值取 `oracle_half` 在该采样帧对应的子目标（`src/high_level/eval.py:211-218`）。`seed=2` 固定，产物 `evaluation_summary.json` 里的 `overall_success_rate` 就是整体准确率。

这个数字反映的是场景理解与任务分解能力，和在线成功率不在同一坐标系。离线尚可的准确率，一旦进入在线闭环、误差逐步累积，未必足以支撑整条长任务，两者的落差正是分层瓶颈的度量，对比时要分开看。

## 评测入口与参数

评测分两个入口。在线 rollout 走 `eval.sh` → `eval.py`：`--tasks_type`（`atomic` / `compositional`）选任务类别，`--eval_mode`（`vanilla` / `half` / `vlm`）选评测设置，`--num_episodes` 定每桶 episode 数，`--episode-length` 定控制步数上限（默认 25），`vlm` 档还需 `--high_level_cfg_path` 指向 L1–L4 规划器配置。离线 VQA 走 `src/high_level/eval.py`，由 `--frame_interval` 与 `--seed` 控制。

## 结果如何汇总

单次评测只产出一份 `<model_folder>/eval/<log_name>/eval_results.csv`，逐任务写一行 `task, success_rate`（`eval.py:243-250`、`eval.py:342-362`）。RoboHiMan 仓库只产出这份 per-task CSV，没有再算 A/AP/C/CP 四类平均或 `X→Y` 训练级 × 任务类矩阵的脚本；这一步需使用者自行在多次评测的 CSV 之上完成，靠 `log_name`（编码训练级与任务类，如 `Base_VLM_Atomic`）对齐后汇总。

## 导航

- 返回上级：[RoboHiMan](../04-robohiman.md)
- 上一节：[三种评测设置](05-evaluation-paradigms.md)
- 下一节：[基线与结果发现](07-baselines-and-results.md)
