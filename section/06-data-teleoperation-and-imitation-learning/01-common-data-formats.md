# 常用数据格式

目标：建立机器人数据格式的阅读框架，能从轨迹粒度、模态组织、metadata、审计与转换风险四个角度判断一种格式是否适合训练和复现。

> 先修：[07 数据类型和收集](README.md)
> 建议：先理解“机器人数据是什么”，再比较格式；不要一开始就背格式名。

在具身智能里，数据格式不是简单的文件后缀。它决定了你怎么保存一条轨迹、怎么检查视频和动作是否对齐、怎么切分训练集和验证集、怎么重算统计量，以及以后能不能把数据接到 LeRobot、RLDS、Open X 或其他训练栈里。

很多初学者第一次接触机器人数据，会把它想成“视频 + 标签”。这不够准确。机器人数据更像一段连续的实验记录：机器人在每个时刻看到了什么、自己处在什么状态、执行了什么动作、任务是否完成、这条轨迹属于哪个场景和任务。不同格式的差别，本质上就是这些信息被放在什么位置、以什么粒度组织、由谁来解释。

这一页先从一条普通的桌面抓取 episode 讲起，再比较 LeRobot、HDF5、robomimic、RLDS、Open X 风格数据，以及 Parquet / MP4 / Zarr 这类组件化存储方式。读的时候不必急着记格式细节，先抓住四件事：数据边界、字段语义、检查方法和后续转换风险。

## 阅读目标

读完这一页，可以用下面几个问题检查自己是否读懂：

1. 机器人数据为什么通常按 episode 和 frame 组织，而不是只按图片或视频组织。
2. LeRobot、HDF5、robomimic、RLDS 的结构差别是什么。
3. 为什么 Open X-Embodiment 更像“跨数据集统一工程”，而不是一种简单文件格式。
4. 为什么大规模数据常把低维状态存成 Parquet，把图像存成 MP4，把大数组存成 Zarr。
5. 面对一个新项目时，如何判断应该优先使用单文件 HDF5、LeRobot 风格目录，还是规划 RLDS 转换链。

## 先从一条机器人轨迹看起

假设我们用机械臂做一个简单任务：把桌上的红色方块放进盒子。一次完整尝试可以叫一条 episode。这个 episode 里面有很多 frame，每个 frame 对应一个时间步。

```text
episode_000001: "Pick up the red cube and place it into the box"

frame 0000
  observation:
    front_camera image
    wrist_camera image
    robot joint positions
    gripper state
  action:
    move end-effector slightly forward
    keep gripper open
  timestamp:
    0.000 s

frame 0001
  observation:
    front_camera image
    wrist_camera image
    robot joint positions
    gripper state
  action:
    move end-effector slightly downward
    keep gripper open
  timestamp:
    0.033 s

...

frame 0179
  observation:
    cube already inside the box
  action:
    stop or open gripper
  success:
    true
```

这说明机器人数据至少有三层结构：

```text
dataset
  └── episode
        └── frame / step
              ├── observation
              ├── action
              ├── timestamp
              └── metadata
```

如果只保存视频，就会丢掉动作和机器人状态；如果只保存状态和动作，就无法训练视觉策略；如果只保存动作，不保存 task 或 success，以后就很难知道这条轨迹到底在完成什么任务。因此，一个好的机器人数据格式，至少要回答四个问题：

| 问题 | 具体含义 |
|---|---|
| 轨迹边界在哪里 | 哪些 frame 属于同一条 episode，episode 从哪里开始、在哪里结束 |
| 每帧有什么 | 图像、状态、动作、时间戳、语言指令分别放在哪里 |
| 字段是什么意思 | action 的每一维是什么，单位是什么，是关节空间还是末端空间 |
| 数据能不能复现 | 版本、统计量、任务文本、切分规则和数据来源是否保存 |

后面所有格式的差别，都可以围绕这四个问题来理解：有的格式更强调训练读取效率，有的更强调单文件归档，有的更强调跨数据集统一接口。只要这四个问题没有回答清楚，格式名字再新也不能说明数据已经可用。

## 先看一张总表

