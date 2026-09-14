# 关节控制基础

机器人进了场、物理也可信了。上一页已经把 `apply_action`、drive 和 `world.step()` 的边界拆清楚了。这一页把这件事真正用起来：给关节下一个目标，然后盯着它一步步移动到位——这是机器人第一次"按你的指令动起来"。

## 本节目标

本节围绕下面几个问题展开：

1. 给关节发「目标」到底发的是什么，最小控制循环怎么写？
2. 发完目标后，怎么让 drive 持续把关节追到位？
3. 怎么客观判断关节「真的动到目标」了，而不只是看起来动了？

阅读这一页前，最好已经能加载机器人、读到关节状态（见 [Articulation 关节体](../03-robot-and-physics/02-articulation.md)）。脚本用 Isaac Sim 5.1.0 的 `isaacsim.*` 接口，可直接在服务器上 headless 跑。

## 关节目标

让关节动，本质是给它一个**目标**，再由 drive（关节的虚拟执行器）把它执行出来。目标有三种，对应 `ArticulationAction` 的三个字段：

| 目标 | 字段 | 含义 | 适合 |
|---|---|---|---|
| 位置 | `joint_positions` | 关节要停到的角度 / 位移 | 机械臂关节、夹爪开合（**最常用**） |
| 速度 | `joint_velocities` | 关节要保持的转速 | 轮子、传送带、连续旋转 |
| 力矩 | `joint_efforts` | 直接施加的力 / 力矩 | 力控、扭矩级 RL 策略 |

一个类比：下目标像给司机出行指令——"停到这个位置"（位置）、"以这个速度开"（速度）、"踩这么大油门"（力矩）；而 drive 是车本身，负责把指令变成实际运动。上一页说过 `set_joint_positions` 是**瞬间改写**（teleport，reset 时用），`apply_action` 才是**经 drive 的正常控制**——这一页要让关节"自己走过去"，所以一律用 `apply_action`。

**入门先用位置目标。** 位置 drive 自带"弹簧 + 阻尼"，会替你把关节稳稳拉到角度并扛住重力；力矩目标则要你自己算重力补偿和动力学，难得多。等需要力控或扭矩级策略时再切力矩。drive 的 stiffness / damping / max force 怎么调，见 [物理属性配置与检查](../03-robot-and-physics/03-physics-audit.md)。

## 最小控制循环

让关节动起来的最小写法只有两步：发一次目标，然后**持续步进**让 drive 去追。

<figure class="doc-figure">
<p class="doc-figure-title">关节控制的最小循环</p>
<div class="figure-flow">
<div class="figure-node"><strong>① 发目标：</strong><code>apply_action(ArticulationAction(joint_positions=target))</code></div>
<div class="figure-node"><strong>② 步进：</strong>循环 <code>world.step()</code>，让物理推进、drive 施力</div>
<div class="figure-node"><strong>③ drive 追目标：</strong>关节被一步步拉向 target（不是瞬间到位）</div>
<div class="figure-node"><strong>④ 读状态确认：</strong><code>get_joint_positions()</code> 看误差是否收敛</div>
</div>
<p class="doc-figure-subtitle">关键在第②步：发一次目标不够，要持续 step，drive 才有时间把关节追到位。</p>
</figure>

存成 `joint_control.py`：

```python
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.robots import Robot
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.utils.nucleus import get_assets_root_path
from isaacsim.core.utils.types import ArticulationAction

world = World()
world.scene.add_default_ground_plane()
add_reference_to_stage(
    get_assets_root_path() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd",
    "/World/Franka",
)
robot = world.scene.add(Robot(prim_path="/World/Franka", name="franka"))
world.reset()                       # 关节要在 reset 之后才可读写

q0 = robot.get_joint_positions()
# 目标姿态：7 个臂关节 + 2 个夹爪手指
target = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785, 0.04, 0.04])
print("start q  =", [round(float(v), 3) for v in q0])
print("target q =", [round(float(v), 3) for v in target])

# 发一次位置目标，然后持续步进，让 drive 把关节追到目标
robot.apply_action(ArticulationAction(joint_positions=target))
for step in range(1, 181):
    world.step(render=False)
    if step in (1, 5, 15, 30, 60, 120, 180):
        q = robot.get_joint_positions()
        err = float(np.abs(q - target)[:7].max())          # 7 个臂关节的最大误差
        print("  step %3d: j2=%+.3f j4=%+.3f j6=%+.3f max_err=%.4f"
              % (step, q[1], q[3], q[5], err))

simulation_app.close()
```

