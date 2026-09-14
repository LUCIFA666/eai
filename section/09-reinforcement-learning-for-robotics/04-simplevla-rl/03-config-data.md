# 10.4.3 代码走读：配置与数据

> 从这一节开始正式读代码。先从最外层的启动脚本和配置系统看起，再往里走数据加载的部分。搞清楚训练是怎么启动的、数据是怎么喂进去的，后面读 rollout 和训练循环才不会晕。

---

## 10.4.3.1 启动入口与配置系统

### 训练脚本长什么样

训练的入口在 `examples/` 目录下，几个 `.sh` 脚本分别对应不同的 benchmark。比如 LIBERO 的就是 `run_openvla_oft_rl_libero.sh`，RoboTwin 的就是 `run_openvla_oft_rl_robotwin.sh`。

打开一个脚本看看，大概长这样：

```bash
#!/bin/bash

# 环境变量
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
export WANDB_MODE=online

# 路径配置
ALIGN_FILE=./align.json
SFT_CKPT_PATH=./checkpoints/openvla-7b-oft
DATA_ROOT=./data

# 超参数
BATCH_SIZE=64
SAMPLES_PER_QUERY=8
LEARNING_RATE=5e-6
MAX_EPS=0.28
MIN_EPS=0.2
TEMPERATURE=1.6

# 启动训练
torchrun --nproc_per_node=8 -m verl.trainer.main_ppo \
    --config $ALIGN_FILE \
    --sft_ckpt_path $SFT_CKPT_PATH \
    --data_root $DATA_ROOT \
    --batch_size $BATCH_SIZE \
    --samples_per_query $SAMPLES_PER_QUERY \
    --learning_rate $LEARNING_RATE \
    --clip_ratio_max $MAX_EPS \
    --clip_ratio_min $MIN_EPS \
    --temperature $TEMPERATURE \
    --benchmark libero \
    --task_name libero_spatial \
    --image_size 224 \
    --max_steps 100000 \
    --save_freq 5000 \
    --val_freq 1000 \
    "$@"
```

结构很清晰：先设环境变量，再设路径，再设超参数，最后用 `torchrun` 启动训练。

### 配置是怎么传的

参数传递有两层：

**第一层：align.json**

这是 veRL 框架的主配置文件，里面定义了训练的基本结构——用什么算法、actor 怎么配、rollout 怎么配、数据怎么加载。大部分内容不用改，直接用默认的就行。

比如算法部分大概是这样：

```json
{
  "algorithm": {
    "name": "grpo",
    "kl_penalty": 0.0,
    "clip_ratio_low": 0.2,
    "clip_ratio_high": 0.28
  },
  "actor_rollout": {
    "model": {
      "path": "openvla_oft",
      "model_name": "openvla-7b-oft"
    },
    "rollout": {
      "temperature": 1.6,
      "max_new_tokens": 2048
    }
  }
}
```

**第二层：命令行参数**

shell 脚本里通过 `--xxx` 传的参数会覆盖 align.json 里的默认值。比如 `--learning_rate 5e-6` 就会把学习率改成 5e-6。

这种设计的好处是：通用配置写在 align.json 里，不用每次都传；需要调的超参数通过命令行传，方便跑实验对比。

### torchrun 分布式启动

注意启动命令是 `torchrun --nproc_per_node=8 -m verl.trainer.main_ppo`。

`torchrun` 是 PyTorch 自带的分布式启动工具，`--nproc_per_node=8` 表示每个节点起 8 个进程，对应 8 张 GPU。

`-m verl.trainer.main_ppo` 表示运行 `verl/trainer/main_ppo.py` 这个模块作为入口。

分布式训练的细节 veRL 已经帮你封装好了，不用自己写 DDP 初始化什么的。但知道这一点很重要——因为后面读代码的时候，你会发现有些变量是"每个进程一份"的，有些是"所有进程共享"的。

### 关键超参数总览

把常用的超参数列个表，方便后面调参的时候查：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `learning_rate` | 5e-6 | RL 阶段学习率，比 SFT 小很多 |
| `batch_size` | 64 | 每次迭代的查询数（任务数） |
| `samples_per_query` | 8 | 每个查询采样几条轨迹（GRPO 群体大小） |
| `clip_ratio_low` | 0.2 | 裁剪下限，ratio 最低到 0.8 |
| `clip_ratio_high` | 0.28 | 裁剪上限，ratio 最高到 1.28 |
| `temperature` | 1.6 | rollout 采样温度 |
| `max_new_tokens` | 2048 | 每条轨迹最多生成多少 token |
| `max_steps` | 100000 | 总训练步数 |
| `save_freq` | 5000 | 多少步存一次 checkpoint |
| `val_freq` | 1000 | 多少步验证一次 |
| `image_size` | 224 | 输入图像尺寸 |

几个值得注意的点：

- **学习率特别小**：5e-6，比 SFT 的 1e-4 小了 20 倍。因为 RL 阶段只是微调，不需要也不能用太大的学习率，不然策略容易崩。
- **batch_size 是查询数**：不是样本数。每个查询会生成 8 条轨迹，所以实际"样本数"是 64 × 8 = 512 条轨迹。
- **非对称裁剪**：clip_ratio_low 和 clip_ratio_high 不一样，对应上一节讲的非对称裁剪设计。

