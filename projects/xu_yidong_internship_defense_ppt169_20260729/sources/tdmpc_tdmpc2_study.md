# tdmpc_tdmpc2_study

# 从TD-MPC到TD-MPC2： 任务导向世界模型、规划与价值学习的统一理解

### 面向人工智能入门学习者的论文讲义 2026年7月4日

## 一句话总览

TD-MPC的核心思想是：

用任务导向latent model做短期规划+用Q函数补长期价值 TD-MPC2的核心出发点是：TD-MPC已经证明了“latent世界模型+ MPC规划 + TD value”这条路线很强，但原始TD-MPC主要面向单任务，容易依赖任务特定超参 数，并且直接放大模型规模时不一定更好。TD-MPC2因此要解决三个问题：

1. 如何让算法在很多连续控制任务上稳定，不需要每个任务重新调参；
2. 如何让同一个世界模型处理不同状态维度、动作维度和机器人形态；
3. 如何让模型规模和数据规模变大时，性能也能稳定提升。

所以，TD-MPC2不是推翻TD-MPC，而是把TD-MPC的思想做得更稳、更通用、 更可扩展。

## 1 强化学习最小背景

连续控制任务通常可以写成一个马尔可夫决策过程：

*M*= (*S**,**A**, T, R, γ*)*.* 其中：

1

<!-- Page 2 -->

*2* *ACTOR-CRITIC*：动作提出者与动作评分者 2 符号 含义 状态，例如机器人关节角、速度、物体位置或图像观测 *s**∈S* 动作，例如每个关节的力矩或目标速度 *a**∈A* 环境动力学，表示做动作后状态如何变化 *T*(*s, a*) 奖励函数，表示当前行为好不好 *R*(*s, a*) 折扣因子，控制未来奖励的重要程度 *γ* 强化学习的目标是找到策略*π*，让长期回报最大：

[*∞* ] ∑ max E*π* *γ**t**r**t* *.* *π* *t*=0 入门时可以把它理解成：机器人每一步都要选动作，但它不能只贪图眼前奖励，还要 考虑这个动作会不会把自己带到一个未来更容易成功的位置。

## 2 Actor-Critic：动作提出者与动作评分者

TD-MPC和TD-MPC2都会用到actor-critic的基本思想。Actor和critic的分工是：

- actor或policy负责提出动作；
- critic或Q function负责评价这个动作长期好不好。

确定性策略，例如DDPG，可以写成：

*a*=*µ**θ*(*s*)*.* 随机策略，例如SAC，可以写成：

*a**∼**π**θ*(*a**|**s*)*.* Q函数表示在状态*s*做动作*a*之后，未来长期回报的估计：

[*∞* ] ∑ *Q**ϕ*(*s, a*)*≈*E *γ**k**r**t*+*k**|**s**t*=*s, a**t*=*a* *.* *k*=0 一个很重要的理解是：

policy负责提出动作，Q负责给动作打长期分数。

SAC还加入熵正则，鼓励策略不要太早变得确定：

max E[*Q*(*s, a*) +*α**H*(*π*(*·|**s*))]*.* *π* 这里*H*是策略熵。熵越大，说明策略越有探索性。这会影响TD-MPC2的policy prior设计。

<!-- Page 3 -->

*3* *MPC*、*CEM*与*MPPI*：在脑内临时试动作 3

## 3 MPC、CEM与MPPI：在脑内临时试动作

MPC，Model Predictive Control，是一种“边走边规划”的控制思想。它不是一次性 学出一个固定动作，而是在当前状态下临时搜索未来几步动作序列：

*τ*= (*a**t**, a**t*+1*, . . . , a**t*+*H**−*1)*.* 如果有一个模型可以预测未来奖励，那么可以给每条动作序列打分：

*H**−*1 ∑ *γ**i**r**t*+*i**.* *G*(*τ*) = *i*=0 然后选择分数最高的动作序列，但只执行第一个动作*a**t*。下一步看到新状态后，再 重新规划。