运行：若按本单元《安装与版本对照》用 conda/pip 安装（isaacsim51 环境），直接 `python joint_control.py` 运行即可；二进制安装则用 Isaac 自带 python：

```bash
./python.sh joint_control.py
```

## 关节确实动到了目标

上面这段脚本把几个关键关节（j2 / j4 / j6）和 7 个臂关节的最大误差按步打印出来：

```text
start q  = [0.012, -0.57, 0.0, -2.81, 0.0, 3.037, 0.741, 0.0, 0.0]
target q = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785, 0.04, 0.04]
  step   1: j2=-0.586 j4=-2.793 j6=+2.994 max_err=1.4226
  step   5: j2=-0.642 j4=-2.670 j6=+2.835 max_err=1.2643
  step  15: j2=-0.722 j4=-2.493 j6=+2.422 max_err=0.8513
  step  30: j2=-0.766 j4=-2.396 j6=+1.854 max_err=0.2826
  step  60: j2=-0.782 j4=-2.361 j6=+1.594 max_err=0.0232
  step 120: j2=-0.783 j4=-2.358 j6=+1.573 max_err=0.0017
  step 180: j2=-0.783 j4=-2.358 j6=+1.573 max_err=0.0017
```

这部分数字把"发目标 → 关节动过去"的全过程说清楚了：

- **不是瞬间到位**：第 1 步发完目标，max_err 还有 1.42；关节是被 drive 一步步拉过去的。最明显的是 j6，从初值 `3.037` 一路降到 `1.573`（目标 `1.571`）。
- **几十步内收敛**：max_err 从 1.42 → 0.28（30 步）→ 0.023（60 步）→ 0.0017（120 步），到 120 步基本贴上目标。
- **收敛后停住**：120 步和 180 步读数完全一样，说明关节已经停在目标姿态、不再动——这正是位置 drive"拉到位再稳住"的表现。

下面是同一台 Franka 被连续驱动做往返运动的 headless 录制，直观看到"发关节目标 → 关节真的动起来"这件事：

<figure class="doc-figure">
<video src="/section/05-simulation-and-task-modeling/assets/isaac-sim-franka-motion.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.5em 0"></video>
<figcaption class="doc-figure-subtitle">Franka 关节被位置目标连续驱动来回扫掠。屏幕上看到的"动"，背后就是上面那种 apply_action + step + drive 追目标的循环在反复执行。</figcaption>
</figure>

## 怎么判断"真的动到位了"

不靠"看起来动了"，靠这三条对照：

- **`max_err` 持续下降并趋近 0**：说明关节在追上目标。如果误差卡在某个值不降，多半是目标越限位、或 drive 太软。
- **关节角逐个逼近 target 的对应值**：像 j6 `3.037 → 1.573` 那样，逐项对得上目标。
- **收敛后读数不再变 / 速度回到 0**：关节停稳，不是还在抖或还在漂。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| `apply_action` 发一次关节就到位 | drive 要靠多次 step 才追到 | 发目标后持续 `world.step()` |
| 发了目标却不动 | 用了 `set_*` 没用 `apply`、忘了 step、或 drive 太软 | 用 `apply_action` + step；软了查 drive |
| 关节会瞬间跳到目标 | 位置 drive 是逐步收敛的过程 | 看 `max_err` 一步步下降，不是一步到位 |
| 力矩控制和位置控制一样省心 | 力矩目标要自己扛重力、动力学 | 入门优先位置目标 |
| 目标值随便填 | 超关节限位会到不了或被截断 | 目标落在关节限位范围内 |
| 夹爪能当臂关节一起规划 | 夹爪是另一类 DOF | 夹爪单独给开合目标 |

## 小结

- 关节能下三种目标，包括位置（`joint_positions`，最常用）、速度、力矩；位置目标 + drive 是日常控制主力。
- 真正"动起来" = 发一次 `apply_action` 目标 + 持续 `world.step()`，让 drive 把关节追到位。
- 判据看 `max_err` 是否逐步收敛到 0、关节是否停稳，而不是"看起来动了"。
- 发了不动先查三件事：`set` / `apply` 用错、忘了 step、drive 太软（→ 物理属性配置与检查）。
- 下一页把"发关节目标"升级成"给末端一个空间目标"——靠 IK 与 RMPflow。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Core API Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/index.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Articulation Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_controllers.html)

## 导航

- 返回目录：[控制](../04-control.md)
- 上一页：[控制链路与 API 边界](01-control-stack.md)
- 下一页：[运动生成](03-motion-generation.md)