下面这张表不负责评判“谁最好”，它的作用是先建立边界感。不同格式适合不同工作流。

| 格式 | 典型组织方式 | 最适合的场景 | 主要代价 |
|---|---|---|---|
| LeRobot v3 风格 | `meta/ + data/*.parquet + videos/*.mp4` | 采集、可视化、训练、共享、版本化都要兼顾 | 目录和 metadata 较多，初学时不如单文件直观 |
| HDF5 | 单个或少量 `.hdf5` 大文件 | 仿真 benchmark、快速归档、顺序读取轨迹 | 容易变成“黑盒大包”，字段语义常藏在代码里 |
| robomimic HDF5 | HDF5 + 规范 demo 层级 | robosuite / robomimic 生态下做算法对比 | 生态边界较强，跨框架常需要转换 |
| RLDS | `dataset -> episode -> step` 语义结构 | TFDS、Open X、Octo、OpenVLA 等训练栈 | 直接人工检查不如表格和视频目录直观 |
| Open X 风格 | 多数据集通过 RLDS 和统一变换接入 | 大规模跨机器人混合训练 | 本体差异、动作空间差异和来源差异处理很重 |
| Parquet / MP4 / Zarr 混合 | 不同模态用不同容器 | 自建数据湖、云端训练、流式读取 | 需要自己维护 schema、同步关系和数据卡 |

判断一个格式是否合适，不要只看它是否流行，而要看它是否适合你的数据规模、检查方式、训练栈和未来转换需求。

## 看格式时先问四个问题

在具体介绍每种格式前，先给一个通用读法。以后你拿到任何机器人数据集，都可以先问这四个问题。

### 第一，数据按什么粒度组织

常见粒度有三种：

```text
按 episode 分文件
  episode_000.parquet
  episode_001.parquet

按 chunk 分文件
  chunk-000/file-000.parquet
  chunk-000/file-001.parquet

按单个大文件归档
  dataset.hdf5
```

按 episode 分文件最直观，适合初学调试；按 chunk 分文件适合大规模训练；单个大文件适合快速归档和旧 benchmark，但后期治理压力会更大。

### 第二，图像和低维状态是否分开

机器人数据里有两类很不一样的信息：

| 类型 | 例子 | 常见存储 |
|---|---|---|
| 高维感知 | RGB 图像、深度图、视频帧 | MP4、图片序列、HDF5 数组、Zarr |
| 低维状态 | 关节角、夹爪状态、动作、时间戳 | Parquet、HDF5 dataset、Zarr array |

把所有东西塞在一起会很方便，但可视化、筛选和云端读取可能不舒服。把图像和状态分开会更工程化，但必须维护好时间同步关系。

### 第三，metadata 是否足够解释字段

一个 `action` 数组的 shape 是 `[7]`，并不等于你理解了它。你还要知道：

```text
action[0] 是 x 增量，还是 joint_1 目标角？
单位是米、弧度、毫米，还是归一化值？
夹爪 1 表示闭合，还是张开？
action 对应的是当前 observation，还是下一帧 observation？
```

如果这些信息只写在外部训练脚本里，而数据本身没有记录，数据迁移和复现就很危险。

### 第四，是否方便审计和转换

做项目时，数据很少停留在一个格式里。你可能先从 HDF5 下载 benchmark，再转成 LeRobot；也可能从 LeRobot 采集真机数据，再导出 RLDS 给 VLA 训练栈。因此，格式越封闭、metadata 越弱，后续转换风险越高。

## LeRobot：面向训练和数据治理的工程格式

LeRobot 风格在本课程中出现频率很高，因为它既适合初学者查看，又能支撑比较完整的数据工程流程。它通常把数据拆成三类：

```text
dataset_root/
  meta/
  data/
  videos/
```

可以粗略理解为：

| 目录 | 作用 |
|---|---|
| `meta/` | 保存数据集说明、feature schema、episode 信息、统计量、task 映射 |
| `data/` | 保存每帧的低维数据，例如 state、action、timestamp、episode index |
| `videos/` | 保存相机图像序列编码后的视频 |