### 为什么只执行第一个动作

因为模型预测未来一定有误差。越往后预测越不准。所以MPC每次只相信模型一 小段时间，执行一步后用真实环境反馈修正。这就像开车导航：你可以看未来几公里路 线，但方向盘每秒都要根据真实路况重新调整。

### CEM与MPPI的区别

CEM和MPPI都是采样式轨迹优化方法。

- CEM更像只看top-*k*最好的轨迹，再用这些精英轨迹更新动作分布；
- MPPI更像让所有轨迹按好坏加权投票，好轨迹权重大，差轨迹权重小。

TD-MPC系列就是把这种规划放到learned latent model里做。

## 4 TOLD：TD-MPC的任务导向latent模型

TD-MPC的世界模型叫TOLD。它不试图预测完整未来世界，例如像素图像。它只 预测对控制任务有用的抽象状态、奖励、价值和动作建议。

TOLD有五个模块：

*z**t*=*h**θ*(*s**t*)*,* *z**t*+1=*d**θ*(*z**t**, a**t*)*,* ˆ*r**t*=*R**θ*(*z**t**, a**t*)*,* ˆ*q**t*=*Q**θ*(*z**t**, a**t*)*,* ˆ*a**t*=*π**θ*(*z**t*)*.*

<!-- Page 4 -->

*5* 4 真实奖励*r**i*与预测奖励ˆ*r**i* 模块 作用 把真实状态*s**t*编码成latent state*z**t* *h**θ* 在latent空间里预测下一步状态 *d**θ* 预测一步奖励 *R**θ* 预测长期价值 *Q**θ* 提供动作建议，帮助规划器更快找到好动作 *π**θ* TOLD的关键不是“完整复原世界”，而是“学一个对任务有用的脑内世界”。例如机 械臂抓杯子时，模型不需要知道桌面纹理每个像素，但需要知道机械臂位置、杯子位置、 动作后能不能更接近成功。

## 5 真实奖励ri与预测奖励ˆri

在强化学习交互中，真实奖励来自环境：

s_next, r_i, done, info = env.step(a_i) 也就是：

(*s**i**, a**i*)*→*(*r**i**, s**i*+1)*.* 这些数据会被存入replay buffer：

(*s**i**, a**i**, r**i**, s**i*+1)*.* 因此：

- *r**i*是真实环境返回的奖励，是训练reward model的标准答案；
- ˆ*r**i*=*R**θ*(*z**i**, a**i*)是模型预测的奖励。

训练reward model的目标是：

*R**θ*(*z**i**, a**i*)*≈**r**i**.*

## 6 TD-MPC的训练与规划闭环

TD-MPC的完整闭环如下：

1. 当前状态*s**t*进入系统；
2. encoder得到latent state*z**t*=*h**θ*(*s**t*)；
3. CEM或MPPI采样很多未来动作序列；

<!-- Page 5 -->

*6* *TD-MPC*的训练与规划闭环 5

4. TOLD在latent空间里模拟未来；
5. reward model预测短期奖励；
6. Q function预测终点之后的长期价值；
7. 选择预测回报最高的动作序列；
8. 只执行第一个动作；
9. 环境返回真实*r**t*和*s**t*+1；
10. 经验存入replay buffer；
11. 用replay buffer继续训练TOLD。

在TD-MPC中，动作序列*τ*的评分不是只看短期奖励，而是：

*H**−*1 ∑ *γ**i**R**θ*(*z**i**, a**i*) +*γ**H**Q**θ*(*z**H**, a**H*)*.* *G*(*τ*) = *i*=0 这个公式非常重要。它说明：

- 前半部分由reward model负责，回答“未来几步看起来怎么样”；
- 后半部分由Q function负责，回答“几步之后的长期前途怎么样”。

因此TD-MPC可以用较短的规划horizon，但仍然不至于短视。

### 我的理解：预训练与在线训练

可以精炼理解为：

