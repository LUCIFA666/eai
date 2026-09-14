# Articulation 关节体

上一页把机器人导成了 USD 资产，但“一堆 link 和 joint”还只是静态结构。要变成能读关节角、能被驱动的机器人对象，靠的是 Isaac Sim 的 **Articulation**。这一页带你认识它，并第一次读写、驱动一个关节体。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么说 articulation 不是一堆零件，而是一棵能驱动的关节树？
2. articulation root 是什么，怎么把一个 USD 机器人包装成可读写的关节体？
3. 怎么读取关节状态、又怎么给它发目标让 drive 驱动起来？

这一页写给已经把机器人导入 stage、会写 Python、想真正读到关节状态并让它动起来的读者。它延续前面“先启动、再 reset、才能读状态”的节奏，只是对象从方块换成了一整棵机器人关节树。

## articulation 不是一堆零件，是一棵能驱动的关节树

URDF / USD 里，机器人是一组 link（刚体）由 joint（关节）连接。**articulation** 是 PhysX / Isaac Sim 把这棵“关节树”整体当成**一个可读写、可驱动的机器人对象**来处理的方式：它把底层的 link、joint、drive 和物理状态包装起来，让你能用 `get_joint_positions()` 这类接口直接读写整台机器人。

一个类比：**散落一地的零件 vs 装配好、能驱动的机械臂**。同样是那些 link 和 joint，没被识别成 articulation 时，它们只是 stage 里互不相干的刚体；被识别成 articulation 后，它们才是一台能被一行代码驱动的机器人。

关节树有两种根：

| 基座类型 | 根是否固定 | 典型机器人 |
|---|---|---|
| 固定基座 | 根 link 固定在世界 | Franka、UR 等桌面机械臂 |
| 浮动基座 | 根 link 可自由移动 | 四足、人形、无人机 |

固定基座误设成浮动，机械臂会被重力拽下去；浮动基座误设成固定，四足永远跑不起来——这一点在上一页导入时的 `fix_base` 就要定好。

## articulation root

PhysX 靠一个叫 **articulation root** 的标记，来识别“从这个 prim 往下是一个关节体”。它就像整棵关节树的把手：抓对了，整台机器人作为一个 articulation 被驱动；抓错了或没有，Isaac Sim 就不认为这是关节体。

最常见的初学者报错就是 articulation root 没选对：

把 articulation 的 prim path 指到了某个中间 link 或纯 Xform，运行时会报类似 **“… is not an articulation”**，或者 `get_joint_positions()` 返回空、关节怎么都不动。正解是把路径指到带 articulation root 的 prim（导入器通常会自动加在机器人根上；自定义资产要确认它存在、且只有一个）。

## 读关节状态

Isaac Sim Core API 把机器人包装成 articulation 对象。最小用法如下（命名空间随版本，见末尾提醒）：

```python
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.robots import Robot
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.utils.nucleus import get_assets_root_path

world = World()
world.scene.add_default_ground_plane()

# 把一台内置 Franka 的 USD 引用进 stage 的 /World/Franka
assets_root = get_assets_root_path()
add_reference_to_stage(
    assets_root + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd",
    "/World/Franka",
)

# 再把它作为 articulation 包装成可读写的机器人对象
robot = world.scene.add(Robot(prim_path="/World/Franka", name="franka"))

world.reset()   # 关键：articulation 在 reset 后才真正初始化

print("dof_names =", list(robot.dof_names))
print("num_dof =", robot.num_dof)
print("joint_positions =", np.round(robot.get_joint_positions(), 3).tolist())
print("joint_velocities =", np.round(robot.get_joint_velocities(), 3).tolist())

simulation_app.close()
```

这段脚本的运行输出如下：

```text
dof_names = ['panda_joint1', 'panda_joint2', 'panda_joint3', 'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7', 'panda_finger_joint1', 'panda_finger_joint2']
num_dof = 9
joint_positions = [0.012, -0.57, 0.0, -2.81, 0.0, 3.037, 0.741, 0.0, 0.0]
joint_velocities = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
```

