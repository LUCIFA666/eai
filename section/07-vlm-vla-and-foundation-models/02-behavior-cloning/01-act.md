# 8.2.1 ACT

ACT 是 Action Chunking with Transformers 的缩写，中文可以理解为“用 Transformer 一次预测一段动作片段”。它最早在 ALOHA 系列工作中被用于低成本双臂精细操作任务，例如双臂搬运方块、插孔、开盖和整理物体。

这里有几个关键词需要先讲清：

- action chunk（动作片段）：不是只预测下一帧动作 `a_t`，而是一次预测未来一段动作 `[a_t, a_{t+1}, ..., a_{t+H-1}]`。
- Transformer：一种使用 attention（注意力机制）的序列模型。这里它不是用来生成文字，而是把图像、机器人状态和动作序列之间的关系建模出来。
- bimanual manipulation（双臂操作）：左右两条机械臂协同完成任务。它比单臂抓取更依赖时序协调，例如一只手扶住物体，另一只手插入或拉开。
- VAE/CVAE：Variational Autoencoder（变分自编码器）及其条件版本。ACT 用它来表达“同一个观测下可能有多种合理动作片段”的不确定性。

ACT 仍然属于行为克隆主线。它的训练数据来自人类遥操作、脚本策略或聚合后的示教数据，训练目标仍然是从 observation（观测）预测 expert action（专家动作）。它和普通 BC baseline 的关键差别是：BC baseline 常常每次预测一个动作，而 ACT 每次预测一个时间片段，并用 Transformer 和可选的 VAE 表达动作序列。

## ACT 解决什么问题

普通单步 BC 的数据流是：

```text
observation_t -> policy -> action_t
```

在机器人上，这种做法有三个常见问题：

1. 视野短。模型只对当前帧做反应，不显式预测接下来几十步的动作意图。
2. 动作抖。相邻两帧的预测可能不一致，真机表现为手臂顿挫、夹爪来回修正。
3. 多模态难。比如同一个方块既可以从左侧绕过去抓，也可以从右侧绕过去抓；单个平均动作可能落在两种策略中间，反而不可执行。

ACT 把数据流改成：

```text
observation_t -> policy -> [action_t, action_{t+1}, ..., action_{t+H-1}]
```

`H` 就是 `chunk_size`，也叫动作片段长度。模型一次给出未来 `H` 步动作，执行端可以连续执行这段动作，也可以每一步重新预测并把多个重叠片段做融合。

这样做的直觉是：机器人操作往往不是一帧一帧独立决策，而是一段连贯 motion（运动）。把一段未来动作作为监督信号，模型更容易学到“伸手、闭合夹爪、抬起、交给另一只手”这种局部技能。

但 action chunk 不是越长越好。片段太短，退化成单步 BC；片段太长，模型会在状态已经变化后继续执行过时动作。ACT 的工程调参，本质上是在“时序一致性”和“闭环反馈频率”之间找平衡。

## 数据样本长什么样

ACT 的一个训练样本不是完整 episode，而是从某个 episode 中随机抽一个起点 `start_ts`，然后取：

```text
input:
  observation at start_ts:
    qpos
    images from one or more cameras

target:
  actions from start_ts to future horizon
  is_pad / action_is_pad padding mask
```

`qpos` 是机器人关节位置。`is_pad` 或 `action_is_pad` 是 padding mask（补齐标记），表示某个时间步是不是真实专家动作；`True` 通常表示该位置是 padding（补齐出来的空位），不应参与动作监督损失。对 ALOHA 双臂任务，gym-aloha 和 ACT 参考项目代码使用 14 维连续动作：左臂 6 个关节位置、左夹爪 1 维、右臂 6 个关节位置、右夹爪 1 维。不同机器人可以有不同 action dimension（动作维度），所以不能把 14 当成通用常数。

ACT 参考项目代码中的 `EpisodicDataset` 做了几件重要的事：

