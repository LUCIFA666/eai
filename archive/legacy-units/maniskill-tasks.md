# ManiSkill 任务环境

ManiSkill 可以先理解成 SAPIEN 之上的“任务环境层”。SAPIEN 负责物理、机器人、关节物体、相机和接触；ManiSkill 把这些底层能力组织成一个个可以直接交互的操作任务。

对学习者来说，最直接的变化是：不用从零摆桌子、加载机械臂、放方块、写相机和成功判定，而是用一个任务 ID 创建环境，然后按 `reset()`、`step()` 的节奏与它交互。

本节选用 ManiSkill 自带的标准任务 `PickCube-v1`。它是一个环境 ID，导入 `mani_skill.envs` 后就可以通过 `gym.make("PickCube-v1")` 创建。任务目标很直观：桌上有一个方块，机器人需要把它抓起来并放到目标位置附近。

![PickCube-v1 reset 后的任务画面](../../section/05-simulation-and-task-modeling/assets/maniskill_pickcube_reset.png)

这个任务足够小，适合作为第一条 ManiSkill 闭环；同时又包含操作任务里常见的几件事：机械臂、夹爪、物体、目标、观测、动作、奖励和成功条件。把它读懂，再去看开抽屉、插销、堆叠等任务，会顺很多。

## 先看一段最小代码

```python
import gymnasium as gym
import mani_skill.envs

env = gym.make(
    "PickCube-v1",
    obs_mode="state",
    control_mode="pd_ee_delta_pose",
    render_mode="rgb_array",
)

obs, info = env.reset(seed=0)
action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
env.close()
```

这段代码体现了 ManiSkill 的基本学习方式：用环境 ID 创建任务，用 `obs_mode` 决定策略看到什么，用 `control_mode` 决定动作如何解释，再从 `reward` 和 `info["success"]` 里读取训练信号与完成判定。

随机动作通常不会成功抓取方块，这很正常。第一次运行的目标不是得到成功策略，而是确认任务接口能跑、观测能读、动作空间清楚、成功条件可以记录。

## 这一组页面包含什么

| 小节 | 读完能回答 |
|---|---|
| [认识 ManiSkill：SAPIEN 之上的任务层](01-maniskill-tasks/01-maniskill-and-sapien.md) | ManiSkill 和 SAPIEN 各自负责什么 |
| [跑通 PickCube-v1：最小闭环](01-maniskill-tasks/02-pickcube-first-run.md) | 一个 ManiSkill 任务如何用 Gymnasium 接口跑起来 |
| [任务的五把钥匙](01-maniskill-tasks/03-task-interfaces.md) | `env_id`、`obs_mode`、`control_mode`、`reward_mode`、`success` 各自改变什么 |
| [观测与渲染](01-maniskill-tasks/04-observation-and-rendering.md) | `state`、`rgbd`、`sensor_data` 和 `env.render()` 的区别 |
| [批量接口与 GPU 并行](01-maniskill-tasks/05-batch-and-gpu.md) | `num_envs` 如何影响接口形状，什么时候需要 `CPUGymWrapper` |
| [下游衔接与常见易错点](01-maniskill-tasks/06-downstream-and-faq.md) | ManiSkill 接到数据、训练和评测时容易混淆什么 |

如果你只是想快速认识 ManiSkill，可以沿着这一组页面读。若要更系统地理解任务接口、真实 probe 产物、任务内部结构，以及它如何与 Genesis、Isaac Sim 或自建任务工作流衔接，建议继续阅读下一组：[ManiSkill 任务接口与 PickCube 实战](02-maniskill-task-interfaces.md)。

## 配套脚本与产物

本节示例脚本放在：

```text
labs/04-simulation/maniskill_pickcube_demo.py
labs/04-simulation/maniskill_pickcube_artifacts.py
```

成功运行后，主要产物包括：

```text
runs/04-simulation/maniskill_pickcube_summary.json
runs/04-simulation/maniskill_pickcube_spaces.txt
runs/04-simulation/maniskill_pickcube_vector.json
runs/04-simulation/maniskill_pickcube_wrapper.txt
section/05-simulation-and-task-modeling/assets/maniskill_pickcube_reset.png
section/05-simulation-and-task-modeling/assets/maniskill_pickcube_rgb.png
section/05-simulation-and-task-modeling/assets/maniskill_pickcube_depth.png
section/05-simulation-and-task-modeling/assets/maniskill_pickcube_rollout.mp4
```

这些产物的作用不同：图片和视频帮助观察任务现象，JSON 和 space 输出帮助确认接口。不要用视频替代 `success`、shape 和 action space 检查。

## 导航

- 上一节：[SAPIEN 生态](../05-sapien-ecosystem.md)
- 返回本章：[仿真建模](../README.md)
- 下一节：[其他仿真生态](../06-other-simulation-ecosystems.md)
