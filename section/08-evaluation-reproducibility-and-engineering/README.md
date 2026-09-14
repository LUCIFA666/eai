# 评测工程

本章按运行载体归类 benchmark：仿真 Benchmark、真机 Benchmark。每个 benchmark 页面自己写清任务、主指标、episode/seed、环境版本与证据口径。

## 二级目录

| 二级主题 | 三级内容 | 分类依据 |
|---|---|---|
| [仿真 Benchmark](01-simulation-benchmarks.md) | 导航、操作、记忆三类：OmniNavBench、LIBERO、Meta-World、CALVIN、RoboTwin 2.0、RoboCasa、SimplerEnv、RLBench、BEHAVIOR-1K、ManiSkill3、VLABench、EBench、MIKASA 等 | 主要在 MuJoCo、SAPIEN、Isaac Gym、CoppeliaSim、OmniGibson 或轻量仿真环境中闭环评测 |
| [真机 Benchmark](02-real-robot-benchmarks.md) | RoboChallenge、RoboArena | 需要真实机器人、真实物体、人工复位、安全事件和现场证据 |

## 本章边界

本章不负责训练模型，也不单独讲通用评测基础。每个 benchmark 页面必须自己写清任务、主指标、episode/seed、环境版本、case 证据和结果解释方式。世界模型相关 benchmark 放第 10 章；真机 benchmark 放 8.2；GenSim 类任务自动生成工具属于仿真与数据侧（第 5、6 章），不在本章。

## Benchmark 覆盖

| Benchmark | 主指标 | 位置 |
|---|---|---|
| OmniNavBench / Habitat Challenge / AI2-THOR / RoboTHOR | Navigation success / SPL / task success | 仿真 Benchmark / 导航 |
| LIBERO | Average Success Rate | 仿真 Benchmark |
| LIBERO Plus | Average Success Rate / robustness drop | 仿真 Benchmark |
| Meta-World | Average Success Rate | 仿真 Benchmark |
| CALVIN | Average completed tasks / sequence length | 仿真 Benchmark |
| RoboTwin 2.0 | Hard Success Rate | 仿真 Benchmark |
| RoboCasa | Average Success Rate | 仿真 Benchmark |
| SimplerEnv / RLBench / BEHAVIOR-1K | Success 或 progress 指标 | 仿真 Benchmark |
| ManiSkill3 | Success Rate（GPU 并行评测） | 仿真 Benchmark |
| VLABench | 语言条件长程任务 + 泛化分箱 | 仿真 Benchmark |
| EBench / HumanoidBench / Isaac Lab-Arena | Success / task score / arena score | 仿真 Benchmark / 操作 |
| MIKASA / RoboMME / RoboMemArena / RoboHiMan | Memory / long-horizon reasoning / task success | 仿真 Benchmark / 记忆 |
| RoboChallenge | Score | 真机 Benchmark |
| RoboArena | 双盲 A/B + Elo 类排名 | 真机 Benchmark |

## 验收方式

随机抽一个 benchmark，应该能从页面追溯：

1. 它属于仿真还是真机评测。
2. 主指标是什么，是否能和其它 benchmark 横向比较。
3. task、case、seed、episode 数和最大步数如何记录。
4. 视频、日志、失败分类和结果表如何保存。
5. 论文、代码、项目页和官方结果在哪里。

## 延伸阅读

- EvoMind VLA SOTA Leaderboard. https://sota.evomind-tech.com/
- EvoMind Methodology. https://sota.evomind-tech.com/methodology/
- EvoMind Dexterous Manipulation SOTA Leaderboard. https://sota.evomind-tech.com/dex/
