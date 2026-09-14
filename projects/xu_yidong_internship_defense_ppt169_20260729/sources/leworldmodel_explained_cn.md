# LeWorldModel 论文精读讲义

*LeWorldModel: Stable End-to-End Joint-Embedding Predictive Architecture from Pixels*

面向人工智能入门学习者的中文讲解

2026 年 7 月 7 日

| 项目 | 内容 |
| --- | --- |
| 论文 | LeWorldModel: Stable End-to-End Joint-Embedding Predictive Architecture from Pixels |
| 作者 | Lucas Maes, Quentin Le Lidec, Damien Scieur, Yann LeCun, Randall Balestriero |
| 主题 | 从原始像素端到端训练稳定的 JEPA latent world model，并用于目标图像规划 |
| 本讲义目标 | 解释研究背景、动机、核心方法、实现细节、实验设置、实验结论和与 TD-MPC / TD-MPC2 的关系 |

## 一句话总览

> **核心理解：** LeWorldModel，简称 LeWM，想解决一个很朴素但很要命的问题：如果我们只让模型预测“下一帧的 latent 表示”，模型很容易把所有图像都编码成同一个向量，从而假装预测正确。LeWM 的做法是：一边训练模型预测下一步 latent，一边用 SIGReg 强迫 latent 分布接近标准高斯，让表示既可预测又不塌缩。训练好后，它像一个轻量脑内模拟器，可以在 latent 空间里用 CEM / MPC 搜索动作，让预测终点靠近目标图像的 latent。

用一个比喻来理解：

- 普通像素生成世界模型像“画家”：它要把未来画面尽量画出来。
- TD-MPC / TD-MPC2 像“带评分器的运动员”：它学习 latent dynamics，同时用 reward 和 Q function 判断动作长期好不好。
- DINO-WM 像“借别人地图的规划器”：它冻结一个预训练视觉模型，把世界投到 DINOv2 特征空间里规划。
- LeWM 像“自己学地图的规划器”：它从像素端到端学习自己的 latent 地图，但必须防止地图坍缩成一个点。SIGReg 就是防止地图坍缩的规则。

这篇论文的创新点可以概括成：

> **端到端、像素输入、无奖励、无重建、无预训练 encoder、无 EMA / stop-gradient，只用一个预测损失和一个高斯分布正则，训练一个稳定可规划的 latent world model。**

## 研究背景和动机

### 什么是 world model

world model 的核心问题是：

**如果我现在看到这个世界，并做一个动作，未来会发生什么？**

在控制任务中，智能体每一步看到观测 $o_t$，执行动作 $a_t$，环境变成新观测 $o_{t+1}$。如果模型能预测：

$$
\hat{o}_{t+1} \approx o_{t+1},
$$

或更常见地预测某个 latent 表示：

$$
\hat{z}_{t+1} \approx z_{t+1},
$$

那么智能体就可以在脑内试动作。比如：

1. 假设我向左推。
2. world model 想象未来状态。
3. 如果未来状态更接近目标，就保留这个动作。
4. 如果未来状态变糟，就换一个动作。

这就是“在想象空间里规划”。对机器人来说，这非常重要，因为真实试错很贵。机械臂撞一次、机器人摔一次、真实环境采集一次数据，都可能耗时或有风险。

### 为什么要在 latent 空间里预测

直接预测像素很直观，但很难。图像里有太多细节：阴影、纹理、背景、光照、相机噪声。控制任务真正关心的往往不是每个像素，而是：

- 物体在哪里；
- 物体朝向是什么；
- 手臂末端在哪里；
- 推一下以后物体会怎么动；
- 当前状态和目标状态之间差多少。

所以很多现代 world model 不预测像素，而是先把图像压缩成 latent：

$$
z_t = enc_\theta(o_t),
$$

然后预测：

$$
\hat{z}_{t+1} = pred_\phi(z_t, a_t).
$$

这就像你不需要记住城市每块砖的颜色，只需要一张路线图。路线图不等于城市照片，但足够用来导航。

### JEPA 是什么

JEPA 是 Joint Embedding Predictive Architecture，可以翻译成“联合嵌入预测架构”。它的基本思想是：

1. 把当前观测 $o_t$ 编码成 latent $z_t$；
2. 把未来观测 $o_{t+1}$ 编码成 latent $z_{t+1}$；
3. 让 predictor 根据当前 latent 和动作预测未来 latent；
4. 不要求模型重建像素，只要求 latent 预测准确。

对应公式是：

$$
z_t = enc_\theta(o_t), \quad z_{t+1}=enc_\theta(o_{t+1}),
$$

