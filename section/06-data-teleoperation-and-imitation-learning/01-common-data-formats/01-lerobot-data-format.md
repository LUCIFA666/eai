# LeRobot 数据格式

目标：读懂 LeRobot 数据集的目录、metadata、stats、episode 索引和 v2/v3 差异，并知道迁移或转换时必须检查哪些语义。

LeRobotDataset 是 Hugging Face LeRobot 生态里用来保存机器人学习数据的标准格式。它关心的不只是“把图片和动作存下来”，还要让一批机器人轨迹能够稳定地读取、可视化、回放、清洗、切分、共享，并最终进入模仿学习或 VLA 训练流程。

可以先把 LeRobotDataset 看成一个面向机器人数据的工程化文件夹。它把图像、动作、状态、任务文本、episode 边界和统计量分别放在合适的位置，而不是把所有东西塞进一个不可读的大文件里。这样做的好处是：训练代码能知道每一帧对应哪条 episode，可视化工具能知道该读取哪一路相机，清洗工具能知道删掉某条轨迹后哪些 metadata 也要同步更新。

本节只讲数据格式，不讲 policy 训练。训练策略、损失函数和真机部署会放到后续章节；这里关注的是：一份 LeRobot 数据集长什么样，v2 和 v3 为什么不同，`meta/info.json`、`meta/stats.json`、任务表和 `meta/episodes/` 分别负责什么，以及拿到一份数据后应该先检查什么。

## 阅读目标

读完这一页，可以用下面几个问题检查自己是否读懂：

1. LeRobot 软件版本和 LeRobotDataset 格式版本为什么不是一回事。
2. 一条机器人 episode 在 LeRobot 里会被拆成哪些信息：低维数据、视频、任务、统计量和 episode metadata。
3. LeRobotDataset v2 为什么直观，v3 为什么更适合大规模数据。
4. `meta/info.json` 里哪些字段最重要，为什么不能只看 `action` 的 shape。
5. `meta/stats.json` 为什么会影响训练和部署，而不是一个可有可无的附属文件。
6. 从 v2 迁移到 v3，或者从其他格式转成 LeRobot 时，最容易损坏哪些信息。

## 先区分两个版本号

学习 LeRobotDataset 时，第一个容易混淆的点是“软件版本”和“数据格式版本”。

| 名称 | 例子 | 说明 |
|---|---|---|
| LeRobot 软件版本 | `0.5.2` | 代码库、命令行工具、数据读取器、训练脚本的版本 |
| LeRobotDataset 格式版本 | `v2.1`、`v3.0` | 数据目录结构、metadata 组织方式、文件分片规则的版本 |

这两个版本号不是同一个东西。一个新的 LeRobot 软件版本，可能仍然能读取旧格式数据；一份旧格式数据，也可能需要迁移到新格式，才能被新的读取器高效使用。

可以用一个更熟悉的类比来理解：Word 软件有版本，`.docx` 文件格式也有版本。你不能只说“我装了新版 Word”，就默认所有旧文档都没有兼容问题。LeRobot 也是一样：你既要知道当前项目使用哪个 LeRobot 代码版本，也要知道手里的数据集本身是 v2.1、v3.0，还是某个转换脚本写出的变体。

在数据卡或实验记录中，建议同时写清楚：

```yaml
software:
  lerobot_version: "0.5.2"
dataset:
  dataset_format: "LeRobotDataset v3.0"
  converted_from: "v2.1"
  conversion_tool: "..."
```

这不是为了形式完整，而是为了后续复现。半年后如果有人发现同一份数据在新代码里读取变慢、episode 数对不上，第一步就要回到这里确认：到底是软件版本变化，还是数据格式本身发生了迁移。

## 一条 LeRobot episode 里有什么

在普通图像分类任务里，数据通常是“图片 + 标签”。机器人数据要复杂得多。一条 episode 是一次完整任务轨迹，它不是一个独立样本，而是一段连续时间序列。

以“把方块拿起来放进盒子”为例，一条 episode 可能包含：

