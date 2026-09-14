# DINO-WM 论文精读讲义

*World Models on Pre-trained Visual Features enable Zero-shot Planning*

面向人工智能入门学习者的中文讲解

2026 年 7 月 7 日

| 项目 | 内容 |
| --- | --- |
| 主论文 | Gaoyue Zhou, Hengkai Pan, Yann LeCun, Lerrel Pinto, ICML 2025 |
| 论文主题 | 用预训练视觉 patch 特征学习离线世界模型，并在测试时零样本规划 |
| 本讲义目标 | 解释背景动机、核心方法、实现细节、实验设置与结论 |

## 一句话总览

DINO-WM 的核心思想可以压缩成一句话：

> **核心理解：** 先用 DINOv2 把图像变成一组空间 patch 特征，再训练一个动作条件的 Transformer 在这个特征空间里预测未来；测试时给一张目标图像，直接在 latent 空间里用 MPC/CEM 搜索动作，让预测未来的 latent 靠近目标图像的 latent。

如果用新人友好的类比，DINO-WM 像是给机器人装了一个“脑内沙盘”：

- 真实世界是一段视频。机器人看到当前画面，也知道自己将要尝试的动作。
- DINOv2 像一个已经见过很多图片的视觉老师，先把画面拆成很多“有意义的小格子”：哪里是墙，哪里是物体，哪里可能是手臂、绳子、颗粒。
- 世界模型不去画出未来图片，而是在这些小格子的语义特征上预测未来。
- 测试时目标也是一张图片。机器人不断在脑内试动作：如果这样推、那样转，未来特征会不会接近目标特征？
- 最后只执行当前最靠谱的第一步，下一步看到新画面再重新规划。

这篇论文最重要的不是“又发明了一种全新的规划器”。MPC 和 CEM 本来就是经典方法。它真正有意思的地方是：**把一个预训练视觉基础模型的 patch 表示变成世界模型的状态空间，让离线数据训练出来的模型可以不依赖奖励、不依赖专家示范、不依赖任务标签，也能在测试时为新目标做规划。**

## 研究背景和动机

### 什么是世界模型

世界模型，英文是 world model。它回答的问题是：

**如果我现在看到这个世界，并且接下来做这些动作，未来会发生什么？**

在控制和强化学习里，我们通常把环境写成一个决策过程。如果观测是图像，环境可以被看成部分可观测马尔可夫决策过程：

$$
  \mathcal{M} = (\mathcal{O}, \mathcal{A}, p),
$$

其中：

- $\mathcal{O}$ 是观测空间，例如 RGB 图像；
- $\mathcal{A}$ 是动作空间，例如二维小球的力、机械臂关节速度、推杆位移；
- $p(o_{t+1}\mid o_{\le t}, a_{\le t})$ 是环境动力学，也就是过去观测和动作如何决定未来观测。

如果我们真的学到了这个转移规律，就可以在脑内做规划：

$$
  o_t, a_t, a_{t+1}, \ldots   \Longrightarrow  
  \hat{o}_{t+1}, \hat{o}_{t+2}, \ldots
$$

然后选一串最可能达成目标的动作。

这件事在机器人和具身智能中非常重要。因为机器人不是只做静态识别，而是要主动改变世界。例如：

- 在迷宫里走到目标位置；
- 用推杆把 T 形物体推到目标姿态；
- 用机械臂把绳子挪到目标形状；
- 把散落颗粒聚成一个方块。

这些任务都要求模型理解“动作会如何改变画面”。这比普通图像分类难得多。

### 为什么只学一个策略不够

近几年 imitation learning 和 reinforcement learning 已经能学到很强的策略。策略可以理解为：

$$
  a_t = \pi(o_t),
$$

也就是“看到当前观测，直接输出动作”。

这种 feed-forward policy 的好处是部署时很快，但它有一个根本问题：**训练结束后，它基本已经把可执行的任务解法固定在参数里了。** 如果测试时出现一个训练中没见过的目标、环境布局或物体形状，它往往不会主动思考“我现在可以怎样一步步达到这个新目标”。

可以把它类比成背题：

- 纯策略方法像背了很多题的学生。见过相似题，就答得很快。
- 世界模型加规划像会推理的学生。即使题目没见过，也能用规则在草稿纸上推演。

DINO-WM 的出发点正是：与其指望训练阶段学会所有任务，不如训练一个通用的未来预测模型，然后在测试时针对当前目标做临时优化。

### 在线世界模型的局限

很多强大的世界模型方法是在在线强化学习里训练的。典型流程是：

1. 当前策略和环境交互，收集数据；
2. 用数据更新世界模型；
3. 用世界模型想象未来，训练更好的策略；
4. 新策略继续收集更好的数据。

Dreamer 系列、TD-MPC 系列都属于这条大路线的一部分。它的优点是数据会围绕当前任务越来越有用。但问题也很明显：