- 单任务**TD-MPC2**：更像“边交互边训练”。先用少量seed transition启动，然后

反复执行 真实交互*→*存入replay buffer*→*更新*h, d, R, Q, p**→*重新规划*.*

- 多任务**TD-MPC2**：可以理解为“先预训练，再在线微调”。先用多任务replay数

据训练通用world model，遇到新任务后再用真实交互继续更新。

一句话：TD-MPC2不是用想象rollout训练自己，真正进入buffer的仍是真实tran- sition；想象rollout主要用于当前决策时的MPC/MPPI规划。

<!-- Page 6 -->

*7* *TD-MPC2*的论文出发点 6

## 7 TD-MPC2的论文出发点

TD-MPC已经很强，但TD-MPC2认为它还有几个明显限制：

1. 主要成功集中在单任务学习；
2. 不同任务往往需要不同超参数；
3. 原始TD-MPC直接放大模型规模时，性能不一定稳定提升；
4. 多任务时，不同任务的状态维度、动作维度和机器人形态差异很大；
5. 奖励尺度差异会让训练不稳定；
6. latent表示不受约束时，可能出现梯度爆炸。

所以TD-MPC2的出发点可以概括为：

让TD-MPC路线变得稳定、少调参、可多任务、可扩展。

TD-MPC2在104个连续控制任务上测试，涵盖DMControl、Meta-World、ManiSkill2 和MyoSuite。它还训练了一个317M参数的多任务世界模型，在80个任务上展示了模 型规模变大后性能继续提升。

## 8 OpenReview视角下的创新点补充

OpenReview的评审意见和作者回复让TD-MPC2的创新点更清楚。一个关键提醒 是：TD-MPC2的创新并不主要在于重新发明MPC规划器。评审人明确指出，TD-MPC2 的规划过程基本沿用TD-MPC，真正的新意在于把TD-MPC改造成一个更稳、更少调 参、更适合多任务和大模型扩展的系统。

### 创新一：从单任务TD-MPC走向多任务世界模型

OpenReview中评审人首先强调的差异是多任务化修改。TD-MPC2在所有模型组件 中加入任务嵌入*e*：

*z**′* =*d*(*z, a, e*)*,* *z*=*h*(*s, e*)*,* ˆ*r*=*R*(*z, a, e*)*,* ˆ*q*=*Q*(*z, a, e*)*,* *a*=*p*(*z, e*)*.* 作者在回复中澄清：任务嵌入只是可学习向量，每个任务一个embedding，和模型其 他参数一起端到端训练。它没有额外的语义监督损失。任务语义之所以会在embedding 空间中浮现，是因为模型必须依靠这些向量来区分不同任务、不同embodiment和不同 动力学。

这点的创新意义是：TD-MPC2不要求人为提供语言描述、任务标签语义或机器人结 构知识，而是让模型通过控制数据自己学出任务关系。论文中任务embedding的T-SNE 可视化也被评审人认为很有意思，因为语义相近或动力学相近的任务会自然靠近。

<!-- Page 7 -->

*8* *OPENREVIEW*视角下的创新点补充 7

### 创新二：统一不同状态和动作空间

多任务连续控制的一个现实问题是，不同任务的状态维度和动作维度不一样。TD- MPC2用zero-padding和action mask解决这个接口问题。

如果最大动作维度是*A*max，某任务只有*A**k*维动作，则把动作补零到*A*max维：

[*a*1*, . . . , a**A**k*]*→*[*a*1*, . . . , a**A**k**,*0*, . . . ,*0]*.* 同时使用mask：

*m*= [1*, . . . ,*1*,*0*, . . . ,*0]*.* 训练policy prior、计算entropy、规划采样时只考虑有效动作维度。这看似是工程细 节，但对多任务世界模型很关键。没有这个设计，一个统一模型就很难同时处理机械臂、 四足机器人、肌肉骨骼手等不同动作空间。

### 创新三：离散回归让reward/value跨任务可比

