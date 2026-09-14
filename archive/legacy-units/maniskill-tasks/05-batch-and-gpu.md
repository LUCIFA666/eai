# 批量接口、GPU 并行与 CPUGymWrapper

ManiSkill 和传统单环境 Gym 最大的差别之一，是默认使用批量接口。前面 `num_envs=1` 时观测是 `(1, 42)`，已经能看到这个设计。`num_envs` 做的事，是把这个 batch 从 1 放大到 N。

## 本节目标

本节围绕下面几个问题展开：

1. ManiSkill 为什么默认使用批量接口，`num_envs=1` 时观测形状为什么是 `(1, 42)` 而不是 `(42,)`。
2. `num_envs=16` 时观测、动作、奖励和 done 的形状如何变化，如何验证 GPU 并行确实跑通了。
3. `single_observation_space` 和 `env.observation_space` 分别该在什么时候用。
4. 多环境下 `terminated` 和 `truncated` 是布尔张量，代码上要注意什么。
5. `CPUGymWrapper` 能解决什么问题，什么时候用它，什么时候不该用。

## 为什么会有 batch 维

ManiSkill 默认使用批量接口，这是为了在 GPU 上并行跑多个环境。即使只创建一个环境（`num_envs=1`），也会把返回值组织成带 batch 维的张量。所以看到 `(1, 42)` 开头的 `1`，不是 bug，也不是多余维度，而是"这一个环境"在批量框架里的统一表达。

## `num_envs=16`：把一个任务同时跑 16 份

单独运行下面命令：

```bash
python labs/04-simulation/maniskill_pickcube_artifacts.py --only-vector --num-envs 16
```

一次通过 GPU vector probe 时，输出可能类似：

```text
observation_space: Box(-inf, inf, (16, 42), float32)
action_space: Box(-1.0, 1.0, (16, 7), float32)

{
  "num_envs": 16,
  "obs_shape": [
    16,
    42
  ],
  "reward_shape": [
    16
  ],
  "done_shape": [
    16
  ],
  "reward_device": "cuda:0",
  "reward_sample": [
    0.06182389333844185,
    0.04422205686569214,
    0.03813909366726875,
    0.0705518051981926,
    0.06454193592071533,
    0.05948738008737564,
    0.0577382817864418,
    0.076698437333107
  ]
}
```

这段输出说明三件事：

**第一**，观测和动作空间的第一维都变成了 16。策略如果直接接环境返回值，就要按 batch 张量处理，而不能写成传统单环境的标量逻辑。

**第二**，`reward_shape` 和 `done_shape` 都是 `[16]`，说明每个环境都有自己的奖励和结束状态。多环境下不能写：

```python
if terminated:
    ...
```

因为 `terminated` 是一组布尔值。应该逐元素处理，或者写：

```python
done = terminated | truncated
if done.any():
    ...
```

> ⚠️ **易错点**：多环境下 `terminated` 和 `truncated` 是布尔张量，不能直接放进 `if`。应使用 `done.any()`、`done.all()` 或按环境下标处理。

**第三**，如果 `reward_device` 显示为 `cuda:0`，说明这次并行环境的 reward 张量在 GPU 上。`reward_sample` 里的数值不同，也能帮助确认多个环境各自独立推进，而不是把同一个结果复制多份。

## single space：写网络时看哪个空间

批量环境的 `env.observation_space` 会带上 `num_envs` 维度。如果写策略网络，经常更关心单个环境的输入输出空间。ManiSkill 环境通常也提供 `single_observation_space` 和 `single_action_space`，用来表示未批量的空间。

直观理解：

| 空间 | 用途 |
|---|---|
| `env.observation_space` | 环境实际返回的批量观测形状 |
| `env.action_space` | 环境实际接收的批量动作形状 |
| `env.single_observation_space` | 单个环境的观测形状，常用于定义网络输入 |
| `env.single_action_space` | 单个环境的动作形状，常用于定义策略输出 |

所以看到 `(16, 42)` 时，不要把网络输入层写成"必须固定 16"。16 是并行环境数量，不是任务状态本身的维度。单个 `PickCube-v1` 的 state 维度仍然是 42。

> ⚠️ **易错点**：把 `(1, 42)` 当成状态多了一维。开头的 `1` 是 batch 维，真正的状态维度是 42。设计策略网络时，应参照 `single_observation_space` 而非 `env.observation_space`。

## CPUGymWrapper：回到传统 Gym 单环境接口

有些下游库只认传统 Gym 风格：单环境、NumPy 数组、Python 标量布尔值。此时可以给 `num_envs=1` 的环境套一层 `CPUGymWrapper`。

使用 `CPUGymWrapper` 后，输出可能类似：

```json
{
  "observation_space": "Box(-inf, inf, (42,), float32)",
  "action_space": "Box(-1.0, 1.0, (7,), float32)",
  "obs_type": "ndarray",
  "obs_shape": [
    42
  ],
  "reward": 0.05829094722867012,
  "reward_type": "float",
  "terminated_type": "bool",
  "truncated_type": "bool",
  "success": false,
  "success_type": "bool"
}
```

对比前面的 `(1, 42)`，这里已经变成 `(42,)`；reward 从张量变成 Python `float`；`terminated`、`truncated` 和 `success` 也变成普通 `bool`。这就是传统单环境代码最熟悉的形态。

代码大致如下：

```python
import gymnasium as gym
import mani_skill.envs
from mani_skill.utils.wrappers.gymnasium import CPUGymWrapper

env = gym.make(
    "PickCube-v1",
    num_envs=1,
    obs_mode="state",
    control_mode="pd_ee_delta_pose",
)
env = CPUGymWrapper(env)

obs, info = env.reset(seed=0)
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
env.close()
```

注意，`CPUGymWrapper` 适合单环境兼容，不是用来做大规模并行训练的。真要吃并行吞吐，应该保留批量张量接口。

> ⚠️ **易错点**：在同一个 Python 进程里先跑 CPU/渲染，再临时启用 GPU PhysX：可能触发初始化顺序错误（`GPU PhysX can only be enabled once`）。`num_envs=16` 建议单独进程验证。

## 小结

- ManiSkill 默认使用批量接口，`num_envs=1` 时也会有 batch 维。这不是 bug，是批量框架的统一表达。
- `num_envs=16` 会让观测、动作、奖励和 done 的第一维都变成 16。
- 多环境下 `terminated` 和 `truncated` 是布尔张量，不能直接放进 `if`，应使用 `.any()` / `.all()` 或逐元素处理。
- `reward_device` 可以作为检查张量所在设备的证据；各环境 reward 不同说明它们是独立推进的。
- 传统 Gym 单环境代码可以用 `CPUGymWrapper` 适配，但并行训练应保留批量接口。
- 设计网络时看 `single_observation_space` / `single_action_space`，不要被 `env.observation_space` 里的 `num_envs` 维度误导。

## 导航

- 上一节：[观测与渲染：state、rgbd 与运行截图](04-observation-and-rendering.md)
- 返回上级：[ManiSkill 任务环境](../01-maniskill-tasks.md)
- 下一节：[下游衔接、常见易错点与自查](06-downstream-and-faq.md)
