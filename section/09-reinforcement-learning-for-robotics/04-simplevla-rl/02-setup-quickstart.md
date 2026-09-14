# 10.4.2 环境搭建与快速上手

> 这一节从零开始搭环境，从硬件要求到软件安装，再到基准环境跑通，一步一步来。环境搭好了才能读代码、跑训练。

---

## 10.4.2.1 硬件需求与配置

### 推荐配置

先说实话：SimpleVLA-RL 对硬件要求不低。7B 参数的 VLA 模型，加上 rollout 采样和环境仿真，没几张好显卡真跑不动。

官方推荐的配置是 **8 张 A800 或 H100，每张 80GB 显存**。这个配置下，LIBERO 上训练大概 1-2 天能收敛。

为什么需要这么多卡？主要是三个地方吃显存：

1. **模型权重**：7B 参数，FP16 下约 14GB
2. **优化器状态**：AdamW 要存动量和方差，也是 14GB 左右
3. **Rollout 采样**：同时生成 8 条轨迹，KV cache 占不少

三张加起来，单卡就要 40-50GB 显存。再加上梯度、激活值什么的，80GB 是比较宽裕的。

### 低配适配方案

如果没有 8 张 A800，也不是完全不能跑，就是得调小参数。几个常见的低配方案：

**4 张 A100 40GB**：
- batch_size 从 64 降到 32 或 16
- samples_per_query 从 8 降到 4（但会影响 GRPO 效果，不建议太低）
- 启用梯度累积，等效 batch size 不变
- 训练时间大概翻倍

**2 张 H100 80GB**：
- 基本能跑，但速度慢
- 可以考虑用更小的模型（比如 1.4B 版本，如果有的话）

**单卡试试水**：
- 不建议正经训练，但可以用来跑通流程、看代码
- batch_size=1，samples_per_query=2，能跑起来就算成功

### 显存估算

给你一个大概的显存账，方便自己估：

| 项目 | 显存占用（7B，FP16） |
|------|---------------------|
| 模型权重 | ~14 GB |
| 优化器状态（AdamW） | ~28 GB |
| 梯度 | ~14 GB |
| KV cache（rollout 时） | ~5-10 GB |
| 激活值 + 其他 | ~5 GB |
| **合计（训练时）** | **~60-70 GB** |

注意这是单卡的估算。如果用数据并行，每张卡都要存一份完整的模型和优化器状态。

### CPU 和内存

CPU 别太差就行，主要是环境仿真要用。LIBERO 这种基于 PyBullet 的环境对 CPU 要求不高，RoboTwin 或者 Isaac Lab 这种物理仿真就吃 CPU 多一些。

内存建议 128GB 以上。模型加载、数据缓存、并行环境都要吃内存。

---

## 10.4.2.2 软件环境安装

### 整体思路

安装顺序很重要，别乱装。建议按这个顺序来：

1. 先建 conda 环境，装 Python
2. 装 PyTorch（跟 CUDA 版本对应）
3. 装 veRL
4. 装 OpenVLA-OFT
5. 装 Flash Attention
6. 装基准环境（LIBERO / RoboTwin）

每一步都验证一下，别攒到最后才发现哪里错了。

### 第一步：Conda 环境

```bash
conda create -n simplevla python=3.10 -y
conda activate simplevla
```

Python 版本就用 3.10，太高太低都可能有兼容问题。

### 第二步：PyTorch

```bash
pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu124
```

注意是 CUDA 12.4 对应的版本。SimpleVLA-RL 和 veRL 都是基于 PyTorch 2.4 开发的，版本不对容易出奇怪的问题。

装完验证一下：

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

能输出版本号和 True 就行。

### 第三步：veRL

这一步要注意分支——**必须用 v0.2.x 分支**，不能直接装 main 分支。main 分支改动比较大，跟 SimpleVLA-RL 不兼容。

```bash
git clone https://github.com/volcengine/verl.git
cd verl
git checkout v0.2.x
pip install -e .
```

`-e` 是可编辑模式，后面改代码方便。

装完可以试试：

```bash
python -c "import verl; print(verl.__version__)"
```

能正常导入就说明基本没问题。

### 第四步：OpenVLA-OFT

这是 VLA 模型本体，也是 SimpleVLA-RL 的"大脑"。