OpenReview中有评审人特别追问：为什么把奖励和价值预测做成离散回归？作者的 回复让这个创新点更清楚。

问题在于，不同任务的reward和value尺度差异很大。如果直接用MSE：

(ˆ*r**−**r*)2*,* (ˆ*q**−**q*)2*,* 大尺度任务会主导梯度，小尺度任务会被淹没。

TD-MPC2改用101-bin的离散回归和交叉熵。这不是为了让预测变粗糙，而是为了 让不同任务的训练信号在数值尺度上更均衡。

作者还解释了替代方案为什么不理想：

- 把奖励二值化为sparse success会丢失很多shaped reward信号，尤其不适合loco-

motion；

- 手动reward normalization需要知道每个任务奖励范围，大规模任务集里不可行；
- 自动运行统计归一化会引入非平稳性，并且容易受异常值影响；
- 即使单步reward被归一化，不同任务的episode length、discount、稀疏性不同，value

target仍然可能尺度不同。

因此，离散回归的创新意义是：

它把reward/value尺度问题从任务级调参问题，变成统一的分类式预测问题。

<!-- Page 8 -->

*8* *OPENREVIEW*视角下的创新点补充 8

### 创新四：稳定大模型训练的一组架构选择

OpenReview里多位评审人关注SimNorm、LayerNorm、Dropout、Mish和Q ensemble。

作者回应说，TD-MPC2虽然不是Transformer，但确实借鉴了很多大模型训练中常见的 稳定化设计：

- LayerNorm让中间表示尺度更稳定；
- Mish激活相比ReLU/ELU表现相近，但梯度更平滑；
- Dropout用在Q函数中，帮助Q学习更稳；
- SimNorm通过softmax单纯形约束latent，使表示偏向稀疏；
- 多个Q函数形成ensemble，降低过估计风险。

其中SimNorm的OpenReview解释尤其重要。作者把它类比为VQ-VAE离散码的 软变体：VQ-VAE用one-hot离散码表示latent，SimNorm则把latent划分为多个连续 单纯形，每个子向量和为1。直观地说：

VQ-VAE是硬选择，SimNorm是softmax松弛。

所以SimNorm不是简单归一化，而是在保留可微训练的同时，让latent表示带有稀 疏和结构化倾向。

### 创新五：Q ensemble采用随机子采样而不是全体取最小

TD-MPC2默认学习5个Q函数。OpenReview中有评审人问：为什么不直接对全 部5个Q函数取最小值？

作者的回答是：对大集合取最小值可能过度保守，会把target Q的偏差传递给学习 过程，损害数据效率；随机抽两个再取最小值，借鉴了REDQ一类方法中的思想，在减 少过估计、保持数据效率和计算速度之间做折中。

因此这个设计的创新不是“越保守越好”，而是：

用适度保守的Q target稳定学习，同时避免全体取最小带来的过强低估。

### 创新六：最大熵policy prior让规划更容易扩展

TD-MPC2的policy prior不是最终决策者，而是规划器的动作建议器。相比TD-MPC 中更接近确定性策略加噪声的做法，TD-MPC2使用最大熵目标训练policy prior：

max E[*αQ*(*z, p*(*z*)) +*β**H*(*p*(*·|**z*))]*.* *p* OpenReview中评审人也把这一点列为TD-MPC2相对TD-MPC的重要差异。它的 意义是：规划器不是从完全随机的动作空间里盲搜，而是从一个保持探索性的动作先验 附近搜索。这对高维动作空间尤其重要。

<!-- Page 9 -->

*9* *TD-MPC2*的世界模型目标 9

### 创新七：系统级可扩展性和开放资源

评审人和meta-review都认可：TD-MPC2的贡献不仅是一个局部技巧，而是一个系 统级改进。它在104个连续控制任务上评估，在80个任务上训练多任务模型，并展示能 力随模型和数据规模增长。代码、数据、模型检查点以及训练GPU成本都公开，这也被 OpenReview评审认为是加分项。

