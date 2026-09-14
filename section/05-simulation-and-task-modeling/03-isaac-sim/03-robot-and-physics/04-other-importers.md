# 其它导入器

前两页把 **URDF** 这条主线讲透了，因为它是机器人资产最常见的入口。但项目里的资产不一定是 URDF：有人从 MuJoCo 迁移（MJCF），有人只有扫描 / 建模得到的网格，有人直接用 CAD（Onshape）设计硬件。这一页帮你按资产类型选对导入路径。

## 本节目标

本节围绕下面几个问题展开：

1. 除了 URDF，MJCF、网格、CAD 等来源各自该用哪个导入器？
2. 这些不同来源为什么最终都汇到同一个 USD 终点？
3. 面对一个具体资产，怎么判断走哪条导入路径最省事？

这一页写给手里的资产不是 URDF、想知道该走哪条导入路的读者。无论来源是 MJCF、CAD 还是普通网格，核心判断都一样：先把它可靠地转成 USD，再按上一页的体检流程补齐物理属性。

## 四类来源，四个导入器，同一个 USD 终点

先记住一个共同点：**任何导入器只负责把“源格式”翻译成 USD，它不保证这份 USD 已经适合仿真。** 导入之后，碰撞体、质量惯量、joint drive、材质和摩擦仍要按 [上一页的物理属性配置与检查](03-physics-audit.md) 检查。

<figure class="doc-figure">
<p class="doc-figure-title">四类来源，四个导入器，同一个 USD 终点</p>
<div class="figure-flow">
<div class="figure-node">URDF / xacro —— ROS 机器人结构 → URDF Importer（见 URDF 到 USD 页面）</div>
<div class="figure-node">MJCF（.xml）—— MuJoCo 模型 → MJCF Importer</div>
<div class="figure-node">网格 obj / stl / fbx / glTF —— 扫描 / 建模件 → Mesh 转 USD</div>
<div class="figure-node">CAD（Onshape 等）—— 自研硬件 → Onshape Importer（需 API key）</div>
</div>
<p class="doc-figure-subtitle">无论哪条路，落地都是 USD；物理属性仍需导入后按体检流程补齐。</p>
</figure>

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-robot-gallery.png" alt="多种机器人同台：三款四足机器人与一款人形机器人" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">多机型同台渲染：不同来源的机器人资产最终都会落到 USD 场景，并在需要控制时被组织成 articulation。</figcaption>
</figure>

## MJCF

MJCF 是 MuJoCo 的模型格式（`.xml`）。要复用 MuJoCo 生态里的机器人或 benchmark（很多腿足、人形、操作任务用 MJCF 描述），用 **MJCF Importer** 转成 USD：

- **启用扩展**：`isaacsim.asset.importer.mjcf`（`Window > Extensions` 搜 “MJCF”）。
- **GUI 导入**：`File > Import` 选 `.xml`，在导入面板设置 fixed base、关节 drive、collision 等。
- **Python 导入**：和 URDF 一样通过 `omni.kit.commands` 暴露命令；命令名 / 参数随版本变，拿不准先 GUI 导一次看生成的 USD。

迁移时尤其要注意 MJCF 和 USD / PhysX 的语义差异：

```text
坐标与单位：MJCF 角度默认按度（degree，URDF 才默认弧度）、还可能用不同默认重力 / 时间步，进 Isaac Sim 要重新核对
关节与执行器：MJCF 的 actuator / gear 不会自动等价成 PhysX joint drive，stiffness / damping 要重设
接触参数：  MJCF 的 solref / solimp 接触模型和 PhysX 不同，摩擦和接触刚度要重调
站姿：      MJCF 的 keyframe 初始姿态不一定保留，站姿可能要在 Isaac Sim 里重设
```

一句话：MJCF 导入能把“形状和结构”搬过来，但“怎么动、怎么接触”往往要按 PhysX 的方式重调。

## 网格

只有网格文件（扫描件、建模件、第三方素材）时，用 Isaac Sim 的资产导入 / Mesh Converter 转 USD。两个要点：

- **只有视觉，没有物理**：网格通常只带几何和材质，不带碰撞体、质量、关节。导进来默认是个 visual mesh，要参与物理就得自己加 collider、rigid body、physics material（见上一页）。
- **instanceable（可实例化）**：同一物体在场景里重复很多次（货架上几十个杯子、并行环境里的同一张桌子）时，应转成 instanceable 资产——多个实例共享同一份网格数据，显存和加载成本大幅下降。这对后面 Isaac Lab 的大规模并行尤其重要。

一个实用习惯：把转换好的 `.usd` 当成“干净资产”单独存一份，再在场景里 reference 它，而不是每次重新导网格。

## CAD

机器人或夹具是你自己用 CAD 设计的，Onshape 这类云 CAD 可经 **Onshape Importer** 直接拉进来（需账号和 API key），适合自研硬件快速迭代：在 CAD 里改完，导入 Isaac Sim 验证装配、碰撞和运动。CAD 导入同样只解决“几何和装配”，关节、drive、碰撞简化、质量惯量仍要补；CAD 的高精度网格往往不适合直接做 collision，通常要凸分解或简化。

## 现成 USD 机器人模型库：robot_usds

如果你的目标机器人已经有现成 USD 资产，可以跳过上面的格式转换步骤。robot_usds 是一个开源的机器人 USD 模型集合，汇集了主流机器人的 USD 格式文件，在 Isaac Sim 中可直接 reference 使用，无需从 URDF/MJCF 导入再调参。它在 USD 生态中的定位类似于 MuJoCo 生态中的 mujoco_menagerie。

[https://github.com/fiveages-sim/robot_usds](https://github.com/fiveages-sim/robot_usds)

## 选哪条路

| 你手里有什么 | 用哪个导入器 | 之后仍要补 |
|---|---|---|
| 已有 USD 模型（robot_usds / NVIDIA Assets） | 直接 reference 到 Stage | 按体检流程核对物理属性 |
| ROS 机器人 URDF / xacro | URDF Importer（第 1 页）| collision 简化、drive、摩擦 |
| MuJoCo 模型 `.xml` | MJCF Importer | joint drive、接触参数、站姿 |
| 网格 obj / stl / fbx / glTF | Mesh Converter | collider、质量、instanceable |
| CAD（Onshape 等）| Onshape Importer | 关节、collision 简化、质量惯量 |

**版本命名空间提醒**：5.x 导入器在 `isaacsim.asset.importer.*`；4.0 及更早是 `omni.importer.*` / `omni.isaac.*`。拿不准当前版本的扩展名 / 命令名时，用 `Window > Extensions` 搜，或 `File > Import` 看支持哪些格式。

## 小结

- URDF 不是唯一入口：MJCF、网格、CAD 各有导入器，终点都是 USD。
- 导入器只翻译“几何和结构”；碰撞、物理材质、质量惯量、joint drive 仍要按体检流程补齐。
- 从 MuJoCo 迁移时，actuator / 接触 / 站姿 / 单位都可能要按 PhysX 重设。
- 重复出现的资产应做成 instanceable，为大规模并行省显存。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
- MuJoCo Documentation, [Modeling (MJCF)](https://mujoco.readthedocs.io/en/stable/modeling.html)

## 导航

- 上一页：[物理属性配置与检查](03-physics-audit.md)
- 下一页：[控制](../04-control.md)
