# 8.2 策略训练：模仿学习与后训练

行为克隆，英文是 Behavior Cloning，常缩写为 BC，指把 imitation learning（模仿学习）写成一个监督学习问题：给定 observation（观测，例如机器人关节状态、相机图像、任务文本）预测 expert action（专家动作，也就是人类遥操作、脚本策略或高质量策略给出的动作）。如果第 6 章把数据采好、对齐好、标注好，本节的 BC 就是第一条真正能训练出策略的路线。

BC 的优势是直接、稳定、工程成本低。它不需要设计 reward（奖励函数），也不需要在真机上大量试错；只要有示教数据，就可以做离线训练。BC 的限制也同样直接：它只学习数据里出现过的状态和动作，一旦部署时自己的小错误把机器人带到训练集中没见过的状态，模型就可能继续错下去。

本节是策略训练二级目录的父页，按一条训练主线组织：行为克隆（本页正文与 ACT、Diffusion Policy、DAgger 三节）→ VLA 的 SFT/co-training 数据配比（VLA 训练范式）→ 跨具身训练（多具身体训练）→ RL 后训练指针（VLA 的 RL 后训练，实操在第 9 章）。ACT 和 Diffusion Policy 不是孤立方法，它们都是把 BC 的动作预测目标做成 action chunk 或 action trajectory 的高级形式。本节先讲普通 BC，再把子页串起来。

## 本组页面

- [ACT](02-behavior-cloning/01-act.md)：用 Transformer 一次预测动作片段。
- [Diffusion Policy](02-behavior-cloning/02-diffusion-policy.md)：用条件去噪生成动作轨迹。
- [DAgger](02-behavior-cloning/03-dagger.md)：用交互式标注缓解 covariate shift。
- [VLA 训练范式](02-behavior-cloning/04-vla-training-paradigms.md)：web+robot co-training 与 SFT 数据配比。
- [多具身体训练](02-behavior-cloning/05-multi-embodiment-training.md)：跨具身数据混合与动作空间统一。
- [VLA 的 RL 后训练](02-behavior-cloning/06-vla-rl-posttraining.md)：奖励设计分类与指针，实操见第 9 章。

## BC 要解决什么

在机器人里，BC 学的是一个 policy（策略）：输入当前观测，输出下一步动作。

```text
observation_t  ->  policy_theta  ->  action_t
```

其中：

- `observation_t` 是第 `t` 帧机器人能看到的信息，例如 `observation.state`、`observation.images.front`、`task`。
- `action_t` 是第 `t` 帧之后要执行的控制命令，例如关节目标、末端速度、夹爪开合。
- `policy_theta` 是带参数 `theta` 的模型，可以是 MLP（多层感知机）、CNN（卷积神经网络）、Transformer（基于注意力机制的序列模型）、Diffusion Policy（扩散策略）或 VLA（Vision-Language-Action，视觉-语言-动作模型）。

最经典的例子是 Pomerleau 的 ALVINN 自动驾驶系统：用摄像头和激光输入预测驾驶方向。现代机器人 BC 做的是同一件事，只是输入变成多相机图像、机器人 proprioception（本体感知，指关节角、速度、力矩等内部状态）、语言任务，输出变成更高维的机器人动作。

## 数学形式

设示教数据集为：

```text
D = {(o_1, a_1*), (o_2, a_2*), ..., (o_N, a_N*)}
```

这里 `o_t` 是 observation，`a_t*` 是 expert action，星号表示“专家给出的目标动作”。BC 训练的目标是让模型输出 `pi_theta(o_t)` 接近 `a_t*`：

```text
L_BC(theta) = (1 / N) * sum_t loss(pi_theta(o_t), a_t*)
```

如果动作是连续值，例如 6 个关节角加 1 个夹爪命令，最常见的是 mean squared error（均方误差，MSE）或 L1 loss（平均绝对误差）：

```text
MSE = mean((pred_action - expert_action)^2)
L1  = mean(abs(pred_action - expert_action))
```

