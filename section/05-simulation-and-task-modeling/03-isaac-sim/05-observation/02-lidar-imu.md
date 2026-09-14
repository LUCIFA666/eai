# RTX Lidar / IMU / 接触传感器

上一页把**相机**当传感器讲透了：相机管线、状态读取、时间对齐。但 Isaac Sim 的传感器不止相机。做移动机器人、四足、人形时，你还会用到**激光雷达**、**IMU** 和**接触传感器**。这一页补齐这三类原生传感器，重点放在脚本内如何取数；如果以后需要发到外部 ROS 2 节点，再去后面的 ROS 2 Bridge 页面。

## 本节目标

本节围绕下面几个问题展开：

1. 取这几类传感器数据有哪两条路径，区别在哪？
2. RTX Lidar 的单帧为什么只是一个扇区，怎么拼成完整一圈点云？
3. IMU 和接触传感器分别读到什么、适合判断什么？

阅读这一页前，最好已经会用相机，并准备给移动 / 腿足 / 人形机器人加更多模态感知。代码用 Isaac Sim 5.1.0 的 `isaacsim.sensors.*` 接口，可在服务器上 headless 跑。

## 两条取数路径

加传感器前先建立一个分类，后面所有坑都和它有关：**RTX 传感器走渲染管线，物理传感器走 PhysX**。

一句话类比：相机和 RTX Lidar 像"摄影组"，要经过渲染才出画面 / 点云；IMU 和接触传感器像贴在机体上的"体感贴片"，直接从物理引擎读数。

<figure class="doc-figure">
<p class="doc-figure-title">原生传感器的两条取数路径</p>
<div class="figure-flow">
<div class="figure-node"><strong>RTX Lidar（走渲染）：</strong>必须先经 Isaac Create Render Product，再接 annotator 取点云</div>
<div class="figure-node"><strong>IMU / 接触（走 PhysX）：</strong>IMUSensor / ContactSensor 直接 get_current_frame()</div>
<div class="figure-node"><strong>脚本内取数：</strong>挂 annotator 或传感器对象，每帧 get_data() / get_current_frame()</div>
<div class="figure-node"><strong>可选发布：</strong>需要外部节点时，再用 Action Graph / ROS 2 Bridge 发成标准话题</div>
</div>
<p class="doc-figure-subtitle">版本命名空间：5.x 用 isaacsim.sensors.physics（IMU/接触）/ isaacsim.sensors.rtx（RTX Lidar），4.5 之前是 omni.isaac.sensor.*。</p>
</figure>

## RTX Lidar

Isaac Sim 的激光雷达是 **RTX Lidar**——用 RTX 光线追踪模拟激光束，比纯几何射线更接近硬件雷达的成像方式（支持强度、多回波、按 JSON 配置不同型号）。几个关键点：

- **两种形态**：旋转式（Rotating，机械旋转 360°）和固态（Solid State，固定视场）。
- **JSON 配置**：线数、水平 / 垂直 FOV、角分辨率、量程、扫描频率等由一个 config 描述（内置 `Example_Rotary`、各家型号模板，也可自定义）。
- **必须挂到自己的 render product**：RTX 传感器和相机一样走渲染管线，必须经 `Isaac Create Render Product` 把输出接出来；多个 RTX 传感器各占资源。

创建（GUI）：`Create > Isaac > Sensors > RTX Lidar`，选一个 config，挂到机器人某个 link 下。下面这张图来自一个最小脚本：在一圈障碍物中央立一台旋转式 RTX Lidar，取一整圈扫描。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-lidar.png" alt="RTX Lidar 点云：左为场景 RGB，右为俯视点云" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">左：相机看到的障碍物场景；右：同一场景的激光扫描（俯视，按高度 / 距离着色），红色三角是雷达位置。每个箱体都在扫描里留下清晰边廓——这正是建图、避障、定位要用的几何信息。</figcaption>
</figure>

取数据有两条路。**① 脚本内直接取**（不发 ROS）——上面那张图就是这么来的：用 `LidarRtx` 包一台旋转雷达，在它的 render product 上挂点云 annotator，逐帧取 `(N, 3)` 点云、拼成一整圈：

