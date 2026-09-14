# 搭一个场景

上一页你知道了场景是一棵 USD 树。这一页先给出一个可以直接跑的最小场景：一块地面、两盏灯、几个物体，然后让它们在重力下落到地面静止。跑完你会得到一张渲染图和一组坐标读数，这就是“搭对了”的证据。

## 本节目标

本节围绕下面几个问题展开：

1. 一个最小可跑场景由哪「四件套」组成？
2. 这段最小脚本怎么从世界、地面、灯光一步步搭到物体落地？
3. 怎么判断场景「搭对了」，又该往哪几页继续深入拆解？

这一页写给已经理解 Stage / Prim / prim path、想第一次自己搭场景的读者。脚本用 Isaac Sim 5.1.0 的 `isaacsim.*` 接口，可在 GUI 或 headless 模式下运行。这里不把每个 API 都展开到最细；更细的拆解放在本页下面四个子页里。

## 四件套

MuJoCo 里写完 MJCF 就有完整场景。Isaac Sim 要你自己一件件挂上去，少一件就出问题。最小一个能看、能仿真的场景，需要四样：

<figure class="doc-figure">
<p class="doc-figure-title">搭一个最小场景：四件套，缺一件就出问题</p>
<div class="figure-flow">
<div class="figure-node"><strong>① 世界 + 地面：</strong><code>World()</code> 带默认物理场景，<code>add_default_ground_plane()</code> 给物体一个落脚点（没地面 → 永远下落）</div>
<div class="figure-node"><strong>② 灯光：</strong>headless 下必须自己加 DistantLight / DomeLight（不加 → 画面全黑）</div>
<div class="figure-node"><strong>③ 物体：</strong>往树上挂 <code>DynamicCuboid</code> / <code>DynamicSphere</code>（带刚体 + 碰撞，会受力）</div>
<div class="figure-node"><strong>④ 初始化 + 步进：</strong><code>world.reset()</code> 初始化物理，循环 <code>world.step()</code> 推进</div>
</div>
<p class="doc-figure-subtitle">这正是上一部分生命周期（启动 → 建世界 → 布景 → reset → step）的"布景"环节。</p>
</figure>

## 继续拆读

这段脚本其实分成四个小问题，建议按下面顺序读：

| 子页 | 解决的问题 | 重点 |
|---|---|---|
| [World 与地面](02-build-a-scene/01-world-and-ground.md) | `World()`、Stage、地面分别负责什么？ | 默认物理场景、地面碰撞、场景根节点 |
| [光源](02-build-a-scene/02-lights.md) | DistantLight / DomeLight / SphereLight 怎么选？能不能放到指定 xyz？ | 主光、环境光、局部光、强度与位置 |
| [动态物体](02-build-a-scene/03-dynamic-objects.md) | `DynamicCuboid` / `DynamicSphere` 的参数怎么理解？ | `prim_path`、`name`、`position`、`scale`、`radius`、`color` |
| [运行与验证](02-build-a-scene/04-run-and-verify.md) | 怎么判断场景真的搭对了？ | `reset`、`step`、z 坐标、半身位 / 半径 |

## 最小可跑脚本

存成 `build_a_scene.py`。如果你只想先跑通，不必马上理解每一行；后面四个子页会逐段拆开：

```python
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})   # 远程 / 无显示器用 True

import numpy as np
import omni.usd
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid, DynamicSphere
from pxr import UsdGeom, UsdLux, Sdf

# ① 世界 + 地面
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

# ② headless 渲染要自己加灯，否则 RGB 画面可能全黑
stage = omni.usd.get_context().get_stage()
UsdGeom.Xform.Define(stage, Sdf.Path("/World/Objects"))   # 物体容器，方便分组
UsdLux.DistantLight.Define(stage, Sdf.Path("/World/DistantLight")).CreateIntensityAttr(2500.0)
UsdLux.DomeLight.Define(stage, Sdf.Path("/World/DomeLight")).CreateIntensityAttr(900.0)

# ③ 往 /World/Objects 下挂物体（注意：color 是 0~1，不是 0~255！）
world.scene.add(DynamicCuboid(
    prim_path="/World/Objects/RedBox", name="red_box",
    position=np.array([0.35, 0.25, 0.30]), scale=np.array([0.18, 0.18, 0.18]),
    color=np.array([0.90, 0.20, 0.20])))
world.scene.add(DynamicCuboid(
    prim_path="/World/Objects/GreenBox", name="green_box",
    position=np.array([-0.05, -0.30, 0.30]), scale=np.array([0.22, 0.22, 0.22]),
    color=np.array([0.20, 0.75, 0.30])))
world.scene.add(DynamicCuboid(
    prim_path="/World/Objects/BlueBox", name="blue_box",
    position=np.array([-0.40, 0.20, 0.30]), scale=np.array([0.16, 0.16, 0.16]),
    color=np.array([0.20, 0.40, 1.00])))
world.scene.add(DynamicSphere(
    prim_path="/World/Objects/Ball", name="ball",
    position=np.array([0.20, -0.02, 0.40]), radius=0.12,
    color=np.array([1.00, 0.85, 0.10])))

# ④ 初始化物理，再步进让物体落到地面
world.reset()
for _ in range(120):
    world.step(render=True)

for nm in ["red_box", "green_box", "blue_box", "ball"]:
    pos, _ = world.scene.get_object(nm).get_world_pose()
    print(nm, "->", np.round(pos, 3))

simulation_app.close()
```

