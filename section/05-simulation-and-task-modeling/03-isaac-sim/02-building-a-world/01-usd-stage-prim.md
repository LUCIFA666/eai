# USD、Stage 与 Prim

上一部分你已经让一个方块在 Isaac Sim 里掉了下来。但你可能还没想清楚一件事：那个方块、那块地面、那盏灯，到底以什么形式存在于“世界”里？这一页就回答这个问题：Isaac Sim 的场景不是写死在一个文件里的，而是一棵能拼装、能引用、能寻址的 **USD 树**。理解了它，你才谈得上“搭”一个世界。

## 本节目标

本节围绕下面几个问题展开：

1. USD、Stage、Prim 这三个词分别指什么，它们怎么组成一棵场景树？
2. 你的代码通常该操作哪一层 Prim，又怎么用 `prim_path` 找到它？
3. 引用（reference）和分层（layer）是怎么把外部资产拼进当前 Stage 的？

这一页写给已经跑通第一个仿真、用过 MuJoCo 的 MJCF、但第一次接触 USD 的读者。不要求你懂 USD 内部格式，只要求你建立“场景是一棵树”的理解视角。

## 场景不是一个文件，而是一棵树

MuJoCo 的世界几乎等于一个 MJCF：一份 XML 从上到下把 body、joint、geom、light 全写死，读进来就是整个场景。USD 不是这样。**USD 是一种"组织场景"的方式**——它把世界拆成一棵节点树，每个节点（机器人、桌子、灯、相机、材质、物理场景）都能单独存在、单独引用、单独替换。

所以在 Isaac Sim 里，"搭场景"不是写一个大文件，而是往一棵树上挂节点、或者把别人做好的资产引用进来。

| 对比 | MuJoCo（MJCF） | Isaac Sim（USD） |
|---|---|---|
| 场景载体 | 一个 XML 文件 | 一棵 Stage 树（可跨多个 `.usd`） |
| 加一个物体 | 在 XML 里加 `<body>` | 往树上 `add` 一个 Prim，或 reference 一份 USD |
| 复用资产 | 复制粘贴 XML 片段 | reference 同一个 `.usd`，改一处全更新 |
| 找一个对象 | 按 name 查 | 按 **prim path**（树上的地址）查 |
| 材质 / 物理 | 写在 geom / option 里 | 各自是树上的 Prim（`Looks` / `PhysicsScene`） |

一句话类比：**MJCF 是一张写死的完整剧本；USD Stage 是一个仿真世界的场景树**——每件道具都是挂在树上、能单独搬动和替换的节点。

## 三个词 + 一个地址

抓住三个概念、外加一个地址，USD 就不神秘了：

| 概念 | 是什么 | 类比 |
|---|---|---|
| **Stage** | 当前打开的整个世界，就是那棵场景树 | 实验场本身 |
| **Prim** | 树上的一个节点：机器人、link、mesh、灯、相机、材质，甚至一个空的 `Xform` 容器 | 场里的一个对象 / 一个分组 |
| **属性（attribute）** | 挂在 Prim 上的数据：位置、缩放、颜色、质量、碰撞 | 道具的具体规格 |
| **prim path** | Prim 在树上的唯一地址，形如 `/World/Objects/RedBox` | 场景树里的地址 |

`prim path` 看着像文件路径，作用也一样：**代码靠它在场景里找到对象**。一个任务脚本通常会显式记下几个关键路径——机器人根、末端执行器、相机、目标物体——后面所有操作都从这些地址出发。

## 操作哪一层 Prim

USD 树最容易让初学者困惑的地方，不是概念难，而是**同一个“物体”下面会有很多 Prim**。看起来是一台机器人、一张桌子、一盏灯，树里却可能拆成根节点、visual mesh、collision mesh、材质、关节、传感器等多层。操作前先问“我要改的是哪一层”：

| 你想做什么 | 通常操作哪一层 |
|---|---|
| 整体移动一个物体 / 机器人 | 物体根 `Xform`，如 `/World/Objects/RedBox`、`/World/Robot` |
| 读取或驱动整台机器人 | 带 articulation root 的机器人根 Prim |
| 改视觉颜色 / 材质 | visual mesh 或 `Looks` 下的材质 Prim |
| 查能不能碰撞 | collision Prim，或带 `CollisionAPI` 的几何 Prim |
| 改光源强度 / 位置 | 对应的 Light Prim，如 `/World/DistantLight`、`/World/KeyLight` |
| 找相机图像来源 | Camera Prim，如 `/World/Camera` |

