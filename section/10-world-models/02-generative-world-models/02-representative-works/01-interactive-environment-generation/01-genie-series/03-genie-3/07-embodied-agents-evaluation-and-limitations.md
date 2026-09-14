
# 具身智能体、评测与局限

## 本页目标

Genie 3 的重要目标之一，是为具身智能体提供多样、按需生成的环境。

本页重点介绍：

```text
SIMA 和 Genie 3 分别负责什么
智能体如何在生成世界中执行任务
SIMA 2 如何在未见世界中行动
生成环境如何用于自我改进
如何区分 Agent 失败和环境失败
Genie 3 当前有哪些限制
```

## 世界模型与智能体的分工

Genie 3 和 SIMA 是两个不同系统。

```text
SIMA：
观察画面、理解目标并选择动作

Genie 3：
根据动作模拟下一世界状态
```

交互循环为：

```text
用户提供任务
-> SIMA 读取当前画面
-> SIMA 输出动作
-> Genie 3 生成动作后的世界
-> SIMA 读取新画面
-> 持续执行
```

Genie 3 不知道 SIMA 的任务目标，只负责模拟动作之后的环境。

## 为什么需要生成式训练环境

传统 Agent 训练依赖：

```text
商业游戏
人工模拟器
真实机器人
固定 benchmark
```

这些环境数量有限，制作成本较高。

生成世界可以提供：

```text
新地图
新天气
新视觉风格
新角色
新障碍
新任务起点
```

有助于减少对固定环境的记忆和过拟合。

## SIMA 2 在新世界中行动

<video src="./assets/genie3-sima2-agent.mp4" controls width="100%"></video>

该视频来自 Google DeepMind 的 SIMA 2 官方演示，展示 SIMA 2 在 Genie 3 新生成且训练阶段未见的世界中理解指令、确定方向并采取动作。需要分别观察智能体决策和环境响应。任务成功不能单独证明世界模型或 Agent 已具备通用能力。

## SIMA 2 的作用

SIMA 2 能够：

```text
理解自然语言目标
分析当前画面
分解部分任务
选择键盘或鼠标动作
根据新观察继续决策
```

这些属于 SIMA 2 的能力，不属于 Genie 3 的内部模块。

## 在生成世界中自我改进

SIMA 2 官方研究还展示：

```text
Gemini 产生任务和估计反馈
-> Agent 在新世界中尝试
-> 保存自生成经验
-> 使用经验训练下一代 Agent
```

这可能减少持续人工演示的需要。

但它要求环境反馈足够可靠。

## 环境错误可能污染经验

如果 Genie 3 出现：

```text
目标物体消失
道路突然改变
动作没有正确响应
碰撞和运动不合理
```

Agent 可能把错误结果当成真实经验。

因此，训练前需要评价：

```text
环境可靠性
任务可完成性
动作响应
目标持续性
状态保持
```

## Agent 失败和环境失败

任务失败可能来自：

```text
Agent 没理解目标
Agent 选择错误动作
Genie 3 未正确响应动作
目标发生漂移
世界结构改变
任务变得不可完成
```

需要区分：

```text
Policy Failure
和
World Model Failure
```

否则无法判断应当改进哪一部分。

## 世界模型评测维度

| 维度 | 核心问题 |
| --- | --- |
| 视觉质量 | 画面是否清晰和连续 |
| 动作响应 | 动作是否及时改变环境 |
| 轨迹分叉 | 不同动作能否产生不同未来 |
| 长时一致性 | 回访区域是否保持 |
| 状态保持 | 用户造成的变化是否被记住 |
| 任务可完成性 | 目标是否持续存在且能够到达 |
| 可复现性 | 相同条件能否重复测试 |
| 物理可信度 | 运动和碰撞是否合理 |
| Agent 可用性 | 智能体能否持续观察和控制 |
| 安全性 | 是否可能生成有害内容 |

## 视觉质量不能替代可靠性

画面可能非常逼真，但如果：

```text
道路无法持续连接
目标随机消失
门不能稳定打开
角色控制延迟严重
```

它仍不适合训练或评测 Agent。

## 已知限制

### 动作空间有限

Promptable World Events 可以改变环境，但并不一定由 Agent 自身执行。

Agent 可以直接执行的动作范围仍然有限。

### 多智能体交互困难

复杂多角色互动需要维护每个主体的状态、目标、遮挡和接触关系，仍是开放问题。

### 现实地点不够准确

Street View Grounding 提供现实起点，但后续环境不是精确地图。

### 文本渲染有限

招牌、道路标识和界面文字仍可能变形。

### 交互时长有限

Genie 3 支持数分钟交互，而不是无限持续世界。

### 物理可信度有限

视觉上合理的水、车辆和碰撞，不等于精确动力学。

## 实验复现问题

生成模型具有随机性。

正式 benchmark 需要：

```text
固定初始条件
可重复动作序列
稳定目标
统一成功标准
环境有效性检查
```

否则不同 Agent 可能面对不同难度的世界。

## 责任与安全

开放世界生成可能带来：

```text
不适当内容
真实地点误导
版权和风格模仿
偏见角色和环境
高风险场景中的错误模拟
```

视觉逼真不等于真实证据。

## 与传统模拟器的关系

| 生成式世界模型 | 传统模拟器 |
| --- | --- |
| 快速生成大量视觉环境 | 状态和物理规则明确 |
| 可从文本和图像创建场景 | 场景通常人工制作 |
| 外观和风格多样 | 任务与奖励易验证 |
| 容易漂移和产生幻觉 | 长时间运行稳定 |
| 随机性较强 | 相同条件易复现 |
| 状态通常不可直接查询 | 可读取坐标、碰撞和奖励 |

更现实的发展方向可能是：

```text
生成模型提供场景和视觉多样性
+
传统模拟器提供物理、状态和任务约束
```

## 研究意义

Genie 3 将生成式世界模型推进到：

```text
实时交互
720p 输出
数分钟一致性
文本世界事件
具身智能体任务
用户可操作的世界创作原型
```

它连接了：

```text
视频生成
世界模拟
智能体学习
交互式内容创作
```

其价值不是已经替代传统模拟器，而是展示了一条新的环境构建路线。

## 本页小结

Genie 3 可以为 SIMA 和 SIMA 2 提供此前不存在的世界，并支持更长动作序列和自生成经验。

但任务失败可能同时来自 Agent 和环境模型。动作空间、多人互动、地理准确性、文字渲染、交互时长、物理可信度和实验复现仍是关键限制。

## 参考资料

- [Genie 3 官方介绍](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/)
- [Genie 模型页面](https://deepmind.google/models/genie/)
- [Genie Prompt Guide](https://deepmind.google/models/genie/prompt-guide/)
- [Project Genie](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/)
- [Project Genie 与 Street View](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie-expands/)
- [SIMA 2](https://deepmind.google/blog/sima-2-an-agent-that-plays-reasons-and-learns-with-you-in-virtual-3d-worlds/)

## 相关页面

- [返回 Genie 3 总览](../03-genie-3.md)
- [长时一致性与环境记忆](04-long-horizon-consistency-and-memory.md)
- [Promptable World Events](05-promptable-world-events.md)
- [Project Genie 与世界创作](06-project-genie-and-world-creation.md)