$$
\hat{z}_{t+1}=pred_\phi(z_t,a_t),
$$

$$
\mathcal{L}_{pred}=\|\hat{z}_{t+1}-z_{t+1}\|_2^2.
$$

JEPA 的好处是简洁：不需要像素级 decoder，不需要生成清晰图像，不需要为光照纹理浪费建模能力。

### JEPA 最大的问题：representation collapse

只用上面的预测损失会出大问题：模型可能学会一个“作弊答案”。

假设 encoder 对所有输入都输出同一个向量 $c$：

$$
enc_\theta(o)=c,\quad \forall o.
$$

然后 predictor 也永远输出 $c$：

$$
pred_\phi(c,a)=c.
$$

那么预测损失是多少？

$$
\mathcal{L}_{pred}=\|c-c\|_2^2=0.
$$

损失完美，但模型什么都没学到。所有图片都被压成同一个点，规划时完全分不清“手臂在左边”和“手臂在右边”。这就是 collapse。

可以把 collapse 想成考试时学生把所有题都回答成“同一个答案”。如果评分规则只看“预测答案和目标答案是否相同”，而目标答案也被学生自己写成同一个东西，那学生就能骗过评分系统。

因此 JEPA 要成功，必须解决：

> **怎样让 latent 既容易预测，又不能塌成常数？**

### 过去方法为什么还不够

已有方法大致有几条路线。

第一类是使用 EMA target encoder 和 stop-gradient。I-JEPA、V-JEPA 等常用这种策略。它的直觉是：让一个慢速更新的“老师网络”提供目标，学生去追老师，避免自己追自己。但论文认为这些技巧有启发式成分，不一定对应一个明确的单一优化目标。

第二类是冻结预训练视觉 encoder，例如 DINO-WM。这样不会 collapse，因为 encoder 已经被大规模数据训练好了，不会被当前世界模型训练拖垮。但代价是：representation 被预训练模型限制，不能完全为当前环境端到端适配。

第三类是像 PLDM 一样端到端训练，但用 VICReg 风格的多项正则防 collapse。问题是损失项很多，超参数多，训练容易不稳。论文强调 PLDM 需要多项损失和多个系数，而 LeWM 把有效调参量压到一个主要系数 $\lambda$。

第四类是 TD-MPC / TD-MPC2 这种任务导向模型控制。它们学习 latent dynamics，但训练目标包括 reward、value、Q function 等任务相关信号。这对强化学习控制很强，但不属于完全 reward-free、task-agnostic 的 JEPA 设置。

LeWM 想要的组合非常野心勃勃：

- 从 raw pixels 学；
- encoder 和 predictor 端到端训练；
- 不使用预训练视觉模型；
- 不使用像素重建；
- 不使用 reward；
- 不使用 EMA 或 stop-gradient；
- 防 collapse 有明确分布匹配解释；
- 还能用于 latent planning。

## 核心贡献和方法

### LeWM 要解决的核心问题

论文要解决的不是“如何生成漂亮视频”，而是：

> **如何从离线像素轨迹中，稳定学到一个可预测、可规划、不塌缩的 latent world model？**

训练数据是一批离线轨迹：

$$
\mathcal{D}=\{(o_{1:T},a_{1:T})\},
$$

其中 $o_t$ 是原始像素图像，$a_t$ 是动作。注意这里没有奖励：

$$
r_t \text{ 不参与训练。}
$$

这点和 TD-MPC / TD-MPC2 非常不同。TD-MPC / TD-MPC2 要学习 reward model 和 Q function；LeWM 只学习世界如何变化。

### 整体架构

LeWM 只有两个核心模块：

```text
原始图像 o_t
   |
   v
Encoder enc_theta
   |
   v
latent z_t
   |
   + action a_t
   v
Predictor pred_phi
   |
   v
预测下一 latent z_hat_{t+1}
```

训练时，真实下一帧也经过同一个 encoder：

```text
下一帧图像 o_{t+1}
   |
   v
Encoder enc_theta
   |
   v
目标 latent z_{t+1}
```

然后优化两件事：

1. 预测要准：$\hat{z}_{t+1}$ 接近 $z_{t+1}$；
2. 表示不能塌：所有 latent 的分布要接近标准高斯。

最终损失是：

$$
\mathcal{L}_{LeWM}=\mathcal{L}_{pred}+\lambda\,SIGReg(Z).
$$

### 模块一：encoder

encoder 把像素图像变成低维 latent：

$$
z_t=enc_\theta(o_t).
$$

论文默认使用 ViT-Tiny：