- 需要不断访问环境，真实机器人上代价很高；
- 学到的模型通常覆盖当前任务和当前策略访问过的状态；
- 换一个任务，可能要重新收集数据或重新训练；
- 很多方法使用 reward、discount、termination 等任务信息，因此模型本身带有任务偏好。

也就是说，在线世界模型很适合“为一个任务不断变强”，但不一定适合“离线学一个任务无关的通用预测器”。

### 离线世界模型为什么困难

离线设置更接近 DINO-WM 想解决的问题。我们先收集一批轨迹：

$$
  \mathcal{D} = \{(o_t, a_t, o_{t+1})\},
$$

然后不再与环境交互，只用这批数据训练模型。

离线世界模型听起来很理想，但过去很多方法为了让它能解决具体任务，往往需要额外辅助信息：

- 专家示范：告诉模型高手怎么做；
- 密集奖励函数：告诉模型每一步好不好；
- 手工关键点：告诉模型哪些物体位置最重要；
- 预训练 inverse model：从目标反推出动作；
- 文本目标或任务标签：告诉模型当前任务是什么。

这些信息当然有用，但会降低方法的通用性。因为真实世界里，给每个新任务设计奖励、收集专家、标关键点都很贵。

DINO-WM 问了一个很关键的问题：

**有没有一种辅助信息，既能帮助离线世界模型学得更稳，又不把它绑定到某个具体任务？**

论文的答案是：**使用大规模预训练视觉模型提供的通用 patch 表示。**

### 为什么不直接预测像素

早期视觉世界模型常常预测未来图像：

$$
  \hat{o}_{t+1} = f_\theta(o_t, a_t).
$$

这很直观，但有几个问题：

- 图像像素维度很高，预测成本大；
- 像素里有很多对控制无关的细节，例如纹理、光照、阴影；
- 只要像素模糊一点，模型看起来就很差，但控制可能并不需要完美重建；
- 扩散视频模型虽然能生成逼真画面，但测试时用它做大量动作优化很慢。

控制真正关心的是：物体在哪里，墙在哪里，手臂姿态怎样，动作会让这些关键结构如何变化。也就是说，我们更想预测一个“可用于控制的抽象世界”，而不是每个像素。

TD-MPC/TD-MPC2 相关方法也强调了类似思想：TOLD 或 TD-MPC2 都不追求复原完整世界。它们更关心预测对控制有用的 latent、reward 和 value。

但是 DINO-WM 和 TD-MPC2 的区别很大：

- TD-MPC2 的 latent 是任务导向的，训练时依赖 reward/value 目标；
- DINO-WM 的 latent 来自冻结的 DINOv2，不依赖当前任务奖励；
- TD-MPC2 的规划目标是 reward + terminal Q；
- DINO-WM 的规划目标是“预测 latent 和目标图像 latent 的距离”。

> **我的理解：**TD-MPC2 是“为奖励优化而学习 latent 世界”；DINO-WM 是“借用预训练视觉语义作为通用 latent 世界，再把目标图像变成规划坐标”。这就是二者的核心分野。

### 为什么是 DINOv2 patch 特征

DINOv2 是一种自监督视觉表征模型。它不是靠人工类别标签训练出来的，而是通过自蒸馏等方法从大量图像中学习有用的视觉结构。

对本文来说，最关键的是 DINOv2 的 Vision Transformer 结构可以输出 patch 特征。假设一张图被切成 $N$ 个 patch，每个 patch 有 $E$ 维特征，那么：

$$
  z_t = \mathrm{enc}(o_t) \in \mathbb{R}^{N \times E}.
$$

这和只用一个全局向量不同。全局向量像“整张图一句话总结”，而 patch 特征像“地图上的很多格子，每格都有语义”。对于控制任务，空间信息非常重要：

- 迷宫导航要知道门和墙在什么位置；
- 推物体要知道推杆、物体边缘、目标姿态的相对空间关系；
- 绳子和颗粒任务要知道形状和局部分布。

因此 DINO-WM 的一个关键判断是：**预训练 patch 表示既保留空间结构，又带有通用语义先验，非常适合做视觉世界模型的状态空间。**

## 核心贡献和方法

### 论文要解决的任务

测试时，系统会得到：

- 当前观测 $o_0$，一张 RGB 图；
- 目标观测 $o_g$，也是一张 RGB 图；
- 一个已经离线训练好的世界模型；
- 没有专家示范、没有奖励函数、没有任务标签、没有预训练 inverse model。

目标是找到动作序列：

$$
  a_0, a_1, \ldots, a_{T-1},
$$

让真实环境最终到达目标图像所描述的状态。

这叫 visual goal reaching。目标不是文字“把物体推到左上角”，而是一张目标图像。模型要自己通过视觉特征判断当前和目标的差距。

### 总架构

```mermaid
flowchart LR
  A[当前图像<br/>o_t] --> B[冻结 DINOv2<br/>patch encoder]
  B --> C[patch latent<br/>z_t in R^{N x E}]
  D[动作序列<br/>a_{t:t+T-1}] --> E[Transformer<br/>transition model]
  C --> E
  E --> F[预测未来<br/>z_hat_{t+T}]
  G[目标图像 latent<br/>z_g = enc(o_g)] --> H[规划代价<br/>||z_hat_{t+T} - z_g||_2^2]
  F --> H
```

