# DreamerV3 论文精读讲义：通过世界模型掌握多样控制任务

论文：Danijar Hafner, Jurgis Pasukonis, Jimmy Ba, Timothy Lillicrap. **Mastering diverse control tasks through world models**. Nature, 2025. DOI: `10.1038/s41586-025-08744-2`

本文讲解对象：刚入门人工智能和强化学习的读者。目标不是只复述摘要，而是让你理解：这篇论文为什么重要，DreamerV3 到底做了什么，公式背后在解决什么训练难题，实验结果证明了什么，以及哪些地方读论文时容易误解。

---

## 0. 一句话先把论文抓住

DreamerV3 是一个通用强化学习算法。它先学习一个“世界模型”，也就是环境在智能体脑中的可微分模拟器；再让 actor 和 critic 在这个想象出来的 latent world 中练习决策。论文的核心亮点不是“又提出一个在某个 benchmark 上更高分的模型”，而是：**同一套超参数、同一套算法，跨 8 个领域、150 多个任务都表现很强，并且在 Minecraft 钻石任务中不用人类数据、不用课程学习，从零开始拿到钻石**。

一个类比：  
普通强化学习像一个学生只能在真实世界里反复试错，摔一次才知道痛。Dreamer 像学生先在脑中形成“如果我这么做，世界会怎么变”的内在模拟器，然后在脑中大量排练，再把排练得到的策略拿到真实环境里试。关键问题是：这个“脑内模拟器”必须足够稳、足够抽象、足够能跨任务工作。DreamerV3 的大量技术细节都在服务这件事。

---

## 1. 研究背景和动机

### 1.1 强化学习在解决什么问题

强化学习（reinforcement learning, RL）研究的是：一个智能体如何通过和环境交互来学习行为。最常见的形式可以写成马尔可夫决策过程（MDP）：

$$
\mathcal{M} = (\mathcal{S}, \mathcal{A}, P, r, \gamma)
$$

其中：

- $\mathcal{S}$ 是状态空间，比如机器人关节角度、游戏画面背后的真实状态。
- $\mathcal{A}$ 是动作空间，比如“向左走”“转动摄像头”“给电机施加力矩”。
- $P(s_{t+1}\mid s_t,a_t)$ 是环境动力学，也就是执行动作后世界如何变化。
- $r(s_t,a_t)$ 是奖励，表示当前行为好不好。
- $\gamma \in [0,1)$ 是折扣因子，用来平衡近期奖励和长期奖励。

智能体的策略记为 $\pi(a_t\mid s_t)$，目标是最大化长期回报：

$$
R_t = \sum_{\tau=0}^{\infty}\gamma^\tau r_{t+\tau}.
$$

新人最容易踩的坑是：强化学习不是简单的监督学习。监督学习有现成答案，比如图片分类的标签；强化学习没有逐步正确答案，它只有交互后的奖励，而且奖励可能非常稀疏、非常延迟。Minecraft 里拿钻石就是典型例子：一开始乱走很久可能什么奖励都没有，只有先砍树、做木板、做木棍、做工作台、做镐、挖矿、炼铁、再挖钻石，才逐步得到稀疏里程碑奖励。

### 1.2 为什么“通用 RL 算法”很难

论文开头强调的核心痛点是：现有 RL 算法经常能在某类任务上工作，但换一个领域就需要大量人工调参。

例如：

- PPO 常被当作稳健 baseline，但在复杂视觉、稀疏奖励、长时间规划任务上可能样本效率较低。
- Rainbow、IQN 等方法强于 Atari 这类离散动作游戏。
- DrQ-v2、TD-MPC2 等方法强于视觉连续控制。
- MuZero 在离散动作规划上很强，但实现复杂，计算开销较高。
- Minecraft 过去的强方法往往借助人类数据、课程学习、脚本化动作或大量工程技巧。

这些方法的问题不是“没用”，而是“不够通用”。一个机器人任务、一个 Atari 游戏、一个 3D 导航任务、一个 Minecraft 生存任务，它们在输入、动作、奖励、时间尺度和随机性上都差很多。一个算法如果每换一个领域都要重新调学习率、奖励归一化、探索强度、模型大小、损失权重，就很难成为真正实用的通用智能体算法。

这篇论文的动机可以概括为：

1. **降低 RL 的使用门槛**：让用户不用成为调参专家，也能把 RL 应用到新任务。
2. **提高跨域稳健性**：视觉输入、向量输入、离散动作、连续动作、稀疏奖励、密集奖励都能覆盖。
3. **利用世界模型提高样本效率**：真实环境交互昂贵时，让智能体在模型里“想象”训练。
4. **证明从零开始探索复杂开放世界的可能性**：Minecraft 钻石任务是一个长视野、稀疏奖励、视觉、开放世界综合挑战。

### 1.3 model-free 与 model-based 的区别

理解 Dreamer 前，先区分两类 RL。

**Model-free RL** 不显式学习环境如何变化。它直接学策略 $\pi(a\mid s)$ 或价值函数 $V(s)$、$Q(s,a)$。可以把它理解成“刷题记经验”：见过某状态，试过某动作，得到过奖励，就慢慢调整策略。

优点：

- 思路直接。
- 不需要学习复杂环境模型。
- 在某些标准任务上非常强。

缺点：

- 通常需要大量真实交互。
- 对奖励尺度、探索、超参数敏感。
- 很难从纯观察中学习任务无关的世界知识。

**Model-based RL** 会学习一个模型 $\hat{P}$ 和 $\hat{r}$，预测“如果我在状态 $s$ 做动作 $a$，接下来会看到什么、得到什么奖励”。这像是在脑中建一个沙盘：