| 组件 | 设置 |
| --- | --- |
| encoder 类型 | Vision Transformer Tiny |
| 参数规模 | 约 5M |
| patch size | 14 |
| 层数 | 12 |
| attention heads | 3 |
| hidden dimension | 192 |
| 输出表示 | 最后一层 CLS token，再接 1 层 MLP + BatchNorm 投影 |

为什么要在 CLS token 后面再加 projection？论文指出 ViT 最后一层有 LayerNorm，而 SIGReg 要控制 embedding 的分布。如果直接在 LayerNorm 后优化高斯正则，效果会受影响；投影层提供一个更适合分布匹配的表示空间。

### 模块二：predictor

predictor 学 latent dynamics：

$$
\hat{z}_{t+1}=pred_\phi(z_t,a_t).
$$

默认 predictor 是一个 Transformer：

| 组件 | 设置 |
| --- | --- |
| predictor 类型 | Transformer / ViT-S 风格 backbone |
| 参数规模 | 约 10M |
| 层数 | 6 |
| attention heads | 16 |
| dropout | 0.1 |
| 动作注入 | Adaptive Layer Normalization, AdaLN |
| 时间建模 | causal mask，自回归预测 |

动作通过 AdaLN 注入每一层。可以把 AdaLN 理解为：动作不是简单拼到输入后面，而是在每层里调节特征的尺度和偏置，让模型知道“当前这个动作会怎样改变世界”。

AdaLN 参数初始化为 0。这个设计很稳：一开始 predictor 主要学习视觉 latent 的基本结构，动作影响逐渐进入训练，避免初期动作条件扰动太强。

### 预测损失

预测损失是 teacher forcing 的下一 embedding 预测：

$$
\mathcal{L}_{pred}
=
\|\hat{z}_{t+1}-z_{t+1}\|_2^2,
\quad
\hat{z}_{t+1}=pred_\phi(z_t,a_t).
$$

这个损失负责让 latent 有动力学含义：如果动作相同、状态相似，预测未来 latent 应该相似；如果动作导致物体位置变化，future latent 也应该变化。

但是只用这个损失会 collapse，所以需要 SIGReg。

### SIGReg：防止 latent collapse 的关键

SIGReg 全称 Sketched-Isotropic-Gaussian Regularizer。它要求 latent embedding 的整体分布接近标准高斯：

$$
Z \sim \mathcal{N}(0,I).
$$

直观上，这相当于告诉 encoder：

> 你不能把所有图像都塞进同一个点。你必须把不同状态分散到一个有体积、有方向、有变化的空间里。

如果所有样本都映射成同一个常数，分布就是一个点质量，不可能像标准高斯，因此会被 SIGReg 惩罚。

#### 为什么不用直接高维检验

设一批 latent 为：

$$
Z \in \mathbb{R}^{N \times B \times d},
$$

其中 $N$ 是历史长度，$B$ 是 batch size，$d$ 是 embedding dimension。

直接判断高维分布是否等于 $\mathcal{N}(0,I)$ 很难。SIGReg 用一个聪明办法：

1. 随机采样 $M$ 个单位方向 $u^{(m)}\in S^{d-1}$；
2. 把高维 latent 投影到这些方向上；
3. 在每个一维投影上做 normality test；
4. 把这些一维测试结果平均。

投影为：

$$
h^{(m)} = Z u^{(m)}.
$$

SIGReg 定义为：

$$
SIGReg(Z)
=
\frac{1}{M}\sum_{m=1}^{M}T(h^{(m)}),
$$

其中 $T(\cdot)$ 是一维 Epps-Pulley 正态性检验统计量。

论文背后的数学依据是 Cramer-Wold 定理：如果所有一维投影都匹配，那么联合分布也匹配。换句话说：

$$
SIGReg(Z)\rightarrow 0
\quad \Longleftrightarrow \quad
P_Z \rightarrow \mathcal{N}(0,I).
$$

这就是 SIGReg 的优雅之处：它不用在高维空间里直接做复杂分布匹配，而是用很多一维影子来约束整体形状。

#### SIGReg 和 SimNorm 的直觉对比

TD-MPC2 使用 SimNorm 约束 latent。SimNorm 像是把 latent 拆成很多组，每组做 softmax，让表示落在多个“可组合槽位”里，从而防止数值乱跑和梯度爆炸。

LeWM 的 SIGReg 不把 latent 分槽，而是约束整体分布像标准高斯。可以这样理解：

- SimNorm 像给 latent 装很多小格子，每组只能在有限槽位中软选择；
- SIGReg 像要求全班学生的座位分布均匀、有方差、别挤成一团；
- 二者都在约束 latent 空间，但目的和数学形式不同。

### 完整训练目标

LeWM 的完整目标是：

