# Genesis 1.x 传感器接口

本页用于说明 Genesis 1.x 文档和示例中更强调的 sensor-based camera 接口，并和配套脚本中已验证的直接 camera 调用做版本边界说明。

## 本节目标

本节围绕下面几个问题展开：

1. Genesis 1.x 文档和示例中的 camera sensor 基本写法是什么？
2. 它和 `scene.add_camera()` / `cam.render()` 这类直接 camera 写法有什么差异？
3. 如何避免把某个版本的 API 写成永久正确？
4. 读者遇到 API 差异时应该怎样回到官方文档核对？

## 先分清 camera 和 sensor 的两种写法

在 Genesis 入门材料里，常见两类相机写法。一类是配套脚本里使用的直接 camera。下面片段默认已经创建好 `scene`，完整可运行上下文见 `labs/06_genesis/04_observation_and_rendering.py`：

```python
cam = scene.add_camera(
    res=(640, 480),
    pos=(3.5, 0.0, 2.5),
    lookat=(0.0, 0.0, 0.5),
    fov=30,
)
scene.build()
scene.step()
result = cam.render(rgb=True)
rgb = result[0] if isinstance(result, tuple) else result
```

另一类是更接近官方新接口风格的 sensor 写法：把 camera 当成场景里的 sensor，构建后通过 `read()` 取数据。官方 Camera Sensors 文档的最小入口是 `gs.sensors.RasterizerCameraOptions`：

```python
import genesis as gs

gs.init(backend=gs.gpu)
scene = gs.Scene()
scene.add_entity(gs.morphs.Plane())
camera = scene.add_sensor(gs.sensors.RasterizerCameraOptions(
    res=(512, 512),
    pos=(3.0, 0.0, 2.0),
    lookat=(0.0, 0.0, 0.5),
    fov=60.0,
))

scene.build(n_envs=1)
scene.step()
data = camera.read()
print(data.rgb.shape)
```

Nyx 示例也沿用了 `scene.add_sensor(...)` 这条思路，只是传入的是插件提供的 `NyxCameraOptions`，并且需要额外依赖和版本约束。下面只展示 Nyx option 类型差异，不是完整可运行脚本：

```python
from gs_nyx_plugin.nyx_camera_options import NyxCameraOptions

camera = scene.add_sensor(NyxCameraOptions(
    res=(1920, 1080),
    pos=(-1.0, 1.0, 1.2),
    lookat=(0.0, 0.0, 0.1),
    fov=20.0,
))
```

这三段代码都在“看世界”，但抽象层级不同：直接 camera 更像方便的离屏相机；core sensor 是 Genesis 传感器系统的一部分；Nyx 则是挂在 sensor 接口上的渲染插件。引用 API 时不能把它们混写成同一种接口。

## 传感器不是只有 RGB

官方 `Simulation Interface` showcase 里，传感器类素材很丰富。实际运行时遇到过这些类型：

| 传感器 / 接口 | 示例 ID | 关注点 |
|---|---|---|
| Depth camera | `sim_04_depth_camera` | RGB 之外还要检查 depth 形状和数值范围 |
| IMU | `sim_05_imu` | 输出不是图像，而是惯性测量数据 |
| LiDAR | `sim_06_lidar` | 点云和距离来自 `sensor.read()`，预览图滤掉地面后勾出障碍物边界 |
| Tactile | `sim_07_tactile_sandbox` | 接触类传感器依赖物理接触和材料配置 |
| ContactForce | `sim_08_contact_force` | 力传感器更适合保存时间序列，不只是截图 |
| SurfaceDistance | `sim_09_surface_distance` | 输出常和几何距离、表面关系有关 |
| Temperature | `sim_10_temperature_grid` | 网格型状态需要看数组结构和物理含义 |

这也是为什么配套脚本坚持保存 `summary.json`：传感器输出不一定能被一张图片完整表达。LiDAR 的点、接触力曲线和温度网格都应该回到原始数据结构里检查。

