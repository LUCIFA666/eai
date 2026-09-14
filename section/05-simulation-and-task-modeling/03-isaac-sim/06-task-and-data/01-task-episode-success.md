# 任务、episode 与成功判定

上一部分结尾你已经有了一个"动 + 看"的最小闭环：每一帧发一个动作、读一组观测。但一个闭环还不是"一个任务"。把杯子抓起来、把方块从 A 推到 B——这些得有明确的**开始**、**结束**和"**算不算成功**"。这一页就把一段会动、会看的仿真，收敛成一个有边界、能判定、能复盘的 **episode（任务回合）**。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么说任务不是一个循环，而是一组接口（reset / step / success…）？
2. 一个 episode 怎么界定，多阶段任务又该怎么拆？
3. 成功和失败分别该怎么客观判定、怎么留证据，而不只看视频？

阅读这一页前，最好已经能让机器人动起来、读到观测，并准备把它组织成一个可评测任务。这一页几乎不引入新 API，重点是任务的"骨架结构"和判定思路；代码以最小骨架示意为主，方便你套到自己的脚本里。

## 任务不是一个循环，而是一组接口

很多人第一次写任务，会写成"加载场景，然后循环发动作"。这能跑出演示，但撑不起数据采集和评测——因为它没回答"这一回合从哪开始、到哪结束、算不算成功"。

更清楚的做法是把任务拆成几个**接口**，每个接口只回答一个问题：

一句话类比：**把任务当成"一直发动作的循环"，就像把一家餐厅理解成"一直在炒菜"**。真正能运转的餐厅得有进货、备菜、出餐、验菜的分工；一个能采集、能评测的任务，也得有加载、初始化、决策、记录、判定的分工。

<figure class="doc-figure">
<p class="doc-figure-title">把任务拆成一组接口，而不是一个大循环</p>
<div class="figure-flow">
<div class="figure-node"><strong>load_scene：</strong>世界里有什么——机器人、物体、桌面、灯光、相机的关键 prim path</div>
<div class="figure-node"><strong>reset / randomize：</strong>这一回合从哪开始——初始位姿、哪些变量随机、采样值是否被记录</div>
<div class="figure-node"><strong>get_action：</strong>高层目标怎么变成航点 / 关节目标 / 夹爪命令</div>
<div class="figure-node"><strong>get_observation：</strong>图像、状态、阶段、时间戳怎么组成 observation 并对齐</div>
<div class="figure-node"><strong>evaluate / log：</strong>success / failure / timeout 怎么判定，视频与结构化数据存到哪</div>
</div>
<p class="doc-figure-subtitle">每个接口只回答一个问题；缺哪个，扩展和复盘就会卡在哪。</p>
</figure>

可以用下面这张表自检：任务是否已经"成形"，还是只是一个演示循环。

| 模块 | 最少要说清什么 |
|---|---|
| `load_scene` | 加载哪些 USD 资产，关键 prim path 是什么 |
| `reset` | 机器人、物体、相机、任务目标如何初始化 |
| `randomize` | 位置 / 姿态 / 材质 / 光照 / 相机扰动是否记录采样值 |
| `get_observation` | 图像、状态、阶段、时间戳是否对齐 |
| `get_action` | 高层目标如何变成航点、关节目标或夹爪命令 |
| `evaluate` | success / failure / timeout 和 `failure_reason` 如何判断 |
| `log_episode` | 视频、结构化数据、metadata 保存在哪里 |

一旦这些边界清楚，后面换物体、换机器人、换相机，或接 RMPflow、VLA、模仿学习，都会轻很多。Isaac Sim 不会替你设计这些接口，但它提供了实现接口所需的场景、物理、传感器和控制能力。

## 一个 episode 就是一次完整尝试

把上面接口串起来，一个 episode 就是一次有头有尾的尝试：

```text
reset 场景
  → 初始化机器人、物体、相机、任务目标（按需随机化）
  → 按状态机执行多个阶段，每帧 step 一次物理
  → 每一帧记录 observation / action / state / phase
  → 判定 success / failure / timeout
  → 保存视频、日志和结构化数据
```

写成最小骨架（接上一部分的"动 + 看"闭环，省略控制器细节）：