这段输出能确认几件事：Franka 是 **9 个 DOF**（7 个臂关节 `panda_joint1~7` + 2 个夹爪手指 `panda_finger_joint1/2`）；`joint_positions` 的顺序和 `dof_names` 一一对应；reset 后机器人停在默认姿态、没有运动，所以 `joint_velocities` 全是 0。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-franka-iso.png" alt="Isaac Sim headless 渲染的 Franka Panda" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">Franka Panda 加载后的渲染图。上面读到的 9 个关节，就是这台机器人身上的 7 个臂关节加 2 个夹爪手指。</figcaption>
</figure>

注意那行 `world.reset()`：和前面方块下落示例一样，**关节状态、DOF 信息都要在 reset 之后才可读**。reset 之前就 `get_joint_positions()`，常见结果是拿到空值或报错——不是机器人坏了，是物理还没初始化。

## 驱动一个关节体

让关节动有两种方式，初学者很容易混：

| 方式 | 做了什么 | 什么时候用 |
|---|---|---|
| `set_joint_positions(q)` | **瞬间改写**关节状态，绕过物理（teleport） | reset、摆初始姿态 |
| `apply_action(ArticulationAction(...))` | 给关节下**目标**，由 joint drive 经物理追踪 | 正常控制 |

```python
from isaacsim.core.utils.types import ArticulationAction

# 摆一个初始姿态（瞬间生效，不走物理）
target_q = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785, 0.04, 0.04])
robot.set_joint_positions(target_q)

# 正常控制：给关节位置目标，由 drive 把它拉过去
robot.apply_action(ArticulationAction(joint_positions=target_q))
for _ in range(120):
    world.step(render=False)
```

`set_joint_positions` 是“把机器人摆过去”，`apply_action` 是“让机器人自己走过去”。训练 / 控制时几乎总是用 `apply_action`；`set_joint_positions` 主要用于 reset 一个回合。至于关节能不能稳稳跟上目标，取决于 joint drive 的参数——那是 [下一页物理属性配置与检查](03-physics-audit.md) 的主题。

**版本提醒**：5.x Core API 在 `isaacsim.core.*` 命名空间（4.5 之前为 `omni.isaac.core.*`）。`Robot` / `Articulation` 的具体导入路径随版本略有差异，拿不准时先用 GUI 加载机器人、在 Script Editor 里试通，再脚本化。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 导入后马上能 `get_joint_positions()` | reset 前 articulation 没初始化 | 先 `world.reset()` 再读 |
| articulation 的 prim path 随便指 | 指错会报 “is not an articulation” | 指到 articulation root 所在 prim |
| `set_joint_positions` 就是控制 | 它瞬间改写、绕过物理 | 控制用 `apply_action` 经 drive |
| 关节不动 = articulation 坏了 | 常是没 `apply_action`、没 `step`，或 drive 太软 | 查动作、step、drive |
| joint 名和 body 名一样 | 是两套名字 | 分别打印 `dof_names` 和 body names |

## 小结

- articulation 把“link + joint”的关节树整体包装成可读写、可驱动的机器人对象。
- articulation root 是 PhysX 识别关节体的“把手”，选错会报 “is not an articulation”。
- 关节状态要在 `world.reset()` 之后才能读；`dof_names` / `num_dof` 帮你确认结构。
- `set_joint_positions` 是瞬间改写（reset 用），`apply_action` 是经 drive 的正常控制。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Core API Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/index.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Python Scripting and Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/index.html)

## 导航

- 返回目录：[机器人资产与物理配置](../03-robot-and-physics.md)
- 上一页：[URDF 到 USD：机器人资产转换](01-urdf-to-usd.md)
- 下一页：[物理属性配置与检查](03-physics-audit.md)
