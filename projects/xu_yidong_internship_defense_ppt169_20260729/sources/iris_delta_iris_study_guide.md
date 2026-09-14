# 从 IRIS 到 $\Delta$-IRIS：Transformer 世界模型、离散 Token 与上下文感知 Tokenization

面向人工智能入门学习者的论文讲义（含专家解读版）

根据两篇论文整理：

- Micheli, Alonso, Fleuret, *Transformers are Sample-Efficient World Models*, ICLR 2023
- Micheli, Alonso, Fleuret, *Efficient World Models with Context-Aware Tokenization*, ICML 2024

# 一句话总览

这两篇论文研究的是同一条路线：

**让智能体先学习一个可想象未来的世界模型，再在这个模型里反复练习。**
IRIS 的核心思想是：

$$
\begin{aligned}
\text{图像}
&\xrightarrow{\text{离散自编码器}} \text{少量图像 token}\\
&\xrightarrow{\text{自回归 Transformer}} \text{未来 token、奖励、终止}\\
&\xrightarrow{\text{解码器}} \text{可训练策略的想象世界}.
\end{aligned}
$$

$\Delta$-IRIS 的核心思想是：

$$
\text{不要每一帧都重新描述整个世界，只描述“相对上一帧无法确定的变化”。}
$$

如果把环境想成一部电影，IRIS 像是每一帧都压缩成一小段文字，再让 GPT 续写后面的帧；
$\Delta$-IRIS 则更像视频压缩：已知上一帧和动作后，只记录真正需要补充的变化信息。
这使得模型需要预测的 token 数量大幅下降，从而训练更快、能扩展到更复杂的视觉环境。

# 研究背景：为什么需要世界模型

## 强化学习最小背景

强化学习关心的问题是：一个智能体在环境中不断观察、行动、得到奖励，最终学会让长期奖励最大。
标准形式可以写成马尔可夫决策过程或部分可观测马尔可夫决策过程。论文中面对的是视觉环境，
因此更接近 POMDP：

$$
x_{t+1}, r_t, d_t \sim p(x_{t+1}, r_t, d_t \mid x_{\le t}, a_{\le t}).
$$

其中：

| 符号 | 含义 |
| --- | --- |
| $x_t$ | 第 $t$ 步看到的图像观测，例如 Atari 或 Crafter 的画面 |
| $a_t$ | 第 $t$ 步采取的动作，例如向左、向右、攻击、制作物品 |
| $r_t$ | 环境给出的奖励 |
| $d_t$ | 是否终止 episode |
| $\gamma$ | 折扣因子，控制未来奖励的重要性 |

智能体的目标是学习策略 $\pi$，最大化期望折扣回报：

$$
\max_{\pi}\ \mathbb{E}_{\pi}\left[\sum_{t=0}^{\infty}\gamma^t r_t\right].
$$

入门时可以把它理解成：智能体每一步都要做动作，但它不能只贪眼前奖励，还要考虑这个动作会不会把自己带到一个未来更容易成功的位置。

## 样本效率为什么重要

深度强化学习很强，但常常非常浪费交互数据。论文第一篇在引言中强调：
很多 Atari 或复杂游戏智能体需要数千万甚至更多环境步才能训练好。
如果环境只是模拟器，慢一点还可以忍受；但如果是真实机器人、自动驾驶、工业控制，就会遇到三个问题：
- **时间贵：**真实环境无法像游戏模拟器那样无限加速。
- **成本贵：**机器人试错会消耗硬件寿命、能源和维护成本。
- **安全贵：**智能体在真实环境中乱试动作，可能损坏设备或造成危险。

因此，样本效率是强化学习走向真实世界的关键门槛。
Atari 100k benchmark 就是为了测试样本效率：每个游戏只允许 $100\,000$ 个动作，
大约等于人类玩 2 小时游戏。与常见 Atari 训练的 5000 万步相比，这是一个非常苛刻的设置。

## Model-free 与 Model-based 的区别

强化学习方法可以粗略分成两类。

### Model-free

直接从真实交互中学习策略或价值函数。它不显式学习环境如何变化。
类比：学生只靠刷真题总结经验，不试图理解出题机制。

### Model-based

先学习一个环境模型，再利用模型规划或训练策略。类比：学生先总结“题目生成规律”，再在自己构造的题里练习。

世界模型是 model-based RL 的核心：

$$
\text{world model} \approx \text{一个可被智能体调用的环境模拟器}.
$$

如果世界模型足够准确，智能体可以在模型里生成大量 imagined trajectories。
这就像开车前在脑中预演不同路线，或者下棋时在脑中推演后续局面。

## 学习在想象中进行

IRIS 和 $\Delta$-IRIS 都属于 “learning in imagination” 路线。
训练循环可以概括为三步：
- **真实收集：**用当前策略在真实环境中收集少量数据。
- **学习世界模型：**用真实数据训练模型，让它预测未来图像、奖励和终止。
- **想象训练策略：**在世界模型里 rollout 很多轨迹，用这些轨迹训练 actor-critic。

这里最关键的假设是：

$$
\text{真实交互只用来修正世界模型，策略的大量练习发生在模型内部。}
$$

这也是风险所在：如果世界模型错了，策略会在错误世界里学会错误行为。
所以两篇论文的真正主角不是 policy，而是 world model architecture。

> **我的理解：世界模型的真正价值**  
> 我认为这两篇论文最值得新人抓住的一点是：世界模型不是为了“画出漂亮视频”，而是为了给策略提供一个足够可信的训练场。它的价值不在于每个像素都完美，而在于它能不能保留动作、奖励、死亡、物体变化这些会影响决策的因果结构。换句话说，世界模型首先是控制用的模型，其次才是生成用的视频模型。

