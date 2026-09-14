# 动态物体

本节分 4 页，这一页拆最小场景里的物体部分。目标不是列完所有几何体，而是先把 `DynamicCuboid`、`DynamicSphere` 和第一次必遇到的参数说清楚。

## 本节目标

本节围绕下面几个问题展开：

1. 动态体和可视体有什么区别，分别在什么时候用？
2. `prim_path` 和 `name` 各自是什么，位置为什么按中心点而不是底面算？
3. 添加物体时，颜色取值、初始高度这些地方有哪些常见坑？

## 动态体和可视体的区别

如果想让物体受重力、会碰撞、能落地，使用 `Dynamic*`：

```python
from isaacsim.core.api.objects import DynamicCuboid, DynamicSphere
```

`DynamicCuboid` / `DynamicSphere` 会带上刚体和碰撞属性。相反，`VisualCuboid` 这类对象只负责显示外观，不参与物理。它会被看见，但不会因为重力下落。

| 需求 | 用什么 |
|---|---|
| 只想画一个标记 / 装饰物 | `VisualCuboid` / `VisualSphere` |
| 想让物体掉落、碰撞、被推动 | `DynamicCuboid` / `DynamicSphere` |

下面这张图来自 Isaac Sim headless 运行后的同场景对比：左边的视觉方块只负责显示外观，不会因为重力下落；右边的动态方块参与物理，步进后落到地面上。

<figure>
  <img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-dynamic-vs-visual.png" alt="Isaac Sim 中 VisualCuboid 和 DynamicCuboid 的物理行为对比" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
  <figcaption class="doc-figure-subtitle">这张图沿用前面页面的 Isaac Sim 运行结果：左侧橙色 <code>VisualCuboid</code> 仍悬在空中，只是可见道具；右侧蓝色 <code>DynamicCuboid</code> 已落到地面，说明它接入了刚体、碰撞和重力。</figcaption>
</figure>

## `prim_path` 是场景地址，`name` 是 Python 里的名字

最小脚本里一块方块这样写：

```python
box = DynamicCuboid(
    prim_path="/World/Objects/RedBox",
    name="red_box",
    position=np.array([0.35, 0.25, 0.30]),
    scale=np.array([0.18, 0.18, 0.18]),
    color=np.array([0.90, 0.20, 0.20]),
)
world.scene.add(box)
```

两个名字容易混：

| 参数 | 含义 | 用在哪里 |
|---|---|---|
| `prim_path` | USD 场景树里的地址 | `/World/Objects/RedBox` |
| `name` | Isaac Sim `world.scene` 注册名 | `world.scene.get_object("red_box")` |

二者都应该唯一。两个对象共用同一个 `prim_path`，就像两个文件写到同一路径；两个对象共用同一个 `name`，后面按名字取对象时也会混乱。

## 位置是中心点，不是底面

`position=np.array([x, y, z])` 写的是物体**中心点**在世界坐标系里的位置，不是底面位置。

例如：

```python
position=np.array([0.35, 0.25, 0.30])
scale=np.array([0.18, 0.18, 0.18])
```

这个方块初始中心高度是 `z=0.30m`，边长是 `0.18m`。落地后底面接触 `z=0`，中心点就会停在：

```text
0.18 / 2 = 0.09m
```

所以终端读到 `z≈0.09` 是正确的。

球也是同理，只是球用 `radius`：

```python
DynamicSphere(
    prim_path="/World/Objects/Ball",
    name="ball",
    position=np.array([0.20, -0.02, 0.40]),
    radius=0.12,
    color=np.array([1.00, 0.85, 0.10]),
)
```

球落地后中心高度应该接近 `z=0.12`。

## 颜色是 0 到 1

Isaac Sim core 对象的 `color` 常用 RGB 数组，范围是 `0~1`：

```python
color=np.array([0.90, 0.20, 0.20])  # 红色
```

不要写成图像软件里常见的 `0~255`：

```python
color=np.array([230, 50, 50])  # 不推荐
```

过大的数值可能被裁剪，导致颜色看起来发白或不符合预期。

## 最小物体代码

```python
import numpy as np
from isaacsim.core.api.objects import DynamicCuboid, DynamicSphere

world.scene.add(DynamicCuboid(
    prim_path="/World/Objects/RedBox",
    name="red_box",
    position=np.array([0.35, 0.25, 0.30]),
    scale=np.array([0.18, 0.18, 0.18]),
    color=np.array([0.90, 0.20, 0.20]),
))

world.scene.add(DynamicSphere(
    prim_path="/World/Objects/Ball",
    name="ball",
    position=np.array([0.20, -0.02, 0.40]),
    radius=0.12,
    color=np.array([1.00, 0.85, 0.10]),
))
```

## 常见错误

| 现象 | 可能原因 | 正解 |
|---|---|---|
| 物体不下落 | 用了 `Visual*` | 换成 `Dynamic*` |
| 落地高度不符合预期 | 把 `position` 当成底面位置 | `position` 是中心点 |
| 颜色很怪或发白 | RGB 写成 0~255 | 改成 0~1 |
| 取对象时报错 | `name` 写错或重复 | 保持 `name` 唯一，并和 `get_object()` 一致 |
| 场景树里找不到物体 | `prim_path` 写错 | 用 `/World/Objects/...` 这类绝对路径 |

## 小结

- 想参与物理，用 `DynamicCuboid` / `DynamicSphere`，不要用只有外观的 `Visual*`。
- `prim_path` 是 USD 地址，`name` 是 Python 里取对象的注册名。
- `position` 是中心点；方块落地后的 z 约等于边长一半，球落地后的 z 约等于半径。
- `color` 用 0~1 RGB。

## 导航

- 返回目录：[搭一个场景](../02-build-a-scene.md)
- 上一页：[光源](02-lights.md)
- 下一页：[运行与验证](04-run-and-verify.md)
