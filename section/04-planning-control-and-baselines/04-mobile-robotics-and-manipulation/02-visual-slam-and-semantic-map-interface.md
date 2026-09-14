# 视觉 SLAM 与语义地图接口

目标：说明移动机器人在具身智能系统中如何把视觉定位、地图、语义对象和导航目标连接起来，而不是把 SLAM 当成孤立算法介绍。

本页需要覆盖：

- 视觉 SLAM / 视觉惯性里程计在移动机器人中的作用：提供 `map`、`odom`、`base_link` 等坐标关系，以及机器人在地图中的实时位姿。
- 视觉 SLAM、激光 SLAM、RGB-D 建图、语义地图之间的分工：哪个负责几何可通行区域，哪个负责对象、房间、语义区域和任务标签。
- 地图表达如何进入导航栈：occupancy grid、costmap、ESDF/TSDF、拓扑图、语义场景图分别适合什么导航决策。
- 语义目标如何变成导航目标：例如“去厨房”“靠近红色杯子”“到桌子左侧”如何落到 waypoint、pose goal、region goal 或 frontier。
- 与第 3 章感知接口的连接：对象检测、位姿估计、语义地图更新需要带 `frame_id`、`timestamp`、`confidence`、`staleness_ms`。
- 与第 8 章评测的连接：导航 benchmark 评测的是 task success、SPL、collision、path length、replanning 次数等，不在本页展开协议细节。
- 常见失败：定位漂移、地图过期、动态障碍物、语义目标错误绑定、坐标系跳变、目标点不可达、导航到位但操作不可达。

本页只保留写作框架，后续详细写作时应优先用 Nav2、RTAB-Map、ORB-SLAM3、VINS-Fusion、OpenVSLAM、Habitat / AI2-THOR 等工程入口举例。