$$
\hat{s}_{t+1}, \hat{r}_t \sim \hat{P}_\phi(\cdot\mid s_t,a_t).
$$

优点：

- 可以在模型里想象未来，减少真实交互。
- 表示学习可以利用大量无标签观察。
- 有潜力形成跨任务的世界知识。

缺点：

- 模型预测误差会累积。
- 高维视觉世界很难建模。
- 如果模型学到无关细节，决策会变慢或不稳；如果太抽象，又可能丢掉任务关键信息。

DreamerV3 的核心立场是：世界模型是通用智能体的重要路线，但要让它在很多领域都稳定工作，必须解决训练尺度、损失平衡、表示可预测性、探索强度等细节问题。

### 1.4 什么是“世界模型”

世界模型不是把整个真实世界像物理引擎一样精确复刻，而是学一个对控制有用的内在表示。你可以把它想成三层：

1. **感知压缩**：把原始图像 $x_t$ 编码成 latent state $z_t$。
2. **动态预测**：根据过去 latent 和动作预测未来 latent。
3. **任务相关预测**：从 latent 中预测奖励、终止信号、价值等。

原始像素很大、很嘈杂，直接在像素中规划很难。Dreamer 的做法是把世界压缩到 latent space，在 latent space 中做想象 rollout：

```text
真实交互:     x_t -> encoder -> z_t
内部记忆:     h_t = recurrent_model(h_{t-1}, z_{t-1}, a_{t-1})
想象未来:     (h_t, z_t) --actor--> a_t --world model--> z_{t+1}, r_t
策略学习:     critic 评价想象轨迹，actor 学会选择更好的动作
```

### 1.5 为什么 Minecraft 钻石任务重要

Minecraft 钻石任务难在多个方面叠加：

- **视觉输入**：智能体看到的是第一人称 64×64×3 图像。
- **开放世界**：每局都是程序生成的 3D 世界。
- **长时间视野**：拿钻石不是几步能完成的，论文中提到熟练人类大约需要 20 分钟。
- **稀疏奖励**：只有达到里程碑物品才给奖励。
- **组合式技能链**：砍树、合成、放置工作台、做镐、挖石头、炼铁、挖钻石等动作必须串起来。
- **探索困难**：一开始随机动作几乎碰不到关键里程碑。

过去有方法用人类演示、视频预训练、课程学习、脚本动作等方式降低难度。DreamerV3 的论文强调：它是在默认超参数下，从零交互学习，不用人类数据和课程学习，最终发现钻石。

---

## 2. 论文的核心贡献

这篇论文的贡献可以分成五层。

### 2.1 一个跨域固定超参数的 DreamerV3 算法

论文提出 Dreamer 第三代，也可称为 DreamerV3。它相对 DreamerV1/V2 的重要变化包括：

- 观测和预测中的 `symlog` 变换。
- KL balancing 加 free bits。
- categorical distribution 的 1% uniform mixture，也叫 unimix。
- reward head 和 critic 使用 symexp two-hot loss。
- actor 使用 percentile return normalization。
- 网络使用 block GRU、RMSNorm、SiLU。
- 优化器使用 adaptive gradient clipping 和 LaProp。
- replay buffer 更大，加入 online queue，并缓存 latent state。

这些设计看似零散，但共同目标是：**同一套设置跨任务稳定训练**。

### 2.2 用 learned world model 做 actor-critic 想象训练

Dreamer 不在真实环境中每走一步就做复杂树搜索，而是：

1. 在真实环境中收集经验。
2. 用经验训练世界模型。
3. 从 replay 中的 latent state 出发，在世界模型里 rollout 未来轨迹。
4. critic 估计想象轨迹的 return。
5. actor 学会选择更高 return 的动作。

也就是说，它把昂贵的真实试错，部分转移到便宜的 latent imagination。

### 2.3 在 8 个领域、150+ 任务上超过或匹配专家算法

论文的 benchmark 覆盖：

- Minecraft
- DMLab
- ProcGen
- Atari
- Atari100K
- BSuite
- DeepMind Control Vision
- DeepMind Control Proprio

这些任务组合了视觉/非视觉、离散/连续动作、2D/3D、密集/稀疏奖励、短视野/长视野、确定/随机、单任务/多配置等挑战。

### 2.4 Minecraft 钻石任务从零成功

在 Minecraft Diamond 任务上，Dreamer 是论文比较中唯一发现钻石的算法。表格中 Dreamer return 为 9.1，PPO 为 5.1，IMPALA 为 7.1，Rainbow 为 6.3。更重要的是，论文图 5 说明：所有 Dreamer 训练 run 都在 1 亿环境步内发现钻石，而比较的强 baseline 没有发现钻石。

### 2.5 证明模型大小和 replay ratio 可以预测性扩展性能

论文训练了从 12M 到 400M 参数的模型，并测试不同 replay ratio。结果显示：

- 模型越大，性能越高。
- 模型越大，达到成功行为需要的环境交互越少。
- replay ratio 越高，性能也更好。

这对工程实践很重要：如果你有更多算力，可以比较可预测地换来更强性能和更高样本效率。

---

## 3. DreamerV3 方法总览

DreamerV3 有三个主要神经网络模块：

| 模块 | 作用 | 类比 |
|---|---|---|
| world model | 预测动作会导致什么未来 | 脑内模拟器 |
| critic | 判断某个未来有多好 | 评委或老师 |
| actor | 选择动作 | 做决策的学生 |

训练流程可以写成：