```python
def run_episode(world, task, max_steps=600):
    task.reset()                      # 归零：见下方"reset 要归零什么"
    records = []
    result = {"success": False, "failure_reason": "timeout"}

    for step_index in range(max_steps):
        obs = task.get_observation()          # 图像 / 状态 / 阶段
        action = task.get_action(obs)         # 当前阶段该发什么
        task.apply(action)
        world.step(render=True)               # 推进一帧物理 + 渲染

        records.append(task.log_step(step_index, obs, action))

        ok, fail = task.evaluate(obs)         # 成功 / 失败判定
        if ok:
            result = {"success": True, "failure_reason": None}
            break
        if fail:
            result = {"success": False, "failure_reason": fail}
            break

    task.save_episode(records, result)        # 视频 + 结构化数据 + metadata
    return result
```

**reset 要归零什么**，是新手最容易漏的地方。它不只是把物体摆回原位，而是要清掉所有"上一回合的残留"：

| 要归零的东西 | 漏了会怎样 |
|---|---|
| 物体 / 机器人初始位姿 | 这一回合从上一回合的终态开始，初始分布不可控 |
| 控制器内部状态（积分项、计时器） | 控制器带着上一回合的速度 / 误差继续跑 |
| 状态机的 `phase` 和步数计数 | episode 边界错乱，日志阶段对不上 |
| 相机 / 传感器缓存 | reset 后第一帧读到旧图 |
| 随机种子 / 采样记录 | 这一回合用了什么随机值无据可查 |

`reset()` 之后通常还要 `world.step()` 空跑几帧，等物理稳定，再开始正式记录——否则第一帧读到的是还没落定的状态。

## 多阶段任务

一个抓取任务不是"一条命令抓起来"，而是一段有名字的阶段序列：

```text
approach_high   高位预接近
pre_grasp       预抓取接近
grasp           下降到抓取位姿
settle          稳定等待几帧
close           闭合夹爪
lift            抬起目标
done            完成
```

下图是同一次抓取任务回合在不同阶段的画面（从左到右：高位接近 → 下降抓取 → 抬起搬运 → 放置完成）。把一次 episode 看成这样一段"有名字的阶段序列"，调试、日志和视频才能按阶段对齐：

![一次抓取任务回合的阶段进展：高位接近、下降抓取、抬起搬运、放置完成](/section/05-simulation-and-task-modeling/assets/isaac-sim-lab-episode-stages.jpg)

状态机的骨架很简单——关键是每个阶段有自己的**进入动作**和**退出条件**：

```python
PHASES = ["approach_high", "pre_grasp", "grasp", "settle", "close", "lift", "done"]

def step_state_machine(phase, obs):
    target = None            # 未覆盖的阶段返回 None，由调用方处理
    if phase == "approach_high":
        target = obs["object_pos"] + [0, 0, 0.20]      # 物体正上方
        if reached(obs["ee_pos"], target):
            return target, "pre_grasp"
    elif phase == "grasp":
        target = obs["object_pos"] + [0, 0, 0.005]
        if reached(obs["ee_pos"], target):
            return target, "settle"
    elif phase == "lift":
        target = obs["object_pos"] + [0, 0, 0.25]
        if obs["object_pos"][2] - obs["object_z0"] > 0.10:
            return target, "done"
    # ... 其余阶段同理
    return target, phase     # 条件没满足就停在本阶段
```

为什么不写成一个大 `while`？因为状态机把"为什么失败"变得可定位。出问题时你不用笼统地问"为什么 pick 失败"，而能问得很具体：

```text
是预接近没到位？        → 停在 approach_high
是下降时偏了？          → grasp 阶段 xy_error 偏大
是闭合前没稳定？        → settle 帧数不够
是夹爪闭合了却没夹住？  → close 后 gripper_width 异常
是抬升高度不够？        → lift 阶段 object_z 没涨
```

每个阶段有名字，失败就会暴露在具体阶段，而不是混在一坨循环里。换机器人、换物体、换夹爪时，这一点尤其省事。

## 成功判定不能只看视频

看视频很重要，但它不能当唯一标准。视频告诉你"看起来发生了什么"，成功判定要回答"任务语义是否真的满足"。

以 pick 为例，肉眼看见物体离开桌面**远远不够**。一个可靠的判定通常会同时看几条：

```python
def is_success(obs):
    lifted   = obs["object_pos"][2] - obs["object_z0"] > 0.10   # 真的抬升超过阈值
    stable   = obs["stable_frames"] >= 10                       # 稳定保持若干帧，不是弹一下
    grasped  = 0.01 < obs["gripper_width"] < 0.08               # 夹爪闭合到合理宽度
    on_target = obs["grasped_id"] == obs["target_id"]           # 抓的是目标，不是旁边的
    no_glitch = not obs["penetration"]                          # 没穿模 / 虚假吸附
    return lifted and stable and grasped and on_target and no_glitch
```