这张表比记住某个固定路径更重要。不同资产的树长得不一样，但“先定位根，再看 visual / collision / articulation / light / camera 分工”的思路是稳定的。

## USD 文件形态

前面讲的 Stage / Prim / attribute 是 USD 的**逻辑结构**；落到磁盘上时，它可以有几种常见文件后缀。初学阶段不用深究底层格式，只要知道它们各自适合什么场景：

| 后缀 | 直觉 | 适合 |
|---|---|---|
| `.usda` | ASCII 文本 USD，人能直接打开看 | 学习、调试、看层级 / reference / attribute，适合小文件 |
| `.usdc` | 二进制 USD（crate），机器读写更高效 | 大资产、生产资产、缓存、mesh 多的场景 |
| `.usd` | 通用 USD 后缀，里面可以是文本或二进制 | 日常保存和引用；不想暴露具体存储形式时常用 |
| `.usdz` | 打包格式，把 USD 和纹理等资源放进一个包 | 交付、分享、移动端 / 查看器预览，不适合频繁编辑 |

所以，**USD 不是只指 `.usd` 这一个后缀**。我们说"USD 场景"时，更多是在说它的组织方式：Stage、Prim、属性、reference、layer。至于文件是 `.usda` 还是 `.usdc`，只是这套结构的存储方式不同。

一个实用判断：

- 想学习和排查：优先导出 / 查看 `.usda`，因为能直接读文本。
- 想保存正式资产：常用 `.usd` 或 `.usdc`，让工具处理性能和体积。
- 想把资产连同贴图发给别人：考虑 `.usdz`。
- 想在脚本里 reference 资产：`.usd`、`.usda`、`.usdc` 都可以被引用；重点是路径、层级和依赖资源是否完整。

`.usda` 打开后大概长这样（这里只是极简示意）：

```usda
#usda 1.0

def Xform "World"
{
    def Xform "Objects"
    {
        def Cube "RedBox"
        {
            double3 xformOp:translate = (0.35, 0.25, 0.3)
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }
    }
}
```

这段文本和你在 Stage 树里看到的 `/World/Objects/RedBox` 是同一件事：文件里描述层级，运行时打开后变成 Stage 上的 Prim。只是生产资产里会有更多材质、mesh、碰撞、物理 schema、reference 和 layer 信息。

## Stage 树长什么样

下面这棵树来自本部分下一页要搭的场景（地面 + 两盏灯 + 一组物体）。脚本遍历 Stage 后可以打印出类似结构（这里只展开到第 2 层，更深的折叠）：

```text
World                    <Xform>
  defaultGroundPlane     <Xform>
    Looks                  <Scope>      # 地面的材质
    GroundPlane            <Xform>      # 含 CollisionPlane（碰撞面）
    Environment            <Xform>
  Physics_Materials        <>           # 物理材质集合
  Objects                <Xform>        # 我们自己建的容器
    RedBox                 <Cube>       # ← 真正的几何 + 刚体在这里
    GreenBox               <Cube>
    BlueBox                <Cube>
    Ball                   <Sphere>
  DistantLight           <DistantLight>
  DomeLight              <DomeLight>
  Looks                    <>           # 物体的可视材质
```

读这棵树，三件事一目了然：

- **场景是"搭"出来的**：`defaultGroundPlane`、两盏灯、`Objects` 容器，都是我们一笔一笔挂上去的节点，不是某个文件里固定的。
- **路径就是地址**：想拿红方块，就找 `/World/Objects/RedBox`；想调灯，就找 `/World/DistantLight`。
- **看得见 ≠ 你要操作的那个**：地面下面还藏着 `Looks`（材质）、`CollisionPlane`（碰撞面）这些子 Prim——你眼里是"一块地面"，树里却是一组分工不同的节点。

## 用代码找 Prim

调 Isaac Sim 时，第一件事往往不是写控制器，而是**确认 stage 里到底有哪些 Prim、路径对不对**。下面是 standalone 脚本里的最小用法（`SimulationApp` 启动之后再 import）：