```python
import numpy as np
import omni.replicator.core as rep
from isaacsim.sensors.rtx import LidarRtx

lidar = LidarRtx(prim_path="/World/lidar", name="lidar",
                 translation=np.array([0.0, 0.0, 0.55]),
                 config_file_name="Example_Rotary")     # 3D 多线配置
world.reset()
lidar.initialize()

rp = lidar.get_render_product_path()
pc = rep.AnnotatorRegistry.get_annotator(
    "IsaacExtractRTXSensorPointCloudNoAccumulator")     # 5.x 逐帧取点云
pc.attach([rp])

# NoAccumulator 是逐帧取数：旋转雷达的单帧只是光束扫过的一个扇区。
# 把绕一圈内的多帧点云拼接起来，才是真正的一整圈。
frames = []
for _ in range(120):
    world.step(render=True)
    pts = pc.get_data()["data"]      # 单帧 (N, 3) xyz（传感器系，一个扇区）
    if pts is not None and len(pts):
        frames.append(np.asarray(pts).reshape(-1, 3))
cloud = np.concatenate(frames, axis=0)   # 累积一整圈（可再按 cm 取整去重）
```

**② 可选发到 ROS 2**：如果要接 RViz 或外部 ROS 2 节点，Action Graph 里 `Isaac Create Render Product → ROS2 RTX Lidar Helper`，一个 helper 选 `laser_scan` 发 `/scan`（`sensor_msgs/LaserScan`），再来一个选 `point_cloud` 发 `/point_cloud`（`PointCloud2`）。本页只要求你理解脚本内取数；发布话题放到 [ROS 2 Bridge](../07-ecosystem/02-ros2-bridge.md)。

**版本提示**：5.x 推荐 `IsaacExtractRTXSensorPointCloudNoAccumulator` 逐帧取点云；`Example_Rotary` 是 3D 多线雷达，2D 单线的 `IsaacComputeRTXLidarFlatScan` 对它会拒绝执行。旧版 4.x 常用 `IsaacCreateRTXLidarScanBuffer` 累积整圈缓冲。

### 取到一圈点云

按上面的方式运行（`LidarRtx` + `IsaacExtractRTXSensorPointCloudNoAccumulator`，中央一台旋转雷达、四周摆障碍物，把绕一圈内的多帧逐帧点云拼接去重），会得到类似下面的点云摘要：

```text
LidarRtx 创建成功 /World/lidar；config=Example_Rotary
点云 shape: (82604, 3)  dtype: float32   # 累积一整圈、多帧拼接去重后
点数: 82604
前 3 点 (x,y,z, 传感器系): [[1.799, 0.094, -0.483], [1.8, 0.094, -0.456], [1.8, 0.094, -0.429]]
xyz 范围: x[-10.80, 10.80]  y[-10.80, 10.80]  z[-0.55, 0.32]
象限覆盖[-180~-90, -90~0, 0~90, 90~180]: [20649, 21000, 20358, 20597]   # 四象限点数相当 = 真·一整圈
```

累积**一整圈**后是 **82604 个 (x, y, z) 点**，x、y 都正负铺开、四个象限点数相当（各约 2 万）——绕中心一圈、四周障碍物都留下边廓，这正是建图、避障、定位要吃的几何数据。有两个关键点要拎清：

- **`IsaacExtractRTXSensorPointCloudNoAccumulator` 是逐帧取数**，旋转雷达的**单帧只是光束扫过的一个扇区**：如果像很多老脚本那样每帧覆盖、只留最后一帧，会得到类似 `x[-5.86, 5.90] y[-10.79, -1.72]` 这种 y 全压在一侧的**扇形**，而不是一整圈。要这一整圈，就得把绕一圈内的多帧点云**拼接去重**（上面那张点云图也是这么累积出来的）。
- 点云在**传感器坐标系**下（地面点 z 固定在 -0.55，是雷达相对地面的安装高度）；另外，本机这套 5.1 环境实测直接用 `IsaacCreateRTXLidarScanBuffer` 取到的是空数组——它在 5.x 仍是合法 annotator（`NoAccumulator` 底层就是它），但迁移老脚本时点云为空的情况并不少见，取不到数时优先换用上面的 `NoAccumulator` 路径。

## IMU 传感器

IMU 给出机体坐标系下的**线加速度、角速度、朝向**，是腿足 / 人形运动策略常用的本体感知。

```python
from isaacsim.sensors.physics import IMUSensor

imu = IMUSensor(prim_path="/World/robot/pelvis/Imu_Sensor", name="imu")
imu.initialize()
frame = imu.get_current_frame()
lin_acc = frame["lin_acc"]      # 线加速度
ang_vel = frame["ang_vel"]      # 角速度
orient  = frame["orientation"]  # 朝向（注意四元数顺序）
```

GUI 创建：`Create > Isaac > Sensors > Imu Sensor`，挂到躯干 / 基座 link（如人形的 `pelvis`）。发到 ROS 2：`Isaac Read IMU Node → ROS2 Publish IMU`（发 `sensor_msgs/Imu` 到 `/imu`）。

### 自由落体里的 IMU 读数

把一个 IMU 挂在自由下落的方块上，逐步打印线加速度和角速度：