# 为什么 Transformer 可以做世界模型

## 把环境动态看成序列建模

Transformer 最擅长处理序列。语言模型会根据前面的 token 预测下一个 token：

$$
p(w_{t+1}\mid w_{\le t}).
$$

IRIS 的关键类比是：

| 语言模型 | 世界模型 | 含义 |
| --- | --- | --- |
| 单词 token | 图像 token | 当前画面的离散表示 |
| 句子前缀 | 历史观测和动作 | 当前上下文 |
| 预测下一个词 | 预测下一帧 token | 想象未来 |

于是动态模型可以写成：

$$
p(z_{t+1}\mid z_{\le t}, a_{\le t}),
$$

其中 $z_t$ 是图像 $x_t$ 被压缩后的 token 序列。

## 为什么不能直接把像素丢给 Transformer

一张 $64\times64\times3$ 的图像有 $12288$ 个像素值。
如果把每个像素都当 token，序列会太长，而标准 self-attention 的计算复杂度大约是：

$$
O(n^2),
$$

其中 $n$ 是序列长度。

所以需要先把图像压缩成少量离散 token。
IRIS 使用 $K=16$ 个 token 表示一帧；
$\Delta$-IRIS 在 Crafter 中只用 $K=4$ 个 $\Delta$-token 表示一帧的变化。

这背后是一个非常重要的工程直觉：

Transformer 很强，但不能把所有原始细节都硬塞进去。真正可扩展的方法要先设计好 tokenization。
> **我的理解：tokenization 比模型大小更关键**  
> 很多人读到 Transformer 会自然想到“把模型做大”。但在这两篇论文里，我更看重 tokenization。因为世界模型的计算瓶颈经常不是 Transformer 会不会表达，而是输入序列是否太长、token 是否把决策相关信息保留下来。IRIS 和 $\Delta$-IRIS 的差别，本质上就是从“用大模型续写图像语言”推进到“先把语言设计得更适合环境动态”。这是一种很工程、也很深刻的研究视角。

# 第一篇论文：IRIS 的动机与贡献

## 论文要解决的问题

论文 *Transformers are Sample-Efficient World Models* 的问题可以概括为：

> 
能否把 Transformer 和离散图像 token 结合起来，做一个足够准确的世界模型，让策略几乎完全在想象中学会玩 Atari？

当时已有的方法包括：
- SimPLe：在视频预测模型中用 PPO 训练策略。
- DreamerV2：用 RSSM 学 latent dynamics，再在 latent imagination 中训练。
- MuZero / EfficientZero：用模型加 lookahead search。
- CURL、DrQ、SPR：更偏 model-free 或 representation learning 的样本高效方法。

IRIS 的定位很清楚：它不使用决策时搜索，而是证明一个 Transformer 世界模型本身就可以提供很强的样本效率。

> **我的理解：IRIS 的研究胆量**  
> IRIS 的大胆之处在于，它没有沿着当时最强的搜索路线继续堆复杂度，而是问了一个更基础的问题：如果世界模型本身足够会“续写环境”，策略能不能靠想象学会行为？这让强化学习问题部分转化成了生成建模问题。对新人来说，这个转化非常重要：现代 AI 里很多突破并不是把旧模块调得更细，而是把问题重写成另一个领域已经擅长解决的形式。

## 核心贡献

IRIS 的贡献主要有四点：
- **提出 Transformer world model。**
把环境动态学习转化为离散 token 序列的自回归建模。
- **使用离散自编码器构造图像语言。**
原始帧先变成少量 token，Transformer 不直接处理像素。
- **策略完全在想象中训练。**
真实环境数据用于训练世界模型，policy/value 的主要训练数据来自模型 rollout。
- **在 Atari 100k 上取得无 lookahead search 方法的新 SOTA。**
只用约 2 小时人类游戏量，mean human-normalized score 达到 1.046，10/26 个游戏超过人类。

# IRIS 方法详解

## 整体结构

IRIS 包含三大模块：

| 模块 | 记号 | 作用 |
| --- | --- | --- |
| 离散自编码器 | $E,D$ | 图像 $\leftrightarrow$ 离散 token |
| 自回归 Transformer | $G$ | 根据历史 token 和动作预测未来 token、奖励、终止 |
| Actor-Critic | $\pi,V$ | 在想象图像中学习行为 |

完整流程如下：

$$
x_t \xrightarrow{E} z_t
\xrightarrow{G,\ a_t} \hat z_{t+1}, \hat r_t, \hat d_t
\xrightarrow{D} \hat x_{t+1}
\xrightarrow{\pi,V} \text{更新策略和价值}.
$$

## 离散自编码器：把图像变成 token

离散自编码器包含编码器 $E$、解码器 $D$ 和 codebook。
编码器先把图像 $x_t$ 映射到连续向量：

$$
y_t \in \mathbb{R}^{K\times d}.
$$

codebook 是 $N$ 个可学习向量：

$$
\mathcal{E}={e_i}_{i=1}^{N},\quad e_i\in \mathbb{R}^d.
$$

每个位置选择最近的 codebook 向量：

$$
z_t^k = \arg\min_i \left\|y_t^k-e_i\right\|_2^2,\quad k=1,\dots,K.
$$

于是图像变成：

$$
z_t=(z_t^1,\dots,z_t^K)\in {1,\dots,N}^K.
$$

IRIS 的主要设置是：