```text
episode_000001
  frame 0:
    observation.images.front
    observation.images.wrist
    observation.state
    action
    timestamp
    task
  frame 1:
    observation.images.front
    observation.images.wrist
    observation.state
    action
    timestamp
    task
  ...
  episode metadata:
    episode_index
    length
    task_index
    data file location
    video file location
    start / end offset
```

这里有几个层次要分开看：

| 层次 | 例子 | 作用 |
|---|---|---|
| 帧级数据 | 图像、状态、动作、时间戳 | 训练时直接读取，用来构造 `observation -> action` 样本 |
| episode 级数据 | 长度、任务 id、起止 offset | 告诉读取器一条轨迹从哪里开始，到哪里结束 |
| 数据集级 metadata | feature schema、fps、路径模板 | 告诉读取器每个字段长什么样、在哪里找 |
| 统计量 | mean、std、min、max | 用于训练归一化和部署反归一化 |
| 任务表 | task id 到 task text 的映射 | 让语言任务和 episode 对齐 |

所以，LeRobotDataset 不是一个“视频文件夹”，也不是一个“Parquet 表格”。它是由 `meta/`、`data/`、`videos/` 共同组成的数据系统。

## 一个 LeRobot 数据集的基本骨架

无论 v2 还是 v3，LeRobot 数据通常都围绕三个目录展开：

```text
dataset_root/
  meta/
  data/
  videos/
```

这三个目录可以这样理解：

```text
meta/    说明书：字段定义、任务表、统计量、episode 边界
data/    低维表格：状态、动作、时间戳、索引等
videos/  高维视觉：各相机的视频帧
```

这种拆分非常重要。机器人数据里既有高维图像，也有低维状态和动作。如果全部放进一个数组文件，读取和审计会很不方便；如果每帧都拆成图片和 JSON，又会产生大量小文件。LeRobot 的设计思路是：低维时序数据用 Parquet，视觉数据用 MP4，组织关系用 metadata 记录。

从训练代码的角度看，它不是直接“遍历 videos 文件夹”，而是先读 `meta/info.json` 和 episode metadata，知道有哪些 feature、每条 episode 的范围和视频位置，再按需要取出对应帧。

## v2 系列：一条 episode 一组文件

LeRobotDataset v2 系列更符合初学者直觉。它常见的组织方式是：每条 episode 有自己的 Parquet 文件和视频文件。

```text
dataset/
  meta/
    info.json
    stats.json
    tasks.jsonl
    episodes.jsonl
  data/
    chunk-000/
      episode_000000.parquet
      episode_000001.parquet
      episode_000002.parquet
  videos/
    chunk-000/
      observation.images.front/
        episode_000000.mp4
        episode_000001.mp4
        episode_000002.mp4
      observation.images.wrist/
        episode_000000.mp4
        episode_000001.mp4
        episode_000002.mp4
```

打开这个目录时，你会很容易理解：

```text
episode_000001.parquet
episode_000001.mp4
```

它们属于同一条轨迹。要单独检查某条 episode，也可以直接找到对应文件。这对教学、小规模采集、手工调试很友好。

### v2 的优点

v2 最主要的优点是直观：

- 文件名直接对应 episode，容易定位。
- 单条 episode 可以单独复制、删除或检查。
- 很多早期脚本默认按 episode 文件读取。
- 初学者更容易把数据结构和真实任务轨迹对应起来。

如果你只有几十条或几百条 episode，v2 的这种直观性很有价值。你可以把某条出错轨迹的 Parquet 和视频单独拿出来检查，不需要先理解 chunk、offset 和共享文件。

### v2 的问题

v2 的问题会在规模变大后出现。假设一个数据集有 10 万条 episode，每条 episode 有两个相机，那么光视频文件就可能有 20 万个，再加上 Parquet、metadata 和缓存文件，文件系统压力会很大。

常见问题包括：

- 文件数量爆炸，目录扫描变慢。
- 远程对象存储和 Hub 缓存效率下降。
- 训练启动前需要扫描大量小文件。
- 随机访问时 I/O 调度不稳定。
- 数据集迁移和版本管理成本升高。

