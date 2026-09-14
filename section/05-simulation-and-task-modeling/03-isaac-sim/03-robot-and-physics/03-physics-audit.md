# 物理属性配置与检查

机器人资产已经导入，关节也能读取和驱动，但仿真时仍可能穿地板、原地发抖、夹不住东西，或者给了目标却跟不上。这一页集中检查碰撞体、质量、摩擦和 Drive 参数，把“能显示”的资产调整到“能稳定参与仿真”的状态。

## 本节目标

本节围绕下面几个问题展开：

1. 一个机器人资产要逐项检查哪些物理属性（碰撞体、质量、材质、drive）？
2. 怎么给只有视觉、没有物理的物体补上碰撞体和物理材质？
3. 物理表现异常时，可以照哪张排查表定位问题？

这一页写给已经能导入并加载机器人 / 物体，但发现仿真行为不对劲的读者。它的重点不是再导入一次资产，而是建立一套排查顺序：先看 visual，再看 collision，再看摩擦和质量，最后看 joint drive。

## 显示与仿真

新手最容易误解的一点：**模型看起来完整，不代表它适合仿真**。一份导入后的 USD，至少有四类信息要分开看：

<figure class="doc-figure">
<p class="doc-figure-title">导入后的 USD：看、撞、滑、动 分开查</p>
<div class="figure-flow">
<div class="figure-node">视觉几何 / 材质 —— 相机看到什么（颜色、纹理、反光）</div>
<div class="figure-node">碰撞体 / 刚体 —— 物理引擎拿什么算接触和运动</div>
<div class="figure-node">物理材质 / 摩擦 —— 接触时滑不滑、弹不弹</div>
<div class="figure-node">joint drive —— 关节怎么被驱动到目标</div>
</div>
<p class="doc-figure-subtitle">先看 visual 是否完整，再开 collider 可视化；碰撞体对了再调摩擦，最后调 drive。</p>
</figure>

一句口诀记住这四层分工：**看得见靠 visual material；撞得上靠 collider；抓得稳靠 physics material 和摩擦；动得顺靠 joint drive。**

## 资产体检

不要一上来就把机器人、物体、相机、控制器全塞进一个大场景里调——越大越难定位问题。按下面顺序逐层加，每一步只引入一种新风险：

```text
1. 只加载机器人：查 link / joint / articulation root / scale / drive / 关节限位
2. 只加载物体：  查 visual / collision / 质量 / 惯量 / 材质 / 摩擦
3. 只加载场景：  查桌面高度 / 地面 / 灯光 / 相机 / 单位 / 坐标原点
4. 机器人 + 物体：查夹爪能否接触，物体会不会穿模 / 弹飞 / 滑走
5. 机器人 + 运动：查 IK / 末端 frame / base pose / 关节执行
6. 完整任务：    最后才查状态机 / 成功判定 / 数据字段
```

机器人单独加载就抖，先别怪任务逻辑；物体单独落地就穿桌，先别怪夹爪。一句话：**先让资产自己可信，再让任务使用资产。**

## 碰撞体

URDF / USD 里，visual 和 collision 是分开的两套几何：

```xml
<link name="panda_link0">
  <visual>    <!-- 给相机和人看，可以精细 -->
    <geometry><mesh filename=".../visual/link0.dae"/></geometry>
  </visual>
  <collision> <!-- 给物理引擎算接触，要简单稳定 -->
    <geometry><mesh filename=".../collision/link0.stl"/></geometry>
  </collision>
</link>
```

几个要点：

