# 下游衔接、常见易错点与自查

前面四节把 ManiSkill 任务环境的接口逐一拆解完了。这一节做两件事：先说清楚这些接口如何接到后面的数据、训练和评测章节，再把整个章节里最容易踩的坑集中梳理一遍。

## 本节目标

本节围绕下面几个问题展开：

1. `obs_mode` 的选择如何影响感知和策略网络的设计。
2. `control_mode` 的选择如何影响规划、遥操作和策略输出。
3. `info["success"]` 如何接到评测工程，日志里至少该记录哪些字段。
4. 整个章节有哪些常见易错点，如何避免。

## 观测接口接到感知和策略网络

`obs_mode` 决定了策略输入的结构：

| `obs_mode` | 输入结构 | 常见下游 |
|---|---|---|
| `state` | 扁平状态向量 | MLP、快速 RL 冒烟、控制接口验证 |
| `state_dict` | 分层状态字典 | 调试、按字段取状态 |
| `rgbd` | 状态、RGB-D、相机参数字典 | 视觉策略、视觉-状态融合 |
| `pointcloud` | 点云和相关状态 | 3D 感知、点云策略 |
| `sensor_data` | 更原始的传感器数据 | 自定义感知管线 |

如果前期用 `state` 训了一个 MLP，后面想切到 `rgbd`，不能只改一行环境配置。输入结构已经从向量变成字典，网络、数据记录和 batch collate 都要一起改。这个问题越早固定，返工越少。

## 控制接口接到规划、控制和学习算法

`control_mode` 决定策略输出是什么。规划算法、遥操作数据和学习策略必须使用同一种控制接口，才能比较或复用。

举例说，`pd_ee_delta_pose` 下的 7 维动作是末端位姿增量加夹爪；`pd_joint_delta_pos` 下的 8 维动作是关节增量加夹爪。它们看起来都能让机器人动，但不是同一类动作。拿一个接口采的数据，不能直接喂给另一个接口的策略。

## success 接到评测工程

`success` 的作用是把"任务是否完成"从 reward 里独立出来。写训练代码时可以关心 reward；写评测代码时应优先记录 success。

本节不展开统计协议，但要先养成一个习惯：日志里至少记录这些字段：

```text
env_id
obs_mode
control_mode
reward_mode
seed
episode_length
success
is_grasped
is_obj_placed
is_robot_static
```

这样以后分析失败原因时，不会只剩一句"没成功"。

## 常见易错点

下面按主题把本章最容易踩的坑逐一列出。

### 环境创建

- **漏写 `import mani_skill.envs`**：只 `import gymnasium` 就 `gym.make("PickCube-v1")`，可能找不到环境。任务注册需要这一行。

### 批量接口与形状

- **把 `(1, 42)` 当成状态多了一维**：开头的 `1` 是 batch 维。ManiSkill 默认批量接口，`num_envs=1` 也带这一维。
- **多环境下写 `if terminated:`**：`terminated` 是一组布尔值，应使用 `done.any()`、`done.all()` 或按环境下标处理。
- **在同一个 Python 进程里先跑 CPU/渲染，再临时启用 GPU PhysX**：可能触发初始化顺序错误。`num_envs=16` 建议单独进程验证。

### 观测与渲染

- **误以为 `rgbd` 只剩图像**：在本节的 `PickCube-v1` 中，`rgbd` 观测仍包含 `agent` 和 `extra` 状态量。纯视觉策略需要自己在数据管线里过滤。
- **把渲染图和观测图混在一起**：`env.render()` 用于展示，`obs["sensor_data"]` 才是策略观测。

### 控制与评测

- **用 reward 判断成功**：成没成看 `info["success"]`。reward 是训练信号，大小和任务设计有关。
- **拿不同 `control_mode` 的成功率直接横比**：动作空间和动作语义都变了，比较不公平。

## 自查问题

下面几个问题可用于回顾本章全部内容：

1. 为什么 `import mani_skill.envs` 看起来什么都没返回，却是 `gym.make("PickCube-v1")` 能工作的前提？
2. `obs_mode="state"` 和 `obs_mode="rgbd"` 的返回结构有什么不同？`rgbd` 是否会自动移除状态量？
3. `pd_ee_delta_pose` 的 7 维动作大致对应什么？它和 `pd_joint_delta_pos` 为什么不能直接比较？
4. `reward` 和 `info["success"]` 分别应该用来做什么？
5. 为什么 `num_envs=1` 时观测是 `(1, 42)`？什么时候会想用 `CPUGymWrapper` 得到 `(42,)`？
6. `num_envs=16` 的输出里，哪些信息能说明批量环境和 GPU 并行确实跑通了？
7. 随机动作下 `last_success` 是 `False`，能不能说明环境有问题？为什么？

这些问题如果能逐一回答，说明已经掌握了 ManiSkill 任务环境的基本接口。

## 小结

- `obs_mode` 决定网络输入结构，影响感知、数据和训练代码。从 state 切到 rgbd 不止改一行配置。
- `control_mode` 决定动作语义，影响规划、遥操作数据和策略输出。不同控制模式下的数据不能互相喂。
- `success` 是评测应记录的完成事实，reward 是训练信号，两者不要混用。
- 日志里应记录 `env_id`、`obs_mode`、`control_mode`、`reward_mode`、`seed`、`episode_length`、`success` 及子条件，方便后续归因分析。
- 本章产物不是 benchmark 报告，而是后续数据、训练和评测章节可以复用的任务接口说明。

## 参考资料

- ManiSkill Documentation: Getting Started / Quickstart
- ManiSkill Documentation: Observation
- ManiSkill Documentation: Controllers
- ManiSkill Documentation: Custom Tasks
- ManiSkill GitHub: <https://github.com/haosulab/ManiSkill>
- SAPIEN Project: <https://sapien.ucsd.edu/>
- 本仓库示例：`labs/04-simulation/maniskill_pickcube_artifacts.py`

## 导航

- 上一节：[批量接口、GPU 并行与 CPUGymWrapper](05-batch-and-gpu.md)
- 返回上级：[ManiSkill 任务环境](../01-maniskill-tasks.md)
- 返回本章：[06 仿真建模](../../README.md)
