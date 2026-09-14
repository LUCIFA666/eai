# Isaac Lab 是什么

如果你刚读完 Isaac Sim，可能会自然地问：既然 Isaac Sim 已经能加载机器人、推进物理、渲染相机，为什么还要再学 Isaac Lab？这一页先回答这个问题。不要求你已经会写 Isaac Sim 脚本，也不要求已经掌握 PPO；先把 Isaac Lab 的位置看清，后面再跑训练。

## 本节目标

本节围绕下面几个问题展开：

1. Isaac Lab 为什么不是 Isaac Sim 的替代品，而是任务与训练层？
2. 机器人学习任务为什么需要 observation、action、reward、reset 这些接口？
3. 并行环境和训练库在 Isaac Lab 中分别承担什么职责？
4. 初学者应该如何判断自己该看 Isaac Sim 还是 Isaac Lab？

## 它不是仿真器，而是任务与训练层

先记住一句话：**Isaac Lab 不是仿真器**。

Isaac Sim 才是负责物理、渲染和场景的底层系统。它能加载机器人、摆放物体、推进 PhysX 物理、渲染相机画面、输出深度图或分割图。你可以把它理解成一个能被 Python 控制的真实物理舞台。

Isaac Lab 建在 Isaac Sim 之上，负责把这个舞台组织成可以训练的机器人学习任务。它关心的是：

- 同时复制出几百到几千个环境；
- 把机器人状态整理成 observation；
- 把策略输出的 action 转成控制命令；
- 计算 reward、termination、reset；
- 接入 RSL-RL、SKRL、RL-Games、SB3 等训练库；
- 保存日志、checkpoint，并支持回放和评估。

可以这样理解：Isaac Sim 提供物理舞台，Isaac Lab 把舞台改造成训练场。训练策略时，你要的不是“一个机器人能在场景里动一下”，而是一套能反复 reset、批量采样、自动评分、保存日志和回放结果的任务系统。

## 为什么不能直接拿 Isaac Sim 训练 RL

强化学习不是只需要一个物理世界。一个可训练任务至少还需要五件事：

| 训练需要什么 | Isaac Sim 直接给够了吗 | Isaac Lab 补上的东西 |
|---|---|---|
| 大量并行环境 | 不直接提供标准 RL 批量接口 | 按 `num_envs` 克隆环境并批量 step |
| 标准 `env.step(action)` | 底层 API 更偏仿真控制 | 包装成 Gymnasium 风格环境 |
| observation / action schema | 需要自己组织 | Observation / Action Manager |
| reward / termination / reset | 需要自己写任务逻辑 | Reward / Termination / Event Manager |
| 训练库对接 | 不是训练库接口 | VecEnv wrapper、训练脚本、配置入口 |

所以 Isaac Lab 的核心价值不是“再造一个仿真器”，而是把仿真器变成**机器人学习环境工厂**。这也是后面所有页面的主线：一个物理场景如何变成 observation / action / reward / reset 的闭环。

## 从训练脚本到 GPU 的分层

把链路从上到下捋一遍：

<figure class="doc-figure">
<p class="doc-figure-title">从训练脚本到 GPU 的分层</p>
<div class="figure-flow">
<div class="figure-node">训练脚本：选择任务、算法和超参数，例如 <code>train.py --task=Isaac-Cartpole-v0</code></div>
<div class="figure-node">RL wrapper：把 Isaac Lab 环境转成具体训练库需要的 VecEnv 接口</div>
<div class="figure-node">Isaac Lab 环境：组织 observation / action / reward / termination / reset</div>
<div class="figure-node">Isaac Sim：PhysX 物理、RTX 渲染、USD 场景、传感器输出</div>
<div class="figure-node">GPU：并行物理、渲染和张量计算</div>
</div>
<p class="doc-figure-subtitle">上层训练库只看到标准环境；底层的物理与渲染细节由 Isaac Sim 承担。</p>
</figure>

关键点是：**RL 库不需要知道底层是 Isaac Sim**。它只需要一个能 reset、能 step、能返回 observation、reward 和 done 的环境。Isaac Lab 正是中间的适配层。

这层隔离带来一个很实用的结果：换机器人、换场景、换奖励时，训练脚本不必完全重写；换训练库时，也不需要重新理解 PhysX 或 USD。课程后面会把这些“可换的部分”逐块拆开。

## 两种任务写法

Isaac Lab 写任务有两种主要风格：

| 写法 | 适合谁 | 特点 |
|---|---|---|
| Manager-based | 新任务、课程学习、需要复用和组合 | 用配置类声明 scene、observation、action、reward、termination 等模块 |
| Direct | 从 Isaac Gym 迁移、非标准逻辑、追求特殊控制 | 直接写环境类，灵活但样板代码更多 |

初学时不用纠结。**拿不准就用 Manager-based**。它更适合学习，也更符合 Isaac Lab 当前推荐的任务组织方式。Direct 会在后面的任务解剖页里作为对照出现。

## 它和 Isaac Gym 的关系

如果你听过 NVIDIA 的 Isaac Gym（2020 年底发布首个 preview，论文发表于 NeurIPS 2021），可以这样理解：

- Isaac Gym 是早期面向 GPU 加速机器人学习的仿真训练框架；
- Isaac Gym 已经停止维护；
- Isaac Lab 是它的正式继任者；
- Isaac Lab 的底层换成 Isaac Sim + Omniverse 体系，使用 USD 场景、PhysX 5 和 RTX 渲染能力。

新项目不建议再从 Isaac Gym 开始。课程后面默认以 Isaac Lab 为主线。

## 小结

- Isaac Lab 不是仿真器，而是建在 Isaac Sim 之上的机器人学习框架。
- Isaac Sim 负责物理、渲染、场景和传感器；Isaac Lab 负责把这些组织成可训练任务。
- 它解决 RL / IL 的关键需求：并行环境、标准接口、批量 observation / action / reward、任务复用和训练库对接。
- 初学时优先走 Manager-based 工作流，Direct 作为进阶或迁移场景再看。

## 参考资料

- Isaac Lab Documentation. https://isaac-sim.github.io/IsaacLab/
- Isaac Lab GitHub. https://github.com/isaac-sim/IsaacLab
- Makoviychuk, V., et al. "Isaac Gym: High Performance GPU-Based Physics Simulation for Robot Learning." NeurIPS 2021.

## 导航

- 返回目录：[认识 Isaac Lab](../01-getting-started.md)
- 下一页：[第一次训练](02-first-run-cartpole.md)
