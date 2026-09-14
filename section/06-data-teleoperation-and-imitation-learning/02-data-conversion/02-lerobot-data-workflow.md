# LeRobot 数据工作流

目标：掌握 LeRobot 数据从采集、回放、可视化、清洗、切分到发布的最小工作流，并能用它审计转换后的数据。

LeRobot 不只是一个数据格式，也是一套围绕机器人数据采集、检查、回放、清洗和发布的工具链。本节不讲策略训练，也不讨论某个 policy 的成功率，而是把 LeRobot 当作一个数据工程范例。

这条数据工程链路从硬件连通性检查开始，到遥操作 dry run、正式记录 episode、可视化检查、动作回放、删除坏数据、切分训练集与验证集、合并数据、重算统计量，最后形成一份可以交给训练阶段的数据卡。

前面几节已经讲过 LeRobotDataset 的目录结构和版本差异，也讲过 HDF5、RLDS 等格式之间的转换。这里换一个更贴近真实项目的问题：当你真的要采一批机器人数据时，怎样保证它不只是“看起来能读”，而是能被后续训练、评测和复现实验可靠使用。


## 本节要解决的问题

读完这一页，可以用下面几个问题检查自己是否读懂：

1. 为什么不能一上来就 `lerobot-record`，而要先做环境检查和遥操作 dry run。
2. `lerobot-info`、`lerobot-teleoperate`、`lerobot-record`、`lerobot-dataset-viz`、`lerobot-replay`、`lerobot-edit-dataset` 分别解决什么问题。
3. 一条 episode 在采集过程中什么时候被保存，什么时候应该被丢弃。
4. 为什么 `save_episode()` 和 `finalize()` 是两个不同层面的收尾动作。
5. 为什么采集后不能直接训练，而要先做可视化、回放、删除、切分和重算统计量。
6. 为什么 train / val / test 不能按 frame 随机切。
7. 一份最小数据卡应该记录哪些信息，才能让别人判断这批数据是否可信。

这些问题合起来，就是一条完整的 LeRobot 数据工作流。

## 先看完整流程

LeRobot 数据工作流可以理解为一条从“硬件能不能动”到“数据能不能训练”的流水线：

```text
system check
  -> teleoperate dry run
  -> record dataset
  -> inspect / replay / edit dataset
  -> split / merge / recompute stats
  -> write data card
  -> hand off to training
```

这条流程的关键不在于命令多，而在于每一步的验收目标不同：

| 阶段 | 你要证明什么 | 如果跳过会怎样 |
|---|---|---|
| 系统检查 | 环境、依赖、相机、编码器、硬件接口可用 | 采集中途才发现视频不能编码或设备不可见 |
| 遥操作 dry run | 控制方向、夹爪方向、相机画面和时间同步正常 | 录下一批动作反向、夹爪错误或画面错位的数据 |
| 正式采集 | episode、frame、task、action、timestamp 被稳定记录 | 数据结构不完整，后续无法训练或复现 |
| 可视化检查 | 训练会读取到的数据内容正确 | 坏视频、错相机、错动作混进训练集 |
| 回放检查 | action 维度、顺序、尺度和接口基本可执行 | 模型学到的动作不能发回真实机器人 |
| 编辑清洗 | 删除坏 episode，修正任务文本和字段 | 噪声数据污染模型 |
| 切分合并 | train / val / test 切分合理，合并后 schema 一致 | 验证指标虚高，或合并后 stats 错误 |
| 数据卡封口 | 记录来源、硬件、版本、清洗规则和已知问题 | 后续无法解释模型成功或失败的原因 |

成熟的数据工作流不会在 episode 录完时结束，还要给每一步留下可追踪的证据。

## 先分清几个核心概念

在开始命令之前，先把几个术语统一。

`repo_id` 是 Hugging Face Hub 上的数据集仓库名，通常写成：

```text
<user>/<dataset_name>
```

例如：

```text
my_name/cube_pick_place
```

它回答的是“这批数据在 Hub 上叫什么”。如果只是本地开发，也可以先把数据落在本地 root 下，但公开文档里不要写机器上的绝对路径。

