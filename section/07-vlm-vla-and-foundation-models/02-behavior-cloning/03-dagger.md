# DAgger

目标：理解 DAgger（Dataset Aggregation）如何通过交互式数据收集解决行为克隆的 covariate shift 问题。

标准行为克隆（BC）只用专家离线数据训练策略，但策略在部署时会遇到训练分布之外的状态——一旦偏离专家轨迹，后续误差会不断累积（covariate shift / compounding error）。DAgger 的核心思路是迭代式训练：每轮用当前策略在环境中 rollout 收集新状态，再由专家对这些新状态标注正确动作，将新数据聚合到训练集中重新训练策略。经过多轮迭代，策略逐渐覆盖自身会访问到的状态分布，从而缓解分布偏移。

DAgger 是一种**训练范式**而非特定网络结构，可以与 ACT、Diffusion Policy 等任意策略架构组合使用。

## 核心流程

1. 用专家数据训练初始策略
2. 用当前策略在环境中执行，收集策略实际访问的状态
3. 专家对这些状态标注正确动作
4. 将新标注数据聚合到训练集，重新训练策略
5. 重复 2-4 直到策略收敛

## 常见变体

- HG-DAgger：人类在线介入（human-gated），仅在策略表现差时切换到专家控制，降低专家标注负担
- EnsembleDAgger：用策略集成的不确定性决定何时请求专家，减少不必要查询
- ThriftyDAgger：结合不确定性和风险估计，在安全关键状态才请求专家介入

## 参考实现

imitation 库提供了 DAgger 及其变体的标准实现，基于 Stable-Baselines3 构建：

[https://github.com/HumanCompatibleAI/imitation](https://github.com/HumanCompatibleAI/imitation)