这种组织方式的好处是分工清楚。训练脚本可以先读 `data/` 里的表格，知道每一帧属于哪条 episode，再按需要从 `videos/` 取图像。检查数据时，也可以先看 `meta/info.json` 确认字段含义，再用可视化工具查看视频和动作是否对齐。

一个简化后的 LeRobot 风格数据大概像这样：

```text
cube_pick_place/
  meta/
    info.json
    stats.json
    tasks.parquet
    episodes/
      chunk-000/file-000.parquet
  data/
    chunk-000/file-000.parquet
  videos/
    observation.images.front/
      chunk-000/file-000.mp4
    observation.images.wrist/
      chunk-000/file-000.mp4
```

这里先别急着背目录名，重点看它怎样把几个问题拆开：

```text
字段是什么意思       -> meta/info.json
数值怎么归一化       -> meta/stats.json
每帧低维数据是什么   -> data/*.parquet
图像在哪里           -> videos/*.mp4
episode 如何定位     -> meta/episodes/*
```

### LeRobot 适合什么

LeRobot 更适合中长期项目，而不是临时保存一次实验结果。典型场景包括：

- 真机遥操作采集数据；
- 需要反复可视化、回放、删除坏 episode；
- 需要把数据上传到 Hub 或共享给别人；
- 需要保留 task、stats、episode metadata；
- 未来可能要转成其他格式。

如果你准备做一个“桌面抓取 500 条 episode”的项目，并且希望后续能可视化、清洗、训练、复现，LeRobot 风格会比较合适。

### LeRobot 的代价

LeRobot 的代价是初学时目录看起来比较多。你不仅要理解视频，还要理解 Parquet、JSON、metadata、stats。对于只想跑一晚上小实验的人，裸 HDF5 或临时脚本可能更快。但只要项目进入持续维护阶段，LeRobot 的结构优势会更明显。

### 初学者看 LeRobot 数据时先看什么

拿到一个 LeRobot 数据集，不要先跑训练。建议按下面顺序看：

```text
1. 打开 meta/info.json
   看格式版本、fps、robot_type、features、dtype、shape、names

2. 打开 meta/stats.json
   看 action 和 state 的统计量是否存在，是否像当前数据计算出来的

3. 随机可视化几条 episode
   看视频、动作、状态、任务文本是否对齐

4. 检查 split
   看 train/val/test 是否按 episode 或场景切，而不是按 frame 随机切
```

这套检查习惯会在后续 LeRobot 专页和数据转换页面里反复出现。

## HDF5：一个大容器，方便归档，也容易藏问题

HDF5 是 Hierarchical Data Format 第 5 版对应的层次化二进制容器。它像一个文件里的小型文件系统，里面可以有 group、dataset、attribute。机器人学习里，很多旧数据集和仿真 benchmark 会用 HDF5 保存 demonstration。

一个常见结构如下：

```text
dataset.hdf5
  data/
    demo_0/
      obs/
        agentview_image
        robot0_eye_in_hand_image
        robot0_joint_pos
        robot0_gripper_qpos
      actions
      rewards
      dones
    demo_1/
      ...
  mask/
    train
    valid
  attrs:
    env_args
    total_samples
```

它的直观优势是：文件少，搬运方便，层次结构也很清楚。一条 demo 通常就是一个 group，`obs` 下面放观测，`actions` 放动作，`rewards` 和 `dones` 用于强化学习或任务结束判断。

### HDF5 为什么常见

HDF5 在机器人领域常见，主要有三个原因。

第一，它适合保存数组。图像、关节角、动作序列、奖励序列本质上都是数组，HDF5 能比较自然地组织它们。

第二，它适合仿真 benchmark。仿真数据通常由脚本批量生成，保存在一个大文件里非常方便。训练时按 demo 顺序读取，也比较直接。

第三，它方便归档。相比几十万个小图片文件，一个 `.hdf5` 文件更容易上传、复制和保存。

### HDF5 的核心风险

HDF5 当然能用，麻烦在于它太自由。不同项目可以随便定义 key：

```text
agentview_image
front_rgb
rgb_static
camera_0
robot0_joint_pos
proprio
state
```

