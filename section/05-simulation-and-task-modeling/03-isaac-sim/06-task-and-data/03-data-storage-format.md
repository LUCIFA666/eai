# 数据存放格式

上一页讲的是“数据应该有什么语义”：step_index、action、robot_state、camera、phase、success、metadata。这一页更具体：这些东西在磁盘上怎么放，文件名怎么起，哪些字段放表里，哪些字段放单独文件，metadata 和 schema 应该写到什么程度。

## 本节目标

本节围绕下面几个问题展开：

1. 主流的数据存放格式有哪些范式，从公开格式里该看什么？
2. 推荐的源数据结构、HDF5 和 schema 该怎么组织？
3. 怎么在不同格式间选择、迁移到训练格式，并写回放脚本读它？

## 先看主流范式

机器人数据格式看起来很多，但底层共识很稳定：**dataset 由许多 episode 组成，episode 由按时间排列的 step 组成，每个 step 至少能对齐 observation 和 action**。差异主要在“怎么落盘”：有人用 Parquet + 视频，有人用 HDF5，有人用 TensorFlow Dataset，有人保留原始 episode 文件夹。

观察几类公开机器人数据集，可以看到它们虽然采用不同容器，但都在围绕 episode、step、observation、action 和 metadata 组织数据：

| 范式 | 公开数据集示例 | 典型结构 | 可借鉴之处 |
|---|---|---|---|
| 表格 + 视频 + metadata | LeRobot PushT | episode 的低维字段放在 Parquet 中，常见列包括 `action`、`timestamp`、`frame_index`、`episode_index`、`task_index`；视觉流单独保存为视频，任务和统计信息放在 `meta/` 下 | 低维数据进表，视觉数据单独存视频 / 图像，靠 frame / episode 索引对齐 |
| episode / step 抽象 | DROID | step 表中同时包含 `is_first`、`is_last`、`is_terminal`、语言指令、`observation.state.*`、`action.*`、`reward`、`timestamp`、`frame_index`、`episode_index` | 每一行就是一个 step；episode 边界、语言指令、observation 和 action 都在同一时间骨架上 |
| HDF5 demonstrations | robomimic | 一条 demonstration 常组织成 `data/demo_0/actions`、`data/demo_0/obs/*`、`data/demo_0/next_obs/*`、`rewards`、`dones` 等数组 | 模仿学习常把一条 demonstration 紧凑封进 HDF5，方便顺序读取 |
| TFRecord / RLDS | RLDS | 数据本体保存为 TFRecord，配套 `features.json` / `dataset_info.json` 描述 observation、action、reward、terminal 等字段 | 抽象上仍是 episode / step，但工程上由 record 文件和 feature schema 管理 |

这些范式给出的启发是：

```text
1. 抽象上遵守 episode / step。
2. 每一帧 / 每一步都要有稳定索引：frame_index、step_index、episode_index。
3. 低维状态和动作适合进表；大体量视觉数据单独存，用路径或索引关联。
4. schema、metadata、episode 边界不是附录，而是数据能被复用的核心。
```

因此，这里不直接照搬某一个数据集格式，而是先用更容易看懂和调试的**源数据格式**采集 Isaac Sim episode；等数据稳定后，再按训练目标转换成 LeRobot / HDF5 / RLDS / WebDataset 这类训练友好的格式。

## 从公开格式中看什么

阅读公开机器人数据集时，不必一开始就理解全部字段。先看四件事：episode 边界在哪里，step 如何编号，observation 和 action 如何对齐，视觉数据和低维状态如何关联。

| 示例 | 最值得看的字段 / 文件 | 读出来的直觉 |
|---|---|---|
| LeRobot PushT | `action`、`observation.state`、`timestamp`、`frame_index`、`episode_index`、视频 MP4 | 训练时常把低维表和视觉流分开存，再靠索引对齐 |
| DROID v3 | `language_instruction`、`observation.state.*`、`action.*`、`is_first` / `is_last` / `is_terminal` | 大规模机器人数据会把语言、状态、动作、终止标记都放进 step 表 |
| robomimic | `data/demo_0/actions`、`obs/*`、`next_obs/*` | 模仿学习常直接读一条 demo 的 action 和 obs 序列 |
| RLDS | `features.json`、`first_record.tfrecord` | schema 先定义清楚，数据本体可以是二进制 record |

这也是 Isaac Sim 源数据里建议保留 HDF5 episode、`dataset/meta/*.jsonl`、`config.yaml` 和 `results/*.json` 的原因：它们分别对应公开数据集里反复出现的几件事——时间索引、字段定义、episode 边界、视觉数据和低维数据对齐。