- 从 `episode_{id}.hdf5` 读取 `/observations/qpos`、`/observations/images/{camera}` 和 `/action`。
- 随机选择 `start_ts`，只取该时刻的观测。
- 在模拟数据里取 `action[start_ts:]`；在真实机器人数据里取 `action[max(0, start_ts - 1):]`，这是 ACT 参考项目代码里的一个时间对齐 hack（临时工程修正），用于让真实机器人 observation-action 对齐更接近。
- 把未来动作补齐到原始 episode 长度 `episode_len`，不是直接补齐到 `chunk_size`。
- 用 `is_pad` 标记哪些 timestep 是补出来的，训练 loss 不应把它们当真实动作。
- 把图像从 `H x W x C` 转成 `C x H x W`，并除以 255。
- 用数据集统计量归一化 `qpos` 和 `action`。这里的数据集统计量后面会保存成 `dataset_stats.pkl`，包含 `qpos` 和 `action` 的均值、标准差等部署必须复用的数值。

这里要区分两层形状。ACT 参考实现的 dataloader 返回的是“从 `start_ts` 到 episode 末尾、再补齐到 `episode_len`”的长动作序列；进入 `ACTPolicy` 后，`policy.py` 才会把 `actions` 和 `is_pad` 截断到 `self.model.num_queries`，也就是训练命令里的 `chunk_size`。LeRobot 的 ACT dataset 则直接围绕 `action_delta_indices = range(chunk_size)` 组织训练样本，所以更接近 `(chunk_size, action_dim)` 的目标张量。

`is_pad` 很关键。假设 episode 长度是 400，`chunk_size=100`，如果 `start_ts=360`，真实未来动作只有 40 步。原始 ACT dataloader 会先补齐到 episode 长度；policy 截断到前 100 步后，其中 60 步是补齐空值。训练时如果把这 60 步也算进 loss，模型会被迫学习“接近 episode 结尾时输出 0 动作”，这会污染策略。

下面是贴近 ACT 参考项目代码的概念性伪代码，用来说明“dataloader 先补到 episode 长度，policy 再截断到 `num_queries`”。它省略了 HDF5 读取、图像堆叠和归一化，不是逐行复制：

```python
def build_reference_act_target(actions, start_ts, *, is_sim, num_queries):
    """Conceptual target construction matching original ACT data flow.

    actions: list of action vectors for one episode
    is_pad[t] == True means the timestep is artificial padding.
    """
    episode_len = len(actions)
    action_dim = len(actions[0])
    action_start = start_ts if is_sim else max(0, start_ts - 1)
    future = actions[action_start:]

    padded = []
    is_pad = []
    for i in range(episode_len):
        if i < len(future):
            padded.append(future[i])
            is_pad.append(False)
        else:
            padded.append([0.0] * action_dim)
            is_pad.append(True)

    # The original ACT policy truncates here before computing ACT loss.
    return padded[:num_queries], is_pad[:num_queries]
```

真实系统还要保存相机名、FPS、action 语义、夹爪归一化方式、控制频率和 observation-action 对齐。ACT 对时间对齐很敏感，因为它预测的是一整段未来动作；错一两帧可能让夹爪闭合、接触和抬起的时机全部偏掉。

## 模型结构

ACT 可以分成四块：

```text
images -> ResNet backbone -> image tokens
qpos/env_state -> linear projection -> state tokens
optional VAE encoder -> latent token
tokens + learned action queries -> Transformer -> action chunk
```

第一块是视觉编码。多相机图像先经过 ResNet backbone（残差网络视觉主干，一类常用的卷积神经网络图像编码器），变成一组 image feature tokens（图像特征 token）。Token 可以理解为 Transformer 处理的向量单元。

第二块是机器人状态编码。`qpos` 这样的低维状态通过线性层投影到和 Transformer 相同的 hidden dimension（隐藏维度），作为 state token。

第三块是可选的 VAE encoder。训练时，ACT 不只看当前观测，还能看到目标动作片段。VAE encoder 把 `[robot_state, action_sequence]` 编码成一个 latent distribution（潜变量分布），通常用均值 `mu` 和对数方差 `logvar` 表示。潜变量 `z` 让模型可以表示示教里的多种合理动作风格。

第四块是 Transformer 主体。它接收 latent token、state token、image tokens，再用一组 learned query（可学习查询向量）生成 `chunk_size` 个输出。每个 query 对应未来一个时间步，最后经过线性层输出动作向量。

