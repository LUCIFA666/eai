# RoboGenesis 数据收集引擎

> 难度：[中级] | 预计用时：50 分钟
> 先修：[大规模真机数据集](03-embodied-training-datasets/01-real-robot-datasets.md) → [第 5 章仿真建模](../05-simulation-and-task-modeling/README.md)
> 建议：把本节看成“采集系统蓝图”，暂不预设三级目录

## 心智模型

RoboGenesis 数据收集引擎可以把它想成“机器人数据工厂的装配线”。以前很多项目把任务配置、场景初始化、相机设置、策略 rollout、视频保存、统计汇总都散落在不同脚本里，能跑一次，但很难复现第二次。引擎化设计的核心是把这些环节拉到一条标准流水线上，让每一条 episode 都带着清楚的配置来源、执行证据和落盘规范离开系统。对第七章来说，它的意义不是“架构更漂亮”，而是让数据从第一天起就可训练、可回放、可审计。

## 学习目标

读完本页后，你应该能：

- 解释 RoboGenesis 风格数据收集引擎为什么要把任务配置、执行 runner 和封口流程拆开。
- 画出场景、机器人、策略、记录器和数据落盘之间的数据流。
- 判断一个采集系统是否已经具备“可复现、可训练、可审计”的最小能力。
- 为后续训练和评测预留必要的 manifest、schema 和版本字段。

## 先看总架构图

```text
task config
  -> scene builder
  -> robot + sensors
  -> policy / teleop / oracle
  -> collection runner
  -> recorder + validator
  -> dataset sink
  -> manifest + videos + stats + card
```

这张图里最重要的一点是：采集不是“跑完 rollout 就结束”，而是要一路走到 manifest 和封口。

## 为什么要引擎化，而不是继续堆脚本

脚本式采集的典型问题：

| 问题 | 早期看起来没事 | 后面会怎样 |
|---|---|---|
| 配置写死在代码里 | 自己还能记得 | 三周后没人知道相机和随机种子 |
| 每个任务单独保存逻辑 | 任务少时还能忍 | 多任务后字段开始漂移 |
| 失败原因不落盘 | 先求能跑 | 无法知道为何成功率波动 |
| 没有封口版本 | 小数据时无所谓 | 训练和评测引用了不同数据版本 |

RoboGenesis 风格的价值正是把这些“迟早会出事”的东西前置处理。

## 采集系统里的 6 个职责

| 组件 | 主要职责 | 产出 |
|---|---|---|
| Task Config | 定义任务、场景、机器人、相机、动作空间和输出规范 | 可解析配置 |
| Scene Builder | 实例化资产、布局、随机化 | 可执行环境实例 |
| Policy / Teleop | 产生动作 | action 流 |
| Collection Runner | 驱动批量 rollout、管理并行和重试 | episode 执行日志 |
| Recorder / Validator | 记录 observation/action，做基本门禁 | 中间样本和检查结果 |
| Dataset Sink | 写出 parquet、视频、manifest、stats | 最终数据包 |

把这 6 个职责拆清楚后，你才能知道错误到底是出在场景、策略、回放，还是落盘。

## 用“采集输出”倒推系统设计

如果一个采集引擎最后至少要产出：

- episode manifest
- observation schema
- action schema
- success / failure 标注
- 视频证据
- dataset card

那么前面的系统设计就必须倒推满足这些输出。比如：

- 没有统一 `task_id`，你就很难写清 dataset card 的任务分布。
- 没有 `scene_seed`，你就很难复现实验。
- 没有失败原因分类，后面就无法做 targeted recollection。

## 一个 episode 在引擎里如何流动

```text
load task config
  -> sample scene seed
  -> reset environment
  -> run policy / teleop
  -> collect observation + action + timestamps
  -> check success / timeout / invalid
  -> save episode artifacts
  -> update dataset manifest
```

如果你能把这 7 步讲清楚，就已经抓住了引擎的主线。

## 这个引擎和其他章节怎么接口

### 对第 5 章

第 5 章负责仿真建模和任务定义，本节负责把这些定义稳定地转成批量数据。也就是说，第 5 章产出的是“世界和任务能否被表达”，本节产出的是“这些表达能否被批量记录成训练数据”。

### 对第 7 章（模型训练）

第 7 章训练 VLA/模仿学习策略时会关心复杂任务和更大规模数据。本节要提前保留的，是 task family、subtask、scene variation 等字段，否则后面很难做长任务和 mixture。

### 对第 8 章（评测）

第 8 章做评测时，最怕“训练数据版本不清”。本节的封口和 manifest 设计，就是为了让训练和评测引用同一份可追踪数据。

## 你应该关心哪些最小输出字段

一个引擎化采集系统，建议至少保证下面这些字段可追踪：

```yaml
dataset:
  schema_version: 1.0.0
  task_version: pick_place_v3
  asset_version: kitchen_assets_2026_05
  robot_type: single_arm_franka
  fps: 20

episode:
  episode_index: 42
  scene_seed: 1234
  success: true
  failure_reason: null
  policy_source: oracle_pick_place_v2

frame:
  timestamp: 1.25
  observation.images.front: ...
  observation.state: ...
  action: ...
```

这套分层和 [常用数据格式](01-common-data-formats.md) 的数据组织要求是一致的，只是这里把它放进了引擎职责中。

## 从“能跑一次”到“能稳定收 1000 条”

当你把采集量从 `10` 提到 `1000`，系统必须额外具备：

| 能力 | 为什么需要 |
|---|---|
| 并行执行 | 否则采集时间不可接受 |
| 断点续跑 | 长作业不能因为单次崩溃全废 |
| 失败重跑 | 坏 episode 不能手工一点点捡 |
| 质量抽检 | 不可能全量人工看视频 |
| 封口版本 | 训练和评测必须知道引用的是哪一版 |

这说明引擎化不是“大厂做法”，而是规模一上来就必需。

## 自测问题

- 为什么一个“能保存视频”的采集脚本，还远远不等于一个数据收集引擎？
- 如果 task config、runner 和 sealing 不拆开，后续最容易在哪些地方失控？
- 为什么说 manifest 和 dataset card 不是后处理附件，而是采集系统输出的一部分？
