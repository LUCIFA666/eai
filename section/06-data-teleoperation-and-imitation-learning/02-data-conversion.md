# 数据转换

目标：把数据转换看成语义迁移和工程审计，而不只是文件重排，能设计字段映射、时间对齐、质量检查和转换报告。

> 先修：[常用数据格式](01-common-data-formats.md) → [LeRobot 数据格式](01-common-data-formats/01-lerobot-data-format.md)
> 建议：把“转换”理解成数据工程，不是字段改名脚本

在具身智能项目里，数据很少从头到尾只待在一种格式里。你可能拿到的是 HDF5 仿真数据，但训练工具更适合读 LeRobot；也可能拿到 RLDS / Open X 风格数据，但想先转成更容易检查的 Parquet、MP4 和 metadata；还可能只是把旧版 LeRobot v2.1 升级到 v3.0。

表面上看，这些工作都叫“格式转换”，但真正要完成的远不只是把文件从一个目录搬到另一个目录。

机器人数据是一段“观测—动作—结果”的时间序列。一次转换如果只保证文件能打开，却没有保证动作语义、时间对齐、episode 边界、视频帧数、任务文本、成功标签和统计量都正确，那么这个新数据集就不应该直接进入训练。

这里先把判断标准说清楚：**转换完成不等于脚本运行成功，而是新数据集可以被读取、回放、审计、复现，并且别人能知道它是怎么来的。**

后面会用 HDF5、RLDS 和 LeRobot 作为主要例子，说明一次可靠的数据转换应该怎么做、容易坏在哪里，以及如何留下最小但有用的转换记录。

## 阅读目标

这一页先围绕几个实际问题展开：

1. 为什么机器人数据转换不能只看字段名，还要检查语义、时间和统计量。
2. 一条完整的转换流水线应该包含哪些阶段。
3. 从 HDF5、RLDS、LeRobot v2 转到 LeRobot v3 时，分别最容易出什么错。
4. 如何设计字段映射表、过滤规则、视频编码配置和质量检查。
5. 为什么转换后要重新计算 `stats`，并留下 conversion report。
6. 如何判断一批转换后的数据能不能安全交给训练脚本。

## 阅读路线

阅读时可以按三步走：先看转换风险，再看流程设计，最后看几条常见转换路径。

```text
为什么转换不是字段改名
转换前先读懂源数据
定义目标 schema，而不是边转边猜
处理字段、语义、时间和治理四层问题
三类常见转换路径
转换后的验证、抽样和封口
```

建议第一次读时按顺序看。之后做项目时，可以把“转换清单”“静默损坏”和“conversion report 模板”当成检查表使用。

## 为什么转换不是字段改名

最容易犯的错误，是把数据转换理解成下面这种表面工作：

```text
agentview_image -> observation.images.front
robot0_joint_pos -> observation.state
actions -> action
```

这一步当然需要做，但它只是转换里最显眼的一层。真正困难的是：源字段和目标字段的名字对上以后，它们背后的含义是否也对上。

举一个最常见的例子。源数据里有一个字段叫 `actions`，shape 是 `[T, 7]`。目标 LeRobot 数据集也有一个字段叫 `action`，shape 也是 `[T, 7]`。这看起来很顺利，但这 7 维可能有完全不同的语义：

```text
情况 A：action = [x, y, z, roll, pitch, yaw, gripper]
情况 B：action = [joint1, joint2, joint3, joint4, joint5, joint6, joint7]
情况 C：action = 归一化后的控制命令，范围约为 [-1, 1]
情况 D：action = 末端目标位姿，不是增量，而是绝对位置
```

如果你只因为 shape 一样就直接转换，训练脚本一般不会报错，但模型学到的动作空间会是错的。更危险的是，这类错误通常不会在第一轮训练日志里暴露，只有到回放、仿真评测或真机部署时才会发现策略动作尺度不对、夹爪方向反了、机械臂轨迹漂移，或者模型根本学不会。

所以，转换真正要完成的是下面这件事：

```text
源数据中的每个关键信息
  -> 在目标数据集中有明确位置
  -> 语义没有被误解
  -> 时间关系没有被打乱
  -> 质量变化有记录
  -> 后续训练者能复现这次转换
```

## 转换前先读懂源数据

开始写转换脚本前，先不要急着处理文件。第一步应该是做 source inspection，也就是把源数据的结构、字段、shape、单位和时间关系读清楚。

