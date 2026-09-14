# 光源

本节分 4 页，这一页专门拆光源。光源看起来只是几行代码，但它牵涉到渲染、headless、USD Prim、强度、位置和方向。初学者第一次保存 RGB 图，最常见的问题就是：物理明明在跑，图却黑了。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么 headless 渲染必须自己补光，光源又为什么只影响画面、不影响物理？
2. 常用光源有哪几种，分别该在什么时候选用、强度怎么起步？
3. 画面过暗或过曝时，按什么顺序调试光源？

## 光源只影响画面，不影响物理

先分清一件事：灯光只影响 **RTX 渲染出来的画面**，不影响物理。没有灯时，方块仍然会下落、接触地面、读出正确坐标；只是相机 RGB 可能是一张黑图。

如果脚本只做物理，例如只读 `get_world_pose()`，可以不加灯；如果要保存图片、视频、相机 RGB、合成数据，就应该显式加灯。

## 最小补光

最小场景里用了两盏灯：

```python
import omni.usd
from pxr import UsdLux, Sdf

stage = omni.usd.get_context().get_stage()

UsdLux.DistantLight.Define(
    stage, Sdf.Path("/World/DistantLight")
).CreateIntensityAttr(2500.0)

UsdLux.DomeLight.Define(
    stage, Sdf.Path("/World/DomeLight")
).CreateIntensityAttr(900.0)
```

这两盏灯的分工是：

| 光源 | 直觉 | 适合做什么 |
|---|---|---|
| `DistantLight` | 太阳光 / 平行光 | 给场景一个明确的主光和阴影方向 |
| `DomeLight` | 天空光 / 环境光 | 把阴影区域抬亮，避免半边全黑 |

这个组合不是唯一正确答案，但很适合作为 headless smoke test 的默认补光：简单、稳定、容易看见物体和阴影。

## 在自建实验室场景里看光源差异

这部分图来自同一个实验室场景：`small_scene1000_textured.usda`。为了看清光源特征，相机固定在桌面近景；房间、桌子、桌面物体、地板和材质都不变，只切换 `/World/LightingStudyLights` 下的光源。这样读图时可以把画面差异主要归因到灯光，而不是场景或视角变化。

<figure>
  <img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-user-scene-lighting-comparison.jpg" alt="RoboGenesis 实验室场景中不同光源设置的渲染对比" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
  <figcaption class="doc-figure-subtitle">同一桌面任务区的光源对比：<code>DistantLight</code> 强调方向和较硬阴影，<code>DomeLight</code> 更像均匀环境补光；<code>SphereLight</code> 在桌面附近形成局部亮区和明显衰减，<code>RectLight</code> 像软箱灯板，覆盖更宽、阴影更柔；强度过高时桌面和玻璃器材会先被冲白。</figcaption>
</figure>

读这部分图时可以抓五个信号：

1. 看方向感：`DistantLight` 的阴影方向更明确，适合模拟太阳或单一主光。
2. 看均匀度：`DomeLight` 抬亮整体暗部，但方向感弱，桌面任务物体不会因此自动变清楚。
3. 看局部衰减：`SphereLight` 放到桌面附近后，离灯近的区域明显更亮，远处更快变暗。
4. 看阴影软硬：`RectLight` 面积更大，桌面照明更均匀，阴影边缘也更柔。
5. 看高光和材质：强度过高时，桌面、地板、玻璃器材会先被冲白，细节反而丢失。

## 能不能把光放到指定 xyz？

可以，但要看是哪一种光。

`DistantLight` 像太阳，重点是方向，位置意义不大；`DomeLight` 像天空环境，也不是靠 xyz 定位。想把灯放到某个具体位置，例如“从左上方照过来”，更适合用 `SphereLight` 或 `RectLight`。

### 放一个点光源到指定位置

```python
from pxr import UsdLux, UsdGeom, Sdf, Gf

stage = omni.usd.get_context().get_stage()

light = UsdLux.SphereLight.Define(stage, Sdf.Path("/World/KeyLight"))
light.CreateIntensityAttr(30000.0)
light.CreateRadiusAttr(0.4)

xform = UsdGeom.Xformable(light.GetPrim())
xform.AddTranslateOp().Set(Gf.Vec3d(2.0, -3.0, 4.0))
```

这盏灯的位置是：

```text
x =  2.0
y = -3.0
z =  4.0
```

`SphereLight` 可以理解成一个有半径的点光源。半径越大，阴影边缘越柔；强度越大，画面越亮。上面的 `30000.0` 不是必须值，只是一个在小尺度场景里容易看见的起点。

### 放一个面光源到指定位置

```python
from pxr import UsdLux, UsdGeom, Sdf, Gf

stage = omni.usd.get_context().get_stage()

light = UsdLux.RectLight.Define(stage, Sdf.Path("/World/SoftBox"))
light.CreateIntensityAttr(5000.0)
light.CreateWidthAttr(2.0)
light.CreateHeightAttr(1.0)

xform = UsdGeom.Xformable(light.GetPrim())
xform.AddTranslateOp().Set(Gf.Vec3d(0.0, -3.0, 3.0))
xform.AddRotateXYZOp().Set(Gf.Vec3f(60.0, 0.0, 0.0))
```

`RectLight` 像摄影灯板，适合做柔和的大面积照明。它既看位置，也看朝向；如果方向不对，可能明明有灯，物体却没被照亮。

## 常用光源怎么选

| 需求 | 推荐 |
|---|---|
| 只想让 headless 图不黑 | `DistantLight + DomeLight` |
| 想从某个 xyz 位置照物体 | `SphereLight` |
| 想要柔和阴影 / 灯板效果 | `RectLight` |
| 想模拟太阳方向 | `DistantLight`，调旋转而不是调位置 |
| 想整体提高暗部亮度 | `DomeLight` |

## 强度先怎么设

不同光源的强度数值尺度不完全一样，初学阶段不用追求物理精确，先追求“画面能稳定看清”：

| 光源 | 起步强度 |
|---|---|
| `DistantLight` | `1000` 到 `5000` |
| `DomeLight` | `300` 到 `1500` |
| `SphereLight` | `10000` 到 `50000` |
| `RectLight` | `1000` 到 `10000` |

如果图太暗，先增加强度；如果图发白、颜色被冲淡，先降低强度。调光时最好一次只改一个参数，否则很难判断是哪一项起了作用。

## 调试光源的顺序

画面黑时，按这个顺序查：

1. 场景里是否真的创建了 Light Prim，例如 `/World/DistantLight`。
2. 相机是否看向物体，而不是看向空处。
3. 物体是否在地面上，是否还没掉进地下。
4. 光源强度是否太低。
5. `RectLight` / `SphereLight` 是否离物体太远，或方向没对上。

如果你只是想快速确认“不是物理问题”，可以先读坐标：只要 `z` 正常落到半身位 / 半径，说明物理没问题，黑图多半是渲染、灯光或相机问题。

## 小结

- headless 黑屏通常不是物理错了，而是渲染缺光或相机没看对。
- `DistantLight + DomeLight` 是最稳的起步补光组合。
- 想把灯放到指定 xyz，用 `SphereLight` 或 `RectLight`；`DistantLight` 主要调方向，`DomeLight` 主要做环境光。
- 光源也是 USD Prim，有自己的路径、属性和 transform。

## 导航

- 返回目录：[搭一个场景](../02-build-a-scene.md)
- 上一页：[World 与地面](01-world-and-ground.md)
- 下一页：[动态物体](03-dynamic-objects.md)