所以 v2 并不是“差”，而是它更适合小规模和直观检查；当数据走向大规模训练时，就需要另一种组织方式。

## v3 系列：多条 episode 合并成共享文件

LeRobotDataset v3.0 的核心变化是 file-based storage：不再默认一条 episode 一个文件，而是把多条 episode 的低维数据合并到共享 Parquet 文件，把多条 episode 的视频帧合并到共享 MP4 文件，然后通过 metadata 记录每条 episode 的位置。

典型 v3 结构可以理解成：

```text
dataset/
  meta/
    info.json
    stats.json
    tasks.parquet
    episodes/
      chunk-000/
        file-000.parquet
  data/
    chunk-000/
      file-000.parquet
      file-001.parquet
  videos/
    observation.images.front/
      chunk-000/
        file-000.mp4
    observation.images.wrist/
      chunk-000/
        file-000.mp4
```

这里最关键的一点是：`data/chunk-000/file-000.parquet` 不再等于某一条 episode。它可能包含很多条 episode 的 frame。视频文件也是一样，`videos/observation.images.front/chunk-000/file-000.mp4` 可能连续存了多条 episode 的图像帧。

那么读取器怎么知道 episode 3 从哪里开始、到哪里结束？

答案是 metadata，尤其是 `meta/episodes/`。

一个简化的 episode metadata 可以理解成：

```text
episode_index: 3
length: 142
task_index: 0
data_path: data/chunk-000/file-000.parquet
video_path:
  observation.images.front: videos/observation.images.front/chunk-000/file-000.mp4
  observation.images.wrist: videos/observation.images.wrist/chunk-000/file-000.mp4
start_offset: ...
end_offset: ...
```

也就是说，v3 把 episode 从“文件名里的自然单位”变成了“metadata 里的逻辑单位”。

### 为什么 v3 更适合大规模数据

v3 的优势来自减少小文件数量和增强远程读取能力：

- 多条 episode 合并后，文件数量大幅减少。
- 数据初始化时不需要扫描海量 episode 文件。
- 在 Hugging Face Hub 等远程托管场景下更适合缓存和 streaming。
- 训练读取器可以根据 metadata 定位片段，不必先下载完整数据集。
- 对上万到百万级 episode 更友好。

这也是 v3 从“方便手工查看的小数据格式”走向“大规模训练和 Hub 流式读取格式”的原因。

### v3 的代价

v3 的代价是可读性下降。你不能再通过“删除一个 episode 文件”来删除一条轨迹，因为这条 episode 可能只是某个大 Parquet 或 MP4 文件中的一段。

如果要删除、切分、合并、重编码或迁移，就必须让这些部分同步更新：

```text
meta/
data/
videos/
stats
```

这也是为什么 v3 更依赖官方工具或可靠转换脚本。手工移动文件很容易造成数据还在，但 metadata 已经指错位置；或者视频还在，但 episode offset 不匹配。

## v2 和 v3 到底怎么选

可以把 v2 和 v3 的差别总结成下面这张表：

| 维度 | v2 / v2.1 | v3.0 |
|---|---|---|
| 组织粒度 | 通常一条 episode 一组文件 | 多条 episode 合并到共享文件 |
| 低维数据 | Parquet | Parquet |
| 视觉数据 | MP4，常按 episode 分文件 | MP4，常按 chunk / file 分组 |
| episode 定位 | 主要靠文件名和列表 | 依赖 metadata 中的路径与 offset |
| 手工检查 | 非常直观 | 需要工具辅助 |
| 小规模教学 | 友好 | 也能用，但不如 v2 直观 |
| 大规模训练 | 小文件压力较大 | 更适合 |
| Hub / streaming | 不如 v3 稳定 | 更适合 |
| 数据清洗 | 单条 episode 容易定位 | 需要同步更新 metadata |
| 典型用途 | 旧脚本、小实验、转换源 | 新数据目标、大规模维护 |

实际选择时可以这样判断：