快速理解一个数据集时，可以用很小的脚本先看字段和 shape：

```python
from pathlib import Path
import pandas as pd
import h5py

root = Path("samples/robot_datasets")

lerobot = pd.read_parquet(
    root / "lerobot/data/chunk-000/episode_000000.parquet"
)
print("LeRobot:", lerobot.shape, list(lerobot.columns))

droid = pd.read_parquet(root / "droid/first_row.parquet")
print("DROID:", droid.shape, list(droid.columns))
print("instruction:", droid.iloc[0]["language_instruction"])

with h5py.File(root / "robomimic/first_demo_only.hdf5", "r") as f:
    demo = f["data/demo_0"]
    print("robomimic actions:", demo["actions"].shape)
    print("robomimic image:", demo["obs/agentview_image"].shape)
```

这段脚本读出来的事实很有代表性：LeRobot 是表 + 视频，DROID 是 step 表里同时放语言 / 状态 / 动作，robomimic 是 HDF5 里的 demo 序列。不同容器背后，抽象仍然是 episode 和 step。

## 推荐源数据结构

这里采用的源数据结构是**一次采集运行一个目录，成功 episode 一个 HDF5 文件，配置、视频、评测结果作为旁路文件保存**。这种结构比“每帧图像散成大量文件”更紧凑，也比直接写成训练平台的 shard 更适合调试：既能单独打开某条 episode，又能从同一个运行目录里找到配置、视频和成功率。

```text
runs/collect/pick_beaker_001/
  config.yaml
  dataset/
    episode_0000.h5
    episode_0001.h5
    meta/
      episode.jsonl
      randomization_episodes.jsonl
      bboxes.jsonl
    _tmp/
  video/
    episode_0000_success.mp4
    episode_0001_fail.mp4
  results/
    episode_0000_success.json
    episode_0001_fail.json
    summary.json
  action_episodes/
    episode_0000_success.json
```

这里有两个要点。第一，`dataset/episode_XXXX.h5` 是训练和回放的主要数据源；课程默认把成功 episode 写入训练清单，失败 episode 可以保留在 `video/`、`results/` 或单独 split 中，用来分析为什么没过，是否参与训练要由 schema 明确标注。第二，`config.yaml`、`results/summary.json` 和 `dataset/meta/*.jsonl` 不是附属品，它们共同回答“这批数据怎么生成、每条 episode 多长、任务是否成功、随机化条件是什么”。

| 位置 | 内容 | 用途 |
|---|---|---|
| `config.yaml` | 本次运行的任务、机器人、相机、采集参数 | 复现采集条件 |
| `dataset/episode_XXXX.h5` | 图像、关节状态、动作、语言指令、物体状态、bbox 等逐帧数组 | 训练和离线回放的主体 |
| `dataset/meta/episode.jsonl` | 每条入库 episode 的索引、长度、任务指令、schema 版本 | 快速扫描数据集 |
| `dataset/meta/randomization_episodes.jsonl` | 每条 episode 的随机化指纹 | 追踪场景变化和采样条件 |
| `dataset/meta/bboxes.jsonl` | 从 HDF5 重建出的 bbox 派生索引 | 给标注检查和轻量工具使用 |
| `video/episode_*.mp4` | 人看的预览视频 | 快速质检，不作为唯一数据源 |
| `results/episode_*.json` | 单条 episode 的步骤级评测结果 | 分析每个 workflow step 是否通过 |
| `results/summary.json` | 本次运行的总体成功率、步骤通过率和明细 | 汇总评测 |
| `action_episodes/` | 可选的动作轨迹 JSON | 调试控制器或复现实验 |

`dataset/_tmp/` 是写入过程中的临时目录。消费数据时只读已经落盘的 `episode_XXXX.h5`，不要把 `_tmp/` 里的中间文件当作有效 episode。

## HDF5

每条入库 episode 被写成一个独立的 HDF5 文件。文件顶层 attrs 记录 schema 和基本状态，顶层 datasets 记录逐帧数据。一个典型文件可以这样理解：

```text
episode_0000.h5
  attrs:
    schema_version = "1.6"
    episode_success = true
    episode_name = "episode_0000"
    robot_type = "ur5e"
  datasets:
    actions
    agent_pose
    step_index
    phase_index
    language_instruction
    camera_1_rgb
    camera_2_rgb
    object_names
    object_positions
    object_orientations
    bboxes_2d
    bbox_visibility
    bbox_camera_names
    object_local_aabb_extents
```

