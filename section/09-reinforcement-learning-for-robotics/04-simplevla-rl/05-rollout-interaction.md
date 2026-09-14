# 10.4.4 代码走读：Rollout 与环境交互

> 这一节读 `rob_rollout.py`，也就是模型跟环境交互的部分。这是 RL 训练里最"忙"的模块——既要调用模型生成动作，又要跟仿真环境通信，还要处理奖励和动态采样。理解了 rollout，整个训练流程就通了一大半。

---

## 10.4.4.1 Rollout 模块结构

### rob_rollout.py 是干什么的

简单说，这个文件的职责就是：**给我一个任务和初始状态，我返回 N 条轨迹和对应的奖励**。

输入：
- 初始状态（来自数据集）
- 语言指令
- 模型（策略网络）

输出：
- 每条轨迹的动作 token 序列
- 每条轨迹的对数概率（训练要用）
- 每条轨迹的二元奖励（0 或 1）

整个过程在 `RobRolloutWorker` 这个类里完成。

### 环境创建与封装

环境的创建在 `create_environment` 函数里。大概长这样：

```python
def create_environment(env_name, task_name, **kwargs):
    if env_name == "libero":
        from libero.envs import LiberoEnv
        env = LiberoEnv(task_name=task_name, **kwargs)
    elif env_name == "robotwin":
        from robotwin.envs import RoboTwinEnv
        env = RoboTwinEnv(task_name=task_name, **kwargs)
    else:
        raise ValueError(f"Unknown environment: {env_name}")
    
    # 包装一下，统一接口
    env = RobEnvWrapper(env, **kwargs)
    return env
```

不同的 benchmark 用不同的环境类，但外面包了一层 `RobEnvWrapper`，对外接口是统一的。这样后面的 rollout 逻辑不用关心具体是哪个环境——反正接口都一样。

`RobEnvWrapper` 主要做这些事：
- 统一 `reset()` 和 `step()` 的返回格式
- 处理图像预处理（resize、归一化）
- 处理动作的编码和解码
- 提供 `get_info()` 方法来检测任务是否成功

### max_steps 是怎么配的

每条轨迹不能无限跑下去，得有个最大步数。这个参数在数据集配置里就有了：

```python
# DATASETS 字典里的配置
"libero_spatial": {
    ...
    "max_episode_length": 500,
    ...
}
```

但注意，这是**环境步数**，不是 token 数。因为有动作分块（action chunking），模型一次生成 8 步动作，所以实际调用模型的次数大概是 500 / 8 ≈ 63 次。

`max_new_tokens` 这个参数（默认 2048）是模型侧的限制——每次生成最多输出多少个 token。两个限制同时生效，哪个先到就停哪个。

### 并行环境池

Rollout 的时候要同时跑很多条轨迹，串行跑太慢了。所以代码里维护了一个环境池——`env_process_pool`。

简单说就是：提前创建好 N 个环境实例，放在一个池子里。需要跑轨迹的时候，从池子里拿空闲的环境来用，用完了放回去。

并行度怎么定？一般跟 GPU 数量或者 batch size 有关。8 张卡的话，可能每张卡对应 8-16 个环境，总共 64-128 个环境并行跑。

实现上用的是 Python 的多进程（`multiprocessing`），每个环境跑在独立的进程里，互不干扰。这样即使某个环境崩了（比如仿真出错），也不会影响其他的。

---

## 10.4.4.2 Rollout 完整流程

把一条轨迹从开始到结束的完整流程拆开来看。

### 第一步：环境重置，拿到初始观测

```python
obs = env.reset(initial_state=init_state)
image = obs["image"]                # 相机图像，shape (H, W, 3)
instruction = task["instruction"]   # 语言指令
```

`reset()` 的时候传入初始状态，环境就会回到指定的初始布局——物体在指定位置，机器人在指定姿态。

返回的观测里最关键的就是图像，后面要喂给视觉编码器。

### 第二步：模型生成动作 token

这一步是核心。把图像和语言指令拼起来，喂给 OpenVLA-OFT 模型，让它生成一串动作 token：

```python
# 伪代码
input_tokens = tokenize_image(image) + tokenize_text(instruction)
action_tokens = model.generate(
    input_tokens,
    max_new_tokens=2048,
    temperature=1.6,      # 高温采样，增加多样性
    do_sample=True,
    num_return_sequences=8,  # 一次生成 8 条不同的轨迹
)
```

几个细节：

**为什么一次生成 8 条？** 因为 GRPO 需要同一个查询的多个样本才能算相对优势。8 是个比较合适的数——太少了优势估计不准，太多了显存和时间都扛不住。

**温度为什么是 1.6？** 上一节讲过——温度高，分布平，探索多。1.6 是论文里调出来的经验值，既能保证探索，又不会让动作太离谱。

**8 条轨迹是怎么生成的？** 有两种方式：
1. 并行生成：一次前向传播同时输出 8 条（batch 维度扩 8 倍）
2. 串行生成：一条一条生成

SimpleVLA-RL 用的应该是并行方式——把 batch 维度从 64 扩到 64×8=512，一次前向传播搞定。这样速度快，但吃显存。

### 第三步：把 token 解码成实际动作

生成出来的是 token ID，得转成机器人能执行的动作：

