# 足式运动控制强化学习

本节介绍四足与人形机器人运动控制（legged locomotion）的强化学习实战路线。这是具身智能 RL 落地最成功的方向，也是第 7 章 Loco-Manipulation VLA、第 11 章 Unitree G1 平台适配所默认存在的"底层运动控制器"的来源：VLA 输出的速度或步态指令，最终要交给一个 RL 训练出的 locomotion policy 去执行。

## 需要覆盖

- 任务建模：观测（本体感受 + 指令）、动作（关节位置目标 + PD）、奖励（速度跟踪、姿态、能耗、足端接触）、终止与课程设计。
- 主线方法：PPO + 大规模并行仿真 + 域随机化（legged_gym / Isaac Lab 路线）。
- 教师-学生蒸馏：特权观测教师到本体感受学生的两阶段训练（RMA 一族）。
- 风格与模仿：AMP 风格奖励、参考轨迹模仿在自然步态中的作用。
- 人形扩展：从四足到双足/人形的差异（接触序列、平衡、上肢协同），HumanoidBench 等评测入口（见第 8 章）。
- Sim2Real：执行器建模、延迟与滤波、摩擦随机化、真机部署检查单（与第 11 章衔接）。
- 实践产出：在 Isaac Lab 或 MuJoCo/MJX 中训练一个四足行走 policy，记录训练曲线、评测视频和域随机化配置。
- 参考实现：legged_gym https://github.com/leggedrobotics/legged_gym 、Isaac Lab https://github.com/isaac-sim/IsaacLab 、unitree_rl_gym https://github.com/unitreerobotics/unitree_rl_gym 。

## 本节边界

仿真平台的使用方法在第 5 章（Isaac Lab、MuJoCo），本节只讲 locomotion 任务本身的建模与训练；Loco-Manipulation 的 VLA 上层见第 7 章形态与模态扩展；真机部署与安全见第 11 章。