- 源 URDF 没有 collision 时，导入器能从 visual mesh 生成碰撞体——适合快速预览，但复杂 mesh 生成的碰撞体可能太重、太粗、局部穿插，物理会不稳定。
- 机器人 link 更适合用简化 mesh / 凸包 / 几何 primitive 作碰撞体。
- **self-collision 要谨慎开**：如果 link 的碰撞体本来就有轻微交叠，开了 self-collision 机器人可能一启动就抖、弹开甚至飞走。先让外部碰撞稳定，再考虑自碰撞。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-franka-collision.png" alt="Franka 碰撞几何高亮渲染" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">Franka 上带 CollisionAPI 的 11 个几何（8 个臂 link（link0~7）+ hand + 两个手指）整体涂绿后，绿色部分就是参与物理碰撞的几何。这个官方 Franka 资产的碰撞体直接复用了 visual 网格，所以碰撞几何几乎就是机器人本体；很多机器人资产则会用更简化的凸包作碰撞体，那时绿色形状会明显比外观更粗、更方。</figcaption>
</figure>

## 物理材质与摩擦

Isaac Sim 里有两种“材质”，初学者常混：

| 材质 | 决定 | 改它影响 |
|---|---|---|
| 视觉材质 | 相机看到的颜色 / 纹理 / 反光 | 渲染、识别、分割、domain randomization |
| 物理材质 | 接触的静摩擦 / 动摩擦 / 弹性 | 滑不滑、弹不弹、夹不夹得住 |

**桌面看起来像木头，不代表它的摩擦就是木头；夹爪看起来是橡胶，也不代表它真有大摩擦。** 物体从夹爪里滑走，要调的是物理材质的摩擦或碰撞体，而不是颜色。调摩擦前先确认 collision mesh 是对的，否则你可能用一个很大的摩擦掩盖了错误的碰撞体，换个场景又坏。

## Drive

这里的 drive 指 **joint drive**，不是显卡驱动。它是物理引擎里的虚拟执行器：你给关节一个目标位置或目标速度，drive 用 stiffness、damping、max force 把关节推向目标。

```text
stiffness：像弹簧，越大越想把关节拉到目标位置
damping：  像阻尼，越大越抑制速度和振荡
max force：drive 最多能施加多大力 / 力矩
```

两种常见模式：

| drive 模式 | 给什么目标 | 适合 | stiffness / damping |
|---|---|---|---|
| position drive | 目标角度 / 位移 | 机械臂关节、夹爪、转向 | stiffness > 0，damping 抑振 |
| velocity drive | 目标速度 | 轮子、输送带、连续旋转 | stiffness ≈ 0，靠 damping 追速度 |

以 Franka 为例：7 个臂关节和夹爪手指通常用 position drive；如果是移动底盘的驱动轮，则常用 velocity drive。导入 URDF 时导入器会生成初始 drive，但那只是起点——进任务前要核对每个 DOF 的 drive mode、stiffness、damping、max force、limit。**“能动”和“动得稳、可控、可复现”是两回事。**

## Franka 体检读数

加载官方 Franka 后遍历它的 USD 树，把质量、joint drive、碰撞体逐项打印出来。这正是上面“先小后大”体检第 1 步在做的事：

```text
--- 碰撞体 / 刚体 / 质量 体检 ---
  /World/Franka/panda_link0    rigid=True  mass=2.814
  /World/Franka/panda_link1    rigid=True  mass=2.360
  /World/Franka/panda_link2    rigid=True  mass=2.380
  ...（link3~6 略，均 1~3 kg）...
  /World/Franka/panda_link7    rigid=True  mass=0.405
  /World/Franka/panda_hand     rigid=True  mass=0.558
  /World/Franka/panda_leftfinger / rightfinger  rigid=True  mass=0.014
小计: 带碰撞 0 | 带刚体 11 | 带质量 11

--- Joint Drive 体检 (stiffness / damping / type) ---
  panda_joint1 ~ panda_joint7   drive[angular] stiffness=400.0 damping=80.0 type=force
  panda_finger_joint1           drive[linear]  stiffness=400.0 damping=80.0 type=force
小计: 带 drive 的关节自由度 8
```

从这部分读数能直接读出几件事：

