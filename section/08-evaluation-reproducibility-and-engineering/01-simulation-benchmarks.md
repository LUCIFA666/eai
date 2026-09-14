# 仿真 Benchmark

目标：把可批量运行、可用固定环境版本复跑的仿真 benchmark 放在同一个入口下，方便比较任务协议、主指标和失败证据。

## 收录范围

| 类型 | Benchmark |
|---|---|
| 导航 | OmniNavBench、Habitat Challenge、AI2-THOR / RoboTHOR、ALFRED / DialFRED、TEACh |
| 操作 | LIBERO、LIBERO Plus、Meta-World、CALVIN、RLBench、ManiSkill2 / ManiSkill3、SimplerEnv、VLABench、RoboTwin 2.0、RoboCasa / RoboCasa365、BEHAVIOR-1K、OmniGibson、VirtualHome、EBench、HumanoidBench、Isaac Lab-Arena |
| 记忆 | MIKASA、RoboMME、RoboMemArena、RoboHiMan |

世界模型相关 benchmark 不放在本节，统一放到第 10 章世界模型评测。RADAR 偏 fully autonomous real-world benchmark，不归入 8.1 仿真 Benchmark。

## 使用原则

- 先确认仿真器和环境版本，例如 SAPIEN、Isaac Gym、MuJoCo、CoppeliaSim 或 OmniGibson。
- 结果表必须保留 task/case 粒度，不能只给总平均。
- 失败证据至少包含视频、case result、seed 和主要 failure type。