$$
\mathcal{L}_{LeWM}
=
\mathcal{L}_{pred}
+\lambda SIGReg(Z).
$$

默认设置：

| 超参数 | 默认值 | 含义 |
| --- | --- | --- |
| $M$ | 1024 | SIGReg 的随机投影方向数 |
| $\lambda$ | 0.1 | SIGReg 正则权重 |
| 有效需要调的超参数 | 主要是 $\lambda$ | 论文认为 $M$ 对下游表现影响很小 |

论文强调，和 PLDM 的多项损失相比，LeWM 只有两个主要损失项，并且有效调参主要集中在 $\lambda$。这使调参从多维网格搜索变成接近一维搜索。

### 测试时规划

训练好 LeWM 后，可以用它做目标图像规划。给定初始观测 $o_1$ 和目标观测 $o_g$：

$$
z_1=enc_\theta(o_1), \quad z_g=enc_\theta(o_g).
$$

给定候选动作序列 $a_{1:H}$，模型自回归 rollout：

$$
\hat{z}_{t+1}=pred_\phi(\hat{z}_t,a_t),
\quad
\hat{z}_1=enc_\theta(o_1).
$$

终点 cost 是：

$$
C(\hat{z}_H)=\|\hat{z}_H-z_g\|_2^2.
$$

规划目标：

$$
a^*_{1:H}
=
\arg\min_{a_{1:H}} C(\hat{z}_H).
$$

也就是说，LeWM 不问“奖励最大是多少”，而问：

> 如果我执行这串动作，想象中的终点 latent 会不会靠近目标图像 latent？

### CEM 和 MPC

论文用 Cross-Entropy Method，简称 CEM，优化动作序列。CEM 的直觉是：

1. 从一个高斯分布里采样很多动作序列；
2. 用 LeWM 在 latent 空间 rollout 每条序列；
3. 计算每条序列的终点 cost；
4. 选 cost 最低的 top-K elite；
5. 用 elite 的均值和方差更新采样分布；
6. 重复多轮；
7. 执行得到的动作，再根据新观测重新规划。

实验中的规划设置：

| 项目 | 设置 |
| --- | --- |
| CEM samples | 300 条候选动作序列 |
| elites | top 30 |
| PushT CEM iterations | 30 |
| 其他环境 CEM iterations | 10 |
| frame-skip | 5 |
| planning horizon | 5 个模型步，对应 25 个环境步 |
| 执行策略 | receding-horizon MPC |

CEM 不是万能的。它是零阶优化，不需要梯度，适合非凸动作搜索；但高维动作空间会变难，因为采样空间会快速膨胀。论文附录也说明 CEM 没有全局最优保证。

## 具体实现讲解

### 训练流程伪代码

下面是帮助理解的 PyTorch 风格伪代码。它不是逐字复现代码，而是保留论文训练逻辑。

```python
def lewm_train_step(obs, actions, encoder, predictor, optimizer, lambd=0.1):
    """
    obs:     [B, T, C, H, W], raw pixel frames
    actions: [B, T, A], action blocks
    """
    # 1. Encode all frames into latent embeddings.
    # Unlike DINO-WM, encoder is trainable here.
    z = encoder(obs)  # [B, T, D]

    # 2. Predict next embeddings from current embeddings and actions.
    z_pred = predictor(z[:, :-1], actions[:, :-1])  # [B, T-1, D]
    z_target = z[:, 1:]                             # [B, T-1, D]

    # 3. Prediction loss.
    pred_loss = ((z_pred - z_target) ** 2).mean()

    # 4. Anti-collapse regularization.
    sigreg_loss = SIGReg(z)

    # 5. Joint end-to-end optimization.
    loss = pred_loss + lambd * sigreg_loss
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return loss.item()
```

注意：这里 encoder 没有 `detach`，没有 stop-gradient，没有 EMA teacher。梯度会同时更新 encoder 和 predictor。这正是 LeWM 的端到端特征。

### SIGReg 伪代码

真实 Epps-Pulley test statistic 有积分和经验特征函数。为了帮助理解，可以把 SIGReg 伪代码写成：

```python
def SIGReg(z, num_proj=1024):
    """
    z: [B, T, D] latent embeddings
    return: scalar regularization loss
    """
    x = z.reshape(-1, z.shape[-1])  # [B*T, D]
    d = x.shape[-1]

    # sample random unit directions
    u = torch.randn(num_proj, d, device=x.device)
    u = u / (u.norm(dim=-1, keepdim=True) + 1e-8)

    # one-dimensional projections
    h = x @ u.T  # [B*T, num_proj]

    # in the real implementation, use Epps-Pulley normality statistics
    # here we show the intuition: each projection should look like N(0, 1)
    mean_loss = (h.mean(dim=0) ** 2).mean()
    var_loss = ((h.var(dim=0) - 1.0) ** 2).mean()

    return mean_loss + var_loss
```