以一个常见 HDF5 文件为例，它可能长这样：

```text
dataset.hdf5
  data/
    demo_0/
      obs/
        agentview_image        shape = [T, H, W, 3]
        robot0_joint_pos       shape = [T, 7]
        robot0_gripper_qpos    shape = [T, 2]
      next_obs/
        agentview_image        shape = [T, H, W, 3]
      actions                  shape = [T, 7]
      rewards                  shape = [T]
      dones                    shape = [T]
    demo_1/
      ...
  mask/
    train
    valid
  attrs:
    env_args
```

看见这个结构后，至少要问几个问题：

- `obs` 是动作执行前的观测，还是已经对齐到动作后的观测？
- `next_obs` 是否存在？如果存在，BC 训练应该用 `obs` 还是 `next_obs`？
- `actions` 是关节空间、末端空间，还是已经归一化后的命令？
- `robot0_gripper_qpos` 的两维分别代表左右手指位置，还是夹爪宽度和状态？
- `dones` 只是 episode 结束标记，还是表示任务成功？
- `mask/train` 和 `mask/valid` 是按 episode 切的，还是按 frame 切的？
- `env_args` 里是否包含任务、机器人、相机、资产版本等复现信息？

这一步可以先做成一份源 schema 说明，而不是直接写最终转换代码。例如：

```yaml
source_schema:
  format: hdf5
  episode_unit: data/demo_i
  image:
    key: obs/agentview_image
    dtype: uint8
    layout: T,H,W,C
    color: RGB
  state:
    key: obs/robot0_joint_pos
    shape: [T, 7]
    semantic: joint positions
  action:
    key: actions
    shape: [T, 7]
    semantic: end-effector delta pose + gripper
  termination:
    key: dones
    semantic: episode boundary, not necessarily success
```

这个文件看起来简单，但它能避免后续大量误解。尤其是在多人协作或复现实验中，后来者需要先知道源数据里每一列到底是什么意思。

## 目标 schema 要先定义好

源数据读清楚之后，第二步是定义目标 schema。目标 schema 不是文件夹长什么样，而是目标数据集希望别人如何理解每个 feature。

如果目标是 LeRobot v3，最少需要提前定义：

```text
observation.images.front
observation.state
action
task
timestamp
episode_index
frame_index
```

还要明确：

- `observation.state` 包含哪些维度，顺序是什么。
- `action` 是什么动作空间，单位是什么。
- 图像 feature 是视频还是图片，分辨率是多少。
- 数据集统一 FPS 是多少。
- `task` 是 episode 级还是 frame 级。
- `success`、`is_last`、`done` 之间如何映射。
- 哪些字段进入训练，哪些只进入 metadata。
- 清洗后是否重新计算 `stats`。

一个目标 schema 草图可以写成：

```yaml
target_schema:
  format: lerobot_v3
  fps: 20
  robot_type: franka
  features:
    observation.images.front:
      dtype: video
      shape: [256, 256, 3]
      names: [height, width, rgb]
    observation.state:
      dtype: float32
      shape: [8]
      names:
        - joint1
        - joint2
        - joint3
        - joint4
        - joint5
        - joint6
        - joint7
        - gripper_width
    action:
      dtype: float32
      shape: [7]
      semantic: end_effector_delta_pose + gripper_command
      unit: meter/radian/normalized_gripper
  metadata:
    keep:
      - source_dataset
      - source_episode_id
      - task_name
      - success
      - conversion_version
```

这样做有一个好处：转换脚本不是在“猜目标格式”，而是在执行一个已经写清楚的契约。

## 转换的四层问题

一次机器人数据转换至少要同时处理四层问题：字段层、语义层、时间层和治理层。少了任何一层，都可能生成一个表面正常、实际不可用的数据集。

### 字段层：key 怎么对过去

字段层是最表面的映射。比如：

| 源字段 | 目标字段 | 额外检查 |
|---|---|---|
| `obs/agentview_image` | `observation.images.front` | 确认视角、分辨率、RGB/BGR |
| `obs/robot0_joint_pos` | `observation.state` 的一部分 | 写清关节顺序 |
| `obs/robot0_gripper_qpos` | `observation.state` 的一部分 | 写清夹爪单位 |
| `actions` | `action` | 确认动作空间和单位 |
| `dones` | `is_last` 或 episode boundary | 不要默认等于 success |
| `language_instruction` | `task` | 确认是 episode 级还是 step 级 |