```text
只是课程小实验，episode 很少?
  -> v2 更容易看懂；v3 也可以，但要依赖工具。

想做长期维护、共享和训练?
  -> 优先 v3。

旧训练脚本只支持 v2.1?
  -> 保留 v2.1，或从 v3 导出 v2.1。

要上传 Hub、做 streaming 或大规模混合?
  -> 优先 v3。
```

v2 和 v3 不是“低级”和“高级”的关系，而是面向不同工程约束。v2 适合看清楚一条轨迹，v3 适合管理很多轨迹。

## `meta/info.json`：先读这个，再训练

拿到一份 LeRobot 数据集，第一件事不应该是直接训练，而是打开：

```text
meta/info.json
```

它相当于数据集的说明书，告诉你：

- 数据集格式版本是什么。
- 机器人类型是什么。
- FPS 是多少。
- 有哪些 feature。
- 每个 feature 的 dtype、shape、names 是什么。
- 视频 feature 的分辨率、通道和编码信息是什么。
- 路径模板和数据组织方式是什么。

一个简化例子如下：

```json
{
  "codebase_version": "v3.0",
  "robot_type": "franka",
  "fps": 30,
  "features": {
    "observation.images.front": {
      "dtype": "video",
      "shape": [480, 640, 3],
      "names": ["height", "width", "rgb"]
    },
    "observation.state": {
      "dtype": "float32",
      "shape": [8],
      "names": {
        "motors": ["x", "y", "z", "roll", "pitch", "yaw", "gripper", "mode"]
      }
    },
    "action": {
      "dtype": "float32",
      "shape": [7],
      "names": {
        "motors": ["x", "y", "z", "roll", "pitch", "yaw", "gripper"]
      }
    }
  }
}
```

这段 JSON 里，最重要的不是 `shape`，而是 `names` 和语义。

很多初学者会看到：

```text
action shape = [7]
```

然后就以为这是标准的 7 维机械臂动作。但这很危险。7 维可能表示：

```text
[x, y, z, roll, pitch, yaw, gripper]
```

也可能表示：

```text
[joint_1, joint_2, joint_3, joint_4, joint_5, joint_6, joint_7]
```

还可能是归一化后的控制命令。shape 一样，不代表语义一样。真正决定模型输出该怎么解释的，是 `names`、单位、action convention 和控制接口。

训练前至少要确认：

| 字段 | 必须确认什么 |
|---|---|
| `robot_type` | 这批数据来自什么机器人 |
| `fps` | observation 和 action 按什么频率记录 |
| `observation.images.*` | 相机位置、分辨率、颜色通道 |
| `observation.state` | 每一维状态分别是什么 |
| `action` | 是关节位置、末端增量、速度、力矩，还是归一化动作 |
| `task` / `task_index` | 任务文本是否能恢复 |
| `codebase_version` | 数据格式版本是否和读取工具匹配 |

`info.json` 看不懂时，直接训练通常是在赌。模型可能能跑起来，但它学到的动作含义未必是你以为的那一个。

## `meta/tasks.*`：任务文本不是随便附上的字符串

LeRobot 数据里，任务文本通常不会简单地重复写在每一帧里，而是通过 task id 关联。不同版本或迁移阶段可能会看到 `meta/tasks.jsonl` 或 `meta/tasks.parquet`；核心不在文件后缀，而在“任务文本表”和 episode/frame 中的 `task_index` 必须一致。

可以理解成：

```text
meta/tasks.*
  task_index: 0
  task: "Pick up the cube and place it in the box"

episode metadata
  episode_index: 12
  task_index: 0
```

这样做有两个好处：

1. 同一个任务文本不用在每一帧重复保存。
2. 任务文本和 episode 的关系更容易审计。

但这也带来一个风险：迁移、合并或修改任务文本时，不能只改某个地方。比如合并两个数据集时，如果两个任务都叫 `task_index = 0`，但实际文本不同，就必须重新整理任务表和索引，否则训练时语言条件会错位。

如果你的模型使用语言指令，检查任务表就非常重要。任务文本错了，模型会把错误语言和动作轨迹配对，训练损失可能照样下降，但语言 grounding 会变差。

## `meta/episodes/`：v3 如何找回一条轨迹

