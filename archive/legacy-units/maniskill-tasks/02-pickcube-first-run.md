# 跑通 PickCube-v1：从创建环境到随机动作

前面我们把 ManiSkill 在 SAPIEN 生态中的位置理清了，这一节动手把它跑起来。目标不是训练一个会抓方块的策略，而是验证环境创建、仿真推进、渲染链路都能正常工作。

## 本节目标

本节围绕下面几个问题展开：

1. `PickCube-v1` 这个任务长什么样，场景里有哪些东西。
2. 最小闭环代码怎么写，每一行在做什么。
3. 如何运行配套脚本生成本节的证据文件。
4. `reset()` 和 `step()` 返回的观测空间和动作空间长什么样。
5. 随机动作下 `success` 为 `False` 是否说明环境有问题。

## PickCube-v1 这个任务长什么样

`PickCube-v1` 的画面很简单：Panda 机械臂在桌面旁边，桌上有一个红色小方块，目标位置用绿色标记表示。任务目标是把方块放到目标位置附近，并让机器人停稳。

![PickCube-v1 reset 后的任务画面](../../assets/maniskill_pickcube_reset.png)

运行时还保存了一段随机动作视频：

<video src="../../assets/maniskill_pickcube_rollout.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

这里的视频不是一个会成功的策略。脚本只是从动作空间里随机采样动作，用来证明环境、控制接口、物理推进和渲染链路都能跑通。随机动作下 `success` 为 `False` 很正常，不代表环境有问题。

## 最小闭环代码

把脚本压缩到最小，核心就是下面这几行：

```python
import gymnasium as gym
import mani_skill.envs  # 注册 ManiSkill 任务

env = gym.make(
    "PickCube-v1",
    num_envs=1,
    obs_mode="state",
    control_mode="pd_ee_delta_pose",
    render_mode="rgb_array",
)

obs, info = env.reset(seed=0)

for _ in range(50):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)

env.close()
```

各行的作用：

| 代码行 | 做什么 |
|---|---|
| `import mani_skill.envs` | 把 ManiSkill 内置任务注册到 Gymnasium |
| `gym.make("PickCube-v1", ...)` | 创建任务环境，指定观测和控制模式 |
| `env.reset(seed=0)` | 初始化 episode，得到初始观测和 info |
| `env.action_space.sample()` | 从动作空间随机采样，用于冒烟测试 |
| `env.step(action)` | 执行动作，推进仿真，返回新观测和奖励 |
| `env.close()` | 释放资源 |

运行后的基本空间如下：

```text
observation_space: Box(-inf, inf, (1, 42), float32)
action_space: Box(-1.0, 1.0, (7,), float32)
```

`(1, 42)` 里的 `1` 不是多余维度，也不是 bug。ManiSkill 默认使用批量接口，即使只创建一个环境，也会把返回值组织成带 batch 维的张量。[批量接口与 GPU 并行](05-batch-and-gpu.md) 会专门解释这个问题。

## 动手跑：生成本节证据

对应脚本是：

```text
labs/04-simulation/maniskill_pickcube_artifacts.py
```

从仓库根目录运行：

```bash
python labs/04-simulation/maniskill_pickcube_artifacts.py --steps 50 --num-envs 16
```

如果当前机器没有 CUDA，先跑单环境与视觉部分：

```bash
python labs/04-simulation/maniskill_pickcube_artifacts.py --steps 50 --skip-gpu
```

如果只想单独验证 `num_envs=16`，建议在一个新的 Python 进程里运行：

```bash
python labs/04-simulation/maniskill_pickcube_artifacts.py --only-vector --num-envs 16
```

这里单独起进程是有原因的：GPU PhysX 不适合在同一个 Python 进程里先被 CPU/渲染相关代码初始化，再临时启用。把并行验证拆成独立进程，可以避免"GPU PhysX can only be enabled once"一类初始化顺序问题。

脚本结构如下：

| 函数 | 做什么 | 主要产物 |
|---|---|---|
| `probe_state_smoke` | 创建 `PickCube-v1`，跑 `reset/step`，保存 reset 图和 rollout 视频 | `spaces.txt`、`reset.png`、`rollout.mp4` |
| `probe_control_modes` | 对比不同控制模式的动作空间 | `summary.json` |
| `probe_rgbd` | 用 `obs_mode="rgbd"` 取 RGB 和 depth | `rgb.png`、`depth.png` |
| `probe_cpu_wrapper` | 演示 `CPUGymWrapper` 如何去掉批量维 | `wrapper.txt` |
| `probe_vector` | 在独立进程里跑 `num_envs=16` | `vector.txt`、`vector.json` |

这比只在正文里贴几行代码更稳：每个结论都有对应的运行文件，后续如果版本升级导致输出变化，也容易重新跑一遍核对。

## 理解首次运行的输出

`summary.json` 里记录的本次冒烟结果如下：

```json
{
  "task": "PickCube-v1",
  "obs_mode": "state",
  "control_mode": "pd_ee_delta_pose",
  "sapien_version": "3.0.3",
  "observation_space": "Box(-inf, inf, (1, 42), float32)",
  "action_space": "Box(-1.0, 1.0, (7,), float32)",
  "reset_info_keys": [
    "elapsed_steps",
    "is_grasped",
    "is_obj_placed",
    "is_robot_static",
    "reconfigure",
    "success"
  ],
  "obs_after_reset": {
    "shape": [1, 42],
    "dtype": "float32"
  },
  "n_steps": 50,
  "mean_reward_random": 0.04417183067649603,
  "max_reward_random": 0.08638028800487518,
  "last_success": [false]
}
```

这里最值得看的不是 reward 数值本身，而是返回结构：观测带 batch 维，reward 是一段随机动作得到的训练信号，`success` 明确出现在 `info` 里。随机动作最后没有成功，这符合预期——随机策略当然抓不起方块。

## 小结

- `PickCube-v1` 是一个简单的桌面抓取任务，场景包含 Panda 机械臂、桌面、红色方块和目标标记。
- 最小闭环只有 ~10 行：创建环境 → reset → 循环 step → close。
- `import mani_skill.envs` 必须写，否则 `gym.make("PickCube-v1")` 找不到环境。
- ManiSkill 默认批量接口，`num_envs=1` 时观测形状也是 `(1, 42)` 而不是 `(42,)`。
- 随机动作下 `success` 为 `False` 是正常的——这说明环境没有"放水"，任务需要真正的策略才能完成。
- 配套脚本把每个结论都落地成可复现的运行文件，版本升级后可以重新跑一遍核对。

## 动手练习

1. 在本地运行 `python labs/04-simulation/maniskill_pickcube_artifacts.py --steps 50 --skip-gpu`，确认能输出 `spaces.txt` 和 `summary.json`。
2. 把 `--steps` 从 50 改成 200，观察 `mean_reward_random` 和 `last_success` 有什么变化。
3. 打开 `runs/04-simulation/` 下的产物文件，对照正文中的输出，看自己机器的结果是否一致。

## 导航

- 上一节：[认识 ManiSkill：SAPIEN 之上的任务层](01-maniskill-and-sapien.md)
- 返回上级：[ManiSkill 任务环境](../01-maniskill-tasks.md)
- 下一节：[任务的五把钥匙：env_id、观测、控制、奖励与成功](03-task-interfaces.md)
