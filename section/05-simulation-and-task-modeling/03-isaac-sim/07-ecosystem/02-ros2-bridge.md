# ROS 2 Bridge

上一页你理解了 Action Graph——数据沿图流动、被 tick 驱动。这一页用它干一件可选但很实用的事：把 Isaac Sim 接进 **ROS 2**。这里不讲真机部署，只讲纯仿真里的话题发布与订阅：让 RViz、MoveIt / Nav2 或你自写的 ROS 2 节点读到 Isaac Sim 的 `/clock`、`/joint_states`、`/tf`、相机和雷达话题。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么要把仿真接进 ROS 2，启用前要先做哪两件事？
2. ROS 2 Bridge 的桥接机制是怎么把数据发出去的？
3. 连不通或收不到时，DDS、`DOMAIN_ID` 和 topic 该怎么对齐排查？

阅读这一页前，最好已经能跑通仿真闭环，并想把它接上 ROS 2。你需要对 ROS 2 的话题（topic）有基本概念；桥接的"收发"在 Isaac Sim 里基本都是用上一页的 **Action Graph 节点**实现的。

## 为什么把仿真接进 ROS 2

ROS 2 Bridge 的核心价值就一句话：**把 Isaac Sim 内部数据翻译成 ROS 2 世界通用的话题**。

这样外部节点不需要懂 Isaac Sim API，只要订阅 `/joint_states`、`/scan`、`/camera` 或 `/tf` 就能工作。你可以用 RViz 看 TF 和点云，用 MoveIt / Nav2 这类 ROS 2 工具链做规划验证，也可以让自写节点订阅观测话题、发布控制话题，和仿真形成闭环。

一句话类比：**ROS 2 Bridge 像翻译官兼接线员**——把仿真内部的关节、相机、雷达"翻译"成 ROS 2 世界通用的话题，再"接线"给 RViz、Nav2 或你的外部节点。

## 启用前的两件事

**1）启用扩展**：`Window > Extensions` 搜索 "ROS 2 Bridge"，启用 `isaacsim.ros2.bridge`。同一时间只能启用一个 ROS 桥接扩展；切换时先禁用一个再启用另一个。

**2）启动前先 source ROS 2**：在启动 Isaac Sim（或运行 standalone 脚本）的**同一个终端**里，先 `source /opt/ros/humble/setup.bash`（或 jazzy）。Isaac Sim 会加载你系统 ROS 2 的库来连接桥接。如果没 source 就启用，它会退回自带的预打包 Humble 库兜底——能跑，但容易和你系统的 ROS 2 版本 / 消息不一致。

```bash
# Linux 上的典型启动顺序
source /opt/ros/humble/setup.bash
./isaac-sim.sh            # 或 ./python.sh your_standalone_script.py
```

## 桥接机制

这是初学者最容易误解的一点：**桥接扩展本身不发任何数据**。真正"发布关节状态、发布相机、发布 TF、订阅指令"的，是 Action Graph 里的一组节点。

<figure class="doc-figure">
<p class="doc-figure-title">Isaac Sim ↔ ROS 2 端到端通路</p>
<div class="figure-flow">
<div class="figure-node"><strong>Isaac Sim 仿真：</strong>关节、相机、雷达、IMU 等传感器与机器人状态</div>
<div class="figure-node"><strong>Action Graph 节点：</strong>Publish Joint State / Clock / TF、Camera Helper、RTX Lidar Helper……</div>
<div class="figure-node"><strong>ROS 2 话题：</strong>/clock、/joint_states、/tf、/camera、/scan、/imu（两端 RMW 与 DOMAIN_ID 要一致）</div>
<div class="figure-node"><strong>外部 ROS 2 节点：</strong>RViz2、Nav2、MoveIt、自写节点或走 ROS 2 的策略进程</div>
</div>
<p class="doc-figure-subtitle">先 source ROS 2、对齐 DDS / DOMAIN_ID、发 /clock 配 use_sim_time，是桥接能通的三个前提。</p>
</figure>

常用的发布 / 订阅节点：

