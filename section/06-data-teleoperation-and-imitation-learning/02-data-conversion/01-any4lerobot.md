# Any4LeRobot

目标：理解 Any4LeRobot 在跨生态数据接入中的定位，知道它有哪些功能、如何选择 converter，以及转换工具能解决什么、不能替你验证什么。

Any4LeRobot 是围绕 LeRobot 数据生态整理的一组社区工具。它不负责训练策略，也不重新定义机器人数据格式；它的主要作用，是把分散在不同项目里的机器人数据转换到 LeRobot，或者从 LeRobot 再导出到 RLDS 等训练栈需要的格式。

读这一节时，不需要一开始就把所有转换器都跑一遍，更重要的是学会判断一个转换工具在做什么、没做什么，以及转换完成后还需要人工审计哪些地方。

项目入口：[Tavish9/any4lerobot](https://github.com/Tavish9/any4lerobot)。

## 先把它看成一座转换桥

前面几节已经讲过，机器人数据格式并不统一。Open X-Embodiment 常用 RLDS / TFDS，LIBERO 和 RoboCasa 常以 HDF5 仿真轨迹出现，RoboMIND 也有 HDF5、多视角和语言任务，AgiBot World 则包含视频、状态、任务元信息和更复杂的采集组织方式。

LeRobot 自己也有 v2.1、v3.0 等不同数据布局。Any4LeRobot 的价值，正是把这些来源和版本之间的转换路径集中起来，而不是让每个项目都临时写一套脚本。

如果每个数据源都单独写一个临时脚本，很快会出现三个问题。

第一，脚本只对当前项目有效。今天能把某个 HDF5 转成 LeRobot，明天换一个数据集，key 名不同、相机名不同、action 维度不同，脚本就要重写。

第二，转换过程不可追溯。很多临时脚本只留下一个输出目录，后来很难知道哪些 episode 被跳过了，哪些相机被保留了，action 是否做过归一化，stats 是否重新计算过。

第三，输出数据虽然“能读”，但不一定“能安全训练”。机器人数据最怕静默错误，例如图像和 action 错开一帧，夹爪方向反了，或者 action 单位从米变成毫米。这些问题通常不会让程序报错，但会直接影响训练结果。

Any4LeRobot 的作用，就是把常见的转换路径集中起来，让不同来源的数据能进入 LeRobot 生态，也让 LeRobot 数据能导出到其它生态。可以把它理解成下面这条桥：

```text
Open X / AgiBot / RoboMIND / LIBERO / RoboCasa / LeRobot old versions
        ↓
    Any4LeRobot converters
        ↓
LeRobotDataset v2.1 / v3.0 或 RLDS
```

注意，这座桥解决的是“格式和流程”的问题，不自动保证所有语义都正确。它能帮你把目录、metadata、视频、Parquet 和 stats 组织起来，但它不能替你判断“这个 action 的第 0 维到底是不是 x 方向位移”。

## Any4LeRobot 和 LeRobot 本体的区别

刚入门时容易把 Any4LeRobot 和 LeRobot 混在一起。它们的关系可以这样理解：

| 名称 | 主要解决的问题 | 更像什么 |
|---|---|---|
| LeRobot | 数据集格式、采集、可视化、回放、训练、策略部署等完整机器人学习工具栈 | 目标生态 |
| Any4LeRobot | 把外部数据转成 LeRobot，或把 LeRobot 转成其他格式 | 转换工具箱 |
| LeRobotDataset | LeRobot 使用的数据集组织规范，例如 v2.1、v3.0 | 数据格式 |
| 具体 converter | 某个源数据到某个目标格式的转换脚本 | 数据搬运与重组流程 |

所以，Any4LeRobot 不是另一个训练框架。它更像数据工程里的“适配层”：上游面对各种数据源，下游对接 LeRobot 或 RLDS。

这一点很重要。使用 Any4LeRobot 以后，仍然应该用 LeRobot 的数据检查、可视化、回放和编辑工具继续审计数据，而不是把转换脚本跑完就直接训练。

## 它到底有哪些功能

它不只做“把某个数据集转成 LeRobot”这一件事，而是围绕 LeRobot 数据生态整理了几类工具。

| 功能类别 | 具体内容 | 对初学者的意义 |
|---|---|---|
| Dataset Tutorial | 数据加载、编辑、过滤、采样、合并 | 先学会怎么检查和整理 LeRobot 数据集 |
| Data Conversion | Open X、AgiBot World、RoboMIND、LIBERO、RoboCasa 转 LeRobot，以及 LeRobot 转 RLDS | 把外部数据接入 LeRobot，或把 LeRobot 数据导出到其它训练生态 |
| Version Conversion | LeRobot v1.6、v2.0、v2.1、v3.0 之间的版本转换 | 处理旧数据升级、新格式回退和脚本兼容问题 |
| Training | `MultiLeRobotDataset` 等多数据集训练辅助 | 让多个 LeRobot 数据源可以组合进入训练流程 |

所以读 Any4LeRobot 时，不要只把它看成一个 converter。更准确地说，它覆盖了三个连续环节：

```text
整理已有 LeRobot 数据
  -> 把外部数据转成 LeRobot / 把 LeRobot 转到其它生态
  -> 把多个 LeRobot 数据源组织进训练
```

不过，这一页的重点仍然放在 Data Conversion。原因是本章讨论的是数据格式和数据转换；训练相关能力只需要知道它存在，具体的训练策略会放到后续章节。

## 拿到项目后先看哪些目录

Any4LeRobot 的项目目录基本是按转换方向组织的。拿到仓库后，按你的源数据类型选择对应目录。

| 目录 | 解决的问题 | 先确认什么 |
|---|---|---|
| `openx2lerobot/` | Open X-Embodiment / RLDS / TFDS 数据转 LeRobot | 子数据集、机器人本体、action convention |
| `agibot2lerobot/` | AgiBot World 数据转 LeRobot | 数据版本、任务元信息、质检字段和动作语义 |
| `robomind2lerobot/` | RoboMIND 数据转 LeRobot | 机器人类型、HDF5 字段、多视角和语言标注 |
| `libero2lerobot/` | LIBERO 仿真 HDF5 数据转 LeRobot | 任务套件、语言指令、success / done 语义 |
| `robocasa2lerobot/` | RoboCasa 仿真数据转 LeRobot | 是否 replay 或重新渲染、相机和分辨率是否变化 |
| `lerobot2rlds/` | LeRobot 数据导出到 RLDS | episode / step flags、`is_last` 和 `is_terminal` |
| `ds_version_convert/` | LeRobotDataset 版本互转 | v2 / v3 文件结构、episode offset 和 stats |

这张表不用背，先拿它建立一个查找顺序：

```text
先问源数据是什么
  -> 再找对应转换目录
  -> 再读该目录 README 或脚本参数
  -> 最后才运行转换
```


## 一个 converter 通常怎么用

不同 converter 的命令行参数不完全一样，所以本节不建议背某一个固定命令。更稳妥的做法是掌握通用使用流程。

```text
1. 准备源数据目录
   确认源数据是否已经下载完整，是否包含 metadata、图像、状态和动作。

2. 选择目标格式
   明确是输出 LeRobotDataset v2.1、v3.0，还是导出到 RLDS。

3. 阅读对应 converter 的 README 或脚本参数
   重点看必填路径、数据集名称、任务过滤、相机选择、输出目录和格式版本。

4. 先做小样本 dry run
   不要直接全量转换。先用少量 episode 检查目录结构和字段。

5. 检查输出目录
   至少应该看到 meta、data、videos 等 LeRobot 关键部分，或者 RLDS 所需的 episode / step 结构。

6. 打开 meta/info.json
   检查 total_episodes、total_frames、features、fps、robot_type、data_path 和 video_path。

7. 抽样可视化
   看图像、action、state、task 是否对齐，尤其检查第一帧、最后一帧和失败样本。

8. 重算或确认 stats
   只要过滤、合并、改 action、改 state，就应该重新计算或明确说明 stats 来源。

9. 写 conversion report
   记录源数据、工具版本、命令、过滤规则、输出 schema 和抽样检查结果。
```

一个抽象的命令形态可以这样理解：

```bash
python path/to/converter.py \
  --src /path/to/source_dataset \
  --out /path/to/output_lerobot_dataset \
  --dataset-name example_name \
  --target-version v3.0
```

这不是某个目录的固定可复制命令，而是提醒你：任何 converter 至少都要说清楚源数据、输出位置、数据集名称和目标格式。具体参数必须以对应目录的 README 或脚本帮助为准。

## 转换后最少要看到什么

如果目标是 LeRobotDataset，转换后不要只看输出目录存在。至少要确认下面这些东西：

```text
meta/info.json
meta/stats.json
meta/tasks.* 或 task 相关 metadata
meta/episodes/ 或 episodes metadata
data/
videos/（如果有 video feature）
```

其中 `meta/info.json` 最关键。它应该能回答：

```text
这个数据集有多少 episode？
总共有多少 frame？
有哪些 observation feature？
action 的 shape 和 names 是什么？
图像是 video feature 还是普通数组？
fps 是多少？
data_path 和 video_path 指向哪里？
```

如果这些问题回答不了，说明 converter 可能只是把文件搬过去了，还没有形成一份可审计的 LeRobot 数据集。

## 它覆盖哪些转换方向

Any4LeRobot 目前覆盖的方向大致可以分成三类。

第一类是外部数据转 LeRobot。这是最常见的用途：

| 转换方向 | 源数据常见形态 | 转换后主要用途 |
|---|---|---|
| Open X-Embodiment -> LeRobot | RLDS / TFDS | 把跨机器人真实数据转成 LeRobot 训练和可视化格式 |
| AgiBot World -> LeRobot | 视频、状态、JSON、任务元信息 | 将大规模同构真机数据带入 LeRobot 生态 |
| RoboMIND -> LeRobot | HDF5、多视角、语言任务 | 统一多机器人、多任务演示数据 |
| LIBERO -> LeRobot | HDF5 仿真轨迹 | 让语言条件仿真 benchmark 可用 LeRobot 读取 |
| RoboCasa -> LeRobot | HDF5、仿真 replay、重新渲染 | 将家庭场景仿真任务转成统一训练数据 |

第二类是 LeRobot 转向其它训练生态，例如：

| 转换方向 | 目标用途 |
|---|---|
| LeRobot -> RLDS | 兼容 OpenVLA、Octo 或其它依赖 RLDS / TFDS 的训练栈 |

第三类是 LeRobot 自身版本互转，例如：

| 转换方向 | 常见原因 |
|---|---|
| v1.6 -> v2.0 | 旧数据升级 |
| v2.0 -> v2.1 | 适配较新的 LeRobot 读取器 |
| v2.1 -> v3.0 | 减少小文件数量，适合更大规模和 Hub 读取 |
| v3.0 -> v2.1 | 兼容只支持旧格式的训练或分析脚本 |

这些方向反映了一个现实：真实项目里很少有“从头到尾只用一种格式”的情况。你可能从 Open X 或 HDF5 数据开始，转到 LeRobot 做可视化和训练，再导出到 RLDS 给另一个 VLA 训练栈使用。

## 读一个 converter 时先看什么

不要把转换脚本当成黑盒。一个靠谱的 converter，通常至少包含五个部分。

第一是源数据读取。它要知道源数据在哪里、key 怎么命名、episode 怎么分组、图像和低维状态怎么取出来。

第二是字段映射。它要把源数据里的字段映射到 LeRobot 的 feature，例如把 `agentview_image` 映射到 `observation.images.front`，把 `robot0_joint_pos` 映射到 `observation.state` 的一部分。

第三是视频和数组处理。图像可能来自 HDF5 数组、图片序列、源视频或者仿真重新渲染结果。转成 LeRobot 时，通常需要写成 video feature，并记录分辨率、FPS、编码方式等信息。

第四是 episode 与 metadata 写入。转换器要写出 `meta/info.json`、`meta/tasks`、`meta/episodes`、`data/` 和 `videos/` 等文件，确保每一帧能回到所属 episode、task 和视频位置。

第五是质量过滤与统计量。损坏视频、空 action、长度不一致、失败轨迹、no-op 轨迹可能需要跳过或单独标记。转换完成后还要生成或重算 `meta/stats.json`。

可以把一个 converter 的内部结构理解成：

```text
source reader
  -> schema parser
  -> field mapper
  -> image/video encoder
  -> episode writer
  -> metadata writer
  -> stats calculator
  -> validation logs
```

如果某个脚本只做了 `old_key -> new_key`，却没有处理 episode 边界、action 语义、图像编码、stats 和数据卡，那么它只能算“半成品转换”。

## 转换不是字段复制

数据转换最容易被误解成“把字段名换一下”。例如：

```text
agentview_image -> observation.images.front
robot0_joint_pos -> observation.state
actions -> action
dones -> is_last
```

这些映射当然重要，但只解决了字段层问题。更难的是字段背后的语义。

比如两个数据源的 action 都是 7 维：

```text
dataset A: action = [x, y, z, roll, pitch, yaw, gripper]
dataset B: action = [joint1, joint2, joint3, joint4, joint5, joint6, joint7]
```

它们的 shape 都是 `[7]`，但是一个是末端位姿增量，一个是关节空间命令。把它们都写成 LeRobot 的 `action` 并不意味着它们可以直接混训。

再比如同样是夹爪字段：

```text
dataset A: gripper = 1 表示闭合
dataset B: gripper = 1 表示张开
dataset C: gripper 是夹爪宽度，单位是米
```

如果不写清楚，模型可能学到完全相反的夹爪动作。

所以转换时至少要同时处理四层：

| 层次 | 要处理的问题 | 常见静默错误 |
|---|---|---|
| 字段层 | key 名称怎么映射 | 相机名写对了，但实际视角错了 |
| 语义层 | action、state、gripper 的含义 | shape 一样但动作空间不同 |
| 时间层 | observation 和 action 如何对齐 | 用了 `next_obs` 或错开一帧 |
| 治理层 | 过滤、split、stats、版本如何记录 | episode 数没变但数据含义变了 |

Any4LeRobot 可以帮助你完成结构转换，但这四层仍然要人工检查。

## 一条比较稳妥的转换流程

无论转换 Open X、AgiBot、RoboMIND、LIBERO 还是 RoboCasa，都可以按下面的流程组织。

```text
准备源数据
  -> 阅读源数据说明和 schema
  -> 选定目标 LeRobot 格式版本
  -> 写字段映射表
  -> 小样本 dry run
  -> 检查输出 meta/info.json
  -> 可视化 3-5 条 episode
  -> 全量转换
  -> 重新计算 stats
  -> 抽样检查成功 / 失败 / 边界样本
  -> 写 conversion report
```

这里有两个关键点。

第一，不要一开始就全量转换。大规模机器人数据很容易有几十 GB、几百 GB 甚至 TB 级别。正确做法是先抽几条 episode 跑通，确认字段、视频、action 和 task 都正常，再扩大规模。

第二，转换后的数据要当作一个新数据集重新检查。它虽然来自源数据，但经过了字段映射、视频编码、过滤、分片、stats 计算，已经不是原始数据的简单复制。

## 转换前要写字段映射表

正式转换之前，最好先写一个 mapping 表。这个表不需要很复杂，但必须把关键字段说清楚。

以一个 HDF5 仿真数据转 LeRobot 为例：

| 源字段 | 目标 LeRobot feature | 检查点 |
|---|---|---|
| `obs/agentview_image` | `observation.images.front` | 是否真的是前视角；RGB / BGR 是否正确 |
| `obs/robot0_eye_in_hand_image` | `observation.images.wrist` | 是否是腕部相机；是否和 front 同步 |
| `obs/robot0_joint_pos` | `observation.state` 的一部分 | 维度顺序、单位、是否包含夹爪 |
| `actions` | `action` | 绝对量、增量、速度命令还是归一化动作 |
| `dones` | `is_last` 或 episode 边界 | 是否等同于成功；是否只是时间结束 |
| `rewards` | metadata 或训练字段 | BC 训练是否使用 reward |
| `env_args` | dataset metadata | 是否保留环境、资产、任务配置 |

这张表不是为了显得正式，而是避免转换时“靠记忆写代码”。机器人数据一旦字段多、相机多、任务多，临时判断很容易出错。

## Open X-Embodiment -> LeRobot

Open X-Embodiment 常用 RLDS / TFDS 组织数据。转换到 LeRobot 时，表面上看是把 RLDS 的 episode / step 转成 LeRobot 的 frame / episode metadata，但实际要处理的东西更多。

Open X 的难点在于跨本体。它汇聚了不同实验室、不同机器人和不同任务的数据。RLDS 能统一 episode / step 结构，但不能统一 action 的物理含义。Any4LeRobot 的 OpenX 转换通常要关注下面几件事：

- 读取 RLDS episode 和 step。
- 保留或映射语言指令、任务信息和数据来源。
- 将图像字段写成 LeRobot 的 video feature。
- 将 state 和 action 写成 LeRobot 的低维数据。
- 记录 robot type、数据来源、控制频率和 action convention。
- 处理最后一帧是否有有效 action 的问题。

转换风险主要有三类。

第一，action space 不统一。同一个 `action` 字段在不同 Open X 子数据集中可能表示不同控制接口，不能因为转换到同一个 LeRobot 字段就默认可混训。

第二，任务文本不统一。有些数据有自然语言任务，有些只有任务 id 或短标签。转换时如果强行填充空字符串，后续语言条件训练会受到影响。

第三，控制频率和相机视角不一致。有些数据采集频率低，有些相机是固定外视角，有些是腕部视角。转换时最好保留 `dataset_source`、`robot_type`、`camera_name` 和 `fps` 相关 metadata。

适合的检查方式是：每个子数据集至少抽几条 episode 可视化，确认图像、task、state、action 和 episode 边界是否符合预期。

## AgiBot World -> LeRobot

AgiBot World 这类数据和 Open X 的差别在于，它更像规模化、工业化采集出来的同构或较强规范化数据。源数据里通常不仅有视频和动作，还会有任务元信息、机器人状态、数据质量信息和采集流程相关字段。

转换 AgiBot World 时，重点不是“跨数据集统一”，而是“别丢掉它原本很有价值的采集治理信息”。例如：

- task id、task name、instruction 是否保留。
- 轨迹是否通过质量检查。
- 是否有失败、重试、人工干预或过滤标签。
- 左右臂、末端执行器、灵巧手等状态是否分清。
- action 是否和机器人发送命令一致，还是经过处理后的动作。

如果这些字段在转换时全部扁平化成普通 `observation.state` 和 `action`，数据当然还能训练，但会损失很多后续筛选和分析价值。

比较稳妥的做法是：训练直接用到的字段写成 LeRobot feature，任务层、质检层、来源层信息放进 metadata 或 dataset card。这样既能让模型读取方便，又能保留数据治理信息。

## RoboMIND -> LeRobot

RoboMIND 的特点是多任务、多物体、多协作臂和语言标注。它通常更接近真实演示数据，而不是单一仿真 benchmark。转换时要特别注意两个问题。

第一个问题是机器人本体差异。即使都属于机械臂，不同协作臂的关节数、末端执行器和状态字段也可能不同。转换时不能只保留一个泛化的 `state` 名字，而要写清每个维度的意义。

第二个问题是任务和物体 taxonomy。RoboMIND 的价值之一在于任务类别和物体类别覆盖较丰富。如果转换时只保留自然语言一句话，而丢掉物体类别、任务类别或场景信息，后续就很难做按类别分析。

一个更好的转换结果应该让你能回答：

```text
这条 episode 属于哪个 task？
操作对象是什么类别？
来自哪种机器人？
用了哪些相机？
action 是什么控制空间？
是否是成功演示？
```

如果这些问题回答不了，说明转换输出还不够完整。

## LIBERO -> LeRobot

LIBERO 是语言条件机器人学习里常见的仿真 benchmark，源数据通常是 HDF5 仿真轨迹。它的重点是语言任务、任务套件、长期学习和多任务泛化。

转换 LIBERO 时要关注：

- 任务套件信息，例如属于哪个 benchmark split。
- language instruction 是否完整保留。
- 初始状态和目标条件是否能复现。
- `obs` 和 `actions` 是否正确对齐。
- success / done / terminal 是否被区分。
- 图像是来自源数据还是重新渲染。
- 是否过滤 no-op 或失败轨迹。

LIBERO 的一个常见风险是把 `done` 当成 `success`。在很多环境里，`done` 只表示 episode 结束，可能是成功结束，也可能是超时结束。转换到 LeRobot 时，如果直接把 `done` 写成成功标签，会污染后续评估和过滤逻辑。

## RoboCasa -> LeRobot

RoboCasa 也是仿真数据，但它的重点更偏家庭厨房、桌面环境、资产变化和布局变化。与 LIBERO 相比，RoboCasa 的图像和场景变化可能更复杂，转换时经常涉及 replay 或重新渲染。

重新渲染是一个很容易被忽视的点。它不是简单改变分辨率，而可能改变：

- 相机位置。
- 光照条件。
- 物体可见性。
- 遮挡关系。
- 图像纹理和背景。
- 训练看到的视觉分布。

所以如果 RoboCasa 转换中做了重新渲染，dataset card 必须写清楚：使用的是原始图像还是重新渲染图像，渲染分辨率是多少，相机配置是否改变，是否过滤过 no-op 或失败轨迹。

这类信息会直接影响模型泛化。如果别人以为数据是原始观测，实际用的是重新渲染结果，实验结论就很难复现。

## LeRobot -> RLDS

LeRobot 转 RLDS 的方向和前面相反。它常用于兼容 OpenVLA、Octo 或其它依赖 TFDS / RLDS 的训练栈。

这时最关键的是把 LeRobot 的 frame 序列重新恢复成 RLDS episode / step 结构：

```text
LeRobot:
  episode_index
  frame_index
  observation.images.front
  observation.state
  action
  task

RLDS:
  episode
    step
      observation
      action
      reward
      discount
      is_first
      is_last
      is_terminal
```

转换风险主要集中在 step flags 上：

- 每条 episode 的第一帧要设置 `is_first=True`。
- 每条 episode 的最后一帧要设置 `is_last=True`。
- `is_terminal` 是否为真要根据任务结束语义判断，不能简单等同于 `is_last`。
- 最后一帧如果没有有效 action，不能当作普通监督样本。

这一步和前面的 RLDS 页面直接相关。RLDS 的强项是清晰表达 episode / step 语义，但前提是这些 flags 被正确写入。

## LeRobot 版本互转

Any4LeRobot 提供的另一个重要能力是 LeRobotDataset 版本互转。最常见的是 v2.1 和 v3.0 之间转换。

v2.1 的特点是直观：一条 episode 往往对应一组文件。它适合小规模检查和旧代码兼容。

v3.0 的特点是工程化：多条 episode 可以共享 Parquet 和 MP4 文件，通过 metadata 记录 offset 和边界。它适合大规模数据、Hub 托管和流式读取。

版本互转容易被低估，因为它看起来不像跨生态转换。但实际上一旦文件粒度和 metadata 组织方式变化，就必须重新检查：

- episode 数是否一致。
- 总 frame 数是否一致。
- 每条 episode 的长度是否一致。
- 任务文本是否一致。
- 视频帧和数据行是否对齐。
- stats 是否重算。
- feature schema 是否完全一致。

如果转换后只看 episode 数，很可能漏掉“每条 episode 少一帧”或“视频 offset 错位”这种静默错误。

## 转换后应该怎样验收

一次转换是否合格，不应该只看脚本有没有报错。至少要留下四类证据。

第一类是 schema 证据。包括 `meta/info.json` 里的 feature 名称、dtype、shape、fps、robot type 和 codebase version。

第二类是计数证据。包括源数据和目标数据的 episode 数、frame 数、跳过的 episode 数，以及跳过原因。

第三类是可视化证据。至少抽样查看成功样本、失败样本、最短 episode、最长 episode 和边界条件样本。

第四类是统计证据。包括 `meta/stats.json` 是否重新计算，action / state 的 min、max、mean、std 是否符合常识。

可以用下面的表作为验收清单：

| 检查项 | 合格标准 |
|---|---|
| feature schema | 每个字段 dtype、shape、names 清楚 |
| episode count | 与源数据一致，或有明确过滤记录 |
| frame count | 总帧数和每条 episode 长度可解释 |
| video sync | 抽样图像、状态、动作时间对齐 |
| action semantics | 写清楚控制空间、单位、维度顺序 |
| task metadata | task id、语言、数据来源保留 |
| stats | 转换后重新计算或说明继承依据 |
| dataset card | 写清源数据、工具版本、过滤规则 |

## Conversion report 应该怎么写

正式转换后，应该留下 conversion report。它不需要写成论文，但至少要让后来的人能复现这次转换。

一个最小模板如下：

```yaml
source:
  name: libero_90
  format: hdf5
  source_version: "official_release"
  episodes_before: 9000
  fps: 20

target:
  format: LeRobotDataset v3.0
  repo_id: user/libero_90_lerobot_v3
  robot_type: franka
  action_space: end_effector_delta_pose_7d
  image_features:
    - observation.images.front
    - observation.images.wrist

conversion:
  tool: Any4LeRobot
  tool_version_or_commit: "<填写实际使用的版本或 commit>"
  command_manifest: runs/libero_90_conversion.yaml
  skipped_episodes:
    corrupted_video: 3
    empty_actions: 9
    invalid_length: 5
    no_op_filtered: 120

validation:
  schema_checked: true
  sampled_visualization:
    count: 20
    covered:
      - shortest_episode
      - longest_episode
      - success_case
      - failure_case
  stats_recomputed: true
  train_val_test_split: episode_level
```

这份报告最好和数据集 README 或实验 manifest 放在一起。它的价值在于，当训练结果异常时，你能回头确认到底是源数据问题、转换问题、过滤问题、stats 问题，还是模型问题。

## 初学者最容易犯的错误

**错误一：只看转换后的数据能不能加载。**
能加载只说明目录和文件基本合法，不说明图像、动作、任务和时间是对齐的。

**错误二：把所有数据源都转成同一个 `action` 字段就直接混训。**
字段名统一不等于动作空间统一。尤其是 Open X 和多机器人数据，必须保留 robot type 和 action convention。

**错误三：转换后不重算 stats。**
删除 episode、过滤 no-op、合并数据、改变 action 字段后，旧 stats 往往已经不可靠。

**错误四：没有保存跳过记录。**
如果 9000 条源 episode 变成 8700 条目标 episode，但没有 skip reason，以后很难判断数据是否被合理过滤。

**错误五：转换仿真数据时不记录是否重新渲染。**
重新渲染会改变视觉分布，必须写在数据卡里。

**错误六：版本转换后只看 episode 数。**
v2.1 和 v3.0 的核心差异在 metadata 和 chunk / offset。episode 数一样，不代表视频帧和 action 一定对齐。

## 实践任务

任选一个转换方向，写一份转换计划：

- Open X-Embodiment -> LeRobot
- AgiBot World -> LeRobot
- RoboMIND -> LeRobot
- LIBERO -> LeRobot
- RoboCasa -> LeRobot
- LeRobot -> RLDS
- LeRobot v2.1 -> v3.0

要求至少写出：

1. 源数据格式和目标格式。
2. 三个关键字段映射。
3. action space 的定义。
4. 是否需要视频编码或重新渲染。
5. 哪些 episode 需要过滤。
6. 转换后如何抽样检查。
7. 是否需要重算 stats。
8. conversion report 中要记录哪些内容。

## 自查问题

1. Any4LeRobot 和 LeRobot 本体分别解决什么问题？
2. 为什么转换脚本跑完不等于数据可以训练？
3. Open X-Embodiment 转 LeRobot 时，为什么必须保留 `robot_type` 和 `dataset_source`？
4. LIBERO 或 RoboCasa 转换时，为什么不能把 `done` 简单当作 `success`？
5. LeRobot 转 RLDS 时，`is_last` 和 `is_terminal` 的区别是什么？
6. 为什么 LeRobot v2.1 -> v3.0 属于格式升级，但仍然需要抽样可视化？
7. 什么情况下必须重新计算 `meta/stats.json`？

## 小结

Any4LeRobot 的价值不在于“让你少写几行脚本”，而在于把多来源机器人数据接入 LeRobot 生态的过程变得更统一、更可复用。它能帮助你完成 Open X、AgiBot、RoboMIND、LIBERO、RoboCasa、LeRobot 版本互转以及 LeRobot -> RLDS 等常见路径。

转换质量不能只看脚本是否运行成功，还要看转换后的字段、语义、时间、metadata、stats 和版本记录能不能被审计。只要后面要做真实训练，就应该把转换输出当成一个新的数据集重新检查，再交给模型。