字段层解决的是“数据放到哪里”，但它还没有回答“数据是什么意思”。

### 语义层：shape 一样不代表含义一样

语义层是转换里最容易漏掉的一层。两个字段都叫 `action`，甚至 shape 都一样，也可能不能直接合并。

例如：

```text
Dataset A:
  action[0:3] = 末端 xyz 增量，单位 meter
  action[3:6] = 末端姿态增量，单位 radian
  action[6]   = 夹爪开合命令

Dataset B:
  action[0:7] = 七个关节目标位置，单位 radian

Dataset C:
  action[0:7] = 已归一化动作，无物理单位
```

如果目标模型只接受一种 action space，那么这三类数据不能简单拼在一起。你可以选择只取其中一类，也可以在 metadata 中标明 `action_space`，或者设计模型显式区分不同机器人本体。但无论哪种做法，都不能把它们伪装成同一个 `action`。

夹爪语义也要特别小心。有些数据里：

```text
0 = open, 1 = close
```

有些数据里刚好相反：

```text
0 = close, 1 = open
```

还有些数据记录的是夹爪宽度，例如单位为米。只要夹爪语义弄反，整个抓取数据就会变得很难学。

### 时间层：图像、状态、动作不一定同频

机器人数据的时间问题比普通视频复杂。源数据可能是：

```text
camera      @ 30 Hz
joint state @ 125 Hz
action      @ 20 Hz
audio       @ 16 kHz
tactile     @ 100 Hz
```

如果目标数据集统一成 30 FPS，你必须决定：

- 相机帧是否逐帧保留。
- 高频关节状态是取最近值、插值，还是降采样。
- 低频 action 是保持上一帧、插值，还是只在控制时刻记录。
- 不同模态是否保存原始 timestamp。
- 如果有延迟，是否需要校正。

一个常见错误是把动作和图像错位一帧。对行为克隆来说，我们通常希望学习：

```text
当前 observation -> 当前应执行的 action
```

如果错用 `next_obs`，就会变成：

```text
动作执行后的 observation -> 刚刚已经执行过的 action
```

这在数学上看只是错了一帧，但在学习上会把因果关系反过来。

### 治理层：转换后要能解释数据怎么变过

治理层关注的是转换历史和数据质量。转换以后，要能回答：

- 转换前有多少条 episode？
- 转换后剩多少条？
- 哪些 episode 被跳过？
- 跳过原因是什么？
- 是否过滤失败轨迹？
- 是否删除 no-op 片段？
- 是否重编码视频？
- 是否修改任务文本？
- 是否重新计算 `stats`？
- 是否生成新的 dataset card 或 manifest？

治理层不是额外的管理文档，它本来就是数据可复现的一部分。没有这些记录，后来训练失败时就很难判断是模型问题、数据问题，还是转换过程造成的偏差。

## 一条完整转换流水线

把上面的内容串起来，一次可靠转换可以按下面这条流水线执行：

```text
source dataset
  -> inspect source schema
  -> define target schema
  -> map fields and units
  -> convert frames / episodes / videos
  -> validate counts and boundaries
  -> sample replay / visualization
  -> recompute stats
  -> write conversion report
  -> archive or publish
```

这条流水线里，每一步都有自己的产物：

| 阶段 | 要做什么 | 产物 |
|---|---|---|
| 源检查 | 列出 key、shape、dtype、单位、fps | source schema |
| 目标定义 | 定义目标 feature、action space、metadata | target schema |
| 字段映射 | 写清每个源字段如何进入目标 | mapping table |
| 过滤规则 | 定义坏 episode、失败样本、no-op 的处理 | filter log |
| 编码处理 | 决定图片是否转视频、codec 和 fps | encoding config |
| 计数验证 | 检查 episode、frame、video frame 数 | validation log |
| 抽样检查 | 看图像、动作、任务、时间是否对齐 | sampled evidence |
| 统计封口 | 重算 stats，写 dataset card | stats + report |

你可以把转换理解成一次小型数据发布流程，而不是一次脚本运行。

## 三类常见转换路径

### 路径 A：HDF5 -> LeRobot

这是最常见的路径之一，尤其是把仿真 benchmark、robomimic、LIBERO、RoboCasa 等旧生态数据接入 LeRobot 工作流时。

