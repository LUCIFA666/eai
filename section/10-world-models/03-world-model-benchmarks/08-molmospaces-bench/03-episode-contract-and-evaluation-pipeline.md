# Episode 契约与评测流水线

MolmoSpaces-Bench 以 `benchmark.json` 或按房屋拆分的兼容目录保存固定 episode。加载器将每条记录解析为 `EpisodeSpec`，其中包含重建起始世界的完整条件。`JsonBenchmarkEvalConfig` 保留机器人和策略的基础配置，episode 中的场景、相机、机器人位姿和任务字段在 rollout 时覆盖其中的占位值。

## `EpisodeSpec` 的固定部分

缩略 JSON 保留了评测器消费的关键字段。完整记录还会包含相机外参、物体增删、任务相关物体、来源 h5 轨迹键和更完整的 task 参数；这些字段共同决定策略看见什么、环境从何处开始以及 success predicate 检查什么。

```json
{
  "source": {"h5_file": "...", "traj_key": "traj_2"},
  "house_index": 2115,
  "scene_dataset": "procthor-objaverse",
  "data_split": "val",
  "robot": {
    "robot_name": "franka_droid",
    "init_qpos": {"arm": [-0.024, -0.737, "..."], "gripper": [0.003, 0.003]}
  },
  "cameras": [{"name": "wrist_camera", "type": "robot_mounted"}],
  "scene_modifications": {"object_poses": {}},
  "task": {"task_cls": "...", "task_horizon_sec": 100},
  "language": {"task_description": "pick up the target object"}
}
```

`scene_dataset`、`house_index` 和物体位姿将模拟器恢复到指定环境；`init_qpos` 与相机定义避免策略因随机起点面对不同视角；`language.task_description` 提供当前目标。评测器可以对同一策略配置逐条替换这些字段。`benchmark_dir` 决定加载哪组 `EpisodeSpec`，其影响覆盖全部 episode 字段，任务文本只是其中一项。

`scene_modifications.object_poses` 中的 body name 只有在已加载场景中能够解析时才会恢复对应位姿。无法解析的条目会产生包含 `house_index`、`scene_dataset` 和 `data_split` 的 warning，并被跳过；episode 的其余恢复过程和 rollout 仍会继续。该 warning 表明起始状态没有完全按照 JSON 恢复。

## 策略与评测配置的接口

自定义策略以 `InferencePolicy` 为基类。`get_action(observation)` 将环境观测依次变为模型输入、模型输出和环境动作；子类定义这些转换和 reset 行为。`JsonBenchmarkEvalConfig` 则提供控制周期、worker、输出和 policy 配置，episode 特定字段由 JSON 提供。

```python
class InferencePolicy(BasePolicy):
    def get_action(self, observation):
        model_input = self.obs_to_model_input(observation)
        model_output = self.inference_model(model_input)
        return self.model_output_to_action(model_output)

class MyEvalConfig(JsonBenchmarkEvalConfig):
    robot_config = FrankaRobotConfig()
    policy_config = MyPolicyConfig(checkpoint_path="/path/to/checkpoint")
    policy_dt_ms = 200.0
```

`get_action_chunk(observation)` 为同一策略接口提供可选的 action chunk。返回非空 chunk 时，评测器在请求下一次观测前按顺序开环执行其中的 action；没有可用 chunk 时，rollout 回退到 `get_action(observation)` 的单动作路径。到达 terminal 或 horizon 时，chunk 会提前结束；启用 oracle termination 后，某个中间 action 满足 success predicate 也会结束剩余 chunk。

`policy_dt_ms` 定义每个环境 action 的控制周期，并决定同一段 `task_horizon_sec` 转换为多少 policy steps。每个 action 都会推进环境并计入 horizon；action chunk 的长度改变观测与模型调用频率，不改变 horizon 的 action 计数单位。控制周期、动作表示和 chunk 长度都属于策略比较的实验条件。

## 从 JSON 到成功率

`run_evaluation()` 读取 benchmark，解析 horizon，构造 eval-mode 配置，再由 `JsonEvalRunner` 按房屋调度并行 rollout。worker 对每个 `EpisodeSpec` 重建任务，从 policy 取得单个 action 或 action chunk，并按 `policy_dt_ms` 逐 action 推进环境；chunk 完成或提前终止后，评测器才请求下一次观测。worker 同时写出 trajectory 与逐 episode 产物。收集阶段形成 `EvaluationResults`，其中包含成功数、总数、`success_rate`、输出目录和逐 episode 结果。

```python
results = run_evaluation(
    eval_config_cls="my_repo.configs:MyEvalConfig",
    benchmark_dir=Path("/path/to/benchmark"),
    checkpoint_path="/path/to/checkpoint",
    task_horizon_steps=500,
    num_workers=4,
)
print(results.success_rate, results.episode_results)
```

`run_evaluation()` 接受 `task_horizon_steps` 或 `task_horizon_sec` 作为显式 horizon；未提供时，runner 使用 episode 中的 `task_horizon_sec` 并按 `policy_dt_ms` 换算。两种显式 horizon 不能同时指定，缺少可解析的 horizon 时评测会终止而非静默猜测默认值。完整复现还依赖具体 benchmark、checkpoint、环境和资源版本。

标准评测模式固定以下条件：默认 `seed=42`，关闭机器人 action noise，保存所有 rollout 而非只保存成功轨迹，并在导入阶段核对资源版本。资源固定版本与预期版本不一致会直接报错，以避免用不同场景资产得到表面上同名的 benchmark 成绩。相机名称、光照、单 episode 或自定义物体等运行时覆盖存在于接口中，但它们改变了原始 episode 的评测条件，不能和默认 benchmark 成绩放在同一列比较。

## 导航

- 返回上级：[MolmoSpaces-Bench](../08-molmospaces-bench.md)
- 上一节：[任务、成功条件与机器人 embodiment](02-tasks-success-conditions-and-embodiments.md)
- 下一节：[策略比较与受控变化](04-policy-comparison-and-controlled-variation.md)