`root` 是数据在本地的落盘位置。它常用于本地缓存、调试和离线读取。正式数据卡里通常只写是否使用固定 root、数据是否上传 Hub，不写某台机器上的具体路径。

`robot.id` 和 `teleop.id` 是硬件和标定绑定的逻辑 id。它们不是随便起的名字，而是贯穿遥操作、采集和回放的身份标识。若同一台硬件在不同阶段用了不同 id，就可能加载错误标定或错误配置，造成动作偏移。

`episode` 是一次完整任务轨迹，从开始执行任务到任务结束。例如“把方块拿起并放进盒子”可以是一条 episode。

`frame` 是 episode 中的一个时间步。一个 frame 通常包含图像、机器人状态、动作、任务文本、时间戳和索引。

`save_episode()` 保存当前这一条 episode 的数据、视频和 metadata。它解决的是“这一条轨迹是否进入数据集”。

`finalize()` 是整个采集 session 的收尾动作，用来刷新 Parquet footer、metadata、统计量等，使数据集后续能稳定读取。它解决的是“整个数据集是否封口完整”。

Rerun 是用于时间序列可视化的工具。它可以把图像、状态、动作曲线、标量、任务文本和时间戳放在同一个时间轴上查看。对机器人数据来说，Rerun 的价值很大，因为很多问题只看文件结构看不出来，必须看时间对齐。

## 数据阶段命令怎么理解

LeRobot 的数据相关命令可以按工作阶段理解：

| 命令 | 作用 | 不是用来做什么 |
|---|---|---|
| `lerobot-info` | 查看环境、依赖、GPU、FFmpeg、LeRobot 脚本和硬件发现情况 | 不采集数据 |
| `lerobot-teleoperate` | 用 leader、键盘或手柄控制 follower，检查控制链路 | 不保存正式 episode |
| `lerobot-record` | 记录人类遥操作 episode，生成 LeRobotDataset | 不做 policy inference |
| `lerobot-dataset-viz` | 用 Rerun 可视化数据集中图像、状态、动作和时间戳 | 不替代人工质量判断 |
| `lerobot-replay` | 从数据集中读取 action 并发回机器人 | 不等于成功率评测 |
| `lerobot-edit-dataset` | 删除、切分、合并、改任务、重算 stats、重编码视频 | 不替代数据卡 |

这几个命令的关系可以画成：

```text
lerobot-info
   |
   v
lerobot-teleoperate
   |
   v
lerobot-record
   |
   v
lerobot-dataset-viz ----> lerobot-edit-dataset
   |                              |
   v                              v
lerobot-replay              clean dataset
                                  |
                                  v
                            data card / training
```

这里最容易误解的是 `lerobot-replay`。它只是把数据集里的动作重新发给机器人，用来检查动作接口、维度顺序和尺度是否合理。真实世界中，物体初始位置、摩擦、延迟和环境状态稍有不同，同一段动作回放不一定完成任务。因此 replay 不能被直接当成 policy 成功率评测。

## 第 0 步：环境和硬件检查

开始采集前，先运行：

```bash
lerobot-info
```

这一步看似简单，但它决定后面很多问题会不会提前暴露。一次完整实验记录至少应该保存下面这些信息：

| 项目 | 为什么要记录 |
|---|---|
| LeRobot 版本 | 不同版本的数据格式、命令参数和默认行为可能不同 |
| Python / PyTorch / CUDA 或 CPU 后端 | 影响采集环境和后续复现 |
| FFmpeg 版本与编码能力 | LeRobot v3 常把图像写成 MP4，编码器异常会直接影响数据 |
| 已安装的 LeRobot console scripts | 确认命令是否来自预期环境 |
| 机器人是否能被发现 | 提前排除端口、权限和驱动问题 |
| teleoperator 是否能被发现 | 提前排除 leader、手柄或键盘控制问题 |
| 相机是否能被发现 | 提前确认相机 index、分辨率、FPS 和画面方向 |

FFmpeg 特别值得单独强调。机器人数据中的图像往往以视频形式保存。如果编码器不可用、像素格式不兼容、帧率写错，数据集可能在采集时看似正常，但后续可视化或训练时才发现视频无法读取。

