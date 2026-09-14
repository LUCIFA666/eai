# 11.5 Policy 训练与评测

## 目标

前面几节已经介绍了 RLBench 的任务结构、观测空间和 demonstration 数据。接下来要关注的是：这些数据如何被 policy 使用，以及训练好的 policy 如何在 RLBench 中闭环评测。

读完本节后，你应该能够回答下面几个问题：

```text
RLBench 本身是否提供完整 policy 训练框架？
一个 policy 在 RLBench 中通常输入什么、输出什么？
demonstration 如何变成 imitation learning 数据？
如何在 RLBench 中执行 policy 并统计 success rate？
训练和评测时最容易出现哪些接口不一致问题？
```

需要先明确一点：RLBench 主要提供 benchmark、任务 API、观测接口、action mode 和 demonstrations。它本身不是一个完整的深度学习训练框架。实际训练 ACT、Diffusion Policy、PerAct、VLA 或其他 policy 时，通常还需要研究者自己写 dataset、model、trainer 和 evaluation loop。


## Policy 训练与评测的整体流程

从 demonstration 到 policy 评测，通常可以分成下面几步：

```text
生成 / 读取 demonstrations
-> 整理 observation-action 训练样本
-> 训练 policy
-> 在 RLBench 环境中 reset task
-> policy 根据 observation 输出 action
-> task.step(action)
-> 根据 success / terminate 统计 success rate
```

可以理解为：

| 阶段 | 输入 | 输出 |
| --- | --- | --- |
| 数据准备 | RLBench demonstrations | observation-action 样本 |
| Policy 训练 | 图像、状态、语言描述、专家动作 | 训练好的 policy |
| 闭环评测 | 当前 observation | policy action |
| 指标统计 | 多次 episode 成功 / 失败 | success rate |

其中最容易出错的是接口对齐。也就是说，训练时 policy 看到的 observation、action 表示、相机视角和归一化方式，必须和评测时保持一致。

---

## RLBench 不直接等于训练框架

RLBench 是一个 benchmark environment，而不是一个完整 policy training library。它主要负责：

```text
提供任务
提供仿真环境
提供 observation
提供 action mode
提供 expert demonstrations
提供 success condition
```

而一个完整训练框架通常还需要自己实现：

```text
Dataset
DataLoader
Policy model
Loss function
Optimizer
Checkpoint
Evaluation loop
```

所以读 RLBench 时要分清两层：

| 层次 | RLBench 是否负责 |
| --- | --- |
| 任务定义 | 负责 |
| 仿真环境 | 负责 |
| demonstration 生成 | 负责 |
| observation 返回 | 负责 |
| success condition 判断 | 负责 |
| 深度学习模型结构 | 通常不负责 |
| 训练循环 | 通常不负责 |
| policy checkpoint 管理 | 通常不负责 |


## Policy 的输入和输出

一个 RLBench policy 通常可以抽象成：

```text
policy(observation, description) -> action
```

其中输入可能包括：

| 输入 | RLBench 来源 |
| --- | --- |
| 任务描述 | `descriptions` |
| RGB 图像 | `front_rgb`、`wrist_rgb`、`left_shoulder_rgb` 等 |
| 深度 / mask | `front_depth`、`front_mask` 等 |
| 机械臂状态 | `joint_positions`、`joint_velocities` |
| 夹爪状态 | `gripper_open`、`gripper_pose` |
| 低维任务状态 | `task_low_dim_state` |

输出则由 action mode 决定。比如前面使用过：

```python
action_mode = MoveArmThenGripper(
    arm_action_mode=JointVelocity(),
    gripper_action_mode=Discrete()
)
```

那么 policy 输出的 action 就要能被这个 action mode 正确解释：

```text
arm action + gripper action
```

如果训练时用的是 joint position action，而评测时环境设置成 joint velocity action，policy 输出和环境解释就会不一致，结果通常会很差，甚至直接报错。


## 从 demonstration 构造训练样本

一条 demonstration 可以看成一个 observation 序列：

```text
demo = [obs_0, obs_1, obs_2, ..., obs_T]
```

在 imitation learning 中，通常要把它整理成：

```text
(obs_0, action_0)
(obs_1, action_1)
(obs_2, action_2)
...
```