| 字段 | 常见 shape | 说明 |
|---|---|---|
| `agent_pose` | `(T, num_dof)` | 每帧机器人关节状态 |
| `actions` | `(T, action_dim)` | 与 observation 对齐的动作；它是关节目标、末端位姿还是增量命令，必须由 schema 定义 |
| `step_index` | `(T,)` | 逐帧时间索引，从 0 连续递增，是对齐所有数据的主键 |
| `phase_index` | `(T,)` | 当前帧属于任务流程的第几个阶段，`-1` 表示过渡帧 |
| `language_instruction` | 标量字符串 | 这条 episode 对应的自然语言任务描述 |
| `camera_1_rgb`、`camera_2_rgb` | `(T, 3, H, W)` 或 JPEG 变长字节 | 多相机 RGB 流；本页示例把 raw RGB 约定为 channel-first |
| `object_names` | `(K,)` | 物体轴的稳定顺序 |
| `object_positions` | `(T, K, 3)` | 关键物体世界坐标；本页示例单位为 meter |
| `object_orientations` | `(T, K, 4)` | 关键物体朝向；本页示例可约定为 `xyzw`，实际顺序必须写进 schema |
| `bboxes_2d` | `(T, K, num_cams, 4)` | 每帧、每物体、每相机的 2D bbox，缺失可用 `NaN` |
| `bbox_visibility` | `(T, K, num_cams)` | bbox 可见性，`0` 表示不可见或遮挡，`1` 表示可见 |
| `bbox_camera_names` | `(num_cams,)` | bbox 第三维对应的相机名顺序 |
| `object_local_aabb_extents` | `(K, 3)` | 物体本地 AABB 尺寸，可用于 3D box 或几何检查 |

后续 schema 版本可以继续增加 `annotations/...` 这类分组字段。读数据时不要只依赖固定版本号，应该先检查 dataset 是否存在，再决定是否启用对应能力。

## metadata

HDF5 负责保存密集数组，旁路 metadata 负责保存索引、配置和评测。这样的分工比把所有信息塞进一个大文件更利于人工检查。

`dataset/meta/episode.jsonl` 的一行可以包含：

```json
{
  "episode_index": 0,
  "tasks": [
    "Rotate the base 90 degrees to the left workspace, pick up the beaker..."
  ],
  "length": 1909,
  "success": true,
  "schema_version": "1.6",
  "robot_type": "ur5e"
}
```

`results/episode_0000_success.json` 保存的是任务步骤级结果，例如每个 workflow step 的 skill、target、success、reason 和 debug metrics。`results/summary.json` 则汇总本次运行的 episode 成功率和 step 通过率。这样拆开之后，训练脚本可以只读 `dataset/`，质检脚本可以先扫 `results/` 和 `video/`，复现实验时再回到 `config.yaml`。

随机化信息建议放在 `dataset/meta/randomization_episodes.jsonl`。只存 seed 不够，因为代码、资产列表或采样顺序一变，同一个 seed 也可能采出不同场景；更稳妥的做法是记录这条 episode 实际采到的参数或随机化指纹。

## schema

HDF5 顶层 attrs 中的 `schema_version` 是最基本的版本标记。随着采集格式演化，可以把字段含义固定成清晰的约定：

| 约定 | 推荐写清楚的内容 |
|---|---|
| 时间对齐 | `agent_pose[t]`、`camera_rgb[t]` 和 `actions[t]` 的对应关系 |
| 图像布局 | raw RGB 是 `CHW` 还是 `HWC`，JPEG 字节如何解码 |
| 坐标单位 | 位置单位是 meter，角度单位是 radian |
| 四元数顺序 | Isaac Sim / USD 常见接口可能不同，数据内应明确 `xyzw` 或 `wxyz` |
| action 语义 | 绝对关节目标、关节增量、末端位姿目标或夹爪命令 |
| 成功过滤 | 失败 episode 是否进入 HDF5，还是只保留 video / results |

如果没有 schema，训练脚本只能靠字段名猜：`q` 是关节位置还是广义坐标？四元数是 `xyzw` 还是 `wxyz`？action 是绝对目标还是增量？这些猜错一次，训练结果就可能整批废掉。

## 格式怎么选

不同规模下可以选不同容器：