用形状写，进入 ACT loss 前的训练 batch 大致是：

```text
observation.images: (B, num_cameras, C, H, W)
observation.state:  (B, state_dim)
action:             (B, chunk_size, action_dim)
action_is_pad:      (B, chunk_size)

model output:
actions_hat:        (B, chunk_size, action_dim)
```

这表示“模型实际监督的目标”形状。对原始 ACT 参考项目代码，这个形状来自 `ACTPolicy` 对 dataloader 长序列的截断；对 LeRobot ACT，这个形状来自 dataset 按 `chunk_size` 直接取出的 action window。

LeRobot 0.5.2 参考项目代码中的 ACT 默认配置体现了这个设计：

| 配置 | 默认值 | 含义 |
|---|---:|---|
| `n_obs_steps` | 1 | 当前实现只取当前观测步 |
| `chunk_size` | 100 | 一次预测 100 步动作 |
| `n_action_steps` | 100 | 每次调用策略后实际执行多少步，不能大于 `chunk_size` |
| `vision_backbone` | `resnet18` | 图像主干网络 |
| `dim_model` | 512 | Transformer hidden dimension |
| `n_heads` | 8 | 多头注意力头数 |
| `dim_feedforward` | 3200 | Transformer 前馈层维度 |
| `use_vae` | `True` | 使用变分目标 |
| `latent_dim` | 32 | 潜变量维度 |
| `kl_weight` | 10 | KL loss 权重 |

LeRobot 里还保留了一个重要工程注释：原始 ACT 实现虽然配置了多个 decoder layer，但由于实现问题，实际只用了第一层；LeRobot 为了匹配原始实现，把 `n_decoder_layers` 设为 1。读实现时不要只看论文或命令行参数，要确认实际 forward path。

## 训练损失

ACT 的训练损失由两部分组成。`masked_L1` 是 masked L1 loss（带 mask 的 L1 绝对误差），意思是只在 `action_is_pad=False` 的真实动作位置计算绝对误差，跳过 padding 位置：

```text
loss = masked_L1(actions_hat, actions, action_is_pad)
     + kl_weight * KL(q(z | state, actions) || N(0, I))
```

第一项是 masked L1。L1 loss 是绝对误差：

```text
|predicted_action - expert_action|
```

`masked` 表示只在真实动作上计算，不在 padding 位置计算。LeRobot 的实现会把 `~batch["action_is_pad"]` 扩展到 action 维度上，再对有效元素求平均。

第二项是 KL divergence（KL 散度）。它衡量 VAE encoder 输出的潜变量分布离标准正态分布 `N(0, I)` 有多远。对高斯分布，常见写法是：

```text
KL = -0.5 * sum(1 + logvar - mu^2 - exp(logvar))
```

`kl_weight` 控制“重构动作片段”和“让潜变量分布规整”之间的权衡。`kl_weight` 太小，潜变量可能记忆训练动作，泛化差；太大，模型可能忽略示教里的细节，动作变得保守或不够准确。

下面的纯 Python 版本展示了 masked L1 + KL 的核心逻辑：

```python
import math


def masked_l1_plus_kl(pred, target, is_pad, mu, logvar, kl_weight=10.0):
    total_abs = 0.0
    count = 0

    for t, padded in enumerate(is_pad):
        if padded:
            continue
        for p, y in zip(pred[t], target[t]):
            total_abs += abs(p - y)
            count += 1

    if count == 0:
        raise ValueError("action chunk has no valid target actions")

    l1 = total_abs / count
    kl = 0.0
    for m, lv in zip(mu, logvar):
        kl += -0.5 * (1.0 + lv - m * m - math.exp(lv))

    return l1 + kl_weight * kl, {"l1": l1, "kl": kl}
```

ACT 参考项目代码中的原始 ACT wrapper 使用 L1 加 KL；同一个实现里的 `CNNMLPPolicy` baseline 只预测第一步动作，并使用 MSE。这正好说明：ACT 不是“换了一个网络名字”，而是监督目标从单步动作变成了动作序列。

## 推理时怎样执行动作

训练时 ACT 预测完整 action chunk。部署时有两种常见执行方式。

第一种是队列执行：