整个方法可以分成三个模块：

1. 观测模型：冻结的 DINOv2，把图像变成 patch latent；
2. 转移模型：动作条件 Transformer，在 latent 空间预测未来；
3. 测试时规划：用 MPC/CEM 搜索动作，让预测 latent 接近目标 latent。

### 贡献一：不重建像素的 DINO latent 世界模型

很多视觉世界模型把“重建图像”作为训练目标。但 DINO-WM 的核心训练目标不是让模型画出未来图像，而是：

$$
  \hat z_{t+1} \approx z_{t+1}.
$$

其中：

$$
  z_t = \mathrm{enc}(o_t),
   
  z_{t+1} = \mathrm{enc}(o_{t+1}).
$$

因为 encoder 是冻结的 DINOv2，所以训练目标可以理解为：给定过去的 DINO patch 特征和动作，预测下一帧的 DINO patch 特征。

这样做有三个好处：

- 训练更轻：不用在高维像素空间计算重建；
- 更聚焦：模型学习语义和空间结构变化，而不是无关像素细节；
- 更通用：latent 不是由某个任务的 reward 学出来的，因此更适合任务无关规划。

### 贡献二：用 patch 特征而不是全局特征

论文专门比较了 R3M、ImageNet ResNet、DINO CLS 和 DINO Patch。区别在于：

- R3M、ResNet、DINO CLS 更接近“一张图一个向量”；
- DINO Patch 是“一张图很多 patch 向量”。

为什么 patch 重要？举个比喻：

- 全局特征像别人告诉你“房间里有桌子、杯子、机械臂”；
- patch 特征像给你一张有坐标的地图，告诉你桌子在哪、杯子在哪、机械臂末端在哪。

控制任务关心的是空间关系和局部接触。只知道“有一个 T 形块”不够，你必须知道它的姿态、边缘、与推杆的距离。所以 DINO Patch 在复杂任务上明显更强。

### 贡献三：测试时零样本视觉规划

训练阶段只学习动力学：

$$
  (o_t, a_t, o_{t+1})   \Rightarrow   z_t, a_t, z_{t+1}.
$$

测试阶段才给目标 $o_g$。模型并没有针对这个目标训练过，也没有目标 reward。它直接把目标图像编码成：

$$
  z_g = \mathrm{enc}(o_g).
$$

然后优化动作序列，使：

$$
  \hat z_T \approx z_g.
$$

这就是论文标题里的 zero-shot planning。这里的 zero-shot 不是说模型完全没见过环境，而是说：

> 世界模型训练好之后，面对新的目标图像，不需要为该目标再训练策略、奖励或 inverse model。

### 贡献四：用标准规划器反过来检验世界模型质量

论文并不强调 CEM/MPC 是新发明。它们是标准工具。作者的逻辑是：

**如果同样用 MPC 规划，某个世界模型能更好地达成目标，那说明它的未来预测更适合控制。**

因此实验里，DINO-WM 把 DINO-WM 和 IRIS、DreamerV3、TD-MPC2 等方法放在同样的离线数据和测试目标下比较。结果显示，DINO-WM 在复杂操控任务上优势很大。

## 方法实现细节

### 观测模型：冻结 DINOv2 encoder

对每个图像观测 $o_t$，使用预训练 DINOv2 encoder：

$$
  z_t = \mathrm{enc}(o_t).
$$

论文附录给出实现中使用的特征形状为：

$$
  z_t \in \mathbb{R}^{14 \times 14 \times 384}.
$$

也就是 $N=196$ 个 patch，每个 patch 是 384 维。可以把它 reshape 成：

$$
  z_t \in \mathbb{R}^{196 \times 384}.
$$

这里 encoder 在训练和测试时都冻结：

$$
  \nabla_{\theta_{\mathrm{enc}}} = 0.
$$

冻结的意义是：不要让小规模机器人数据破坏 DINOv2 从大规模视觉数据中学到的通用结构。机器人数据可能只有几千条轨迹，而 DINOv2 的视觉先验来自大规模图像数据。让它保持稳定，反而更有利于泛化。

> **注意：** 论文主文说观测图像是 $224\times224$，附录实现又写到 encoder 输入 resize 后得到 $14\times14$ patch 特征。复现时应优先检查开源代码的实际 resize 流程；理解方法时只需抓住“图像被编码为空间 patch 特征”这一点。

### 转移模型：动作条件 Transformer

世界模型要学的是：

$$
  p_\theta(z_{t+1} \mid z_{t-H+1:t}, a_{t-H+1:t}).
$$

其中 $H$ 是历史长度。直觉上，只看当前一帧可能不知道速度和动量。比如一个小球在同一个位置，可能正在向左动，也可能正在向右动。多看几帧才能推断动态信息。

