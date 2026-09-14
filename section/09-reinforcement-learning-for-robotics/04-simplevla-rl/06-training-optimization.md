# 10.4.5 代码走读：训练与策略优化

> 这一节读训练循环和策略优化，也就是 `main_ppo.py` 和 `grpo.py` 这两个核心文件。拿到 rollout 的轨迹和奖励之后，怎么用 GRPO 算法更新模型参数，是整个 RL 训练的核心。

---

## 10.4.5.1 Trainer 与训练循环

### main_ppo 是入口

训练的主入口在 `verl/trainer/main_ppo.py`，这是 veRL 框架提供的 PPO/GRPO 训练器。SimpleVLA-RL 直接复用了这个训练器，只是把数据、rollout、模型换成了机器人操作相关的。

启动之后，main_ppo 会按顺序做这些事：

1. 解析配置（align.json + 命令行参数）
2. 初始化分布式训练环境
3. 加载 SFT 模型作为初始策略
4. 创建数据加载器
5. 创建 rollout worker
6. 创建 actor（策略网络）
7. 进入训练循环

前面几步都是初始化，真正的训练在第 7 步的循环里。

### SFT 模型加载

训练不是从零开始的——先加载一个 SFT 之后的模型作为起点。SFT 模型已经学会了基本的操作技能，RL 只是在这个基础上进一步提升。

加载的代码大概长这样：

```python
# 伪代码
actor_model = OpenVLAOFTModel.from_pretrained(sft_ckpt_path)
actor_model = actor_model.to(device)
actor_model = DDP(actor_model)  # 分布式数据并行
```

`from_pretrained` 会加载权重、tokenizer、配置这些东西。加载完之后包一层 DDP，就可以分布式训练了。

注意：rollout 的时候用的也是同一个模型。训练和采样共享参数——每更新一次策略，rollout 用的就是更新后的新策略。这就是 on-policy RL 的特点。

### 分布式训练初始化

分布式这部分 veRL 已经封装好了，不用自己写。但知道几个关键点有助于理解代码：

**数据并行（DDP）**：每张卡存一份完整的模型，数据分到各张卡上，梯度通过 all-reduce 同步。7B 模型 + 8 张卡，这是最直接的方式。

**模型并行？**：7B 模型单张 80GB 卡能放下，所以不需要模型并行。如果以后换更大的模型（比如 70B），可能就要上张量并行了。

**Rollout 怎么分布？**：rollout 也是分布式的——每张卡负责一部分查询的采样，然后结果汇总到一起更新策略。

### Checkpoint 保存与恢复

训练过程中会定期保存 checkpoint，方便中断后继续训练，也方便挑最好的模型来评估。

保存的内容包括：
- 模型权重
- 优化器状态
- 学习率调度器状态
- 当前步数
- 其他训练状态

```bash
# 保存的目录大概长这样
checkpoints/
├── step_5000/
├── step_10000/
├── step_15000/
└── ...
```

恢复训练的时候，指定 `--resume_from_checkpoint` 就行，会从断点继续跑。

存储开销不小——7B 模型 + 优化器状态，一个 checkpoint 大概 40-50GB。训练 10 万步、每 5000 步存一次，就是 20 个 checkpoint，差不多 1TB。实际中一般不会存这么多，会设个上限，旧的自动删掉。

### 完整训练循环

把一个训练步拆开来看，一共七步：

**第 1 步：采样数据**

从数据集中采样一批查询（任务 + 初始状态）。batch_size=64 的话，就是 64 个不同的查询。

**第 2 步：Rollout 采样轨迹**

把这 64 个查询丢给 rollout worker，每个查询生成 8 条轨迹，总共 512 条轨迹。每条轨迹都有对应的动作 token、对数概率、二元奖励。

这一步是最耗时的——既要跑模型生成，又要跑仿真环境。

**第 3 步：计算优势**

对每个查询的 8 条轨迹，计算群体相对优势：

```python
# 伪代码
mean_r = rewards.mean(dim=-1, keepdim=True)
std_r = rewards.std(dim=-1, keepdim=True)
advantages = (rewards - mean_r) / (std_r + 1e-8)
```

成功的轨迹拿到正优势，失败的拿到负优势。加个 1e-8 防止除零。

**第 4 步：计算新策略的对数概率**

把轨迹重新喂给当前的 actor 模型，算出新策略下每个动作 token 的对数概率。

为什么要重新算一遍？因为 rollout 时候用的是旧策略，现在策略参数已经更新过几次了（PPO 一般会在同一批数据上更新多次），需要用最新的策略重新算 log_prob。

**第 5 步：计算 GRPO Loss**

这是核心的一步，下一小节详细讲。简单说就是：
- 算新旧策略的概率比 ratio
- 算裁剪后的 surrogate loss
- 用优势加权
- 取 min 之后求平均

**第 6 步：反向传播 + 参数更新**

```python
# 伪代码
optimizer.zero_grad()
loss.backward()
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
optimizer.step()
scheduler.step()
```

梯度裁剪是标配，防止梯度爆炸。学习率调度器一般用余弦退火或者线性衰减。