这比"视频里抓起来了"麻烦，但它是数据质量的底线：**一旦把失败样例标成成功，后面的训练、评测和模型分析都会被污染**。

## 最小 episode 判定

下面是一个最小 episode（一个方块从空中落向地面的目标圆盘）的输出摘要，用来演示上面的“状态机阶段 + 多条件判定”。它不需要机械臂和 IK，却完整跑过 `reset → 逐帧 step → 判定` 的闭环：

```text
phase 转换序列 (step, phase):
  (0,  'falling')
  (23, 'touchdown')
  (33, 'falling')      # 触地后弹起、又短暂离地
  (37, 'touchdown')

成功判定（多条件，全真才算成功）:
  start            : [0.137, -0.031, 1.0]
  final_pos        : [0.1323, -0.0342, 0.05]
  phase==settled   : False     # 方块仍在微小弹动，没“静止保持”够久
  in_target_x(<R)  : True
  in_target_y(<R)  : True
  => success       : False
```

这部分输出恰好说明了为什么“成功判定不能只看落点”：方块的 xy 明明落进了目标圆盘（`in_target` 都是 True），但因为它一直在微小弹跳、没达到“静止保持若干帧”的 `settled` 条件，最终仍判 `success=False`。**多条件取与（AND）让判定更严格，不容易把“看起来成了”的样例误标成成功**——这正是上文强调的。

## 失败也要留证据

一个 episode 不应该只有一个视频文件。每一步至少记录足够的字段，让你能回答"这一帧处在哪个阶段、发了什么动作、物体在哪、为什么判成功 / 失败"：

```text
step_index           # 时间骨架，对齐一切的主键
phase                # 当前阶段名
action               # 这一帧发的动作
joint_positions      # 关节角 / 速度
ee_pose              # 末端位姿（位置 + wxyz 四元数）
gripper_width        # 夹爪开合
object_pose          # 目标物体位姿
success / failure_reason
```

一个 episode 的产出，理想形态不是孤零零一个 `video.mp4`，而是一组对齐的结构化数据：

```text
episode_000/
    video.mp4          # 给人看的视图
    observations.h5    # 图像 / 状态 / 动作，按 step_index 对齐
    metadata.json      # 任务、机器人、相机、随机种子、资产版本
    success.json       # 是否完成 + 关键指标
    debug_events.jsonl # 阶段切换、失败原因、几何证据
```

特别提醒：**别只存成功样例**。失败样例往往最有诊断价值——它告诉你哪个阶段最容易卡、哪类物体最难抓、是运动生成挂了还是 drive / 接触挂了、成功判定是不是太松或太严。只有成功率数字、没有失败证据的实验，几乎无法迭代。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 加载场景 + 循环发动作就是一个任务 | 那只是演示，没有边界和判定 | 拆成接口：load / reset / action / obs / evaluate |
| reset 就是把物体摆回原位 | 控制器状态、phase、缓存都得清 | 按"reset 归零表"逐项清，再空跑几帧 |
| 多阶段任务写个大 while 就行 | 失败混成一团，无法定位 | 写成命名状态机，按阶段对齐日志 |
| 视频里抓起来了就是成功 | 视频只反映表象 | 判定看抬升 / 稳定 / 夹爪 / 目标 / 穿模 |
| 只存成功的 episode | 失败样例最有诊断价值 | 失败也存全字段 + `failure_reason` |
| 有视频就算采集到数据了 | 缺对齐字段无法训练 | 视频之外存结构化、按 `step_index` 对齐的数据 |

## 小结

- 任务不是一个循环，而是一组接口：load_scene / reset+randomize / get_action / get_observation / evaluate+log，每个只回答一个问题。
- 一个 episode 是一次完整尝试：reset（彻底归零）→ 状态机多阶段 step → 每帧记录 → 判定 → 保存。
- 多阶段任务写成命名状态机，失败才能定位到具体阶段，而不是混在大 `while` 里。
- 成功判定要看任务语义（抬升 / 稳定 / 夹爪 / 目标 / 无穿模），不能只看视频；失败样例也要留全证据。

## 参考资料

- ManiSkill Documentation, [Custom Tasks: Intro](https://maniskill.readthedocs.io/en/latest/user_guide/tutorials/custom_tasks/intro.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Examples](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/examples.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)

## 导航

- 返回目录：[任务、数据采集与合成数据](../06-task-and-data.md)
- 下一页：[数据采集、回放与质检](02-data-collection.md)