```text
if action_queue is empty:
    predict a chunk of H actions
    push first n_action_steps actions into queue

each control step:
    pop one action from queue and send to robot
```

原始 ACT 代码里，默认 `query_frequency = num_queries`。`query_frequency` 是查询频率，表示策略每隔多少个控制步重新查询模型、重新预测一个 action chunk；默认情况下，预测 100 步就执行 100 步，再重新预测。LeRobot 把这件事显式拆成 `chunk_size` 和 `n_action_steps`：模型可以预测 100 步，但只执行前 50 步，然后丢弃剩下 50 步并重新观测。这种做法能提高闭环性。

第二种是 temporal ensembling（时间集成）。开启后，策略每一步都重新预测一个未来 action chunk。于是同一个执行时刻会被多个历史 chunk 预测到：

```text
time 0 predicts actions for 0..99
time 1 predicts actions for 1..100
time 2 predicts actions for 2..101
...
current time t has several candidate actions
```

Temporal ensembling 会把这些候选动作加权平均。注意它不是 LeRobot ACT 的默认行为：LeRobot 默认 `temporal_ensemble_coeff=None`，只有把这个系数设成数值时才启用；原始 ACT 也需要显式加 `--temporal_agg`。启用后常用指数权重，原始 ACT 使用的常见系数是 `0.01`。在 LeRobot 的实现说明里，候选动作按“较早预测到较新预测”的顺序加权：

```text
w_i = exp(-coeff * i)
```

当 `coeff` 为正时，较早预测的动作权重更高。这听起来反直觉，但它能保留 action chunk 的连贯意图；如果过度偏重新预测，模型会退回到逐帧反应，动作反而可能抖。

一个简化版融合函数如下：

```python
import math


def temporal_ensemble(candidates, coeff=0.01):
    """Blend action candidates for the same control step.

    candidates are ordered from oldest prediction to newest prediction.
    """
    if not candidates:
        raise ValueError("no action candidates")

    weights = [math.exp(-coeff * i) for i in range(len(candidates))]
    normalizer = sum(weights)
    action_dim = len(candidates[0])
    blended = [0.0] * action_dim

    for weight, action in zip(weights, candidates):
        for j, value in enumerate(action):
            blended[j] += weight * value / normalizer

    return blended
```

Temporal ensembling 的好处是动作更平滑，坏处是推理开销更高，因为每个控制步都要查询模型。在 LeRobot 里，只要启用 temporal ensembling，`n_action_steps` 必须为 1；原始 ACT 开启 `--temporal_agg` 时也会把 `query_frequency` 设为 1。实际调参时，不要把它当成无条件提升；它可能让策略更稳，也可能让响应变慢。

## ACT 训练流程

ACT 参考项目代码给出了一个完整的模拟实验流程。以 `sim_transfer_cube_scripted` 为例：

1. 用脚本策略生成 HDF5 数据。

```bash
python3 record_sim_episodes.py \
  --task_name sim_transfer_cube_scripted \
  --dataset_dir <data save dir> \
  --num_episodes 50
```

2. 可视化检查采集到的 episode。

```bash
python3 visualize_episodes.py \
  --dataset_dir <data save dir> \
  --episode_idx 0
```

3. 训练 ACT。

```bash
python3 imitate_episodes.py \
  --task_name sim_transfer_cube_scripted \
  --ckpt_dir <ckpt dir> \
  --policy_class ACT \
  --kl_weight 10 \
  --chunk_size 100 \
  --hidden_dim 512 \
  --batch_size 8 \
  --dim_feedforward 3200 \
  --num_epochs 2000 \
  --lr 1e-5 \
  --seed 0
```

4. 评估时使用相同命令加 `--eval`。如果要启用时间集成，再加 `--temporal_agg`。

```bash
python3 imitate_episodes.py \
  --task_name sim_transfer_cube_scripted \
  --ckpt_dir <ckpt dir> \
  --policy_class ACT \
  --kl_weight 10 \
  --chunk_size 100 \
  --hidden_dim 512 \
  --batch_size 8 \
  --dim_feedforward 3200 \
  --num_epochs 2000 \
  --lr 1e-5 \
  --seed 0 \
  --eval
```

