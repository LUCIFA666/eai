# 调参与排错

仿真里看到机器人“在抖”“在飘”“穿模了”“滑落了”，每个现象往往对应一两个具体参数。这一页把前面几节出现的旋钮（kp / damping / friction / solref / timestep 等）按“现象 → 候选参数 → 验证手段”汇成一张速查表，让调参尽量从“凭感觉”回到“先定位、再验证”。

## 本节目标

本节按“现象 → 参数”来排错，回答几类问题：

1. 关节在震荡、过冲、跟不上目标，该调哪些参数？
2. 接触穿模、抖动、物体滑落，又该从哪里下手？
3. 仿真发散、出现 NaN，常见原因有哪些？
4. 怎么用 viewer 边改边看，快速验证一处改动？

## 现象 → 参数定位表

| 现象 | 可能原因（按优先级） | 验证方法 |
|---|---|---|
| 关节震荡（来回抖） | 1. kp 太大 / damping 太小<br>2. timestep 太大<br>3. actuator gainprm 太激进 | 减小 kp 或增大 damping；减半步长 |
| 关节到达目标很慢 | 1. kp 太小<br>2. actuator 的 ctrlrange 截断了目标值<br>3. 摩擦太大 | 增大 kp；检查 ctrlrange 和目标是否匹配 |
| 关节到了目标但有静差 | 1. 用的 motor（没有位置反馈）而不是 position<br>2. 位置伺服的 gainprm 不够 | 换 position actuator 或增大 gainprm |
| 接触穿模（geom 互相穿过） | 1. collision geom 没设置或设置不对<br>2. contype/conaffinity 排除了这对接触<br>3. timestep 太大 | 检查 collision geom 存在且 contype≠0；减小 solref timeconst（让接触更硬）；减半步长 |
| 物体在接触面上抖动 | 1. solref timeconst 太小（约束太硬）<br>2. timestep 太大<br>3. 积分器不适合 | 增大 solref timeconst；减半步长；换 IMPLICIT |
| 物体夹不住（滑落） | 1. friction[0] 太小<br>2. 夹持力不够（ctrl 太小）<br>3. collision geom 形状不合理 | 增大 friction[0]；增大 ctrl；检查碰撞几何 |
| 发散 / NaN | 1. timestep 太大<br>2. 模型初始化有问题（body 重叠）<br>3. 控制量过大 | 减半步长；检查初始 body 位置无重叠；检查 ctrl 范围 |
| 仿真似乎在"慢动作" | 1. 渲染和物理步数关系混乱<br>2. 计算机性能不足 | 确认每渲染帧对应的物理步数；用离屏渲染测纯物理速度 |

## 关节侧：振荡、过冲、跟踪迟滞

关节行为问题通常跟 actuator 的刚度（kp/gainprm）和阻尼（damping）有关。一个实用的小口诀：

- **振荡 → 加阻尼**（增大 damping 或减小 kp）。
- **太慢 → 加刚度**（增大 kp）。
- **到了目标但总是差一点点 → 检查 ctrlrange**，目标值可能被截断了。

如果用的是 Panda 自带的 `<general>` actuator，对应的参数是 `gainprm` 和 `biasprm`。改它们之前建议先备份原始值。Panda 的默认值往往是针对这个特定机器人调过的，盲改容易越调越糟。

## 接触侧：穿模、抖动、滑落

接触问题要分清楚是"根本没产生接触"还是"接触有但不正确"。

**诊断步骤：**

1. 先确认 collision geom 存在且 `contype` 不是 0。
2. 用 viewer 开启接触点可视化（`mjVIS_CONTACTPOINT`），看接触点是否出现在期望的位置。
3. 如果接触点太少或位置不对 → 检查 collision geom 的形状和位置。
4. 如果接触点多但物体仍在穿模 → 减小 `solref` 的 timeconst，或减小 timestep。
5. 如果接触正常但物体滑落 → 增大 `friction[0]`。

## 稳定性：发散与 NaN

仿真发散（状态向无穷大增长）通常表现为：

- 物体突然"飞"出场景。
- `qpos` 或 `qvel` 里出现 NaN。
- 控制台打印 `mjWARN_BADQACC` 警告。

比较常见的三个原因和对应处理：

1. **timestep 太大**：这往往是最高频的原因。把 `timestep` 减半试试，如果从 0.005 减到 0.002 就稳定了，说明之前确实偏激进。
2. **大质量比**：一个很轻的物体和一个很重的物体碰撞，轻的容易被"弹飞"。条件允许的话，尽量别让质量差超过 100:1，或者适当增大轻物体的质量。
3. **初始穿透**：模型加载时两个 geom 就已经重叠在一起，MuJoCo 会产生很大的排斥力把它们推开，导致数值不稳定。检查初始位姿，尽量确保没有 geom 重叠。

## 用 viewer 实时调试

交互式 viewer 往往是调参里比较顺手的工具。一个基本工作流：

1. 启动 viewer 加载模型：`python -m mujoco.viewer --mjcf=scene.xml`
2. 在另一个终端编辑 MJCF 文件（比如改 friction）。
3. 在 viewer 里按 `Ctrl+L` 热加载模型，不需要重启程序。
4. 观察行为变化，决定是保留还是继续调。

也可以在 Python 脚本里用 `launch_passive` 模式，一边运行仿真、一边修改 `model.opt` 或模型属性，实时看效果。这一用法会在观测与渲染部分展开。

## 小结

- 关节问题优先查 actuator 参数（kp/damping/gainprm）和 ctrlrange。
- 接触问题先确认 collision 几何正确，再用接触可视化看接触产生的位置。
- 发散最常见的原因是 timestep 太大，减半步长往往是第一反应。
- 热加载（`Ctrl+L`）让调参迭代很快，不用每次重启程序。

## 参考资料

- [MuJoCo Documentation: Computation（solver / integrator）](https://mujoco.readthedocs.io/en/stable/computation/index.html)
- [MuJoCo Documentation: Programming（调试与可视化）](https://mujoco.readthedocs.io/en/stable/programming/index.html)

## 导航

- 上一节：[摩擦与求解器参数](05-friction-and-solver.md)
- 返回上级：[控制与物理](../03-control-and-physics.md)
- 下一节：[动手：写一个 PD 控制器](07-hands-on-control.md)