| 超参数 | IRIS 值 |
| --- | --- |
| 图像尺寸 | $64\times64$ |
| 词表大小 $N$ | 512 |
| 每帧 token 数 $K$ | 16 |
| token embedding 维度 $d$ | 512 |

入门类比：自编码器像一个翻译器，把连续图像翻译成离散短句；
解码器再把短句翻译回图像。
Transformer 不直接看图像，而是学习这种短句如何随动作变化。

## 自编码器损失

IRIS 的自编码器训练损失包括三部分：

$$
\mathcal{L}_{AE}
= \underbrace{\|x-D(z)\|_1}_{\text{重建损失}}
+ \underbrace{\|\mathrm{sg}(E(x))-e(z)\|_2^2
+ \|\mathrm{sg}(e(z))-E(x)\|_2^2}_{\text{VQ commitment / codebook 损失}}
+ \underbrace{\mathcal{L}_{perceptual}(x,D(z))}_{\text{感知损失}}.
$$

其中 $\mathrm{sg}(\cdot)$ 表示 stop-gradient。
它的作用是控制梯度流向，使编码器和 codebook 能稳定对齐。

## Transformer 动态模型

IRIS 的 Transformer 输入是交错的帧 token 和动作：

$$
(z_0^1,\dots,z_0^K,a_0,z_1^1,\dots,z_1^K,a_1,\dots,z_t^1,\dots,z_t^K,a_t).
$$

它预测三类东西：

$$
\hat z_{t+1}^k \sim p_G(\hat z_{t+1}^k\mid z_{\le t},a_{\le t},\hat z_{t+1}^{<k}),
$$

$$
\hat r_t \sim p_G(\hat r_t\mid z_{\le t},a_{\le t}),
$$

$$
\hat d_t \sim p_G(\hat d_t\mid z_{\le t},a_{\le t}).
$$

注意第一行里的 $\hat z_{t+1}^{<k}$。
这表示下一帧的 $K$ 个 token 不是一次性独立预测，而是像语言模型那样一个接一个生成。
第 $k$ 个 token 会依赖之前已经生成的 token。

## 动态模型的训练目标

Transformer 的训练数据来自 replay buffer 中真实收集的片段。
对每个片段：

$$
(x_\tau,a_\tau,r_\tau,d_\tau,\dots,x_{\tau+L},a_{\tau+L}).
$$

先用 $E$ 得到 token，再训练 $G$ 做监督预测：
- transition token：交叉熵损失；
- termination：交叉熵损失；
- reward：均方误差或交叉熵，取决于奖励形式。

最简化写法：

$$
\mathcal{L}_G
= \sum_{t,k}\mathrm{CE}(z_{t+1}^k,\hat z_{t+1}^k)
+ \sum_t \mathrm{CE}(d_t,\hat d_t)
+ \sum_t \ell(r_t,\hat r_t).
$$

## 在想象中训练策略

有了世界模型后，IRIS 从 replay buffer 中拿一个真实起始帧 $x_0$，然后在模型内部 rollout：

$$
\hat x_t \xrightarrow{\pi} a_t
\xrightarrow{G} \hat z_{t+1},\hat r_t,\hat d_t
\xrightarrow{D} \hat x_{t+1}.
$$

这个过程持续 $H$ 步。IRIS 使用 imagination horizon $H=20$。

因为 rollout horizon 有限，不能只用短期奖励估计价值，所以引入 value network $V$。
论文采用 Dreamer 系列常用的 $\lambda$-return：

$$
\Lambda_t =
\begin{cases}
\hat r_t+\gamma(1-\hat d_t)\left((1-\lambda)V(\hat x_{t+1})+\lambda\Lambda_{t+1}\right), & t < H,\\
V(\hat x_H), & t=H.
\end{cases}
$$

Value loss：

$$
\mathcal{L}_V
= \mathbb{E}_{\pi}\left[
\sum_{t=0}^{H-1}\left(V(\hat x_t)-\mathrm{sg}(\Lambda_t)\right)^2
\right].
$$

Policy 使用带 value baseline 的 REINFORCE：

$$
\mathcal{L}_{\pi}
=-\mathbb{E}_{\pi}\left[
\sum_{t=0}^{H-1}
\log \pi(a_t\mid \hat x_{\le t})\,
\mathrm{sg}(\Lambda_t-V(\hat x_t))
+\eta H(\pi(\cdot\mid \hat x_{\le t}))
\right].
$$

这里的 $H(\pi)$ 是策略熵，鼓励探索。

## IRIS 伪代码

**代码：IRIS 训练循环的简化伪代码**

```python
for epoch in range(num_epochs):
    # 1. collect real experience
    obs = env.reset()
    for _ in range(steps_collect):
        rec_obs = decoder(encoder(obs))
        action = policy.sample(rec_obs)
        next_obs, reward, done = env.step(action)
        replay.add(obs, action, reward, done)
        obs = env.reset() if done else next_obs

    # 2. train world model on real trajectories
    for _ in range(world_model_updates):
        batch = replay.sample_segments(length=L)
        tokens = encoder(batch.obs)
        recon = decoder(tokens)
        loss_ae = reconstruction_loss(batch.obs, recon) + vq_losses(...)
        loss_g = transformer_prediction_loss(tokens, batch.action,
                                             batch.reward, batch.done)
        update(encoder, decoder, transformer, loss_ae + loss_g)

    # 3. train policy/value in imagination
    for _ in range(policy_updates):
        x = replay.sample_initial_obs()
        imagined = rollout_world_model(x, encoder, decoder, transformer, policy, H)
        lambda_returns = compute_lambda_returns(imagined.rewards,
                                                imagined.dones,
                                                value)
        update(value, value_loss(lambda_returns))
        update(policy, reinforce_loss(lambda_returns, value, imagined.actions))
```