这套脚本会保存 `dataset_stats.pkl`。`dataset_stats` 是数据集统计量，保存 `qpos` 和 `action` 的 mean/std（均值和标准差）等数值；`.pkl` 是 Python pickle 序列化文件。评估时会用同一套统计量做 pre-process（输入预处理）和 post-process（输出后处理）：

```text
qpos_normalized = (qpos - qpos_mean) / qpos_std
action = action_normalized * action_std + action_mean
```

如果训练和部署使用的统计量不一致，动作尺度会直接错掉。ACT 预测的是连续控制目标，归一化错误通常不是“性能下降一点”，而是“机器人动作完全不对”。

ACT 参考项目代码会做 rollout（把策略放进环境或真机控制闭环里跑完整个 episode 的试跑/评估）。ACT README 报告，在示例模拟任务和配置下，transfer cube 成功率大约可以到 90%，insertion 大约 50%。这些数字只能作为示例参考，不能当作所有机器人任务的承诺。不同相机、控制频率、任务难度、示教质量和动作空间都会显著改变结果。

## 和 LeRobot 工作流的关系

LeRobot 把 ACT 封装成一种 policy type。概念上，训练 batch 仍然包含：

```text
observation.image.*
observation.state
action
action_is_pad
```

`ACTPolicy.forward()` 负责把图像字段整理成 image list，调用 ACT 模型，然后计算 masked L1 和 KL。`ACTPolicy.select_action()` 则负责部署时的一步动作选择：

- 如果没有 temporal ensembling，就维护一个 action queue。队列空了才预测新 chunk。
- 如果启用 temporal ensembling，就每步预测新 chunk，并用 `ACTTemporalEnsembler` 融合重叠预测。
- 每次环境 reset 后必须调用 policy reset，清空 action queue 或 temporal ensemble 状态。

LeRobot 配置里的三个时间参数容易混淆：

| 参数 | 含义 | 调参建议 |
|---|---|---|
| `n_obs_steps` | 输入多少步历史观测 | ACT 参考实现目前默认只支持 1 |
| `chunk_size` | 模型一次预测多少步动作 | 由任务节奏和控制频率决定 |
| `n_action_steps` | 每次调用后实际执行多少步 | 必须小于等于 `chunk_size`；越小越闭环 |

如果控制频率是 50 Hz，`chunk_size=100` 代表模型预测未来 2 秒动作。对双臂搬运，这可能合理；对需要快速接触反馈的插孔或插线任务，2 秒可能太长，需要缩短执行步数或开启时间集成。

## 调参顺序

ACT 的参数很多，但不要一开始同时改。推荐顺序是：

| 项 | 先看什么 | 常见调整 |
|---|---|---|
| 数据质量 | episode 是否成功、动作是否平滑、相机是否稳定 | 先清洗数据，再训练 |
| action 语义 | 关节位置、末端位姿、夹爪范围是否一致 | 统一 action schema |
| 归一化 | `dataset_stats.pkl` 是否随 checkpoint 保存 | 部署必须加载同一份 stats |
| `chunk_size` | rollout 是否中途停顿或过度惯性 | 先试 50、100、200 这类量级 |
| `n_action_steps` | 是否需要更强闭环反馈 | 小于 `chunk_size` 会更频繁重规划 |
| `kl_weight` | 动作是否多样但不稳定，或过于平均 | 常从 10 附近开始扫 |
| temporal ensembling | 动作是否抖动 | 开启后观察响应是否变慢 |
| 训练时长 | loss plateau 后 rollout 是否还改善 | 真机任务常要继续训练更久 |
| batch size/lr | validation loss 是否震荡或发散 | 小 batch 通常配小学习率 |
| 相机视角 | 关键接触点是否可见 | 少加模型，多修视角 |

ACT 参考项目 README 特别提醒：真机数据更难建模，loss plateau（损失曲线进入平台期）之后，成功率和平滑性仍可能继续改善。因此不要只用 validation loss 决定停止训练；要看 rollout 视频、成功率、接触时机和动作平滑性。

## 常见错误