```text
step | lin_acc(m/s^2)        | ang_vel(rad/s)
   0  | [0.0,  0.0,  0.0]     | [0.0,  0.0,  0.0]
  24  | [0.0,  0.0,  0.0]     | [-0.16, -0.10, 0.0]
  48  | [6.63, 15.19, 17.38]  | [2.24,  0.17, 0.25]    # 触地瞬间冲击
  59  | [0.05, 4.75,  6.75]   | [-2.62, 0.0, -0.02]
```

这部分数有个反直觉但物理正确的现象：**自由下落阶段 `lin_acc` 接近 0**，而不是 9.8。因为 IMU 测的是**比力（specific force）**，不是世界系下的加速度——自由落体处于失重状态，比力就是 0；直到 step 48 触地，才出现明显冲击峰值 `[6.6, 15.2, 17.4]`。腿足 / 人形策略观测里常带 IMU，理解“它测的是比力、在机体系下”能避免把观测定义写错。

## 接触传感器

接触传感器报告刚体之间的接触力，用于抓取判断、足底着地 / 腾空、跌倒检测。它建在 PhysX 接触报告之上：

```python
from isaacsim.sensors.physics import ContactSensor

contact = ContactSensor(
    prim_path="/World/robot/left_foot/contact",
    min_threshold=0.0,
    max_threshold=1e7,
)
contact.initialize()
value = contact.get_current_frame()   # 含接触力等
```

**延伸**：在 Isaac Lab 里，接触和 IMU 被进一步封装成 `ContactSensorCfg` / `ImuCfg`，还能批量跟踪腾空时间（`current_air_time`）。这里讲的是 Isaac Sim 这一层的原生传感器，理解它有助于看懂上层框架在做什么。

## 传感器一览

| 传感器 | 形态 | 主要输出 | 典型用途 | 取数路径 |
|---|---|---|---|---|
| 相机 | RGB-D | RGB / 深度 / 分割 / 法线 | 视觉策略、数据采集 | 渲染 |
| RTX Lidar | 旋转 / 固态 | LaserScan / PointCloud | 移动机器人、AMR、建图导航 | 渲染 |
| IMU | — | 线加速度 / 角速度 / 朝向 | 腿足 · 人形本体感知 | PhysX |
| 接触传感器 | — | 接触力 / 接触状态 | 抓取、步态、跌倒检测 | PhysX |

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| RTX Lidar 像相机一样直接出数据 | 它走渲染，要先接 render product | `Isaac Create Render Product` 后再取 / 发 |
| 没按 Play 也能取雷达数据 | RTX 传感器要仿真运行才出数据 | 先 Play / `world.step()` 再取 |
| 雷达 annotator 名字随便用 | 3D 多线雷达用 FlatScan 会拒绝执行 | 5.x 用 `...PointCloudNoAccumulator` |
| IMU 读出来就是世界系 | IMU 读的是机体系 | 和训练观测约定（机体系 / 四元数顺序）对齐 |
| 传感器命名空间照抄旧教程 | 4.5 之前是 `omni.isaac.sensor.*` | 5.x 用 `isaacsim.sensors.physics/.rtx` |
| 多挂几个 RTX 传感器无所谓 | 各占渲染资源，显存吃紧 | 按需降分辨率 / 降频 |

## 小结

- 传感器分两条取数路径：RTX（相机 / Lidar）走渲染，IMU / 接触走 PhysX——这决定了它们怎么取数、怎么发布。
- RTX Lidar 基于光追、按 JSON 配型号，必须先接 Render Product；脚本内挂 annotator 逐帧取点云，需要外部接口时再经 RTX Lidar Helper 发 `/scan`、`/point_cloud`。
- IMU 给机体系线加速度 / 角速度 / 朝向，接触传感器给接触力；二者 `initialize()` 后 `get_current_frame()` 直接读。
- 版本命名空间是高频坑：5.x 用 `isaacsim.sensors.*`；IMU 机体系约定要和策略观测对齐。

## 参考资料

- NVIDIA Isaac Sim Documentation, [RTX Lidar Sensors](https://docs.isaacsim.omniverse.nvidia.com/latest/ros2_tutorials/tutorial_ros2_rtx_lidar.html)
- NVIDIA Isaac Sim Documentation, [Sensors](https://docs.isaacsim.omniverse.nvidia.com/latest/sensors/index.html)
- NVIDIA Isaac Sim Documentation, [IMU / Physics Sensors](https://docs.isaacsim.omniverse.nvidia.com/latest/sensors/isaacsim_sensors_physics.html)

## 导航

- 返回目录：[观测与传感器](../05-observation.md)
- 上一页：[相机与传感器观测](01-cameras-and-sensors.md)
- 下一页：[Observation → Action 闭环](03-observation-loop.md)
