# 一个完整实验流程：以 ObjectNav 为例

目标：用 ObjectNav 作为例子，串起 Habitat 实验中的数据集、episode、传感器、动作空间、策略、训练、评测和实验记录。

ObjectNav 是学习 Habitat 的好例子。它比 PointNav 多了语义目标，需要 agent 找到某一类物体；但它又不像 Rearrangement 那样涉及复杂抓取和物体状态。因此 ObjectNav 很适合作为从基础导航走向语义导航的过渡任务。

## ObjectNav 在问什么

ObjectNav 的目标不是一个坐标，而是一个物体类别。

```text
给定一个陌生室内场景。
agent 从某个起点出发。
目标是一个物体类别，比如 chair、bed、toilet。
agent 根据 RGB / depth / semantic / GPS+Compass 等观测选择动作。
当它认为已经到达目标附近时，执行 stop。
评测系统判断是否成功，并计算路径效率。
```

这和 PointNav 的区别很大。PointNav 可以直接给目标坐标；ObjectNav 要求 agent 理解场景语义，知道哪些区域更可能有目标物体，还要在看不到目标时进行探索。

## 第一步：确定 scene dataset

ObjectNav 依赖语义信息，所以 scene dataset 不是随便选的。你要先确认使用哪个场景数据集：Matterport3D、HM3D-Semantics，还是其他带语义标注的场景。

| 检查项 | 说明 |
|---|---|
| scene 文件 | `.glb` 或其他可被 Habitat-Sim 加载的场景文件 |
| navmesh | 用于起点采样、路径规划和 SPL 计算 |
| semantic 文件 | ObjectNav 需要目标类别和实例信息 |
| scene config | 指向场景、语义和资源路径 |
| split | train / val / test 场景如何划分 |

如果 semantic 没有正确加载，ObjectNav 的目标类别和语义观测都会出问题。RGB 图正常不代表 ObjectNav 数据就正常。

## 第二步：确定 episode dataset

ObjectNav 的 episode dataset 记录任务实例。一个 episode 大致包含：

```text
episode_id
scene_id
start_position
start_rotation
object_category
goals / goal positions
shortest_path_distance
```

不同版本的具体字段可能不同，但核心都是：在哪个场景，从哪里出发，找什么物体，成功条件如何判断。

episode dataset 决定任务难度。比如起点离目标很近，任务会简单；目标类别很少，任务也会简单；如果训练和测试场景重叠，泛化评估就不干净。因此写实验时必须记录 episode split。

## 第三步：确定传感器

ObjectNav 常见传感器组合包括：

| 输入 | 影响 |
|---|---|
| RGB | 需要模型从图像中识别物体和场景线索 |
| depth | 帮助建图、避障和判断空间结构 |
| semantic | 直接提供语义类别，会显著改变任务难度 |
| GPS+Compass | 提供位姿相关信息，能降低定位难度 |

这一步非常关键。一个 RGB-D agent 和一个 RGB-D + semantic agent 不是同一难度；一个有 GPS+Compass 的 agent 和一个完全依赖视觉里程计的 agent，也不能直接比较。

实验记录里建议写成：

```text
sensors: RGB_SENSOR, DEPTH_SENSOR, GPS_COMPASS_SENSOR
semantic sensor: off
resolution: 256 x 256
```

不要只写“使用视觉输入”。

## 第四步：确定动作空间

ObjectNav 常用离散导航动作：

```text
move_forward
turn_left
turn_right
stop
```

`stop` 很重要。agent 必须在认为已经到达目标附近时主动停止。只会靠近目标但不会 stop，任务仍可能失败。

动作空间也会影响结果。如果一个方法使用离散动作，另一个方法使用连续速度控制，二者不能直接只比 success。需要说明动作粒度、步长、转角、噪声模型和控制方式。

## 第五步：选择策略

ObjectNav 可以用多种策略完成：

| 策略类型 | 说明 |
|---|---|
| random policy | 只用于检查环境能否运行，不能作为有效方法 |
| PPO / RL policy | 从 reward 中学习导航策略 |
| imitation learning | 从专家路径或示范学习 |
| map-based planner | 建图、目标检测、路径规划组合 |
| VLM / LLM-assisted policy | 用视觉语言模型或语言模型辅助目标判断和规划 |

## 第六步：训练与验证

训练时通常关注 reward、loss、episode length、train success 等信号。但真正评测时，应该看验证集或测试集上的指标。

| 指标 | 说明 |
|---|---|
| success | 是否成功找到目标并停止 |
| SPL | 成功率和路径效率的组合 |
| distance_to_goal | 最终离目标距离 |
| path length | 实际行走路径长度 |
| failure cases | 找错类别、没探索到、撞墙、不会 stop 等 |

只看训练曲线不够。ObjectNav 的重点是泛化到新场景和新物体实例，所以验证集表现更重要。

## 第七步：写实验记录卡

一个合格 ObjectNav 实验，至少应该写清下面内容：

```text
task: ObjectNav
Habitat-Sim: version or commit
Habitat-Lab: version or commit
scene dataset: HM3D / Matterport3D / other
episode dataset: name and split
object categories: category list or benchmark definition
sensors: RGB / depth / semantic / GPS+Compass
action space: move_forward / turn_left / turn_right / stop, step size, turn angle
policy: PPO / IL / planner / VLM-based method
training frames or episodes: ...
metrics: success, SPL, distance_to_goal
random seed: ...
```

## 常见问题

| 现象 | 可能原因 |
|---|---|
| agent 一直找不到目标 | 目标类别太难、探索不足、语义输入缺失、训练不足 |
| RGB 有图但 ObjectNav 报错 | episode 指向的 scene 或语义文件不完整 |
| success 不低但 SPL 很差 | 能找到目标，但路径很绕 |
| 训练集表现好，验证集差 | 场景记忆或过拟合，不具备泛化能力 |
| agent 到目标旁边但失败 | 没执行 stop，或成功距离 / 可见性条件没满足 |

## 本页小结

ObjectNav 能把 Habitat 的实验链路完整串起来：scene dataset 提供房间和语义，episode dataset 提供任务实例，sensor 决定 agent 看见什么，action space 决定它怎么动，policy 决定如何决策，metric 决定结果怎么解释。理解了 ObjectNav，再看更复杂的 VLN、EQA 和 Rearrangement 会顺很多。

## 导航

- 上一页：[从 1.0 到 3.0](06-habitat-versions.md)
- 返回：[Habitat 简介](../01-habitat-simulation.md)
- 下一页：[与其他仿真生态对比](08-comparison.md)

## 进一步阅读可以看：

- [Habitat-Lab documentation](https://aihabitat.org/docs/habitat-lab/)
- [HM3D dataset](https://aihabitat.org/datasets/hm3d/)
- [Habitat-Sim supported datasets](https://github.com/facebookresearch/habitat-sim/blob/main/DATASETS.md)