# 10.1.1 MDP/POMDP

这一节不是只讲 MDP/POMDP 两个名词，而是把一个机器人强化学习任务拆成最小闭环：谁在决策、看到了什么、能做什么、为什么算成功、一次尝试什么时候结束、数据如何流向算法。后面学习 PPO、SAC、奖励设计时，都会反复回到这个建模框架。

## 学习目标

读完本页后，你应该能：

- 用自己的话解释 agent、environment、state、observation、action、reward、return、discount、trajectory、episode。
- 区分 value、Q value、advantage 各自回答的问题。
- 说明 MDP 和 POMDP 的区别，以及机器人任务为什么通常更像 POMDP。
- 判断一个任务更适合 on-policy 还是 off-policy 数据流。
- 把一个简单机器人或控制任务写成结构化任务定义，而不是只说“让它学会做事”。

## 为什么这对机器人 / VLA 很重要

在机器人里，算法通常不是第一层问题，任务建模才是。一个抓取任务如果 observation 漏掉夹爪开合状态、reward 只奖励“物体抬高”、termination 又设得太早，那么 PPO 和 SAC 都可能学偏。VLA 场景也是一样：模型很大不等于问题消失，你仍然要定义动作空间、成功信号、回报归因和 rollout 结束条件。

可以把 RL 想成一个反复运行的实验系统：

- 机器人或仿真环境产生观测。
- 策略根据观测输出动作。
- 环境执行动作，返回下一个观测和奖励。
- 训练器把这段交互当作数据，更新策略。

如果这个环节里任何一个定义错了，训练曲线也许会动，但学到的不一定是你要的能力。

## 核心概念

### 1. Agent、Environment、State、Observation

- `agent`：做决策的部分，通常是策略网络。
- `environment`：接收动作、推进系统动力学、返回反馈的部分。
- `state`：如果你能看到世界的全部决定性信息，这就是状态。
- `observation`：agent 实际拿到的输入，通常只是 state 的一部分或带噪声投影。

机器人任务里，真实 state 可能包括：

- 机械臂全部关节位置与速度。
- 末端执行器姿态。
- 目标物体 6D 位姿。
- 接触状态、摩擦、隐藏扰动。

但策略拿到的 observation 往往只是：

- 编码器读数。
- 相机图像。
- 力传感器数值。
- 历史动作或历史帧的一小段堆叠。

这就是为什么现实机器人经常是 POMDP，而不是理想化的完全可观测 MDP。

### 2. Action、Reward、Return

- `action`：agent 输出的控制命令。
- `reward`：单步反馈，表示这一步“看起来多好”。
- `return`：从当前时刻往后累计的总收益，通常带折扣。

离散动作示例：

- CartPole：左推 / 右推。

连续动作示例：

- Pendulum：施加多大扭矩。
- 机械臂：每个关节速度、位置增量或末端位姿增量。

单步 reward 很局部，但 return 体现长期效果。机器人里常见误区是只盯着即时奖励，忽略长期后果。例如末端快速撞向物体也许会立刻缩短距离，却可能导致抓取失败或不安全。

折扣回报常写成：

```text
G_t = r_t + γ · r_{t+1} + γ² · r_{t+2} + ...
```

其中 `γ` 是折扣因子（discount factor）：

- 越接近 `1`，越重视长期结果。
- 越小，越偏向眼前收益。

在机器人控制里，`γ` 往往对应”你希望策略有多强的长视野”。

### 3. Value、Q、Advantage

这三个量经常让初学者混淆，可以直接记成三个问题：

- `V(s)`：如果我现在在这个状态，未来总体有多好？
- `Q(s, a)`：如果我现在在这个状态，并且先做这个动作，未来总体有多好？
- `A(s, a)`：这个动作相对“平均水平”到底好多少？

一个常用关系是：

```text
A(s, a) = Q(s, a) - V(s)
```

直觉上：

- `V` 像“这个局面本身值多少钱”。
- `Q` 像“在这个局面里做某个具体动作值多少钱”。
- `A` 像“这个动作有没有超常发挥”。

PPO 经常直接依赖 advantage 来更新策略；SAC 则更强调学习 Q 函数并借它指导 actor。

### 4. Trajectory、Episode、Termination

