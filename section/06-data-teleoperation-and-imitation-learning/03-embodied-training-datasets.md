# 具身智能数据集

目标：建立具身智能训练数据的全景视图，理解不同来源、不同模态的数据如何服务于机器人策略学习。

具身智能的训练数据远不止真机操作轨迹。从数据来源看，可以分为真机采集、仿真生成、人类视频和互联网视频；从任务类型看，可以分为操作、抓取、导航和人-物交互；从模态看，可以涵盖 RGB、深度、本体感觉、语言、触觉、力/力矩等。不同类型的数据在策略训练管线中扮演不同角色：有的用于端到端模仿学习，有的用于视觉预训练，有的用于 affordance 建模，有的用于 sim-to-real 数据增强。

这一页先做数据类型地图，不急着展开单个数据集。后面的子页会按来源和用途拆开：先看真实机器人轨迹，再看人类视频、交互数据、仿真生成数据、抓取数据、导航场景和互联网视频预训练数据。读的时候可以一直带着两个问题：数据从哪来，适合训练什么能力。

## 阅读目标

读完这一页，建议能回答三个问题：

1. 具身智能训练数据为什么不能只等同于真机遥操作数据。
2. 真机轨迹、人类视频、仿真数据、抓取数据和导航场景数据分别适合解决什么问题。
3. 做一个训练项目时，为什么经常需要混合多种数据来源，而不是只依赖单一数据集。

## 数据类型总览

| 子节 | 数据类型 | 代表数据集 | 典型用途 |
|------|---------|-----------|---------|
| [大规模真机数据集](03-embodied-training-datasets/01-real-robot-datasets.md) | 真机遥操作轨迹 | Open X-Embodiment、DROID、BridgeData V2 等 | 端到端模仿学习、VLA 训练 |
| [Egocentric 视频数据集](03-embodied-training-datasets/02-egocentric-video-datasets.md) | 人类第一人称视频 | Ego4D、Ego-Exo4D、Epic-Kitchens | Affordance 学习、动作先验、视觉预训练 |
| [人-物交互数据集](03-embodied-training-datasets/03-hand-object-interaction-datasets.md) | 手部精细操作记录 | HOI4D、DexYCB、OakInk | 灵巧手策略、抓取规划、affordance 建模 |
| [仿真生成数据](03-embodied-training-datasets/04-simulation-generated-datasets.md) | 仿真自动化轨迹 | MimicGen、RoboCasa、DexMimicGen | 数据扩充、预训练、sim-to-real |
| [抓取专用数据集](03-embodied-training-datasets/05-grasp-datasets.md) | 抓取位姿标注 | GraspNet-1Billion、DexGraspNet | 抓取检测、抓取规划 |
| [导航与场景数据集](03-embodied-training-datasets/06-navigation-scene-datasets.md) | 室内 3D 场景与导航路径 | Matterport3D、R2R | 视觉语言导航、空间推理 |
| [互联网视频预训练数据](03-embodied-training-datasets/07-internet-video-pretraining-data.md) | 大规模网络视频 | Something-Something V2、Howto100M | 视频-语言预训练、动作语义理解 |

## 如何选择数据类型

不同研究目标对应不同的数据类型组合：

- 训练通用操作策略（VLA/ACT/Diffusion Policy）→ 优先看真机数据集，辅以仿真生成数据扩充
- 视觉预训练或 affordance 研究 → Egocentric 视频 + 互联网视频提供大规模视觉先验
- 灵巧手和精细操作 → 人-物交互数据集 + 抓取专用数据集
- 移动操作或导航 → 导航与场景数据集
- 数据不足时的规模扩充 → 仿真生成数据（MimicGen 系列）

实际项目中往往需要混合使用多种类型的数据。关键是理解每种数据的优势和局限，在训练管线中合理配比。