```python
import omni.usd

# 拿到当前 stage（standalone 里也可用 world.stage）
stage = omni.usd.get_context().get_stage()

# 1) 按 prim path 取对象，先确认它真的存在
red = stage.GetPrimAtPath("/World/Objects/RedBox")
print("valid:", red.IsValid(), "| type:", red.GetTypeName())

# 2) 遍历整棵树，把"对象找不到"这类问题一眼看穿
for prim in stage.Traverse():
    print(prim.GetPath(), prim.GetTypeName())

# 3) 列出某个容器下的直接子节点
for child in stage.GetPrimAtPath("/World/Objects").GetChildren():
    print("child:", child.GetName())
```

`IsValid()` 是 `False`，几乎总是两种原因：**路径写错**（大小写、漏了 `/World`），或者**资产还没加载完**就去取。遇到"对象为空 / 图像全黑 / 姿态不变"，先 `Traverse` 一遍看实际路径，别凭记忆猜是 `/World/robot` 还是 `/World/Robot`。

## 引用与分层

USD 真正的威力是 **reference（引用）**：当前 stage 不复制资产内容，而是在某个 prim path 下"挂"一份外部 `.usd`。

```text
/World/Robot  ->  reference robots/franka/franka.usd
/World/Table  ->  reference assets/table.usd
```

好处是同一份资产改一次、处处更新；多个场景共享一个机器人 USD。但引用也带来一类最常见的坑：

| 现象 | 多半是因为 |
|---|---|
| 模型变白、没纹理 | 只引用了子 Prim，材质 `Looks` 没跟着进来 |
| 物体移动时位置怪 | 资产原点不在几何中心 |
| 机器人 / 物体大十倍或小十倍 | scale 没对齐（单位见下一页之后的"坐标与单位"） |
| 仿真时穿模、掉下去 | 有 visual mesh 但缺 collision |
| 脚本突然找不到对象 | prim path 改了，代码还在找旧地址 |

调试引用问题的顺序很固定：先确认 Prim 是否存在 → 是否挂在预期父节点下 → scale 是否合理 → 有没有 collision → 引用资产的材质和子 Prim 是否一起加载了。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| USD 就是个模型格式 | 它同时描述层级、引用、材质、物理 | 把它当"场景的组织方式" |
| 场景写在一个文件里 | Stage 可跨多个 `.usd` 拼出来 | 用 reference 组合资产 |
| 看得见的就是要控制的 Prim | 下面还有 visual / collision / 材质子 Prim | 控制找 articulation root，移动找物体根 `Xform` |
| 路径随便写 | prim path 大小写、层级敏感 | 先 `Traverse` 确认实际路径 |
| 引用进来就万事大吉 | 材质 / 碰撞 / scale 可能没带全 | 按上面的清单逐项体检 |
| `.usda`、`.usdc` 是另一套东西 | 它们仍然是 USD，只是保存形态不同 | 学习看 `.usda`，生产多用 `.usd` / `.usdc` |

## 小结

- USD 不是模型格式，是"场景的组织方式"：MJCF 一个文件写死，USD 是一棵能拼装、引用、寻址的树。
- 记住三个词 + 一个地址：**Stage**（世界树）、**Prim**（节点）、**属性**（节点上的数据）、**prim path**（找对象的地址）。
- `.usda`、`.usdc`、`.usd`、`.usdz` 都是 USD 生态里的文件形态：文本、二进制、通用后缀和打包格式各有用途。
- 一个 Prim 下常有 visual / collision / 材质 / 关节等子节点——"看得见"不等于"你要操作的那个"。
- 引用让资产可复用，但材质、碰撞、scale、路径都可能出岔子，导入后要按清单体检。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Python Scripting and Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/index.html)
- NVIDIA Learn OpenUSD, [OpenUSD File Formats](https://docs.nvidia.com/learn-openusd/latest/stage-setting/usd-file-formats.html)
- NVIDIA Omniverse Documentation（OpenUSD：Stage 与 Prim）. https://docs.omniverse.nvidia.com/

## 导航

- 返回目录：[二、场景构建与坐标约定](../02-building-a-world.md)
- 下一页：[搭一个场景](02-build-a-scene.md)