这些名字是否等价，不能只靠猜。更麻烦的是，很多语义不一定写在 HDF5 文件里，而是写在训练代码或 README 里。例如：

```text
action 是末端位姿增量还是关节位置？
夹爪命令 1 表示张开还是闭合？
obs 是动作前观测，next_obs 是动作后观测吗？
图像是 RGB 还是 BGR？
任务成功标签是 dones、success，还是外部文件？
```

如果这些问题没弄清楚，HDF5 转 LeRobot 或 RLDS 时就很容易发生静默损坏。

### 接手 HDF5 数据的第一步

接手 HDF5 数据时，不建议直接训练。第一步应该打印 key 树、shape、dtype 和 attribute。

```text
先看结构：
  data/demo_0/obs/...
  data/demo_0/actions
  data/demo_0/dones

再看形状：
  image: [T, H, W, C]
  actions: [T, A]
  robot state: [T, S]

再查语义：
  每个 action 维度是什么
  每个 state 维度是什么
  每条 demo 是否有成功标签
```

HDF5 很适合作为源格式，但如果你要长期维护、共享和筛选数据，通常需要补充更明确的 schema 或转换成更工程化的目录结构。

## robomimic：HDF5 里的规范派

robomimic 本质上仍然是 HDF5，但它比许多随手写的 HDF5 更规范。它常用于 robosuite / robomimic 生态里的模仿学习和算法对比。

典型结构大致是：

```text
demo.hdf5
  data/
    demo_0/
      obs/
        agentview_image
        robot0_eye_in_hand_image
        robot0_eef_pos
        robot0_gripper_qpos
      next_obs/
        ...
      actions
      rewards
      dones
    demo_1/
      ...
  mask/
    train
    valid
```

和“自由组织的 HDF5 文件”相比，robomimic 的价值不在于 HDF5 本身多了新能力，而在于它对机器人模仿学习数据做了更明确的结构约定：

| 方面 | robomimic 中的约定 | 意义 |
|---|---|---|
| demo 层级 | 通常按 `data/demo_0/...`、`data/demo_1/...` 组织 | 每条 demonstration 是清晰的数据单元 |
| obs / next_obs | 明确区分动作前后的观测 | 便于行为克隆、离线强化学习和时序建模 |
| actions / rewards / dones | 使用固定字段保存动作、奖励和终止标记 | 训练脚本可以按统一接口读取 transition |
| env metadata | 记录环境名称、环境参数和仿真配置 | 有利于仿真环境重建、回放和复现 |
| mask | 用 `mask/train`、`mask/valid` 等记录切分 | 提醒 train / valid split 也是数据格式的一部分 |

它适合用来做 benchmark，因为许多训练脚本已经知道如何读取这种结构。

### 为什么仍然需要小心

robomimic 规范了很多结构，但它仍然不能替你解决所有语义问题。比如 action 是什么空间、图像来自哪个相机、任务定义是什么，仍然要结合数据集说明和环境配置理解。

另外，robomimic 强依赖自己的生态。如果你要接入 LeRobot、RLDS 或 VLA 训练栈，通常仍然要写转换层，把 demo、obs、action、split 和 metadata 重新映射到目标格式。

## RLDS：把 episode 和 step 放到数据结构最上层

RLDS 是 Reinforcement Learning Datasets 的缩写，常和 TensorFlow Datasets 一起使用。学习 RLDS 时，不要先盯着文件后缀，先看它怎样把 episode / step 语义放到数据结构里。

可以把 RLDS 理解成：

```text
dataset
  episode_000
    step_000
      observation
      action
      reward
      is_first = true
      is_last = false
      is_terminal = false
    step_001
      observation
      action
      reward
      is_first = false
      is_last = false
      is_terminal = false
    ...
    step_N
      observation
      reward
      is_first = false
      is_last = true
      is_terminal = true or false
```

RLDS 的重点是：每个 step 都知道自己在一条 episode 里的位置。`is_first` 表示 episode 开始，`is_last` 表示 episode 结束，`is_terminal` 表示环境是否真正终止。`is_last` 和 `is_terminal` 不能简单混用：前者说明这条记录到这里结束，后者才说明环境进入了真正终止状态；如果是 timeout 或人为截断，二者可能不同。

