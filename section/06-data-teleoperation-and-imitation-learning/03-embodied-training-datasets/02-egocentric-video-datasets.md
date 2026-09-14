# Egocentric 视频数据集

目标：全面了解以人类第一视角（Egocentric View）采集的视频数据集生态，掌握各数据集的规模、标注类型与适用场景，为具身 AI 研究选择合适的数据源。

Egocentric（第一人称）视频是具身 AI 数据的重要补充。真机操作数据量级有限且采集成本高，而人类在日常生活中执行的操作任务与机器人目标高度重合——抓取、放置、开关、工具使用等。通过大规模第一人称视频，模型可以学到丰富的手-物交互先验、场景 affordance 和时序动作结构，再迁移到机器人策略中。

下面按"与具身 AI 的关联度"分五大类介绍主流 ego 数据集。

## 总览对比表

| 数据集 | 年份 | 规模 | 模态 | 核心特色 | 具身 AI 关联 |
|--------|------|------|------|---------|-------------|
| [Ego4D](02-egocentric-video-datasets/01-ego4d.md) | 2021 | 3,670 hrs | RGB + IMU + 眼动 + 音频 | 最大单源 ego 基准，5 大 benchmark | 视觉预训练、动作预测 |
| [Ego-Exo4D](02-egocentric-video-datasets/02-ego-exo4d.md) | 2023 | 1,286 hrs | ego+exo 同步 + IMU + 3D 点云 | 双视角对齐 | 跨视角迁移到机器人 |
| [EgoLife](02-egocentric-video-datasets/03-egolife.md) | 2025 | 300 hrs | 多视角 + 音频 + 密集标注 | 连续一周共居记录 | 长上下文日常理解 |
| [EPIC-KITCHENS-100](02-egocentric-video-datasets/04-epic-kitchens-100.md) | 2018/2020 | 100 hrs | RGB | 厨房动作识别标杆 | 操作技能学习 |
| [HD-EPIC](02-egocentric-video-datasets/05-hd-epic.md) | 2025 | 41 hrs | 高分辨率 RGB | EPIC 高清扩展，密集标注 | 精细动作识别 |
| [HOI4D](02-egocentric-video-datasets/06-hoi4d.md) | 2022 | 2.4M RGB-D 帧 | RGB-D + 4D 点云 + 手/物 mesh | 类别级 4D 手-物交互 | 3D 交互理解 |
| [ARCTIC](02-egocentric-video-datasets/07-arctic.md) | 2022 | 2.1M 帧 | RGB + SMPL-X + 物体 mesh | 双手+全身+铰接物体 | 灵巧双手操作 |
| [EgoDex](02-egocentric-video-datasets/08-egodex.md) | 2025 | 829 hrs | Vision Pro 原生 3D 手部追踪 | 194 种双手任务 | VLA 双手操作训练 |
| [EgoHOS](02-egocentric-video-datasets/09-egohos.md) | 2022 | 11K+ 帧 | RGB + 分割掩码 | 手-物像素级分割 | affordance 检测 |
| [Assembly101](02-egocentric-video-datasets/10-assembly101.md) | 2022 | 513 hrs | 12 视角 + 3D 手部姿态 | 程序化组装任务 | 操作规划与错误检测 |
| [EGTEA Gaze+](02-egocentric-video-datasets/11-egtea-gaze-plus.md) | 2018 | 28 hrs | RGB + 眼动 | 注视-动作对齐 | 注意力引导操作 |
| [HoloAssist](02-egocentric-video-datasets/12-holoassist.md) | 2023 | 169 hrs | HoloLens 多模态 | 交互式任务辅助 | 人机协作指令 |
| [EgoProceL](02-egocentric-video-datasets/13-egoprocel.md) | 2022 | 62 hrs | RGB + key-step 标注 | 第一人称程序学习 | 关键步骤识别与任务规划 |
| [EgoExoLearn](02-egocentric-video-datasets/14-egoexolearn.md) | 2024 | 120 hrs | ego + 示教视角 + 眼动 | 桥接观察与执行 | 人类视频→机器人迁移 |
| [EgoBody](02-egocentric-video-datasets/15-egobody.md) | 2022 | 125 序列 | RGB-D + SMPL-X | ego 视角人体姿态 | 人机社交交互 |
| [EgoPAT3D](02-egocentric-video-datasets/16-egopat3d.md) | 2022 | 1M+ RGB-D 帧 | RGB-D + 3D 轨迹 | 动作目标 3D 预测 | 抓取目标预测 |
| [EgoObjects](02-egocentric-video-datasets/17-egoobjects.md) | 2023 | 9,200+ 视频 | RGB + 检测标注 | 类别级与实例级物体检测 | 物体泛化识别 |

## 大规模基础基准