```python
# 伪代码
actions = action_tokenizer.decode(action_tokens)
# actions shape: (num_chunks, chunk_size, action_dim)
# 比如 (63, 8, 7) 表示 63 个分块，每个分块 8 步，每步 7 维动作
```

解码过程就是：
1. 把 token ID 映射回 bin 索引（0-255）
2. 把 bin 索引反归一化回真实动作值
3. 按分块大小重新组织成时间步序列

这一步是动作 tokenizer 的工作，具体实现在 OpenVLA-OFT 的代码里。

### 第四步：在环境里执行动作

解码出动作之后，就一条一条丢给环境执行：

```python
# 伪代码
rewards = []
for trajectory in all_trajectories:
    env.reset(initial_state=init_state)  # 每条轨迹都从同一个初始状态开始
    done = False
    step = 0
    
    while not done and step < max_steps:
        action = trajectory[step]
        obs, _, done, info = env.step(action)
        step += 1
    
    # 回合结束，判断成功还是失败
    success = info.get("success", False)
    rewards.append(1.0 if success else 0.0)
```

注意几个点：

**所有轨迹从同一个初始状态开始**：这很重要。GRPO 的"群体相对"是建立在"同一个查询、同一个初始状态"的基础上的。如果初始状态不一样，奖励就没有可比性了。

**奖励是二元的**：要么 1 要么 0，没有中间值。成功检测由环境的 `get_info()` 方法提供——每个任务都有自己的成功判据，比如"杯子是否在盘子里""方块是否被推到目标区域"。

**中间不给奖励**：只有回合结束的时候给一个最终奖励。这就是稀疏奖励 + 二元奖励的组合。

### 第五步：返回结果

最后把结果打包返回：

```python
return {
    "action_tokens": action_tokens,      # 动作 token 序列，训练要用
    "log_probs": log_probs,              # 每个 token 的对数概率，训练要用
    "rewards": rewards,                  # 每条轨迹的二元奖励
    "success_count": sum(rewards),       # 成功了几条
    "num_trajectories": len(rewards),    # 总共几条
}
```

`log_probs` 这个东西很重要——后面算策略比（ratio）的时候要用。模型生成的时候顺便把每个 token 的对数概率记下来，省得后面再算一遍。

---

## 10.4.4.3 动态采样的代码实现

### 为什么需要动态采样

上一节讲过这个问题：如果 8 条轨迹全成功或者全失败，优势就是 0，没有梯度信号。动态采样就是为了解决这个问题。

代码里大概长这样：

```python
# 伪代码
def rollout_with_dynamic_sampling(query, num_samples=8, max_retries=5):
    for attempt in range(max_retries):
        # 采样一批轨迹
        trajectories = model.generate(query, num_samples=num_samples, ...)
        rewards = evaluate_trajectories(trajectories)
        
        # 检查是不是全成功或全失败
        all_success = all(r == 1.0 for r in rewards)
        all_failure = all(r == 0.0 for r in rewards)
        
        if not (all_success or all_failure):
            # 有成功也有失败，这个 batch 有用
            return trajectories, rewards
        
        # 全成功或全失败，扔掉重采
        # print(f"Retry {attempt+1}: all {'success' if all_success else 'failure'}, resampling...")
    
    # 重试次数用完了，返回最后一批（即使全一样）
    return trajectories, rewards
```

逻辑很直接：采一批，检查奖励多样性，不行就重来。

### 同质性检测

检测逻辑就是看奖励集合的大小是不是 1：

```python
# 简洁写法
if len(set(rewards)) == 1:
    # 所有奖励都一样，重采
    continue
```

因为是二元奖励，所以只有两种情况会触发重采：
- 全是 0（全失败）
- 全是 1（全成功）

### 重试次数

`max_retries` 一般设 5 次左右。不能无限重试，不然训练会卡在这里。

什么时候会连续重试很多次？一般是训练后期——模型已经很强了，大部分任务都能一次成功，这时候全成功的概率就很高。

论文里的处理方式是：如果重试了 N 次还是全成功，那就接受这批数据——虽然优势是 0，但至少不会卡死训练。

### 动态采样对训练速度的影响

动态采样会增加 rollout 的时间，因为有时候要多跑几批。但这个开销是值得的——没有动态采样，训练根本不收敛。

实际训练中，重试率大概在 20-50% 之间，取决于任务难度和训练阶段。前期模型差，全失败多；后期模型好，全成功多。中间阶段重试率最低。

### 跟 GRPO 的配合

动态采样保证了每个 batch 都有正有负的优势信号，GRPO 才能有效更新策略。

可以这么理解两者的关系：
- **动态采样** 负责"选有信息量的 batch"
- **GRPO** 负责"用这个 batch 更新策略"

缺了任何一个，RL 训练都跑不起来。

---

## 小结

Rollout 这一层是训练的"数据生成器"——每一步训练都要先经过 rollout 拿到轨迹和奖励，然后才能更新策略。

核心流程五步走：
1. 环境重置，拿到初始图像和指令
2. 模型高温采样，生成 8 条不同的动作轨迹
3. 动作 token 解码成实际动作
4. 逐条轨迹在环境里执行，判断成功/失败
5. 动态采样检查，不行就重来

下一节看训练循环和策略优化，也就是拿到这些轨迹之后，怎么用 GRPO 来更新模型参数。
```
