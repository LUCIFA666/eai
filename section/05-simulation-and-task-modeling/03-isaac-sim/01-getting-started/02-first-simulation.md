# 第一次仿真

你已经知道 Isaac Sim 是平台而非单一物理引擎，现在要第一次让它真正动起来。如果读过 MuJoCo，可以把这一页理解成 Isaac Sim 版的“第一次跑通”：目标不是学完所有 API，而是先走完整条生命周期，并知道怎样判断环境和脚本都已经跑通。

## 本节目标

本节围绕下面几个问题展开：

1. 第一次运行要跑通哪条最小闭环？
2. 启动脚本、环境初始化和主循环的顺序为什么重要？
3. 日志、画面、checkpoint 或输出文件应该怎么看？
4. 如果第一次运行失败，应该先排查哪几个最常见原因？

## 跑一次仿真，就是走完一条生命周期

MuJoCo 的“第一次”几乎没有仪式感：import、读模型、`mj_step` 循环，三五行就动。Isaac Sim 不一样：它要先启动运行时，再搭好场景，再初始化物理，最后才开始步进渲染。少一步，要么直接报错，要么物体一动不动。

记牢这条生命周期，比记任何 API 都重要：

<figure class="doc-figure">
<p class="doc-figure-title">一次 Isaac Sim 仿真的生命周期</p>
<div class="figure-flow">
<div class="figure-node">from isaacsim import SimulationApp：拿到启动入口</div>
<div class="figure-node">SimulationApp(...)：启动 Kit 运行时</div>
<div class="figure-node">import isaacsim.core / omni.*：依赖运行时的模块要放在启动后</div>
<div class="figure-node">World()：建世界 / 舞台，并带上默认物理场景</div>
<div class="figure-node">add 地面 + 物体：布景</div>
<div class="figure-node">world.reset()：物理在这一刻才真正初始化</div>
<div class="figure-node">loop：world.step(render=True)：推进物理，可选渲染</div>
<div class="figure-node">simulation_app.close()：释放运行时，干净退出</div>
</div>
<p class="doc-figure-subtitle">顺序敏感：<code>isaacsim.core</code>、<code>isaacsim.sensors</code>、<code>omni.*</code> 这类依赖 Kit 运行时的模块要在 <code>SimulationApp(...)</code> 之后 import，物体状态必须在 reset 后才能读。</p>
</figure>

## 和 MuJoCo 的差异

| 对比 | MuJoCo | Isaac Sim |
|---|---|---|
| 第一步 | `import mujoco` 即用 | 必须先 `SimulationApp(...)` 启动 |
| import 顺序 | 随意 | 敏感：`core` 必须在运行时启动后 import |
| 用哪个 python | 系统 / conda | pip 安装用当前环境的 `python`；预编译包用自带 `python.sh` |
| 物理就绪 | `MjData(model)` 即可 | 必须 `world.reset()` 之后 |
| 步进 | `mujoco.mj_step(m, d)` | `world.step(render=True)` |
| 渲染 | 另起 viewer | `step(render=True)` 一并推进 |
| 启动 | 毫秒级 | 首次几十秒（编译 shader / 拉资源）|

一句话：MuJoCo 是一台计算器，按下就出数；Isaac Sim 是一个实验场，得先启动运行时、布好场景、初始化物理，机器才会动。

## 最小脚本

存成 `hello_isaac.py`：

```python
# 铁律：先从 isaacsim 拿到 SimulationApp 入口；SimulationApp 创建之后，
# 才 import 依赖 Kit 运行时的模块，例如 isaacsim.core、isaacsim.sensors、omni.*
# （课程锁定的 Isaac Sim 5.1.0 使用 isaacsim.* 命名空间；4.5 之前的版本使用 omni.isaac.*，4.5 起迁移到 isaacsim.*，见“安装与版本对照”）
from isaacsim import SimulationApp
simulation_app = SimulationApp({'headless': False})  # 无显示器 / 远程服务器改 True

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

cube = world.scene.add(
    DynamicCuboid(
        prim_path='/World/Cube',
        name='cube',
        position=np.array([0.0, 0.0, 1.0]),
        scale=np.array([0.5, 0.5, 0.5]),
        color=np.array([0.0, 0.0, 1.0]),
    )
)

world.reset()  # 物理在这里才真正初始化

for i in range(300):
    pos, _ = cube.get_world_pose()
    v = cube.get_linear_velocity()
    if i % 50 == 0:
        print(f'[step {i:3d}] z={pos[2]:.3f}  vz={v[2]:.3f}')
    world.step(render=True)

simulation_app.close()
```

运行时只记住一句话：**在哪个 Python 里装了 Isaac Sim，就用哪个 Python 跑脚本**。

如果按本部分《安装与版本对照》的 pip 流程安装，也就是已经创建并激活了 `isaacsim51` 环境，就这样运行：

```bash
conda activate isaacsim51
PYTHONNOUSERSITE=1 python hello_isaac.py
```

这里的 `python` 指的是当前 `isaacsim51` 环境里的 Python，不是系统自带的 `/usr/bin/python`，也不是 base 环境的 Python。

如果你用的是预编译包 / 工作站版，没有通过 pip 装到 conda 环境里，那么 Isaac Sim 会自带 Python 运行时。此时进入 Isaac Sim 安装目录后运行：

```bash
./python.sh hello_isaac.py
```

预期：弹窗里蓝方块从 1m 高下落、触地后静止；终端打印 z 从 ~1.0 递减、vz 由 0 变负。看到 z 在掉、vz 变负，就算跑通。

