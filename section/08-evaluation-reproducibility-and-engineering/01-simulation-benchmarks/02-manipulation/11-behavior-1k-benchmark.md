# BEHAVIOR-1K
BEHAVIOR-1K 更关注真实日常家务场景中的长程 embodied AI 任务。和 RLBench 这类桌面机械臂操作 benchmark 相比，它更强调复杂场景、丰富物体状态、任务目标描述和长程执行过程。
## 官方资源

| 资源 | 作用 |
| --- | --- |
| [BEHAVIOR-1K Official Website](https://behavior.stanford.edu/index.html) | 官方项目页，包含 benchmark 简介、任务特点和 challenge 入口 |
| [BEHAVIOR-1K GitHub](https://github.com/StanfordVL/BEHAVIOR-1K) | 官方代码仓库，包含 OmniGibson、BDDL、任务、安装和评测相关代码 |
| [BEHAVIOR-1K Paper](https://arxiv.org/abs/2403.09227) | 原始论文，介绍 benchmark 设计、任务来源、场景物体和仿真能力 |
| [Installation Guide](https://behavior.stanford.edu/getting_started/installation.html) | 官方安装说明，建议安装时优先参考 |
| [2025 BEHAVIOR Challenge](https://behavior.stanford.edu/challenge/index.html) | BEHAVIOR Challenge 页面，包含任务设置、规则和评测信息 |
| [Challenge Baselines](https://behavior.stanford.edu/challenge/baselines.html) | Challenge baseline 说明，包括 OpenVLA-OFT 等策略微调示例 |

## 推荐阅读顺序

| 页面 | 作用 |
| --- | --- |
| [概览与评测协议](11-behavior-1k-benchmark/01-overview-and-benchmark-protocol.md) | 理解 BEHAVIOR-1K 是什么、任务特点和评测方式 |
| [环境配置](11-behavior-1k-benchmark/02-env-setup.md) | 配置 BEHAVIOR-1K / OmniGibson 环境并完成 smoke test |
| [BDDL 任务定义](11-behavior-1k-benchmark/03-bddl-task-definition.md) | 理解任务如何用初始条件和目标条件描述 |
| [场景、物体与状态](11-behavior-1k-benchmark/04-scenes-objects-and-states.md) | 理解复杂场景、物体类别和 object states |
| [运行任务与观测空间](11-behavior-1k-benchmark/05-running-a-task-and-observation.md) | 学习如何 reset 任务、读取 observation 并执行 step |
| [Policy 评测](11-behavior-1k-benchmark/06-policy-evaluation-and-challenge.md) | 理解 policy 接入方式、评测指标和 Challenge baseline |