这里的创新可以理解为：TD-MPC2证明了TD-MPC这条路线不只是一个单任务算 法，而是有可能成为大规模连续控制世界模型的基础。

### OpenReview对创新边界的提醒

OpenReview也提醒我们，不要把TD-MPC2的贡献讲得过满。更准确的说法是：

- 规划算法本身主要沿用TD-MPC，不是TD-MPC2的主要新发明；
- 很多组件来自已有思想，例如LayerNorm、Dropout、最大熵RL、ensemble Q；
- TD-MPC2的价值在于把这些设计仔细组合到TD-MPC中，并通过大规模实验验

证它们互补有效；

- 方法仍主要面向连续动作空间，离散动作空间需要更换或重设规划方法，例如考虑

MCTS；

- 它继承MPC的部分缺点，例如决策时计算开销较高，以及在高度多模态转移中可

能更困难；

- 多任务数据来自单任务TD-MPC2 replay buffer，距离真实机器人领域更混杂的数

据分布仍有距离。

所以从OpenReview的角度，TD-MPC2的创新点最好这样表述：

TD-MPC2的创新不是提出一个完全不同于TD-MPC的新范式，而是把TD- MPC系统化地改造成一个可稳定扩展到多任务、大模型和统一超参数设置 的连续控制世界模型算法。

## 9 TD-MPC2的世界模型目标

TD-MPC2仍然学习一个decoder-free的隐式世界模型。所谓decoder-free，是指它 不预测原始观测，而是直接预测latent、reward和value。

模型训练目标可以写成：

*H* ∑ *λ**t*[ ] *c**z**∥*ˆ*z**t**−*sg(*h**θ*(*s**t*))*∥*2 2 +*c**r*CE(ˆ*r**t**, r**t*) +*c**q*CE(ˆ*q**t**, q**t*) *L*(*θ*) =E *.* *t*=0 三个部分分别对应：

<!-- Page 10 -->

*10* *EMA TARGET NETWORK*为什么稳定 10 损失项 含义 latent prediction 让模型在latent空间里预测未来状态 reward prediction 让模型预测真实环境奖励 value prediction 让模型预测TD target所代表的长期价值 其中sg表示stop-gradient。它让目标encoder输出不反传梯度，避免模型自己追着 自己动。

## 10 EMA target network为什么稳定

TD target是：

*q**t*=*r**t*+*γ* ¯*Q*(*z**t*+1*, p*(*z**t*+1))*.* 这里¯*Q*是EMA target network：

¯*Q**←**ρ*¯*Q*+ (1*−**ρ*)*Q.* TD-MPC2使用：

*ρ*= 0*.*99*.* 这表示每次更新时，target network保留99%的旧参数，只吸收1%的当前Q参数。

为什么这有用？因为TD学习里目标本身依赖模型预测。如果直接用正在快速变化 的*Q*来构造target，模型就像在追一个不断移动、甚至自己制造出来的目标。

EMA的效果是让目标变慢、变平滑：

- 降低单个batch噪声对target的影响；
- 减少Q估计误差在bootstrapping中快速放大；
- 让训练更接近一个目标相对稳定的监督学习问题。

代码形式如下：

@torch.no_grad() **def**update_target(Q, Q_bar, rho=0.99):

**for**p, p_bar**in zip**(Q.parameters(), Q_bar.parameters()):

p_bar.data.mul_(rho) p_bar.data.add_((1 - rho) * p.data) 可以把¯*Q*理解成一个慢半拍的老师。学生*Q*每一步都在快速学习，老师¯*Q*会参考 学生，但只慢慢修订标准答案。

<!-- Page 11 -->

*11* *SIMNORM*：约束*LATENT*表示 11

### 我的理解：慢速锚点与误差累积

可以把EMA target network理解为给TD学习提供一个慢速锚点。因为TD target 中当前要学习的价值依赖下一步的价值估计：