一个简化流程是：

```text
HDF5 groups
  -> read demo_i
  -> extract obs / action / task / done / success
  -> align per episode
  -> write low-dimensional rows to Parquet
  -> encode image arrays to MP4
  -> write meta/info.json
  -> write meta/tasks
  -> write meta/episodes
  -> recompute meta/stats.json
```

这条路径最容易出错的地方有几个。

第一，`obs` 和 `next_obs` 不要错用。BC 训练通常使用 `obs[t] -> action[t]`。`next_obs[t]` 是动作执行后的状态，不能随便当成当前输入。

第二，`done` 不等于成功。很多 HDF5 数据里的 `dones` 只表示 episode 结束。任务失败也可以结束，超时也可以结束。如果目标数据集需要 `success` 字段，必须从源数据的成功标签或任务逻辑里确认，不能直接把 `done` 当成功。

第三，多相机 key 要仔细映射。比如：

```text
agentview_image -> observation.images.front
robot0_eye_in_hand_image -> observation.images.wrist
```

这个映射看起来简单，但要实际看图确认。否则 front / wrist 一旦互换，模型输入就会变错，但训练不会报错。

第四，图像通道要检查。某些项目用 OpenCV 读写图像，可能是 BGR；目标数据集如果默认 RGB，颜色通道错了会影响视觉策略。

第五，仿真 metadata 要保留。环境名称、资产版本、任务配置、随机种子、初始状态等信息不一定进入模型训练，但应该进入 metadata 或 dataset card，否则后续难以复现。

### 路径 B：RLDS -> LeRobot

RLDS 常见于 Open X-Embodiment、Octo、OpenVLA 等生态。它最重要的结构是：

```text
dataset
  -> episode
       -> step
            observation
            action
            reward
            discount
            is_first
            is_last
            is_terminal
```

从 RLDS 转 LeRobot 时，重点不是“能不能读出数据”，而是 episode / step 语义是否完整保留下来。

需要特别检查：

- 每条 episode 是否只有第一步 `is_first = true`。
- 每条 episode 是否只有最后一步 `is_last = true`。
- `is_terminal` 是否与 timeout、失败、成功区分。
- 最后一帧是否还有有效 action。
- 语言任务是 episode 级还是 step 级。
- reward / discount 是否进入训练，还是只保留到 metadata。
- 多相机字段是否稳定映射到 LeRobot feature 名。

最后一帧尤其容易出错。RLDS 官方语义里，`is_last` 为真的 step 通常表示 episode 的结束状态，后续动作、reward、discount 等字段可能不再是有效监督信号。转成 LeRobot 时，如果把最后一帧也当成普通 `observation -> action` 样本，就可能给模型喂入无效动作。

一个更稳妥的处理是：

```text
if step.is_last and action_invalid:
    keep observation as terminal metadata
    do not use it as BC supervision
else:
    write observation/action as normal frame
```

实际项目中，是否丢掉最后一帧，要看源数据集的定义。但必须显式判断，不能默认全部有效。

### 路径 C：LeRobot v2.x -> v3.x

LeRobot v2 到 v3 看起来只是同生态内部升级，但也不能掉以轻心。v2 常见组织方式是：

```text
data/episode_000000.parquet
videos/observation.images.front/episode_000000.mp4
```

v3 则更倾向于：

```text
data/chunk-000/file-000.parquet
videos/observation.images.front/chunk-000/file-000.mp4
meta/episodes/chunk-000/file-000.parquet
```

也就是说，v3 里一条 episode 不一定对应一个独立文件，而是通过 `meta/episodes/` 记录它在共享文件中的位置。升级时要确认：

- episode 数是否一致。
- 每条 episode 的 frame 数是否一致。
- 每条 episode 的 task 是否一致。
- 视频帧数是否和 frame 数对应。
- `episode_index`、`frame_index` 是否连续且正确。
- `meta/info.json` 的 feature schema 是否和旧版一致。
- `meta/stats.json` 是否重算或确认仍然有效。
- 抽样可视化同一条 episode，确认图像、状态、动作、任务对齐。

版本升级不是简单改目录结构，而是把数据重新封装成新的读取契约。

## 转换后的验证

转换完成后，至少要做三类验证：程序验证、人工抽样和统计封口。

### 程序验证：先证明结构没坏