这个简化版只检查均值和方差，不等价于论文的 Epps-Pulley 检验，但直觉一致：投影后的分布不能挤成一个点，应该接近均值 0、方差 1 的高斯。

### CEM 规划伪代码

```python
@torch.no_grad()
def plan_with_cem(o_start, o_goal, encoder, predictor,
                  horizon=5, num_samples=300, num_elites=30,
                  num_iters=30, action_dim=2):
    z0 = encoder(o_start)
    zg = encoder(o_goal)

    mu = torch.zeros(horizon, action_dim)
    sigma = torch.ones(horizon, action_dim)

    for _ in range(num_iters):
        actions = mu + sigma * torch.randn(num_samples, horizon, action_dim)

        z = z0.repeat(num_samples, 1)
        for t in range(horizon):
            z = predictor.one_step(z, actions[:, t])

        cost = ((z - zg) ** 2).mean(dim=-1)
        elite_idx = torch.topk(cost, k=num_elites, largest=False).indices
        elite_actions = actions[elite_idx]

        mu = elite_actions.mean(dim=0)
        sigma = elite_actions.std(dim=0).clamp_min(1e-4)

    return mu  # MPC can execute the first block, then replan
```

这段规划代码体现了 LeWM 的控制思想：不训练一个固定 policy，而是在测试时用 world model 临时优化动作序列。

### 和 TD-MPC / TD-MPC2 的方法对比

TD-MPC / TD-MPC2 的典型规划评分是：

$$
G(\tau)
=
\sum_{i=0}^{H-1}\gamma^i R_\theta(z_i,a_i)
+\gamma^H Q_\theta(z_H,a_H).
$$

也就是：

- reward model 负责短期行为好不好；
- Q function 负责规划终点之后的长期价值；
- policy prior 或 actor 可以帮助规划器提出更好的动作候选；
- TD-MPC2 还用 SimNorm、离散 reward / value 回归、Q ensemble、EMA target 等稳定训练。

LeWM 的规划目标则是：

$$
C(\tau)=\|\hat{z}_H-z_g\|_2^2.
$$

它没有 reward model、没有 Q function、没有 actor、没有 terminal value。它只需要目标图像 $o_g$。

| 方面 | TD-MPC / TD-MPC2 | LeWorldModel |
| --- | --- | --- |
| 训练信号 | reward、value、latent dynamics | next latent prediction + SIGReg |
| 是否需要奖励 | 需要或高度依赖 reward / value 学习 | 不需要 |
| 是否从像素端到端学 encoder | TD-MPC 常用状态或任务导向表示，TD-MPC2 重点在控制稳定性 | 是，从 raw pixels 训练 encoder |
| 防 latent 不稳定 | SimNorm、EMA target、Q ensemble、离散回归等 | SIGReg 高斯分布正则 |
| 规划目标 | 最大化 reward + terminal Q | 最小化终点 latent 与目标 latent 的距离 |
| 任务属性 | 任务导向控制算法 | 更偏 reward-free、task-agnostic world model |
| 适合场景 | 有奖励、有交互或 replay buffer 的连续控制 | 有离线动作轨迹和目标图像的 latent planning |

> **直观对比：** TD-MPC2 像“会给动作打长期分数的控制专家”；LeWM 像“会从图像自己学物理地图的想象器”。前者擅长 reward-driven control，后者强调 reward-free latent world modeling。

## 实验设置和结果

### 实验问题

论文实验主要回答四个问题：

1. LeWM 能不能在不同 2D / 3D 连续控制任务上做目标图像规划？
2. LeWM 的端到端训练是否比 PLDM 更稳定？
3. LeWM 是否能接近或超过 DINO-WM，同时规划更快？
4. LeWM latent 是否真的包含物理结构，而不是只服务于表面规划指标？

### 环境和数据集

| 环境 | 任务类型 | 数据规模 | 数据来源 / 策略 | 训练 |
| --- | --- | --- | --- | --- |
| TwoRoom | 2D 导航，穿过门到另一个房间目标 | 10,000 episodes，平均 92 steps | noisy heuristic policy | 每个 world model 10 epochs |
| PushT | 2D 推 T 形块到目标姿态 | 20,000 expert episodes，平均 196 steps | expert episodes | 每个 world model 10 epochs |
| OGBench-Cube | 3D 机械臂移动 cube 到目标位置 | 10,000 episodes，每条 200 steps | benchmark heuristic | 每个 world model 10 epochs |
| Reacher | 2D 双关节机械臂到目标构型 | 10,000 episodes，每条 200 steps | SAC policy | 每个 world model 10 epochs |

