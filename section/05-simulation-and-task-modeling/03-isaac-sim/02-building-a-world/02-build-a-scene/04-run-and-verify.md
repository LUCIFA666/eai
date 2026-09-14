# 运行与验证

本节分 4 页，这一页拆最小场景的最后一步：为什么要 `reset`，为什么要 `step`，以及怎样用画面和坐标判断场景是否搭对。

## 本节目标

本节围绕下面几个问题展开：

1. `reset`、`step`、`render` 分别做了什么，为什么顺序不能乱？
2. 怎么用物体的 z 坐标客观验证它确实落到了地面？
3. 结果不对时，画面和数字各能说明什么，按什么顺序排查？

## `reset` 让物理真正就绪

在 Isaac Sim 里，写完 USD 场景并不等于物理已经可用。你可以先把地面、灯光、物体都挂到 Stage 上，但刚体、碰撞、质量这些物理对象要等 `reset` 后才真正初始化：

```python
world.reset()
```

所以读状态前要先 `reset`：

```python
world.reset()
pos, _ = cube.get_world_pose()
```

如果在 `reset` 之前读状态，轻则拿到不完整值，重则直接报错。

## `step` 推进物理，`render` 决定是否渲染

```python
for _ in range(120):
    world.step(render=True)
```

`step` 做两件事：

| 参数 | 含义 | 适合 |
|---|---|---|
| `render=True` | 推进物理，同时渲染一帧画面 | 要看 GUI、保存 RGB / 视频 |
| `render=False` | 只推进物理，不渲染画面 | 只读状态、批量跑物理、smoke test |

最小场景为了验证画面，使用 `render=True`。如果只是安装验证或读坐标，`render=False` 更快，也更少受光源 / 相机影响。

## 用 z 坐标验证落地

落地后，动态物体的中心 z 应该接近它的“半身位”：

| 物体 | 尺寸参数 | 落地后中心 z |
|---|---|---|
| 边长 0.18 的方块 | `scale=[0.18, 0.18, 0.18]` | `0.09` |
| 边长 0.22 的方块 | `scale=[0.22, 0.22, 0.22]` | `0.11` |
| 半径 0.12 的球 | `radius=0.12` | `0.12` |

示例代码：

```python
for nm in ["red_box", "green_box", "blue_box", "ball"]:
    pos, _ = world.scene.get_object(nm).get_world_pose()
    print(nm, "->", np.round(pos, 3))
```

示例输出：

```text
red_box   -> [ 0.35   0.252  0.09 ]
green_box -> [-0.055 -0.295  0.11 ]
blue_box  -> [-0.403  0.202  0.08 ]
ball      -> [ 0.2   -0.02   0.12 ]
```

这里的重点不是小数点后一两位完全一致，而是数量级和物理意义一致：方块 / 球没有掉穿地面，也没有悬在半空。

坐标能说明物理大概率正确，画面则能说明相机、光源和渲染链路也在工作。下面这张图来自同一个最小场景的 headless 渲染：如果你能看到地面、阴影和物体，同时终端 z 坐标也接近半身位，就说明“场景搭起来了”。

<figure>
  <img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-built-scene.png" alt="Isaac Sim 最小场景渲染结果" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
  <figcaption class="doc-figure-subtitle">验证时不要只看图，也不要只看日志。画面说明渲染可读，z 坐标说明物理落地，两者合在一起才是可靠的最小场景检查。</figcaption>
</figure>

## 画面和数字分别说明什么

| 信号 | 能说明什么 | 不能说明什么 |
|---|---|---|
| 坐标 z 正常 | 物理、地面、尺寸单位大概率正确 | 光源、相机、渲染是否正确 |
| 画面有物体和阴影 | 灯光、相机、渲染大概率正确 | 物体是否真的动态落地 |
| x、y 基本不变 | 物体主要是竖直落下 | 场景没有给它额外水平速度 |

因此，调试时最好同时看两个信号：**画面**和**坐标**。只看画面容易被视角 / 光源骗，只看坐标又发现不了黑屏和相机问题。

## 调试顺序

如果场景不对，按这个顺序查：

1. 脚本是否创建了 `SimulationApp`，并且在 `isaacsim.core.*` import 之前。
2. 是否创建了 `World` 和地面。
3. 动态物体是否用 `Dynamic*`，而不是 `Visual*`。
4. 是否调用了 `world.reset()`。
5. 是否循环调用了 `world.step()`。
6. 如果数字正常但图黑，再去查灯光和相机。

## 小结

- `reset` 是物理初始化边界；没有 `reset`，不要急着读物体状态。
- `step` 才会推进仿真；不 step，世界不会自己动。
- 用 z 坐标能快速判断物体是否正确落地；用画面能判断灯光和渲染是否正常。
- 先用数字排物理问题，再用画面排渲染问题，调试会快很多。

## 导航

- 返回目录：[搭一个场景](../02-build-a-scene.md)
- 上一页：[动态物体](03-dynamic-objects.md)
- 下一页：[坐标系与单位](../03-frames-and-units.md)