### 为什么这很重要

在大规模训练里，数据经常会被 shuffle、filter、batch、streaming。如果轨迹边界只靠外部文件名或隐式长度保存，一旦数据被切片或混合，就容易丢失边界信息。RLDS 把边界写进 step 级字段，训练管线就能稳定知道：

```text
哪些 step 是新 episode 的开始；
哪些 step 是 episode 的最后一步；
最后一步是否还能用于 action 监督；
episode 是自然终止，还是 timeout 截断。
```

这对强化学习、模仿学习、VLA 训练都很重要。特别是在模仿学习里，最后一个 step 有时只有终止观测，没有可监督的下一步 action；如果不区分这些标记，训练样本会被错误构造。

### RLDS 适合什么

RLDS 适合多任务、多数据源和大规模训练栈，尤其常见于 Open X-Embodiment、Octo、OpenVLA 等生态。它让不同数据源至少可以统一成：

```text
episode -> step -> observation/action/reward/flags
```

这样训练管线可以用一致的方式迭代数据。

### RLDS 不能解决什么

RLDS 统一的是数据结构，不是机器人语义。两个数据集都叫 `action`，并不代表可以直接混训：

```text
Robot A action:
  [x, y, z, roll, pitch, yaw, gripper]

Robot B action:
  [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6, joint_7]

Robot C action:
  [base_v, base_w, arm_delta, gripper]
```

它们都可以放进 RLDS，但动作空间完全不同。真正决定能否混训的，是你有没有明确记录 robot type、action convention、control frequency、gripper semantics，以及模型是否能处理这些差异。

## Open X 风格：跨数据集统一工程，而不是一个文件格式

Open X-Embodiment 经常和 RLDS 一起出现，但它本身不应该被理解成一个简单格式。更准确地说，它是一套把多个实验室、多个机器人、多个任务数据统一到可训练接口里的大规模混合工程。

可以这样理解：

```text
many labs
  └── many robots
        └── many local datasets
              └── converted to RLDS-style interface
                    └── used for large-scale policy / VLA training
```

它的价值在于规模和覆盖面。单个机器人数据集通常只能覆盖有限的任务、有限的场景和有限的本体；Open X 风格的数据则试图把多个来源放在一起，让模型从更大的真实机器人经验中学习。

### 这种统一为什么难

难点不在“把文件读出来”，而在“不同来源是否真的能放在一起训练”。

需要统一或至少显式记录的信息包括：

| 差异 | 例子 | 如果忽略会怎样 |
|---|---|---|
| 机器人本体 | 单臂、双臂、移动操作平台 | action 维度和控制含义不一致 |
| 相机布置 | 前视角、腕部相机、侧视角 | 同名 image 可能看到完全不同的内容 |
| 控制频率 | 5Hz、10Hz、20Hz、30Hz | 动作步长和时间尺度不同 |
| 任务文本 | 模板句、人工标注、短标签 | 语言条件语义不一致 |
| 成功定义 | 成功标签、终止标志、人工筛选 | 评估和过滤规则不一致 |
| 数据质量 | 远程操控、脚本生成、人工演示 | 轨迹风格和噪声不同 |

Open X 风格数据给我们的提醒是：不能把“数据越多越好”理解成简单拼接。真正要回答的是：

```text
多来源数据必须有来源字段；
不同本体不能默认 action 兼容；
统一训练接口之前，先做统一审计。
```

这也是后续介绍大规模真机数据集时会不断强调的主线。

## Parquet / MP4 / Zarr：组件化存储的工程思路

当数据规模变大后，很多项目会自然走向组件化存储：不同模态用不同容器，而不是所有东西塞进一个文件。

| 模态 | 常见容器 | 为什么这样存 |
|---|---|---|
| 状态、动作、索引、时间戳 | Parquet | 列式读取快，适合统计、过滤、按字段检查 |
| 连续 RGB 图像 | MP4 | 视频编码压缩率高，训练读取和远程存储更友好 |
| 点云、体素、大数组、长时序块 | Zarr | 分块读写灵活，适合大规模数组和随机 window |
| metadata | JSON、YAML、Parquet | 适合保存 schema、版本、task、episode 边界 |

