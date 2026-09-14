# Policy Rollout + 人工修正

本页讲半自动采集:已有策略自行执行,人类只在快失败时用任意 teleop 设备介入修正,采到模型真实会遇到的 OOD 状态与失败恢复数据,对提升 closed-loop policy 很有帮助,衔接 DAgger / human-in-the-loop 微调与 10.10 真机 RL(HIL-SERL)。要写:需记录"哪些动作来自 policy、哪些来自 human"的字段;需已有可运行策略、安全风险更高,不适合最初入门。