模型使用 ViT 风格 Transformer，但去掉普通 ViT 的图像 patch tokenization 层，因为输入已经是 DINOv2 的 patch embedding。

动作如何进入模型？论文做法是先用 MLP 把动作编码到高维：

$$
  e_t^a = \phi(a_t),
$$

然后把动作 embedding 拼接到每个 patch 特征上：

$$
  \tilde z_t^i = [z_t^i; e_t^a],   i=1,\ldots,N.
$$

如果有 proprioception，比如机械臂关节角、末端位置等，也可以类似拼接到 latent 上。这样模型既知道视觉场景，也知道自己身体状态和动作。

### 为什么需要 causal attention mask

训练时，模型会拿到一段轨迹片段：

$$
  o_{t-H+1},\ldots,o_t,o_{t+1}.
$$

如果 Transformer 的 attention 不加限制，它可能在训练时偷看未来帧。这样训练损失很好看，但测试时未来帧并不存在，性能会崩。

所以论文引入 frame-level causal attention。核心原则是：

$$
  \text{预测 } z_{t+k} \text{ 时，只能看 } z_{\le t+k-1}.
$$

这类似做考试时不能偷看答案。加 mask 后，模型必须真的从过去和动作中学习动力学。

消融实验非常有力：在 PushT 上，历史长度 $h=3$ 时：

$$
  \text{无 mask 成功率}=0.08, 
  \text{有 mask 成功率}=0.92.
$$

这说明 causal mask 不是小技巧，而是防止训练-测试不一致的关键设计。

### 训练目标：latent consistency loss

训练时使用 teacher forcing。每次从离线轨迹中切出长度 $H+1$ 的片段，前 $H$ 帧作为上下文，预测后续 latent。

简化写法：

$$
  \hat z_{t+1}
  =
  p_\theta\bigl(z_{t-H+1:t}, \phi(a_{t-H+1:t})\bigr).
$$

训练损失是预测 latent 和真实下一帧 latent 的均方误差：

$$
  \mathcal{L}_{\mathrm{pred}}
  =
  \left\|
  p_\theta(\mathrm{enc}(o_{t-H+1:t}), \phi(a_{t-H+1:t}))
  -
  \mathrm{enc}(o_{t+1})
  \right\|_2^2.
$$

由于 $\mathrm{enc}$ 冻结，$\mathrm{enc}(o_{t+1})$ 就像一个固定监督标签。

和 TD-MPC2 对比会更清楚。TD-MPC2 的目标通常包含：

$$
  \mathcal{L}_{\mathrm{TD-MPC2}}
  =
  \mathcal{L}_{z}
  + \mathcal{L}_{r}
  + \mathcal{L}_{q},
$$

也就是 latent prediction、reward prediction、value prediction。DINO-WM 刻意不学习 reward 和 value：

$$
  \mathcal{L}_{\mathrm{DINO-WM}}
  =
  \mathcal{L}_{\mathrm{pred}}.
$$

这使它更任务无关，但也意味着测试时必须给一个视觉目标，而不是只给奖励函数。

### 可选 decoder：只为解释，不参与规划

论文还训练了一个 decoder：

$$
  \hat o_t = q_\psi(z_t),
$$

对应重建损失：

$$
  \mathcal{L}_{\mathrm{rec}}
  =
  \|q_\psi(z_t)-o_t\|_2^2.
$$

但这个 decoder 是可选的，主要用于可视化世界模型的预测。规划时不需要把 latent 解码成图像。

这点非常重要：**DINO-WM 的决策发生在 latent 空间，不发生在像素空间。**

论文还测试了如果把 decoder loss 反传到 predictor 会怎样。PushT 上：

$$
  \text{不加 decoder loss 的成功率}=0.92, 
  \text{加 decoder loss 的成功率}=0.80.
$$

这说明像素重建目标并不一定帮助控制，甚至可能把模型注意力拉向对控制无关的细节。

### 测试时规划：把目标图像变成 latent 目标

测试时，给当前图像 $o_0$ 和目标图像 $o_g$：

$$
  \hat z_0 = \mathrm{enc}(o_0), 
  z_g = \mathrm{enc}(o_g).
$$

给定一个候选动作序列：

$$
  \tau = (a_0,\ldots,a_{T-1}),
$$

世界模型递推预测：

$$
  \hat z_{t+1} = p_\theta(\hat z_t, a_t),  t=0,\ldots,T-1.
$$

规划代价是最终预测 latent 和目标 latent 的距离：

$$
  C(\tau) = \|\hat z_T - z_g\|_2^2.
$$

目标是找最小代价动作序列：

$$
  \tau^\star = \arg\min_{\tau} C(\tau).
$$

如果用一句话解释：**在脑内试很多未来动作，谁能把未来画面的 DINO patch 特征推近目标图，谁就是好动作。**

### CEM：如何搜索动作序列

CEM，全称 Cross-Entropy Method，是一种采样式优化。它不需要对动作求梯度，而是反复采样和筛选。