所有环境都是连续动作空间。输入是原始像素，规划目标由目标观测图像给出。

### Baselines

论文比较了：

| 方法 | 简要说明 |
| --- | --- |
| LeWM | 本文方法，端到端像素 JEPA，SIGReg 防 collapse |
| DINO-WM | 冻结 DINOv2 encoder 的 latent world model |
| DINO-WM + prop | DINO-WM 使用额外 proprioception 的版本 |
| PLDM | 端到端 JEPA world model，但使用 VICReg 风格多项正则 |
| GCBC | goal-conditioned behavioral cloning |
| GCIVL / GCIQL | goal-conditioned offline RL |
| Random | 随机策略 |

### 主结果：规划成功率

| 方法 | TwoRoom SR | Reacher SR | PushT SR | OGBench-Cube SR |
| --- | ---: | ---: | ---: | ---: |
| LeWM | 87 | 86 | 96 | 74 |
| DINO-WM + prop | 100 | - | 92 | - |
| PLDM | 97 | 78 | 78 | 65 |
| DINO-WM | 100 | 79 | 74 | 86 |
| GCBC | 100 | - | 75 | 84 |
| GCIQL | 100 | - | 20 | 64 |
| GCIVL | 100 | - | 33 | 56 |
| Random | 0 | 10 | 2 | 48 |

结论要分任务看：

- TwoRoom 很简单，低维且数据多样性低。LeWM 只有 87，不如 PLDM / DINO-WM / GCBC 等 100。论文解释可能是 SIGReg 要把 latent 推向高维高斯，但 TwoRoom 的真实内在维度很低，高斯约束反而可能不合适。
- Reacher 上 LeWM 86，高于 PLDM 78 和 DINO-WM 79。
- PushT 是关键结果：LeWM 96，高于 PLDM 78、DINO-WM 74，也高于带 proprioception 的 DINO-WM 92。说明 LeWM 从像素学到的 latent 能捕获 agent 和 block 的关键物理量。
- OGBench-Cube 上 DINO-WM 86 高于 LeWM 74。论文认为可能因为 3D 场景视觉复杂度更高，端到端训练 encoder 更难；预训练 DINOv2 视觉先验在这里有优势。

这组结果的核心不是“LeWM 每个任务都第一”，而是：

> LeWM 在不使用预训练 encoder、不使用 reward、不使用 reconstruction 的情况下，能在复杂任务上达到强竞争力，并在 PushT 上显著超过其他 JEPA world model。

### 规划速度和固定计算预算

论文特别强调效率：

| 比较 | DINO-WM | LeWM |
| --- | ---: | ---: |
| Full planning time | 47 s | 0.98 s |
| PushT fixed FLOPs SR | 13 | 90 |
| OGBench-Cube fixed FLOPs SR | 48 | 74 |

LeWM 最多可达到约 48x 更快规划。原因是 LeWM 的 latent 更紧凑，编码 token 数比 DINO-WM 少约 200x。DINO-WM 用 DINOv2 patch token，表示更重；LeWM 使用 compact CLS latent，规划 rollout 更便宜。

### 物理量 probing：latent 里有没有物理信息

论文不只看规划成功率，还问：latent 是否能恢复真实物理量？

在 PushT 上，研究者训练 linear probe 和 MLP probe，从 latent 预测：

- agent location；
- block location；
- block angle。

| Property | Model | Linear MSE ↓ | Linear r ↑ | MLP MSE ↓ | MLP r ↑ |
| --- | --- | ---: | ---: | ---: | ---: |
| Agent Location | DINO-WM | 1.888 ± 0.500 | 0.977 | 0.003 ± 0.022 | 0.999 |
| Agent Location | PLDM | 0.090 ± 0.311 | 0.955 | 0.014 ± 0.119 | 0.993 |
| Agent Location | LeWM | 0.052 ± 0.149 | 0.974 | 0.004 ± 0.056 | 0.998 |
| Block Location | DINO-WM | 0.006 ± 0.007 | 0.997 | 0.002 ± 0.003 | 0.999 |
| Block Location | PLDM | 0.122 ± 0.341 | 0.938 | 0.011 ± 0.066 | 0.994 |
| Block Location | LeWM | 0.029 ± 0.073 | 0.986 | 0.001 ± 0.006 | 0.999 |
| Block Angle | DINO-WM | 0.050 ± 0.101 | 0.979 | 0.009 ± 0.052 | 0.995 |
| Block Angle | PLDM | 0.446 ± 0.625 | 0.745 | 0.056 ± 0.184 | 0.972 |
| Block Angle | LeWM | 0.187 ± 0.359 | 0.902 | 0.021 ± 0.139 | 0.990 |

