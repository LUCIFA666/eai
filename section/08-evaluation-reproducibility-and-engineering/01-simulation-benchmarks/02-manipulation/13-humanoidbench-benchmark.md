# HumanoidBench

本节介绍 HumanoidBench：基于 MuJoCo 的人形机器人全身控制仿真 benchmark，覆盖 locomotion（walk / run / stairs 等）与 whole-body manipulation 两类任务，机器人本体为 Unitree H1 与 G1（带灵巧手）。后续详细页需要写清任务清单、观测与动作空间、成功判定与 return 口径、baseline（TD-MPC2 / DreamerV3 / SAC / PPO）结果和环境版本。

- 项目页：https://humanoid-bench.github.io/
- 代码：https://github.com/carlosferrazza/humanoid-bench
- 与第 9 章足式运动控制 RL 一节互为呼应：那边讲怎么训 locomotion policy，这里讲怎么评。
