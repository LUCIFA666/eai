# URDF 到 USD

上一部分你已经能在 Isaac Sim 里搭一个空场景。但真正的任务主角是机器人，而 Isaac Sim 的世界是 USD——它并不直接“吃”URDF。这一页解决的就是：把一台 URDF（很多时候还是 xacro 模板）机器人，变成 Isaac Sim 能稳定加载、能仿真的 USD 资产。

## 本节目标

本节围绕下面几个问题展开：

1. URDF 和 USD 分属哪两层，xacro、URDF、USD 三者怎么区分？
2. 怎么用 URDF Importer（GUI）和脚本两种方式把机器人导入成 USD？
3. 导入完成后，应该先做哪些「体检」确认资产没问题？

这一页写给会写 Python、可能在 ROS / MoveIt / RViz 里见过 URDF，但第一次在 Isaac Sim 里导机器人的读者。不要求你懂 USD 内部结构。

## URDF 和 USD 不是同一层东西

很多人把 URDF 和 USD 都当成“机器人模型文件”。这不算错，但它们其实是两个层级：

- **URDF** 更像一份**机器人结构说明书**：有哪些 link、link 之间靠哪些 joint 连接、每个 link 的 visual / collision / inertial 是什么。它天生服务于 ROS、TF、MoveIt 这套机器人生态。
- **USD** 更像 Isaac Sim 里的**整个舞台**：不只机器人，还有桌子、物体、相机、灯光、材质、物理场景、传感器，以及它们之间的引用和层级。Isaac Sim 用 USD 作为核心场景表示，所以最终进入它的是一个 USD stage，而不只是一个 URDF。

一句话类比：**URDF 是“机器人的零件图纸”，USD 是“整个仿真世界的布景清单”**。要把机器人搬进 Isaac Sim 这个世界，就得先把图纸翻译成场景能用的格式。

| 你想知道 | 在 URDF 里看 | 在 USD / Isaac Sim 里看 |
|---|---|---|
| 有哪些 link 和 joint | `<link>` / `<joint>` | `/World/Robot/...` 下的 link / joint prim |
| mesh 在哪里 | `mesh filename=...` | USD reference / payload / mesh prim / 材质绑定 |
| 关节怎么动 | joint type / axis / limit | articulation / drive / joint state |
| 能不能物理接触 | collision mesh / inertial | collision API / PhysX 属性 / 质量 / 接触 |
| 放在场景哪里 | URDF 通常不管 | prim path / xform / stage tree |

这也解释了一句要记住的话：**“URDF 能在 RViz 里显示”不等于“它能在 Isaac Sim 里稳定仿真”**——显示只需要 visual mesh，仿真还要 collision、质量、惯量和 drive 都对。

前面说 URDF / USD 是两个层级——导入完一台机器人就能直接看到：在视口里遍历一遍 stage，它不是一个 mesh，而是一棵 `link / joint` 子树。

```python
import omni.usd

stage = omni.usd.get_context().get_stage()
for prim in stage.Traverse():
    print(f"{str(prim.GetPath()):<34}{prim.GetTypeName()}")
```

以 Franka 为例，打印出来大致是这样（省略了各 link 下的 visual / collision / 材质子节点）：

```text
/World/Robot                      Xform
/World/Robot/panda_link0          Xform
/World/Robot/panda_joint1         PhysicsRevoluteJoint
/World/Robot/panda_link1          Xform
/World/Robot/panda_joint2         PhysicsRevoluteJoint
/World/Robot/panda_link2          Xform
/World/Robot/panda_joint3         PhysicsRevoluteJoint
/World/Robot/panda_link3          Xform
...
/World/Robot/panda_link7          Xform
/World/Robot/panda_joint8         PhysicsFixedJoint
/World/Robot/panda_link8          Xform
/World/Robot/panda_hand           Xform
/World/Robot/panda_finger_joint1  PhysicsPrismaticJoint
/World/Robot/panda_leftfinger     Xform
/World/Robot/panda_finger_joint2  PhysicsPrismaticJoint
/World/Robot/panda_rightfinger    Xform
```

每个 `panda_linkN` 是一个 link 节点，`panda_jointN` 是把它们连起来的 joint，根节点 `/World/Robot` 挂着 articulation root（具体路径和命名随导入器版本略有差异）。这就是 URDF 导入链路的典型结果：**整机在场景里是一棵 link/joint 子树，而不是单个 mesh 文件**。

