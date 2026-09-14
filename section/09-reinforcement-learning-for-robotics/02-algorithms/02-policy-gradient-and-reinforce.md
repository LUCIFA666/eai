## 9.2.2 策略梯度与 REINFORCE (Policy Gradient / REINFORCE)

在 DQN 等基于价值（Value-based）的方法中，智能体的逻辑是“先评估动作的价值，再间接推导策略”。但这种方式在具身智能领域遇到了瓶颈：现实机器人的控制任务（如机械臂关节扭矩、自动驾驶方向盘转角）往往需要**连续动作空间**。直接对连续空间进行离散化会导致“维度灾难”和精度损失，且基于价值的方法推导出的策略往往是不连续的，训练过程不稳定。

既然我们的最终目的是要一个好策略，那为什么不直接学习策略本身呢？这就是策略梯度（Policy Gradient）的核心思想。

### 1. 策略梯度定理：数学基础

策略梯度方法直接使用参数化模型（如神经网络）来表示策略 $\pi_\theta(a\vert{}s)$。对于机器人连续控制，网络通常输出一个动作分布（如高斯分布）的参数（均值和标准差），允许智能体直接从中采样。这种方法不仅原生支持连续动作分布，还能很好地处理随机策略（Stochastic Policy）需求场景，自带随机探索机制。

通过梯度上升，我们直接优化智能体的期望回报：


$$J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}[R(\tau)]$$

其核心支撑是**策略梯度定理（Policy Gradient Theorem）**：


$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta} \left[ \sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t\vert{}s_t) \Phi_t \right]$$

公式直观地表明了优化的方向：$\nabla_\theta \log \pi_\theta(a_t\vert{}s_t)$ 指向提高当前动作发生概率的网络参数修改方向。如果动作的评价指标 $\Phi_t$ 为正，就增加该动作在对应状态下被选中的概率；反之则降低（“好的动作多做，坏的动作少做”）。

其中 $\Phi_t$ 可以是多种形式：

* **轨迹总回报**：$\sum_{k=t}^T \gamma^{k-t} r_k$
* **状态-动作值函数**：$Q^{\pi_\theta}(s_t, a_t)$
* **优势函数**：$A^{\pi_\theta}(s_t, a_t) = Q^{\pi_\theta}(s_t, a_t) - V^{\pi_\theta}(s_t)$

### 2. REINFORCE 算法：基本数据流与实现

REINFORCE 是最基础的蒙特卡洛策略梯度算法。它的基本数据流和运作逻辑非常直观：

1. **采样轨迹**：机器人在当前策略 $\pi_\theta$ 下与环境交互，收集一条完整的轨迹 $\tau = (s_0, a_0, r_0, s_1, a_1, r_1, \dots)$。
2. **计算回报**：使用蒙特卡洛方法，计算整条轨迹的回报。
3. **策略更新**：用回报加权对数概率（log-prob）的梯度，更新策略网络。

以下是基础的 REINFORCE 算法核心代码实现：

```python
import torch

class REINFORCE:
    def __init__(self, policy_network, lr=0.001):
        self.policy = policy_network
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=lr)
        
    def update(self, trajectories):
        losses = []
        for states, actions, returns in trajectories:
            # 计算对数概率 (log-prob)
            action_dist = self.policy(states)
            log_probs = action_dist.log_prob(actions)
            
            # 策略梯度损失（负号因为我们要最大化回报，而优化器默认梯度下降）
            loss = -(log_probs * returns).mean()
            losses.append(loss)
            
        # 梯度更新
        total_loss = torch.stack(losses).mean()
        self.optimizer.zero_grad()
        total_loss.backward()
        self.optimizer.step()
        
        return total_loss.item()

```

### 3. 策略梯度的局限性与减少方差的技术

尽管思想优雅，但基础的 REINFORCE 算法存在明显的痛点：

* **高方差**：环境往往具有随机性。蒙特卡洛回报估计方差极大，导致网络参数更新的方向左右横跳，训练极其不稳定。
* **样本效率低**：必须跑完一整局才能拿到回报进行更新（On-policy），且历史交互数据用完即弃，无法重复利用。
* **收敛缓慢**：由于梯度估计不准确，算法通常需要大量的交互才能收敛。

为了稳定训练，研究人员引入了以下几种核心的方差缩减技术：

#### 3.1 因果性（Causality）与回报归因

未来动作不影响过去奖励。因此，在评估动作时，不应使用整条轨迹的总回报，而应使用奖励至当前时刻的**轨迹级回报（Rollout Return）**：


$$\Phi_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$$

#### 3.2 基线（Baseline）方法

从回报中减去一个与当前动作无关的基线 $b(s_t)$，不改变梯度的期望值，但能显著减少方差：


$$\nabla_\theta J(\theta) = \mathbb{E} \left[ \sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t\vert{}s_t) (R_t - b(s_t)) \right]$$


最优基线理论值为状态价值函数 $V^{\pi_\theta}(s_t)$。这一思想直接引出了后续同时学习策略和价值网络的**演员-评论家（Actor-Critic）架构**。

#### 3.3 广义优势估计（GAE）

广义优势估计（GAE）进一步平衡了偏差与方差，通过引入衰减因子 $\lambda$ 定义了极其稳定的优势估计：


$$\hat{A}_t^{\text{GAE}(\gamma,\lambda)} = \sum_{l=0}^{\infty} (\gamma\lambda)^l \delta_{t+l}$$


其中 $\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)$ 为时序差分误差。

---

### 💡 机器人视角 (Robotics Perspective)

在真实的物理机器人任务中（如抓取、行走），环境充满随机性且往往面临极度稀疏的奖励（例如仅在最后成功抓取到物体后才获得微小奖励）。

纯 REINFORCE 算法由于样本效率和高方差问题，**很少作为实际机器人任务的 baseline 被直接部署**。然而，它是解释现代强化学习优化来源的基石。目前统治具身控制和机器人的先进算法（如 PPO、TRPO、A2C/A3C）全部建立在策略梯度的视角之上。

**对视觉-语言-动作模型（VLA）微调的意义：**
大模型时代，VLA 的强化学习微调（VLA-RL 或后训练阶段）高度依赖策略梯度算法。要读懂前沿工作的训练代码和 loss 设计，必须深刻理解 REINFORCE 体系中的几个核心变量：

* **log-prob**：动作分布的对数概率。
* **advantage**：引入基线后的优势评估（用于衡量当前动作究竟比平均水平好多少）。
* **rollout return**：轨迹级回报的归因与回传。

理解了 REINFORCE，才能真正掌握模型在现实世界中如何通过环境反馈来纠正和迭代自身的行为决策。
