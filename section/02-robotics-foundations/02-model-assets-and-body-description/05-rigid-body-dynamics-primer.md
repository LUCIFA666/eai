# 刚体动力学速览

本节介绍具身智能需要的最小刚体动力学概念：质量、质心、惯性张量的物理含义，动力学方程（Newton-Euler / Lagrangian）的直觉理解，以及这些量如何对应到 URDF `inertial`、MJCF `inertial`/`fullinertia` 等模型资产字段。目标不是完整推导，而是让读者在第 4 章全身控制（浮动基动力学）和第 5 章仿真建模（物理参数调校）之前，能解释"仿真器为什么需要这些参数、参数错了会发生什么"。

## 需要覆盖

- 质量、质心、惯性张量是什么，为什么惯性张量必须正定、主惯量满足三角不等式。
- 动力学方程 M(q)q̈ + C(q,q̇)q̇ + g(q) = τ 各项的直觉含义（不做完整推导）。
- 固定基与浮动基的差别，为什么足式机器人必须用浮动基建模。
- 这些量与 URDF `<inertial>`、MJCF `inertial` 字段的对应关系，以及常见错误（单位错、质心偏移、惯量过小导致仿真发散）。
- 参考：MuJoCo Computation 文档 https://mujoco.readthedocs.io/en/stable/computation/index.html 、Featherstone《Rigid Body Dynamics Algorithms》。