采集前还要做一轮硬件安全检查：

1. 急停是否有效。
2. 机械臂限位是否正确。
3. 人工接管和复位流程是否清楚。
4. 相机支架和线缆是否固定。
5. 任务物体是否在安全范围内。
6. 采集人员是否知道如何丢弃当前 episode。
7. 如果数据会上传 Hub，账号和仓库命名规则是否已经确定。

机器人数据采集不是普通脚本运行。只要涉及真实硬件，先保证安全，再考虑效率。

## 第 1 步：先遥操作，不直接录数据

环境检查通过后，不应该马上开始 `lerobot-record`，而是先做遥操作 dry run：

```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=<robot_port> \
  --robot.id=my_follower \
  --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader \
  --teleop.port=<teleop_port> \
  --teleop.id=my_leader \
  --display_data=true
```

这条命令里有几类信息：

| 参数 | 含义 |
|---|---|
| `--robot.type` | follower 机器人类型 |
| `--robot.port` | follower 连接端口 |
| `--robot.id` | follower 的逻辑 id |
| `--robot.cameras` | 相机配置，包括名称、类型、分辨率、FPS |
| `--teleop.type` | leader 或遥操作设备类型 |
| `--teleop.port` | leader 连接端口 |
| `--teleop.id` | leader 的逻辑 id |
| `--display_data=true` | 是否显示观测和控制数据，便于检查 |

遥操作循环可以概括成：

```text
robot.get_observation()
teleop.get_action()
teleop_action_processor(...)
robot_action_processor(...)
robot.send_action(...)
optional Rerun logging
precise_sleep(...)
```

这个循环里有两个处理器值得注意：

- `teleop_action_processor(...)` 可能处理 leader 端输入，例如坐标变换、按键映射、手柄死区、夹爪开合转换。
- `robot_action_processor(...)` 可能处理 follower 端动作，例如限幅、速度限制、坐标系转换、安全过滤。

如果后面记录的数据保存的是 processed action，而不是 raw action，就需要在数据卡里写清楚。否则训练出来的模型到底是在学习人手原始输入，还是学习发送到机器人的最终动作，会变得不清楚。

dry run 阶段至少要检查：

1. leader 往左，follower 是否也往左。
2. leader 往前，follower 是否朝预期方向运动。
3. 夹爪开合方向是否正确。
4. 相机名称是否对应真实视角，例如 `front` 是否真的是前视角。
5. 图像是否上下颠倒或左右镜像。
6. 控制 FPS 是否稳定。
7. Rerun 中图像、状态和动作是否大体同步。
8. 机器人静止时 action 是否接近零或预期保持值。
9. 复位后系统是否还能继续稳定控制。

这一步的原则很简单：遥操作不稳定，不要录数据。错误数据比没有数据更难处理，因为它可能结构完整、能正常读取，却在语义上完全错误。

## 第 2 步：正式记录数据集

遥操作稳定后，才进入正式记录阶段。典型命令如下：

下面是 bash 写法示例。Windows / PowerShell 用户可以直接把 `${HF_USER}` 替换成自己的 Hugging Face 用户名。

```bash
HF_USER=$(huggingface-cli whoami | head -n 1)

lerobot-record \
  --robot.type=so101_follower \
  --robot.port=<robot_port> \
  --robot.id=my_follower \
  --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader \
  --teleop.port=<teleop_port> \
  --teleop.id=my_leader \
  --display_data=true \
  --dataset.repo_id=${HF_USER}/cube_pick_place \
  --dataset.num_episodes=50 \
  --dataset.single_task="Pick up the cube and place it in the box" \
  --dataset.streaming_encoding=true \
  --dataset.encoder_threads=2
```

这条命令除了机器人和遥操作设备配置外，还包含 dataset 相关参数：

| 参数 | 含义 |
|---|---|
| `--dataset.repo_id` | 数据集仓库名 |
| `--dataset.num_episodes` | 本次要采集多少条 episode |
| `--dataset.single_task` | 本批数据的任务文本 |
| `--dataset.streaming_encoding` | 是否边采集边编码视频 |
| `--dataset.encoder_threads` | 视频编码线程数 |

