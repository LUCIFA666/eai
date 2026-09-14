# 数据类型、转换与收集

目标：建立机器人学习数据层的整体框架，能从数据格式、数据转换、数据源和数据收集引擎四个角度组织一个可复现的数据工作流。

本章只处理机器人学习的数据层：常用数据格式是什么、格式之间如何转换、具身智能训练数据源有哪些、RoboGenesis 数据收集引擎如何组织采集。遥操作硬件、人体视频到机器人动作迁移、真机现场采集和安全部署属于真机实战章节；Behavior Cloning、DAgger、ACT、Diffusion Policy 等“如何用数据训练策略”的内容放到后续策略训练章节；benchmark 协议和结果复现放到后续评测章节。

本章由五个二级模块组成。前两节先解决“数据怎么存”和“格式怎么转”，第三节建立数据源的阅读方法，第四节把采集过程组织成可复现的数据收集引擎，第五节讨论数据配比与质量评估。

## 章节结构

| 二级模块 | 三级页面 | 学习重点 |
|---|---|---|
| [常用数据格式](01-common-data-formats.md) | [LeRobot 数据格式](01-common-data-formats/01-lerobot-data-format.md)、[HDF5](01-common-data-formats/02-hdf5.md)、[RLDS](01-common-data-formats/03-rlds.md) | LeRobot、HDF5、RLDS 的组织方式、优点、代价和转换风险 |
| [数据转换](02-data-conversion.md) | [Any4LeRobot](02-data-conversion/01-any4lerobot.md)、[LeRobot 数据工作流](02-data-conversion/02-lerobot-data-workflow.md) | 从源数据到 LeRobot 的字段映射、验证、统计重算和转换报告 |
| [具身智能数据集](03-embodied-training-datasets.md) | 真机数据集、Egocentric 视频、人-物交互、仿真生成、抓取、导航、互联网视频 | 按数据类型分类的具身 AI 训练数据全景 |
| [RoboGenesis 数据收集引擎](04-robogenesis-data-engine.md) | 不预设三级目录 | 用引擎化方式组织任务配置、runner、recorder、validator 和 dataset sink |
| [数据配比与质量评估](05-data-mixture-and-quality.md) | 不预设三级目录 | mixture 配比、质量过滤与去重、data scaling 经验，解决"多少才够、什么才算好" |

## 本章边界

本章重点是数据类型、数据来源、数据转换和采集引擎，不展开遥操作硬件、真机采集流程和策略训练算法本身。真机数据采集和人类示教迁移放在第 11 章，模型训练与推理、评测工程、强化学习、sim2real 和安全部署会在后续章节分别展开。

本章默认学习对象是初学者，内容会优先回答：

- 一条机器人轨迹应该包含哪些字段，字段之间如何对齐。
- LeRobot、HDF5、RLDS 各自适合什么场景。
- 如何用 Any4LeRobot 设计可审计的格式转换流程。
- 大规模真机数据源的机器人本体、任务规模、模态和合规边界有什么差异。
- 如何用 RoboGenesis 数据收集引擎组织数据收集任务，而不是把数据生成和落盘逻辑散落在脚本里。
- 如何用 LeRobot 跑通一个可复现的数据采集、可视化、回放、编辑和封口流程。

## 本章产出

完成本章后，你应该能产出一份小型机器人模仿学习项目的数据包和训练记录：

- 一份轨迹 schema，说明 observation、state、action、task、success、timestamp 和 metadata 的含义。
- 一份真机数据源对照表，记录机器人类型、规模、任务、模态、许可和使用风险。
- 一份格式转换报告，记录源数据、转换工具版本、过滤规则、输出 schema 和抽样检查结果。
- 一组 replay 或 data visualization 证据，证明 observation、action、task 和 video 对齐。
- 一份 RoboGenesis 风格采集蓝图，写清 task config、runner、recorder、validator 和 dataset sink 的边界。

## 验收方式

可以用下面的问题自测：

- 给定一个 episode，能否指出每个 frame 的 observation、action、timestamp 和 task 如何对齐？
- 能否说明 LeRobot、HDF5、RLDS 的文件组织差异？
- 能否判断 Open X、DROID、BridgeData V2 这类大规模真机数据源分别适合回答什么问题？
- 能否说明 HDF5 或 RLDS 转 LeRobot 时最容易错的字段或语义？
- 能否用 LeRobot 工具完成 record、dataset-viz、replay、edit 和 stats 维护？
- 能否画出 RoboGenesis 数据收集引擎从 task config 到 dataset sink 的数据流？

这些问题能回答清楚，才说明你已经从“有一堆演示数据”进入了“能管理一个可复现、可扩展的机器人学习数据系统”。下一步再进入策略训练内容，学习这些数据如何训练成不同类型的策略。