# IRIS 实验结果详解

## 实验设置

IRIS 主要在 Atari 100k 上评估。
设置要点如下：
- 26 个 Atari 游戏；
- 每个游戏只允许 $100\,000$ 个真实动作；
- 约等于 2 小时人类游戏经验；
- 每个游戏 5 个随机种子；
- 最终对每个游戏评估 100 个 episode；
- 与 SimPLe、CURL、DrQ、SPR、MuZero、EfficientZero 等方法比较。

Atari 100k 常用 human-normalized score：

$$
\mathrm{HNS}
=\frac{\mathrm{score}_{agent}-\mathrm{score}_{random}}
{\mathrm{score}_{human}-\mathrm{score}_{random}}.
$$

$\mathrm{HNS}=1$ 表示人类水平；
$\mathrm{HNS}>1$ 表示超过人类；
$\mathrm{HNS}=0$ 表示随机策略水平。

## 核心定量结果

| 方法 | #超人类游戏 | Mean HNS | Median HNS | IQM |
| --- | --- | --- | --- | --- |
| SimPLe | 1 | 0.332 | 0.134 | 0.130 |
| CURL | 2 | 0.261 | 0.092 | 0.113 |
| DrQ | 3 | 0.465 | 0.313 | 0.280 |
| SPR | 6 | 0.616 | 0.396 | 0.337 |
| IRIS | 10 | 1.046 | 0.289 | 0.501 |

论文结论是：
- IRIS 在无 lookahead search 方法中达到新的 state of the art；
- mean HNS 达到 1.046，超过人类平均水平；
- 10/26 个游戏超过人类；
- 与 SPR 相比，mean、IQM、optimality gap、超人类游戏数量都有明显改进。

> **我的理解：不要只看 mean HNS**  
> 我会把 IRIS 的结果理解成“世界模型路线很有潜力，但还不均匀成熟”。Mean HNS 很高，说明它在一些环境里能学出很强行为；median 没有同样突出，说明它不是全面碾压。对强化学习论文来说，这种差异很常见，也很值得看：平均值告诉我们上限，median 和失败案例告诉我们方法的真实短板在哪里。

## 怎么看这些结果

IRIS 的 mean 很高，但 median 不是最高。
这说明它在一些游戏上特别强，例如 Boxing、Breakout、CrazyClimber、Krull 等；
但在某些游戏上仍然困难，例如 Frostbite、PrivateEye、Alien 等。

论文指出两个重要失败原因：

### 双重探索问题

如果某个新关卡或新机制必须通过低概率事件触发，IRIS 需要先在真实环境中发现它，
世界模型才能学会它；之后 policy 还要在想象中再次发现并利用它。
这就是 double exploration problem。

### 视觉细节瓶颈

有些游戏需要很小的视觉细节，例如敌人、奖励、玩家位置。
如果 16 个 token 不足以重建这些细节，world model 就会给 policy 一个错误世界。
论文附录显示，在 Alien、Asterix、BankHeist 中把每帧 token 从 16 增加到 64 后，
Asterix 从 853.6 提高到 1890.4，BankHeist 从 53.1 提高到 282.5。

## 质性分析

IRIS 的图像例子展示了三类能力：
- 在 KungFuMaster 中，从同一个起始帧生成多个合理未来，说明模型能表达不确定性；
- 在 Pong 中，只给前两帧和真实动作，模型可以像素级预测球和挡板轨迹；
- 在 Breakout 和 Gopher 中，模型能预测奖励和 episode termination。

这很关键，因为策略不是在真实环境中学习，而是在世界模型生成的图像中学习。
如果模型不知道“球没接住会死”或“打掉砖块有奖励”，policy 就无法学到正确行为。

# 第二篇论文：$\Delta$-IRIS 的动机与贡献

## 从 IRIS 到 $\Delta$-IRIS 的问题

IRIS 已经证明：

$$
\text{离散自编码器}+\text{自回归 Transformer}
$$

可以成为有效的世界模型。

但 IRIS 有一个扩展瓶颈：

每一帧都独立编码，token 必须包含重建整张图所需的全部信息。
环境越复杂，帧越难压缩，需要的 token 越多，Transformer 越慢。
Transformer 的 attention 是二次复杂度。
如果每帧 token 从 16 增加到 64，序列长度会显著增加，训练和想象速度都会下降。
第一篇论文附录已经显示：更多 token 能提高重建和性能，但代价很大。

## $\Delta$-IRIS 的核心观察

连续视频帧之间通常有大量冗余。
如果我知道上一帧和你刚按的动作，就不需要完整描述下一帧。

例如：
- 智能体按右键，角色向右移动一格：这大多是确定性的；
- 砍树后木头数量增加：这也大多由动作和规则决定；
- 突然刷出敌人、怪物随机移动：这是随机或不确定部分。

$\Delta$-IRIS 的思想是：

$$
\text{token 不再描述整张图，而是描述在给定过去和动作后仍无法确定的变化。}
$$

论文称这些离散 token 为 $\Delta$-tokens。

> **我的理解：$\Delta$-IRIS 的创新不是简单省 token**  
> 我认为 $\Delta$-IRIS 的关键不是“把 16 个 token 变成 4 个 token”这么表面，而是它重新定义了 token 的任务。IRIS 的 token 要回答“这张图是什么”，$\Delta$-IRIS 的 token 要回答“在已知过去和动作后，还有什么无法推出”。后者更接近因果和动态建模，也更符合控制任务的需求：智能体真正关心的是动作造成了什么变化，而不是每一帧的所有静态背景。