如果动作是离散类别，例如“夹爪开/关”，可以用 cross entropy（交叉熵损失）。如果策略输出的是 Gaussian distribution（高斯分布），可以最大化 expert action 的 log likelihood（对数似然），也就是让专家动作在模型分布下概率更高。

这几个写法本质上都在回答同一个问题：在专家状态分布里，模型动作和专家动作有多接近？

## 训练样本长什么样

BC 的最小样本可以只有一帧观测和一个动作：

```yaml
observation.state: [joint_1, joint_2, ..., gripper]
observation.images.front: image_t
task: "pick up the red block"
action: [target_joint_1, target_joint_2, ..., target_gripper]
```

但机器人任务通常需要时间上下文。比如只看当前图像，模型可能看不出夹爪正在接近还是正在离开。于是样本常扩展成：

```text
past observations:  o_{t-k}, ..., o_t
future actions:     a_t, a_{t+1}, ..., a_{t+h-1}
```

LeRobot 的 `delta_timestamps` 就服务于这种窗口化读取：你可以让数据集返回过去几帧图像、当前状态，甚至未来一段 action。ACT 和 Diffusion Policy 更进一步，直接预测 action chunk（动作片段），也就是一次输出一段未来动作，而不是只输出下一帧动作。

对初学者来说，先分清三种训练方式：

| 目标 | 输入 | 输出 | 适合 |
|---|---|---|---|
| 单步 BC | 当前观测 | 下一步 action | 最小基线、调试数据 |
| 历史条件 BC | 最近几帧观测 | 下一步 action | 需要速度/趋势的任务 |
| Chunk BC | 最近观测 | 未来一段 action | 动作平滑、推理频率低、双臂细粒度任务 |

第一个版本最容易跑通。后两个版本更接近真实系统，但也更依赖数据对齐、episode 边界、padding mask（填充掩码，用来告诉模型哪些动作只是补齐长度，不应计入损失）。

## 输入和动作表示

BC 训练失败，很多时候不是模型太小，而是 observation 或 action 语义不清楚。

常见 observation 输入：

| 输入 | 含义 | 风险 |
|---|---|---|
| `observation.state` | 机器人本体状态，例如关节角、夹爪位置 | 维度顺序必须和动作一致记录 |
| `observation.images.*` | 一个或多个相机图像 | 相机移动、曝光变化、遮挡会改变分布 |
| `task` | 自然语言任务描述 | 同一动作对应多个任务时必须提供 |
| `observation.environment_state` | 仿真环境真值状态 | 真机通常没有，不能误当普通视觉输入 |

常见 action 表示：

| 动作 | 例子 | 注意事项 |
|---|---|---|
| absolute joint target（绝对关节目标） | 下一步目标关节角 | 容易和当前状态强绑定，真机控制器要一致 |
| delta joint action（关节增量动作） | 当前关节角加一个小增量 | 更像速度控制，但会累计误差 |
| end-effector delta（末端增量） | 末端 `dx, dy, dz, droll, dpitch, dyaw` | 需要 IK 或末端控制器 |
| gripper command（夹爪命令） | 开、关、目标宽度 | 连续/离散表示要统一 |

动作表示没有绝对正确，只有“采集、训练、部署是否同义”。如果录制的是 processed teleop action（处理后的遥操作动作），训练就应该学习这个语义；如果部署前又经过 clipping（裁剪）或安全处理，要记录被裁剪前后的区别，否则模型误差很难诊断。

## 数据准备

训练 BC 前，先做数据准备，不要直接把所有 episode 丢进模型。

1. 过滤：先用 `success=true` 且 `valid=true` 的 episode 建立基线。失败数据可以保留，但不要在最小 BC 里无标记混入。
2. 划分：按 episode、variation（变化条件）或场景划分 train/val/test，避免同一条 episode 的相邻帧同时进训练和验证。
3. 归一化：对状态和动作做 mean/std（均值/标准差）或 min/max（最小值/最大值）归一化，让不同维度的数值尺度可比。
4. 检查频率：确认 FPS、timestamp、frame_index 和动作延迟一致。
5. 检查动作范围：统计每一维 action 的 min/max/mean/std，找出常数维、异常尖峰和长期饱和。

