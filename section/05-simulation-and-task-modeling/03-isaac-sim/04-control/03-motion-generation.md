# 运动生成

上一页你能给关节发目标了。但做任务时，你想说的通常不是"七个关节各转到多少度"，而是"把夹爪送到杯子上方"。从"末端要去哪"到"每个关节转多少"，中间隔着一层——这就是运动生成（motion generation）。这一页讲清楚这一层在做什么，以及 IK、RMPflow、全局规划各解决什么问题。

## 本节目标

本节围绕下面几个问题展开：

1. 运动生成怎么把「任务目标」翻译成一串关节动作？
2. IK 和 RMPflow 各自解决什么问题、该怎么选？
3. 怎么验证生成出来的关节目标可达、不自碰、够平滑？

阅读这一页前，最好已经会给关节发目标，并且想进一步让末端按空间目标移动。本页以概念和取舍为主，帮你建立"航点 / 方法 / 执行"的分层直觉，不要求你一次记住所有算法。

## 从任务目标到关节动作

"抓起杯子"这种任务，机器人并不能直接理解。常见做法是把它拆成一串**航点**（子目标），再让运动生成把每个航点变成关节能执行的动作：

<figure class="doc-figure">
<p class="doc-figure-title">从任务目标到物理执行：一条自上而下的链路</p>
<div class="figure-flow">
<div class="figure-node"><strong>任务目标：</strong>抓起杯子</div>
<div class="figure-node"><strong>航点 / 子目标：</strong>水平偏移接近 → 侧向逼近物体 → 下降至抓取高度 → 等待稳定 → 闭合夹爪 → 提升物体 → 完成</div>
<div class="figure-node"><strong>运动生成：</strong>IK / Trajectory / RMPflow / RRT / cuRobo —— 把末端目标变成关节动作</div>
<div class="figure-node"><strong>articulation action：</strong>关节位置 / 速度 / 力矩目标（上一页那一层）</div>
<div class="figure-node"><strong>joint drive → PhysX：</strong>drive 执行目标，物理引擎推进</div>
</div>
<p class="doc-figure-subtitle">航点是"想去哪"，运动生成是"怎么过去"，drive 是"实际执行"。</p>
</figure>

记住三句话，后面就不容易把这几层搞混：

```text
航点是目标。
IK / RMPflow / RRT / Trajectory 是去目标的方法。
Drive 是执行这些方法输出的关节目标。
```

这段动图展示了 pick 的每个航点：它不是展示"机器人动得很顺"，而是在展示一个 pick 任务怎样被拆成一串有语义的子目标。每个箭头和标签都对应一个阶段：水平偏移接近、侧向逼近物体、下降至抓取高度、等待稳定、闭合夹爪、提升物体，最后完成。屏幕上看到的是末端沿着这些 waypoint 走，背后执行的仍然是"末端空间目标 → IK / RMPflow → 关节动作 → drive"。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/assets/episode-ur16e-pick-beaker-waypoints.gif" alt="UR16e pick beaker 任务中的航点序列" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">UR16e pick beaker 航点序列：水平偏移接近、侧向逼近物体、下降至抓取高度、等待稳定、闭合夹爪、提升物体、完成。</figcaption>
</figure>

看这段动图时，重点不是记住某个具体坐标，而是看清航点的分工：

| GIF 阶段 | 航点含义 | 如果省略会怎样 |
|---|---|---|
| 阶段1：水平偏移接近 | 先从安全区域移动到物体附近 | 末端可能从不合适的方向直插目标 |
| 阶段2：侧向逼近物体 | 沿侧向靠近杯子，让夹爪进入可抓区域 | 夹爪容易离目标太远，后续下降对不准 |
| 阶段3：下降至抓取高度 | 把夹爪送到真正适合闭合的位置 | 高度不对时，夹爪会夹空或碰歪物体 |
| 阶段4：等待稳定 | 给机械臂、物体和接触前姿态一点稳定时间 | 还在晃动时闭合，抓取更容易失败 |
| 阶段5：闭合夹爪 | 执行夹持动作，让物体进入夹爪约束 | 没有闭合就抬起，物体不会被带走 |
| 阶段6：提升物体 | 把物体抬离桌面，验证抓取是否成立 | 只接触到物体，但没有完成 pick |
| 阶段7：完成 | 任务进入完成状态，可记录 success 或进入下一任务 | 缺少终止判断，数据里不知道这一回合是否成功 |