LeRobot 0.5.2 中，`DatasetRecordConfig` 的常见默认值包括：

| 配置 | 默认值 | 含义 |
|---|---:|---|
| `fps` | 30 | 记录和控制目标频率 |
| `episode_time_s` | 60 | 每条 episode 最长记录时间 |
| `reset_time_s` | 60 | episode 之间给人工复位的时间 |
| `num_episodes` | 50 | 默认采集 episode 数 |
| `video` | `True` | 图像保存为视频 |
| `push_to_hub` | `True` | 采集结束后上传到 Hub |
| `streaming_encoding` | `False` | 默认不实时编码视频 |

这些默认值不能盲信。比如默认 `fps=30` 不代表你的相机真的稳定输出 30 FPS；默认 `episode_time_s=60` 不代表每个任务都适合记录 60 秒。实际项目应该根据任务长度、控制频率、相机负载和存储速度调整。

### 一帧里通常记录什么

正式采集时，每个 frame 通常会保存：

```text
observation frame
action frame
task string
timestamp
frame index
episode index
episode metadata
```

其中 observation 可能包括：

```text
observation.images.front
observation.images.wrist
observation.state
```

action 可能包括：

```text
action
```

task 可能是 episode 级，也可能是 frame 级重复保存。对单任务采集来说，所有 episode 的 task 文本可能一样；对多任务采集来说，必须确保每条 episode 的 task 和实际任务一致。

### raw action、processed action 和 sent action

在真实采集中，action 这个词有时会指不同层次：

```text
raw action       : 遥操作设备产生的原始动作
processed action : 经过坐标变换、裁剪、限幅后的动作
sent action      : 最终发送给机器人控制接口的动作
```

如果数据集中只保存其中一种，就要在数据卡中说明。如果保存的是 processed action，那么模型训练学到的就是处理后的动作分布；部署时也要用同样的后处理方式。否则训练和部署会不一致。

## streaming encoding：效率和实时性的权衡

`streaming_encoding=true` 表示边采集边编码 MP4，而不是先保存图像再统一编码视频。

它的好处是：

- `save_episode()` 可能更快。
- 不需要保留大量中间图片。
- 采集完成后更快得到可读取的视频文件。

它的代价是：

- 实时编码会占 CPU 或 GPU 资源。
- 编码线程过多可能影响控制循环。
- 高分辨率多相机时容易让 FPS 下降。
- 编码失败可能影响当前 episode 的保存。

因此，如果采集时发现机器人控制卡顿、Rerun 中时间戳不稳定或视频帧率异常，可以按下面顺序排查：

```text
先降低 encoder_threads
  -> 再降低相机分辨率
  -> 再降低相机 FPS
  -> 再关闭 streaming_encoding
  -> 最后检查 FFmpeg 和磁盘写入速度
```

对于初学者，小规模采集时可以先关闭流式编码，把系统稳定性跑通后再优化效率。

## Episode 保存、丢弃和 resume

`lerobot-record` 会把任务记录时间和复位时间分开：

```text
record episode with dataset
reset environment without dataset
if rerecord:
    clear_episode_buffer()
else:
    save_episode()
finally:
    finalize()
```

这段流程非常重要。

“record episode with dataset” 表示任务执行过程会进入数据缓冲区；“reset environment without dataset” 表示复位过程不进入训练数据。这样做是为了避免模型学到无关动作。

比如任务是“把方块放进盒子”，人工复位时把方块拿回起点、把机械臂移回初始位姿，这些动作不属于任务示教，不应该混进 episode。

当一条 episode 失败时，采集人员应该能够选择丢弃并重录。丢弃时会清空当前缓冲，不保存这条坏数据。失败 episode 是否完全删除，要看项目目标：如果是训练成功示教策略，失败轨迹通常删除；如果研究失败恢复或人类纠错，则失败轨迹也可能保留，但必须标注清楚。

如果采集中途断电或程序崩溃，LeRobot 支持 resume。这里有一个容易出错的点：

```text
dataset.num_episodes 表示“本次还要追加多少条”，不是最终总数。
```

