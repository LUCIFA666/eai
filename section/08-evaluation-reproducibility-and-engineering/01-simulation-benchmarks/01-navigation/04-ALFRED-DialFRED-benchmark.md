# ALFRED / DialFRED

ALFRED 是一个面向语言指令驱动家庭任务的 embodied AI benchmark。它要求 agent 根据自然语言目标、分步指令和第一人称视觉观测，在 AI2-THOR 室内环境中完成长程任务。

## 官方资源

| 资源 | 作用 |
| --- | --- |
| [ALFRED Project Website](https://askforalfred.com/) | ALFRED 官方主页，包含论文、代码、数据、leaderboard 和 Data Explorer |
| [ALFRED GitHub](https://github.com/askforalfred/alfred) | ALFRED 代码、数据下载、模型训练和评测说明 |
| [ALFRED Data README](https://github.com/askforalfred/alfred/blob/master/data/README.md) | 数据结构、trajectory JSON、视频、图像和 annotation 说明 |
| [AI2-THOR](https://ai2thor.allenai.org/) | ALFRED 使用的交互式室内仿真环境 |
| [DialFRED GitHub](https://github.com/xfgao/DialFRED) | DialFRED 代码、数据处理和对话扩展说明 |
| [DialFRED Paper](https://arxiv.org/abs/2202.13330) | DialFRED 论文，介绍 dialogue-enabled embodied instruction following |
| [DialFRED Challenge](https://eval.ai/web/challenges/challenge-page/1859/overview) | DialFRED EvalAI challenge 页面 |

## 推荐阅读顺序

| 页面 | 作用 |
| --- | --- |
| [概览与评测协议](04-ALFRED-DialFRED-benchmark/01-overview-and-benchmark-protocol.md) | 理解 ALFRED 是什么，以及它为什么是语言驱动长程家庭任务 benchmark |
| [任务结构、语言指令与动作序列](04-ALFRED-DialFRED-benchmark/02-task-structure-instructions-and-actions.md) | 理解 ALFRED 中的任务类型、自然语言指令、专家动作和子目标 |
| [环境配置与数据准备](04-ALFRED-DialFRED-benchmark/03-environment-setup-and-data-preparation.md) | 理解 ALFRED 如何依赖 AI2-THOR、如何下载数据和准备基本运行环境 |
| [DialFRED：对话式指令扩展](04-ALFRED-DialFRED-benchmark/04-dialfred-dialogue-extension.md) | 理解 DialFRED 如何在 ALFRED 基础上加入主动提问和用户回答 |
| [评测指标与结果分析](04-ALFRED-DialFRED-benchmark/05-evaluation-metrics-and-result-analysis.md) | 理解任务成功率、子目标成功率、路径长度、交互失败类型和对话设置下的结果分析 |


## 与前面几个 benchmark 的关系

和前面几个 navigation benchmark 相比，ALFRED / DialFRED 的重点更加偏向语言指令驱动的长程家庭任务。

| Benchmark           | 重点                                       | 适合理解什么                         |
| ------------------- | ---------------------------------------- | ------------------------------ |
| OmniNavBench        | 通用导航、多任务组合、跨机器人形态                        | 多种导航能力如何被组织到统一评测中              |
| Habitat Challenge   | ObjectNav、ImageNav、Rearrangement 和在线评测协议 | 具身导航与移动操作任务如何通过 challenge 形式评测 |
| AI2-THOR / RoboTHOR | 室内交互环境、ObjectNav、sim-to-real             | agent 如何在可交互房间中移动、观察和操作物体      |
| ALFRED / DialFRED   | 语言指令、长程家庭任务、对话式信息获取                      | agent 如何把自然语言转化为连续动作序列         |

因此，ALFRED 可以看作是在 AI2-THOR 环境基础上进一步构造的语言任务 benchmark。它不只是让 agent 在房间里移动或寻找物体，而是要求 agent 根据自然语言完成一串有顺序的家庭任务。DialFRED 则进一步加入对话能力，使 agent 可以在信息不足时主动提问。
