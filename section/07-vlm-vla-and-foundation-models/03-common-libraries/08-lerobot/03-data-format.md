# 8.5.2.3 LeRobot数据格式及转换


LeRobotDataset 是 HuggingFace LeRobot 使用的机器人数据格式，目前存在两个版本：v2.1 和 v3.0。v2.1 面向手工调试和小规模实验，一个 episode 对应一组 Parquet + MP4 文件；v3.0 将多条 episode 合并到共享文件中，通过 metadata 记录每条 episode 的偏移，适合大规模训练和 Hub 流式读取。

本章以 LIBERO 单臂操作数据集（1693 条 episode、273465 帧、2 路相机、Panda 机械臂、10 fps）为例，展示两个版本的完整目录结构、核心文件内容以及单条数据的实际数值。

## 宏观结构对比

核心差异：**v2.1 一个 episode 一组文件，v3.0 多条 episode 合并到共享文件**。

v2.1：

```text
dataset/
├── meta/
│   ├── info.json
│   ├── stats.json
│   ├── episodes.jsonl
│   ├── episodes_stats.jsonl
│   └── tasks.jsonl
├── data/
│   └── chunk-000/
│       ├── episode_000000.parquet
│       ├── episode_000001.parquet
│       └── ...
└── videos/
    └── chunk-000/
        ├── observation.images.image/
        │   ├── episode_000000.mp4
        │   └── ...
        └── observation.images.image2/
            ├── episode_000000.mp4
            └── ...
```

v3.0：

```text
dataset/
├── meta/
│   ├── info.json
│   ├── stats.json
│   ├── tasks.parquet
│   └── episodes/
│       └── chunk-000/
│           └── file-000.parquet
├── data/
│   └── chunk-000/
│       └── file-000.parquet
└── videos/
    ├── observation.images.image/
    │   └── chunk-000/
    │       └── file-000.mp4
    └── observation.images.image2/
        └── chunk-000/
            └── file-000.mp4
```

文件对照：

| 文件 | v2.1 | v3.0 |
|---|---|---|
| 任务文本 | `meta/tasks.jsonl` | `meta/tasks.parquet` |
| episode 元信息 | `meta/episodes.jsonl` | `meta/episodes/chunk-000/file-000.parquet` |
| episode 统计量 | `meta/episodes_stats.jsonl` | 合并到 episodes parquet 的扁平列 |
| 帧数据 | `data/.../episode_N.parquet`（每 episode 独立） | `data/.../file_N.parquet`（所有 episode 合并） |
| 视频 | `videos/chunk-000/{cam}/episode_N.mp4` | `videos/{cam}/chunk-000/file_N.mp4` |

---

## v3.0 详解

### `meta/info.json` — 全局元信息

打开数据集后第一件事就是查看此文件。它回答"这批数据是什么、有多少、有哪些字段、怎么组织的"。训练代码据此构建数据加载 pipeline。

```json
{
  "codebase_version": "v3.0",
  "fps": 10.0,
  "robot_type": "panda",
  "total_episodes": 1693,
  "total_frames": 273465,
  "data_files_size_in_mb": 100,
  "features": {
    "observation.images.image":  { "dtype": "video",   "shape": [256, 256, 3] },
    "observation.images.image2": { "dtype": "video",   "shape": [256, 256, 3] },
    "observation.state":         { "dtype": "float32", "shape": [8] },
    "action":                    { "dtype": "float32", "shape": [7] },
    "timestamp":                 { "dtype": "float32", "shape": [1] },
    "frame_index":               { "dtype": "int64",   "shape": [1] },
    "episode_index":             { "dtype": "int64",   "shape": [1] },
    "index":                     { "dtype": "int64",   "shape": [1] },
    "task_index":                { "dtype": "int64",   "shape": [1] }
  }
}
```

初学者要养成习惯：训练前先读 `info.json`，不要假设 `action` 是 7 维，也不要假设相机名字一定是 `image`。不同机器人、不同控制接口会给同名字段不同语义。

### `meta/tasks.parquet` — 任务文本

数据帧中的 `task_index` 外键关联到此表。LIBERO 共有 40 个不同任务：

| task_index | task |
|---|---|
| 0 | put the white mug on the left plate and put the yellow and white mug on the right plate |
| 1 | put the white mug on the plate and put the chocolate pudding to the right of the plate |
| 2 | put the yellow and white mug in the microwave and close it |
| 3 | turn on the stove and put the moka pot on it |
| 4 | put both the alphabet soup and the cream cheese box in the basket |
| ... | （共 40 条） |

### `meta/stats.json` — 归一化统计量