**第 7 步：记录日志，检查是否要验证或保存**

每一步都会把 loss、reward、KL、熵这些指标记到 W&B 或者 tensorboard 里。每隔 val_freq 步跑一次验证，每隔 save_freq 步存一次 checkpoint。

七步走完，一个训练步就结束了，然后回到第 1 步继续。

---

## 10.4.5.2 Actor 与策略优化

### Actor 模型结构

Actor 就是策略网络，也就是 OpenVLA-OFT 模型本身。没有额外的 Critic 网络，也没有额外的 head——直接用 VLA 模型当策略网络。

输入：图像 + 语言指令
输出：下一个动作 token 的概率分布（在整个词表上）

这个概率分布就是策略 π(a|s)——给定当前状态（图像 + 历史动作 + 指令），输出每个可能动作的概率。

### 动作 token 的概率分布

因为动作被离散化成了 token，所以策略输出的就是词表上的分类分布。每个位置输出一个 logits 向量，softmax 之后就是概率。

```python
# 伪代码
logits = model(input_ids=input_tokens, attention_mask=attention_mask)
# logits shape: (batch, seq_len, vocab_size)

probs = F.softmax(logits, dim=-1)
log_probs = F.log_softmax(logits, dim=-1)
```

取动作的时候，从这个分布里采样（训练时，温度 1.6）或者取最大概率的那个（推理时，贪婪）。

### GRPO Loss 怎么算

这是最核心的部分。一步一步拆开来看：

**第 1 步：算策略比 ratio**

```python
# 旧策略的对数概率（rollout 时候存的）
old_log_probs = batch["old_log_probs"]

# 新策略的对数概率（刚刚重新算的）
new_log_probs = compute_log_probs(actor_model, batch["input_ids"], batch["actions"])

# 概率比
ratio = torch.exp(new_log_probs - old_log_probs)
```

ratio > 1 表示新策略比旧策略更倾向于选这个动作；ratio < 1 表示更不倾向。

**第 2 步：算 surrogate loss**

```python
# 原始的 surrogate
surr1 = ratio * advantages

# 裁剪后的 surrogate
surr2 = torch.clamp(ratio, 1 - eps_low, 1 + eps_high) * advantages

# 取较小的那个（PPO 的 clip 目标）
surr = torch.min(surr1, surr2)
```

裁剪的目的是防止策略更新太猛——新旧策略差太多的话，梯度估计就不准了。

注意这里是**非对称裁剪**：
- 下限是 `1 - eps_low = 0.8`
- 上限是 `1 + eps_high = 1.28`

ratio 往上走可以走得更远，往下走被限制得更紧。上一节讲过为什么——鼓励提升好动作的概率，不要一下子把坏动作砍太狠。

**第 3 步：取负号，求平均**

```python
# 我们要最大化 surr，但优化器是最小化 loss，所以加个负号
loss = -surr.mean()
```

就这么简单。没有 KL 项，没有 value function loss，就这一项。

**第 4 步：反向传播更新**

跟普通的 supervised loss 一样，`loss.backward()` 然后 `optimizer.step()`。

### 为什么这么简单也能 work？

GRPO 的 loss 看起来比 PPO 简单很多——少了 Critic loss，少了 KL 项，少了 GAE。但实验证明它在 VLA 任务上效果很好。

原因大概有几个：

1. **SFT 初始化提供了好的起点**：策略已经在"正确的区域"了，不需要大幅调整
2. **二元奖励 + 动态采样**保证了每个 batch 都有有效的梯度信号
3. **群体相对优势**虽然不如 Critic 准，但在 8 个样本的情况下已经够用了

简单反而有好处——超参数少，不容易调崩，显存占用低。

---

## 10.4.5.3 设计取舍：为什么去掉 Critic 和 KL？

这两个设计选择是 SimpleVLA-RL 跟传统 PPO 最大的不同，也是最值得聊的地方。

### 为什么去掉 Critic？

传统 PPO 有两个网络：Actor（策略）和 Critic（价值函数）。Critic 的作用是估计每个状态的价值 V(s)，然后用来算优势函数 A = Q - V。

SimpleVLA-RL 把 Critic 整个去掉了，用群体相对优势代替。

**省显存**：这是最直接的好处。Critic 网络一般跟 Actor 差不多大（7B 参数），去掉之后每张卡省约 14GB 显存。再加上不用存 Critic 的优化器状态，又省 14GB。加起来一张卡省 28GB——8 张卡就是 224GB，很可观。

**省训练时间**：Critic 也要训练，每次迭代多一次前向和反向传播。去掉之后训练速度快不少。

**群体相对优势够用吗？**：在二元奖励 + 同初始状态的设定下，8 条轨迹的相对优势虽然有噪声，但方向基本是对的。GRPO 用裁剪来限制更新幅度，噪声大一点也不会崩。

**实验验证**：论文里做了消融，去掉 Critic 之后性能没有下降，某些任务甚至更好。可能是因为 Critic 在稀疏奖励下本身就难训练——价值函数估不准，反而会引入噪声。