例如原计划采 50 条，已经完成 30 条，中断后恢复时设 `num_episodes=20`，表示再追加 20 条。数据卡里应该记录：

```yaml
resume:
  original_repo_id: user/cube_pick_place
  completed_before_resume: 30
  additional_episodes: 20
  reason: power interruption
```

否则后面别人看到数据总数，很难知道它是一次采完，还是多次追加。

## 第 3 步：录完先可视化，不要直接训练

录完数据后，第一件事应该是看数据，而不是训练。使用：

```bash
lerobot-dataset-viz \
  --repo-id ${HF_USER}/cube_pick_place_20260522_143000 \
  --episode-index 0
```

`lerobot-dataset-viz` 会用 Rerun 显示训练真正会读取到的数据，包括：

- 相机图像。
- action 曲线。
- state 曲线。
- 任务文本。
- 时间戳。
- frame index。

这里要注意：它显示的是训练会读取的数据，不是相机原始流。也就是说，如果视频编码、相机 key、时间戳、feature schema 或 action 字段有问题，通常会在这里暴露。

可视化时至少要抽查：

| 抽查对象 | 为什么 |
|---|---|
| 第 0 条 episode | 检查采集开头是否正常 |
| 最短 episode | 检查提前结束或失败样本 |
| 最长 episode | 检查长时间录制是否掉帧 |
| 随机 3 条 episode | 避免只看顺手样本 |
| 删除候选 episode | 确认是否真的需要删除 |
| 每个 task 至少 1 条 | 多任务数据必须覆盖所有任务文本 |

可视化时重点看这些现象：

1. 图像是否花屏、黑屏、卡顿或帧重复。
2. 任务开始前是否有大量无关动作。
3. reset 动作是否混入 episode。
4. action 曲线是否突然出现巨大尖峰。
5. state 和 action 是否有明显时间错位。
6. 夹爪动作是否和画面中的开合对应。
7. task 文本是否和实际动作一致。
8. 多相机画面是否对应正确相机名称。
9. episode 结束位置是否合理。

如果这些问题没有处理，训练脚本通常不会报错，但模型会学到错误行为。

## 第 4 步：回放动作检查接口

可视化通过后，可以用 `lerobot-replay` 检查动作接口：

```bash
lerobot-replay \
  --robot.type=so101_follower \
  --robot.port=<robot_port> \
  --robot.id=my_follower \
  --dataset.repo_id=${HF_USER}/cube_pick_place_20260522_143000 \
  --dataset.episode=0
```

回放时，系统会从数据集中读取 `action`，按数据集 FPS 发给机器人。它主要检查：

- action 维度是否符合控制接口。
- action 维度顺序是否正确。
- action 数值尺度是否合理。
- 夹爪控制是否能正常执行。
- 数据集 FPS 和回放节奏是否一致。
- `robot.id` 是否能加载正确标定。

回放失败不一定说明数据错，因为真实环境有很多变化：物体位置不同、摩擦不同、延迟不同、复位误差不同、夹爪接触状态不同。更准确地说，`lerobot-replay` 的目标是检查“动作接口是否合理”，不是证明“任务一定成功”。

如果回放时机器人突然大幅移动，常见原因包括：

1. action 单位错了，例如米和毫米混淆。
2. action 表示错了，例如把增量动作当成绝对位置。
3. action 维度顺序错了。
4. stats 或归一化反归一化配置错了。
5. robot id 不一致，加载了错误标定。
6. 数据集中保存的不是最终 sent action，而是某个中间动作。

## 第 5 步：编辑、清洗和切分

发现坏数据后，用 `lerobot-edit-dataset` 清理：

```bash
lerobot-edit-dataset \
  --repo_id ${HF_USER}/cube_pick_place_20260522_143000 \
  --new_repo_id ${HF_USER}/cube_pick_place_clean \
  --operation.type delete_episodes \
  --operation.episode_indices "[3, 7, 18]"
```

这里建议使用 `new_repo_id` 输出一个新的 clean 数据集，而不是覆盖原数据。保留 raw dataset 的好处是：后续如果清洗规则改了，可以重新从原始数据生成 clean 版本。