程序检查可以覆盖一些确定性错误：

```python
def audit_episode(obs_len, action_len, timestamps, *, fps):
    errors = []

    if obs_len != action_len:
        errors.append("obs/action length mismatch")

    if len(timestamps) != obs_len:
        errors.append("timestamp length mismatch")

    if any(t2 <= t1 for t1, t2 in zip(timestamps, timestamps[1:])):
        errors.append("timestamps are not strictly increasing")

    expected_dt = 1.0 / fps
    jitter = [
        abs((t2 - t1) - expected_dt)
        for t1, t2 in zip(timestamps, timestamps[1:])
    ]

    if jitter and max(jitter) > expected_dt:
        errors.append("large timestamp jitter")

    return errors
```

真实项目里还要继续检查：

- NaN / Inf。
- action 范围是否超出预期。
- state 维度是否稳定。
- 图像是否能正常解码。
- video frame 数是否和数据行数一致。
- task 文本是否为空。
- episode index 是否重复。
- split 是否按 episode 切分。

### 人工抽样：看脚本看不到的问题

有些错误程序很难自动发现。例如：

- front camera 和 wrist camera 互换。
- RGB / BGR 通道反了。
- 视频能解码但花屏。
- action 和图像错位一两帧。
- success 标签和画面不一致。
- 失败样本被误删或误保留。
- 语言指令和实际任务不匹配。

所以转换后必须抽样看。抽样不需要看完整数据集，但至少覆盖：

```text
最短 episode
最长 episode
一个成功样本
一个失败样本
一个边界条件样本
每个相机至少一个样本
每个任务类别至少一个样本
```

如果是 HDF5 转 LeRobot，可以用 LeRobot 的可视化工具看转后的数据；如果是 RLDS 转 LeRobot，可以抽样比对原始 step 顺序和转换后的 frame 顺序。

### 统计封口：重新计算 stats

只要发生了下面任意一种情况，就应该重新计算 `stats`：

- 删除了一批 episode。
- 合并了多个数据源。
- 修改了 action 字段。
- 修改了 state 字段。
- 改变了图像分辨率。
- 修改了 train / val / test split。
- 过滤了失败轨迹或 no-op 片段。

原因很直接：训练归一化使用的是转换后的数据分布，而不是源数据分布。旧统计量如果继续沿用，模型可能能训练，但尺度会偏。

例如，源数据里 action 单位是毫米，转换后改成米。如果 `stats` 没重算，模型看到的归一化尺度就完全错了。

## conversion report 怎么写

任何一次正式转换，都应该留下 conversion report。它不需要很长，但要回答“这批数据从哪里来、怎么变成现在这样”。

一个最小模板如下：

```yaml
source:
  name: libero_pick_place
  format: hdf5
  episodes_before: 1200
  fps: 20
  source_version: "original_release"

target:
  format: lerobot_v3
  robot_type: franka
  action_space: end_effector_delta_pose_7d
  image_keys:
    - observation.images.front
    - observation.images.wrist
  fps: 20

conversion:
  tool: custom_converter
  tool_version: "commit-2ef2370"
  date: 2026-05-22
  skipped_episodes: 17
  skip_reasons:
    corrupted_video: 3
    empty_actions: 9
    invalid_length: 5
  image_encoding:
    codec: h264
    resolution: 256x256
  action_transform:
    source: normalized_delta_pose
    target: metric_delta_pose

validation:
  episode_count_checked: true
  frame_count_checked: true
  sampled_episodes: [0, 25, 200]
  visualization_checked: true
  replay_checked: false
  stats_recomputed: true

notes:
  - "done is mapped to is_last, not success"
  - "success label is inherited from source task metadata"
```

这份报告的意义是：以后换一个人接手，也能知道这批数据不是天然生成的，而是从某个源数据、经过某个工具版本、按某些过滤规则转换来的。

## 最容易出现的静默损坏

下面这些问题最危险，因为训练脚本通常不会直接报错。

### 1. episode 数没变，但每条少了一帧

转换前后都显示 500 条 episode，看起来没问题。但如果每条 episode 的最后一帧都丢了，任务完成状态、终止标志和最后动作都会受影响。

### 2. 图像 key 对了，但相机内容互换

字段叫 `observation.images.front`，但里面实际是 wrist camera。模型能正常训练，却学不到预期的视觉关系。

### 3. action shape 对了，但单位错了