```text
1. 用当前 actor 和真实环境交互，收集 (x_t, a_t, r_t, c_t)
2. 把经验存入 replay buffer
3. 从 replay buffer 采样序列
4. 训练 world model：重建观测，预测 reward/continue，学习 latent dynamics
5. 从 replay latent state 出发，在 world model 中 imagination rollout
6. 用 imagined rewards 和 critic bootstrap 计算 lambda returns
7. 更新 critic：拟合 return 分布
8. 更新 actor：选择能带来更高 normalized return 的动作，并保持适度探索
9. 重复
```

伪代码如下：

```python
for step in training:
    # collect real experience
    action = actor.sample(model_state)
    obs, reward, done = env.step(action)
    replay.add(obs, action, reward, not done)

    # train from replayed sequences
    batch = replay.sample_sequences(batch_size=16, length=64)
    model_loss = train_world_model(batch)

    # imagine in latent space
    start_states = encode_replayed_states(batch)
    imagined = rollout_world_model(start_states, actor, horizon=15)

    returns = lambda_returns(imagined.rewards, imagined.continues, critic)
    critic_loss = train_critic(imagined.states, returns)
    actor_loss = train_actor(imagined.states, imagined.actions, returns, critic)
```

注意：这段代码只是帮助理解。真实 DreamerV3 的实现还有分布式 replay、latent state 缓存、具体网络结构、优化器和多种稳健化细节。

---

## 4. 世界模型：Dreamer 的“脑内模拟器”

### 4.1 输入、记忆和 latent state

论文把世界模型实现为 recurrent state-space model（RSSM）。它有两个核心状态：

- $h_t$：确定性 recurrent state，可以理解为 RNN/GRU 的记忆。
- $z_t$：随机 latent representation，用 categorical distributions 表示。

二者拼在一起构成 model state：

$$
s_t = \{h_t, z_t\}.
$$

为什么需要 $h_t$？因为视觉观测通常不是完整状态。比如 Minecraft 中一帧图像不一定告诉你刚才从哪里来、背包里发生了什么、目标进度如何。RNN 的 $h_t$ 用来整合历史。

为什么还需要 $z_t$？因为 $h_t$ 是根据过去递推的确定性记忆，而 $z_t$ 从当前观测编码得到，可以注入当前时刻的新感知信息，并允许模型表达不确定性。

### 4.2 世界模型的方程

论文中的模型方程可以整理为：

$$
h_t = f_\phi(h_{t-1}, z_{t-1}, a_{t-1})
$$

$$
z_t \sim q_\phi(z_t \mid h_t, x_t)
$$

$$
\hat{z}_t \sim p_\phi(\hat{z}_t \mid h_t)
$$

$$
\hat{r}_t \sim p_\phi(\hat{r}_t \mid h_t, z_t)
$$

$$
\hat{c}_t \sim p_\phi(\hat{c}_t \mid h_t, z_t)
$$

$$
\hat{x}_t \sim p_\phi(\hat{x}_t \mid h_t, z_t).
$$

逐个解释：

- sequence model $f_\phi$：看过去的记忆、上一步 latent、上一步动作，更新当前记忆。
- encoder $q_\phi$：看当前观测 $x_t$ 和记忆 $h_t$，得到 posterior latent $z_t$。
- dynamics predictor $p_\phi$：不看当前图像，只根据 $h_t$ 预测 latent。这是想象未来时要用的部分。
- reward predictor：预测奖励。
- continue predictor：预测 episode 是否继续，$c_t \in \{0,1\}$。
- decoder：从 latent state 重建输入，逼迫 latent 保留感知信息。

一个关键点：真实训练时有 $x_t$，所以可以用 encoder 得到 $z_t$；想象未来时没有未来图像，只能用 dynamics predictor 采样 $\hat{z}_{t+1}$。因此世界模型必须学会让 latent 既含信息，又可预测。

### 4.3 世界模型的三个损失

世界模型总损失：

$$
L(\phi) =
\mathbb{E}_{q_\phi}
\left[
\sum_{t=1}^{T}
\left(
\beta_{\mathrm{pred}}L_{\mathrm{pred}}
+
\beta_{\mathrm{dyn}}L_{\mathrm{dyn}}
+
\beta_{\mathrm{rep}}L_{\mathrm{rep}}
\right)
\right].
$$

论文默认：

$$
\beta_{\mathrm{pred}}=1,\quad
\beta_{\mathrm{dyn}}=1,\quad
\beta_{\mathrm{rep}}=0.1.
$$

#### 4.3.1 Prediction loss

Prediction loss 负责让模型重建观测、预测奖励和继续信号：

$$
L_{\mathrm{pred}}
=
-\log p_\phi(x_t\mid z_t,h_t)
-\log p_\phi(r_t\mid z_t,h_t)
-\log p_\phi(c_t\mid z_t,h_t).
$$

直观理解：如果 latent state 真的理解了当前世界，它应该能回答：

- 我现在看见的画面大概是什么？
- 我会得到什么奖励？
- episode 是否还会继续？

#### 4.3.2 Dynamics loss

Dynamics loss 让 prior dynamics $p_\phi(z_t\mid h_t)$ 追上 encoder posterior $q_\phi(z_t\mid h_t,x_t)$：

$$
L_{\mathrm{dyn}}
=
\max\left(
1,\;
\mathrm{KL}
\left[
\mathrm{sg}(q_\phi(z_t\mid h_t,x_t))
\;\|\;
p_\phi(z_t\mid h_t)
\right]
\right).
$$

这里 $\mathrm{sg}(\cdot)$ 是 stop-gradient，意思是把某一边当常量，不让梯度传过去。这个损失主要训练 dynamics predictor：你要学会不用当前图像，也能预测 encoder 从当前图像里提取出来的 latent。