| 格式 | 适合 | 优点 | 注意 |
|---|---|---|---|
| HDF5 + JSONL / MP4 旁路 | Isaac Sim 源数据 | 一条入库 episode 一个文件，数组紧凑，metadata 可单独扫描 | 并发写入要使用临时文件和原子 rename |
| 文件夹 + PNG / NPY / JSONL | 入门、小数据、教学演示 | 直观、容易 debug、无需重工具 | 文件数量多时管理成本高 |
| Parquet + 外部图像文件 | 中等规模 episode 数据 | 表字段好筛选，和 Python 数据栈兼容 | 图像仍建议外置 |
| Zarr | 大规模数组、云端 / 分块读取 | chunk 友好，适合大数据 | 初学者理解成本略高 |
| WebDataset / tar shards | 大规模视觉训练 | 训练吞吐好 | 更像训练格式，不适合第一版采集源数据 |

建议顺序是：**先用 HDF5 + JSONL / MP4 旁路保存可回放的源数据，再按训练需要转换成 LeRobot / robomimic / RLDS / Zarr / WebDataset**。采集源数据追求自描述和可审计，训练格式追求吞吐和批处理效率，两者不一定是同一个格式。

## 怎么迁移到训练格式

源数据格式和主流格式之间的关系可以这样理解：

| 目标格式 | 转换方式 | 适合场景 |
|---|---|---|
| LeRobot | 读取 `dataset/episode_XXXX.h5`，把低维数组转成 Parquet，把相机序列编码成 MP4，写 metadata、episode 边界和统计量 | VLA / imitation learning 训练，想接 Hugging Face 数据生态 |
| RLDS | 把每个 HDF5 episode 展开成 steps，每个 step 写 `observation`、`action`、`is_first`、`is_last`、`is_terminal` | 想和 Open X-Embodiment / TFDS 风格数据对齐 |
| robomimic HDF5 | 把每条 episode 映射成 `data/demo_i`，下面放 `actions`、`obs/*`、`next_obs/*`、`rewards` | 经典模仿学习 pipeline，顺序读取 demonstrations |
| WebDataset | 把图像、低维状态和 label 打成 tar shard | 大规模视觉训练，追求吞吐 |

这就是为什么源数据里要保留 `config.yaml`、`episode.jsonl`、`schema_version`、相机名、物体名和评测结果：转换脚本需要知道每个字段的含义、形状、单位和时间对齐方式。源数据越清楚，后处理越不容易变成猜谜。

## 回放脚本应该怎么读

一个合格的数据格式，应该能被一个很小的回放脚本读懂：

```python
from pathlib import Path
import json
import h5py
import numpy as np

run_dir = Path("runs/collect/pick_beaker_001")
episode_path = run_dir / "dataset/episode_0000.h5"
episode_meta = [
    json.loads(line)
    for line in (run_dir / "dataset/meta/episode.jsonl").read_text().splitlines()
]

with h5py.File(episode_path, "r") as f:
    print(dict(f.attrs))
    rgb_chw = f["camera_1_rgb"][0]
    rgb_hwc = np.transpose(rgb_chw, (1, 2, 0))
    joint = f["agent_pose"][0]
    action = f["actions"][0]
    step_index = f["step_index"][0]
```

这段脚本不需要 Isaac Sim，也不需要重新跑物理。它只验证一件事：数据本身是否能按 step 读取。如果离开仿真运行时就读不懂，那说明采集格式和后处理绑得太死。

## 小结

- 主流机器人数据集的共同抽象是 dataset / episode / step；不同项目只是在落盘容器上选择不同取舍。
- Isaac Sim 源数据采用“一次采集运行一个目录，入库 episode 一个 HDF5 文件”的结构。
- `dataset/episode_XXXX.h5` 保存密集逐帧数组，`dataset/meta/*.jsonl` 保存 episode 索引和随机化信息。
- `video/` 和 `results/` 服务人工质检和评测分析，不能替代 HDF5 中的结构化数据。
- 源数据格式优先自描述、可回放、可审计；训练格式可以后处理转换。

## 参考资料

- Hugging Face LeRobot Documentation, [LeRobotDataset v3.0](https://huggingface.co/docs/lerobot/main/lerobot-dataset-v3)
- Google Research, [RLDS Dataset Format](https://github.com/google-research/rlds)
- robomimic Documentation, [Datasets Overview](https://robomimic.github.io/docs/v0.2/datasets/overview.html)
- DROID Documentation, [The DROID Dataset](https://droid-dataset.github.io/droid/the-droid-dataset)

## 导航

- 返回目录：[任务、数据采集与合成数据](../06-task-and-data.md)
- 上一页：[数据采集、回放与质检](02-data-collection.md)
- 下一页：[headless 批量与可复现](04-headless-and-repro.md)