步骤如下：

1. 初始化一个动作序列分布，例如高斯分布 $\mathcal{N}(\mu,\Sigma)$；
2. 从中采样 $N$ 条动作序列；
3. 用世界模型 rollout 每条序列，计算代价 $C(\tau)$；
4. 选出代价最低的 top-$K$ 条 elite 序列；
5. 用 elite 序列更新 $\mu,\Sigma$；
6. 重复若干轮；
7. 得到最优动作序列后，只执行前 $k$ 个动作，之后重新观察并重新规划。

MPC 的思想是 receding horizon：规划一段未来，但只执行开头，再用真实反馈修正。这就像开车导航不会一次性把方向盘固定到目的地，而是不断根据新路况微调。

### 为什么 CEM 比梯度下降好

世界模型是可微的，所以理论上可以直接对动作序列做梯度下降：

$$
  a_{0:T-1} \leftarrow a_{0:T-1}
  - \eta \nabla_{a_{0:T-1}} C.
$$

论文也测试了 GD，但效果差很多。例如：

$$
  \text{PointMaze: GD }0.22 \text{ vs MPC }0.98, 
  \text{PushT: GD }0.28 \text{ vs MPC }0.90.
$$

原因可能是动作优化问题高度非凸。接触、碰撞、绕墙、推物体都有很多局部最优。CEM 同时试很多候选序列，更容易跳出局部坑。

### 简化 PyTorch 伪代码

下面代码不是论文官方实现，而是帮助理解训练逻辑的简化版本。

**DINO-WM 训练步骤的简化伪代码**

```python
def train_step(images, actions, dino_encoder, transition, action_mlp, opt):
    # images:  [B, H+1, C, height, width]
    # actions: [B, H, action_dim]

    with torch.no_grad():
        # z: [B, H+1, N_patches, emb_dim]
        z = dino_encoder(images)

    z_context = z[:, :-1]        # past latents
    z_target = z[:, 1:]         # future latents
    a_emb = action_mlp(actions)

    # Predict future DINO patch features.
    z_pred = transition(
        z_context,
        a_emb,
        causal_mask=True
    )

    loss = ((z_pred - z_target) ** 2).mean()

    opt.zero_grad()
    loss.backward()
    opt.step()

    return loss.item()
```

测试时规划的简化伪代码如下：

**DINO-WM + CEM/MPC 规划的简化伪代码**

```python
@torch.no_grad()
def plan(current_img, goal_img, dino_encoder, transition, cem_iters=10):
    z0 = dino_encoder(current_img)
    zg = dino_encoder(goal_img)

    mu = torch.zeros(horizon, action_dim)
    sigma = torch.ones(horizon, action_dim)

    for _ in range(cem_iters):
        # Sample action sequences.
        actions = mu + sigma * torch.randn(num_samples, horizon, action_dim)

        # Roll out every sequence in latent space.
        z = z0.repeat(num_samples, 1, 1)
        for t in range(horizon):
            z = transition.one_step(z, actions[:, t])

        # Final latent should match goal latent.
        cost = ((z - zg) ** 2).mean(dim=(1, 2))

        # Keep elite sequences and refit distribution.
        elite_idx = cost.topk(k=num_elites, largest=False).indices
        elite_actions = actions[elite_idx]
        mu = elite_actions.mean(dim=0)
        sigma = elite_actions.std(dim=0).clamp_min(1e-4)

    # MPC executes only the first action, then replans.
    return mu[0]
```

### 和 TD-MPC/TD-MPC2 的关系

在 TD-MPC/TD-MPC2 中，一个典型的规划评分公式是：

$$
  G(\tau)
  =
  \sum_{i=0}^{H-1}\gamma^i R_\theta(z_i,a_i)
  +
  \gamma^H Q_\theta(z_H,a_H).
$$

意思是：短期用 reward model 打分，长期用 Q function 补足。

DINO-WM 的规划公式则是：

$$
  C(\tau)=\|\hat z_T-z_g\|_2^2.
$$

二者差别可以总结如下：

| 方面 | TD-MPC2 | DINO-WM |
| --- | --- | --- |
| latent 来源 | 由控制任务数据和 reward/value 目标训练 | 冻结的 DINOv2 patch 特征 |
| 训练信号 | latent、reward、value | 只预测未来 DINO latent |
| 规划目标 | 最大化 predicted reward + terminal Q | 最小化预测 latent 和目标图像 latent 的距离 |
| 是否需要奖励 | 需要，reward/value 是核心训练信号 | 不需要 |
| 是否任务导向 | 是 | 更任务无关 |
| 适合目标形式 | 奖励函数定义的任务 | 目标图像定义的任务 |

> **更浅显地说：**TD-MPC2 像一个知道“什么行为得分高”的运动员；DINO-WM 像一个会预测“动作会把画面变成什么样”的想象器。前者靠奖励评分，后者靠目标图像对齐。

## 实验设置和结果

