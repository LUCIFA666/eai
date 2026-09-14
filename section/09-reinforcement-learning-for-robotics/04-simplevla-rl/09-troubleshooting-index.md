# 10.4.8 故障排查与索引

> 最后一节，把常见的坑和关键信息汇总一下。跑实验的时候遇到问题，先翻这一节，大部分问题应该能找到答案。后面附了文件索引和参数速查表，方便快速定位。

---

## 10.4.8.1 常见问题与故障排查

### CUDA 显存不足（OOM）

这是最常见的问题，尤其是用 40GB 或者更小显存的卡的时候。

**报错信息**：
```
RuntimeError: CUDA out of memory. Tried to allocate ...
```

**解决方法，按优先级排序**：

**1. 减小 batch_size**

最直接的办法。默认 64 的话，试试 32 或者 16。batch 小了梯度噪声会大一些，但至少能跑起来。

```bash
--batch_size 32
```

**2. 减小 samples_per_query**

从 8 降到 4 或者 6。群体小了，优势估计会更不准，但显存压力小很多。

```bash
--samples_per_query 4
```

**3. 启用梯度检查点（gradient checkpointing）**

用时间换空间——前向传播的时候不存所有中间激活值，反向传播的时候重新算。显存能省 30-40%，但速度慢 20-30%。

```bash
--gradient_checkpointing
```

**4. 减小 max_new_tokens**

生成的 token 少了，KV cache 占的显存就少了。简单任务可以设小一点。

```bash
--max_new_tokens 1024
```

**5. 用更小的模型**

如果以上都试过了还是不行，那就只能换更小的模型了。比如从 7B 降到 1B 或者 3B。

一般来说，按 1→2→3→4 的顺序试，大部分情况都能解决。

### Flash Attention 编译失败

装 Flash Attention 的时候经常会编译失败，一般是版本不匹配的问题。

**报错信息**：
```
ModuleNotFoundError: No module named 'flash_attn'
# 或者
RuntimeError: FlashAttention only supports Ampere GPUs or newer.
```

**检查这几个版本是否匹配**：

- **CUDA 版本**：Flash Attention 2.x 需要 CUDA 11.6 以上，推荐 12.x
- **PyTorch 版本**：要跟 CUDA 版本对应，不能错配
- **gcc 版本**：太新或者太旧都可能编不过，推荐 9.x 或者 10.x
- **GPU 架构**：Ampere 及以上（A100、A800、H100、3090、4090 等），Turing 及以下不支持

**常用的安装命令**：

```bash
# 先装 PyTorch
pip install torch==2.4.0+cu124 --index-url https://download.pytorch.org/whl/cu124

# 再装 Flash Attention，加 --no-build-isolation
pip install flash-attn --no-build-isolation
```

`--no-build-isolation` 这个参数很重要——不加的话可能会用错 PyTorch 版本，导致编译失败。

如果还是编不过，可以试试直接装预编译的 wheel：

```bash
pip install flash-attn --no-build-isolation --no-cache-dir
```

或者去 Flash Attention 的 GitHub release 页面下载对应版本的 wheel 文件直接装。

### LIBERO / RoboTwin 导入错误

环境装好了但 import 失败，一般是路径或者依赖的问题。

**报错信息**：
```
ModuleNotFoundError: No module named 'libero'
# 或者
ImportError: cannot import name 'LiberoEnv' from 'libero'
```

**检查这几点**：

**1. 是不是装到了正确的 conda 环境里**

有时候 pip install 装到 base 环境去了，但运行的时候用的是另一个环境。

```bash
which python  # 看看当前用的是哪个 python
pip list | grep libero  # 看看有没有装
```

**2. 是不是需要从源码安装**

有些 benchmark 不支持 pip install，得 clone 下来然后 `pip install -e .`

```bash
cd LIBERO
pip install -e .
```

**3. 依赖是不是装全了**