常用编辑操作包括下面几类。具体 `operation.type` 名称可能随 LeRobot 版本略有变化，实际执行前应以 `lerobot-edit-dataset --help` 和当前版本文档为准。

| 操作 | 用途 | 注意点 |
|---|---|---|
| `info` | 查看 episode 数、frame 数和 feature 信息 | 适合清洗前后对比 |
| `delete_episodes` | 删除失败或异常 episode | 要记录删除原因 |
| `split` | 切分 train / val / test | 不要按 frame 随机切 |
| `merge` | 合并多个同 schema 数据集 | 合并前检查 action 语义 |
| `update_tasks` / `modify_tasks` | 修正任务文本 | 同义任务要统一，注意当前版本实际名称 |
| `remove_feature` | 删除不需要的相机或字段 | 删除后要更新 schema 和 stats |
| `recompute_stats` | 重算归一化统计量 | 删除、合并、改字段后必须做 |
| `convert_image_to_video` / `convert_to_video` | 图片转视频或重编码为视频格式 | 检查编码、画质和帧同步 |

## 为什么不能按 frame 切分

机器人数据中相邻帧高度相关。假设一条 episode 中连续几帧是：

```text
frame 100: 机械臂靠近方块
frame 101: 机械臂稍微更近一点
frame 102: 机械臂继续靠近
```

如果按 frame 随机切，很可能出现：

```text
frame 100 -> train
frame 101 -> val
frame 102 -> test
```

这会导致验证集和测试集泄漏训练集信息。模型在 val/test 上表现很好，并不代表真的泛化，只是因为它见过几乎相同的相邻帧。

更合理的切分单位是：

| 切分单位 | 适合场景 |
|---|---|
| episode | 最基本的切分方式 |
| task | 测试未见任务泛化 |
| variation | 测试同一任务的不同变化 |
| object instance | 测试未见物体 |
| scene | 测试未见环境 |
| operator | 测试不同操作者风格 |
| collection date | 测试跨天、跨批次稳定性 |

如果只是课程小实验，至少要做到 episode-level split。如果是严肃评测，最好按任务、物体、场景或操作者做更强切分。

## 合并数据集时检查什么

合并数据集比删除 episode 更危险，因为两个数据集看起来 schema 一样，语义却可能不同。

合并前至少检查：

1. `features` 是否完全一致。
2. `fps` 是否一致。
3. `robot_type` 是否一致。
4. action 表示是否一致，是末端增量、关节位置还是速度命令。
5. action 单位是否一致。
6. 夹爪开合方向是否一致。
7. 相机名称是否一致。
8. 相机分辨率和裁剪方式是否一致。
9. task 文本是否需要统一。
10. 是否包含 `operator_id`、`scene_id`、`intervention` 等扩展字段。
11. 合并后是否重算 stats。

如果合并的是不同日期、不同场景、不同操作者的数据，建议保留来源字段，例如：

```yaml
source:
  collection_day: day_02
  operator_id: op_03
  scene_id: kitchen_table_a
```

这些字段不一定进入模型训练，但对后续错误分析非常有用。

## 最小数据清单

一个可以交给训练阶段的数据集，至少要有一份 manifest 或数据卡。下面是一个最小模板：

```yaml
hardware:
  robot_type: so101_follower
  robot_id: my_follower
  teleop_type: so101_leader
  teleop_id: my_leader
  cameras:
    front:
      type: opencv
      width: 640
      height: 480
      fps: 30

dataset:
  repo_id_raw: user/cube_pick_place_20260522_143000
  repo_id_clean: user/cube_pick_place_clean
  lerobot_version: "0.5.2"
  code_commit: dfdc48a7f131c89ade51e322f5c11180b8509c72
  fps: 30
  num_episodes_raw: 50
  num_episodes_clean: 47
  removed_episodes:
    - index: 3
      reason: "object slipped out of workspace"
    - index: 7
      reason: "camera dropped frames"
    - index: 18
      reason: "wrong task execution"
  single_task: "Pick up the cube and place it in the box"
  split_rule: "episode-level split by object position"
  stats_recomputed: true

checks:
  lerobot_info_saved: true
  teleoperate_dry_run_checked: true
  dataset_viz_sampled_episodes: [0, 5, 12, 25, 49]
  replay_checked_episodes: [0, 12]
  known_issues:
    - "minor lighting variation across episodes"
```