## IK

机械臂不能直接控制末端在空间里"飞"，它只能转关节。所以需要在两套坐标之间换算：

- **正运动学（FK）**：给定关节角 `q`，算末端在哪里。
- **逆运动学（IK）**：给定末端目标位姿 `x_target`，反求一组关节角 `q`，使 `FK(q) ≈ x_target`。

IK 对新手最容易造成"给个坐标机器人就该能去"的错觉。实际上它有几个绕不开的坑：

| 坑 | 表现 | 直觉 |
|---|---|---|
| 目标不可达 | 物体太远 / 太高 / 出工作空间 → 无解 | 手再长也够不到 |
| 位置可达、姿态难 | 位置在范围内，但强行要求夹爪竖直可能无解 | 够得到，但拧不成那个角度 |
| 多解跳变 | 同一目标有"肘上 / 肘下"多组解，可能突然甩一下 | 没约束就乱选一个解 |
| 解 ≠ 安全路径 | IK 只保证终点能到，不保证过程不撞桌 / 撞自己 | 终点合法不代表一路平安 |
| 奇异位形 | 接近奇异时末端动一点、关节要动很大 | 看着"抽一下"，其实是解跳了分支 |

所以实际工程里常给 IK 加保护：用当前关节角做 warm start（让解靠近当前姿态）、限制每步关节变化量、放宽姿态约束、先到安全接近航点再下降、IK 失败时退回 RMPflow。

6 轴和 7 轴机械臂的差别也值得知道：一个完整末端位姿是 6 个约束（位置 3 + 姿态 3）。6 自由度机械臂面对它"刚好够用"，余量很小；7 自由度多一个冗余自由度，可以在保持末端位姿不变的前提下调整肘部、远离限位、绕开障碍——更从容，但"解不唯一"也意味着算法必须知道偏好什么。

## RMPflow

IK 像一个**瞬时求解器**：给一个目标，返回一组关节角，不天然管轨迹平滑，也不天然处理动态障碍。RMPflow 则像一个**连续运动策略**：你给末端目标，它根据当前关节状态、末端 frame、关节限制、碰撞球和障碍物，每一帧持续输出"下一小步该怎么动"。

一个直观区别：

```text
IK：    这个末端目标，有没有一组关节角能到？
RMPflow：从现在开始，每一帧怎么动过去比较稳？
```

所以 RMPflow 适合跟随移动目标、动态更新障碍、做局部避障和连续控制。它的使用链路大致是：

```python
from isaacsim.robot_motion.motion_generation import RmpFlow, ArticulationMotionPolicy

rmpflow = RmpFlow(
    robot_description_path=cfg_dir + "/franka/rmpflow/robot_descriptor.yaml",
    urdf_path=cfg_dir + "/franka/lula_franka_gen.urdf",
    rmpflow_config_path=cfg_dir + "/franka/rmpflow/franka_rmpflow_common.yaml",
    end_effector_frame_name="right_gripper",
    maximum_substep_size=0.00334,
)
policy = ArticulationMotionPolicy(articulation, rmpflow)

for _ in range(500):
    pos, ori = target.get_world_pose()
    rmpflow.set_end_effector_target(pos, ori)   # ① 每帧设末端目标
    rmpflow.update_world()                       # ② 刷新障碍状态
    action = policy.get_next_articulation_action(physics_dt)  # ③ 生成下一步动作
    articulation.apply_action(action)            # ④ 交给 drive 执行
    world.step(render=True)
```

**这是概念示例。** RMPflow 依赖一套配置文件（`robot_description.yaml` / URDF / `rmpflow_config.yaml` / 碰撞球），官方支持的机器人（如 Franka）在 `isaacsim.robot_motion.motion_generation` 的 `motion_policy_configs` 里自带；换新机器人就要自己准备。RMPflow 最常踩的坑往往不在算法，而在"配置和场景对不上"：URDF 关节名与 USD articulation 不一致、end-effector frame 配错、base pose 没同步、碰撞球太大 / 太小、障碍没 `update_world()`。