在 v2 中，一条 episode 往往对应一个文件，边界很直观。在 v3 中，episode 边界主要靠 `meta/episodes/` 记录。

它通常负责回答：

- 这条 episode 有多长。
- 它属于哪个 task。
- 它的低维数据在哪个 Parquet 文件里。
- 每个 video feature 对应哪个 MP4 文件。
- 这条 episode 在共享文件中的起止位置。
- 视频中的起止时间或帧偏移是多少。

可以用下面这张逻辑图来理解：

```text
meta/episodes/
  episode_000012
      |
      |-- data path + row offset
      v
data/chunk-000/file-000.parquet
      |
      |-- video path + time/frame offset
      v
videos/observation.images.front/chunk-000/file-000.mp4
```

所以在 v3 中，“一条 episode”不是某一个物理文件，而是 metadata 指向的一段连续数据。读取器按照这些指针，把 `data/` 和 `videos/` 中的片段重新拼成训练样本。

这也是为什么 v3 不能随便手工改目录。只要 metadata 中的 offset 或路径错了，就会出现非常隐蔽的问题：数据能打开，但图像和动作不是同一条轨迹，或者 episode 长度被截断。

## `meta/stats.json`：它会改变模型看到的数值尺度

`meta/stats.json` 保存每个数值 feature 的统计量，例如：

```text
mean
std
min
max
```

它常用于训练时的 normalizer，也用于部署时把模型输出反归一化。

比如真实动作范围是：

```text
action x: [-0.05, 0.05]
```

训练时可能被归一化到比较稳定的数值范围。模型预测的是归一化后的动作，部署时需要用同一套 stats 转回真实动作尺度。

`stats.json` 不是附属文件，它会进入训练和部署闭环。

常见事故包括：

- 删除坏 episode 后没有重算 stats。
- 合并多个数据集后仍使用其中一个数据集的 stats。
- action 维度顺序变了，但 stats 仍来自旧 schema。
- 某个 camera 或 state 字段被删除，stats 里还残留旧字段。
- 训练和 rollout 使用了不同版本的 stats。

这些错误不一定会让程序报错。最危险的情况是：模型能正常输出动作，但动作尺度错了。

举个例子，模型以为 `action[0]` 是归一化到 `[-1, 1]` 的末端 x 方向增量，真实机器人接口却把它解释为米级位置目标。此时系统可能不会在读取数据阶段报错，但真机执行会出现明显异常。

所以只要做过下面任一操作，就应该重新计算或至少严格确认 stats：

```text
删除 episode
合并数据集
修改 action/state 字段
改变 train/val/test split
迁移格式
从 HDF5/RLDS 转成 LeRobot
重编码或删除视觉 feature
```

## 一帧数据在训练时长什么样

理解完 `meta/` 后，再看训练读取器返回的样本会更清楚。一个 frame 样本通常可以抽象成：

```python
sample = {
    "observation.images.front": image_tensor,
    "observation.images.wrist": image_tensor,
    "observation.state": state_tensor,
    "action": action_tensor,
    "timestamp": timestamp,
    "episode_index": episode_index,
    "frame_index": frame_index,
    "task": "Pick up the cube and place it in the box"
}
```

不同数据集字段会不同，但核心思想类似：每个样本都是从一条 episode 中取出的某个时间步，包含视觉、状态、动作、时间和任务信息。

如果训练的是行为克隆，最基本的监督关系是：

```text
当前 observation  ->  当前 action
```

如果做 diffusion policy 或 sequence policy，读取器可能会取一个时间窗口：

```text
过去若干帧 observation  ->  未来若干帧 action
```

这时 episode 边界尤其重要。窗口不能跨过 episode 结尾，否则模型会把上一条任务的最后几帧和下一条任务的开头拼在一起。

## 为什么视频要单独存成 MP4

机器人数据里，图像通常是最大头。假设一条 episode 60 秒，30 FPS，一个相机就有 1800 帧。如果有两个相机，就是 3600 张图。把每帧都存成单独图片，会产生大量小文件；把每帧都直接放进 Parquet，也会让表格变得过大。