| 你想发 / 收什么 | 关键节点 | 话题（示例） |
|---|---|---|
| 仿真时钟 | ROS2 Publish Clock | `/clock`（配合 `use_sim_time`） |
| 关节状态 / 指令 | ROS2 Publish / Subscribe Joint State | `/joint_states` |
| TF 变换树 | ROS2 Publish Transform Tree | `/tf` |
| 里程计 | ROS2 Publish Odometry | `/odom` |
| 相机 RGB / 深度 / 内参 | ROS2 Camera Helper | `/camera/rgb`、`/camera/depth`、`/camera/camera_info` |
| RTX 激光雷达 | ROS2 RTX Lidar Helper | `/scan`、`/point_cloud` |
| IMU | Isaac Read IMU Node → ROS2 Publish IMU | `/imu` |

一张"发布关节状态 + 时钟"的最小图长这样（相机和雷达稍特殊，要先经 `Isaac Create Render Product`，见观察单元的[《RTX Lidar / IMU》](../05-observation/02-lidar-imu.md)一页）：

```text
On Playback Tick ─exec─┬─▶ ROS2 Publish Joint State   (targetPrim = /robot)
                       └─▶ ROS2 Publish Clock
Isaac Read Simulation Time ─simTime─┬─▶ Publish Joint State.timeStamp
                                    └─▶ Publish Clock.timeStamp
ROS2 Context ─context─┬─▶ Publish Joint State.context
                      └─▶ Publish Clock.context
```

**更稳妥的起步方式**：别一开始就手连几十个节点。用 `Tools > Robotics > ROS 2 OmniGraphs`，里面有相机、RTX Lidar、TF、Joint State 等模板，弹窗填图路径、目标 prim、`frameId`、命名空间、勾选要发布的数据，自动生成整张图。确认能发布后，再打开图看它连了什么——这是理解桥接最快的路径。

## DDS 与 DOMAIN_ID 要对齐

ROS 2 底层用 DDS 中间件，两大实现是 **Fast DDS** 和 **Cyclone DDS**。Isaac Sim 与外部节点要互通，两端的 RMW（DDS 实现）和 `ROS_DOMAIN_ID` 必须一致，否则话题"看得见名字、收不到数据"，甚至互相看不见。

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0
```

选哪个实现不是重点，关键是两端 RMW 一致；Isaac Sim 预打包并默认回退 Fast DDS，NVIDIA 的 Isaac ROS（真机侧）文档则推荐 Cyclone。

经验：两端话题不通，**先查这两个环境变量是否一致**，再查 QoS 和 namespace。

## 控制发布频率

Action Graph 每个仿真帧 tick 一次，发布率默认跟仿真帧率走。给每个 publisher 单独降频，改它的 `frameSkipCount`（上一页讲过）：

```text
/joint_states  frameSkipCount=1  → ~30 Hz（仿真 60 FPS 时）
/imu           frameSkipCount=1  → ~30 Hz
/scan          frameSkipCount=11 → ~5 Hz
/camera/rgb    frameSkipCount=3  → ~15 Hz
```

## 桥接输出示例

下面是 Isaac Sim 通过 `isaacsim.ros2.bridge` 发布 ANYmal-C 的 `/joint_states` 与 `/clock` 后，用 `ros2` 命令行抓到的输出摘要：

```text
$ ros2 topic list
/clock
/joint_states
/parameter_events
/rosout

$ ros2 topic info /joint_states
Type: sensor_msgs/msg/JointState
Publisher count: 1

$ ros2 topic hz /joint_states
average rate: 158.084
	min: 0.004s max: 0.061s std dev: 0.00427s window: 4294

$ ros2 topic echo /joint_states --once
header:
  stamp:
    sec: 88
    nanosec: 16671257