#### 4.3.3 Representation loss

Representation loss 反过来让 encoder 产生更容易被 dynamics 预测的 latent：

$$
L_{\mathrm{rep}}
=
\max\left(
1,\;
\mathrm{KL}
\left[
q_\phi(z_t\mid h_t,x_t)
\;\|\;
\mathrm{sg}(p_\phi(z_t\mid h_t))
\right]
\right).
$$

直观理解：如果 encoder 把每个像素噪声都塞进 $z_t$，dynamics 很难预测；如果 $z_t$ 太简单，又会丢掉控制所需信息。Representation loss 让表示更可预测，prediction loss 又防止表示变成空壳。

### 4.4 free bits：为什么 KL 要 clip 到 1 nat

论文使用 free bits，把 KL 损失下限裁到 1 nat：

$$
\max(1, \mathrm{KL}[\cdot]).
$$

这是什么意思？当 KL 已经足够小，小于 1 nat 时，就不再继续强迫它更小。这样可以避免模型过度追求“latent 好预测”，最后把 latent 压得没有信息。

类比：老师要求学生写摘要。摘要太长不行，因为无法预测和泛化；但摘要短到只剩“这是一件事”也不行，因为没信息。free bits 就像告诉模型：“摘要已经够简洁了，不要再删了，接下来多关注能不能重建和预测有用内容。”

### 4.5 1% unimix：避免 categorical 分布过于自信

DreamerV3 的 encoder、dynamics predictor 和 actor 的 categorical distributions 不是直接使用神经网络 softmax，而是混合：

$$
p_{\mathrm{mix}} = 0.99\,p_{\mathrm{net}} + 0.01\,p_{\mathrm{uniform}}.
$$

这样每个类别都有至少一点概率。它的作用是：

- 避免概率变成 0，导致 $\log 0$ 或 KL 爆炸。
- 防止模型过早变得确定。
- 提高跨任务训练稳定性。

这看似是小技巧，但在统一超参数跨领域训练时非常重要。

---

## 5. Critic：如何评价想象出来的未来

### 5.1 critic 预测 return 分布

Dreamer 的 critic 不是只输出一个标量值，而是预测 return 的分布：

$$
v_\psi(R_t\mid s_t).
$$

标量值读出为该分布的期望：

$$
v_t = \mathbb{E}[v_\psi(\cdot\mid s_t)].
$$

为什么要预测分布？因为不同环境的 return 尺度可能差几个数量级，且 return 可能多峰。例如一个随机地图中，有些 episode 天然更容易拿高分，有些更难。分布式 critic 比单个高斯标量更稳。

### 5.2 lambda return

Dreamer 在 imagined trajectory 中展开有限步，默认 imagination horizon 为 15。为了考虑更长远的奖励，它用 bootstrapped $\lambda$ return：

$$
R_t^\lambda
=
r_t
+
\gamma c_t
\left(
(1-\lambda)v_t + \lambda R_{t+1}^\lambda
\right),
$$

$$
R_T^\lambda = v_T.
$$

默认：

$$
\gamma = 0.997,\quad \lambda = 0.95.
$$

$c_t$ 是 continue flag。如果 episode 结束，$c_t=0$，后面的价值就不再计入。

直观理解：

- $\lambda=0$：完全依赖一步 reward 加 critic bootstrap，偏差大但方差小。
- $\lambda=1$：尽量用 rollout 真实/预测奖励，偏差小但方差大。
- $\lambda=0.95$：折中。

critic 的损失是最大似然：

$$
L(\psi) =
-\sum_{t=1}^{T}
\ln p_\psi(R_t^\lambda\mid s_t).
$$

### 5.3 critic replay loss

论文还把 critic loss 用在 replay buffer 中的真实轨迹上，权重较低：

$$
\beta_{\mathrm{val}} = 1,\quad
\beta_{\mathrm{repval}} = 0.3.
$$

为什么？在奖励难预测的环境里，仅靠 imagined reward 训练 critic 可能不够稳定。对 replay 轨迹加一个较弱的 value loss，相当于用真实经验校正 critic。

### 5.4 critic EMA regularizer 和零初始化

critic 的目标依赖自己预测的 value，这容易不稳定。论文用 critic 参数的指数滑动平均（EMA）作为正则目标，类似 target network：

- critic EMA regularizer scale 为 1。
- critic EMA decay 为 0.98。

另外，reward predictor 和 critic 的输出权重初始化为 0。原因是随机初始化时，模型可能一开始“幻想”出很大的奖励或价值，导致 early learning 延迟。零初始化让模型一开始更保守。

---

## 6. Actor：如何在想象世界中学习行动

### 6.1 actor 的目标

actor 输出策略：

$$
a_t \sim \pi_\theta(a_t\mid s_t).
$$

Dreamer 与一些 model-based planning 方法不同：它和真实环境交互时直接从 actor sample 动作，不做在线 lookahead tree search。它的规划主要发生在训练时的 latent imagination 中。

### 6.2 actor loss

论文使用 REINFORCE estimator，离散和连续动作都能用。可以把 actor 的优化理解为最大化 normalized advantage 加探索熵：

$$
L(\theta)
=
-
\sum_{t=1}^{T}
\mathrm{sg}
\left(
\frac{R_t^\lambda - v_t}{\max(1,S)}
\right)
\log \pi_\theta(a_t\mid s_t)
\text{entropy regularization}.
$$

其中 $R_t^\lambda - v_t$ 类似 advantage：如果某动作导致的 return 比 critic 预期更好，就增加它的概率；更差就降低概率。

### 6.3 为什么要 return normalization