## 先分清 xacro、URDF、USD 三层

项目里常拿到的不是干净的 `.urdf`，而是 `.urdf.xacro`。先记住这条链，别急着把文件直接丢给 Isaac Sim：

<figure class="doc-figure">
<p class="doc-figure-title">从模板到资产：三层各司其职</p>
<div class="figure-flow">
<div class="figure-node">.urdf.xacro —— 模板源：宏、参数、左右臂前缀、是否带夹爪</div>
<div class="figure-node">.urdf —— 展开后的结构说明书：link / joint / mesh 路径 / limit / 惯量 / 碰撞体</div>
<div class="figure-node">URDF Importer —— 导入配置：drive、collider、articulation、self-collision</div>
<div class="figure-node">.usd —— 可复用资产：reference 进 stage，仿真前先体检</div>
</div>
<p class="doc-figure-subtitle">不要把导入当终点：先生成，再导入，再体检，最后存成可复用资产。</p>
</figure>

`xacro` 是 URDF 的**模板语言**。URDF 只能描述一个确定的机器人；xacro 能用宏和参数生成不同版本（左右臂、带不带夹爪、不同命名前缀）。比如双臂机器人，纯 URDF 要把两条臂几乎重写两遍，xacro 把“一条臂”写成宏，再用不同前缀调用两次：

```xml
<xacro:macro name="robot_arm" params="prefix">
  <link name="${prefix}_link1"/>
  <joint name="${prefix}_joint1" type="revolute">
    <parent link="${prefix}_base"/>
    <child link="${prefix}_link1"/>
  </joint>
</xacro:macro>

<xacro:robot_arm prefix="left"/>
<xacro:robot_arm prefix="right"/>
```

关键是：**不要把“生成 URDF”和“导入 USD”混成一步**。稳妥的流水线分两段：

1. 在普通 Python / ROS 环境里，把 xacro 展开成 URDF；
2. 在 Isaac Sim 里，把 URDF 导入并保存成 USD。

这样 xacro 阶段能单独调试（不必每次启动 Isaac Sim），URDF 作为中间产物可被检查、提交、对比；万一 USD 导入失败，你也能判断问题出在“模板展开”还是“导入器”。

## 用 URDF Importer 导入（GUI）

Isaac Sim 的导入能力来自 `isaacsim.asset.importer.urdf` 扩展。第一次建议走 GUI，把界面和选项看一遍：

1. 确认 `isaacsim.asset.importer.urdf` 扩展已启用；
2. `File → Import`，选择 URDF 文件；
3. 设置导入选项：输出 USD 路径、固定底座还是移动底座、关节 drive、碰撞体、self-collision；
4. 点击 Import，机器人加入当前 stage，并生成可复用的 USD。

GUI 适合第一次理解导入器都有哪些旋钮。等你要批量转换、在服务器上跑或接进项目流水线，就该换成脚本。

## 脚本化导入（批量 / headless）

Isaac Sim 通过 `omni.kit.commands` 暴露两步：先建导入配置，再解析导入。

```python
import omni.kit.commands

# 1) 创建导入配置
status, cfg = omni.kit.commands.execute("URDFCreateImportConfig")
cfg.merge_fixed_joints = False  # 保留 fixed joint（link 更全、便于核对结构）；注意 5.1 起设 True 也不再合并带质量 / 惯量的 link
cfg.fix_base = True          # 机械臂常固定底座；移动 / 腿足机器人设 False
cfg.make_default_prim = True
cfg.distance_scale = 1.0     # 长度单位缩放，1.0 = 不缩放（URDF 本就是米）

# 2) 解析并导入，返回 stage 上的 prim 路径
status, prim_path = omni.kit.commands.execute(
    "URDFParseAndImportFile",
    urdf_path="/path/to/robot.urdf",
    import_config=cfg,
)
print("imported at:", prim_path)
```

headless 下最好直接让导入器把机器人写成独立 USD：给 `URDFParseAndImportFile` 传一个 `dest_path` 即可，省得留外部 layer / reference / 绝对路径，换机器、换目录就坏。

