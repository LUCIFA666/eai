# VLA 训练范式

本节介绍 VLA 的完整训练范式，把零散的训练方法串成一条主线：互联网图文与机器人数据的联合训练（web + robot co-training）、监督微调（SFT）、以及强化学习后训练（RL post-training）三个阶段。要讲的内容：RT-2 式 web+robot co-training（闭源，仅作里程碑概念）、OpenVLA 在 Open X-Embodiment 上的数据混合策略、online RL 微调的定位与取舍。参考实现：VLA-RL https://github.com/VLA-RL/VLA-RL （RL 后训练详见 [VLA 的 RL 后训练](06-vla-rl-posttraining.md)）。