## 核心贡献

$\Delta$-IRIS 的贡献主要有四点：
- **上下文感知自编码器。**
编码和解码当前帧时，不只看当前帧，也看过去帧和动作。
- **用少量 $\Delta$-tokens 表示随机变化。**
在 Crafter 中每帧只用 4 个 token，而 IRIS 需要 16 或 64 个 token。
- **在 Transformer 序列中加入连续 I-tokens。**
I-token 是当前世界状态的连续摘要，帮助 Transformer 不必从所有历史 $\Delta$-token 中重新积分状态。
- **在 Crafter 上取得更好的扩展性。**
10M frames 时 $\Delta$-IRIS return 16.1，超过 DreamerV3 XL 的 15.1；
训练速度比 IRIS 64-token 版本快约 10 倍。

# $\Delta$-IRIS 方法详解

## 上下文感知 tokenization

IRIS 的自编码器是：

$$
E_I: X\rightarrow {1,\dots,N_I}^{K_I},\quad
D_I:{1,\dots,N_I}^{K_I}\rightarrow X.
$$

它独立编码每一帧：

$$
z_t=E_I(x_t).
$$

$\Delta$-IRIS 改成：

$$
E:S(X\times A)\times X \rightarrow Z^K,
$$

$$
z_t=E(x_0,a_0,\dots,x_{t-1},a_{t-1},x_t).
$$

解码器也带上下文：

$$
\hat x_t
=D(x_0,a_0,\dots,x_{t-1},a_{t-1},z_t).
$$

这意味着 $z_t$ 不必携带完整图像信息。
它只需要告诉解码器：

> 
在已知过去帧和动作的情况下，还有哪些东西是你无法自己推出来的？

这就是 $\Delta$-token 的直觉。

## 确定性与随机性的拆分

$\Delta$-IRIS 最重要的理论直觉是把动态拆成两部分：

$$
\text{环境变化} = \text{确定性变化} + \text{随机/不可预测变化}.
$$

确定性变化可以由 decoder 根据过去帧和动作直接建模；
随机变化由 $\Delta$-tokens 传递给 decoder。

类比视频压缩：
- I-frame：完整关键帧；
- P/B-frame：相对于附近帧的变化；
- $\Delta$-IRIS：让 token 更像“变化补丁”而不是完整图像。

## $\Delta$-IRIS 自编码器损失

$\Delta$-IRIS 的自编码器训练损失包括：

$$
\mathcal{L}_{\Delta AE}
= \alpha_1\|x-\hat x\|_1
+\alpha_2\|x-\hat x\|_2^2
+\alpha_{\max}\mathcal{L}_{max\text{-}pixel}
+\alpha_c\mathcal{L}_{commit}.
$$

论文中 Crafter 主要设置为：

| 项目 | 值 |
| --- | --- |
| 词表大小 $N$ | 1024 |
| 每帧 $\Delta$-token 数 $K$ | 4 |
| token embedding 维度 | 64 |
| conditioning time steps | 1 |
| L1 权重 | 0.1 |
| L2 权重 | 1.0 |
| max-pixel 权重 | 0.01 |
| commitment 权重 | 0.02 |

max-pixel loss 的作用是避免模型只追求平均误差很小，却忽略局部关键像素。
对于游戏画面，小物体、敌人、血量、工具图标都可能只占几个像素，但对决策非常重要。

## 为什么需要 I-tokens

如果只预测 $\Delta$-tokens，会出现一个新问题：
要判断当前世界状态，Transformer 可能需要把初始帧、所有动作、所有过去 $\Delta$-tokens 全部整合起来。

这比 IRIS 直接预测下一帧 token 更难。
因为 $\Delta$-token 是变化，不是完整状态。

论文用 I-token 解决这个问题。
I-token 是由当前帧经过 CNN 得到的连续 embedding：

$$
\tilde x_t = f_{\mathrm{CNN}}(x_t).
$$

它不是离散 token，也不是 Transformer 预测的对象；
它只是放进 Transformer 输入序列，帮助模型知道“当前世界长什么样”。

输入序列变成：

$$
(\tilde x_0,a_0,z_1^1,\dots,z_1^K,\tilde x_1,a_1,z_2^1,\dots,z_2^K,\dots).
$$

Transformer 预测：

$$
\hat z_t^{k+1}\sim
p_G(\hat z_t^{k+1}\mid \tilde x_{<t}, z_{<t}, a_{<t}, z_t^{\le k}),
$$

$$
\hat r_t\sim p_G(\hat r_t\mid \tilde x_{\le t},z_{\le t},a_{\le t}),
\quad
\hat d_t\sim p_G(\hat d_t\mid \tilde x_{\le t},z_{\le t},a_{\le t}).
$$

入门类比：

> 
$\Delta$-token 像“变化记录”，I-token 像“当前地图快照”。
没有地图快照，只看变化记录，时间一长就很容易迷路。

## $\Delta$-IRIS 的想象 rollout

$\Delta$-IRIS 的想象过程与 IRIS 相似，但下一帧的解码依赖过去上下文：

$$
\hat x_{t+1}
=D(\hat x_{\le t},a_{\le t},\hat z_{t+1}).
$$

简化伪代码如下：

**代码：Delta-IRIS 想象过程的简化伪代码**

