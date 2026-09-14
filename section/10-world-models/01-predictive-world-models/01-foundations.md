# 基础概念

目标：明确预测式世界模型的建模对象、训练信号和控制接口，避免和生成式世界模型、世界动作模型混淆。

预测式世界模型通常覆盖四个问题：

- **预测什么**：像素、低维状态、latent state、patch feature、joint embedding、reward、discount、terminal flag。
- **怎么预测**：RSSM / latent dynamics、Transformer dynamics、JEPA / feature prediction、decoder-free latent model。
- **怎么用来决策**：latent imagination actor-critic、CEM / MPPI / MPC、value-guided planning、goal-conditioned feature matching。
- **怎么验收**：不只看重建误差，还要看 rollout 稳定性、长期奖励预测、规划成功率、真实机器人样本效率和跨任务泛化。

写作时需要强调：预测式世界模型并不一定要重建图像。很多现代方法更关心任务相关 latent 或预训练视觉特征，因为像素级重建可能浪费容量，也未必提升控制效果。