不同环境奖励尺度差异巨大。一个任务每步奖励可能是 0.001，另一个任务一次成功可能奖励 100。若 entropy regularizer 固定，奖励尺度变化会改变探索和利用的平衡。

DreamerV3 用 batch 中 return 的 95 分位和 5 分位估计尺度：

$$
S =
\mathrm{EMA}
\left(
\mathrm{Per}(R_t^\lambda,95)
-
\mathrm{Per}(R_t^\lambda,5),
0.99
\right).
$$

actor loss 中除以 $\max(1,S)$。这里的 `max(1,S)` 很关键：

- 如果 return 尺度很大，就缩小梯度，避免爆炸。
- 如果 return 尺度很小，尤其稀疏奖励早期，就不把噪声强行放大。

论文对比了 advantage normalization、reward/return 标准差归一化、固定熵约束等方法，发现这种 percentile return normalization 更适合跨域固定超参数。

---

## 7. 稳健预测：symlog 和 symexp two-hot

### 7.1 symlog：对正负大数都温柔压缩

普通平方误差遇到大目标值时梯度可能很大，训练容易不稳。直接取 $\log$ 又不能处理负数。Dreamer 使用 bi-symmetric log：

$$
\mathrm{symlog}(x)
=
\mathrm{sign}(x)\log(|x|+1),
$$

其逆变换：

$$
\mathrm{symexp}(x)
=
\mathrm{sign}(x)(\exp(|x|)-1).
$$

symlog 的性质：

- $x$ 接近 0 时，近似恒等映射，不影响小数值学习。
- $|x|$ 很大时，用 log 压缩数量级，避免大梯度。
- 正负数都能处理。

PyTorch 示例：

```python
import torch

def symlog(x):
    return torch.sign(x) * torch.log1p(torch.abs(x))

def symexp(x):
    return torch.sign(x) * (torch.exp(torch.abs(x)) - 1)
```

DreamerV3 用 symlog 处理 vector observations 的 encoder 输入和 decoder target。

### 7.2 symexp two-hot：把回归问题变成软分类

对于 reward 和 value，DreamerV3 不直接用普通回归，而是输出一个 softmax 分布，bin 位置采用指数间隔：

$$
B = \mathrm{symexp}([-20,\ldots,+20]).
$$

预测值读作：

$$
\hat{y}
=
\mathrm{softmax}(f(x))^\top B.
$$

目标值 $y$ 用 two-hot 编码：找到最接近它的两个 bin，把权重按距离分给这两个 bin。损失是 soft target cross entropy：

$$
L(\theta)
=
-
\mathrm{twohot}(y)^\top
\log \mathrm{softmax}(f(x,\theta)).
$$

这有什么好处？

- 分类交叉熵的梯度主要由概率误差决定，不直接随目标数值大小爆炸。
- two-hot 保留连续值信息，不像 one-hot 那样粗糙。
- 指数间隔 bin 能覆盖非常大的正负 return 范围。

简化代码：

```python
def two_hot(values, bins):
    # values: [B], bins: [K], sorted ascending
    values = values.clamp(bins[0], bins[-1])
    idx = torch.searchsorted(bins, values)
    idx = idx.clamp(1, len(bins) - 1)
    lo = idx - 1
    hi = idx
    left = bins[lo]
    right = bins[hi]
    weight_hi = (values - left) / (right - left)
    weight_lo = 1.0 - weight_hi
    target = torch.zeros(values.shape[0], len(bins), device=values.device)
    target.scatter_(1, lo[:, None], weight_lo[:, None])
    target.scatter_(1, hi[:, None], weight_hi[:, None])
    return target
```

注意：真实实现要更小心处理边界、数值稳定和正负 bin 求和顺序。

---

## 8. 具体实现细节

### 8.1 网络结构

论文方法部分给出的实现要点：

- 图像输入：stride-2 convolution 编码到 $6\times6$ 或 $4\times4$，再 flatten。
- 图像解码：transpose stride-2 convolution，输出端 sigmoid。
- 向量输入：先 symlog，再用三层 MLP 编码和解码。
- actor 和 critic：三层 MLP。
- reward predictor 和 continue predictor：一层 MLP。
- sequence model：GRU，但 recurrent weight 是 8 个 block 的 block-diagonal 结构。
- 激活与归一化：RMSNorm + SiLU。

block GRU 的意义：普通全连接 recurrent matrix 如果 hidden 很大，参数和计算会按平方增长。block-diagonal 把大矩阵拆成多个块，允许更多 memory units，同时控制计算量。

### 8.2 默认超参数

论文扩展表 5 的关键超参数：

| 类别 | 名称 | 值 |
|---|---:|---:|
| General | replay capacity | $5\times10^6$ |
| General | batch size | 16 |
| General | batch length | 64 |
| General | activation | RMSNorm + SiLU |
| General | learning rate | $4\times10^{-5}$ |
| General | gradient clipping | AGC(0.3) |
| General | optimizer | LaProp, $\epsilon=10^{-20}$ |
| World Model | reconstruction loss scale $\beta_{\mathrm{pred}}$ | 1 |
| World Model | dynamics loss scale $\beta_{\mathrm{dyn}}$ | 1 |
| World Model | representation loss scale $\beta_{\mathrm{rep}}$ | 0.1 |
| World Model | latent unimix | 1% |
| World Model | free nats | 1 |
| Actor Critic | imagination horizon $H$ | 15 |
| Actor Critic | discount horizon $1/(1-\gamma)$ | 333 |
| Actor Critic | return lambda $\lambda$ | 0.95 |
| Actor Critic | critic replay loss scale $\beta_{\mathrm{repval}}$ | 0.3 |
| Actor Critic | actor entropy regularizer $\eta$ | $3\times10^{-4}$ |
| Actor Critic | actor unimix | 1% |
| Actor Critic | RetNorm scale | $\mathrm{Per}(R,95)-\mathrm{Per}(R,5)$ |
| Actor Critic | RetNorm limit | 1 |
| Actor Critic | RetNorm decay | 0.99 |

