# Planning Scene 实战：添加障碍物并绕障规划

目标：在上一页 `hello_moveit` 的基础上加入碰撞物体，让 MoveIt 2 的规划请求从“空世界移动到目标”升级为“在规划场景中绕开障碍物移动到目标”。

我们只关注一条工程链路：**创建 collision object，把它加入 Planning Scene，然后观察规划轨迹如何绕开它。**

## Planning Scene 是规划器相信的世界

Planning Scene 不是一张普通图片，也不是只给 RViz 看的可视化图层。它是 MoveIt 2 在规划时使用的世界模型。规划器会基于这个模型判断哪些状态碰撞、哪些路径可行、哪些物体已经被机器人抓住。

| 组成 | 说明 | 出错时的典型现象 |
|---|---|---|
| RobotState | 当前关节状态和 link 位姿 | 起点和机器人实际状态不一致 |
| World Geometry | 桌面、箱子、墙等环境几何 | 轨迹穿过现实中的障碍物 |
| Collision Objects | 程序动态添加的碰撞物体 | RViz 看不到障碍物，规划也不绕开 |
| Attached Collision Objects | 被夹爪抓住并附着到 link 上的物体 | 抓起物体后仍按空夹爪规划 |
| Allowed Collision Matrix | 哪些对象之间允许接触 | 抓取时夹爪碰到物体却被判定失败 |

<div class="concept-note concept-orange">关键：规划器只会避开 Planning Scene 中存在并同步成功的物体。</div>

## 本例要做的改动

上一页的 `hello_moveit` 只设置了一个目标位姿，然后调用 `plan()` 和 `execute()`。这一页在它前面插入四个动作：

1. 引入 `PlanningSceneInterface`。
2. 创建一个 box 形状的 `CollisionObject`。
3. 把 box 放到机器人前方。
4. 将这个对象应用到 Planning Scene。

最终效果是：目标位姿仍然在机器人前方，但中间多了一个障碍物，规划轨迹必须绕过去。

![Planning Around Objects 规划结果](assets/tutorials/planning-around-object.png)
<div class="image-caption">来源：MoveIt Tutorials - Planning Around Objects。障碍物进入 Planning Scene 后，轨迹会绕开 box。</div>

## 第一步：加入 PlanningSceneInterface

在 C++ 文件中加入头文件：

```cpp
#include <moveit/planning_scene_interface/planning_scene_interface.hpp>
```

`MoveGroupInterface` 负责对某个 planning group 发起规划请求；`PlanningSceneInterface` 负责向 MoveIt 2 的 planning scene 添加、更新或删除世界物体。两者经常一起出现，但职责不同：

| 接口 | 主要职责 |
|---|---|
| `MoveGroupInterface` | 设置目标、调用 planner、执行轨迹 |
| `PlanningSceneInterface` | 管理场景中的 collision object |

## 第二步：把目标位姿放到需要绕障的位置

为了让绕障效果明显，目标位姿不再使用上一页的简单位置，而是放到会被 box 影响的区域：

```cpp
target_pose.orientation.y = 0.8;
target_pose.orientation.w = 0.6;
target_pose.position.x = 0.1;
target_pose.position.y = 0.4;
target_pose.position.z = 0.4;
move_group_interface.setPoseTarget(target_pose);
```

这里的位姿有两个注意点：

| 字段 | 说明 |
|---|---|
| `position` | 目标位置在 planning frame 下表达 |
| `orientation` | 四元数需要是合法旋转；不要随手填三个欧拉角进去 |

初学者可以先把这段当作“让末端到达某个可达目标”的示例。真正做项目时，目标位姿通常来自任务逻辑、感知结果或人工示教。

## 第三步：创建一个 box collision object

下面的函数创建一个名为 `box1` 的障碍物。它使用 planning frame 作为参考坐标系，形状是长方体，位置在机器人前方：

```cpp
auto const collision_object = [frame_id =
  move_group_interface.getPlanningFrame()] {
  moveit_msgs::msg::CollisionObject collision_object;
  collision_object.header.frame_id = frame_id;
  collision_object.id = "box1";

  shape_msgs::msg::SolidPrimitive primitive;
  primitive.type = primitive.BOX;
  primitive.dimensions.resize(3);
  primitive.dimensions[primitive.BOX_X] = 0.5;
  primitive.dimensions[primitive.BOX_Y] = 0.1;
  primitive.dimensions[primitive.BOX_Z] = 0.5;

  geometry_msgs::msg::Pose box_pose;
  box_pose.orientation.w = 1.0;
  box_pose.position.x = 0.2;
  box_pose.position.y = 0.2;
  box_pose.position.z = 0.25;

  collision_object.primitives.push_back(primitive);
  collision_object.primitive_poses.push_back(box_pose);
  collision_object.operation = collision_object.ADD;
  return collision_object;
}();
```