如果是语言条件策略，则变成：

```text
(description, obs_0, action_0)
(description, obs_1, action_1)
(description, obs_2, action_2)
...
```

直观地说，训练目标是让模型看到当前图像和状态后，输出和专家相似的动作：

```text
预测动作 policy(obs, description)
专家动作 expert_action
loss = prediction 和 expert_action 的差异
```

对于连续动作，常见 loss 是 L1 或 MSE；对于离散化 action token，则可能使用 cross entropy。


## 一个最小 Dataset 思路

下面给出一个教学版的 dataset 思路。它不是完整工程代码，而是说明 RLBench demonstration 如何被整理成训练样本。

```python
class RLBenchDemoDataset:
    def __init__(self, demos, descriptions):
        self.samples = []

        for demo in demos:
            for i in range(len(demo) - 1):
                obs = demo[i]
                next_obs = demo[i + 1]

                # 这里的 expert_action 只是示意。
                # 实际项目中需要根据 action mode 和 demo 保存字段确定动作来源。
                expert_action = next_obs.joint_positions

                self.samples.append({
                    "description": descriptions[0],
                    "front_rgb": obs.front_rgb,
                    "wrist_rgb": obs.wrist_rgb,
                    "joint_positions": obs.joint_positions,
                    "gripper_open": obs.gripper_open,
                    "action": expert_action,
                })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]
```

这里要注意一点：RLBench 的 observation 里包含很多字段，但不是所有字段都适合作为 action label。真实训练时，expert action 应该和你选择的 action mode 保持一致。比如使用 joint position 控制，就应整理成 joint position target；使用 end-effector pose 控制，就应整理成末端位姿动作。


## 常见 policy 输入形式

不同方法会使用不同输入。可以先按下面几类理解。

### 1. 低维状态 policy

低维状态 policy 只使用机器人和任务相关的低维状态，例如：

```text
joint_positions
gripper_pose
gripper_open
task_low_dim_state
```

优点是训练快，适合调试算法；缺点是不适合研究视觉泛化。

### 2. 单视角视觉 policy

单视角视觉 policy 通常只使用一个相机，例如：

```text
front_rgb + robot_state
```

这种设置比较适合入门，数据量和模型复杂度都比较可控。

### 3. 多视角视觉 policy

多视角 policy 会使用多个相机，例如：

```text
front_rgb
left_shoulder_rgb
right_shoulder_rgb
wrist_rgb
robot_state
```

这种输入更完整，可以缓解遮挡问题，但训练成本也更高。

### 4. 语言条件 policy

如果 policy 需要根据语言描述执行不同任务，则输入还要包括：

```text
descriptions
```

这种形式更接近 VLA：

```text
视觉输入 + 语言指令 + 机器人状态 -> 动作
```


## 训练阶段需要统一的配置

训练 policy 前，建议先固定下面几个设置：

| 配置 | 为什么重要 |
| --- | --- |
| task list | 决定训练哪些任务 |
| variation 范围 | 决定任务变化难度 |
| camera views | 决定 policy 看到哪些图像 |
| image size | 决定模型输入尺寸和显存 |
| action mode | 决定 action label 的含义 |
| normalization | 决定状态和动作数值尺度 |
| train / test split | 决定评测是否公平 |

这些配置不要在训练和评测之间随意改变。比如训练时只用 `front_rgb`，评测时却给 `front_rgb + wrist_rgb`，模型结构就对不上；训练时 action 是 joint position，评测时 action mode 是 joint velocity，动作语义也会错。


## Policy 评测的基本流程

RLBench policy 评测通常是闭环执行，而不是只在 demonstration 上算 loss。

评测流程可以写成：

```text
for each task:
    for each episode:
        descriptions, obs = task.reset()
        for t in range(max_steps):
            action = policy(obs, descriptions)
            obs, reward, terminate = task.step(action)
            if terminate:
                break
        记录这次 episode 是否成功
计算 success rate
```

对应伪代码：

```python
success_count = 0
num_episodes = 25

for episode in range(num_episodes):
    descriptions, obs = task.reset()

    for t in range(max_steps):
        action = policy.act(obs, descriptions)
        obs, reward, terminate = task.step(action)

        if terminate:
            break

    if reward > 0:
        success_count += 1

success_rate = success_count / num_episodes
print("Success rate:", success_rate)
```