ACT 参考项目代码体现了这些基本原则：`utils.py` 会统计 `action_mean/action_std` 和 `qpos_mean/qpos_std`，训练时把 action 和 qpos 归一化；读取 episode 时随机选一个 `start_ts`，仿真数据取从该时刻开始的一段 action，真实机器人数据则用 `max(0, start_ts - 1)` 做一个时间对齐修正，再用 `is_pad` 标记补齐的动作。LeRobot 的训练脚本也会用 dataset metadata 和 statistics 构造 preprocessor/postprocessor（预处理器/后处理器），把数据归一化和反归一化放进训练/部署流程里。

一个最小的数据审计函数可以这样写：

```python
def summarize_action_ranges(episodes, action_dim):
    values = [[] for _ in range(action_dim)]

    for episode in episodes:
        if not episode.get("success", False):
            continue
        for frame in episode["frames"]:
            action = frame["action"]
            if len(action) != action_dim:
                raise ValueError("action dimension mismatch")
            for i, value in enumerate(action):
                values[i].append(float(value))

    summary = []
    for i, dim_values in enumerate(values):
        if not dim_values:
            summary.append({"dim": i, "count": 0})
            continue
        mean = sum(dim_values) / len(dim_values)
        summary.append({
            "dim": i,
            "count": len(dim_values),
            "min": min(dim_values),
            "max": max(dim_values),
            "mean": mean,
        })

    return summary
```

如果某一维动作的 `min=max=0`，要确认它真的是固定维度，而不是数据写入失败。如果某一维夹爪命令只出现 0.5001 到 0.5002，也要怀疑夹爪没有被正确记录。

## 损失函数怎么选

BC 常见损失可以按动作类型选择：

| 动作类型 | 常用损失 | 解释 |
|---|---|---|
| 连续关节/末端动作 | MSE、L1、Huber | MSE 对大误差更敏感，L1 对离群点更稳，Huber 介于两者之间 |
| 离散夹爪开关 | cross entropy | 把开/关当分类问题 |
| 连续夹爪宽度 | MSE 或 L1 | 把夹爪当连续控制值 |
| action chunk | masked L1/MSE | 只在非 padding 的动作上计算损失 |
| 概率策略 | negative log likelihood | 让专家动作在模型分布下概率更高 |

一个带 padding mask 的 MSE 可以这样写。这里用纯 Python 展示逻辑，真实训练里通常用 PyTorch tensor 实现。

```python
def masked_mse(pred_actions, expert_actions, valid_mask):
    total = 0.0
    count = 0

    for pred, expert, valid in zip(pred_actions, expert_actions, valid_mask):
        if not valid:
            continue
        if len(pred) != len(expert):
            raise ValueError("action dimension mismatch")
        for p, e in zip(pred, expert):
            total += (float(p) - float(e)) ** 2
            count += 1

    return total / max(count, 1)
```

ACT 参考项目代码展示了更完整的版本：对 action chunk 用 L1 loss，并用 `action_is_pad` 去掉 padding 部分；如果启用 VAE（Variational Autoencoder，变分自编码器），还会加入 KL divergence（KL 散度，衡量模型潜变量分布和先验分布差异）的正则项。Diffusion Policy 虽然看起来不像“直接回归 action”，但训练时仍然是从数据中的 expert action trajectory 学习；在 LeRobot 0.5.2 参考实现里，MSE 的目标取决于 `prediction_type`，可以是噪声 `eps`，也可以是原始 clean action trajectory（干净动作轨迹）。

## 一个最小 BC 训练循环

概念上，BC 训练循环很短：

```python
for batch in dataloader:
    pred_action = policy(batch["observation"])
    loss = loss_fn(pred_action, batch["action"])
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
```

真实项目会多出几件事：

