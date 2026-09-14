# 坐标系与单位

上一页你搭好的场景里，红方块落稳后坐标是 `[0.35, 0.252, 0.09]`。这串数字到底是“在哪儿、用什么单位、相对谁量的”？这一页就把位置、朝向、单位这三件最容易埋雷的事讲清楚。它们现在看着琐碎，但到下一部分处理机器人资产、做 IK 和控制时，frame 没对齐会让所有目标点一起偏。

## 本节目标

本节围绕下面几个问题展开：

1. Isaac Sim 默认的长度、角度和坐标系约定是什么？
2. 同一个点为什么换个 frame 数字就变，描述「目标在哪里」前要先问哪三个问题？
3. 怎么在 world 与 base 之间换算位姿，并把坐标系画出来核对？

阅读这一页前，最好已经能搭出简单场景，并准备给机器人或相机指定目标位姿。示例只用到一点 numpy，不需要任何机器人库。

## 默认约定

Isaac Sim 大部分坑不是公式错，而是**单位和约定没对齐**。先把默认值刻进脑子：

| 量 | 默认约定 | 说明 |
|---|---|---|
| 位置 | **米（m）** | `World(stage_units_in_meters=1.0)` 把 stage 单位设成米；USD 文件原生默认是厘米 |
| 角度 | **弧度（rad）** | Python API 普遍用弧度；GUI 里常以角度显示，别混 |
| 姿态 | **四元数，顺序 `wxyz`** | `get_world_pose()` 返回 `(position, quat_wxyz)`；很多其它库用 `xyzw`，转换时务必对齐 |
| 缩放 | 无量纲倍数 | 资产 scale 不对，物体会大十倍 / 小十倍 |

回头看上一页的示例读数就一目了然（姿态一行是补打印 `get_world_pose()` 姿态分量后的读数，上一页脚本默认只打印位置）：

```text
red_box  pos=[ 0.350  0.252  0.090]  quat(wxyz)=[ 1.00  0.00  0.00  0.00]
```

- `pos` 是 **world frame** 下、**单位米**：红方块在世界原点右前方 0.35m、0.25m，离地 0.09m。
- `quat=[1,0,0,0]` 是**单位四元数**（wxyz），表示"没有旋转"——方块自由下落不会自转，所以姿态保持初始朝向。

## 同一个点，换个 frame 数字就变

最关键的一句话：**位置永远是"相对某个 frame"量出来的**。同一个点，在不同 frame 下数字可能完全不同。常见的几类 frame：

<figure class="doc-figure">
<p class="doc-figure-title">从 world 到工具：一条 frame 变换链</p>
<div class="figure-flow">
<div class="figure-node"><strong>world frame：</strong>整个 stage 的世界坐标，所有位姿的公共基准</div>
<div class="figure-node"><strong>robot base frame：</strong>机器人底座坐标；base 在 world 中的位姿决定两者换算</div>
<div class="figure-node"><strong>link / joint frame：</strong>每个连杆的局部坐标，沿运动学链一层层叠加</div>
<div class="figure-node"><strong>end-effector / tool frame：</strong>夹爪或工具中心，IK / 运动生成的目标常要换算到这里或 base</div>
<div class="figure-node"><strong>camera / object frame：</strong>相机成像坐标、物体局部坐标；像素↔3D 还要相机内外参</div>
</div>
<p class="doc-figure-subtitle">说"目标在 [0.6, 0.1, 0.82]"而不说在哪个 frame，等于没说清。</p>
</figure>

举例：说"烧杯中心在 `[0.6, 0.1, 0.82]`"——如果是 **world frame**，它就在世界里那个位置；如果是 **robot base frame**，还得结合机器人底座在 world 里的位姿，才知道它到底在哪。机械臂控制最常见的错误之一，就是把 world frame 下的目标，直接当成 base frame 或 end-effector frame 的目标喂给控制器。

## 任何"目标在哪里"，先问三个问题

只要涉及一个位姿，开口前先问自己：