<figure class="doc-figure">
<p class="doc-figure-title">传感器：深度相机</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_04_depth_camera.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_04_depth_camera.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/sensors/depth_camera_custom_vverts.py</code>。左：场景 RGB；右：机器人深度相机的深度图（turbo 配色，近＝蓝、远＝红，物体呈暗色近景）。深度的核心证据是 depth 数组本身，这里把它可视化出来与场景对照。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">传感器：IMU</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_05_imu.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_05_imu.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/sensors/imu_franka.py</code>。左：Franka 末端画圆；右：IMU 实时读数曲线（上＝线加速度 xyz，下＝角速度 xyz）。IMU 的核心证据正是这些惯性读数，而不是画面本身。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">传感器：触觉沙盒</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_07_tactile_sandbox.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_07_tactile_sandbox.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/sensors/tactile_sandbox.py</code>。左：球压向 taxel 触觉垫；右：ContactDepthProbe 的 20×20 接触深度热力图（中心接触最深＝红）。触觉的核心证据是这张接触场，而不是场景截图。</p>
</figure>

`sim_06_lidar` 的运行摘要能说明这一点。预览图已经把整圈扫描收敛成障碍物边界：滤掉地面回波后，只保留每个方向上最近的障碍物表面，对应的结构化证据都在 `metrics` 里：

```json
{
  "id": "sim_06_lidar",
  "adapter": "lidar_obstacle_boundary",
  "resolution": [1060, 580],
  "captured_frames": 150,
  "metrics": {
    "total_rays": 8192,
    "hit_points": 1798,
    "projected_hit_points": 1360,
    "ground_filtered": true,
    "boundary_azimuth_bins": 266
  },
  "result": "passed"
}
```

这里的字段比截图更关键：`total_rays` 是发出的射线总数；滤掉地面后 `hit_points` 是命中障碍物的点数，`projected_hit_points` 是其中落进左侧画面的数量，`boundary_azimuth_bins` 统计有多少个方位角方向探到了障碍物边界。训练时策略网络不该吃这张可视化图，而应该回到传感器返回的结构化点云与距离。

<figure class="doc-figure">
<p class="doc-figure-title">传感器：LiDAR（障碍物边界）</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_06_lidar.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_06_lidar.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/sensors/lidar_teleop.py</code>。左：滤除地面回波后，LiDAR 点只贴在障碍物朝向传感器的表面，勾出它们的边界；右：把每个方位角上最近的回波画成俯视边界图（按距离上色，内圈圆柱近＝绿、外圈方块远＝橙，中心三角＝传感器），并有一根圆柱绕传感器缓慢移动、边界随之更新。点云与距离来自 <code>sensor.read()</code>。</p>
</figure>

`sim_08_contact_force` 也是同一个原则。它的 composite 预览左侧保留场景渲染，右侧把真实接触力历史画成曲线。摘要里最值得引用的是：

```json
{
  "id": "sim_08_contact_force",
  "adapter": "contact_force_composite",
  "captured_frames": 150,
  "metrics": {
    "max_force_norm": 279.5279846191406,
    "history_samples": 375,
    "zerocopy_required": false
  },
  "result": "passed"
}
```

这段摘要说明三件事：第一，预览图用了 adapter；第二，曲线不是人为装饰，而是来自 `375` 个传感器历史样本；第三，最大力范数约 `279.53`，可以作为检查接触是否真的发生的数值证据。对力传感器来说，曲线和数值比某一帧 RGB 更接近“观测本体”。

<figure class="doc-figure">
<p class="doc-figure-title">传感器：接触力（左渲染 + 右真实力曲线）</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_08_contact_force.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_08_contact_force.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/sensors/contact_force_go2.py</code>。这是合成画面：左侧场景渲染，右侧绘制真实 ContactForceSensor 历史（375 个样本，最大力范数约 279.53），不能把曲线当相机输出。</p>
</figure>

`sim_09_surface_distance` 和 `sim_10_temperature_grid` 只捕获了 `4` 帧，但摘要里都是 `result: passed`，并且 `stopped_after_max_frames: false`。这类示例展示的是传感器能力入口和配置结果，不适合用“视频够不够长”来判断成败。引用它们时，应该写成“短帧数的能力快照”，而不是“动态过程复现”。