- 图像归一化、裁剪、resize。
- 状态和动作归一化。
- action padding mask。
- mixed precision（混合精度训练）和梯度裁剪。
- checkpoint（模型检查点）保存和恢复。
- validation loss、rollout（真实或仿真执行）success、视频可视化。

LeRobot 0.5.2 参考实现中 `lerobot_train.py` 的 `update_policy()` 就是这个结构：从 dataloader 取 batch，调用 `policy.forward(batch)` 得到 loss，用 accelerator 做反向传播，裁剪梯度，执行 optimizer 和 scheduler。`TrainPipelineConfig` 则把 dataset、policy、batch size、steps、eval frequency、output directory 等训练参数集中起来。

一个典型命令形态是：

```bash
lerobot-train \
  --policy.type=act \
  --dataset.repo_id=<user>/<dataset_name> \
  --batch_size=8 \
  --steps=20000 \
  --output_dir=outputs/train/bc_act_baseline
```

具体 `policy.type` 要和任务、数据格式、机器性能匹配。初学者不要一开始就追最大模型，应该先跑一个小基线，确认数据、动作、归一化和部署链路都对。

## 离线指标怎么看

BC 最容易误判的地方是：training loss 和 validation loss 看起来很好，但机器人 rollout（真实或仿真执行）失败。

离线训练时至少看：

| 指标 | 说明 | 典型问题 |
|---|---|---|
| train loss | 训练集误差 | 过高说明模型、数据或归一化有问题 |
| validation loss | 未参与训练的 episode 误差 | 只按帧随机划分会虚高可信度 |
| per-dim action error | 每一维动作误差 | 夹爪、腕部、底盘维度常被平均值掩盖 |
| gripper accuracy | 夹爪开关是否正确 | 连续 MSE 可能看不出开关时机错 |
| temporal smoothness | 动作是否抖动 | loss 低但真机动作可能高频振荡 |
| action saturation | 动作是否常到边界 | 可能是归一化或控制范围错 |

Validation loss 只回答“模型能否拟合留出的专家数据”。它不回答“模型犯错后能不能恢复”。机器人部署时，下一帧 observation 取决于上一帧模型 action，而不是专家 action。这会造成 covariate shift（协变量偏移）：训练看到的是专家访问的状态分布，部署看到的是模型自己访问的状态分布。

所以 BC 的最终评估必须包含 rollout：

- 仿真里固定种子和未见 seed 的成功率。
- 真机少量安全试验。
- 不同初始位置、物体姿态、光照、遮挡下的成功率。
- 失败视频分类：看错物体、动作延迟、夹爪时机错、碰撞、越界、无法恢复。

## 为什么 BC 会学成平均动作

BC 的一个经典问题是 multimodality（多模态性）：同一个 observation 下可能有多种合理动作。

例如桌上有一个方块，人类示教里一半从左侧绕过去抓，一半从右侧绕过去抓。如果模型用 MSE 训练一个确定性动作，最小化平均误差的结果可能是“从正中间伸过去”，但正中间刚好会撞到障碍物。这不是数据不够，而是损失函数和动作分布不匹配。

缓解方法包括：

- 让任务描述更具体，例如写明“从左侧接近”。
- 在数据里分阶段或分 mode（模式）标注。
- 使用 action chunk，让模型看到更长的动作意图。
- 使用概率策略、mixture density network（混合密度网络）或 Diffusion Policy 表达多个动作模式。
- 对同一状态附近的冲突动作做数据清理，确认不是时间对齐错误。

因此，低 MSE 不总是好策略；它可能只是把多个专家动作平均了。

## 训练集大小和基线顺序

一个实用的 BC 开发顺序：

1. State-only MLP：只用机器人状态，不用图像。它不能解决视觉任务，但能快速检查 action、归一化和训练循环。
2. Image + state CNN：加入单相机图像，确认视觉输入确实有用。
3. 多相机或历史帧：解决遮挡和运动趋势问题。
4. Action chunk：减少推理频率，提高动作连续性。
5. 更复杂策略：ACT、Diffusion Policy、SmolVLA 或其他 VLA。

