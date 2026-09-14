# 相机与传感器观测

机器人能动了，接下来要拿到它"看见"的东西——RGB、深度、分割，以及自己的关节状态。这一页讲 Isaac Sim 里的相机怎么用：它不是"截图按钮"，而是一条由渲染驱动的数据管线，理解了这一点，那些"图怎么是黑的""图和动作对不上"的坑就都能解释。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么说相机是「传感器」，而不是「截图按钮」？
2. 一台相机能取出哪些通道（RGB、深度、分割），分别怎么用？
3. 渲染出来的图为什么会是黑的，又为什么常常需要多视角？

阅读这一页前，最好已经会让机器人按目标运动。现在我们把注意力转到另一半：把相机、传感器和状态读出来，喂给策略或存成数据集。

## 相机是传感器，不是截图按钮

在 MuJoCo 里你可能习惯"渲染一帧拿张图"。Isaac Sim 不一样：相机是 stage 里的一个 `Camera` prim，由 RTX 渲染器和传感器封装连接起来。你**配置**的是相机参数，**等待**的是渲染器产出，**读取**的是传感器最近一次完成渲染的帧缓存。

<figure class="doc-figure figure-camera" aria-label="Isaac Sim 相机出图流程">
  <p class="doc-figure-title">Isaac Sim 相机出图流程</p>
  <p class="doc-figure-subtitle">相机不是截图按钮，而是一条由渲染驱动的数据管线。</p>
  <div class="figure-flow">
    <div class="figure-node">
      <strong>相机配置</strong>
      <span><code>prim_path</code>、位置 / 朝向、resolution、focal_length、clipping_range。</span>
    </div>
    <div class="figure-node">
      <strong>Camera prim</strong>
      <span>stage 里的传感器节点，可固定在世界，也可挂在手腕。</span>
    </div>
    <div class="figure-node">
      <strong>Render product</strong>
      <span>RGB、depth、segmentation、bbox 等输出绑定到渲染器。</span>
    </div>
    <div class="figure-node">
      <strong>Frame buffer</strong>
      <span>保存最近一次完成渲染的数据；读太早会拿到空帧或旧帧。</span>
    </div>
    <div class="figure-node">
      <strong>读取观测</strong>
      <span><code>get_rgb()</code>、<code>get_depth()</code>、<code>get_current_frame()</code>。</span>
    </div>
    <div class="figure-node">
      <strong>写入 episode</strong>
      <span>和 step_index、state、action、phase 一起对齐保存。</span>
    </div>
  </div>
  <p class="doc-figure-subtitle">核心经验：创建相机后要等渲染完成；读到的是上一帧完成的传感器缓存；保存时必须和动作、状态、阶段对齐。</p>
</figure>

## 最小示例

下面把"创建 → reset → initialize → 预热 → 读帧"串成一段可运行代码：

```python
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": False})

import numpy as np
import isaacsim.core.utils.numpy.rotations as rot_utils
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.sensors.camera import Camera

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()
world.scene.add(
    DynamicCuboid(
        prim_path="/World/cube", name="cube",
        position=np.array([0.0, 0.0, 0.5]),
        scale=np.array([0.2, 0.2, 0.2]),
        color=np.array([1.0, 0.0, 0.0]),
    )
)

camera = Camera(
    prim_path="/World/camera",
    position=np.array([1.2, 0.0, 0.6]),
    frequency=30,
    resolution=(256, 256),
    orientation=rot_utils.euler_angles_to_quats(np.array([0, 25, 180]), degrees=True),
)
# +X 为相机前向，此处 yaw 180° 使其朝向原点方向，pitch 25° 让视线向下俯视方块

world.reset()
camera.initialize()           # reset 之后才 initialize
camera.add_distance_to_image_plane_to_frame()

for _ in range(8):            # 预热：让渲染器先产出几帧
    world.step(render=True)

rgb = camera.get_rgb()
depth = camera.get_depth()
print("rgb shape:", rgb.shape, "depth shape:", depth.shape)

simulation_app.close()
```

要点：`get_rgb()` / `get_depth()` 读的是**上一轮渲染完成**的缓存，所以 reset 或移动相机后，必须先 `world.step(render=True)` 预热若干帧，再读图。

## 一台相机，多种通道

同一台相机、同一帧渲染，可以同时产出多种像素级输出。下面是同一台 Franka 在 5.1 上 headless 渲染的 RGB、深度、分割三件套——**完全相同的相机视角**，区别只在"读哪个通道"：

<figure class="doc-figure">
  <p class="doc-figure-title">同一相机视角的三种通道</p>
  <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0.5em 0">
    <div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-franka-rgb.png" alt="RGB" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">RGB（<code>get_rgb</code>）</div></div>
    <div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-franka-depth.png" alt="深度" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">深度（近黄远紫）</div></div>
    <div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-franka-seg.png" alt="语义分割" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">语义分割（机器人一色）</div></div>
  </div>
  <figcaption class="doc-figure-subtitle">RGB 让模型"看见"世界；深度（<code>distance_to_image_plane</code>，这里按 viridis 上色，近黄远紫）给出每个像素沿相机前向轴到成像平面的距离（z-depth）——要"到相机光心的欧氏距离"用的是另一个 annotator <code>distance_to_camera</code>，反投影点云时两者不能混用；语义分割把机器人作为一个类别从背景分出来。深度和分割属于额外的 annotator，需要先添加对应输出、并确保物体打了语义标签，否则会是空的。</figcaption>