LIBERO 依赖 robosuite、mujoco 这些，少一个都不行。看看 README 里的安装说明，一步一步来。

**4. Mujoco 是不是激活了**

老版本的 Mujoco 需要 license key，新版本（2.3+）不用了。如果用的是旧版，确认 key 是不是放对位置了。

### Vulkan 初始化失败（无头服务器）

在没有显示器的服务器上跑仿真环境，经常会遇到渲染相关的错误。

**报错信息**：
```
Vulkan: 初始化失败
# 或者
GLFWError: (65544) b'X11: The DISPLAY environment variable is missing'
```

**解决方法**：用虚拟显示。

**方法一：Xvfb**

```bash
# 安装
sudo apt-get install xvfb

# 运行的时候前面加 xvfb-run
xvfb-run -a python train.py
```

**方法二：VirtualGL + TurboVNC**

如果需要 GPU 加速的渲染（比如 Isaac Sim），Xvfb 可能不够，得用 VirtualGL。

```bash
# 启动虚拟显示
vglrun python train.py
```

**方法三：用 headless 渲染模式**

有些仿真环境支持 headless 模式，直接在代码里设：

```python
env = gym.make("Libero-v0", headless=True)
```

或者在启动命令里加：

```bash
--headless
```

具体看环境文档，每个环境的设置方式不太一样。

### 训练不收敛

跑了几千步，成功率还是跟 SFT 基线差不多，甚至还降了。

**先排查这几个常见原因**：

**1. SFT 基线是不是太弱了**

如果 SFT 成功率只有 1-2%，那 RL 可能也很难起来。试试：
- 增加 SFT 的演示数据
- 增加 SFT 的训练步数
- 确认演示数据的质量——是不是有很多噪声或者错误的演示

SFT 基线至少要到 5-10%，RL 才能比较稳地往上走。

**2. 学习率是不是太高了**

学习率太高的话，策略更新太猛，容易崩。试试降到 1e-6 或者 5e-7。

怎么判断是不是学习率太高？看 KL 散度——如果 KL 飙升得很快，或者成功率剧烈波动，大概率是学习率太高了。

**3. 温度是不是太高了**

温度 1.6 是默认值，但不是所有任务都适合。如果任务比较精细，高温采样可能导致动作太随机，学不到东西。试试降到 1.0 或者 0.8。

**4. 奖励函数是不是有问题**

确认成功检测是不是对的——会不会把失败的判成成功，或者把成功的判成失败。

可以手动看几条轨迹：
- 成功奖励的轨迹，是不是真的完成了任务
- 失败奖励的轨迹，是不是真的没完成

奖励信号错了的话，RL 肯定学不对。

**5. 动作归一化是不是错了**

这个比较隐蔽——归一化范围不对的话，模型输出的动作就会偏，要么动不起来，要么直接超范围。

检查一下：
- 训练数据里的动作范围是不是跟归一化参数对得上
- 推理的时候反归一化用的参数是不是跟训练时一样

### W&B 连接超时

服务器连不上 W&B 的时候，日志就记不了了。

**解决方法：用离线模式**

```bash
WANDB_MODE=offline python train.py
```

或者在代码里设：

```python
import wandb
wandb.init(mode="offline")
```

训练完了之后，再把离线日志同步上去：

```bash
wandb sync ./wandb/offline-run-xxx
```

如果完全不想用 W&B，也可以用 tensorboard，veRL 应该也支持。

---

## 10.4.8.2 关键索引

### 核心文件索引表

| 文件 | 作用 | 关键内容 |
|------|------|---------|
| `rob_dataset.py` | 数据集与任务配置 | DATASETS 字典、数据加载、动作归一化 |
| `rob_rollout.py` | Rollout 与环境交互 | 环境创建、轨迹采样、动态采样、奖励计算 |
| `grpo.py` | GRPO 算法实现 | 优势计算、策略比、非对称裁剪、Loss 计算 |
| `main_ppo.py` | 训练主循环 | 初始化、训练循环、Checkpoint、评估 |
| `align.json` | 超参数配置 | 学习率、batch size、温度、裁剪范围等 |
| `action_tokenizer.py` | 动作 token 化 | 动作→token 编码、token→动作解码、分块 |