1. 这个位置是在**哪个 frame** 下描述的？（world？base？tool？）
2. 单位是**米**还是厘米，角度是**弧度**还是角度？
3. 姿态四元数是 **`wxyz`** 还是 `xyzw`？

这三问没对齐，后面的 IK、运动生成、相机标注、数据记录都会带着同一个错误往下传——而且现象往往不是"报错"，而是"机器人朝错误方向慢慢挪过去"，更难查。

## world 到 base

最常见的换算，就是把 world 下的目标点喂给需要 base frame 的控制器。下面用纯 numpy 演示，机器人底座位姿可由 `articulation.get_world_pose()` 拿到（返回 position 与 `wxyz` 四元数）：

```python
import numpy as np

def quat_wxyz_to_R(q):
    w, x, y, z = q
    return np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - w*z),     2*(x*z + w*y)],
        [2*(x*y + w*z),     1 - 2*(x*x + z*z), 2*(y*z - w*x)],
        [2*(x*z - w*y),     2*(y*z + w*x),     1 - 2*(x*x + y*y)],
    ])

# 机器人底座在 world 中的位姿（get_world_pose() 返回 position 和 quat(wxyz)）
base_pos  = np.array([0.40, 0.00, 0.00])
base_quat = np.array([1.0, 0.0, 0.0, 0.0])     # wxyz，无旋转

p_world = np.array([0.60, 0.10, 0.82])          # world frame 下的目标（如烧杯中心）

R = quat_wxyz_to_R(base_quat)
p_base = R.T @ (p_world - base_pos)              # world -> base: R^T (p_world - t)
print("target in base frame:", p_base)          # -> [0.20 0.10 0.82]
```

底座在 world 原点右移了 0.40m，所以同一个目标点换到 base frame 后，x 从 0.60 变成 0.20。如果把 `p_world` 误当 base frame 目标直接发给控制器，机器人就会朝错位置走；底座一旦带旋转，偏差会更大。

## 把 frame 画出来

不要只盯着数字猜。Isaac Sim 里可以把目标点、末端 frame、相机视锥、物体中心都可视化或打印出来比对。只要这些 frame 没对齐，IK、运动生成、相机标注、数据记录会一起错。先确认"每个数字属于哪个 frame、单位对不对"，再往下做控制。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 位置就是位置 | 必须相对某个 frame 才有意义 | 永远说清在哪个 frame |
| 单位无所谓 | USD 原生是厘米，Isaac 设成米 | 用 `stage_units_in_meters=1.0`，按米理解 |
| 角度按度算 | API 普遍用弧度 | 程序里一律弧度，GUI 显示别混用 |
| 四元数都一样 | `wxyz` 与 `xyzw` 顺序不同 | Isaac core 是 `wxyz`，跨库先转换 |
| world 目标能直接发给控制器 | 控制器常要 base / tool frame | 先做 frame 换算 |
| 机器人慢慢走偏是控制器的锅 | 多半是 frame / 单位没对齐 | 回到三问逐项核对 |

## 小结

- Isaac Sim 默认：位置**米**、角度**弧度**、姿态**四元数 `wxyz`**；`World(stage_units_in_meters=1.0)` 把 stage 设成米。
- 位置永远相对某个 frame；同一个点换 frame 数字就变，说目标必须说清 frame。
- 任何位姿先问三件事：哪个 frame、什么单位、四元数顺序。
- world → base 用 `R^T (p_world - t)` 换算；frame 没对齐会让所有目标一起偏。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Python Scripting and Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/index.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Motion Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/motion_generation_overview.html)
- Pixar OpenUSD, [Stage Metrics（metersPerUnit）](https://openusd.org/release/api/group___usd_geom_linear_units__group.html)

## 导航

- 返回目录：[场景构建与坐标约定](../02-building-a-world.md)
- 上一页：[搭一个场景](02-build-a-scene.md)
- 下一页：[机器人资产与物理配置](../03-robot-and-physics.md)