```python
def imagine_delta_iris(x0, policy, encoder, decoder, transformer, horizon):
    frames = [x0]
    actions = []
    delta_tokens = []
    rewards = []
    dones = []

    for t in range(horizon):
        # policy acts on reconstructed / imagined frames
        action = policy.sample(frames)
        actions.append(action)

        # I-token summarizes the current world state
        i_token = cnn_frame_embedder(frames[-1])

        # transformer autoregressively predicts next delta tokens
        z_next = []
        for k in range(K):
            logits = transformer(i_tokens_so_far, actions, delta_tokens, z_next)
            z_k = sample_categorical(logits)
            z_next.append(z_k)

        reward, done = transformer.predict_reward_done(...)
        rewards.append(reward)
        dones.append(done)

        # decoder reconstructs the next frame using context + delta tokens
        next_frame = decoder(frames, actions, z_next)
        frames.append(next_frame)
        delta_tokens.append(z_next)

        if done:
            break

    return frames, actions, rewards, dones
```

# $\Delta$-IRIS 实验结果详解

## Crafter 实验设置

第二篇论文主要使用 Crafter benchmark。
Crafter 是一个受 Minecraft 启发的程序生成环境，特点包括：
- 图像输入；
- 离散动作空间；
- 非确定性动态；
- 生存、探索、战斗、采集、制作等机制；
- 共有 22 个任务，考察探索、泛化、信用分配和长期规划。

对比方法包括：
- DreamerV3 M；
- DreamerV3 XL；
- IRIS 16 tokens；
- IRIS 64 tokens；
- $\Delta$-IRIS；
- $\Delta$-IRIS without I-tokens。

实验统一使用 imagined-to-collected data ratio $=64$，每个方法 5 个种子。
每 $1$M frames 评估一次，每次用 256 个测试 episode。

## Crafter 主要结果

| 方法 | Return @1M | Return @5M | Return @10M | 参数量 | FPS |
| --- | --- | --- | --- | --- | --- |
| $\Delta$-IRIS | 7.7 | 15.4 | 16.1 | 25M | 20 |
| DreamerV3 XL | 9.2 | 14.2 | 15.1 | 200M | 30 |
| IRIS 64 tokens | 5.5 | -- | -- | 48M | 2 |
| $\Delta$-IRIS w/o I-tokens | 6.6 | 10.4 | 12.6 | 24M | 22 |
| DreamerV3 M | 6.2 | 12.6 | 13.7 | 37M | 40 |
| IRIS 16 tokens | 4.4 | -- | -- | 50M | 6 |

结论：
- 1M frames 时 DreamerV3 XL 更强，说明 $\Delta$-IRIS 在极少数据时还不占优；
- 超过约 3M frames 后，$\Delta$-IRIS 学习曲线超过 DreamerV3；
- 10M frames 时，$\Delta$-IRIS return 16.1，高于 DreamerV3 XL 的 15.1；
- $\Delta$-IRIS 约解决 17/22 个任务；
- IRIS 64 tokens 训练非常慢，FPS 只有 2，而 $\Delta$-IRIS FPS 为 20，约快 10 倍；
- 去掉 I-tokens 后，10M return 从 16.1 降到 12.6，说明 I-token 对动态建模很关键。

> **我的理解：实验结果说明了“表示方式”的力量**  
> 从实验上看，$\Delta$-IRIS 的优势并不是参数量最大带来的。它只有 25M 参数，比 DreamerV3 XL 的 200M 小很多，却在 10M frames 时更强。这说明在世界模型里，结构归纳偏置非常重要：如果模型输入被设计成更贴近环境变化规律，模型可以用更少参数、更少 token 做更有效的预测。

## World model 指标与消融

论文还直接比较了世界模型的重建与预测质量。

| 方法 | L2 reconstruction loss |
| --- | --- |
| $\Delta$-IRIS 4 tokens | 0.000185 |
| IRIS 64 tokens | 0.001715 |
| IRIS 16 tokens | 0.007496 |

这个结果非常重要：
即使用 4 个 $\Delta$-tokens，$\Delta$-IRIS 的重建误差也远小于 IRIS 64 tokens。
原因不是 token 魔法变强了，而是任务变简单了：

$$
\text{重建整张图} \quad \rightarrow \quad \text{在上下文中补充变化}.
$$

I-token 消融：

| 方法 | next token CE | reward CE |
| --- | --- | --- |
| $\Delta$-IRIS | 1.57 | 0.108 |
| $\Delta$-IRIS w/o I-tokens | 1.73 | 0.135 |

去掉 I-token 后，下一 token 预测和 reward 预测都变差。
这说明 I-token 不只是锦上添花，而是在帮助 Transformer 维护当前状态。

## Atari 100k 附录结果

$\Delta$-IRIS 也在 Atari 100k 上测试。
它与 IRIS 相比：

| 方法 | #超人类游戏 | Mean HNS | IQM |
| --- | --- | --- | --- |
| SimPLe | 1 | 0.33 | 0.13 |
| DreamerV3 | 9 | 1.10 | 0.50 |
| STORM | 10 | 1.27 | 0.64 |
| IRIS | 10 | 1.05 | 0.50 |
| $\Delta$-IRIS | 11 | 1.39 | 0.65 |

论文强调：$\Delta$-IRIS 在 Atari 100k 上 aggregate metrics 高于 IRIS，
同时训练时间约 26 小时，相比 IRIS 有 5 倍加速。

# 两篇论文的关系

## IRIS 解决了什么

IRIS 回答的是：

> 
Transformer 能不能作为样本高效强化学习中的世界模型？

答案是可以。
只要先把图像变成离散 token，Transformer 就能学环境动态；
policy 可以在想象中训练，并在 Atari 100k 中达到强表现。