headless 怎么开：把参数改为 `{'headless': True}` 即可——无界面照样推进物理、出数据，适合服务器 / 远程。本页默认 `False` 只是为了第一次能直观看到方块下落。

## 运行输出

下面是一段 Isaac Sim 5.1.0 headless 运行输出。headless 模式不打开窗口，但物理过程和 GUI 模式一致；如果额外架设相机，也可以录下画面。

终端按 step 打印的 `z`（高度）和 `vz`（竖直速度）：

```text
=== free-fall cube : step / z(m) / vz(m/s) ===
[step   0] z=1.000  vz=-0.327
[step  15] z=0.591  vz=-2.780
[step  30] z=0.362  vz=0.253
[step  45] z=0.261  vz=0.024
[step  60] z=0.250  vz=0.046
[step  75] z=0.250  vz=0.046
[step  90] z=0.250  vz=0.046
[step 105] z=0.250  vz=0.046
```

录下来的画面（蓝方块从 1m 高下落、触地后停住）：

<figure class="doc-figure">
<video src="/section/05-simulation-and-task-modeling/assets/isaac-sim-freefall-cube.mp4" controls muted loop playsinline poster="/section/05-simulation-and-task-modeling/assets/isaac-sim-freefall-cube-last.png" style="max-width:100%;height:auto;display:block;margin:0.5em 0"></video>
<figcaption class="doc-figure-subtitle">Isaac Sim headless 录制：蓝方块自由下落到网格地面，触地后静止。</figcaption>
</figure>

怎么读这部分数字（这就是“跑通”的判据）：

- **`z` 从 1.000 一路降到 0.250 不再变**：方块边长 0.5m，落地后中心停在半个身位高（0.25m）——它真的落到地面并停住了。
- **`vz` 的轨迹是“下落 → 反弹 → 静止”**：step 15 到 −2.780（下落在加速），随后触地**弹了一下**——step 30 的 `vz=+0.253`、`z` 从 0.261 回跳到 0.362 就是这次反弹，再很快稳定下来。
- 一个容易看走眼的细节：静止后 `z` 牢牢停在 0.250，但 `vz` 不是干净的 0、而是一个 ~0.05 的小值且不再变化。这**不是**方块还在动（真有 0.046 m/s 的话，十几步就该升起约 1cm，而 `z` 纹丝不动），而是 PhysX 对**贴地静止刚体**报出的求解器残留速度——所以判断“停没停”要看 `z`，别只盯着 `vz`。
- 看到 **z 一路下掉、触地回弹、最后 z 稳定**，第一次仿真就算跑通了。

## 逐段拆

| 代码 | 角色 | 漏了会怎样 |
|---|---|---|
| `SimulationApp({...})` | 启动 Kit 运行时 | 后续 import 直接崩 |
| 运行时启动后 `import ...core` | 拿到操作世界的 API | 顺序错 → 报错 / 段错误 |
| `World(...)` | 建世界 + 默认物理场景 | 没有承载物体的舞台 |
| `add_default_ground_plane()` | 给一个地面 | 方块掉进虚空永远下落 |
| `DynamicCuboid(...)` | 带刚体 + 碰撞的动态体 | 用 `VisualCuboid` 只可见、不受力 |
| `world.reset()` | 初始化物理 | 物体不动、`get_*` 取不到值 |
| `world.step(render=True)` | 推进一帧物理并渲染 | 不调 = 冻结；`render=False` = 无画面 |
| `simulation_app.close()` | 收工：干净退出 | 进程残留 / 窗口卡死 |

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 装在 `isaacsim51`，却用 base / 系统 python 跑 | 当前 Python 里没有 Isaac Sim | 先 `conda activate isaacsim51`，再用 `PYTHONNOUSERSITE=1 python ...` |
| 用预编译包，却拿系统 python 跑 | 预编译包依赖自带运行时 | 进入安装目录后用 `./python.sh ...` |
| 先 import core 再启动 | import 依赖运行时已起 | `SimulationApp` 永远第一行 |
| 建完物体就能读状态 | 物理还没初始化 | 先 `world.reset()` |
| `while True` 就能动 | 不 step 不推进 | 必须循环 `world.step()` |
| 启动卡住了 | 在编译 shader / 拉资源 | 首次等几十秒正常 |
| 远程也能 `headless=False` | 无 X / 显卡起不来 | 远程用 `headless=True` |
| `VisualCuboid` 怎么不掉 | 它没有刚体 | 受力要用 `DynamicCuboid` |

## 小结

- “第一次跑通”本质是走完：启动 → 建世界 → 布景 → `reset` 初始化物理 → `step` 步进 → `close`。
- 三条最容易出错的铁律：`SimulationApp` 必须先创建、用安装了 Isaac Sim 的 Python、`reset` 后物理才就绪。
- 跑通判据：方块 z 递减、触地后稳定；远程 / 无显示器把 `headless` 改成 `True`。

## 参考资料

- NVIDIA Isaac Sim Documentation, Python Scripting and Tutorials. https://docs.isaacsim.omniverse.nvidia.com/latest/python_scripting/index.html
- NVIDIA Isaac Sim Documentation, Core API（World / Objects）. https://docs.isaacsim.omniverse.nvidia.com/latest/

## 导航

- 返回目录：[一、认识 Isaac Sim](../01-getting-started.md)
- 上一页：[Isaac Sim 是什么](01-what-is-isaac-sim.md)
- 下一页：[三个理解视角](03-three-mental-models.md)