这里的 `reward > 0` 只是简化写法。不同任务和不同版本中，成功判断可能还会结合 task 的 success condition 或 terminate 信息。



## 训练 loss 和闭环 success rate 的区别

训练时常见的 imitation learning loss 是：

```text
预测动作和专家动作的误差
```

例如：

```text
MSE(policy(obs), expert_action)
L1(policy(obs), expert_action)
CrossEntropy(action_token_logits, action_token_label)
```

但是评测时真正看的通常是：

```text
success rate
```

这两者不完全一样。训练 loss 低，不一定表示闭环执行成功率高。原因包括：

| 问题 | 说明 |
| --- | --- |
| compounding error | 一步预测误差会在闭环执行中逐渐累积 |
| distribution shift | 评测时 policy 进入的状态可能和 demonstration 中不同 |
| action scale mismatch | 动作归一化或反归一化不一致 |
| camera mismatch | 训练和评测使用的相机视角不同 |
| task variation mismatch | 训练和评测的 variation 不一致 |

所以 RLBench policy 最终一定要放回环境里闭环评测，而不是只看训练集 loss。


## 多任务评测

如果要评测多个任务，可以把 task class 放在列表里：

```python
from rlbench.tasks import ReachTarget, PushButton, OpenDrawer

tasks = [
    ReachTarget,
    PushButton,
    OpenDrawer,
]
```

然后分别统计每个任务的 success rate：

```text
ReachTarget: 0.80
PushButton: 0.60
OpenDrawer: 0.40
Average: 0.60
```

多任务评测时，要特别注意每个任务测试的 episode 数是否一致，否则 average success rate 可能不公平。


## 保存评测结果

建议评测时把结果保存成结构化文件，例如 JSON：

```python
import json

with open("eval_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

结果可以类似：

```json
{
  "ReachTarget": 0.8,
  "PushButton": 0.6,
  "OpenDrawer": 0.4,
  "average": 0.6
}
```

如果还保存视频或图片，可以按下面结构组织：

```text
eval_outputs/
├── eval_results.json
├── ReachTarget/
│   ├── episode_000.mp4
│   ├── episode_001.mp4
│   └── ...
└── PushButton/
    ├── episode_000.mp4
    └── ...
```

这样后续写报告或 debug 时更方便。

## 常见问题

### 1. 训练和评测 action mode 不一致

这是最常见问题之一。比如训练数据里的 action 来自 joint position，但评测环境用的是 joint velocity，模型输出就会被错误解释。

解决方法是：训练前先固定 action mode，并在数据生成、训练和评测中保持一致。

### 2. 图像视角不一致

训练时如果使用 `front_rgb`，评测时也应该使用相同视角。如果评测时改成 `wrist_rgb` 或多视角输入，模型通常无法直接使用。

### 3. 图像尺寸不一致

训练时图像如果被 resize 到 `128x128`，评测时也要保持一致。否则模型输入维度可能不匹配。

### 4. 状态和动作没有归一化

机械臂状态和动作数值尺度不同，如果不归一化，训练可能不稳定。训练时做了 normalization，评测时就必须做相同的 normalization 和 inverse normalization。

### 5. 只看 loss，不做闭环评测

imitation learning 的训练 loss 只能说明模型在 demonstration 数据上拟合得怎么样，不能直接代表机器人任务成功率。最终仍然要看 RLBench 中的 success rate。

---

## 本节小结

RLBench 的 policy 训练与评测可以压缩成下面这条链路：

```text
demonstrations
-> observation-action 样本
-> 训练 policy
-> task.reset()
-> policy.act(obs, descriptions)
-> task.step(action)
-> 统计 success rate
```

其中最关键的是接口一致性：

```text
训练和评测必须使用一致的 observation 配置
训练和评测必须使用一致的 action mode
训练和评测必须使用一致的图像尺寸和归一化方式
```

理解这一点后，再去接入具体模型，比如 ACT、Diffusion Policy、PerAct、VLA 或其他 imitation learning / reinforcement learning 方法，就会清楚很多：模型结构可以变化，但 RLBench 提供的任务、观测、动作和评测闭环是统一的。