*q**t*=*r**t*+*γ* ¯*Q*(*z**t*+1*, p*(*z**t*+1))*.* 也就是说，*Q**t*的学习目标来自*Q**t*+1的预测。如果当前Q和下一步Q都同步快速变 化，小的估计误差就可能沿着时间递推链条传播：

*Q**t*+1估高*→**Q**t*学到偏高target*→*后续更多target被带偏*.* 这就是bootstrapping中容易出现的误差累积和误差放大。EMA的作用不是让target 一步变得绝对准确，而是让用于构造target的¯*Q*慢慢跟随在线*Q*：

¯*Q**←*0*.*99 ¯*Q*+ 0*.*01*Q.* 因此，你可以把它理解为：

由于TD学习中的目标值由下一时刻的价值估计自举得到，当前Q与未来 Q之间存在强耦合。如果所有Q估计都同步快速变化，小的估计误差会沿时 间递推传播并被放大。因此TD-MPC2使用EMA target network作为慢速 锚点，使target在局部时间窗口内相对稳定，让Q学习在小范围内平滑调 整。它本质上是牺牲目标更新速度，换取训练稳定性和更低的误差累积风险。

所以，与其说EMA是简单地“以时间换精度”，不如说它是：

以目标更新速度换训练稳定性。

## 11 SimNorm：约束latent表示

TD-MPC2的一个关键稳定性设计是SimNorm。假设latent state*z*是512维，Sim- Norm维度*V*= 8。模型把它分成：

512 = 64*×*8*.* 每8维为一组，在组内做softmax：

**import**torch **import**torch.nn.functional**as**F **def**simnorm(z, V=8, tau=1.0):

shape = z.shape z = z.view(*shape[:-1], -1, V) z = F.softmax(z / tau, dim=-1) **return**z.view(*shape)

<!-- Page 12 -->

*11* *SIMNORM*：约束*LATENT*表示 12 每一组softmax后都满足：

*V* ∑ *g**i,j**≥*0*,* *g**i,j*= 1*.* *j*=1 这会带来两个效果：

1. latent数值不能无限变大，降低梯度爆炸风险；
2. 每组倾向突出少数几个维度，形成更稀疏、更结构化的表示。

普通latent像一张自由草稿纸，可能越写越乱。SimNorm像把latent填进很多个小 概率分布盒子，每个盒子里总量固定，因此训练更稳定。

### 我的理解：有限要素槽位，而不是有限状态类别

可以把SimNorm直观理解为：一个环境中真正影响控制的抽象要素不是无限混乱 的，模型可以把这些要素组织到有限个槽位中。在TD-MPC2的默认设置里，512维latent 被拆成64组，因此可以把它想成64个抽象因素槽位。每个槽位内部有8个候选模式， softmax表示模型在这8个模式之间分配权重。

但这里需要特别注意：

不是说环境只有64种状态，也不是说只有64种要素。

更准确的说法是：

SimNorm把latent表示拆成64个可组合的因素槽位，每个槽位做一次soft选择。

如果每个槽位接近one-hot，整体组合能力大约类似于：

864*,* 这是极其巨大的组合空间。所以SimNorm不是把环境粗暴压成64类，而是让模型用许 多可组合的小结构来表示复杂状态。

因此，它主要不是通过减少参数量来减少训练量。latent维度仍然是512，模型计算 量并不会因为SimNorm直接大幅下降。它真正减少的是表示空间的混乱程度：

- 限制latent数值无限变大；
- 让每组表示有固定总量；
- 让模型更倾向于使用稀疏、结构化的表示；
- 降低dynamics、reward、Q学习时的梯度不稳定风险。

<!-- Page 13 -->

*12* 13 离散回归：解决奖励尺度差异 所以这段理解可以整理成一句话：

SimNorm可以理解为：我不让模型用完全自由的512维实数乱表示世界，而 是让它把世界状态组织成64个抽象因素槽位；每个槽位在8个候选模式之 间做soft选择。这不一定直接减少训练计算量，但会让表示更规整、更稳定， 从而让训练更容易成功。