训练时 preprocessor 读取此文件做归一化 `(value - mean) / std`，推理时 postprocessor 用同样数值做反归一化。**数据发生任何变更（删除 episode、合并数据集、修改字段）后必须重算**。此外还包含 `q01`/`q10`/`q50`/`q90`/`q99` 分位数。

常见事故：

- 清洗或合并数据后没有重新计算 stats，归一化统计量错误。
- train 和 rollout 使用了不同数据集的 stats，推理输出尺度偏离。
- action 维度顺序变了，但 stats 仍来自旧 schema。



### `meta/episodes/chunk-000/file-000.parquet` — Episode 定位索引

这是 v3.0 的核心文件，替代 v2.1 的 `episodes.jsonl` + `episodes_stats.jsonl`。1693 行 × 14 列，每行对应一条 episode。

以 **Episode 2** 为例（完整 14 列）：

| 列名 | 值 | 含义 |
|---|---|---|
| `episode_index` | 2 | episode 编号 |
| `length` | 345 | 帧数 |
| `dataset_from_index` | 498 | data parquet 起始行号 |
| `dataset_to_index` | 843 | data parquet 结束行号（不含） |
| `data/chunk_index` | 0 | 数据 chunk 编号 |
| `data/file_index` | 0 | 数据 file 编号 |
| `videos/observation.images.image/chunk_index` | 0 | 相机 1 视频 chunk |
| `videos/observation.images.image/file_index` | 0 | 相机 1 视频 file |
| `videos/observation.images.image/from_timestamp` | 49.8 | 相机 1 视频起始秒 |
| `videos/observation.images.image/to_timestamp` | 84.3 | 相机 1 视频结束秒 |
| `videos/observation.images.image2/chunk_index` | 0 | 相机 2 视频 chunk |
| `videos/observation.images.image2/file_index` | 0 | 相机 2 视频 file |
| `videos/observation.images.image2/from_timestamp` | 49.8 | 相机 2 视频起始秒 |
| `videos/observation.images.image2/to_timestamp` | 84.3 | 相机 2 视频结束秒 |

数据定位规则：查表得 `dataset_from=498`、`dataset_to=843`，则：

```text
data/chunk-000/file-000.parquet 的第 498~842 行        → 帧数据
videos/.../image /chunk-000/file-000.mp4 的 49.8~84.3s → 相机 1 视频
videos/.../image2/chunk-000/file-000.mp4 的 49.8~84.3s → 相机 2 视频
```

前一 episode 的 `dataset_to_index=498` 与本条 `dataset_from` 恰好衔接，各 episode 在 data parquet 和 MP4 中均为**连续无间隔存储**。

> 此例中所有数据都在 `chunk-000/file-000` 中，因为总帧数 27 万尚不触发拆分。当 data parquet 大小超过 `data_files_size_in_mb`（默认 100 MB）时，会自动拆分为 `file-000.parquet`、`file-001.parquet`……，视频同理。

### `data/chunk-000/file-000.parquet` — 帧级数值数据

所有 1693 条 episode 的全部 273465 帧合并为一个 Parquet 文件。以下为 Episode 0 前 3 帧：

| 列 | frame 0 | frame 1 | frame 2 |
|---|---|---|---|
| `observation.state` | `[-0.0534, 0.0070, 0.6783, 3.1408, 0.0018, -0.0899, 0.0388]` | `[-0.0533, 0.0070, 0.6783, 3.1408, 0.0017, -0.0897, 0.0389]` | `[-0.0532, 0.0070, 0.6783, 3.1408, 0.0017, -0.0893, 0.0389]` |
| `action` | `[0.0161, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0]` | `[0.0134, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0]` | `[0.0027, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0]` |
| `timestamp` | 0.0 | 0.1 | 0.2 |
| `frame_index` | 0 | 1 | 2 |
| `episode_index` | 0 | 0 | 0 |
| `task_index` | 0 | 0 | 0 |

图像/视频数据不直接存储在 data parquet 单元格中，而是以 MP4 文件存放于 `videos/` 目录。读取时通过 episodes 表的 `from_timestamp`/`to_timestamp` 从 MP4 解码对应帧区间。

---

## v2.1 格式

同一批 LIBERO 数据若以 v2.1 格式存储，核心差异在于**文件粒度**和**metadata 格式**：