论文明确说：同一设置用于所有 benchmark，包括视觉/非视觉、连续/离散动作、2D/3D。没有使用 annealing、prioritized replay、weight decay 或 dropout。

### 8.3 模型尺寸

论文使用多个模型尺寸测试 scaling：

| 参数量 | hidden size $d$ | recurrent units $8d$ | base conv channels $d/16$ | codes per latent $d/16$ |
|---:|---:|---:|---:|---:|
| 1M | 64 | 512 | 16 | 4 |
| 12M | 256 | 2048 | 16 | 16 |
| 25M | 384 | 3072 | 24 | 24 |
| 50M | 512 | 4096 | 32 | 32 |
| 100M | 768 | 6144 | 48 | 48 |
| 200M | 1024 | 8192 | 64 | 64 |
| 400M | 1536 | 12288 | 96 | 96 |

默认大多数任务使用 200M 模型。DMC Proprio 使用 1M 模型，因为低维 proprioceptive 输入不需要很大的视觉世界模型。

### 8.4 replay ratio

Replay ratio 表示每收集一个环境步，对 replay 中多少时间步进行训练。论文解释：梯度步数与环境步数的比例还要除以 batch 的时间步数和 action repeat。

例子：Atari 上 replay ratio = 32，action repeat = 4，batch shape = $16\times64$，对应约每 128 个环境步做 1 个梯度步，200M 环境步约 1.5M 个梯度步。

这个量体现的是算力与数据效率的交换：replay ratio 越高，同一批真实经验被训练利用得越多，通常数据效率更高，但计算成本更高。

### 8.5 Minecraft 环境实现

论文中的 Minecraft Diamond 基于 MineRL v0.4.4，Minecraft 版本 1.11.2。

观测包括：

- 64×64×3 第一人称图像。
- 400 多个物品的 inventory count vector。
- episode 开始以来最大 inventory count vector，用来告诉智能体已达成哪些里程碑。
- 当前装备物品 one-hot。
- health、hunger、breath 标量。

奖励：

- 12 个里程碑，每个首次获得给 +1：log、plank、stick、crafting table、wooden pickaxe、cobblestone、stone pickaxe、iron ore、furnace、iron ingot、iron pickaxe、diamond。
- 失去半颗/一颗心等生命值变化时有小奖励调整：lost heart -0.01，restored heart +0.01。论文没有重点研究这个 shaping 是否必要。

episode：

- 玩家死亡或 36,000 步结束。
- 20 Hz 控制频率，对应 30 分钟。

动作空间被整理成 25 个离散动作：

| id | action |
|---:|---|
| 0 | noop |
| 1 | attack |
| 2 | turn_up |
| 3 | turn_down |
| 4 | turn_left |
| 5 | turn_right |
| 6 | walk_forward |
| 7 | walk_back |
| 8 | walk_left |
| 9 | walk_right |
| 10 | jump_forward |
| 11 | place_dirt |
| 12 | craft_planks |
| 13 | craft_stick |
| 14 | craft_crafting_table |
| 15 | place_crafting_table |
| 16 | craft_wooden_pickaxe |
| 17 | craft_stone_pickaxe |
| 18 | craft_iron_pickaxe |
| 19 | equip_stone_pickaxe |
| 20 | equip_wooden_pickaxe |
| 21 | equip_iron_pickaxe |
| 22 | craft_furnace |
| 23 | place_furnace |
| 24 | smelt_iron_ingot |

论文还加速了 block breaking。原因很实际：Minecraft 里打破方块需要连续按住攻击键很多步。若随机策略有 25 个动作，要连续几百步都选中 attack，概率约为 $1/25^{400}\approx 10^{-560}$，几乎不可能靠随机探索发现。作者认为“学会长按鼠标几百步”不是 Minecraft 智能挑战的核心，所以沿用前人做法加速破坏方块。

这个细节很重要：Dreamer 的 Minecraft 成就非常强，但不是原版人类键鼠完整动作空间下从零学习；它使用 MineRL competition 风格的抽象合成动作和加速 block breaking。

---

## 9. 实验设置

### 9.1 总体设置

论文在 8 个领域、150+ 任务上评估 Dreamer。所有 Dreamer agent 和 PPO agent 都在单张 Nvidia A100 GPU 上训练。Dreamer 默认使用 200M 参数模型，replay ratio 根据 benchmark 预算设置。

随机种子：

- Dreamer 和 PPO：每个 benchmark 通常 5 个 seed。
- BSuite：按 benchmark 要求 10 个 seed。
- Minecraft：10 个 seed，用来可靠报告多少 run 拿到钻石。

曲线展示 mean，阴影表示一个标准差。

### 9.2 Benchmark overview

| Benchmark | Tasks | Env steps | Action repeat | Env instances | Replay ratio | GPU days | Model size |
|---|---:|---:|---:|---:|---:|---:|---:|
| Minecraft | 1 | 100M | 1 | 64 | 32 | 8.9 | 200M |
| DMLab | 30 | 100M | 4 | 16 | 32 | 2.9 | 200M |
| ProcGen | 16 | 50M | 1 | 16 | 32 | 8.3 | 200M |
| Atari | 57 | 200M | 4 | 16 | 32 | 7.7 | 200M |
| Atari100K | 26 | 400K | 4 | 1 | 128 | 0.1 | 200M |
| BSuite | 23 | benchmark-specific | 1 | 1 | 1024 | 0.5 | 200M |
| DMC Vision | 20 | 1M | 1 | 16 | 256 | 1.2 | 200M |
| DMC Proprio | 20 | 1M | 1 | 16 | 1024 | 1.5 | 1M |