这份清单解决的是复现和责任边界问题。训练效果好或坏时，别人至少能知道数据是怎么来的、删了什么、怎么切分、stats 是否重算、是否做过可视化和回放检查。

## 一条数据能进入训练前的验收标准

在本章里，验收标准不是 policy 成功率，而是数据是否可信。一个 clean LeRobot 数据集至少应该满足：

1. 能被指定版本的 LeRobot 正常读取。
2. `meta/info.json` 中 feature schema 清楚。
3. episode 数和 frame 数符合预期。
4. 每个视频 feature 的帧数和数据行数对齐。
5. 每条 episode 的 task 文本正确。
6. 已删除坏 episode，并记录删除原因。
7. train / val / test 按 episode 或更高层级切分。
8. 删除、合并、改字段后已经重算 stats。
9. 至少抽样可视化过多条 episode。
10. 至少回放检查过若干条动作。
11. 数据卡记录硬件、版本、任务、清洗规则和已知问题。

如果这些条件没有满足，数据不应该直接进入训练阶段。

## 常见错误

下面这些错误在真实采集中很常见：

| 错误 | 表现 | 修正 |
|---|---|---|
| 没先 teleoperate 就 record | 动作方向或夹爪方向错误 | 先做 dry run 并用 Rerun 检查 |
| `robot.id` / `teleop.id` 不一致 | 加载错标定，动作偏移 | 同一硬件全流程使用同一 id |
| 相机 key 起错 | `front` 实际是 wrist 或 side | 采集前看画面，数据卡写清视角 |
| 采集后不 `finalize()` | metadata 不完整或读取失败 | 采集结束必须封口 |
| reset 动作混入 episode | 模型学到无关复位行为 | reset 阶段不要传 dataset |
| repo_id 覆盖旧数据 | 数据版本混乱 | raw 和 clean 数据用不同 repo_id |
| 不看数据直接训练 | 坏 episode 污染模型 | 先 viz、replay、edit、split |
| 按 frame 随机切分 | 验证指标虚高 | 按 episode、task、场景或物体切分 |
| 合并后不重算 stats | 归一化统计量错误 | 删除、合并、改字段后重算 |
| 任务文本不统一 | 同一任务多个标签 | 使用统一 taxonomy 或任务编辑操作 |
| 只保存命令不保存版本 | 后续无法复现 | 数据卡记录 LeRobot 版本和 commit |

## 实践任务

为一个小型桌面操作任务跑通 LeRobot 数据工作流。你需要提交：

1. `lerobot-info` 输出摘要：LeRobot、Python、PyTorch、CUDA 或 CPU、FFmpeg。
2. Teleoperate 证据：命令、硬件 id、相机配置、Rerun 截图或文字检查结果。
3. Record 证据：`dataset.repo_id`、episode 数、FPS、任务文本、是否 streaming encoding。
4. Dataset 证据：`lerobot-dataset-viz` 检查过的 episode、发现的问题和删除规则。
5. Replay 证据：回放过哪些 episode，动作接口是否正常。
6. Edit 证据：删除、切分、合并或重算 stats 的命令和结果。
7. 数据卡：采集来源、硬件、任务、字段、清洗规则、版本和已知问题。

验收标准是：另一个人只看数据卡和 repo_id，就能判断这批数据是否可以进入训练，并能复现数据读取过程。

## 自查问题

1. 为什么 `lerobot-record` 之前必须先做 `lerobot-teleoperate`？
2. `save_episode()` 和 `finalize()` 的区别是什么？
3. 为什么 `lerobot-replay` 不是成功率评测？
4. streaming encoding 会带来什么好处和风险？
5. 为什么 train / val / test 不能按 frame 随机切？
6. 合并两个 LeRobot 数据集前，为什么不能只看 feature 名称一样？
7. 删除 episode 或合并数据后，为什么必须重算 stats？
8. 一份最小数据卡应该记录哪些信息？