## $\Delta$-IRIS 解决了什么

$\Delta$-IRIS 回答的是：

> 
IRIS 这条路线能不能更快、更可扩展，适应更复杂环境？

答案是：通过上下文感知 tokenization 和 I-token，可以大幅减少每帧 token 数，
并让 Transformer 把算力集中在随机动态上。

## 核心区别表

| 维度 | IRIS | $\Delta$-IRIS |
| --- | --- | --- |
| token 含义 | 描述整张图像 | 描述给定上下文后仍需补充的变化 |
| 自编码器输入 | 当前帧 $x_t$ | 过去帧、动作、当前帧 |
| 解码器输入 | token $z_t$ | 过去帧、动作、$\Delta$-tokens |
| 每帧 token 数 | Atari 中 16；复杂时可到 64 | Crafter 中 4 |
| Transformer 输入 | 图像 token + action token | I-token + action token + $\Delta$-token |
| 主要优势 | 证明 Transformer world model 可行 | 更快、更可扩展、重建更好 |
| 主要风险 | token 数随视觉复杂度增加 | $\Delta$-token 预测更难，需要 I-token 支撑 |

# 实现细节：从论文到代码该怎么想

## 模块化实现

一个实际代码库通常可以拆成以下模块：

| 模块 | 主要函数 |
| --- | --- |
| ReplayBuffer | 存储真实轨迹，采样片段 |
| Tokenizer / Autoencoder | encode, decode, reconstruction loss |
| DynamicsTransformer | predict next token, reward, done |
| ActorCritic | policy action, value estimate |
| ImaginationRollout | 用世界模型生成 imagined trajectory |
| Trainer | 调度真实收集、世界模型更新、策略更新 |

## VQ tokenization 的核心代码

**代码：VQ tokenization 的极简 PyTorch 风格示意**

```python
def vector_quantize(y, codebook):
    # y: [batch, K, dim]
    # codebook: [N, dim]
    # compute squared distance to every code
    dist = ((y[:, :, None, :] - codebook[None, None, :, :]) ** 2).sum(-1)
    indices = dist.argmin(dim=-1)          # [batch, K]
    quantized = codebook[indices]          # [batch, K, dim]

    # straight-through estimator:
    quantized_st = y + (quantized - y).detach()
    return indices, quantized_st
```

这段代码对应公式：

$$
z_t^k=\arg\min_i\|y_t^k-e_i\|_2^2.
$$

## 自回归预测 next tokens

**代码：自回归生成下一帧 token 的极简示意**

```python
def sample_next_tokens(transformer, context, K):
    next_tokens = []
    for k in range(K):
        logits = transformer(context, partial_next=next_tokens)
        token_k = categorical_sample(logits[:, -1])
        next_tokens.append(token_k)
    return next_tokens
```

关键点是：
第 $k$ 个 token 的预测依赖已经生成的 $1,\dots,k-1$ 个 token。
这允许模型表达同一帧内部 token 之间的依赖关系。

## 为什么 reward 和 done 也要预测

只预测下一帧不够。
策略训练需要奖励和终止信号。

如果模型能生成画面，却不知道哪一帧得分、哪一帧死亡，那么 policy 在想象中就没有可靠学习目标。
因此 IRIS 和 $\Delta$-IRIS 都让 Transformer 同时预测：

$$
(\hat z_{t+1},\hat r_t,\hat d_t).
$$

## 训练比例的含义

两篇论文都使用交替训练：
- 收集真实数据；
- 多次更新世界模型；
- 多次在想象中更新 policy/value。

$\Delta$-IRIS 中固定 imagined-to-collected data ratio 为 64。
直观理解：每收集 1 份真实数据，允许智能体在脑内练习约 64 份等价数据。

这也是 model-based RL 的价值所在：

$$
\text{少量真实经验} \rightarrow \text{大量模型内训练经验}.
$$

# 新人容易卡住的概念

## 世界模型不是越真实越好，而是要对决策有用

很多新人会以为世界模型必须像真实世界一样完美。
其实强化学习中更重要的是：

$$
\text{模型是否保留了影响奖励和动作选择的关键信息。}
$$

例如 Breakout 中，墙壁纹理的小误差可能不重要；
球的位置、砖块是否消失、球没接住是否终止才重要。

## 离散 token 的意义

离散 token 的好处是让视觉动态变成类似语言建模的问题。
Transformer 对离散序列非常成熟，交叉熵训练也稳定。

但 token 太少会丢细节，token 太多会让 Transformer 太慢。
IRIS 的瓶颈正是这个 trade-off。

## 为什么 $\Delta$-token 能省 token

因为它利用了时间冗余。
如果上一帧已经告诉你地形、角色、背包位置，动作又告诉你角色想做什么，
下一帧的大部分内容都可以推断。

真正需要 token 记录的是：
- 随机刷新的敌人；
- 不确定的怪物移动；
- 模型难以从规则中直接推断的局部变化；
- 视觉中细小但决策相关的误差补丁。

## 为什么 I-token 很像“状态缓存”

只看 $\Delta$-token 就像只看一串“往右、往上、少了一个怪、加了一个木头”的日志。
时间长了以后，你很难仅凭日志准确恢复当前地图。

I-token 相当于不断提供当前状态摘要。
它不是要替代 $\Delta$-token，而是帮助 Transformer 在预测下一步变化时知道当前世界大概是什么样。

# 局限性与未来方向