### Ego4D

Meta AI 联合全球 13 所大学发布的大规模第一人称视频基准，约 3,670 小时、923 位参与者、来自 9 个国家 74 个场景的日常活动视频。提供五大基准任务：情景记忆（Episodic Memory）、手-物交互（Hands & Objects）、视听理解（Audio-Visual）、社交互动（Social）和未来预测（Forecasting）。

Ego4D 是 ego-centric 领域最具代表性的数据源，也是许多视觉预训练模型（如 EgoVLP、LaViLa）的核心训练集。

[https://ego4d-data.org/](https://ego4d-data.org/)

### Ego-Exo4D

Ego4D 的演进版本（Meta AI, 2023），核心创新是同时提供第一人称（ego）和第三人称（exo）的配对视频，覆盖 1,286 小时、740 位参与者、13 个城市。附带 IMU、眼动追踪、3D 点云和音频。

双视角对齐对具身 AI 特别有价值：ego 视角接近机器人腕部相机，exo 视角接近外部监控相机，两者对齐后可以学习跨视角的动作表征和空间理解，是人类视频→机器人策略迁移的关键数据基础。

[https://ego-exo4d-data.org/](https://ego-exo4d-data.org/)

### EgoLife

由多家机构联合发布的连续生活记录数据集（2025），6 名参与者在共居环境中连续记录一周，总计约 300 小时。同时提供第一人称和第三人称同步视频，附带密集标注。

EgoLife 的核心价值在于**长上下文理解**：与 Ego4D 的片段式采集不同，EgoLife 捕获完整的日常生活流（讨论、购物、烹饪、社交、娱乐），支持 EgoLifeQA 基准——面向实际需求的长上下文问答任务，如回忆过去事件、监控健康习惯、提供个性化建议。这类长程理解能力对机器人在家庭环境中的长期任务规划和个性化服务至关重要。

[https://egolife-ai.github.io/](https://egolife-ai.github.io/)

### EPIC-KITCHENS-100

University of Bristol 发布的厨房场景第一人称视频数据集（2018 首版，2020 扩展至 100 小时），覆盖 45 个厨房、90K 个动作片段。参与者自行叙述非脚本化的烹饪过程，标注粒度细致，覆盖动作片段、物体交互和动作预测。

厨房场景是具身操作研究的高频测试场景，EPIC-KITCHENS 提供的长尾物体分布和复杂动作组合对策略泛化研究有重要价值，是 ego-centric 动作识别领域的事实标准基准。

[https://epic-kitchens.github.io/](https://epic-kitchens.github.io/)

### HD-EPIC

EPIC-KITCHENS 的高分辨率扩展版（University of Bristol, 2025），约 41 小时，提供比原版更密集的细粒度标注。高分辨率使得模型能够捕获更精细的手部动作和物体状态变化，适合需要像素级精度的操作技能学习。

[https://hd-epic.github.io/](https://hd-epic.github.io/)

## 手-物交互与灵巧操作

### HOI4D

清华大学与北京大学联合发布（2022），包含 2.4M RGB-D 帧、4K 段序列、800 个物体、610 个房间场景。提供类别级 4D 交互标注：全景分割、3D 手部/物体姿态和 mesh 重建。

HOI4D 的独特之处在于 4D（3D 空间 + 时间）维度的手-物交互标注，使其成为 3D 交互理解和类别级物体操作研究的核心数据集。

[https://hoi4d.github.io/](https://hoi4d.github.io/)

### ARCTIC

ETH Zurich 与 MPI 联合发布（2022），2.1M 帧，339 段序列，11 个铰接物体（如笔记本电脑、剪刀、开瓶器）。ARCTIC 是目前唯一同时提供双手 + 全身（SMPL-X）+ 铰接物体的数据集，对灵巧双手操作研究不可替代。

[https://arctic.is.tue.mpg.de/](https://arctic.is.tue.mpg.de/)

### EgoDex

Apple 发布的大规模双手灵巧操作数据集（2025），829 小时、30K 条轨迹、194 种双手任务。使用 Apple Vision Pro 原生 3D 手指追踪采集，无需外部传感器。EgoDex 是目前规模最大的双手灵巧操作 ego 数据集，直接面向 VLA 模型的双手操作训练。

[https://github.com/apple/ml-egodex](https://github.com/apple/ml-egodex)

### EgoHOS

手-物像素级分割数据集（2022），11K+ 帧。提供精确的手部和所持物体的分割掩码，可用于 affordance 检测——判断哪些区域可以交互、当前正在交互什么。

[https://github.com/owenzlz/EgoHOS](https://github.com/owenzlz/EgoHOS)

## 程序化任务与日常活动

### Assembly101

University of Bristol 与 Meta AI 联合发布（2022），513 小时、12 个视角同步录制、1M+ 动作片段、18M 3D 手部姿态标注。任务是无指导的玩具车辆组装——参与者不看说明书，自由尝试拼装。

Assembly101 是第一个大规模多视角程序化任务数据集，组装任务的顺序多样性和错误模式对机器人操作规划和错误检测研究极有价值。

[https://assembly-101.github.io/](https://assembly-101.github.io/)

### EGTEA Gaze+

Georgia Tech 发布的烹饪场景数据集（2018），28 小时、10K+ 标注片段，配有同步眼动追踪数据。EGTEA Gaze+ 的独特价值在于注视（gaze）与动作的对齐标注——人类在操作时看哪里，这个信息对学习注意力引导的操作策略和理解人类操作意图非常关键。

[https://cbs.ic.gatech.edu/fpv/](https://cbs.ic.gatech.edu/fpv/)

### HoloAssist

Microsoft Research 发布（2023），169 小时，使用 HoloLens 采集。场景是一个人戴着 HoloLens 执行任务（如组装家具、调试设备），另一个人远程通过语音和 AR 标注提供指导。这种交互式任务辅助数据对具身 AI 中的人机协作指令理解非常有用。

[https://holoassist.github.io/](https://holoassist.github.io/)

### EgoProceL

程序化学习数据集（2022），62 小时，覆盖 16 个生活领域。与 Assembly101 的单一任务不同，EgoProceL 强调跨领域的关键步骤识别和可变顺序（同一任务可以有多种完成路径），适合研究灵活的任务规划。

[https://sid2697.github.io/egoprocel/](https://sid2697.github.io/egoprocel/)

## 机器人迁移专用

### EgoExoLearn

上海人工智能实验室发布（2024），120 小时 ego + 示教视角视频，附带眼动数据。EgoExoLearn 专门设计用于桥接"观察学习"与"执行"的鸿沟——人类通过观察示教视频学会操作后，从自己的 ego 视角执行同一任务，两段视频配对标注。这种数据结构直接服务于人类视频→机器人动作迁移的研究。

[https://github.com/OpenGVLab/EgoExoLearn](https://github.com/OpenGVLab/EgoExoLearn)

## 身体姿态与场景理解

### EgoBody

ETH Zurich 发布（2022），125 段序列，提供 ego 视角下的人体 3D 姿态（SMPL-X）标注。EgoBody 解决的核心问题是：从机器人的 ego 视角如何准确感知周围人类的身体姿态和运动意图，对于人机社交交互和安全协作具有直接价值。

[https://egobody.ethz.ch/](https://egobody.ethz.ch/)

### EgoPAT3D

NYU 发布（2022），1M+ RGB-D 帧。任务是 3D 动作目标预测——给定当前 ego 视角的观察，预测人手即将到达的 3D 位置。对机器人抓取目标预测和动作预期有直接用途。

[https://ai4ce.github.io/EgoPAT3D/](https://ai4ce.github.io/EgoPAT3D/)

### EgoObjects

Meta 发布（2023），9,200+ 段视频，面向 ego 视角下的类别级和实例级物体检测。覆盖家庭和办公环境中的日常物体，测试模型在第一人称视角下的物体识别泛化能力。

[https://github.com/facebookresearch/EgoObjects](https://github.com/facebookresearch/EgoObjects)

## 选择建议

根据研究方向选择数据集：

| 研究方向 | 推荐数据集 |
|---------|-----------|
| 视觉预训练 / 基础模型 | Ego4D, EPIC-KITCHENS-100 |
| 跨视角迁移（人→机器人） | Ego-Exo4D, EgoExoLearn |
| 长程日常活动理解 | EgoLife, Ego4D |
| 手-物交互建模 | HOI4D, ARCTIC, EgoHOS |
| 双手灵巧操作 | EgoDex, ARCTIC |
| 程序化任务与装配 | Assembly101, HoloAssist, EgoProceL |
| 人体姿态感知 | EgoBody, EgoPAT3D |
| 注意力与眼动 | EGTEA Gaze+, Ego-Exo4D |

## 趋势

Ego-centric 数据集领域在 2024-2026 年呈现几个明显趋势：

- **规模爆发**：从 Ego4D 的 3,670 小时到 2025-2026 年出现万小时级数据集（如 EgoDex 829 hrs、Assembly101 513 hrs），数据量级持续攀升
- **多模态融合**：纯 RGB 已不够，深度、眼动、IMU、触觉、3D 手部追踪成为标配
- **面向迁移设计**：EgoExoLearn、Ego-Exo4D 等数据集明确以"人类视频→机器人策略"迁移为设计目标
- **连续长程记录**：从短片段采集转向 EgoLife 式的连续生活流记录，支撑长上下文理解能力