- **11 个刚体 = 8 个臂 link（`link0`~`link7`）+ hand + 左右手指**。这里有个**和"7 DOF"极容易混**的点：Franka 常被叫"7 轴机械臂"，指的是 7 个**关节**（`panda_joint1~7`，即 7 个自由度）；但 **link 比关节多一个**——`joint1` 连 `link0→link1`、`joint7` 连 `link6→link7`，N 个关节串起 N+1 个 link，多出来的就是那个不动的**固定底座 `link0`**。所以"7 自由度"对应的是 **8 个臂 link**，别把关节数当成 link 数。
- **每个 link 的质量都已设好**（link0 最重 2.81 kg，手指最轻 14 g）——质量缺失或为 0 会让仿真发疯，这里都正常。
- **8 个自由度都配了 drive，`stiffness=400 / damping=80 / type=force`**，这是 Franka 能稳定跟随关节目标的前提；关节“跟不上目标”时就来这里看这三个数。
- **一个反直觉的坑**：遍历顶层 prim 时“带碰撞”的计数是 **0**——不是没有碰撞体，而是官方 Franka 的碰撞几何**藏在 instanceable 引用内部**，顶层 `Traverse` 直接看不到（要递归进 instance proxy 才看得到，上面那张绿色碰撞体图就是这么渲染出来的）。这恰恰印证了“显示 ≠ 仿真、碰撞体要专门去查”。

## 给只有视觉的物体补上物理

如果一个物体导入后“只有视觉、没有物理”，可以用 USD Physics schema 补碰撞体、刚体和物理材质：

```python
from pxr import UsdPhysics, UsdShade
import omni.usd

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath("/World/Objects/beaker_1")

# 1) 让它能碰撞、并作为刚体参与动力学
UsdPhysics.CollisionAPI.Apply(prim)
UsdPhysics.RigidBodyAPI.Apply(prim)

# 2) 建物理材质并设摩擦 / 弹性（物理材质 ≠ 视觉材质）
mat = UsdShade.Material.Define(stage, "/World/PhysicsMaterials/rubber")
pm = UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
pm.CreateStaticFrictionAttr(1.0)
pm.CreateDynamicFrictionAttr(0.9)
pm.CreateRestitutionAttr(0.0)

# 3) 把物理材质绑定到碰撞 prim
UsdShade.MaterialBindingAPI.Apply(prim)  # applied schema 需先 Apply，否则校验器会告警
UsdShade.MaterialBindingAPI(prim).Bind(mat, materialPurpose="physics")
```

第 2 步建的是**物理材质**（管摩擦、弹性），和决定颜色纹理的视觉材质是两回事。物体从夹爪里滑走，要动的是这里，而不是颜色。

## 物理属性排查表

| 现象 | 优先排查 |
|---|---|
| 机器人 / 物体穿地板 | `init_state` 的 z、collision 是否缺失、地面碰撞 |
| 原地发抖 / 炸飞 | self-collision 交叠、stiffness 太高、质量 / 惯量异常 |
| 物体从夹爪滑走 | 物理材质摩擦、指尖 collision、夹爪 drive |
| 关节跟不上目标 | drive stiffness / damping / max force / velocity limit |
| 末端去错地方 | 目标位姿、世界坐标、base pose、末端 frame |
| 切到速度控制后回不来 | control mode、stiffness 是否被置零 |

这张表的重点不是记参数，而是**判断问题在哪一层**：很多时候你以为是控制器不好，其实是 drive 太软；以为夹爪控制错了，其实是指尖没 collision 或摩擦太低。

## 小结

- 导入后的 USD 要分开看四类信息：视觉（看）、碰撞体（撞）、物理材质 / 摩擦（滑）、joint drive（动）。
- 体检遵循“先小后大”：先让单个资产可信，再组合，最后上任务。
- collision 不是 visual：从 visual 生成的碰撞体可能不稳，self-collision 要谨慎开。
- drive 是关节的虚拟执行器，分 position / velocity 两种模式；穿地、发抖、滑走、跟不上各有对应的排查层。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Physics](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/index.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Gain Tuner Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_robot_setup_gain_tuner.html)

## 导航

- 返回目录：[机器人资产与物理配置](../03-robot-and-physics.md)
- 上一页：[Articulation 关节体](02-articulation.md)
- 下一页：[其它导入器：MJCF / Onshape / Mesh](04-other-importers.md)