## 方法选择

新手不必一开始掌握所有算法，但要知道它们解决的问题不同：

| 方法 | 输入 | 输出 | 适合 |
|---|---|---|---|
| IK | 末端目标位姿 | 一组关节角 | 目标附近、一步求解、简单到位 |
| Trajectory | 关节 / 任务空间路径点 | 带时间的轨迹 | 已知路径、要平滑执行 |
| RMPflow | 末端目标 + 机器人状态 + 动态障碍 | 连续的关节 action | 实时跟随、局部避障、反应式控制 |
| RRT / 路径规划 | 起点、终点、静态障碍 | 一条全局路径 | 绕过复杂静态障碍 |
| cuRobo / cuMotion | 批量 IK、碰撞约束、mesh | 高性能规划 / 控制 | 大规模、GPU 加速、复杂碰撞 |

做简单 pick 演示，IK 或 RMPflow 往往够用；柜门、狭窄通道、桌面障碍多的任务，可能要全局规划；大规模并行或复杂 mesh 碰撞，才考虑 cuRobo / cuMotion。RMPflow 擅长在目标附近平滑调整，但它是局部反应式的，不是全局搜索器——目标藏在障碍物后面、需要先绕到另一侧时，单靠它可能陷入局部行为，这时要先用 RRT 找路、再用轨迹和底层控制执行。

## 问题在运动生成还是 drive？

运动生成层和 drive 层经常被混在一起。一个实用的分层判断：

```text
生成的目标本身就绕 / 偏 / 撞：查 RMPflow / IK / end-effector frame / 碰撞球。
目标合理，但关节执行慢 / 软 / 抖 / 无力：查 drive 增益 / max force / 控制模式。
运动和执行都合理，但接触结果不对：查 collision / 物理材质 / 摩擦 / 质量。
```

也就是说，RMPflow 不是"替你调好一切"的万能按钮：它负责产生合理动作，drive 负责执行动作，碰撞体 / 摩擦 / 质量决定动作落到物理世界后会发生什么。任务失败时，要沿这条链一层层查，而不是只盯着"规划器是不是不行"。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 给个坐标 IK 就一定能到 | 可能不可达 / 姿态难 / 无解 | 先判断目标是否在工作空间、放宽姿态 |
| IK 解出来路径就安全 | IK 只管终点，不管过程碰撞 | 配航点 / 轨迹 / 避障，别一步求解到底 |
| RMPflow 能做全局绕障 | 它是局部反应式 | 复杂绕行先用 RRT 等全局规划 |
| 导入了机器人 RMPflow 就能用 | USD 资产 ≠ 运动生成配置 | 还要准备 URDF / description / 碰撞球 |
| 末端抽一下是 drive 坏了 | 常是 IK 在奇异附近跳解 | 查目标姿态、奇异、warm start |
| 7 轴一定比 6 轴好控 | 冗余带来"解不唯一" | 7 轴更灵活但要告诉算法偏好什么 |

## 小结

- 任务 → 航点 → 运动生成 → articulation action → drive → PhysX：运动生成是"把末端目标翻译成关节动作"的那一层。
- IK 是瞬时求解器，有不可达 / 多解 / 解非安全路径 / 奇异等坑，工程上要加 warm start、限步长、放宽姿态等保护。
- RMPflow 是连续反应式策略，适合实时跟随与局部避障；全局绕障靠 RRT 等规划器。
- 排查要分层：目标绕偏查运动生成，执行软抖查 drive，接触不对查物理。
- 下一页回到工程排查：机器人不动、抖动、末端偏移时，先判断问题在哪一层。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Motion Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/motion_generation_overview.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [RMPflow](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/concepts/rmpflow.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Configuring RMPflow for a New Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_configure_rmpflow_denso.html)

## 导航

- 返回目录：[控制](../04-control.md)
- 上一页：[关节控制基础](02-joint-control.md)
- 下一页：[控制排查](04-control-debugging.md)