这种方式比单文件 HDF5 复杂，但更接近大规模数据工程。比如 LeRobot v3 就是典型的组件化思路：低维数据用 Parquet，图像用 MP4，episode 定位和 schema 放在 metadata 里。

### 组件化存储的关键风险

组件化的风险是同步关系更复杂。你必须保证：

```text
data 第 100 行
  对应 videos/front 第 100 帧
  对应 videos/wrist 第 100 帧
  对应 timestamp 第 100 个时间戳
  对应 episode_id 和 frame_id
```

如果视频掉帧、重编码失败、时间戳漂移，训练脚本可能不会立刻报错，但 observation 和 action 已经错位。因此组件化存储一定要配合明确的 manifest、hash、episode metadata 和抽样可视化流程。

## 几种格式放在一起怎么理解

下面这张对照表可以作为本节的最终地图。

| 你关心的问题 | 更相关的格式或结构 | 解释 |
|---|---|---|
| 想快速保存一批仿真 rollout | HDF5 / robomimic HDF5 | 文件少，顺序读取方便 |
| 想做长期真机数据采集和清洗 | LeRobot | metadata、可视化、回放、编辑更完整 |
| 想接入 OpenVLA / Octo 等训练栈 | RLDS | episode/step 结构更适合 dataset pipeline |
| 想做跨机器人混合训练 | Open X 风格 | 需要显式处理本体和 action 差异 |
| 想自建大规模数据湖 | Parquet / MP4 / Zarr | 按模态拆分，适合云端和流式读取 |

也可以把它们看成不同层次：

```text
底层容器:
  HDF5, Parquet, MP4, Zarr

数据组织约定:
  LeRobot, robomimic HDF5, RLDS

跨数据集工程:
  Open X-Embodiment style mixture
```

这能避免一个常见误解：HDF5、Parquet、MP4 是存储容器；LeRobot 和 RLDS 是组织约定；Open X 更像数据汇聚和统一工程。它们不是同一层面的东西。

## 实际选型：不要问“哪个最好”

很多人会问：

```text
我的项目到底应该用 HDF5，还是 LeRobot，还是 RLDS？
```

这个问题不能脱离项目阶段回答。更合理的是看你的项目处在什么状态。

### 情况一：小规模仿真复现实验

如果你只是复现一个仿真 benchmark，数据量不大，训练脚本本来就读 HDF5，那么继续使用 HDF5 或 robomimic HDF5 很合理。此时最重要的是把 key、shape、env metadata 和 split 读清楚，而不是为了“格式新”强行转换。

```text
推荐：
  HDF5 / robomimic HDF5

重点检查：
  demo 数量、obs/action 对齐、env_args、train/valid mask
```

### 情况二：真机采集和长期维护

如果你要自己采集数据，并且之后要可视化、删除坏 episode、重算 stats、上传共享，LeRobot 风格更合适。

```text
推荐：
  LeRobot v3 风格

重点检查：
  meta/info.json、stats.json、videos 与 data 对齐、episode-level split
```

### 情况三：大规模跨数据集训练

如果你的目标是接入 Open X、Octo、OpenVLA 或其他 VLA 训练栈，那么要关注 RLDS 或能稳定转换到 RLDS 的格式。

```text
推荐：
  RLDS 或可稳定导出 RLDS 的中间格式

重点检查：
  is_first/is_last/is_terminal、action convention、robot type、数据来源字段
```

### 情况四：自建多模态数据湖

如果你要长期积累不同任务、不同机器人、不同传感器的数据，可能需要组件化存储：

```text
推荐：
  Parquet + MP4 + Zarr + manifest

重点检查：
  timestamp 对齐、schema 文档、版本管理、数据卡、hash
```

## 一个最小决策流程

下面这个流程可以作为初学项目的选型参考。