</figure>

它们各自回答不同的问题：RGB 回答"看起来是什么"，深度回答"离多远、谁在前谁在后"，分割回答"哪些像素属于哪个物体"。做抓取时，RGB 用来识别，深度帮判断高度和接触距离，分割让评测可以客观判断"夹爪是否真的对准了目标"。

## 为什么图会是黑的

"场景里明明有东西，存出来却是黑图"是最常见的新手问题，原因几乎都在"读太早"或"没绑对"：

- camera prim 路径写错，绑到了不存在的相机。
- 相机创建了，但没 `initialize()`。
- 加了 depth / segmentation annotator，但还没推进渲染。
- reset 后立刻读第一帧，RTX 管线、材质还没准备好。
- 刚移动相机 / 物体就读图，新姿态还没被渲染出来。
- clipping range 不合适：near 太大裁掉近处夹爪，far 太小远处物体消失、深度异常。

稳妥做法：reset 后先丢掉前几帧，只从渲染稳定后的帧开始记录；尤其采集数据集时，别把第一张黑图、半加载图混进训练数据。这个等待不是浪费时间，而是在保证"读到的图真的对应当前仿真状态"。

## 为什么需要多视角

单视角很容易误判：正面看像夹住了，侧面可能夹在杯沿上；俯视能看 XY 对齐，却看不清高度。所以数据采集里常用多台相机覆盖彼此的盲区：

<figure class="doc-figure">
  <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:0.5em 0">
    <div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-lab-camera-global.jpg" alt="全局相机视角" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">全局相机：看任务布局与整体位姿</div></div>
    <div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-lab-camera-topdown.jpg" alt="俯视相机视角" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">俯视相机：看 XY 对齐与目标选择</div></div>
  </div>
  <figcaption class="doc-figure-subtitle">同一时刻同一场景，两台相机回答不同的问题。画面里的 <code>Camera 1 (rgb)</code> 视口标识说明这是任务里某台相机的实时观测，不是事后截图。常见组合还包括看高度的侧视相机和看末端接触细节的腕部相机。</figcaption>
</figure>

相机摆位的原则不是"画面好不好看"，而是**能不能看到成功判定和失败发生所需要的证据**：抓杯子至少要有一个视角看到杯沿、夹爪指尖和抬升高度。几个最常用参数：

```text
prim_path:       相机在 stage 里的路径
resolution:      输出大小，入门常用 256x256 快速迭代
focal_length:    焦距，越大视角越窄、越像"拉近"
clipping_range:  near/far 裁剪，near 太大裁掉近处、far 太小裁掉远处
orientation:     朝向四元数（wxyz/xyzw 顺序、坐标轴约定易错，改完务必渲染一帧核对）
```

腕部相机的 `prim_path` 往往依赖机器人 USD 里已有的相机 prim；换机器人时这个路径可能不存在，要改成新机器人对应的手部相机路径。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 创建相机就能立刻读到图 | 要 reset → initialize → 预热渲染后才有帧 | 读图前先 `step(render=True)` 若干次 |
| `get_rgb()` 拍的是当前这一行 | 读的是上一轮渲染完成的缓存 | 移动相机 / 物体后先 step 再读 |
| 黑图 = 相机坏了 | 多为路径错、没 initialize、没预热、clipping 不当 | 按黑图清单逐项查 |
| 一个漂亮视角就够了 | 单视角易误判接触和高度 | 多视角覆盖盲区，按"证据"摆位 |
| 深度 / 分割自动就有 | 是额外 annotator，分割还需语义标签 | 显式添加输出、给物体打 class 标签 |

## 小结

- 相机是 stage 里的传感器 prim，由 RTX 渲染驱动；你配置参数、等待渲染、读取帧缓存。
- 流程：创建 → `reset` → `initialize` → 预热若干 `step(render=True)` → 读 `get_rgb()` / `get_depth()`。
- 同一相机可出 RGB / 深度 / 分割多通道，分别回答"看起来是什么 / 离多远 / 哪些像素属于谁"。
- 黑图几乎都因读太早或没绑对；单视角易误判，按"成功 / 失败证据"设计多视角摆位。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)
- Isaac Lab Documentation, [Sensors](https://isaac-sim.github.io/IsaacLab/main/source/overview/core-concepts/sensors/index.html)

## 导航

- 返回目录：[观测与传感器](../05-observation.md)
- 上一页：[控制](../04-control.md)
- 下一页：[RTX Lidar / IMU / 接触传感器](02-lidar-imu.md)
