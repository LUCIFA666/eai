# 多 GPU 与分布式

当单卡显存或吞吐不够时，可以把训练扩到多 GPU。多 GPU 不是把一个 PhysX scene 拆到多张卡上，而是每张卡跑一批环境和一个训练进程，再同步梯度。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-distributed-topology.svg" alt="多 GPU 分布式训练拓扑" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">多 GPU 训练中，每张卡各跑一批环境和一个 trainer rank，梯度通过 NCCL AllReduce 同步。</figcaption>
</figure>

## 本节目标

本节围绕下面几个问题展开：

1. 多 GPU 训练的基本原理是什么（每卡一批环境 + 梯度同步）？
2. 怎么用 `torchrun` 启动单机多卡和多节点训练？
3. `--num_envs` 是每卡还是总数，学习率怎么随 GPU 数缩放？
4. 哪些库适合多卡，多节点常见现象怎么判断？

## 基本原理

```text
GPU 0：num_envs 个环境 + trainer rank 0
GPU 1：num_envs 个环境 + trainer rank 1
GPU 2：num_envs 个环境 + trainer rank 2

每个 rank 独立采样
梯度通过 NCCL AllReduce 同步
总环境数 = GPU 数 * 每 GPU num_envs
```

在本页这种 `torch.distributed.run` 启动方式下，每个 rank 都会创建一份环境，因此 `--num_envs` 可以按“每个训练进程的环境数”理解；如果一张 GPU 对应一个 rank，它也就是每张 GPU 的环境数，而不是所有 GPU 加起来的总数。

<video src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-go2-32dogs-forward.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

并行训练的画面重点不在某一只机器人，而在“一批环境同时采样”。多 GPU 继续放大的也是这件事：每个 rank 各自推进一批环境，再同步策略梯度。

## 启动命令

以下命令需在已激活 Isaac Lab Python 环境的前提下运行（或把 `python` 换成 `./isaaclab.sh -p`）。

两张 GPU：

```bash
python -m torch.distributed.run --nproc_per_node=2 \
    scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-Velocity-Flat-Unitree-Go2-v0 \
    --num_envs 2048 \
    --distributed \
    --headless
```

四张 GPU：

```bash
python -m torch.distributed.run --nproc_per_node=4 \
    scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-Velocity-Flat-Unitree-Go2-v0 \
    --num_envs 2048 \
    --distributed \
    --headless
```

总环境数分别是 `2 * 2048` 和 `4 * 2048`。

## 支持哪些库

| 库 | 分布式支持 |
|---|---|
| RSL-RL | 支持 |
| RL-Games | 支持 |
| SKRL | 支持 |
| SB3 | 不适合作为 Isaac Lab 多 GPU 主线 |

如果目标是高吞吐多卡训练，优先考虑 RSL-RL、RL-Games 或 SKRL。

## num_envs 怎么选

| 任务类型 | 每卡环境数起点 |
|---|---|
| CartPole / 低维任务 | 8192 或更高 |
| 四足 locomotion | 2048-4096 |
| 灵巧手 / 接触密集 | 1024-2048 |
| 带 RGB 相机 | 128-512 |
| 带深度 / 多相机 | 更保守，从 64-256 起 |

先在单卡上找到不 OOM 的环境数，再乘以 0.8-0.9 留余量。

## 学习率缩放

多 GPU 会增大总 batch。学习率是否需要调整，要看算法配置和 reward 曲线；下面的开方缩放可以作为起点，而不是固定公式：

```text
lr_new = lr_base * sqrt(num_gpus)
```

在很多 PPO 任务里，开方缩放比线性缩放更保守。多卡后如果 reward 震荡或突然崩掉，先回到单卡学习率或降低学习率，再判断是否需要改 reward。

## 多节点

多节点就是跨机器训练。它不是在一台机器上启动两次，而是在多台机器上同时启动同一个训练脚本；每台机器有自己的 `node_rank`，所有机器通过主节点的 IP 和端口汇合。

跨机器训练适合下面几类场景：

| 场景 | 为什么需要多节点 |
|---|---|
| 单机 GPU 数不够 | 一台机器只有 4 张卡，但任务需要 8 张或更多卡的采样吞吐 |
| 单机显存不够 | 视觉任务、接触密集任务、多相机任务会让单机资源很快耗尽 |
| 想缩短大规模 RL 训练时间 | 每台机器各自采样一批环境，总采样吞吐随节点数增加 |
| 做大规模对比实验 | 多节点可以把同一套训练配置扩展到更大的环境总数 |

