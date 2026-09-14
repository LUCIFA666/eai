## 9.2.3 演员-评论家方法（Actor-Critic）

在前一节中我们讨论了策略梯度方法（REINFORCE），它虽然能够直接处理连续动作空间，但单纯依赖蒙特卡洛轨迹回报进行更新会导致极高的方差。为了降低方差，我们在策略梯度中引入了基线（Baseline），最理想的基线就是状态价值函数 $V(s)$。

既然需要 $V(s)$，我们就不如直接用一个神经网络来学习它。这就自然地引出了现代强化学习中应用最广泛的核心框架——**演员-评论家方法（Actor-Critic）**。

### 1. 架构核心：两大脑的职责分工

Actor-Critic 方法将价值函数和策略梯度结合起来，形成了两个协同工作的神经网络：

* **Actor（演员/策略网络）**：$\pi_\theta(a\vert{}s)$，负责根据当前状态选择动作。它通过接收 Critic 的评价来更新自身的动作概率。
* **Critic（评论家/价值网络）**：$V_\phi(s)$ 或 $Q_\phi(s,a)$，负责评估 Actor 选出的动作或当前状态的好坏。它通过环境给予的真实奖励来更新自身的评价准度。

在具身智能中，这就像是一个正在学习走路的机器人（Actor）和一个站在旁边的教练（Critic）。机器人尝试迈步，教练根据经验告诉它这一步走得好不好，机器人根据反馈调整下一步的姿态，同时教练也在观察中不断提升自己的评估眼光。

以下是 Actor-Critic 基础架构的 PyTorch 实现代码：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super().__init__()
        # Actor网络：输出动作分布参数（以连续控制为例输出均值和标准差）
        self.actor = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim * 2)  # 均值和标准差
        )
        
        # Critic网络：输出状态价值 V(s)
        self.critic = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, state):
        value = self.critic(state)
        actor_output = self.actor(state)
        mean, log_std = actor_output.chunk(2, dim=-1)
        std = log_std.exp()
        
        return mean, std, value

```

### 2. 数学桥梁：价值、优势与时序差分

要理解 Actor-Critic 的运作，必须理清几个核心评价指标的关系：

* **状态价值 $V(s)$**：在状态 $s$ 下，按照当前策略一直执行下去的期望总回报。
* **动作价值 $Q(s,a)$**：在状态 $s$ 下，**先执行动作 $a$**，然后按照当前策略一直执行下去的期望总回报。
* **优势函数 $A(s,a)$**：定义为 $A(s,a) = Q(s,a) - V(s)$。它衡量的是“采取动作 $a$”比“该状态下的平均表现”要好多少。

如果直接计算优势函数，我们需要同时拟合 $Q$ 网络和 $V$ 网络，这会带来巨大的计算开销。在实际工程中，我们通常使用时序差分误差（TD Error）作为优势函数的无偏估计：


$$\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)$$

**为什么 Critic 可以降低策略梯度的方差？**
在 REINFORCE 中，我们用一整条轨迹的真实回报 $G_t$ 来指导策略更新。而在 Actor-Critic 中，我们将 $G_t$ 替换为了由 Critic 计算出的 TD 目标 $r_t + \gamma V(s_{t+1})$。因为 $V(s)$ 是一个平滑的函数近似，它过滤掉了环境中由于单次随机事件引起的剧烈波动，从而极大地降低了策略梯度的方差。

### 3. Actor-Critic 的基本训练循环与 A2C/A3C

一个标准的 Actor-Critic 训练循环（以优势 Actor-Critic，即 A2C 为例）包含以下步骤：

1. **采样**：Actor 与环境交互，执行动作，获取奖励 $r$ 和下一状态 $s'$。
2. **估值与 Advantage 计算**：Critic 评估 $V(s)$ 和 $V(s')$，计算出 TD 误差（优势函数）。
3. **更新 Critic**：最小化价值估计的均方误差（MSE）。
4. **更新 Actor**：最大化优势加权的对数概率。

```python
def a2c_update(states, actions, rewards, next_states, dones, actor_critic, gamma=0.99):
    # Critic更新：最小化价值估计误差
    values = actor_critic.critic(states)
    next_values = actor_critic.critic(next_states)
    targets = rewards + gamma * next_values * (1 - dones)
    critic_loss = F.mse_loss(values, targets.detach())
    
    # Actor更新：最大化优势加权对数概率
    advantages = targets - values.detach()
    action_dist = actor_critic.get_action_dist(states) # 需自行实现分布获取
    log_probs = action_dist.log_prob(actions)
    actor_loss = -(log_probs * advantages).mean()
    
    # 总损失（实际应用中通常会加入策略的熵正则项以鼓励探索）
    total_loss = actor_loss + 0.5 * critic_loss
    return total_loss

```

为了加速训练，DeepMind 提出了**异步优势 Actor-Critic (A3C)**。A3C 摒弃了经验回放池，通过在多个 CPU 核心上启动多个并行的工作者（Worker）在不同环境实例中探索，然后异步更新一个全局网络，这既保证了数据的多样性，又大幅提升了训练速度。

### 4. 算法谱系：On-policy 与 Off-policy 的分支

我们常说的 PPO、DDPG、TD3、SAC 并不是孤立的算法，它们本质上都是 Actor-Critic 思想在不同方向上的延伸：

* **On-policy Actor-Critic（同策略）**：例如 A2C、TRPO、**PPO**。Critic 严格评估当前 Actor 的策略。这要求收集到的数据在更新网络后必须被丢弃。这类方法训练极其稳定，是目前大多数大模型微调和通用任务的首选。
* **Off-policy Actor-Critic（异策略）**：例如 DDPG、**TD3**、**SAC**。Critic 评估的是最优策略（类似于 Q-learning），因此可以使用经验回放池（Replay Buffer）重复利用历史数据。这类方法的样本效率极高，在数据获取成本高昂的机器人领域占据主导地位。

---

### 💡 机器人视角 (Robotics Perspective)

Actor-Critic 是目前机器人连续控制的绝对主干范式。无论是机械臂的灵巧操作还是四足机器人的越野行走，底层算法基本都隶属于 AC 谱系。

在实际的机器人训练中，一个核心的工程痛点是：**Critic 的不准会导致整个系统崩溃。**
如果 Critic 出现了“盲目乐观”（过度高估某个坏动作的 Q 值），Actor 就会迅速利用（Exploit）这个漏洞，导致策略网络朝着完全错误的方向更新。这就是为什么针对机器人的前沿算法（如 TD3 的双 Critic 取小值机制、SAC 的熵正则化、以及各类 Offline RL 算法）都会把核心精力放在**如何约束和修正 Q 函数的估计误差**上。

此外，在大语言模型（LLM）和视觉-语言-动作模型（VLA）的对齐与强化学习微调（RLHF / VLA-RL）中，Actor-Critic 依然是核心心智模型：

* 生成动作或文本的模型本身就是 **Actor**。
* 训练中的 Reward Model（奖励模型）和 Value Model（价值模型）承担了 **Critic** 的职责。
* 对生成轨迹进行 Advantage 估计并回传梯度，其底层逻辑与上述的 A2C 别无二致。