<figure class="doc-figure">
<p class="doc-figure-title">传感器：表面距离（短帧能力快照）</p>
<img src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_09_surface_distance.png" alt="surface distance ShadowHand">
<p class="doc-figure-subtitle">官方 <code>examples/sensors/surface_distance_shadowhand.py</code>（仅 4 帧，用静图）。这是能力入口的快照，应回到几何距离数据判读，不按长视频标准判成败。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">传感器：温度网格（短帧能力快照）</p>
<img src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_10_temperature_grid.png" alt="temperature grid">
<p class="doc-figure-subtitle">官方 <code>examples/sensors/temperature_grid.py</code>（仅 4 帧，用静图）。网格型状态要回到数组结构与物理含义。</p>
</figure>

## Nyx 是 sensor 体系里的渲染插件

Nyx 的官方示例展示了 sensor 接口的另一种扩展方向：相机不仅能读 RGB，还能换成更强的渲染后端，支持 PBR 材质、HDRI、灯光类型、Gaussian splat、object picking、多相机多环境等。

运行记录中的依赖边界是：

```text
genesis-world==1.1.0
gs-nyx==0.1.2
gs-nyx-plugin==0.1.3
av==17.1.0
NVIDIA Driver 580.126.09
```

这里有两个使用要点：

1. `NyxCameraOptions` 来自 Nyx 插件，不是最小 Genesis 脚本必备知识，应该放在渲染扩展中讲；
2. 官方示例能跑不等于无需记录依赖，尤其是插件、驱动和视频编码依赖。

`render_03_nyx_attached_camera` 就是一个很好的案例：它最终可以生成完整视频，但成功素材要和依赖、视频编码、path planner 失败日志以及作用范围很小的 adapter 一起读。这里先记住 Nyx 的版本和依赖边界；具体错误日志放到下一页的渲染验收中细读。

## 版本边界

Genesis 版本变化比较快，所以涉及 API 时遵守三个规则：

| 规则 | 写法 |
|---|---|
| 已验证的配套脚本 | 写明脚本路径、运行环境和摘要文件 |
| 官方新接口 | 写明“按官方文档当前写法”，不要当成永久 API |
| 需要 adapter 的示例 | 同时保留原始失败日志和 adapter 原因 |

读者遇到 API 差异时，先不要急着改一堆代码。建议按顺序查：

1. 当前 `genesis-world` 版本；
2. 示例来自 Genesis 主仓库还是 `genesis-nyx`；
3. 是否需要可选依赖，例如 `gs-nyx-plugin`、`av`、`pyuipc`；
4. 失败发生在物理、渲染、传感器读取、视频编码，还是 viewer GUI。

## 读完应能回答

1. `scene.add_camera()` 和 `scene.add_sensor(...)` 的抽象层级有什么不同？
2. `sim_08_contact_force` 的曲线为什么比某一帧 RGB 更接近观测本体？
3. 如果 Nyx 示例失败，为什么要先区分依赖、视频编码、path planner 和 viewer GUI？

## 小结

- Genesis 里相机既可以作为直接 camera 使用，也可以作为 sensor 系统的一部分。
- 传感器输出不一定是图像，很多时候更应该检查数组、时间序列和结构化数据。
- Nyx 展示的是 sensor + renderer plugin 的扩展路径，不是最小入门依赖。
- 写 API 时要明确版本和运行证据，不能把某次成功截图写成永久保证。

## 参考资料

- Genesis World Documentation, Visualization & Rendering. https://genesis-world.readthedocs.io/en/v1.0.0/user_guide/getting_started/visualization.html
- Genesis World Documentation, Camera Sensors. https://genesis-world.readthedocs.io/en/v1.0.0/user_guide/getting_started/sensors/camera_sensors.html
- Genesis World Documentation, Nyx Renderer. https://genesis-world.readthedocs.io/en/v1.0.0/user_guide/getting_started/nyx_renderer.html

## 导航

- 上一页：[camera 与图像保存](02-camera-and-image-save.md)
- 返回目录：[观察、渲染与传感器](../03-observation-rendering-sensors.md)
- 下一页：[渲染常见问题](04-rendering-check.md)
