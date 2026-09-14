# World 与地面

本节分 4 页，这一页只拆最小场景里的第一块：为什么要先创建 `World`，为什么要加地面，以及它们和 USD Stage / PhysX 物理场景是什么关系。

## 本节目标

本节围绕下面几个问题展开：

1. `World` 在脚本里扮演什么角色，为什么它是操作仿真的入口？
2. 地面除了能看见，为什么还必须带碰撞？
3. 怎么用容器 Prim 把场景树整理整齐？

## `World` 是脚本操作仿真的入口

在 standalone 脚本里，`SimulationApp` 负责启动 Isaac Sim 运行时；`World` 则是后续操作场景和物理的入口。最小写法是：

```python
from isaacsim.core.api import World

world = World(stage_units_in_meters=1.0)
```

这里的 `stage_units_in_meters=1.0` 很重要：它约定 **1 个 stage unit 等于 1 米**。后面写 `position=[0, 0, 1]`，意思就是物体中心在 1 米高的位置，而不是 1 厘米、1 毫米或某个任意单位。

可以先把 `World` 理解成三件事的统一入口：

| 它管什么 | 你会怎么用 |
|---|---|
| USD Stage | 往 `/World/...` 下挂 Prim |
| 物理场景 | `reset()` 后让 PhysX 初始化刚体、碰撞、关节 |
| 对象注册表 | 用 `world.scene.add(...)` 加对象，用 `world.scene.get_object(name)` 取对象 |

## 地面不只是能看见，它也带碰撞

加默认地面：

```python
world.scene.add_default_ground_plane()
```

这一步做的不只是画一张网格地面。它还提供了一个物理碰撞平面，让动态物体能落在上面。如果没有地面，`DynamicCuboid` 会受重力一直往下掉，z 坐标会越来越小。

最小验证脚本里，方块最后能停在 `z=0.09` 或 `z=0.11` 这样的半身位高度，就是因为它底部碰到了地面。

下面这张图来自 Isaac Sim headless 运行后的对比：左边加了地面，方块被碰撞面托住；右边不加地面，同样步进 30 帧后，方块继续往下掉，物理读数已经到 `cube_z = -0.711`。

<figure>
  <img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-ground-vs-no-ground.png" alt="Isaac Sim 中有地面和没地面时方块运动结果的对比" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
  <figcaption class="doc-figure-subtitle">地面不是装饰网格，而是物理碰撞面。没有地面时，<code>DynamicCuboid</code> 仍然受重力，但没有任何东西能接住它。</figcaption>
</figure>

## 用容器 Prim 整理场景树

最小脚本里有这一行：

```python
from pxr import UsdGeom, Sdf

stage = omni.usd.get_context().get_stage()
UsdGeom.Xform.Define(stage, Sdf.Path("/World/Objects"))
```

`/World/Objects` 是一个空的 `Xform` Prim，可以把它理解成文件夹。它本身不参与物理，也不发光，只是用来分组：

```text
/World
  GroundPlane
  DistantLight
  DomeLight
  Objects
    RedBox
    GreenBox
    BlueBox
    Ball
```

（此处为简化示意，实际 prim 名为 defaultGroundPlane 且内含子层级。）

这样做的好处是：以后查找、隐藏、移动、批量删除物体时，路径更清楚。小脚本里可以不建容器，但一旦场景里有几十个物体，不分组会很快乱掉。

## 最小代码片段

```python
from isaacsim.core.api import World
import omni.usd
from pxr import UsdGeom, Sdf

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

stage = omni.usd.get_context().get_stage()
UsdGeom.Xform.Define(stage, Sdf.Path("/World/Objects"))
```

到这里，场景还没有物体，也没有灯光。它只是有了一个以米为单位的世界、一个可碰撞地面，以及一个准备挂物体的容器。

## 常见错误

| 现象 | 可能原因 | 检查点 |
|---|---|---|
| 物体一直往下掉 | 没有地面，或地面没参与碰撞 | 是否调用了 `add_default_ground_plane()` |
| 位置看起来尺度不对 | 单位没按米理解 | `stage_units_in_meters=1.0` 是否保留 |
| 后面按路径找不到物体 | Prim 路径和容器路径不一致 | 物体是否真的放在 `/World/Objects/...` |

## 小结

- `World` 是脚本操作 USD 场景和物理仿真的入口。
- `add_default_ground_plane()` 给物体一个可碰撞落脚点，不只是画网格。
- `/World/Objects` 这类 `Xform` Prim 是分组容器，能让场景树更清楚。

## 导航

- 返回目录：[搭一个场景](../02-build-a-scene.md)
- 下一页：[光源](02-lights.md)