`action.shape = [7]` 没问题，但单位从毫米变成米，或者从绝对位置变成增量。模型输出尺度会彻底错。

### 4. `success` 被默认填成同一个值

如果源数据没有 success 字段，转换脚本可能默认全部 `true` 或全部 `false`。后续按成功样本过滤时会出现严重偏差。

### 5. `done` 被误当成任务成功

`done` 只说明 episode 结束，不说明任务成功。超时、失败、人工中断都可能产生 `done`。

### 6. train / val 按 frame 切

同一条 episode 的相邻帧高度相似。如果随机按 frame 切，验证集会泄漏训练集信息，指标会虚高。

### 7. dataset card 还写着旧 schema

数据已经改成末端增量 action，但文档还写关节位置。后来者按文档训练，结果会完全错位。

## 一个实际转换计划示例

假设你要把一个 HDF5 抓取数据集转成 LeRobot v3，可以先写这样的计划：

```text
源数据：
  format: HDF5
  episode: data/demo_i
  image: obs/agentview_image
  state: obs/robot0_joint_pos + obs/robot0_gripper_qpos
  action: actions
  terminal: dones

目标数据：
  format: LeRobot v3
  image: observation.images.front
  state: observation.state
  action: action
  task: "pick up the cube"
  fps: 20

转换规则：
  1. 使用 obs，不使用 next_obs 作为 BC 输入。
  2. agentview_image 转为 MP4，保持 RGB。
  3. robot0_joint_pos 和 gripper_qpos 拼成 observation.state。
  4. actions 写为 action，并在 info.json 里写清每一维含义。
  5. dones 只映射为 episode boundary，不映射为 success。
  6. 删除空 action、长度不一致、视频无法解码的 episode。
  7. 转换后按 episode 切 train/val。
  8. 重新计算 stats。
  9. 抽样最短、最长、成功、失败 episode 做可视化。
```

这比直接写“运行 converter.py”更可靠，因为它把转换假设都显式化了。

## 后续页面怎么读

- [Any4LeRobot](02-data-conversion/01-any4lerobot.md)：看跨生态转换工具如何把不同来源数据接入 LeRobot。
- [LeRobot 数据工作流](02-data-conversion/02-lerobot-data-workflow.md)：看转换后如何检查、可视化、编辑、切分和重算 stats。

如果你在做自己的转换脚本，也可以先写一个类似 `inspect_lerobot_dataset.py` 的检查脚本。它不一定负责转换，只负责确认目标数据集能不能被读取、feature 是否齐全、episode 数和 frame 数是否合理。

## 小结

- 机器人数据转换不是字段改名，而是把源数据重新组织成一个可训练、可回放、可审计、可复现的新数据集。
- 一次可靠转换至少要处理字段、语义、时间和治理四层问题。
- HDF5 -> LeRobot 要特别注意 `obs` / `next_obs`、多相机、`done` / `success` 和仿真 metadata。
- RLDS -> LeRobot 要特别注意 `is_first`、`is_last`、`is_terminal` 和最后一帧 action 是否有效。
- LeRobot v2 -> v3 虽然是同生态升级，也必须检查 episode 长度、视频、task、state、action 和 stats。
- 删除、合并、改字段、改 split 后都应该重新计算 stats。
- 转换后必须留下 conversion report，否则这批数据以后很难被复现和审计。

## 实践任务

任选一种路径：

- HDF5 -> LeRobot
- RLDS -> LeRobot
- LeRobot v2 -> LeRobot v3

写一份转换计划，至少包含：

1. 源数据的关键字段树。
2. 目标数据的 feature schema。
3. 关键字段映射表。
4. 至少 3 个语义风险。
5. 时间对齐策略。
6. 过滤规则。
7. 转换后验证项。
8. conversion report。

## 自查问题

1. 为什么说转换成功不能只看文件能不能打开？
2. `obs` 和 `next_obs` 同时存在时，行为克隆训练通常应该用哪个？
3. `done` 和 `success` 有什么区别？
4. 为什么两个数据集的 `action` shape 都是 `[7]`，仍然不能直接混训？
5. 从 RLDS 转 LeRobot 时，为什么最后一帧最容易出错？
6. 为什么删除 episode 或合并数据集后要重新计算 `stats`？
7. 什么情况下必须人工抽样看视频，而不是只看脚本日志？