```bash
git clone https://github.com/openvla/openvla-oft.git
cd openvla-oft
pip install -e .
```

如果要下载预训练权重，去 Hugging Face 找 `openvla/openvla-7b-oft`，大概 14GB 左右。

```bash
# 装一下 huggingface-cli 方便下模型
pip install huggingface_hub
huggingface-cli download openvla/openvla-7b-oft --local-dir ./checkpoints/openvla-7b-oft
```

### 第五步：Flash Attention

这一步最容易出问题，要有心理准备。Flash Attention 需要从源码编译，对 CUDA 版本、gcc 版本、PyTorch 版本都有要求。

```bash
pip install flash-attn --no-build-isolation
```

`--no-build-isolation` 这个参数很重要，不加的话可能会用错 PyTorch 版本。

如果编译失败，常见原因：

1. **CUDA 版本不匹配**：确保 `nvcc --version` 跟 PyTorch 的 CUDA 版本一致
2. **gcc 版本太新或太旧**：建议 gcc 9-12 之间
3. **内存不够**：编译时很吃内存，至少 32GB 内存

实在编译不过的话，可以试试预编译的 wheel：

```bash
pip install flash-attn --no-build-isolation --find-links https://github.com/Dao-AILab/flash-attention/releases
```

或者直接跳过——Flash Attention 是优化用的，没有它也能跑，就是慢一些、显存占得多一些。

### 第六步：其他依赖

```bash
pip install transformers accelerate datasets wandb einops timm
```

wandb 是用来打日志的，如果不想用可以跳过，但建议还是装一下，训练的时候看曲线方便。

---

## 10.4.2.3 基准环境安装

SimpleVLA-RL 支持好几个基准环境，最常用的是 LIBERO 和 RoboTwin。先从 LIBERO 开始，因为它安装最简单，对硬件要求也最低。

### LIBERO 安装

LIBERO 是基于 PyBullet 的机器人操作基准，包含 130 个任务，分四个套件。

```bash
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git
cd LIBERO
pip install -e .
```

装完验证一下：

```bash
python -c "import libero; print('LIBERO OK')"
```

如果报缺少资源文件的错，跑一下下载脚本：

```bash
python scripts/download_assets.py
```

LIBERO 的任务分四个 suite：
- LIBERO-Spatial：空间关系任务，最简单，适合入门
- LIBERO-Object：物体操作任务
- LIBERO-Objective：目标条件任务
- LIBERO-10：10 个精选任务，评测常用

### RoboTwin 安装（可选）

RoboTwin 是基于 Isaac Sim 的，安装麻烦一些，对显卡要求也高（需要 RTX 20 系以上，支持 Vulkan）。

如果要装的话：

```bash
# 先装 Isaac Sim（通过 Omniverse Launcher）
# 然后装 RoboTwin
git clone https://github.com/RoboTwin/RoboTwin.git
cd RoboTwin
pip install -e .
```

无头服务器上跑 Isaac Sim 可能会遇到 Vulkan 初始化的问题，需要装虚拟显示或者用 EGL 后端。这个坑后面故障排查那节再说。

### 最终目录结构

都装完之后，你的工作目录大概长这样：

```
workspace/
├── SimpleVLA-RL/       # 主仓库
├── verl/               # veRL 框架
├── openvla-oft/        # OpenVLA-OFT 模型
├── LIBERO/             # LIBERO 基准环境
├── RoboTwin/           # RoboTwin（可选）
└── checkpoints/
    └── openvla-7b-oft/ # 预训练权重
```

### 跑个最小测试

环境都装好了，跑个最小的测试确认一下：

```bash
cd SimpleVLA-RL
python -c "
import torch
from verl.workers.rob_dataset import RoboDataset
print('All imports OK')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU count: {torch.cuda.device_count()}')
"
```

能正常输出，没有报错，说明环境基本搭好了。

---

## 小结

环境搭建这一步，说难不难，说简单也不简单——主要是 Flash Attention 编译和 Isaac Sim 仿真环境容易出问题。

建议的节奏：
1. 先把基础环境（Python + PyTorch + veRL + OpenVLA-OFT）搭好
2. 装 LIBERO，跑通最简单的配置
3. 等训练跑通了，再考虑装 RoboTwin 或者 Isaac Lab 这些更复杂的环境

下一节正式进入代码，从配置入口和数据管线开始读。
```
