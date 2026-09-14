# TEACh

## 官方资源

| 资源 | 作用 |
| --- | --- |
| [TEACh Project Website](https://teachingalfred.github.io/) | TEACh 项目主页，包含论文、项目介绍、示例 episode 和相关入口 |
| [TEACh GitHub](https://github.com/alexa/teach) | TEACh 官方代码、数据下载、episode replay、inference 和 evaluation 工具 |
| [TEACh Paper](https://arxiv.org/abs/2110.00534) | TEACh 论文，介绍任务设置、数据采集、EDH / TfD / TATC benchmark 和实验结果 |
| [AI2-THOR](https://ai2thor.allenai.org/) | TEACh 使用的底层交互式室内仿真环境 |
| [TEACh AAAI Paper Page](https://ojs.aaai.org/index.php/AAAI/article/view/20097) | AAAI 论文页面，可用于确认正式发表信息 |
| [Dialog Acts for TEACh](https://arxiv.org/abs/2209.12953) | TEACh 对话行为标注扩展，用于分析任务型具身对话中的语言功能 |

## 推荐阅读顺序

| 页面 | 作用 |
| --- | --- |
| [概览与对话协议](05-TEACh-benchmark/01-overview-and-dialogue-protocol.md) | 理解 TEACh 是什么，以及它为什么把具身任务和自然语言对话结合起来 |
| [Commander / Follower 与任务数据](05-TEACh-benchmark/02-commander-follower-and-task-data.md) | 理解 Commander、Follower、game session、dialogue、action 和 state change 的关系 |
| [EDH、TfD 与 TATC Benchmark](05-TEACh-benchmark/03-edh-tfd-and-tatc-benchmarks.md) | 理解 TEACh 中三个核心 benchmark 的输入、输出和评测目标 |
| [环境配置、Replay 与视频生成](05-TEACh-benchmark/04-environment-setup-replay-and-video.md) | 理解如何安装 TEACh、下载数据、重放 episode，并生成示例视频 |
| [评测指标与结果分析](05-TEACh-benchmark/05-evaluation-metrics-and-result-analysis.md) | 理解任务成功率、goal-condition success、效率指标和常见失败类型 |

## 本节定位

TEACh 是一个面向对话式具身任务执行的 benchmark。它不是只给 agent 一条静态指令，而是让一个知道任务目标和部分环境线索的 Commander 与一个控制虚拟 agent 的 Follower 通过自然语言协作，在模拟家庭环境中完成任务。

可以把 TEACh 理解成：

```text
Commander 知道任务目标和环境线索
-> Follower 通过第一人称视角控制 agent
-> 双方通过自然语言对话协作
-> Follower 在 AI2-THOR 环境中导航和操作物体
-> 最终根据环境状态判断任务是否完成
```

TEACh 的重点不是单纯 ObjectNav，也不是单纯语言到动作序列，而是“对话如何帮助具身 agent 完成任务”。在任务执行过程中，Follower 可以询问物体位置、确认目标、报告失败或请求帮助；Commander 则可以提供方向、目标描述、纠错信息或替代方案。

本章按下面顺序展开：

```text
TEACh 总览
-> Commander / Follower 交互与数据结构
-> EDH、TfD、TATC 三类 benchmark
-> 环境配置、episode replay 和视频生成
-> 评测指标与结果分析
```

## 与前面几个 benchmark 的关系

TEACh 和前面几个 benchmark 的关系可以这样理解：

| Benchmark | 重点 | 适合理解什么 |
| --- | --- | --- |
| OmniNavBench | 通用导航、多任务组合、跨机器人形态 | 多种导航能力如何被统一评测 |
| Habitat Challenge | ObjectNav、ImageNav、Rearrangement 和 challenge 协议 | 具身导航和移动操作如何通过在线评测比较 |
| AI2-THOR / RoboTHOR | 室内交互环境、ObjectNav、sim-to-real | agent 如何在可交互房间中移动、观察和操作 |
| ALFRED / DialFRED | 语言指令、长程家庭任务、主动提问 | agent 如何将自然语言转化为长程动作序列 |
| TEACh | Commander / Follower 对话、EDH、TfD、TATC | 对话如何参与具身任务执行和错误修正 |

TEACh 可以看作是在 AI2-THOR / ALFRED 类家庭任务环境上进一步强调“人机协作对话”的 benchmark。它不仅关注 agent 是否能执行动作，还关注 agent 如何利用历史对话理解任务、恢复失败、请求帮助并完成家庭任务。

