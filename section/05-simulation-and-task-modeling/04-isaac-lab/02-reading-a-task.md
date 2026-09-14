# 任务结构与 Manager 系统

上一部分已经跑通 CartPole，并建立了三个理解视角：并行张量、配置驱动 + Manager、仿真到 RL 环境。本部分开始进入“读任务”的阶段。Isaac Lab 任务通常分散在注册入口、环境配置、MDP 函数、agent 配置和训练脚本里；如果按文件顺序硬扫，很容易迷路。

## 本节目标

本节围绕下面几个问题展开：

1. 读一个 Isaac Lab 任务时，应该先找哪些文件和配置？
2. 环境类、Manager、MDP 函数和训练配置之间怎么连接？
3. Manager-based 和 Direct 两种写法分别适合什么任务？
4. 如何沿着 reset、observation、reward、termination 追踪一次 step？

本部分给出一套固定读法：先找任务 ID 和 `gym.register`，再看 `env_cfg` 如何声明 scene、observation、action、reward、termination 和 event，最后看 agent 配置与训练入口。这样读任务，才知道每个函数在闭环里的位置。

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [任务由什么组成](02-reading-a-task/01-env-anatomy.md) | 一个 RL 任务最低由哪几块组成？ | scene、observation、action、reward、termination、event 与 MDP 循环 |
| [八大 Manager 系统](02-reading-a-task/02-manager-system.md) | 每个 Manager 到底管什么？ | Observation / Action / Reward / Termination / Event / Command / Curriculum / Recorder |
| [拆解 reach 任务](02-reading-a-task/03-walkthrough-reach.md) | 一个真实任务怎么从注册入口一路读到奖励？ | 任务注册、环境配置、scene、command、observation、action、reward、termination |
| [Manager-based vs Direct](02-reading-a-task/04-manager-based-vs-direct.md) | 什么时候用声明式，什么时候手写环境类？ | 两种工作流的结构、优缺点和选择规则 |

## 读任务的固定顺序

建议以后读任何 Isaac Lab 任务都按下面顺序走：

```text
1. 找任务 ID：它在 __init__.py 里如何 gym.register？
2. 找 env_cfg：scene / observations / actions / rewards / terminations 在哪里声明？
3. 找 mdp 函数：自定义 observation、reward、termination 是怎么计算的？
4. 找 agent 配置：PPO、SKRL、RL-Games 等训练超参在哪里？
5. 跑一次最小训练或 play：日志和画面是否符合代码预期？
```

这个顺序的好处是：先看任务的结构，再看局部函数。不要一上来就钻进某个 reward 函数，否则很容易知道一棵树的叶子，却不知道这棵树长在哪里。

## 读完本部分后

完成这一部分后，应该能打开任意一个官方任务，按注册入口、环境配置、Manager、MDP 函数、agent 配置的顺序读下去，并判断它更适合用 Manager-based 还是 Direct 工作流。

## 导航

- 上一页：[认识 Isaac Lab](01-getting-started.md)
- 返回上级：[Isaac Lab](../04-isaac-lab.md)
- 下一页：[场景与机器人资产](03-scene-and-robot.md)