把这段拆开看，会更容易理解：

| 字段 | 本例取值 | 含义 |
|---|---|---|
| `header.frame_id` | `move_group_interface.getPlanningFrame()` | 物体位姿在哪个坐标系下定义 |
| `id` | `box1` | 后续更新、删除或 attach 时使用的名字 |
| `primitive.type` | `BOX` | 几何体类型 |
| `BOX_X / BOX_Y / BOX_Z` | `0.5 / 0.1 / 0.5` | box 在三个方向上的尺寸，单位是米 |
| `box_pose.position` | `(0.2, 0.2, 0.25)` | box 中心在 planning frame 中的位置 |
| `operation` | `ADD` | 把该物体加入场景 |

`frame_id` 是最容易被忽略的字段。如果 frame 错了，物体可能出现在意想不到的位置；如果物体位置不对，规划结果看起来就会像“MoveIt 2 没有避障”。

## 第四步：应用到 Planning Scene

创建对象只是准备消息，真正更新场景需要调用 `PlanningSceneInterface`：

```cpp
moveit::planning_interface::PlanningSceneInterface planning_scene_interface;
planning_scene_interface.applyCollisionObject(collision_object);
```

这一行执行后，RViz 中应当能看到 box。之后再调用 `plan()`，规划器就会把这个 box 纳入碰撞检查。

在真实系统里，还要注意场景同步。很多“刚加了障碍物但规划仍穿过去”的问题，本质上是添加对象和发起规划之间没有给系统留出同步时间，或者 RViz 看到的场景与 `move_group` 实际使用的场景不同步。学习 demo 时先用 RViz 确认物体出现，再观察 planned path 是否绕开。

## 运行方式

如果你已经在上一页保存过带 MotionPlanning 和 visual tools 的 RViz 配置，可以用它启动 demo。MoveIt Tutorials 中使用的形式是：

```bash
ros2 launch moveit2_tutorials demo.launch.py rviz_config:=kinova_hello_moveit.rviz
```

另一个终端运行你的节点：

```bash
ros2 run hello_moveit hello_moveit
```

观察顺序建议如下：

1. RViz 中是否出现 `box1`。
2. 目标 pose 是否仍然显示在预期位置。
3. 点击或等待程序规划后，planned path 是否绕开 box。
4. 执行时机械臂是否沿绕障轨迹运动。

## 常见问题排查

| 现象 | 优先检查 |
|---|---|
| RViz 中没有 box | `applyCollisionObject()` 是否调用，RViz 是否订阅 planning scene |
| box 出现但位置不对 | `header.frame_id`、`box_pose.position`、Fixed Frame |
| 轨迹仍然穿过 box | 物体是否在规划前同步，box 尺寸是否覆盖了路径 |
| 规划失败 | 目标可能不可达，或障碍物把可行通道完全挡住 |
| 执行前看不到轨迹 | 先确认 `plan()` 成功，再检查 display topic |

如果规划失败，不要第一反应就换 planner。先确认世界模型正确、目标可达、起点合法。规划器通常只是最后一层；前面的模型错了，后面再强的算法也会做出奇怪决定。

## 小结

Planning Scene 决定规划器“看见什么”。在空场景中能规划成功，不代表真实任务中就能安全执行；只有把桌面、箱体、工装和被抓物体正确加入场景，collision-aware planning 才有意义。本页的核心代码并不多：创建 `CollisionObject`、设置 frame / shape / pose / operation，再用 `PlanningSceneInterface` 应用到场景。

## 自查问题

1. `MoveGroupInterface` 和 `PlanningSceneInterface` 分别负责什么？
2. `CollisionObject.header.frame_id` 为什么重要？
3. `primitive.dimensions` 中的三个数单位是什么？
4. 如果 RViz 看到了 box，但轨迹仍穿过它，应该检查哪些同步问题？
5. 为什么不能把所有规划失败都归咎于 planner？

## 参考资料

- [Planning Around Objects](https://moveit.picknik.ai/main/doc/tutorials/planning_around_objects/planning_around_objects.html)
