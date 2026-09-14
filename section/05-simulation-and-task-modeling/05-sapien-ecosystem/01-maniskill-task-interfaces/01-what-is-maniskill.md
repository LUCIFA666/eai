# ManiSkill 是什么

学习一个机器人操作任务时，最容易把两件事混在一起：一件是“世界如何被仿真”，另一件是“任务如何被学习算法使用”。前者关心物理、碰撞、关节、相机和渲染；后者关心观测、动作、奖励、终止条件和成功判定。

在 SAPIEN 生态里，SAPIEN 更接近第一层，ManiSkill 更接近第二层。SAPIEN 提供底层仿真能力，ManiSkill 在这些能力之上组织任务：机器人怎么初始化，物体放在哪里，策略看到什么，动作怎样解释，奖励怎么算，任务是否完成。

这也是本节学习 ManiSkill 的角度：不把它当作另一个“大而全”的仿真平台，而是把它当作标准任务接口来读。

## 从场景到任务

如果从零写仿真脚本，通常要先加载机器人、创建桌子和物体、放置相机、写控制循环，再判断任务是否成功。ManiSkill 把这些步骤封装到任务环境里，读者面对的入口变成：

```python
import gymnasium as gym
import mani_skill.envs

env = gym.make(
    "PickCube-v1",
    obs_mode="state",
    control_mode="pd_ee_delta_pose",
    reward_mode="dense",
)
```

这里的 `PickCube-v1` 不是本书新起的脚本名，而是 ManiSkill 内置的环境 ID。`import mani_skill.envs` 会把 ManiSkill 任务注册到 Gymnasium；注册完成后，`gym.make("PickCube-v1")` 才知道要创建哪个任务。

这段配置已经回答了四个问题：做什么任务，策略看到什么，动作控制什么，训练信号怎么给。真正评测时，还要读 `info["success"]` 和它的子条件。

## 一张心智图

从使用者角度看，ManiSkill 程序可以按下面这条线理解：

```text
import mani_skill.envs
        |
        v
Gymnasium 注册表里出现 PickCube-v1
        |
        v
gym.make(env_id, obs_mode, control_mode, reward_mode, num_envs)
        |
        v
ManiSkill 创建任务：场景、机器人、物体、控制器、相机、奖励和成功条件
        |
        v
reset(seed) 产生一个 episode 初始状态
        |
        v
step(action) 推进物理、更新观测、计算 reward、写入 info
        |
        v
下游算法读取 obs / reward / terminated / truncated / info
```

这张图的重点是：`gym.make()` 不是“启动一个黑盒 demo”，而是在选定一个任务契约。`obs_mode`、`control_mode`、`reward_mode` 和 `num_envs` 会影响后面每一步返回的数据形状和语义。

## 分工边界

| 工具 | 在本章里的角色 | 更适合解决的问题 |
|---|---|---|
| SAPIEN | 底层仿真能力 | 物理、机器人、关节物体、接触、相机、渲染 |
| ManiSkill | 标准化任务环境 | 物体操作任务、benchmark、RL / IL 入门、GPU batch |
| Genesis | 自定义实验后端和多物理探索 | 原子动作、实验室物体迁移、刚柔耦合、多物理 |
| Isaac Sim | 高保真机器人仿真平台 | USD 资产、RTX 传感器、ROS 2、合成数据、系统工程 |
| Isaac Lab | Isaac Sim 之上的学习任务框架 | 并行训练、Manager 系统、RL / IL 工作流 |

这张表不是要给平台排座次，而是帮助读者判断学习重点。ManiSkill 的优势是把任务接口整理得很清楚；Genesis 和 Isaac Sim 更常被用来处理自定义后端、高保真资产、传感器生态和系统集成问题。学 ManiSkill，不等于要用它替代其他平台；更重要的是学会一个操作任务应该怎样被写成可训练、可评测、可复现的接口。

## 常见误解

| 误解 | 更准确的理解 |
|---|---|
| ManiSkill 是另一个通用仿真器 | 它更像 SAPIEN 之上的任务环境和 benchmark 层 |
| 视频能播放就说明任务完成 | 视频只说明现象可见，成功要看 `info["success"]` |
| reward 高就等于成功 | reward 是训练信号，success 是完成判定 |
| ManiSkill 可以替代 Genesis / Isaac Sim | 它们解决的问题不同，ManiSkill 更适合学习标准任务接口 |

## 小结

- SAPIEN 提供底层仿真能力，ManiSkill 负责任务环境。
- `PickCube-v1` 是 ManiSkill 内置环境 ID，需要通过 `import mani_skill.envs` 注册后再交给 `gym.make()`。
- 学 ManiSkill 的重点是读懂任务配置、观测、动作、奖励、成功和 batch。
- 任务 API 不是完整后端迁移方案；换平台时还要重新核对资产、控制、传感器和成功判定来源。

## 导航

- 返回上级：[ManiSkill 任务接口与 PickCube 实战](../01-maniskill-task-interfaces.md)
- 下一页：[安装与环境自检](02-install-and-env-check.md)