## 12 离散回归：解决奖励尺度差异

普通reward或value回归可能使用MSE：

*L*MSE= (ˆ*r**−**r*)2*.* 但多任务中不同任务奖励尺度差异很大。一个任务奖励可能在[0*,*1]，另一个任务 return可能接近1000。直接MSE会让大尺度任务主导训练。

TD-MPC2把reward和value预测变成离散回归。模型输出101个bin的logits：

ˆ*r*=logits*r**∈*R101*,* ˆ*q*=logits*q**∈*R101*.* 真实数值先经过变换并投影到bin上，然后用交叉熵学习：

*L**r*=CE(ˆ*r, r*)*,* *L**q*=CE(ˆ*q, q*)*.* 直觉是：不强迫模型一开始就精确预测一个连续数字，而是先判断目标大概落在哪 个区间。这对value learning特别重要，因为value本来就是带噪声的长期估计。

## 13 Q ensemble：减少过估计

Q-learning容易有过估计问题。如果某个动作的Q值被偶然估得过高，规划器就会 偏向它，导致错误被放大。

TD-MPC2默认训练5个Q函数：

*Q*1*, Q*2*, Q*3*, Q*4*, Q*5*.* 计算target时，随机抽两个target Q函数并取较小值：

) (¯*Q**i*(*z**t*+1*, a**′*)*,*¯*Q**j*(*z**t*+1*, a**′*) *q**t*=*r**t*+*γ*min *,* *a**′* =*p*(*z**t*+1)*.* 这相当于两个老师打分时取更保守的那个，可以减少虚高价值对训练和规划的污染。

<!-- Page 14 -->

*14* 最大熵*POLICY PRIOR* 14

## 14 最大熵policy prior

TD-MPC2最终动作来自规划，但它仍然学习一个policy prior：

*a**∼**p**θ*(*·|**z, e*)*.* policy prior的任务不是替代规划，而是帮助规划。它告诉MPPI：哪些动作比较可 能是好动作。

TD-MPC2使用最大熵思想训练policy prior：

max E[*αQ*(*z, p*(*z*)) +*β**H*(*p*(*·|**z*))]*.* *p* 第一项让策略倾向高价值动作；第二项让策略保持探索，不要过早塌缩到单一动作。

可以把policy prior理解成规划器的向导。它不是直接替规划器做最终决定，但能让 规划器少在明显无用的动作区域浪费采样。

## 15 MPPI规划：短期reward加长期Q

TD-MPC2使用MPPI做局部轨迹优化。每个决策步大致如下：

z_t = encoder(s_t) initialize action distribution N(mu, sigma) for iteration in range(6):

sample 512 action sequences rollout each sequence in latent space score = predicted rewards + terminal Q update mu, sigma using elite / weighted trajectories execute first action from the optimized sequence 规划目标可以写成：

[*H**−*1 ] ∑ max *γ**i**R**θ*(*z**t*+*i**, a**t*+*i*) +*γ**H**Q**θ*(*z**t*+*H**, a**t*+*H*) *.* *a**t**,...,a**t*+*H* *i*=0 TD-MPC2默认horizon很短：

*H*= 3*.* 这看起来短，但并不短视，因为terminal Q负责估计三步之后的长期价值。也就是 说：

MPC管近处精细动作，Q函数管远处长期趋势。

<!-- Page 15 -->

*16* 多任务：*ZERO-PADDING*与*ACTION MASK* 15

## 16 多任务：zero-padding与action mask

多任务学习会遇到一个工程难题：不同任务的状态维度和动作维度可能不同。

例如：

任务 状态维度 动作维度 2 小车 低维 7 机械臂 中维 39 仿生手 高维 TD-MPC2的做法是把输入输出pad到最大维度。例如最大动作维度是39，某任务 只有7维动作：

[*a*1*, . . . , a*7]*→*[*a*1*, . . . , a*7*,*0*, . . . ,*0]*.* 然后使用action mask：

*m*= [1*, . . . ,*1*,*0*, . . . ,*0]*.* 训练和规划时只考虑有效动作维度。这可以避免模型在无效动作维度上制造虚假的 entropy或预测误差。

此外，TD-MPC2给每个任务一个可学习task embedding：

*e**k**∈*R96*.* 所有模块都可以条件化在这个任务向量上：

*z**′* =*d*(*z, a, e*)*,* *z*=*h*(*s, e*)*,* ˆ*r*=*R*(*z, a, e*)*,* ˆ*q*=*Q*(*z, a, e*)*,* *a*=*p*(*z, e*)*.* 这样同一个模型既共享通用控制知识，又能区分不同任务。

<!-- Page 16 -->

*17* *TD-MPC*与*TD-MPC2*的关系 16

## 17 TD-MPC与TD-MPC2的关系

TD-MPC TD-MPC2 方面 latent model + MPC + TD 核心思想 保留该主线并加强稳定性 value 与扩展性 TOLD，decoder-free 世界模型 改进的隐式世界模型 latent稳定性 latent约束较弱 使用SimNorm reward/value预测 101-bin离散回归 连续回归为主 Q函数 较少Q函数 默认5个Q，随机抽两个取 min policy prior 确定性策略加噪声 最大熵随机策略 task embedding、zero- 多任务支持 较有限 padding、action mask 超参数 更依赖任务调节 强调同一套超参数跨任务 使用 展示1M到317M的scaling 扩展性 直接放大不一定稳定

## 18 默认5M TD-MPC2的关键超参数

超参数 值 含义 Planning horizon 3 每次向前模拟3步 Population size 512 每轮采样512条动作序列 Elites 64 用最好的64条轨迹更新分 布 Planning iterations 6 每个环境步迭代优化6次 Replay buffer 106 最多存一百万条经验 Batch size 256 每次训练采样256条数据 UTD 1 每收集一步数据更新一次 模型 Latent dim 512 latent state维度 Task embedding dim 96 多任务中任务向量维度 Q functions 5 Q ensemble数量 Reward/value bins 101 离散回归bin数 Learning rate 3*×*10*−*4 主网络学习率 Encoder LR encoder学习率更小 1*×*10*−*4 Gradient clip 20 防止梯度过大

<!-- Page 17 -->

*19* 17 把整套系统想成机器人脑内结构

## 19 把整套系统想成机器人脑内结构

可以把TD-MPC和TD-MPC2想成一个机器人脑内系统：

部件 作用 环境 给真实状态转移和真实奖励 Replay buffer 存过去经验 Encoder 把真实状态压缩成latent state Dynamics model 在latent空间里想象未来 Reward model 判断短期行为好不好 Q function 判断长期前途好不好 Policy prior 给规划器动作建议 MPPI planner 在脑内试很多动作序列并选第一步执行 最重要的记忆方式是：

TD-MPC不是直接学一个策略就结束，而是学一个能在latent空间里想象 未来的模型，再每一步现场规划。

TD-MPC2进一步把这个系统变成更稳定、更通用的版本：

TD-MPC2 =稳定latent表示+稳定value target +保守Q ensemble +最 大熵动作先验+多任务统一接口。

## 最后总结

如果只记住一条主线，应当是：

TD-MPC解决的是如何用learned latent model做规划；TD-MPC2解决的 是如何让这条路线稳定、少调参、多任务、可扩展。

TD-MPC的聪明之处在于，它不要求世界模型还原所有细节，只要求模型预测对控 制有用的信息。TD-MPC2的聪明之处在于，它发现真正阻碍这种方法规模化的不是单个 公式，而是一组稳定性和工程鲁棒性问题：latent会爆、reward尺度不一、Q会过估计、 policy会塌缩、多任务维度不齐。于是TD-MPC2用SimNorm、离散回归、Q ensemble、 EMA target、最大熵policy prior、zero-padding和action mask，把这条方法链条补强。