跨机器训练的核心收益是吞吐：每张 GPU 都跑一批 Isaac Lab 环境和一个 trainer rank，然后通过分布式后端同步梯度。代价是网络通信、节点同步和排障复杂度都会上升，所以通常先把单机多卡跑稳，再扩到多节点。

两台机器训练时，两边都要执行命令。区别只有 `--node_rank` 不同，`--master_addr` 都指向主节点的可访问 IP。

机器 0 作为主节点：

```bash
python -m torch.distributed.run \
    --nnodes=2 \
    --nproc_per_node=4 \
    --node_rank=0 \
    --master_addr=192.168.1.100 \
    --master_port=29500 \
    scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-Velocity-Flat-Unitree-Go2-v0 \
    --num_envs 2048 \
    --distributed \
    --headless
```

机器 1 作为第二个节点：

```bash
python -m torch.distributed.run \
    --nnodes=2 \
    --nproc_per_node=4 \
    --node_rank=1 \
    --master_addr=192.168.1.100 \
    --master_port=29500 \
    scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-Velocity-Flat-Unitree-Go2-v0 \
    --num_envs 2048 \
    --distributed \
    --headless
```

这里的含义是：

| 参数 | 含义 |
|---|---|
| `--nnodes=2` | 一共有 2 台机器参与训练 |
| `--nproc_per_node=4` | 每台机器启动 4 个训练进程，通常对应 4 张 GPU |
| `--node_rank=0/1` | 当前机器在多节点训练中的编号 |
| `--master_addr` | 主节点 IP，其他节点要能访问它 |
| `--master_port` | 分布式 rendezvous 端口，两台机器必须一致 |
| `--num_envs 2048` | 每个训练进程使用的环境数 |

这部分配置的总训练进程数是 `2 * 4 = 8`，总并行环境数是 `2 * 4 * 2048 = 16384`。如果只在机器 0 上运行，训练会一直等待机器 1 加入。

常见现象：

| 现象 | 含义 |
|---|---|
| `Setting OMP_NUM_THREADS ... to be 1` | `torch.distributed.run` 的正常提示，用于避免 CPU 线程过载 |
| `hostname of the client socket cannot be retrieved` | 主机名解析警告，不一定是失败；若后续不继续，优先检查网络 |
| 长时间没有训练日志 | 第二台机器没有启动、`node_rank` 配错、端口不通，或 `master_addr` 不是可访问 IP |

多节点训练的通信成本更高，只有在单节点多卡仍不够时再考虑。

## PBT

Population-Based Training 是一组策略并行训练、定期复制好策略并扰动超参的方式。Isaac Lab 中主要和 RL-Games 工作流相关。

它适合昂贵任务的超参搜索，但需要多倍 GPU 资源，不是入门训练必需项。

## 单机 2 GPU

第一次验证分布式时，建议先用 CartPole 这类小任务跑单机 2 GPU，而不是直接上四足或人形大任务。验收目标是 rank 能启动、NCCL 能同步、两个进程都进入训练日志。

```text
Synchronizing parameters for rank 0...
Synchronizing parameters for rank 1...
Learning iteration 0/2
Learning iteration 1/2
Training time: 4.05 seconds
```

多节点命令只有在所有节点同时启动时才算完成验证。它需要第二台机器在同一时间启动、`master_addr` 可达、`node_rank` 不重复、端口未被占用；只在当前机器启动 node 0 会一直等待 node 1。真正上两台机器时，应分别保存两端 stdout、stderr、GPU 分配和 checkpoint 目录，方便之后复盘通信和训练问题。

## 小结

- 多 GPU 是每卡一批环境和一个训练进程，梯度通过 NCCL 同步。
- 在本页命令中，`--num_envs` 是每个训练进程的环境数；总环境数要再乘训练进程数。
- 学习率可以从单卡配置或 `sqrt(num_gpus)` 缩放起步，再根据曲线调整。
- 多节点需要所有机器同时启动；`node_rank` 区分机器，`master_addr` 指向主节点。
- 多 GPU 适合 RSL-RL、RL-Games、SKRL；SB3 不作为大规模主线。

## 导航

- 上一页：[域随机化](05-domain-randomization.md)
- 返回目录：[训练与评测](../05-training.md)
- 下一页：[性能优化与调试](07-performance-debug.md)