- `trajectory`：一段连续交互序列，形如 `(o_t, a_t, r_t, o_{t+1}, ...)`。
- `episode`：从 reset 开始，到成功、失败或时间上限结束的一整次尝试。
- `termination`：这一局为什么结束。

机器人任务里常见结束条件：

- 成功抓到并抬起目标。
- 发生碰撞或越界。
- 达到最大步数。
- 对象掉落、姿态失控。

termination 的定义会直接影响训练信号。过早结束会减少探索，过晚结束会让失败状态反复刷无意义数据。

### 5. MDP 与 POMDP

当下一个状态和奖励只依赖当前状态与动作时，可以写成 MDP：

```text
(S, A, P, R, γ)
```

但现实里 agent 往往拿不到完整状态，只能看到 observation，于是更接近 POMDP：

```text
(S, A, O, P, R, Ω, γ)
```

你不必死记符号，关键是理解：

- MDP 假设“该知道的都知道了”。
- POMDP 承认“你只能看到部分世界”。

机器人为什么常是 POMDP：

- 相机有遮挡。
- 力觉有噪声。
- 目标物体的真实摩擦和质量未知。
- 单帧图像看不出速度，需要时间上下文。

应对办法通常不是“假装它是 MDP”，而是：

- 增加观测维度。
- 堆叠历史帧或历史动作。
- 使用状态估计器。
- 在训练和评测中明确部分可观测假设。

### 6. On-policy 与 Off-policy

这是后面 PPO 和 SAC 的分水岭。

- `on-policy`：主要使用当前策略刚采到的数据更新自己。
- `off-policy`：允许复用旧数据，通常放进 replay buffer 反复训练。

可以先用一句话记住：

- PPO 更像“边跑边记新笔记，然后按这批新笔记修正自己”。
- SAC 更像“把经验都存进仓库里，反复抽样学习”。

对机器人而言：

- on-policy 更新更直接，但样本效率通常低。
- off-policy 样本效率更高，尤其适合昂贵的连续控制采样。
- 如果你的观测、奖励或策略版本变化太大，旧数据也可能变得难用。

## 一个机器人任务的心智模型

把 RL 任务建模成下面这张思维表，比背公式更有用：

| 元素 | 你要回答的问题 | 机器人示例 |
| --- | --- | --- |
| Observation | 策略到底看到了什么？ | 关节角、夹爪状态、目标相对位姿、图像 |
| Hidden state | 哪些量真实存在但观测不到？ | 摩擦、遮挡后的物体姿态、外力扰动 |
| Action | 策略能控制什么？ | 关节速度、末端增量、夹爪开合 |
| Reward | 什么行为被鼓励？ | 成功抓取、接近目标、平滑运动 |
| Success | 怎样才算任务完成？ | 物体离台面超过阈值并保持稳定 |
| Failure | 怎样算失败？ | 碰撞、越界、掉落、超时 |
| Horizon | 一次尝试最多多长？ | 100 或 200 控制步 |
| Data flow | 数据如何喂给算法？ | rollout buffer 或 replay buffer |

如果这张表写不出来，说明任务还没有被定义清楚，不适合直接开训。

## 代码实操：用 Gymnasium 体验 RL 闭环

下面的代码不使用任何 RL 库，只用 Gymnasium 手动执行最朴素的交互循环。你可以直接在 Python REPL 中运行，理解"agent-environment"的信息流。

```python
import gymnasium as gym
import numpy as np

# --- 1. 创建环境，查看空间定义 ---
env = gym.make("CartPole-v1")
print("observation 空间:", env.observation_space)  # Box(4,) — 四个连续值
print("action 空间:     ", env.action_space)        # Discrete(2) — 左/右

# --- 2. 随机策略跑一个 episode ---
obs, info = env.reset(seed=0)   # obs 是 shape=(4,) 的 numpy 数组
total_return = 0.0
for t in range(500):
    action = env.action_space.sample()  # 随机选动作
    next_obs, reward, terminated, truncated, info = env.step(action)
    total_return += reward
    # 注意区分 terminated（成功/失败）和 truncated（超时）
    if terminated or truncated:
        break
    obs = next_obs

print(f"episode 结束于 step {t}, return = {total_return}")
# 随机策略在 CartPole 上大约得 20~30 分
```

上面短短几行就包含了所有 MDP 要素：

- `obs`：observation（杆角度、角速度、车位置、车速度四维向量）。
- `action`：离散动作（0=左推，1=右推）。
- `reward`：每活一步 +1。
- `terminated/truncated`：episode 结束条件。
- `total_return`：一局累计回报。