### 9.3 Baseline 选择

论文比较了两类 baseline：

1. **统一 PPO baseline**：使用 Acme 中高质量 PPO 实现，固定超参数，并尽量选到跨域性能强的设置。
2. **各领域专家算法**：例如 MuZero、Rainbow、PPG、IRIS、TWM、Boot DQN、DrQ-v2、TD-MPC2、DMPO、IMPALA、R2D2+ 等。

Minecraft 上，作者还调了 IMPALA 和 Rainbow，因为从零端到端学习 Minecraft Diamond 此前没有成功报告。

---

## 10. 实验结果

### 10.1 总分表

论文扩展表 1 总结如下：

| Benchmark | Score type | Dreamer | PPO | Tuned expert 1 | Tuned expert 2 |
|---|---|---:|---:|---:|---:|
| Minecraft | Return | **9.1** | 5.1 | IMPALA 7.1 | Rainbow 6.3 |
| DMLab | Capped mean | **71** | 36 | IMPALA 66 (10x data) | R2D2+ 65 (10x data) |
| ProcGen | Normed mean | **72** | 43 | PPG 65 | Rainbow 55 |
| Atari | Gamer median | **830** | 180 | MuZero 693 | Rainbow 223 |
| Atari100K | Gamer mean | **125** | 11 | IRIS 105 | TWM 96 |
| BSuite | Task mean | **66** | 49 | Boot DQN 60 | DQN 54 |
| DMC Vision | Task mean | **802** | 206 | DrQ-v2 705 | TD-MPC2 634 |
| DMC Proprio | Task mean | **843** | 205 | DMPO 834 | TD-MPC2 825 |

这张表的含义非常强：Dreamer 不只是赢 PPO，还在很多领域超过了为对应领域专门调过的专家算法。

### 10.2 各 benchmark 结论

**Atari**  
57 个 Atari 2600 游戏，200M frames，sticky action 设置。Dreamer 的 gamer median 为 830，超过 MuZero 693 和 Rainbow 223。论文还强调 Dreamer 使用的计算资源只是 MuZero 的一部分。

**ProcGen**  
16 个程序生成游戏，50M frames，考验泛化和视觉干扰。Dreamer normed mean 72，超过 PPG 65 和 Rainbow 55。固定超参数 PPO 得分 43。

**DMLab**  
30 个 3D 任务，测试空间和时间推理。Dreamer 在 100M frames 得到 capped mean 71，超过 IMPALA 和 R2D2+ 在 1B steps 的结果 66 和 65。这里 baseline 有 10 倍数据优势，因此论文称数据效率提升超过 1000%。

**Atari100K**  
26 个 Atari 游戏，只有 400K frames，相当于约 2 小时游戏时间。Dreamer gamer mean 125，超过 IRIS 105、TWM 96。论文指出 EfficientZero 仍是强方法，但用了在线树搜索、prioritized replay、超参数 schedule 和 early reset 等复杂机制；Dreamer 在不使用这些复杂机制的情况下超过其余方法。

**DMC Proprio**  
20 个机器人连续控制任务，低维本体感知输入，1M steps。Dreamer task mean 843，接近/超过 DMPO 834 和 TD-MPC2 825。这里 Dreamer 使用 1M 小模型即可。

**DMC Vision**  
同样 20 个控制任务，但输入变成高维图像。Dreamer task mean 802，超过 DrQ-v2 705 和 TD-MPC2 634。这个结果说明 world model 在视觉控制中很有优势。

**BSuite**  
23 个环境，共 468 个配置，测试 credit assignment、奖励尺度鲁棒性、随机性、记忆、泛化和探索。Dreamer task mean 66，超过 Boot DQN 60 和 DQN 54，尤其在 scale robustness 类别改进明显。

### 10.3 Minecraft 钻石结果

Minecraft Diamond 是全文最醒目的实验。设置是：

- 100M environment steps。
- 64 个并行环境实例。
- replay ratio 32。
- 单张 A100，约 8.9 GPU days。
- 稀疏 milestone reward。
- 不使用人类数据。
- 不使用 adaptive curriculum。

结果：

- Dreamer return 9.1，高于 PPO 5.1、IMPALA 7.1、Rainbow 6.3。
- Dreamer 是比较中唯一发现 diamond 的算法。
- 所有 Dreamer agents 在 100M 环境步内发现钻石。
- baseline 可以推进到 iron pickaxe 等较高级物品，但没有发现 diamond。

这说明 Dreamer 的世界模型和探索机制能支撑长链条技能发现。不过要同时记住前面的限制：这里使用的是 MineRL 风格动作空间、抽象合成动作和加速 block breaking，不是完整原版人类键鼠动作空间。

### 10.4 消融实验

论文图 6 做了两类消融。

#### 10.4.1 稳健性技巧消融

去掉以下技巧会降低平均表现：

- observation symlog。
- return normalization，替换成 advantage normalization。
- symexp two-hot，替换成 Huber。
- KL balance 和 free bits。
- 全部去掉。

论文观察到：所有技巧平均上都有贡献，其中尤其重要的是 world model objective 中的 KL balance/free bits，其次是 return normalization 和 symexp two-hot。不同技巧可能只在某些任务上关键，所以跨域平均很需要它们的组合。

