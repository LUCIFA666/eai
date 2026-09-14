# 认识 ManiSkill：SAPIEN 之上的任务层

我们先不从 benchmark 讲起，而是先把 ManiSkill 在 SAPIEN 生态中的位置搞清楚。对于初学者来说，最重要的不是背出 ManiSkill 有多少套任务，而是理解它和 SAPIEN 的分工：谁管物理，谁管任务，我们写的代码主要和谁打交道。

## 本节目标

本节围绕下面几个问题展开：

1. SAPIEN 和 ManiSkill 各自负责什么，为什么本节主要和 ManiSkill 这一层打交道。
2. ManiSkill 是如何把 SAPIEN 的底层能力封装成标准任务接口的。
3. `import mani_skill.envs` 背后做了什么，为什么它是 `gym.make("PickCube-v1")` 能工作的前提。
4. 一个 ManiSkill 任务的基本节奏（闭环）是什么样的。

## ManiSkill 在 SAPIEN 上面补了什么

SAPIEN 更像底层仿真后端：它处理刚体、关节、接触、相机和渲染。ManiSkill 则把这些能力整理成任务环境：某个桌面任务里用什么机器人，物体怎么初始化，相机放在哪里，动作如何解释，奖励怎么计算，成功条件是什么，都会被任务类封装起来。

可以这样分工：

| 层级 | 主要负责什么 | 本节里怎么接触 |
|---|---|---|
| SAPIEN | 物理、关节物体、接触、相机、渲染 | 通过 ManiSkill 间接使用 |
| ManiSkill | 任务、机器人控制接口、观测、奖励、成功判定 | 用 `gym.make("PickCube-v1")` 创建 |
| Gymnasium | 统一的环境交互格式 | 用 `reset()` / `step()` 跑闭环 |

所以本节的代码不会从 SAPIEN 原始 API 开始写桌面、方块和机器人，而是直接进入 ManiSkill 的任务接口。这样更接近后续训练、采数据和评测会用到的入口。

### 从 `gym.make` 到任务实例：背后发生了什么

从使用者角度看，入口只有 `gym.make("PickCube-v1")`。但它背后大致有几层：

| 层级 | 作用 | 初学者需要关心什么 |
|---|---|---|
| 任务注册 | 把 `PickCube-v1` 这样的字符串映射到任务类 | 漏掉 `import mani_skill.envs` 会找不到环境 |
| 场景构建 | 加载机器人、桌面、方块、目标和相机 | 决定 reset 后场景里有什么 |
| episode 初始化 | 根据 seed 初始化物体与目标位置 | 决定每一轮从哪里开始 |
| 控制器 | 把动作向量解释成关节或末端控制目标 | 决定动作空间维度和语义 |
| 观测构造 | 把机器人状态、任务状态、传感器数据组织成 `obs` | 决定策略网络的输入结构 |
| 奖励与成功 | 计算 reward，并把子条件写入 `info` | 决定训练信号和完成判定 |

本节不要求去改 ManiSkill 源码。先能从外部接口读懂任务，已经足够支撑后面的采数据和训练。等需要自定义任务时，再去看 ManiSkill 的任务类、场景加载、`evaluate()`、`compute_dense_reward()` 等实现函数会更合适。

### `import mani_skill.envs` — 容易被忽略的一行

有一行代码看起来什么都没做，但它必不可少：

```python
import mani_skill.envs  # 注册 ManiSkill 任务
```

它没有返回值，但它会把 ManiSkill 内置任务注册到 Gymnasium 里。没有这一步，`gym.make("PickCube-v1")` 可能找不到对应环境。这是 ManiSkill 初学者最容易漏掉的一行。

## 一个 ManiSkill 任务的基本节奏

从创建环境到跑完一个 episode，核心节奏只有五步：

<figure class="doc-figure figure-loop" aria-label="ManiSkill 任务闭环">
  <p class="doc-figure-title">一个 ManiSkill 任务的基本节奏</p>
  <p class="doc-figure-subtitle">从重置 episode，到给动作、推进物理、读取成功信息。</p>
  <div class="figure-pipeline">
    <div class="figure-node tone-green">
      <strong>创建任务</strong>
      <span><code>gym.make("PickCube-v1")</code> 选定任务、观测和控制模式。</span>
    </div>
    <div class="figure-node tone-blue">
      <strong>重置 episode</strong>
      <span><code>reset(seed=0)</code> 得到初始 <code>obs</code> 与 <code>info</code>。</span>
    </div>
    <div class="figure-node tone-gold">
      <strong>给动作</strong>
      <span>动作来自策略，也可以先用 <code>action_space.sample()</code> 冒烟测试。</span>
    </div>
    <div class="figure-node tone-rose">
      <strong>推进仿真</strong>
      <span><code>step(action)</code> 更新物理状态、奖励和结束标志。</span>
    </div>
    <div class="figure-node tone-green">
      <strong>读结果</strong>
      <span>从 <code>reward</code> 读训练信号，从 <code>info["success"]</code> 读是否完成。</span>
    </div>
  </div>
  <div class="figure-note">核心节奏：<code>reset</code> → 读 <code>obs</code> → 给 <code>action</code> → <code>step</code> → 从 <code>info</code> 读任务状态。</div>
</figure>

后面的小节里，我们会把这张图的每一步展开：创建环境时需要配置哪些参数（第三节），`reset()` 和 `step()` 返回的观测长什么样（第四节），以及多个环境并行时这个闭环会怎么变（第五节）。

## 小结

- ManiSkill 是 SAPIEN 上层的任务环境库，用 `gym.make()` 就能创建标准操作任务。
- `import mani_skill.envs` 负责注册任务名，是 `gym.make("PickCube-v1")` 能工作的前提。这是最容易漏掉的一行。
- 一个 episode 的基本节奏是：`reset()` 拿初始观测，循环里给动作并 `step()`，再从返回值里读奖励、结束标志和 `info`。
- ManiSkill 不只是一个任务集合——它同时把控制器、观测构造、奖励计算和成功判定都封装在了任务实例里。

## 导航

- 上一节：[ManiSkill 任务环境](../01-maniskill-tasks.md)
- 返回上级：[ManiSkill 任务环境](../01-maniskill-tasks.md)
- 下一节：[跑通 PickCube-v1：最小闭环](02-pickcube-first-run.md)