---

## 10.4.3.2 数据与任务构建

### rob_dataset.py 是干什么的

`verl/workers/rob_dataset.py` 这个文件负责数据加载和任务构建。简单说就是：你告诉它"我要跑 LIBERO 的 spatial 任务"，它就把对应的数据集准备好，包括任务列表、初始状态、演示数据这些。

### 数据集注册机制

代码里有一个 `DATASETS` 字典，大概长这样：

```python
DATASETS = {
    "libero_spatial": {
        "env_name": "libero",
        "task_suite": "libero_spatial",
        "image_size": 224,
        "camera_names": ["agentview_image"],
        "max_episode_length": 500,
        "action_dim": 7,
        "num_demos": 50,
    },
    "libero_object": {
        ...
    },
    "robotwin": {
        ...
    },
}
```

每个 benchmark 对应一个配置项，定义了环境名称、任务套件、图像尺寸、相机名称、最大回合长度、动作维度、演示数量这些信息。

你要加新任务的话，就在这个字典里加一项就行——这是 veRL 框架设计得比较方便的地方。

### 各基准的配置差异

几个常用 benchmark 的配置对比：

| 配置项 | LIBERO Spatial | LIBERO Object | RoboTwin |
|--------|---------------|--------------|----------|
| 动作维度 | 7 | 7 | 7 |
| 图像尺寸 | 224 | 224 | 256 |
| 相机数 | 1（agentview） | 1 | 1 |
| 最大回合长度 | 500 | 500 | 1000 |
| 任务数 | 10 | 10 | ？ |
| 演示数/任务 | 50 | 50 | ？ |

都是 7-DoF 的动作空间，单视角输入。区别主要在图像尺寸和回合长度——RoboTwin 的任务更复杂一些，所以回合更长。

### 数据格式

演示数据的格式跟 OpenVLA-OFT 是一致的，每个任务一个文件夹，里面放图像和轨迹文件：

```
task_name/
├── demo_0/
│   ├── agentview_image/
│   │   ├── 0000.png
│   │   ├── 0001.png
│   │   └── ...
│   └── trajectory.json
├── demo_1/
│   └── ...
└── ...
```

**trajectory.json** 里存的是每一步的动作和状态：

```json
{
  "actions": [[0.1, 0.2, -0.05, ...], ...],  # 每一步的 7-DoF 动作
  "states": [...],                            # 机器人状态（关节角度等）
  "language_instruction": "把杯子放到盘子里",  # 语言指令
  "success": true                              # 这条演示是否成功
}
```

**动作维度**：7 维，分别是：
- 3 维位置（x, y, z）
- 3 维姿态（通常是欧拉角或四元数转的轴角）
- 1 维夹爪（0 到 1 之间，0 是张开，1 是闭合）

**动作归一化**：训练前会把动作归一化到 [-1, 1] 之间，然后再离散化成 256 个 bin。推理的时候再反归一化回真实动作值。

### 语言指令

每个任务都有一条或多条语言指令。LIBERO 的指令比较自然语言化，比如"把红色的方块放到蓝色的碗里"。

模型输入的时候，语言指令会跟图像特征一起喂给 LLM。指令的 token 化用的是 LLaMA2 的 tokenizer。

### 数据加载流程

简单说一下数据是怎么加载的：

1. 启动时，根据 `--benchmark` 和 `--task_name` 找到对应的数据集配置
2. 遍历数据目录，加载所有演示的 trajectory.json
3. 图像不一次性全加载——用到的时候再读，省内存
4. 每个训练步，随机选一批任务，每个任务随机选一个初始状态
5. 初始状态 + 语言指令 = 一个"查询"，喂给 rollout 模块

第 5 步很重要——RL 训练不是直接用演示数据训练，而是用演示数据提供初始状态和任务指令，然后让模型自己去探索、自己去试。演示数据的作用是"告诉模型任务长什么样"，而不是"教模型每一步该怎么做"。

### 初始状态怎么选

每个任务有多个初始状态（来自不同的演示）。训练的时候随机选一个，这样模型不会只记住一种初始布局，泛化性更好。

初始状态包括：
- 物体的位置和姿态
- 机器人的初始关节角度
- 环境的其他变量（比如灯光、纹理这些，一般不变）

选好初始状态后，环境会重置到这个状态，然后模型从这里开始生成动作。

---

## 小结

配置和数据这一层，核心就是两个东西：

1. **配置系统**：align.json 打底，命令行参数覆盖，torchrun 分布式启动
2. **数据管线**：DATASETS 字典注册各 benchmark，trajectory.json 存动作和指令，图像按需加载

理解了这些，下一节读 rollout 的时候就知道——"查询"是哪来的、初始状态是怎么设的、语言指令从哪取的。

下一节看 `rob_rollout.py`，也就是模型怎么跟环境交互、怎么采样轨迹。
```