前三个是最常改的——加新任务改 rob_dataset.py，加新环境改 rob_rollout.py，调算法改 grpo.py。

### 关键超参数速查表

| 参数 | 默认值 | 作用 | 调大的影响 | 调小的影响 |
|------|--------|------|-----------|-----------|
| `learning_rate` | 5e-6 | 策略更新步长 | 收敛快但易崩 | 稳但慢 |
| `batch_size` | 64 | 每步训练的查询数 | 梯度稳但显存大 | 梯度噪声大 |
| `samples_per_query` | 8 | GRPO 群体大小 | 优势准但显存大 | 优势噪声大 |
| `temperature` | 1.6 | 采样温度 | 探索多 | 探索少 |
| `eps_low` | 0.2 | 裁剪下限 | 允许更大幅度下降 | 限制更紧 |
| `eps_high` | 0.28 | 裁剪上限 | 允许更大幅度上升 | 限制更紧 |
| `max_new_tokens` | 2048 | 最大生成长度 | 支持长轨迹 | 显存小 |
| `action_chunk_size` | 8 | 动作分块大小 | 生成效率高 | 控制更精细 |
| `max_retries` | 5 | 动态采样重试次数 | 梯度信号更有效 | 训练更快 |

调参建议：
- 先调学习率，这是影响最大的参数
- 显存不够就减 batch_size 和 samples_per_query
- 训练不稳定就降低温度和学习率
- 收敛太慢就提高学习率或者温度

### 硬件配置与训练时间对照表

| 硬件配置 | 显存/卡 | 适用场景 | 单步时间（估算） | 10 万步总时间（估算） |
|---------|---------|---------|-----------------|---------------------|
| 8× A800 80GB | 80 GB | 推荐配置，完整训练 | ~30-60 秒 | ~80-170 小时 |
| 8× H100 80GB | 80 GB | 更快，完整训练 | ~20-40 秒 | ~55-110 小时 |
| 4× A100 40GB | 40 GB | 低配，需减 batch | ~60-120 秒 | ~170-330 小时 |
| 2× H100 80GB | 80 GB | 中等配置 | ~60-90 秒 | ~170-250 小时 |
| 1× 4090 24GB | 24 GB | 试水，只能跑小模型 | - | - |

注意：这些是粗略估算，实际速度取决于：
- 任务复杂度（环境 step 时间）
- 轨迹长度（max_steps）
- batch 大小
- 动态采样的重试率
- 网络和存储速度

一般来说，rollout 占总时间的 60-70%，训练更新占 20-30%，其他开销占 10% 左右。所以优化 rollout 速度是提升整体训练速度的关键。

---

## 小结

到这里，SimpleVLA-RL 的代码阅读笔记就全部结束了。

八节内容，从架构到环境，从数据到 rollout，从训练到实战，最后是故障排查和索引。整个体系走了一遍。

几个核心观点再强调一下：

1. **SimpleVLA-RL 的设计哲学是"少即是多"**——去掉 Critic、去掉 KL、用二元奖励、用动态采样，把能砍的都砍了，只留最核心的。换来的是低显存占用和稳定的训练。

2. **动作 token 化是关键**——把连续的动作空间离散化成 token，让 VLA 模型可以直接用语言模型的那一套方法来训练。RL 也因此变得简单——就是在 token 级别做策略优化。

3. **SFT + RL 的两阶段流程很实用**——SFT 给个好起点，RL 再精调。不用从零 RL，也不用完全依赖监督学习，两者结合效果最好。

4. **适配新机器人没有想象中难**——主要就是动作空间适配和环境包装器两块，核心算法不用改。

```