name:
- LF_HAA
- LH_HAA
- RF_HAA
- RH_HAA
- LF_HFE
- ...（共 12 个关节）
```

这里的 `average rate` 按**墙钟时间**统计，而 headless 仿真一帧步进多快取决于当时的 GPU 负载，所以这个频率会浮动。它反映的是“仿真当前跑多快”，不是某个固定的目标频率。

验证桥接通不通，就这几条命令：

```bash
ros2 topic list                 # 话题有没有出来
ros2 topic hz /joint_states     # 发布频率
ros2 topic echo /scan           # 实际数据
rviz2                           # 可视化（Fixed Frame 选对、勾 use_sim_time）
```

**在服务器上运行的两个关键点**：① 启动前把桥接自带的 humble 库目录加进 `LD_LIBRARY_PATH`（`.../isaacsim.ros2.bridge/humble/lib`），否则它会 dlopen 不到 `librmw_fastrtps_cpp.so` 而启动失败；② 发布端（仿真）与抓取端（`ros2` CLI）的 `RMW_IMPLEMENTATION` 和 `ROS_DOMAIN_ID` 必须一致。另外 `ROS2PublishJointState` 的 `targetPrim` 要指向**关节树的根 link**（如 ANYmal 的 `/World/Robot/base`），指到外层 Xform 会报 "is not an articulation"——这正是机器人资产部分讲过的 articulation root 那个坑。

根据上面 `ros2 topic list / info -v / hz` 得到的话题信息，可以画出这张拓扑图：

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-ros2-graph.png" alt="Isaac Sim 发布的 ROS 2 话题拓扑" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">Isaac Sim 的 OmniGraph 节点（<code>_World_ActionGraph_*</code>）发布 <code>/joint_states</code>（sensor_msgs/JointState，RELIABLE）和 <code>/clock</code>，下游的 RViz2 / Nav2 / 你的节点订阅这些话题。整张图没有接入真机，全部是纯仿真发布。</figcaption>
</figure>

## standalone 脚本里启用（Python）

```python
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})   # 先启动应用

from isaacsim.core.utils.extensions import enable_extension
enable_extension("isaacsim.ros2.bridge")             # 再启用桥接
simulation_app.update()

# 之后用 omni.graph.core 的 og.Controller.edit 建发布图（见上一页示例），
# 或加载一个已带 Action Graph 的 USD 场景，再进主循环 world.step()。
```

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 启用桥接就会自动发数据 | 桥接本身不发数据 | 用 Action Graph 节点发布 / 订阅 |
| source 不 source 无所谓 | 不 source 会用兜底库，版本不一致 | 同一终端先 source 再启动 |
| 话题列出来了就一定收得到 | DDS / DOMAIN_ID 不一致照样收不到 | 先对齐 `RMW_IMPLEMENTATION` 和 `ROS_DOMAIN_ID` |
| 不发 `/clock` 也行 | 下游用墙钟，和仿真时间错位 | 发 `/clock` 并让下游 `use_sim_time` |
| `targetPrim` 指机器人外层 Xform | 那不是 articulation | 指向关节树根 link |
| 相机 / 雷达直接发 | 它们要先接 Render Product | 经 `Isaac Create Render Product` 再发，见观察单元的[《RTX Lidar / IMU》](../05-observation/02-lidar-imu.md)一页 |

## 小结

- ROS 2 Bridge 把 Isaac Sim 内部数据翻译成 ROS 2 topic，方便 RViz、MoveIt / Nav2 或外部节点接入纯仿真闭环。
- 启用前两件事：启用 `isaacsim.ros2.bridge` + 启动前在同一终端 source ROS 2。
- 桥接不发数据，真正收发的是 Action Graph 节点（Publish Joint State / Clock / TF、Camera / RTX Lidar Helper……）。
- 话题不通先查 DDS 与 `ROS_DOMAIN_ID`；发 `/clock` 配 `use_sim_time`；`targetPrim` 指向 articulation 根。

## 参考资料

- NVIDIA Isaac Sim Documentation, [ROS 2 Bridge / ROS 2 Tutorials](https://docs.isaacsim.omniverse.nvidia.com/latest/ros2_tutorials/index.html)
- NVIDIA Isaac Sim Documentation, [Running a Reinforcement Learning Policy through ROS 2](https://docs.isaacsim.omniverse.nvidia.com/latest/ros2_tutorials/tutorial_ros2_rl_controller.html)
- NVIDIA Isaac Sim Documentation, [ROS 2 Setting Publish Rates](https://docs.isaacsim.omniverse.nvidia.com/latest/ros2_tutorials/tutorial_ros2_publish_rate.html)

## 导航

- 返回目录：[仿真接口](../07-ecosystem.md)
- 上一页：[OmniGraph / Action Graph](01-omnigraph.md)