## IRIS 的局限
- 对视觉细节敏感的游戏需要更多 token，计算成本增加；
- 对低概率事件和新关卡存在 double exploration problem；
- policy 仍然从重建帧学习，没有充分利用 world model 内部 representation；
- 没有结合 MCTS，可能错过规划型方法的优势。

## $\Delta$-IRIS 的局限
- 极少数据时不一定优于 DreamerV3 XL；
- 每一步使用固定数量 $\Delta$-tokens，但真实环境的不确定性是动态变化的；
- $\Delta$-token 预测任务更难，需要 I-token 等结构支撑；
- 仍然依赖世界模型质量，稀有事件没有被真实数据覆盖时，模型无法想象正确机制。

## 可能的研究方向

论文提出或暗示了几个方向：
- 动态决定每一步需要多少 $\Delta$-tokens；
- 让 policy 直接利用 world model 的内部 representation；
- 与 MCTS 或其他 planning 方法结合；
- 改进探索，使稀有事件更容易进入 replay buffer；
- 设计更强的上下文感知视频 tokenization。

# 专家视角：我自己的理解

## 这两篇论文真正连接了两个时代

我的理解是，IRIS 和 $\Delta$-IRIS 连接了强化学习和生成模型两个时代。
传统强化学习更关心 value、policy、exploration、planning；
而这两篇论文把一大部分难点推给了 generative modeling：

$$
\text{如果我能生成足够可信的未来，策略学习就可以在生成世界里发生。}
$$

这和大模型时代的思路很像：先学一个强大的预测模型，再把下游任务放到这个模型提供的表征或模拟能力上。
所以 IRIS 不只是一个 Atari agent，它代表了一种思考方式：

强化学习的关键瓶颈，可能不是 policy optimizer 不够聪明，而是智能体缺少一个可复用、可扩展、可想象的世界表征。
## IRIS 的本质：把 RL 问题搬到语言模型熟悉的地盘

IRIS 最让我觉得聪明的地方，是它把视觉动态变成了“离散 token 序列预测”。
这一步非常像把一个陌生问题翻译成 Transformer 熟悉的语言。

如果直接在像素空间预测未来，模型面对的是连续、高维、噪声很大的对象；
如果先经过离散自编码器，模型面对的是更短、更稳定的 token 序列。
于是问题从：

$$
\text{预测下一张复杂图片}
$$

变成：

$$
\text{预测下一串离散符号}.
$$

我认为这就是 IRIS 最核心的思想价值。
它不是单纯把 Transformer 塞进 RL，而是认真设计了一个让 Transformer 能发挥优势的接口。

## $\Delta$-IRIS 的本质：从“压缩图像”走向“压缩变化”

$\Delta$-IRIS 的进步更像是从图像压缩走向动态压缩。
IRIS 问的是：一帧图像怎样压缩成 token？
$\Delta$-IRIS 问的是：在已经知道过去和动作后，下一帧还剩多少信息需要编码？

这两个问题的难度完全不同。
第一种会浪费很多 token 描述静态背景；
第二种把 token 集中在不确定变化上。
对控制任务来说，第二种更自然，因为智能体采取动作后真正关心的是“世界发生了什么变化”。

所以我会把 $\Delta$-IRIS 看成一个更成熟的世界模型设计：
它不再把环境当成一串独立图片，而是当成一个由动作驱动、由规则和随机性共同产生的动态系统。

## 我认为最重要的启发

如果你刚入门人工智能，我建议从这两篇论文带走三个启发：
- **好的表示能改变问题难度。**
同样是预测未来，像素、整帧 token、$\Delta$-token 的难度完全不同。
- **世界模型要服务于决策。**
它不是单纯追求视觉好看，而是要正确模拟奖励、终止、物体交互和动作后果。
- **未来的 model-based RL 可能更像生成模型工程。**
关键问题会越来越像：如何 tokenization、如何建模长上下文、如何表达不确定性、如何把模型内部表示交给 policy 使用。

## 我对这条研究线的判断

我认为 IRIS 系列的长期价值不一定只体现在 Atari 或 Crafter 分数上，而在于它提示了一个方向：
如果我们能学到足够可靠的环境生成模型，那么强化学习可以减少大量真实试错。
这对机器人、自动驾驶、游戏 AI、交互式智能体都非常重要。

但我也不会过度乐观。
世界模型一旦学错，policy 会在错误世界里过拟合；
稀有事件如果没有进入数据，模型也不会凭空学会；
而现实世界的长时序、多对象、部分可观测和安全约束比 Atari/Crafter 难得多。

所以我对这两篇论文的评价是：

它们不是已经解决了通用智能体训练问题，而是清楚展示了一个很有前途的方向：用生成式世界模型把昂贵的真实试错转化为便宜的想象训练，并通过更聪明的 tokenization 让这件事变得可扩展。
# 最后总结

IRIS 的意义在于，它把视觉强化学习中的世界模型明确转化为：

$$
\text{离散视觉 token 的自回归序列建模问题}.
$$

这让 Transformer 能够进入 model-based RL 的核心位置。
IRIS 证明了这种方法在 Atari 100k 这种样本高效场景中很强。

$\Delta$-IRIS 的意义在于，它进一步指出：

$$
\text{真正限制扩展性的，不只是 Transformer 容量，而是 tokenization 是否高效。}
$$

通过让 token 描述变化而不是整帧，并用 I-token 提供当前状态摘要，
$\Delta$-IRIS 把世界模型做得更快、更适合复杂环境。

**一句话评价：**
IRIS 证明了 Transformer 可以做样本高效世界模型；
$\Delta$-IRIS 证明了更聪明的 tokenization 是让这条路线扩展到复杂环境的关键。
