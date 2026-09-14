# 9.1.4.3 Benchmark 的数据与任务机制

本节介绍 CALVIN 的数据格式、观测空间、动作空间、语言标注和评估机制。

## 数据规模与目录结构

CALVIN 总数据量约 1.3 TB，包含约 240 万帧 `.npz` 数据。论文中的采集口径是四个环境总计约 24 小时 play data，每个环境约 6 小时，对应约 240 万个交互 step，并可构造约 4000 万个 1-2 秒的 short-horizon windows。每一帧对应一个机器人交互 timestep，包含相机观测、动作、机器人状态、场景状态等信息。

典型数据目录结构如下：

```text
calvin_debug_dataset/
├── training/
│   ├── episode_XXXXXXX.npz
│   ├── ep_start_end_ids.npy
│   ├── scene_info.npy
│   ├── statistics.yaml
│   └── lang_annotations/
└── validation/
    ├── episode_XXXXXXX.npz
    ├── ep_start_end_ids.npy
    ├── scene_info.npy
    ├── statistics.yaml
    └── lang_annotations/
```

训练代码会从 `training/` 和 `validation/` 中读取 episode 文件，并根据语言标注构造训练样本。

## 观测空间

每一帧中常见的观测 key 包括：

| Key | 含义 | 形状 |
|---|---|---|
| `rgb_static` | 静态相机 RGB | `200 x 200 x 3` |
| `rgb_gripper` | 腕部/夹爪相机 RGB | `84 x 84 x 3` |
| `rgb_tactile` | 触觉 RGB 图像，当前数据 README 中列出 | `160 x 120 x 6` |
| `depth_static` | 静态相机深度图 | `200 x 200` |
| `depth_gripper` | 腕部/夹爪相机深度图 | `84 x 84` |
| `depth_tactile` | 触觉深度图 | `160 x 120 x 2` |
| `robot_obs` | 机器人本体状态 | `15` 维 |
| `scene_obs` | 场景状态 | `24` 维 |




## 状态信息

`scene_obs` 包含场景中对象的位置、方向和关节状态，例如：

- 滑动门状态；
- 抽屉状态；
- 按钮状态；
- 开关状态；
- 灯泡、LED 状态；
- 红、蓝、粉色方块的位置和欧拉角。

`robot_obs` 包含机器人本体感觉信息，例如：

- 末端位置；
- 末端欧拉角；
- 夹爪开合宽度；
- 机械臂关节角；
- 夹爪动作。

## 语言标注与 language embeddings

每个数据 split 中都有语言标注文件，通常位于：

```text
training/lang_annotations/auto_lang_ann.npy
validation/lang_annotations/auto_lang_ann.npy
```

其中包含：

| 字段 | 含义 |
|---|---|
| `language/ann` | 原始自然语言指令列表 |
| `language/task` | 每条语言对应的 task id |
| `language/emb` | 预先计算好的 MiniLM 语言 embedding |
| `info/indx` | 每条语言对应任务的起止帧索引 |

论文中，作者收集了 400 多条 crowd-sourced natural language instructions，覆盖 34 个任务，并利用环境状态对数据中的有意义片段进行程序化标注。baseline 默认读取预计算的 MiniLM embedding，向量维度为 384，因此复现时不需要先训练语言模型。如果要替换语言模型，可以使用项目中的 relabel 脚本重新生成 embedding。

## 任务机制

CALVIN 的任务是语言条件桌面操作。论文定义了 34 个具体任务，环境可以根据初始状态和最终状态自动判断任务是否完成。常见任务包括：

| 任务类型 | 示例 |
|---|---|
| 抽屉/滑门 | 打开抽屉、关闭抽屉、移动滑动门 |
| 灯光/按钮 | 打开灯泡、关闭灯泡、打开 LED |
| 方块操作 | 拿起红色方块、推动蓝色方块、旋转粉色方块 |
| 组合操作 | 把方块放进抽屉、堆叠方块、移除堆叠方块 |

评估时，机器人会从初始状态开始，按顺序接收多个自然语言子任务。策略需要在每个子任务内持续输出动作，直到任务判定器认为当前任务完成，或者达到最大步数仍未完成。

## 评估协议与指标

CALVIN 论文中包含两类主要评估。

第一类是 Multi-Task Language Control，简称 MTLC。它评估策略对 34 个 manipulation task 的单任务泛化能力。每个任务执行 10 次 rollout，测试语言指令不出现在训练集中。

第二类是 Long-Horizon MTLC，简称 LH-MTLC。它评估策略能否连续完成多个语言指令。标准长时序评估中，每次 rollout 包含 5 个连续子任务，过滤不可行、循环或过于相似的序列后得到 1000 条 unique instruction chains。每条长序列结束后，机器人会重置到 neutral position，以避免初始机械臂姿态给策略带来偏置。

CALVIN 常用指标是连续任务成功率和平均完成长度：

| 指标 | 含义 |
|---|---|
| 1/5 success | 至少连续完成第 1 个子任务的比例 |
| 2/5 success | 连续完成前 2 个子任务的比例 |
| 3/5 success | 连续完成前 3 个子任务的比例 |
| 4/5 success | 连续完成前 4 个子任务的比例 |
| 5/5 success | 连续完成全部 5 个子任务的比例 |
| Avg. Len. | 正确轨迹的平均完成任务长度 |

CALVIN 不只是看单任务成功率，也关注策略在长任务链中能持续完成多远。