```text
dataset/
├── meta/
│   ├── info.json                    ← codebase_version: "v2.1", 含 total_chunks/total_videos
│   ├── stats.json                   ← 与 v3.0 内容一致
│   ├── episodes.jsonl               ← 每行 {episode_index, tasks, length}
│   ├── episodes_stats.jsonl         ← 每行 {episode_index, stats: {...}}
│   └── tasks.jsonl                  ← 每行 {task_index, task}
├── data/
│   └── chunk-000/
│       ├── episode_000000.parquet   ← Episode 0（214 帧）
│       ├── episode_000001.parquet   ← Episode 1（284 帧）
│       └── ...                      ← 共 1693 个独立文件
└── videos/
    └── chunk-000/
        ├── observation.images.image/
        │   ├── episode_000000.mp4
        │   └── ...
        └── observation.images.image2/
            ├── episode_000000.mp4
            └── ...
```

典型 JSONL 内容：

```jsonl
┌─ meta/tasks.jsonl ──────────────────────────────────────────
│ {"task_index": 0, "task": "put the white mug on the left plate..."}
│ {"task_index": 1, "task": "put the white mug on the plate..."}
│
├─ meta/episodes.jsonl ───────────────────────────────────────
│ {"episode_index": 0, "tasks": ["put the white mug..."], "length": 214}
│ {"episode_index": 1, "tasks": ["put the white mug..."], "length": 284}
│
├─ meta/episodes_stats.jsonl ─────────────────────────────────
│ {"episode_index": 0, "stats": {"action": {"mean": [...], "count": [214]}, ...}}
```

`meta/stats.json` 的全局统计量由这些 per-episode stats 加权聚合得到。

v2.1 的优缺点：

- 文件名直接包含 `episode_index`，定位单条 episode 直观，适合手工调试。
- 删除/替换单条 episode 可直接操作文件，不需要工具。
- 但 episode 多时文件数爆炸（1693 episodes ≈ 6700+ 个文件），文件系统 I/O 压力大，不支持 Hub streaming。

---

## 关键差异速查

| 维度 | v2.1 | v3.0 |
|---|---|---|
| 数据文件命名 | `episode_000000.parquet` | `file_000.parquet` |
| 数据粒度 | 1 文件 = 1 episode | 1 文件 = 所有 episode |
| 视频路径 | `videos/chunk-000/{cam}/episode_N.mp4` | `videos/{cam}/chunk-000/file_N.mp4` |
| 任务文件 | `tasks.jsonl` | `tasks.parquet` |
| episode 元信息 | `episodes.jsonl` | `episodes/chunk-000/file_000.parquet` |
| episode 统计量 | `episodes_stats.jsonl` | 合并到 episodes parquet |
| 定位单 episode | 文件名直接查找 | 查 episodes 表的 offset |
| 删除单 episode | 直接删文件 | 必须通过 `lerobot-edit-dataset` |
| info.json 字段 | `total_chunks`, `total_videos` | `data_files_size_in_mb` |
| streaming | 不支持 | 支持 |
| 适用场景 | 教学、调试、小规模 | 大规模训练、远程存储 |

---

## v2.1 转 v3.0

LeRobot 提供官方转换脚本：

```bash
# Hub 数据集
python src/lerobot/scripts/convert_dataset_v21_to_v30.py --repo-id=lerobot/pusht

# 本地数据集（原地转换）
python src/lerobot/scripts/convert_dataset_v21_to_v30.py \
  --repo-id=my_dataset \
  --root=/path/to/v21/dataset \
  --push-to-hub=false
```

转换流程：读取 v2.1 结构 → 合并 data 文件 → 合并视频文件 → 聚合 stats → 写入 v3.0 结构 → 原目录备份为 `*_old`。


## 小结

LeRobot v2.1 和 v3 的差别本质上不是哪个更高级，而是数据规模和工程约束不同：

- v2.1 更直观，适合旧脚本和手工检查，文件名即 episode 编号。
- v3 更工程化，适合大规模、远程、流式和长期维护，所有数据通过 metadata 索引。
- 任何转换都必须把 `data/`、`videos/`、`meta/` 和 stats 作为一个整体处理，不能只移动文件。

新采集的数据集默认即为 v3.0，只有从旧版本继承的数据才需执行 v2.1 → v3.0 转换。


## 自测问题

- LeRobot 软件版本和 LeRobotDataset 格式版本有什么区别？
- v3.0 的核心变化是什么？为什么大规模训练需要 file-based storage？
- `meta/stats.json` 在训练和部署中分别起什么作用？什么情况下必须重算？
- v2.1 的 `episodes_stats.jsonl` 和 v3.0 的 episodes parquet 有什么区别？

## 导航

- 返回父页：[LeRobot](../08-lerobot.md)
- 上一节：[环境安装与版本固定](02-setup.md)
- 下一节：[ACT 复现](04-act.md)