LeRobot 通常把图像序列编码成视频，原因是：

- 存储效率更高。
- 文件数量更少。
- 按相机组织更清晰。
- 适合远程托管和流式读取。
- 训练时可以通过解码器按需取帧。

但视频编码也有代价：

- 压缩可能改变像素。
- RGB / YUV 色彩空间转换可能带来差异。
- 某些 codec 在不同机器上兼容性不同。
- 随机访问依赖关键帧和解码器。
- 重编码可能造成掉帧或时间戳漂移。

所以，如果你做的是对视觉细节很敏感的任务，比如细小物体抓取、透明物体操作、按钮按压等，最好抽样检查视频解码后的画面。训练读到的是解码后的图像，不一定等同于相机原始帧。

## 迁移到 v3 时不是简单移动文件

从 v2.1 迁移到 v3.0，看起来像是把文件从“每条 episode 一个文件”变成“多条 episode 合成一个 chunk”。但实际迁移要处理四类内容：

```text
文件组织变化
metadata 结构变化
episode 边界重建
stats 和 task 信息更新
```

迁移后至少检查：

| 检查项 | 通过标准 |
|---|---|
| episode count | 迁移前后 episode 数一致，或有明确过滤日志 |
| frame count | 总帧数一致，或有明确丢弃原因 |
| episode length | 每条 episode 长度一致 |
| feature schema | dtype、shape、names 没有意外变化 |
| task mapping | 每条 episode 的任务文本能正确恢复 |
| video sync | 视频帧和 action/state 时间对齐 |
| stats | 已重算，或有明确继承依据 |
| random replay | 抽样 episode 可视化或回放正常 |

建议至少抽样检查以下几类 episode：

```text
最短 episode
最长 episode
第一条 episode
最后一条 episode
一个成功样本
一个失败或边界样本
```

只检查 episode 总数是不够的。一个常见静默错误是：总 episode 数没变，但每条 episode 少了最后一帧；或者视频帧数对了，但视频和 action 差了一帧。

## 和其他格式转换时要特别小心什么

LeRobot 常作为目标格式，也常作为中间格式。比如：

```text
HDF5 -> LeRobot
RLDS -> LeRobot
LeRobot v2 -> LeRobot v3
LeRobot -> RLDS
```

每种转换都有自己的风险。

### HDF5 -> LeRobot

HDF5 里常见 `obs`、`next_obs`、`actions`。转成 LeRobot 时要确认：

```text
当前 observation 是否对应当前 action
next_obs 有没有被误用
图像是 RGB 还是 BGR
gripper 是开合宽度还是二值命令
done 是否等于 success
```

如果 `obs/action` 对齐错了，训练脚本可能照样跑，但监督关系已经错了。

### RLDS -> LeRobot

RLDS 强调 episode/step 和 `is_first`、`is_last`、`is_terminal`。转 LeRobot 时要确认：

```text
episode 边界是否保留
最后一帧是否有有效 action
terminal 和 timeout 是否区分
language instruction 是否映射到 task
```

特别是最后一帧。很多 RLDS 数据中最后一帧只是 terminal observation，不一定有可监督 action。不能直接当成普通训练样本。

### LeRobot -> RLDS

反向转换时，要把 LeRobot 的 `episode_index`、`frame_index`、task 和 feature 重新组织成 RLDS episode/step 结构。这里最容易丢的是：

```text
is_first
is_last
is_terminal
discount
reward
dataset_source
```

如果后续要接 OpenVLA、Octo 或 Open X 风格训练栈，这些字段不能随便丢。

## 常见易错点

下面这些问题在初学者使用 LeRobotDataset 时很常见：