如果按前面 pip 流程安装在 `isaacsim51` 环境里，运行：

```bash
conda activate isaacsim51
PYTHONNOUSERSITE=1 python build_a_scene.py
```

如果你用的是 NVIDIA 预编译包 / 工作站版，则进入 Isaac Sim 安装目录后运行 `./python.sh build_a_scene.py`。

## 运行结果

上面这段脚本运行后，画面应当是：网格地面上落着红、绿、蓝三个方块和一个黄球，光照、阴影都正常。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-built-scene.png" alt="搭出来的最小场景：网格地面 + 红绿蓝方块 + 黄球" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">地面 + DistantLight/DomeLight + 三个 DynamicCuboid + 一个 DynamicSphere，reset 后步进落地。</figcaption>
</figure>

终端打印的落稳后坐标（单位是米）：

```text
red_box   -> [ 0.35   0.252  0.09 ]
green_box -> [-0.055 -0.295  0.11 ]
blue_box  -> [-0.403  0.202  0.08 ]
ball      -> [ 0.2   -0.02   0.12 ]
```

## 怎么判断"搭对了"

不靠感觉，靠这两条对照：

- **画面里看得见地面和物体、有阴影** → 灯加对了，没掉进 headless 黑场。
- **每个物体的 z 落到"半个身位 / 一个半径"高**：方块边长 0.18 → 落地后中心 z≈0.09；边长 0.22 → z≈0.11；球半径 0.12 → z≈0.12。数字和上面的运行读数对得上，说明物理、地面、单位（米）都正确，物体已经落地静止。

x、y 几乎没变（只有微小抖动），是因为它们只是竖直下落、没有水平受力——这也间接说明初始位置就是你写进 `position` 的那串数字。

## 逐项拆

| 代码 | 在搭什么 | 漏了 / 写错会怎样 |
|---|---|---|
| `World(stage_units_in_meters=1.0)` | 世界 + 默认物理场景，单位定为米 | 没有承载物体的舞台 |
| `add_default_ground_plane()` | 地面（含碰撞面） | 物体掉进虚空一直下落 |
| `UsdGeom.Xform.Define(.../Objects)` | 一个空容器，给物体分组 | 不致命，但树会乱、不好寻址 |
| `DistantLight` / `DomeLight` | 平行光 + 环境光 | **headless 画面全黑** |
| `DynamicCuboid` / `DynamicSphere` | 带刚体 + 碰撞的物体 | 用 `Visual*` 只可见、不受力 |
| `color=[0.9, 0.2, 0.2]` | RGB，范围 **0~1** | 写 `[230,50,50]` 会被裁成白色 |
| `world.reset()` | 初始化物理 | 物体不动、`get_*` 取不到值 |
| `world.step(render=True)` | 推进一帧物理 + 渲染 | 不调 = 冻结；落不下来 |

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 不加灯也能渲染 | headless 没有默认光源 | 自己加 DistantLight / DomeLight |
| 颜色写 0~255 | Isaac core 的 `color` 是 0~1 | `[0.9,0.2,0.2]` 而不是 `[230,50,50]` |
| 建完物体就能读坐标 | 物理还没初始化 | 先 `world.reset()` 再 `get_world_pose()` |
| 加了物体它就该落地 | 没 step 不推进物理 | 循环 `world.step()` |
| 两个物体同名同路径 | 后者覆盖前者 | 每个 `prim_path` / `name` 唯一 |
| `scale` 就是最终尺寸 | 立方体是边长缩放、球用 `radius` | 看清每种形状的尺寸参数 |

## 小结

- 一个最小场景的"四件套"：世界 + 地面、灯光、物体、reset + step，缺一件就黑屏 / 落空 / 不动。
- headless 渲染通常要自己加灯；物体颜色是 0~1；读坐标前必须先 `reset()`。
- "搭对了"的判据：画面有地面 + 物体 + 阴影，且每个物体 z 落到半身位 / 一个半径高。
- 下一页把这套场景里反复出现的坐标和单位说清楚，免得位姿和尺度埋雷。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Core API（World / Objects）](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Python Scripting and Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/index.html)

## 导航

- 返回目录：[场景构建与坐标约定](../02-building-a-world.md)
- 上一页：[USD、Stage 与 Prim](01-usd-stage-prim.md)
- 下一页：[坐标系与单位](03-frames-and-units.md)