结论：

- LeWM 明显强于 PLDM，说明它的 latent 更物理、更可解码。
- DINO-WM 在某些物理量上非常强，可能来自 DINOv2 的大规模预训练视觉先验。
- LeWM 即使没有预训练，也能学出可用于恢复位置和角度的表示。

### violation-of-expectation：模型是否能发现不物理事件

论文还做了 violation-of-expectation，简称 VoE。这个想法来自发展心理学：如果婴儿看到“不可能事件”，例如物体瞬移，会表现出惊讶。world model 也可以用 prediction error 来度量 surprise：

$$
surprise_t = \|\hat{z}_{t+1}-z_{t+1}\|_2^2.
$$

实验构造三种轨迹：

1. 正常轨迹；
2. 视觉扰动：物体颜色突然变化；
3. 物理扰动：物体瞬移到随机位置。

结果：

- 物理瞬移会产生明显 surprise spike；
- 正常轨迹保持低 surprise；
- 颜色变化的 surprise 较弱，并且统计上不显著；
- 物理扰动在三个环境中都有显著提升，paired t-test 显示 $p<0.01$。

这说明 LeWM 更敏感于“物理连续性被破坏”，而不是只对颜色这种视觉变化敏感。换句话说，它学到的 latent dynamics 不只是表面纹理，而包含一些物理规律。

### 训练稳定性和消融实验

#### 训练方差

PushT 上 3 个随机种子的成功率：

| Model | PushT SR |
| --- | ---: |
| DINO-WM | 92.0 ± 1.63 |
| PLDM | 78.0 ± 5.0 |
| LeWM | 96.0 ± 2.83 |

PLDM 方差更大，LeWM 更稳定。

#### predictor size

| Predictor size | PushT SR |
| --- | ---: |
| tiny | 80.67 ± 6.54 |
| small | 96.0 ± 2.83 |
| base | 86.7 ± 3.06 |

ViT-S / small 最好。太小容量不足，太大可能优化更难或过拟合。

#### decoder loss

| 设置 | PushT SR |
| --- | ---: |
| LeWM without decoder loss | 96.0 ± 2.83 |
| LeWM with decoder loss | 86.0 ± 7.54 |

这和 DINO-WM 的结论相似：像素重建不一定帮助控制。重建可能鼓励模型记住视觉细节，但规划更需要物体位置、接触关系和动力学。

#### encoder architecture

| Encoder | PushT SR |
| --- | ---: |
| LeWM ViT | 96.0 ± 2.83 |
| LeWM ResNet-18 | 94.0 ± 3.27 |

说明 LeWM 不完全依赖特定 encoder 架构，尽管 ViT 略好。

#### predictor dropout

| Dropout | PushT SR |
| --- | ---: |
| 0.0 | 78 ± 6.54 |
| 0.1 | 96.0 ± 2.83 |
| 0.2 | 85.33 ± 5.74 |
| 0.5 | 66.67 ± 4.11 |

适度 dropout 最好。没有 dropout 泛化差，过强 dropout 又破坏动力学建模。

#### 规划优化器

| Solver | LeWM SR | PLDM SR |
| --- | ---: | ---: |
| CEM | 96.0 ± 2.83 | 78.0 ± 5.0 |
| SGD | 26 ± 4.32 | 4.67 ± 0.06 |
| RMSProp | 67.33 ± 2.49 | 49.33 ± 8.26 |
| Adam | 84 ± 7.12 | 80 ± 3.27 |

CEM 最好，说明动作规划问题高度非凸，采样式优化比直接梯度法更稳。

#### SIGReg 参数

论文发现：

- random projections 数量对下游控制影响很小；
- integration knots 数量影响也不大；
- embedding dimension 太小会明显变差，超过约 184 后收益饱和；
- $\lambda\in[0.01,0.2]$ 时 PushT SR 都在 80 以上；
- $\lambda=0.5$ 时性能明显下降，因为正则太强，压过了动力学预测。

这支持作者的说法：LeWM 的有效调参主要是一个 $\lambda$，比多损失项 JEPA 更容易稳定训练。

## 这篇文章的创新点分析

### 创新一：把 JEPA world model 做到真正端到端

DINO-WM 很强，但它冻结 DINOv2 encoder。冻结 encoder 的好处是避免 collapse，坏处是表示能力被预训练模型限制。LeWM 的野心是：encoder 不冻结，直接从任务像素数据端到端学。

