# 代表工作导读：SayCan、Code as Policies 与 VoxPoser

本节介绍"语言到技能"路线的三个经典锚点工作，帮助读者把本组前四页的方法论落到具体系统上：SayCan（LLM 打分 + 价值函数过滤技能）、Code as Policies（LLM 直接生成可执行策略代码）、VoxPoser（LLM+VLM 生成 3D value map 供运动规划器使用）。

## 需要覆盖

- SayCan：任务分解为技能序列，LLM 语义打分与 affordance 价值函数相乘选技能；论文与项目页 https://say-can.github.io/ 。
- Code as Policies：把技能接口暴露为 Python API，LLM 生成组合代码；https://code-as-policies.github.io/ 。
- VoxPoser：语言生成 affordance/constraint value map，接零样本轨迹合成；https://voxposer.github.io/ 。
- 三者与本组"指令到技能 / 技能接口 / 反馈纠错"页面的对应关系，以及与第 7 章端到端 VLA 路线的边界。