| 错误 | 表现 | 修正 |
|---|---|---|
| 忘记 mask padding | episode 末尾动作异常，模型学到输出 0 | 用 `action_is_pad` 或 `is_pad` 屏蔽补齐段 |
| 按帧切分 train/val | validation loss 很好，换 episode 失败 | 按 episode 或 variation 划分 |
| 训练和评估 stats 不一致 | 动作幅度整体错误 | checkpoint 旁保存并加载同一份 `dataset_stats.pkl` |
| `chunk_size` 过大 | 遇到偏差后继续执行旧计划 | 缩短 `n_action_steps` 或开启时间集成 |
| `chunk_size` 过小 | 动作像单步 BC 一样抖 | 增大片段或做 temporal ensembling |
| 相机顺序变化 | 离线 loss 正常，部署完全失败 | 固定 camera names 和输入顺序 |
| action 维度顺序错 | 左右臂或夹爪动作错位 | 用 schema 文档和可视化回放检查 |
| 夹爪归一化错 | 夹爪一直开或一直闭 | 记录 raw、normalized、sent action |
| 只看离线 loss | 真机接触阶段失败 | 必须做 rollout 和视频复盘 |
| 盲目加大模型 | 训练更慢但问题不变 | 先查数据、时间对齐和控制接口 |

特别注意：ACT 的失败经常看起来像“模型不够大”，实际原因可能是示教时间对齐错、夹爪控制延迟、相机看不到接触点、左右臂 action 顺序反了，或训练集里同一状态下混入了互相矛盾的动作。

## 何时使用 ACT

ACT 适合：

- 双臂或长时序操作，需要一段连续动作意图。
- 高质量示教数量不算巨大，但动作时序清晰。
- 视觉加状态输入，动作是连续控制目标。
- 普通 BC 单步预测抖动明显。
- 希望先用相对成熟的模仿学习 policy 做真机 baseline。

ACT 不一定适合：

- 任务强依赖高频触觉闭环，但观测里没有触觉或接触状态。
- 环境变化很大，需要长程语言规划或记忆。
- action schema 不稳定，数据来源混杂且没有统一归一化。
- 只有少量失败示教，成功动作分布不清楚。
- 需要表达非常复杂的多峰动作分布，此时可以考虑下一节的 Diffusion Policy。

和 Diffusion Policy 相比，ACT 的优势是结构直接、训练和推理链路相对清楚、在 ALOHA/LeRobot 生态里有成熟实现。Diffusion Policy 的优势是把 action trajectory 当成扩散生成过程，对复杂多模态动作分布更自然，但训练和推理成本、采样参数也更多。

## 本节实践任务

用一批 ALOHA 风格或 LeRobot 风格数据训练一个 ACT baseline。实践产出至少包括：

- 数据说明：episode 数、成功率、FPS、相机列表、state/action 维度。
- 动作片段配置：`chunk_size`、`n_action_steps`、是否使用 temporal ensembling。
- 模型配置：视觉 backbone、hidden dimension、KL 权重、batch size、learning rate、训练 epochs/steps。
- 归一化文件：action/state mean/std 保存在哪里，部署时如何加载。
- 离线指标：train loss、validation loss、masked L1、KL loss。
- Rollout 指标：成功率、平均 return、失败类型、视频路径。
- 对比实验：至少和单步 BC 或不同 `chunk_size` 的 ACT 做一次对比。
- 结论：当前瓶颈是数据、动作空间、模型、训练时长、还是真机控制接口。

验收标准是：另一个人可以根据你的数据版本、训练命令、checkpoint、统计量和评估命令复现离线指标，并能通过 rollout 视频判断 ACT 的动作片段是否连贯。

## 学习检查清单

- 能解释 ACT 和单步 BC 的区别。
- 能说明 `chunk_size`、`n_action_steps`、`query_frequency` 的关系。
- 能画出 `image/qpos -> Transformer -> action chunk` 的数据流。
- 能解释 VAE latent、KL loss 和 `kl_weight` 的作用。
- 能说明为什么 `action_is_pad` 必须参与 loss mask。
- 能读懂 ACT 的训练样本形状 `(B, chunk_size, action_dim)`。
- 能解释 temporal ensembling 为什么可能让动作更平滑，也可能让响应变慢。
- 能列出 ACT 上真机前必须检查的归一化、相机顺序、动作维度和时间对齐。