### 实验要回答的问题

论文实验围绕四个问题：

1. 能否只用预收集的离线轨迹训练 DINO-WM？
2. 训练好后，能否直接用它做视觉目标规划？
3. 性能是否真的依赖预训练视觉表示，尤其是 patch 表示？
4. 能否泛化到新的环境布局、物体形状、颗粒数量等配置？

### 环境和任务

论文测试六类环境：

| 环境 | 任务描述 | 指标 |
| --- | --- | --- |
| Maze | 二维受力小球在迷宫中到达目标位置，需要处理速度、加速度、惯性 | Success Rate |
| Wall | 两个房间中间有墙和门，智能体要穿过门到达另一侧目标 | Success Rate |
| Reach | DeepMind Control 中二维双关节机械臂，要匹配目标姿态 | Success Rate |
| PushT | 推杆把 T 形物体推到目标位置和姿态，涉及接触动力学 | Success Rate |
| Rope | XArm 操作软绳达到目标形状 | Chamfer Distance |
| Granular | 操作约一百个颗粒，把它们聚成目标形状 | Chamfer Distance |

前四个任务用成功率，越高越好；Rope 和 Granular 用 Chamfer Distance，越低越好。

所有任务都以目标图像指定目标状态。模型不是根据 reward 解任务，而是根据“当前图像和目标图像的 latent 差距”做规划。

### 离线数据规模

论文使用的训练数据来自预收集轨迹。附录中的主要数据规模如下：

| 环境 | 历史长度 $H$ | frameskip | 轨迹数 | 轨迹长度 |
| --- | --- | --- | --- | --- |
| PointMaze | 3 | 5 | 2000 | 100 |
| Reacher | 3 | 5 | 3000 | 100 |
| PushT | 3 | 5 | 18500 | 100-300 |
| PushObj | 3 | 5 | 20000 | 100 |
| Wall | 1 | 5 | 1920 | 50 |
| WallRandom | 1 | 5 | 10240 | 50 |
| Rope | 1 | 1 | 1000 | 5 |
| Granular | 1 | 1 | 1000 | 5 |

共享训练设置包括：AdamW 优化器，decoder learning rate $3\times10^{-4}$，predictor learning rate $5\times10^{-5}$，action encoder learning rate $5\times10^{-4}$，action embedding 维度 10，训练 100 epochs，batch size 32。转移模型约 19M 参数，ViT backbone 深度 6，attention heads 16，MLP 维度 2048。

### 主结果：六个环境上的规划性能

| 模型 | Maze SR | Wall SR | Reach SR | PushT SR | Rope CD | Granular CD |
| --- | --- | --- | --- | --- | --- | --- |
| IRIS | 0.74 | 0.04 | 0.18 | 0.32 | 1.11 | 0.37 |
| DreamerV3 | 1.00 | 1.00 | 0.64 | 0.30 | 2.49 | 1.05 |
| TD-MPC2 | 0.00 | 0.00 | 0.00 | 0.00 | 2.52 | 1.21 |
| DINO-WM | 0.98 | 0.96 | 0.92 | 0.90 | 0.41 | 0.26 |

结论：

- 在简单导航任务 Maze 和 Wall 上，DINO-WM 与 DreamerV3 接近，已经很强。
- 在 Reach 和 PushT 这类需要精细空间理解和接触动力学的任务上，DINO-WM 明显更好。
- 在 Rope 和 Granular 这类变形物体或颗粒任务上，DINO-WM 的 Chamfer Distance 最低。
- TD-MPC2 在该离线无奖励设置下表现很差。原因不是 TD-MPC2 本身弱，而是它原本依赖 reward/value 学习任务导向 latent；这里没有 reward，等于拿掉了它的关键训练信号。

> **核心理解：** 这组结果最能说明 DINO-WM 的定位：它不是要替代所有基于 reward 的模型控制方法，而是证明当任务由目标图像指定、且没有奖励/专家/任务标签时，预训练视觉 patch latent 可以成为非常有效的规划空间。

### 预训练表示消融：patch 为什么关键

论文比较了不同 encoder：

| Encoder | Maze SR | Wall SR | Reach SR | PushT SR | Rope CD | Granular CD |
| --- | --- | --- | --- | --- | --- | --- |
| R3M | 0.94 | 0.34 | 0.40 | 0.42 | 1.13 | 0.95 |
| ResNet | 0.98 | 0.12 | 0.06 | 0.20 | 1.08 | 0.90 |
| DINO CLS | 0.96 | 0.58 | 0.60 | 0.44 | 0.84 | 0.79 |
| DINO Patch | 0.98 | 0.96 | 0.92 | 0.90 | 0.41 | 0.26 |

这个表很关键。Maze 中大家都不错，因为任务简单。但在 Wall、Reach、PushT、Rope、Granular 上，DINO Patch 明显领先。