如果 state-only 模型都学不会一个关节目标任务，问题通常不在视觉模型，而在数据 schema、动作语义、归一化、时间对齐或训练代码。这个顺序能避免一开始就把所有问题都藏进大模型里。

## 调参与工程细节

BC 的核心超参数不多，但每个都很实际：

| 参数 | 作用 | 建议 |
|---|---|---|
| batch size | 每次更新用多少样本 | 太小梯度噪声大，太大可能显存不够 |
| learning rate | 每步更新幅度 | loss 发散先降学习率 |
| steps/epochs | 训练时长 | 小数据容易过拟合，要看 validation 和 rollout |
| image augmentation | 图像增强 | 小幅颜色、裁剪可提高视觉鲁棒性，过强会破坏任务细节 |
| action normalization | 动作归一化 | 训练、评估、部署必须使用同一套统计量 |
| grad clip | 梯度裁剪 | 防止偶发大梯度破坏训练 |
| seed | 随机种子 | 记录模型初始化、数据 shuffle、仿真 seed |

对真机 BC，最重要的不是“loss 降到多低”，而是训练产物能不能复现：

- 数据集版本和 commit。
- 训练配置 JSON/YAML。
- normalization stats。
- checkpoint 路径。
- 评估 seed 和视频。
- 真机控制器版本和安全限制。

没有这些记录，就算某次训练成功，也很难复现。

## 常见错误

| 错误 | 表现 | 修正 |
|---|---|---|
| 按帧随机划分 train/val | validation loss 很低，换 episode 就失败 | 按 episode 或 variation 划分 |
| 失败轨迹混入成功 BC | 模型学到放弃、撞击或错误夹取 | 标注并过滤 `success/valid` |
| 忽略动作延迟 | 模型总是慢半拍 | 校正 observation-action 对齐 |
| 忽略 action clipping | 训练动作和真机执行动作不同 | 记录 raw/processed/sent action |
| 只看平均 loss | 夹爪或少数关键维度错误被掩盖 | 看 per-dim error 和阶段指标 |
| 图像增强太强 | 关键小物体被裁掉或颜色变错 | 用任务相关增强，不破坏目标 |
| 没保存 normalization stats | 部署动作尺度错 | stats 和 checkpoint 一起保存 |
| 过早上大模型 | 问题难以定位 | 先 state-only，再 image，再 chunk |
| validation 用同一场景 | 指标好但泛化差 | 留出未见位置、物体、操作者或光照 |

## 本节实践任务

用第 6 章的一个小数据集，设计并训练一个最小 BC baseline（基线模型）。实践产出至少包括：

- 数据说明：episode 数、成功 episode 数、action 维度、observation 字段、FPS。
- 划分规则：train/val/test 是否按 episode 或 variation 划分。
- 归一化统计：状态和动作的 mean/std 或 min/max。
- 模型配置：输入字段、模型类型、参数量、batch size、learning rate、训练 steps。
- 离线结果：train loss、validation loss、per-dim action error。
- Rollout 结果：成功率、失败视频或失败原因分类。
- 一段结论：下一步应该补数据、改 action 表示、做 DAgger，还是换成 action chunk 策略。

验收标准是：另一个人可以用你的数据版本、训练配置和 checkpoint 复现同一组离线指标，并能看懂为什么这个模型能或不能上真机。

## 学习检查清单

- 能用一句话解释 BC 为什么是监督学习。
- 能写出 `observation -> policy -> action` 的数据流。
- 能说明 MSE、L1、cross entropy、masked loss 分别适合什么动作。
- 能解释为什么 train/val loss 低不代表 rollout 成功。
- 能说明 covariate shift 对机器人 BC 的影响。
- 能列出 BC 训练前必须检查的数据质量项。
- 能读懂 LeRobot 训练循环里 dataset、policy、loss、optimizer、checkpoint 的关系。
- 能设计一个 state-only 到 image+state 的基线升级顺序。
