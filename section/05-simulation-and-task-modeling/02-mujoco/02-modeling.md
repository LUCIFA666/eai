# 建模（MJCF 与数据）

在 MuJoCo 里，一台机器人长什么样、有几个关节、每个关节能转多少、各部件是什么形状，全写在一份文本文件里，这种文件用的格式叫 MJCF。某种意义上，读懂这份文件，就等于读懂了这台机器人。而后面的控制、观测、抓取，本质上都是在和它（编译后的 `mjModel` / `mjData`）打交道，所以这一章是后面一切的地基。我们就拿一台真实机器人的模型来读：Franka Panda 机械臂，来自 DeepMind 的现成模型库 mujoco_menagerie。它的 MJCF 文件，我们会从整体骨架一路读到具体字段，读懂之后再动手改上一两处，看看仿真里有什么变化。

## 前置概念

读这一章前，建议先理解（详见 [MuJoCo 程序怎么运转](01-overview/02-mental-model.md)）：

- **MJCF**：MuJoCo 描述模型的 XML 格式。
- **mjModel / mjData**：编译后的静态结构 / 每步变化的动态状态。
- **step 循环**：`ctrl → mj_step → qpos/qvel/sensor → 重复`。

## 学习路径

| 小节 | 读完能回答 | 重点 |
|---|---|---|
| [MJCF 整体骨架](02-modeling/01-mjcf-skeleton.md) | 一个 MJCF 文件有哪些顶层节？ | compiler / option / default / asset / worldbody / actuator / sensor / keyframe |
| [body 树与关节](02-modeling/02-body-and-joint.md) | body 之间怎么嵌套？joint 有哪些类型？ | body 树、joint 四类型、inertial、site |
| [坐标系与朝向](02-modeling/03-coordinate-frames.md) | 读到一个 xpos，是世界还是局部？ | World / Body / Local frame、xyz=RGB、四元数 wxyz |
| [几何与资产](02-modeling/04-geom-and-asset.md) | visual 和 collision 几何有什么不同？ | geom 类型、mesh、material、texture |
| [default 继承](02-modeling/05-default-inheritance.md) | 没显式写的属性从哪里继承？ | `<default>` 类比 CSS、嵌套、childclass |
| [mjModel vs mjData](02-modeling/06-mjmodel-vs-mjdata.md) | 哪些值会变、哪些不会？ | 静态 vs 动态，编译过程，常见误解 |
| [常用字段速查](02-modeling/07-common-fields.md) | qpos / qvel / ctrl / sensordata 分别是什么？ | 字段按用途分类 + 一张速查表 |
| [keyframe 与命名](02-modeling/08-keyframe-and-naming.md) | 怎么设初始姿态？怎么用名字找对象？ | keyframe、mj_name2id、data.body("...") |
| [URDF ↔ MJCF](02-modeling/09-urdf-to-mjcf.md) | URDF 文件能直接用吗？怎么转？ | 两种格式的差异、加载 URDF 的限制、转换工作流 |
| [动手：改一个模型](02-modeling/10-hands-on-modify.md) | 自己改一处，能看到什么变化？ | 改 Panda、加 free joint、换 UR5e |

## 导航

- 上一节：[认识 MuJoCo](01-overview.md)
- 返回上级：[MuJoCo](../02-mujoco.md)
- 下一节：[控制与物理](03-control-and-physics.md)
