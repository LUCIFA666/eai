# 模型代码流程

本页集中介绍 SimpleVLA-RL 的三个核心模块——Trainer、Rollout、Actor——如何串成一次完整的训练闭环。建议先读本页建立主线，再进入三个子页看具体代码。

主线：`SFT checkpoint -> RayTrainer -> rollout 环境交互 -> complete/finish_step -> token reward -> GRPO advantage -> PPO clipped update`。

## 子页

- [Trainer 与 Reward](04-model-code-flow/01-trainer-reward.md)：`main_ppo.py`、`RobRewardManager`、`RayTrainer.fit()`，以及训练主循环如何组织 rollout、reward、advantage 和 update。
- [Rollout 与环境交互](04-model-code-flow/02-rollout-env.md)：LIBERO/RoboTwin 环境、Observation、VLA 输入、action 生成和 trajectory 收集。
- [Actor 与策略优化](04-model-code-flow/03-actor-policy.md)：FSDP worker、OpenVLA/OpenVLA-OFT、old logprob、PPO loss 和 checkpoint 保存。

- 返回上级：[SimpleVLA-RL](../04-simplevla-rl.md)