- **只看action.shape，不看 action 语义**：shape 一样不代表动作空间一样。
- **把 LeRobot 软件版本当成数据格式版本**：代码版本和数据 layout 是两件事。
- **手工删除 v3 里的某个文件**：可能破坏共享文件和 metadata 的对应关系。
- **清洗后不重算 stats**：训练不一定报错，但动作尺度可能错。
- **合并数据集只看字段名一致**：同名字段可能来自不同机器人或不同单位。
- **视频能播放就认为没问题**：还要检查帧数、时间戳、相机 key 和 action 对齐。
- **按 frame 切 train/val/test**：相邻帧高度相似，会造成数据泄漏。
- **只保存数据，不保存转换记录**：后面无法判断数据来源、格式版本和清洗规则。
- **把 task 当成装饰字段**：语言条件模型中，task 错位会直接影响训练目标。
- **录制或转换后没有正确 finalize**：v3 会增量写入 Parquet 和 metadata，结束前没有正确收尾可能导致文件不完整或无法稳定加载。
- **从 v2 到 v3 只看 episode 数**：还要看 frame count、length、video sync 和 stats。

## 一个最小检查流程

拿到一份 LeRobot 数据集后，可以按下面顺序检查：

```text
1. 打开 meta/info.json
   -> 看格式版本、robot_type、fps、features、action names

2. 打开任务表，例如 meta/tasks.parquet 或 meta/tasks.jsonl
   -> 看任务文本是否合理，task_index 是否唯一且能和 episode 对上

3. 查看 meta/episodes/
   -> 看 episode 数、length 分布、路径和 offset 是否完整

4. 抽样读取 data/
   -> 看 action/state 是否有 NaN、Inf、异常范围

5. 抽样解码 videos/
   -> 看相机是否正确、颜色是否正常、帧数是否对齐

6. 检查 meta/stats.json
   -> 看是否和当前数据字段一致，清洗后是否重算

7. 抽样可视化或 replay
   -> 看图像、状态、动作和任务是否真的对齐

8. 记录 dataset card / manifest
   -> 写清来源、版本、清洗规则、split 和 stats 状态
```

这套流程不复杂，但能帮你避免很多“训练才发现数据坏了”的问题。

## 小结

LeRobotDataset 的核心价值，是把机器人轨迹从“零散文件”组织成一个可训练、可视化、可共享、可审计的数据集。v2 和 v3 的差别，本质上是数据规模和工程约束不同：v2 更直观，适合小规模检查和旧脚本；v3 更工程化，适合大规模、Hub 托管和流式读取。

实际使用 LeRobot 数据时，最重要的不是记住目录名，而是理解每一层在保护什么信息：

```text
info.json     保护 feature schema 和数据含义
tasks.*       保护任务文本和 task id 映射
episodes      保护 episode 边界和共享文件 offset
data          保存低维状态、动作、时间戳
videos        保存高维视觉观测
stats         保存训练和部署需要的数值尺度
```

只要你做了转换、清洗、合并、切分或迁移，就要把这些部分作为一个整体重新检查。LeRobotDataset 让机器人数据更标准化，但它不会自动替你保证 action 语义、时间对齐和任务标签都正确。

## 实践任务

找一份 LeRobot 数据集，完成一次最小审计：

1. 读取 `meta/info.json`，列出所有 feature 的 dtype、shape 和 names。
2. 判断数据集是 v2.1 还是 v3.0。
3. 随机选 3 条 episode，记录它们的 length、task 和视频 feature。
4. 检查 `action` 每一维的含义，说明它是关节空间、末端空间还是其他控制形式。
5. 检查 `meta/stats.json` 是否覆盖当前所有数值 feature。
6. 写一段迁移风险说明：如果把这份数据转成另一种格式，最可能丢什么信息。

## 自查问题

1. LeRobot 软件版本和 LeRobotDataset 格式版本有什么区别？
2. v2 为什么适合手工检查？v3 为什么适合大规模训练？
3. v3 中一条 episode 为什么不能简单等同于一个文件？
4. `meta/info.json` 里为什么不能只看 `shape`，还要看 `names` 和语义？
5. `meta/stats.json` 为什么会影响真机部署时的动作尺度？
6. 从 HDF5 转 LeRobot 时，`obs` 和 `next_obs` 为什么容易导致时间错位？
7. 从 RLDS 转 LeRobot 时，最后一帧为什么需要特别检查？
8. 为什么 train/val/test 不应该按 frame 随机切分？
