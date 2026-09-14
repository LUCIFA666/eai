# 动手学具身 AI：章节总览

本项目目标是做一套比常见入门资料更完整、更细、并且真正从代码落地的具身 AI 课程。主体课程按能力域收敛成一级主题；具体算法、库、benchmark、case 和代码实验放在下级页面。

## 课程结构

| 一级章节 | 二级结构重点 |
|---|---|
| [01 导论](01-introduction/README.md) | 领域认知、任务地图、系统拆解、学习方法 |
| [02 机器人基础](02-robotics-foundations/README.md) | 机器人系统总览、模型资产与本体描述、空间关系与坐标约定、机器人状态观测、动作空间与命令接口、末端执行与接触、软件接口与运行调试 |
| [03 感知](03-perception-and-3d-vision/README.md) | 几何感知基础、对象感知、视觉基础模型、可交互感知、空间定位与语义地图、感知接口与闭环 |
| [04 规划控制](04-planning-control-and-baselines/README.md) | 运动规划基础、运动规划工具与实践、控制方法、移动机器人与移动操作、语言条件任务执行与技能编排 |
| [05 仿真建模](05-simulation-and-task-modeling/README.md) | 平台选择、MuJoCo、Isaac Sim、Isaac Lab、SAPIEN 生态、其他仿真生态、任务与场景自动生成 |
| [06 数据类型和收集](06-data-teleoperation-and-imitation-learning/README.md) | 常用数据格式、数据转换、具身智能数据集、RoboGenesis 数据收集引擎、数据配比与质量评估 |
| [07 模型训练与推理](07-vlm-vla-and-foundation-models/README.md) | VLA 基础、策略训练、常用库、部署推理、其他范式（含实时分块与在线学习）、形态与模态扩展 |
| [08 评测工程](08-evaluation-reproducibility-and-engineering/README.md) | 仿真 Benchmark、真机 Benchmark |
| [09 强化学习](09-reinforcement-learning-for-robotics/README.md) | 基础概念、经典算法（含 Model-based RL）、RLINF、SimpleVLA-RL、足式运动控制 RL |
| [10 世界模型](10-world-models/README.md) | 预测式、生成式（含 Cosmos）、世界模型评测 |
| [11 真机实战](11-real-robot-practice/README.md) | 安全与硬件选型、Hello Robot、硬件检查与标定、数据采集、平台适配、训练桥接、部署推理、Sim2Real |
| [12 研究生态](12-research-ecosystem-and-resources/README.md) | 论文导读与追踪入口、国内外知名团队、硬件与产业生态 |

## 学习路径

- 零基础路径：01 -> 02 -> 03 -> 04 -> 05。
- 操作学习路径：05 -> 06 -> 07 -> 08。
- VLA 路径：03 -> 06 -> 07 -> 08。
- 真机路径：02 -> 03 -> 04 -> 05 -> 11。
- 研究复现路径：12 -> 08 -> 07 -> 09。

## 验收方式

每个主题最终都要能落到四类产物：可运行代码、标准输入输出规范、失败案例和评测记录。只收集链接或只写概念不算完成。
