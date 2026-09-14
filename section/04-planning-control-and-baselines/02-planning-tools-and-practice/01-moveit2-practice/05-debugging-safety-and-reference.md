# 排错、安全与速查：把 MoveIt 2 当工程系统使用

目标：把各类现象、命令和检查项整理成排错流程和速查表。遇到 MoveIt 2 规划失败时，先判断责任层，而不是直接换 planner。

## 故障责任层

| 层级 | 典型现象 | 优先检查 |
|---|---|---|
| 环境 | workspace 构建失败 | ROS 2 是否 source、`rosdep` 是否完成、内存是否不足 |
| RViz 插件 | 打开 RViz 后没有 MotionPlanning | 是否在 Displays 中添加 MotionPlanning display |
| Frame | RViz 显示异常或机器人不在预期位置 | Fixed Frame 是否设置为 `/base_link` |
| Planning Group | 面板中 group 不对或无法规划 | 是否选择 `manipulator` |
| Start / Goal State | 规划起点或目标不符合预期 | 绿色 start state、橙色 goal state 是否显示正确 |
| Collision | link 变红或目标拖不进去 | 是否处于自碰撞，是否勾选 collision-aware IK |
| Planned Path | 点击 Plan 后没有合理路径 | 起点、目标、碰撞、工作空间是否合理 |
| Planning Scene | 障碍物未影响轨迹 | box 是否出现在 RViz，场景是否同步 |
| MTC Stage | 抓放任务失败 | 查看失败发生在哪个 stage |

<div class="concept-note concept-orange">经验：先查输入条件，再查 planner</div>

很多时候问题不在 OMPL，而在目标、状态、场景和配置。换 planner 只能改变搜索方式，不能修复错误 frame、过期 joint state 或不存在的场景物体。

## 命令速查

| 任务 | 命令 |
|---|---|
| source ROS 2 | `source /opt/ros/jazzy/setup.bash` |
| 创建 workspace | `mkdir -p ~/ws_moveit/src` |
| 下载教程仓库 | `git clone -b <branch> https://github.com/moveit/moveit2_tutorials` |
| 导入依赖仓库 | `vcs import --recursive < moveit2_tutorials/moveit2_tutorials.repos` |
| 安装依赖 | `rosdep install -r --from-paths . --ignore-src --rosdistro $ROS_DISTRO -y` |
| 构建 workspace | `colcon build --mixin release` |
| 低内存顺序构建 | `colcon build --mixin release --executor sequential` |
| source workspace | `source ~/ws_moveit/install/setup.bash` |
| 启动 RViz demo | `ros2 launch moveit2_tutorials demo.launch.py` |
| 创建 C++ package | `ros2 pkg create --build-type ament_cmake --dependencies moveit_ros_planning_interface rclcpp --node-name hello_moveit hello_moveit` |
| 启动 MTC demo | `ros2 launch moveit_task_constructor_demo demo.launch.py` |
| 运行 MTC 抓放 | `ros2 launch moveit_task_constructor_demo run.launch.py exe:=pick_place_demo` |

## RViz 速查

| 项 | 官方设置 / 现象 |
|---|---|
| Fixed Frame | `/base_link` |
| Robot Description | `robot_description` |
| Planning Scene Topic | `/monitored_planning_scene` |
| Trajectory Topic | `/display_planned_path` |
| Planning Group | `manipulator` |
| Start State | 绿色机器人，可作为规划起点 |
| Goal State | 橙色机器人，可作为规划目标 |
| Planned Path | 规划轨迹，可用 trail 或 trajectory slider 查看 |
| Collision-Aware IK | 勾选后 IK 会尝试避开碰撞解 |

## 现象到章节索引

| 现象 | 回看小节 |
|---|---|
| 不知道 MoveIt 2 和教程环境怎么装 | MoveIt 2 引入 |
| RViz 中没有 MotionPlanning 面板 | 基础规划实战 |
| 分不清绿色、橙色和轨迹机器人 | 基础规划实战 |
| 不知道如何把 RViz 操作写成 C++ | 基础规划实战 |
| 障碍物没有影响规划轨迹 | Planning Scene 实战 |
| 规划绕障示例跑不通 | Planning Scene 实战 |
| 抓放任务失败但不知道失败在哪里 | 任务规划实战 |
| 想继续学 Servo / Setup Assistant / MoveItCpp | 本页“后续学习方向” |

## 真机前安全提醒

迁移到真实机器人前，至少要做这组检查：

1. 急停按钮可用，操作者知道如何触发。
2. 初始速度和加速度缩放足够低。
3. 工作空间内没有人和易碎物。
4. URDF collision geometry 足够保守。
5. joint limits 与真实硬件一致。
6. controller joint names、顺序和接口类型一致。
7. 先执行短距离、无接触、无负载轨迹。
8. Planning Scene 中加入桌面、夹具和固定障碍物。

## 后续学习方向

后面可以继续学习：

| 方向 | 说明 |
|---|---|
| MoveIt Servo | 适合遥操作、视觉伺服和持续姿态跟踪；需要使用官方 Examples / Servo 文档。 |
| Setup Assistant | 用自己的 URDF 生成 MoveIt 配置包；需要在后续专题中重新声明资料来源。 |
| MoveItCpp | 更直接访问 MoveIt 核心能力的 C++ 接口；适合后续进阶工程专题。 |
| 自定义规划器配置 | OMPL、Pilz、CHOMP、STOMP 等 pipeline / planner 参数配置。 |

## 小结

MoveIt 2 是一个工程系统。工程系统的排错方式不是“看到失败就换算法”，而是把问题放回责任层：环境、RViz、frame、start/goal、碰撞、Planning Scene、stage。只要这个顺序建立起来，MoveIt 2 的复杂性会从一团报错变成一张能走的地图。