### MDP vs POMDP 的直觉

```python
# CartPole 给出完整状态 — 接近 MDP
obs, _ = env.reset()
print("完整 obs:", obs)
# → [车位置, 车速度, 杆角度, 杆角速度]   四个量就够做决策

# 假设你只能看到杆角度（遮挡了其他三个量）—— POMDP
partial_obs = obs[2:3]  # 只有杆角度
print("部分 obs:", partial_obs)
# 同一个杆角度，可能对应完全不同的车速度和角速度
# → 策略只看这个值，很难做出正确决策
```

在真实机器人上，"只给了部分信息"几乎是常态：相机有盲区，力觉有噪声，物体质量和摩擦是隐变量。

## 伪代码：从交互到学习

下面的伪代码故意不区分 PPO / SAC，只保留 RL 闭环：

```text
initialize policy
for episode in 1..N:
    obs = env.reset()
    for t in 1..T:
        action = policy(obs)
        next_obs, reward, done, info = env.step(action)
        store(obs, action, reward, next_obs, done)
        obs = next_obs
        if ready_to_learn():
            update_policy_from_data()
        if done:
            break
```

这个框架里最重要的不是伪代码本身，而是四个问题：

- `policy(obs)` 的输入到底是什么？
- `reward` 是否真的对应任务目标？
- `store(...)` 是只存新数据，还是长期复用旧数据？
- `done` 是成功、失败还是时间截断？

## 和本仓库实验的对应关系

本节概念可以直接落到 `labs/08-rl/` 里的三个轻量脚本上：

- `labs/08-rl/ppo_cartpole.py`
  - observation：杆角度、角速度等环境向量。
  - action：离散左右推。
  - 算法数据流：on-policy。
  - 结果可对照 `runs/08-rl/ppo_cartpole_metrics.json` 与 `runs/08-rl/random_baseline.txt`。
- `labs/08-rl/sac_pendulum.py`
  - action：连续扭矩。
  - 更适合理解 Q 函数和 off-policy 经验复用。
  - 结果可对照 `runs/08-rl/sac_pendulum_metrics.json`。
- `labs/08-rl/reward_shaping_demo.py`
  - 不强调深度网络，而是强调“同一个环境，不同 reward 定义会导致不同学习速度”。
  - 结果可对照 `runs/08-rl/reward_shaping.json` 与 `runs/08-rl/reward_shaping.txt`。

如果你准备做自己的机器人实验，建议先像这些脚本一样把任务定义压缩到一个足够小、可复现、可解释的闭环。

## 常见坑

- 把 observation 当成真实 state。实际漏掉关键变量时，训练不稳定不是算法自动能补救的。
- 把 reward 当成目标本身。reward 只是你写出来的代理目标，不一定等于真实任务成功。
- 只看平均回报，不看成功率、失败模式和 episode 长度。
- 没写清 done 的原因。成功终止、失败终止、时间截断混在一起会让日志难解释。
- 任务还没建模清楚就急着换更复杂算法。
- 在机器人场景里忽视动作限幅、控制频率和安全边界，导致“能学”但不可执行。

## 练习任务

选一个最简单的机器人技能，写一张任务建模卡。建议题目：

- 二维平面导航到目标点。
- 单臂把末端移动到指定位置。
- 夹爪靠近并抓住桌面上的单个方块。

至少写清：

- observation 有哪些字段。
- 哪些重要量没有被直接观测到。
- action 是离散还是连续。
- success / failure / timeout 条件。
- reward 由哪些项组成。
- 如果要在 PPO 和 SAC 之间选一个 baseline，你会先用哪一个，为什么。

## 自测问题

- 为什么机器人任务通常更像 POMDP，而不是理想 MDP？
- `V(s)`、`Q(s, a)`、`A(s, a)` 各自回答的是什么问题？
- 为什么“reward 增长”不一定等于“任务真的做对了”？
- 对于连续控制任务，为什么很多人会先想到 SAC 而不是 PPO？
- 如果一个任务只能拿到图像单帧，你会如何弥补部分可观测问题？
- 你能否把 `labs/08-rl/ppo_cartpole.py` 和 `labs/08-rl/sac_pendulum.py` 分别归类到 on-policy / off-policy，并解释原因？