```python
status, prim_path = omni.kit.commands.execute(
    "URDFParseAndImportFile",
    urdf_path="/path/to/robot.urdf",
    import_config=cfg,
    dest_path="/path/to/robot.usd",   # 导入时直接写出独立 USD
)
```

带纹理的资产尤其要走 `dest_path`——官方文档明确：这样才能保证纹理被正确打包、加载。如果你是在当前 stage 里改了很多东西、想把整个舞台另存，再用通用的 `stage.Flatten()` + `Export`；对“单台机器人资产”来说 `dest_path` 更直接。

需要在导入前微调机器人时，可以把一步式拆成两步——先 `URDFParseFile` 解析出 `robot_model`，改完再 `URDFImportRobot` 导入。最常见的用途是统一设置关节 drive：

```python
status, robot_model = omni.kit.commands.execute(
    "URDFParseFile", urdf_path="/path/to/robot.urdf", import_config=cfg,
)
for j in robot_model.joints:
    robot_model.joints[j].drive.strength = 1047.2   # 关节刚度
    robot_model.joints[j].drive.damping = 52.36     # 关节阻尼
status, prim_path = omni.kit.commands.execute(
    "URDFImportRobot", urdf_robot=robot_model, import_config=cfg,
)
```

（`URDFParseAndImportFile` 本质就是把这两步连起来。）

把导入拆成可控的小步、必要时回退，不是“高级技巧”，而是资产流水线该有的韧性：机器人描述来自不同厂家、不同 ROS 包、不同历史版本，mesh 路径、命名、惯量、collision、mimic joint 都可能让导入器表现不一致。

**版本提醒**：5.x 导入器在 `isaacsim.asset.importer.urdf` 命名空间，命令名和配置字段随版本可能变化。拿不准时，先用 GUI 导入一次、看它生成的 USD 结构，再脚本化。

## 导入后先体检

导入后最该做的不是马上写控制器，而是检查资产的物理属性。下面是最常见的检查项，细节会在后面的 [物理属性配置与检查](03-physics-audit.md) 一节展开（紧接的下一页是 [Articulation 关节体](02-articulation.md)）：

| 检查项 | 看什么 |
|---|---|
| 机器人 prim | stage 里真出现了机器人，而不是只建了空 stage |
| 根 prim 路径 | 稳定且符合预期，如 `/World/Robot` |
| articulation root | 是否正确——它决定这台机器人是不是一个可驱动的关节体 |
| visual mesh | 完整，材质 / 纹理没丢 |
| collision mesh | 存在、不过粗、不互相穿插 |
| scale | 是米制，机器人尺寸合理 |
| fix_base | 机械臂固定，移动 / 腿足机器人不固定 |
| joint drive | stiffness / damping / limit 适合控制 |

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 能在 RViz 显示就能在 Isaac Sim 仿真 | 显示只需要 visual mesh | 导入后按体检表逐项查 |
| `.urdf.xacro` 可以直接丢给导入器 | xacro 是模板，还没展开 | 先把 xacro 展开成 `.urdf` 再导入 |
| `package://...` 路径导入器认识 | 那是 ROS 包索引，Isaac Sim 不一定认 | 让 ROS 包可见，或换成绝对路径 |
| visual mesh 漂亮 = collision 没问题 | collision 常是简化体，甚至缺失 | 在 GUI 里单独查 collision mesh |
| 导入一次就一劳永逸 | 留外部 layer / reference / 绝对路径，换机就坏 | 导入时用 `dest_path` 写出独立 USD，必要时再打包资产 |
| 固定机械臂忘了 `fix_base` | 机器人会被重力直接拽下去 | 机械臂 `fix_base=True` |

## 小结

- URDF 是机器人结构说明书，USD 是 Isaac Sim 的完整舞台；导入做的就是 URDF / xacro → USD 资产。
- 拿到 xacro 先展开成 URDF 再导入；两段式流水线方便调试和归档。
- 导入有两条路：GUI（`File → Import`）适合第一次理解选项，脚本（`omni.kit.commands` / `URDFParseAndImportFile`）适合批量和 headless。
- 导入“成功”只是起点，必须体检 mesh / collision / scale / articulation root / drive / fix_base——细节见后面《物理属性配置与检查》一节。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Tutorial: Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)

## 导航

- 返回目录：[机器人资产与物理配置](../03-robot-and-physics.md)
- 下一页：[Articulation 关节体](02-articulation.md)