原因不是简单地“DINO 比其他模型强”，而是 **DINO Patch 保留了空间结构**。DINO CLS 是全局向量，虽然也来自 DINO，但丢失了很多局部几何细节。控制任务不是只问“图里有什么”，还问“它们在哪里、如何相互作用”。

### 泛化到新环境配置

论文还测试模型是否能泛化到训练中没见过的配置：

| 模型 | WallRandom SR | PushObj SR | GranularRandom CD |
| --- | --- | --- | --- |
| IRIS | 0.06 | 0.14 | 0.86 |
| DreamerV3 | 0.76 | 0.18 | 1.53 |
| R3M | 0.40 | 0.16 | 1.12 |
| ResNet | 0.40 | 0.14 | 0.98 |
| DINO CLS | 0.64 | 0.18 | 1.36 |
| DINO-WM | 0.82 | 0.34 | 0.63 |

三个任务分别考察不同泛化：

- WallRandom：门和墙的位置变了。DINO-WM 成功率 0.82，说明它不是死记固定门位置，而是学到了“墙和门”的视觉概念。
- PushObj：物体形状变了。DINO-WM 仍然最高，但只有 0.34，说明新的接触几何仍然很难。
- GranularRandom：颗粒数量和分布变了。DINO-WM CD 最低，说明 patch 表示对局部颗粒分布变化比较鲁棒。

这个结果提醒我们：DINO-WM 确实提高了泛化，但不是魔法。对于从未见过的物体形状和复杂接触动力学，它仍然会受数据覆盖限制。

### 预测质量：LPIPS 和 SSIM

虽然 DINO-WM 不用像素重建训练 predictor，论文仍训练 decoder 来可视化 latent rollout，并比较预测图像质量。

LPIPS 越低越好：

| 方法 | PushT | Wall | Rope | Granular |
| --- | --- | --- | --- | --- |
| R3M | 0.045 | 0.008 | 0.023 | 0.080 |
| ResNet | 0.063 | 0.002 | 0.025 | 0.080 |
| DINO CLS | 0.039 | 0.004 | 0.029 | 0.086 |
| AVDC | 0.046 | 0.030 | 0.060 | 0.106 |
| DINO-WM | 0.007 | 0.0016 | 0.009 | 0.035 |

SSIM 越高越好：

| 方法 | PushT | Wall | Rope | Granular |
| --- | --- | --- | --- | --- |
| R3M | 0.956 | 0.994 | 0.982 | 0.917 |
| ResNet | 0.950 | 0.996 | 0.980 | 0.915 |
| DINO CLS | 0.973 | 0.996 | 0.980 | 0.912 |
| AVDC | 0.959 | 0.983 | 0.979 | 0.909 |
| DINO-WM | 0.985 | 0.997 | 0.985 | 0.940 |

有趣的是，DINO-WM 没有直接用像素重建损失训练 transition，却反而预测出了更可解码、更接近真实未来的 latent。这说明 DINOv2 patch 特征空间本身具有很好的物理和语义组织性。

### 数据规模消融

PushT 上，训练数据越多，规划成功率和预测质量越好：

| 数据规模 | Success Rate | SSIM | LPIPS |
| --- | --- | --- | --- |
| 200 | 0.08 | 0.949 | 0.056 |
| 1000 | 0.48 | 0.973 | 0.013 |
| 5000 | 0.72 | 0.981 | 0.007 |
| 10000 | 0.88 | 0.984 | 0.006 |
| 18500 | 0.92 | 0.987 | 0.005 |

这说明 DINO-WM 不是只靠 DINOv2 “白送”能力。预训练视觉特征提供了强表示，但动力学仍然需要足够的动作-结果数据来学习。

### causal mask 消融

PushT 上 causal mask 的效果：

| 设置 | $h=1$ | $h=2$ | $h=3$ |
| --- | --- | --- | --- |
| 无 mask | 0.76 | 0.36 | 0.08 |
| 有 mask | 0.76 | 0.88 | 0.92 |

解释：

- $h=1$ 时没有未来可偷看，所以二者一样；
- 历史越长，无 mask 越容易在训练时偷看未来；
- 有 mask 后，长历史提供速度、动量、接触趋势等信息，成功率提升。

### CEM、GD、MPC 的比较

论文比较了规划优化方式：

| 方法 | PointMaze | PushT | Wall | Rope | Granular |
| --- | --- | --- | --- | --- | --- |
| CEM open-loop | 0.80 | 0.86 | 0.74 | NA | NA |
| GD open-loop | 0.22 | 0.28 | NA | NA | NA |
| MPC with CEM | 0.98 | 0.90 | 0.96 | 0.41 | 0.26 |

结论：

- 单次 open-loop 规划不如 MPC，因为模型误差会累积；
- GD 容易陷入局部最优；
- CEM + MPC 最稳，因为它不断用真实观测纠偏。

### 推理时间

附录中，DINO-WM 在 NVIDIA A6000 上：

- batch 32 单步 inference：0.014 秒；
- 传统仿真 rollout batch 1：3.0 秒；
- CEM 规划，100 samples $\times$ 10 iterations：53.0 秒。

