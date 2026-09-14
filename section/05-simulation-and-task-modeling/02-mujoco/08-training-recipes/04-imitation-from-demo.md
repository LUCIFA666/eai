# 行为克隆入门

RL 不是唯一的训练方法。当已经有“专家轨迹”（可能来自真人遥操作，也可能是脚本生成）时，模仿学习往往比 RL 更快、更稳。这一页给一个尽量简单的行为克隆配方：用前面抓取实战那一节跑出来的 demo，训一个小网络复现它。

## 本节目标

本节回答几个问题：

1. 模仿学习和强化学习的根本差别在哪？
2. “录 demo → 训最小模型 → 回放评估”这条路具体怎么走？
3. 行为克隆有哪些天生的局限？

## IL 和 RL 的差别

**模仿学习（Imitation Learning，IL）**是把专家动作当作标签，用监督学习直接拟合"看到什么观测 → 做什么动作"的映射。不需要奖励函数，也不需要在仿真里试错，但需要有专家示范数据。

**强化学习（Reinforcement Learning，RL）**是在仿真里通过试错和奖励信号来学习。不需要专家数据，但需要大量的环境交互和精心设计的奖励函数。

简单来说：IL = 有监督学习（有答案照抄），RL = 试错学习（自己摸索什么是好的）。

## 录 demo

从抓取流程录一段专家轨迹（下面的 `expert_policy` 和 `grasping_scene.xml` 是占位，替换成第 6 章抓取实战里的控制器和场景文件即可——比如就拿 reach 阶段的关节轨迹练手）：

```python
import numpy as np
import mujoco

observations = []
actions = []

model = mujoco.MjModel.from_xml_path("grasping_scene.xml")
data = mujoco.MjData(model)

for step in range(500):
    # 专家策略（可以是脚本控制器，也可以是遥操作记录）
    action = expert_policy(data)  # 返回 ctrl 数组

    # 记录观测和动作
    obs = np.concatenate([data.qpos, data.qvel])
    observations.append(obs)
    actions.append(action)

    data.ctrl[:] = action
    mujoco.mj_step(model, data)

# 保存为 .npz
np.savez("demo.npz", obs=np.array(observations), acts=np.array(actions))
```

## 行为克隆最小骨架

行为克隆（Behavior Cloning，BC）是最简单的 IL 方法：**用专家数据训练一个监督学习模型，输入是观测、输出是要执行的动作，损失函数是预测动作和专家动作之间的均方误差。**

下面用 PyTorch 写一个最小骨架，目的是把这条链路讲清楚，而不是追求工程完备；真要训一个能用的策略，通常会换成成熟框架（见本页末尾的说明）。

```python
import torch
import torch.nn as nn
import numpy as np

# 加载 demo
demo = np.load("demo.npz")
obs = torch.tensor(demo["obs"], dtype=torch.float32)
acts = torch.tensor(demo["acts"], dtype=torch.float32)

# 最简单的 MLP 策略
class Policy(nn.Module):
    def __init__(self, obs_dim, act_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, act_dim),
        )

    def forward(self, x):
        return self.net(x)

policy = Policy(obs.shape[1], acts.shape[1])
optimizer = torch.optim.Adam(policy.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

# 训练
for epoch in range(100):
    pred = policy(obs)
    loss = loss_fn(pred, acts)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    if epoch % 20 == 0:
        print(f"epoch {epoch}: loss = {loss.item():.6f}")

torch.save(policy.state_dict(), "bc_policy.pt")
```

## 训练 + 回放

训练时关注 loss 曲线：loss 持续下降，说明模型在逐渐拟合专家行为。不过 loss 低并不等于效果好。有时 loss 已经很低，但策略在实际环境里执行时会累积误差、慢慢偏离。所以评估时最好还是在仿真里实际跑一遍：

```python
# 在仿真里跑学到的策略（先重置到初始状态）
mujoco.mj_resetData(model, data)
for _ in range(300):
    obs_tensor = torch.tensor(
        np.concatenate([data.qpos, data.qvel]), dtype=torch.float32)
    with torch.no_grad():
        action = policy(obs_tensor).numpy()
    data.ctrl[:] = action
    mujoco.mj_step(model, data)
```

## 行为克隆的局限

BC 简单但有几个局限：
- **分布偏移**：训练时模型只见过专家的状态分布，执行时一旦偏离就会越来越错（误差累积）。
- **需要专家数据**：如果没有现成的 demo，需要额外成本去获取。
- **不会比专家更好**：BC 只能逼近专家，不能超越。

更高级的 IL 方法（如 DAgger、GAIL）和 RL 方法可以部分克服这些问题，前者深入见 [10 强化学习](../../../09-reinforcement-learning-for-robotics/README.md)。如果目标是训一个真正能上手的模仿学习策略，工程上一般不必从零手写：HuggingFace 的 [LeRobot](https://github.com/huggingface/lerobot) 提供了 ACT、Diffusion Policy 等成熟策略和统一的数据格式，面向真机部署，和 [07 数据](../../../06-data-teleoperation-and-imitation-learning/README.md) 一章的采集与组织流程能直接衔接。

## 小结

- 行为克隆 = 用专家 demo 做监督学习，把观测映射到动作。
- 录 demo → 训练 MLP → 在仿真里回放验证。
- BC 简单但受限于分布偏移和专家数据质量。

## 参考资料

- [LeRobot（HuggingFace，模仿学习策略与真机数据工具）](https://github.com/huggingface/lerobot)
- [MuJoCo Documentation: Python Bindings](https://mujoco.readthedocs.io/en/stable/python.html)
- [Ross et al., "A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning"（DAgger）, AISTATS 2011](https://arxiv.org/abs/1011.0686)

## 导航

- 上一节：[MJX + Brax 管线](03-mjx-brax-pipeline.md)
- 返回上级：[训练教程](../08-training-recipes.md)
- 下一节：[Sim2Real 指路](05-sim2real-pointers.md)