这更难，因为 encoder 会被预测损失牵着走，一不小心就 collapse。LeWM 的贡献是用 SIGReg 让端到端训练变得稳定。

### 创新二：用分布匹配防 collapse，而不是堆很多技巧

很多防 collapse 方法像“给模型打补丁”：EMA、stop-gradient、variance loss、covariance loss、temporal loss、多项权重调节。LeWM 更像给出一个简单原则：

> latent 整体分布应该像 $\mathcal{N}(0,I)$。

这个原则很直观：

- 有均值控制，不让表示整体漂移；
- 有方差控制，不让所有样本挤在一起；
- 有方向覆盖，不让信息只藏在少数维度；
- 用随机投影和正态性检验，让高维约束可计算。

### 创新三：保留 reward-free 和 reconstruction-free

LeWM 不学 reward，也不学 value，也不重建像素。它只学：

$$
(z_t,a_t)\rightarrow z_{t+1}.
$$

这使它更接近“任务无关世界模型”。当目标以图像给出时，它可以直接用 latent goal matching 来规划。

### 创新四：速度优势来自 compact latent

DINO-WM 的 patch latent 很有空间结构，但 token 多，规划时每条候选动作都要 rollout 高维 token 表示。LeWM 使用 compact CLS latent，规划 rollout 便宜得多。

所以 LeWM 在 full planning time 上从 DINO-WM 的 47 秒降到 0.98 秒。这里的意义很大：world model 如果要测试时规划，推理速度本身就是方法能力的一部分。

### 需要谨慎理解的地方

LeWM 不是在所有环境都打败 DINO-WM，也不是证明预训练视觉模型没用。OGBench-Cube 上 DINO-WM 仍然更好，说明复杂 3D 视觉场景中，大规模预训练视觉先验依然有价值。

LeWM 的真正价值在于：

> 它证明了不依赖预训练 encoder，也可以稳定训练 reward-free、reconstruction-free、end-to-end JEPA world model，并且在多个控制任务上达到强竞争力。

## 给初学者的学习路线

如果你刚入门，可以按这个顺序理解：

1. 先理解 world model：模型不是直接输出动作，而是预测动作后的世界变化。
2. 再理解 latent world model：不预测像素，而预测压缩后的状态表示。
3. 再理解 JEPA：用当前 latent 预测未来 latent，不做像素重建。
4. 再理解 collapse：如果没有约束，encoder 可能把所有图像映射成同一个向量。
5. 再理解 SIGReg：要求 latent 分布接近高斯，防止所有样本挤在一起。
6. 最后理解 CEM / MPC：测试时在 latent 空间里试动作序列，让预测终点接近目标 latent。

最关键的公式只有三个：

预测：

$$
\hat{z}_{t+1}=pred_\phi(z_t,a_t).
$$

训练：

$$
\mathcal{L}_{LeWM}
=
\|\hat{z}_{t+1}-z_{t+1}\|_2^2
+\lambda SIGReg(Z).
$$

规划：

$$
a^*_{1:H}
=
\arg\min_{a_{1:H}}
\|\hat{z}_H-z_g\|_2^2.
$$

## 最后总结

LeWorldModel 的研究动机是解决端到端 JEPA world model 的稳定训练问题。只用 prediction loss 会 collapse；使用预训练 encoder 又失去端到端适应能力；使用多项正则又带来复杂调参。LeWM 用 SIGReg 这个高斯分布正则，让 latent 既能预测未来，又保持足够分散，从而避免塌缩。

方法上，LeWM 使用一个 ViT encoder 从像素得到 compact latent，用 Transformer predictor 根据 latent 和动作预测下一 latent。训练目标只有：

$$
\mathcal{L}_{pred}+\lambda SIGReg.
$$

测试时，LeWM 用目标图像的 latent 作为目标，在 latent 空间中通过 CEM / MPC 优化动作序列。

实验上，LeWM 在 PushT 和 Reacher 上超过 PLDM 与 DINO-WM，在 OGBench-Cube 上低于 DINO-WM 但仍有竞争力，在 TwoRoom 上因为任务内在维度太低而表现不如其他方法。它的规划速度显著快于 DINO-WM，并且 probing 与 VoE 实验证明 latent 中包含物理结构和对物理异常的敏感性。

> **一句话评价：** LeWM 的核心贡献不是提出一个更复杂的世界模型，而是把端到端 JEPA world model 训练变简单、稳定、可规划：用 prediction loss 学动力学，用 SIGReg 防 collapse，用 CEM / MPC 在 compact latent 空间里做目标图像规划。
