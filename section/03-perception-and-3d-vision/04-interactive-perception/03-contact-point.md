# 3D Contact Point

> 难度：[高级] | 预计用时：60 分钟
> 先修：[Affordance Heatmap](02-affordance-heatmap.md)

目标：把 2D 可供性结果落到 3D 接触点、法向、接近方向和执行约束上，让规划器真正能用。

## 先弄懂三个关键概念

**surface normal（表面法向量）**：垂直于物体表面的方向。告诉机器人接触面朝哪个方向。例如桌面法向量是 `(0, 0, 1)` 竖直向上。

**approach vector（接近向量）**：机器人末端应该从哪个方向接近接触点。例如从正上方抓杯子，接近向量是 `(0, 0, -1)`。

**pregrasp pose（预抓取姿态）**：接触前的准备位置。通常是沿着 approach vector 远离 contact point 的一段距离。真实接触前，夹爪要先移动到 pregrasp，再沿 approach 向 contact point 逼近。

**IK（逆运动学）**：Inverse Kinematics，从目标位置求关节角度。给定末端的目標位置和朝向，IK求解每个关节应该转多少度。

2D heatmap 只是在相机画面里说“这里值得试试”，3D contact point 才是在机器人工作空间里说“末端要到哪里、朝什么方向接近、宽度要开多大”。前者像地图上的标注，后者像导航给出的精确停车位。只要任务需要真实接触，最终就必须从像素走到 3D。

## 本页目标

这一页读完后，我们希望能一起把下面几件事说明白：

- 解释 pixel affordance 如何通过 depth、内参与外参变成 base frame 下的 3D 点。
- 写出 contact point、surface normal、approach vector 与 pregrasp pose 的关系。
- 判断哪些字段缺失会让 planner 无法执行。
- 为抓把手、按按钮、抓杯子等任务写出最小 contact contract。

## 从像素到 3D 的路线

```text
top affordance pixel (u, v)
      + depth(u, v)
      + camera intrinsics
      -> 3D point in camera frame
      + extrinsics
      -> 3D point in base frame
      + local geometry / normal estimate
      -> contact point + normal + approach
```

这条链上任何一环坏掉，planner 都可能拿到一个“看起来合理、实际上不可达”的目标。

## 最小几何公式回顾

```text
x = (u - cx) * z / fx
y = (v - cy) * z / fy
z = depth(u, v)
P_base = T_base_camera * P_camera
```

注意：这里的 `z` 必须是与相机模型一致的深度单位，`T_base_camera` 也必须和当前相机 frame 完全匹配。

## contact point 还不够，为什么还要 normal 和 approach

| 字段 | 作用 |
|---|---|
| `contact_point_xyz` | 告诉末端要去哪里 |
| `surface_normal_xyz` | 告诉局部接触面朝向 |
| `approach_vector_xyz` | 告诉末端应从哪个方向接近 |
| `pregrasp_offset_m` | 告诉接触前的安全准备位姿 |
| `required_gripper_width_m` | 告诉夹爪张开多少 |

如果只有一个 3D 点，planner 仍然不知道末端应如何朝向与接近。

## 三个典型任务对比

| 任务 | contact point 要求 | 额外约束 |
|---|---|---|
| 抓杯子 | 点落在侧壁可夹持区域 | 夹爪宽度、避开桌面 |
| 拉抽屉把手 | 点落在把手中心附近 | approach 沿把手法向，留出拉动空间 |
| 按按钮 | 点落在按钮中心 | approach 近似垂直面板 |

这说明 3D contact point 总是和动作语义绑在一起。

## 一个推荐的输出结构

```yaml
contact_candidate:
  object_id: drawer_handle_01
  action_type: pull
  frame_id: panda_link0
  contact_point_xyz_m: [0.62, -0.05, 0.31]
  surface_normal_xyz: [0.0, 0.0, 1.0]
  approach_vector_xyz: [-1.0, 0.0, 0.0]
  pregrasp_offset_m: 0.08
  required_gripper_width_m: 0.035
  confidence: 0.74
  failure_code: null
```

## 法向和接近方向怎么来

来源通常有三类：

| 来源 | 优点 | 风险 |
|---|---|---|
| depth / pointcloud 局部平面拟合 | 直接、可解释 | 噪声和空洞影响大 |
| CAD / mesh 先验 | 稳定，适合已知对象 | 与实物偏差会误导 |
| 学习模型直接预测 | 端到端方便 | 更依赖训练分布 |

教学场景里，优先强调可解释的几何估计更容易排错。

## planner 为什么还需要 pregrasp pose

真实接触通常不是“直接冲到 contact point”。更常见的流程是：

```text
pregrasp pose
   -> 沿 approach vector 逼近
   -> 到 contact point
   -> 触发闭手 / 按压 / 拉动
```

如果没有 `pregrasp_offset` 或等效的安全接近约束，系统很容易在靠近前就碰撞。

## 常见失败模式

| 失败 | 现象 | 原因 |
|---|---|---|
| 点在物体外 | 规划到空中或桌面里 | heatmap 与 mask 不一致 |
| 法向反了 | 末端从错误方向接近 | 法向估计方向歧义 |
| 点对了但不可达 | IK 或碰撞失败 | 缺 pregrasp / 障碍约束 |
| 宽度不匹配 | 抓取前就碰撞或夹不住 | 没估算物理尺寸 |

## 自检问题

1. 为什么 2D 上一个高分像素还不能直接当作机器人接触目标？
2. `surface_normal` 与 `approach_vector` 为什么通常不能省略成一个字段？
3. 如果点和法向都正确，但 planner 仍报碰撞，最可能还缺哪类信息？

## 练习

### [观察] 为三种动作写 3D 接触需求

1. 选择抓杯子、拉抽屉、按按钮三个任务。
2. 分别写出每个任务至少需要哪三个 3D 字段。

完成后，可以先用下面几条检查这一部分是否已经到位：
- 三个任务的字段组合明显不同。
- 能解释哪一个任务最依赖正确法向。

### [复现] 写一份 contact contract

1. 为一个动作定义 `contact_candidate` schema。
2. 至少包含 `contact_point_xyz_m`、`surface_normal_xyz`、`approach_vector_xyz`、`confidence`、`failure_code`。
3. 写出它如何与 planner 对接。

完成后，可以先用下面几条检查这一部分是否已经到位：
- schema 足以让 planner 尝试生成 pregrasp pose。
- 能指出至少一个会导致执行不可行的缺失字段。

## 导航

- 上一节：[Affordance Heatmap](02-affordance-heatmap.md)
- 返回本章：[感知与三维视觉](../README.md)
- 下一节：[抓取位姿生成](04-grasp-pose-generation.md)


