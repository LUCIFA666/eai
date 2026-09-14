# 基于模型的强化学习（Model-based RL）

目标：解释 model-based RL 的核心思路——学习环境动力学模型，再用模型规划或训练策略；介绍 TD-MPC2 和 DreamerV3 两个代表方法；厘清与 model-free RL 的权衡，以及与第 10 章 World Model 的关系。

## 核心思路

Model-free RL（PPO、SAC）直接从与环境的交互中估计价值函数或策略梯度，不显式建模环境的转移动力学。它的优点是实现简单、不依赖模型精度，但代价是样本效率低：需要大量真实交互才能收敛。

Model-based RL 的出发点是：如果能学到一个准确的**动力学模型**（dynamics model）——给定当前状态和动作，预测下一状态——那么就可以用这个模型做两件事：

1. **规划（planning）**：在模型内部搜索动作序列，不需要和真实环境交互。
2. **想象训练（imagination-based training）**：用模型生成虚拟轨迹，补充真实样本，提高样本利用率。

核心权衡：model-free 样本效率低但模型假设少；model-based 样本效率高但模型误差会传播，尤其在长 horizon 任务中，预测偏差会随步骤累积。

## 与 Model-free 的对比

| 维度 | Model-free（PPO/SAC） | Model-based（TD-MPC2/DreamerV3） |
|------|----------------------|----------------------------------|
| 样本效率 | 低 | 高 |
| 计算开销（推理） | 低 | 高（规划需多步前向） |
| 对模型误差的敏感度 | 不适用 | 高（长 horizon 误差累积） |
| 适合场景 | 仿真采样便宜 | 真机/样本昂贵 |
| 实现复杂度 | 低 | 高 |

## TD-MPC2：隐空间中的模型预测控制

TD-MPC2（Temporal Difference Model Predictive Control v2，Hansen et al. 2023）是 model-based RL 在机器人连续控制上表现最全面的方法之一。它的关键设计是把动力学模型放在**紧凑的隐空间**（latent space）里，而不是在原始观测空间预测。

核心组件：

- **编码器**：把高维观测（图像或状态向量）压缩成低维隐向量 `z`。
- **隐动力学模型**：给定 `z_t` 和动作 `a_t`，预测下一隐向量 `z_{t+1}`。
- **奖励预测头**：从 `(z_t, a_t)` 预测即时奖励。
- **价值函数**：在隐空间中估计长期回报，用于规划截断（不需要无限展开）。

规划时，TD-MPC2 在隐空间里用 **MPPI**（Model Predictive Path Integral）采样多条候选动作序列，评估累积奖励 + 价值函数，选出最优序列的第一个动作执行。

TD-MPC2 的突出特点是**跨任务通用性**：论文中一组网络权重在 100+ 个连续控制任务（DMControl、MuJoCo、Maniskill 等）上统一训练，验证了隐空间模型的泛化能力。

代码仓库：https://github.com/nicklashansen/tdmpc2

```python
# TD-MPC2 使用示例（简化版，参考官方仓库）
from tdmpc2 import TDMPC2

model = TDMPC2(cfg)          # 从 yaml 配置初始化
obs, _ = env.reset()

for step in range(total_steps):
    action = model.act(obs, t0=(step == 0))   # MPPI 规划选动作
    next_obs, reward, done, _, info = env.step(action)
    model.buffer.add(obs, action, reward, next_obs, done)
    if model.buffer.ready():
        model.update()       # 更新编码器 + 动力学模型 + 价值函数
    obs = next_obs
```

## DreamerV3：用世界模型做想象训练

DreamerV3（Hafner et al. 2023）走了另一条路：不在真实环境中规划，而是在**世界模型**（world model）内部展开完整轨迹，用想象中的经验训练策略。

DreamerV3 的世界模型是一个 **RSSM**（Recurrent State Space Model），包含：

- **循环隐状态**：用 GRU 编码历史，捕捉部分可观测性。
- **表征模型**：把观测编码到随机隐变量。
- **转移模型**：在隐空间预测下一状态的先验分布。
- **解码器**：从隐状态重建观测（用于监督世界模型训练）。
- **奖励和终止预测头**：在想象轨迹中提供训练信号。

策略训练完全在世界模型内部进行：给定当前隐状态，展开 H 步想象轨迹，用 actor-critic 算法（类 PPO 结构）更新策略，再以新策略收集少量真实数据更新世界模型。

DreamerV3 在 Atari、DMControl、Minecraft、机器人抓取等多个领域都达到了强竞争力的结果，且**超参数基本不需要针对任务调整**，这使它成为跨域 world model 研究的重要基准。

代码仓库：https://github.com/danijar/dreamerv3

## 与第 10 章 World Model 的关系

第 10 章（世界模型）从更宏观的视角讨论世界模型：大规模视频预训练、视频预测、场景理解。Model-based RL 可以看作**世界模型应用于策略优化的一个子方向**：

- 第 10 章的 world model 有时不直接用于控制，而是用于表征学习、视频生成、物理常识推理。
- Model-based RL 里的 world model（如 DreamerV3 的 RSSM）通常规模更小，专门为在线策略训练服务。
- 两者的技术基础高度重叠：隐空间建模、预测误差优化、不确定性估计。

理解 DreamerV3 的想象训练机制，有助于读懂第 10 章中关于 world model 用于 planning 的讨论。

## 什么时候用 Model-based RL

适合 model-based RL 的场景：

- **样本昂贵**：真机实验每步成本高，需要最大化每次交互的信息利用。
- **动力学结构明显**：机械臂运动学、刚体物理相对规律，模型容易学准。
- **需要长 horizon 推理**：规划能力帮助处理延迟奖励。
- **任务多样**：一组隐空间模型权重复用到多任务（TD-MPC2 的优势场景）。

不太适合的场景：

- **高频控制**：规划本身有计算延迟，50 Hz 以上控制频率压力较大。
- **接触密集**：接触动力学难以建模，模型误差高，规划效果下降。
- **仿真环境免费**：已有 Isaac Lab / MuJoCo 并行仿真时，model-free 的 PPO 通常更简单。

## 常见坑

- 模型误差累积：长 horizon 想象轨迹的预测误差指数累积，策略在真实环境里往往比想象中差。解决方向是缩短想象 horizon 并用价值函数截断。
- 模型过拟合：世界模型在训练数据上拟合但泛化差，尤其在数据量少的早期训练阶段。
- 规划开销：MPPI 需要并行采样大量候选序列，对 GPU 内存有要求。
- 忽视真实数据比例：想象轨迹比例太高时，策略会被模型偏差带偏；需要维持合理的真实数据更新频率。

## 延伸阅读

- Hansen et al. (2023) *TD-MPC2: Scalable, Robust World Models for Continuous Control* — https://github.com/nicklashansen/tdmpc2
- Hafner et al. (2023) *Mastering Diverse Domains through World Models (DreamerV3)* — https://github.com/danijar/dreamerv3
- 第 10 章世界模型（`section/10-world-models/`）