#### 10.4.2 学习信号消融

作者停止不同梯度对 world model representation 的塑造：

- 去掉 value gradients。
- 去掉 reward 或 value gradients。
- 去掉 reconstruction gradients。

结果显示 Dreamer 的性能主要依赖 world model 的无监督 reconstruction objective。换句话说，Dreamer 并不是只靠稀疏 reward 来学表示；它大量依赖“从观察中理解世界结构”。这也暗示未来可以用无监督视频预训练来增强世界模型。

### 10.5 Scaling 实验

论文测试了：

- 模型大小：12M 到 400M。
- replay ratio：1 到 64。

结果：

- 模型大小越大，Crafter 和 DMLab goals 表现越好。
- 更大的模型不仅最终分数更高，而且需要更少真实环境交互。
- replay ratio 越高，性能越好。

这说明 DreamerV3 具备比较好的 scaling behavior。对于实践者来说，这意味着可以通过增加模型参数和训练计算换取更高性能，而不是完全靠重新调参。

---

## 11. 为什么 DreamerV3 能跨域稳定

把方法拆开看，DreamerV3 的成功来自几个互补机制。

### 11.1 latent world model 降低学习难度

原始像素空间太大。Dreamer 不直接在像素里规划，而是先学 latent representation。这类似人类玩游戏时不会记住每个像素，而是记住“我面前有树”“背包里有木头”“我需要做工作台”。

### 11.2 reconstruction 给了密集学习信号

稀疏奖励任务最大的问题是 reward 太少。Dreamer 的 world model 每一步都可以通过重建观测得到训练信号，即使当前没有奖励。这样 agent 可以先学世界结构，再把少量奖励和世界结构连接起来。

### 11.3 imagination 提高经验利用率

真实环境里一步一步试很慢。Dreamer 每次从 replay 中取 latent state，在模型里 rollout 多步，让 actor 和 critic 从想象轨迹中学习。replay ratio 越高，同样真实数据被利用越充分。

### 11.4 symlog/two-hot/RetNorm 解决尺度问题

跨域算法最大的敌人之一是尺度：

- 输入尺度不同。
- 奖励尺度不同。
- return 分布不同。
- 梯度大小不同。

DreamerV3 的 symlog、symexp two-hot、percentile return normalization 和 adaptive gradient clipping 都在把“尺度差异”变成训练器能处理的形式。

### 11.5 free bits 和 KL balance 解决表示压缩的两难

表示太复杂，未来难预测；表示太简单，控制没信息。KL balance/free bits 让模型在这两者之间取得稳健平衡。

---

## 12. 常见误解澄清

### 12.1 DreamerV3 是一个多任务统一模型吗？

不是。论文强调的是同一算法和同一超参数配置可以用于很多任务，不是训练一个单一神经网络同时掌握所有任务。每个实验仍然训练对应 agent。

### 12.2 Dreamer 在真实交互时会做树搜索吗？

不会。论文明确说环境交互时从 actor sample 动作，不做 lookahead。它的“规划”主要体现在训练时利用 world model 想象未来。

### 12.3 Minecraft 成就是完全原版游戏吗？

不是完整原版键鼠空间。它基于 MineRL competition 环境，使用抽象 crafting actions、25 个离散动作，并加速 block breaking。但它仍然是视觉输入、低层移动/视角控制、稀疏奖励、长链条技能任务，所以难度很高。

### 12.4 为什么不直接预测像素未来来控制？

Dreamer 确实会用 decoder 重建观测，但 actor/critic 主要在 latent state 上学习。像素预测太细，很多细节和控制无关。latent model 的目标是学对控制有用的、可预测的世界状态。

### 12.5 为什么要预测 continue flag？

如果 episode 结束，未来 reward 不应继续 bootstrap。continue flag $c_t$ 让 lambda return 在终止处截断：

$$
R_t^\lambda
=
r_t + \gamma c_t((1-\lambda)v_t+\lambda R_{t+1}^\lambda).
$$

---

## 13. 新人学习路线

如果你想真正读懂这篇论文，建议按下面顺序补背景：

1. **强化学习基础**：MDP、policy、return、value function、Bellman equation。
2. **Policy gradient**：REINFORCE、advantage、entropy regularization。
3. **Actor-critic**：actor 负责行动，critic 负责评价。
4. **Model-based RL**：学习环境模型、rollout、planning。
5. **Variational latent models**：encoder、decoder、KL、posterior/prior。
6. **RSSM/Dreamer 系列**：PlaNet、DreamerV1、DreamerV2。
7. **分布式 value learning**：categorical value distribution、two-hot targets。
8. **训练稳定化技巧**：normalization、gradient clipping、target networks/EMA。

---

## 14. 最后总结

这篇论文的中心思想是：要让强化学习更通用，不能只在策略网络上堆技巧，而要让智能体学会一个稳定、可扩展、可想象的世界模型。DreamerV3 通过 RSSM latent dynamics、actor-critic imagination training、symlog/symexp two-hot/return normalization/KL balancing/free bits/unimix 等稳健化设计，实现了固定超参数跨大量控制任务的强性能。

最值得记住的不是某一个公式，而是这个系统工程式的组合：

```text
世界模型提供密集表示学习和想象训练
+ actor-critic 在 latent world 中优化长期回报
+ 一组尺度稳健和 KL 稳健技巧让训练跨域不崩
= 一个可以 out-of-the-box 应用到多样控制任务的通用 RL 算法
```

一句话评价：**DreamerV3 把“智能体在脑中模拟世界再练习决策”这条路线，推进到了跨领域固定超参数和 Minecraft 从零拿钻石的强实证阶段。**