```text
你的数据只是小规模仿真 rollout 吗？
  ├─ 是：HDF5 / robomimic HDF5 通常足够
  └─ 否：继续

你需要长期维护、可视化、回放和清洗吗？
  ├─ 是：优先考虑 LeRobot 风格
  └─ 否：继续

你要接入 RLDS / Open X / VLA 训练栈吗？
  ├─ 是：规划 RLDS 转换链，必要时直接产出 RLDS
  └─ 否：继续

你是否有多模态、大规模、云端读取需求？
  ├─ 是：考虑 Parquet / MP4 / Zarr 组件化存储
  └─ 否：选择最容易审计、最贴合现有训练脚本的格式
```

这条流程不是绝对规则，但能避免一开始就陷入“社区现在流行什么格式”的讨论。

## 常见易错点

### 把格式名当成数据质量保证

数据是 LeRobot 或 RLDS，不代表它一定干净。格式只能提供组织方式，不能自动保证动作语义正确、视频没有掉帧、任务文本可靠、success 标签准确。

### 只看 action 的 shape

`shape = [7]` 没有太大信息量。它可能是 7 个关节角，也可能是末端位姿加夹爪，还可能是归一化后的动作。必须看 names、unit、control mode 和 robot type。

### 按 frame 随机切 train / val

机器人相邻帧高度相似。按 frame 切会让同一条 episode 的连续片段同时进入训练集和验证集，指标会虚高。更合理的切分单位是 episode、场景、物体、任务或操作者。

### 转换后不重算 stats

只要删除 episode、合并数据、改变 action/state 字段或修改 split，就应该重新计算统计量。旧 stats 和新数据不匹配时，模型训练可能不会报错，但动作尺度会悄悄出问题。

### 忽略视频编码带来的变化

MP4 会带来压缩、色彩空间转换、关键帧依赖和解码差异。视觉策略读到的是解码后的图像，不是原始相机帧。对小物体、透明物体、接触边缘敏感的任务，要特别注意视频质量。

## 后续页面怎么读

本节只是选型地图，后面几页会把重点格式拆开讲：

- [LeRobot 数据格式](01-common-data-formats/01-lerobot-data-format.md)：详细看 LeRobot v2/v3 的目录、metadata 和迁移风险。
- [HDF5](01-common-data-formats/02-hdf5.md)：详细看层次化容器、chunk/压缩设置、HDF5 转 LeRobot 时的检查项。
- [RLDS](01-common-data-formats/03-rlds.md)：详细看 episode/step 语义、`is_first`、`is_last`、`is_terminal` 和跨训练栈转换。
- [数据转换](02-data-conversion.md)：把前面的格式放到转换场景里，学习字段、语义、时间和治理四个层次。

读的时候建议带着一个具体问题：如果给你一批新数据，你能不能说清楚它的 episode 边界、action 语义、图像存储、metadata 和转换风险。

## 练习

### 练习 1：给三种格式写工作流画像

分别为 LeRobot、HDF5、RLDS 写一句话：

```text
它最适合什么？
它最怕什么误用？
转换时最容易丢什么信息？
```

示例：

```text
LeRobot:
  最适合长期维护、可视化和训练一体化的数据集。
  最怕 metadata、stats 和 videos/data 不同步。
  转换时最容易丢 episode offset、feature names 和统计量依据。
```

### 练习 2：为 500 条桌面抓取数据做格式选型

假设你要采集 500 条桌面抓取 episode，请写出：

1. 主格式选择。
2. 为什么适合采集、可视化和训练。
3. 未来可能转换到什么格式。
4. 必须保留哪些 metadata。
5. train / val / test 准备按什么粒度切。

一个合格答案应该明确写出：

```text
主格式 + 备用转换目标 + action 语义 + metadata + split 规则
```

而不是只写一个文件扩展名。

## 自查问题

1. 为什么说机器人数据不是简单的“视频 + 标签”？
2. HDF5 为什么适合快速归档，但容易变成黑盒？
3. LeRobot 为什么更适合长期维护和数据治理？
4. RLDS 为什么要把 `is_first`、`is_last` 放在 step 级？
5. Open X-Embodiment 为什么更像跨数据集统一工程，而不是一种文件格式？
6. Parquet / MP4 / Zarr 组件化存储的最大风险是什么？
7. 为什么同样是 7 维 action，也不能直接认为两个数据集可以混训？