这说明 latent world model 的单步预测很快，尤其相比复杂变形体仿真。但测试时规划仍有计算开销，因为 CEM 要评估许多候选动作序列。实际部署时可能需要更高效的采样、warm start、策略先验或分层规划。

## 如何理解创新点

### 不是“DINO + Transformer”这么简单

表面看，方法似乎很朴素：

$$
  \text{DINOv2 encoder} + \text{Transformer predictor} + \text{CEM planning}.
$$

但它的创新不在复杂，而在选择了一个很干净的分解：

- 感知问题交给大规模预训练视觉模型；
- 动力学问题交给离线动作轨迹；
- 任务目标在测试时用目标图像指定；
- 控制优化交给 MPC/CEM。

这种分解使得每个部分都很清楚。模型不需要同时学视觉语义、像素重建、奖励、价值、策略。它只学一件事：**在 DINO patch 空间里，动作如何让世界变化。**

### 为什么能 zero-shot

zero-shot 的关键不是模型凭空知道所有任务，而是目标被表示成同一个 latent 空间里的点：

$$
  o_g \xrightarrow{\mathrm{enc}} z_g.
$$

只要当前状态和目标状态都能被 DINOv2 patch 特征稳定表示，规划器就可以尝试找到一条 latent 轨迹：

$$
  z_0 \rightarrow \hat z_1 \rightarrow \cdots \rightarrow \hat z_T \approx z_g.
$$

这就把“完成任务”转化成“在 latent 地图里走到目标坐标”。

### 和生成式视频模型的区别

生成式视频模型关注：

$$
  \text{未来视频看起来是否真实？}
$$

DINO-WM 关注：

$$
  \text{未来 latent 是否足够准确，能支持控制？}
$$

论文中 AVDC 可以生成看起来合理的视频，但会出现单步中大幅不物理的变化，并且难以精确到达目标。控制任务不是只要“像视频”，而是要“动作-结果关系可用于优化”。这就是世界模型和普通视频生成模型的差别。

### 局限性

DINO-WM 也有明显限制：

- 需要离线数据覆盖足够多状态和动作，否则世界模型无法预测没见过的动力学；
- 需要动作标注，因此不能直接使用普通互联网视频，除非能估计动作；
- 当前主要在 action space 做规划，高维连续动作会让 CEM 成本变高；
- 对复杂长程任务，仅靠最终 latent MSE 可能不够，需要子目标或层次结构；
- DINO 特征来自静态图像预训练，不一定天然理解所有物理属性，例如质量、摩擦、弹性；
- 目标必须以图像给出，若任务目标是语言、规则或隐藏变量，需要额外转换。

## 给初学者的复习路线

如果你刚入门，可以按以下顺序理解：

1. 先理解世界模型：它不是直接输出动作，而是预测“动作之后世界会怎样”。
2. 再理解 latent：模型不需要预测像素，可以预测一个更紧凑、更有意义的状态。
3. 再理解 DINOv2 patch：一张图不是一个向量，而是一张带语义的空间地图。
4. 再理解 MPC：每一步都在脑内试未来动作，但只执行第一步。
5. 最后理解 DINO-WM 的创新：用预训练 patch latent 作为任务无关世界模型空间，再用目标图像 latent 做零样本规划。

最值得记住的对比是：

| 路线 | 它学什么 | 它怎样做任务 |
| --- | --- | --- |
| 纯策略 | 从观测到动作的映射 | 看到状态直接输出动作 |
| TD-MPC2 | 任务导向 latent + reward/value | 在 latent 中规划，使 reward + Q 最大 |
| DINO-WM | DINO patch 空间中的动作条件动力学 | 在 latent 中规划，使预测未来接近目标图像 latent |

## 最后总结

DINO-WM 的研究动机是：现有策略方法泛化差，在线世界模型任务依赖强，离线世界模型又常需要专家、奖励、关键点或 inverse model。论文提出，用 DINOv2 预训练 patch 特征作为通用视觉状态空间，可以绕开很多任务特定依赖。

方法上，它冻结 DINOv2 encoder，把图像编码为 patch latent；用动作条件 Transformer 预测未来 latent；训练只用离线轨迹的 latent consistency loss；可选 decoder 只用于解释；测试时把目标图像也编码为 latent，并通过 CEM/MPC 搜索动作，使预测未来 latent 接近目标 latent。

实验上，DINO-WM 在六类视觉控制环境中表现强，尤其在 PushT、Reach、Rope、Granular 等需要空间理解和接触/变形动力学的任务上显著优于基线。消融表明，DINO patch 表示、causal mask、充足数据、decoder-free 训练和 MPC replanning 都是关键因素。

> **核心理解：** 我对这篇论文创新点的最终理解是：DINO-WM 把“任务无关视觉理解”和“动作条件动力学预测”接起来，让目标图像本身成为规划目标。它不是让模型记住某个任务的奖励，而是让模型学会在一个预训练视觉地图里想象未来。