### 为什么去掉 KL 正则？

KL 散度项的作用是防止新策略跟旧策略差太远，相当于一个"软约束"。传统 PPO 里经常加：

```
L = L_clip - β * KL(π_new || π_old)
```

SimpleVLA-RL 把 β 设成了 0，也就是完全没有 KL 约束。

**SFT 初始化是关键**：SFT 之后的模型已经有了合理的策略分布。RL 阶段只是微调，策略不会偏离太远——不需要 KL 来"拉着"。

**KL 反而会限制探索**：加了 KL 之后，策略不敢大胆尝试新动作，因为偏离参考模型太多会被惩罚。但 RL 训练的核心就是探索——不试怎么知道哪个动作好？实验发现，加了 KL 之后性能反而下降了。

**裁剪已经够了**：PPO 的裁剪机制本身就在限制策略更新的幅度——ratio 被限制在 [0.8, 1.28] 之间。有了这个硬约束，KL 软约束就不是必须的了。

**省显存**：又是省显存。KL 项需要一份"参考模型"的参数来算 KL 散度。去掉 KL 之后，参考模型也不用存了，又省 14GB。

### 加起来省了多少显存？

算一笔账：

| 项目 | 有 Critic + KL | 无 Critic + KL | 节省 |
|------|---------------|---------------|------|
| Actor 权重 | 14 GB | 14 GB | 0 |
| Critic 权重 | 14 GB | 0 | -14 GB |
| 参考模型权重 | 14 GB | 0 | -14 GB |
| Actor 优化器 | 28 GB | 28 GB | 0 |
| Critic 优化器 | 28 GB | 0 | -28 GB |
| **合计** | **98 GB** | **42 GB** | **-56 GB** |

一张卡省 56GB——这不是小数目。7B 模型在 80GB 卡上，有 Critic + KL 的话可能都放不下。去掉之后 42GB，还有 38GB 的空间给激活值和 KV cache，宽裕很多。

这就是为什么 SimpleVLA-RL 能在 8 张 A800 上跑 7B 模型的 RL 训练——把能砍的都砍了，只留最核心的。

---

## 10.4.5.4 训练监控指标

训练的时候要看哪些指标？几个关键的：

### 成功率 / 平均奖励

最直接的指标——模型在任务上的表现怎么样。

- **训练集成功率**：每一步 rollout 的平均奖励，也就是成功轨迹的比例。这个指标波动比较大，因为每个 batch 的任务不一样。
- **验证集成功率**：每隔 val_freq 步在固定的验证集上跑一次，结果更稳定。用来判断模型是不是真的在进步。

正常的训练曲线应该是：前期快速上升，中期慢慢涨，后期趋于平稳。LIBERO Spatial 这种简单任务，最后能到 95%+ 的成功率。

### KL 散度

虽然训练 loss 里没有 KL 项，但监控的时候还是要看——它能告诉你策略跟 SFT 基线差了多远。

```
KL(π_current || π_sft)
```

- KL 太小：策略没怎么变，可能学习率太低或者训练不够
- KL 太大：策略偏离太远，可能要崩了

一般 RL 训练中，KL 在 1-5 之间比较健康。如果突然飙升，说明训练不稳定了。

### 策略熵

熵衡量的是策略的"随机程度"——熵高，说明动作分布比较平，探索多；熵低，说明策略很确定，探索少。

```
Entropy = -Σ p(a|s) * log p(a|s)
```

训练过程中熵一般会逐渐下降——模型越来越确定"该做什么"。但如果熵降得太快太低，说明模型过早收敛到了次优策略，可能需要调高温度或者学习率。

### 梯度范数

梯度的 L2 范数，用来监控梯度爆炸或者消失。

- 梯度范数突然飙升：可能是 batch 里有异常数据，或者策略更新太猛
- 梯度范数一直很小：可能学习率太低，或者梯度消失了

有梯度裁剪在，一般不会炸，但监控一下还是好的。

### 其他指标

还有一些辅助指标：

- **裁剪比例**：有多少比例的 ratio 被裁剪了。太高说明策略更新太猛，太低说明学习率可能不够。
- **价值损失**：如果有 Critic 的话要看。SimpleVLA-RL 没有 Critic，所以不用管。
- **每步时间**：训练速度，用来估算总时间。

---

## 小结

训练与策略优化这一层，核心就是"简单但有效"：

- **训练循环七步走**：采样 → rollout → 算优势 → 重新算 log_prob → 算 GRPO loss → 反向传播 → 日志与保存
- **GRPO Loss 很简洁**：就一个裁剪的 surrogate loss，没有 Critic 项，没有 KL 项
- **砍 Critic 和 KL 是关键设计**：省了大量显存，让 7B 模型的 RL 训练成为可能，而且实验证明性能没降
- **监控四个关键指标**：成功率、KL 散度、策略熵、梯度范数

下一节讲 SFT 冷启动和完整的 RL 训练流程——从 SFT 开始，到 RL 训练收敛，再到评估和 checkpoint 管理。
```

