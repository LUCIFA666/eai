# viewer 与无界面运行

前面几页已经让机器人能动起来。现在要回答另一个基础问题：**如何观察这个仿真世界？**

在 Genesis 里，观察大致有两条路径：一条是给人看的 viewer，用来交互式检查场景；另一条是给程序用的 camera，用来保存图像、深度或分割等观测。初学时不要把这两条混在一起。viewer 打不开，不一定说明仿真不能跑；camera 能出图，也不等于传感器配置已经适合训练。

## 本节目标

本节围绕下面几个问题展开：

1. viewer 和 camera 分别解决什么问题？
2. 为什么远程和桌面环境上的可视化排错方式不同？
3. 为什么要先用 `show_viewer=False` 验证物理循环？
4. 通过无界面运行后，怎样再进入 camera 验收？

## viewer 是给人调试用的

viewer 的作用是显示场景：机器人在哪里，地面有没有穿模，关节运动是否合理，物体有没有飞走。它很适合第一次调试，但它不是仿真本身。

本页的 `scene = ...` 片段都是局部配置示例，默认已经完成 `import genesis as gs`。完整的离屏相机脚本见 `labs/06_genesis/04_observation_and_rendering.py`。

一个典型入口是：

```python
scene = gs.Scene(show_viewer=True)
```

如果有桌面图形环境，viewer 能快速检查：

- 机器人是否成功加载；
- 初始姿态是否合理；
- 控制目标是否让机器人朝预期方向运动；
- 物体是否掉落、穿透或抖动；
- 相机大概应该放在哪里。

但 viewer 有一个现实问题：它依赖图形环境。服务器、SSH、Docker、远程无显示器环境里，viewer 可能先于仿真本身出问题。所以排错时要记住一句话：**viewer 是调试工具，不是仿真核心路径**。

## 运行中暴露的观察边界

官方 showcase 运行很适合用来说明：同样是“看到了画面”，来源可能完全不同。

| 素材 | 运行状态 | 观察边界 |
|---|---|---|
| `render_00_follow_entity`、`render_01_moving_camera` | Genesis core rendering `2/2` 通过 | 这是普通 camera / rendering 路径，适合说明程序化相机 |
| `sim_11_draw_debug` | `75` 帧 usable，但用了 overlay adapter | viewer debug primitive 不会自动进入 offscreen camera，需要投影或后处理 |
| `sim_01_imgui_joint_control` | `75` 帧 usable，但用了静态 proxy | ImGui 面板依赖交互 viewer，无界面环境只能保留说明性代理图 |
| `sim_12_mesh_point_picker`、`sim_13_mouse_interaction` | `75` 帧 usable，但标注 GUI 依赖 | 鼠标点选和拖拽不是普通 headless camera 能完整复现的交互 |
| `render_03_nyx_attached_camera` | Nyx 通过，但保留 no-adapter failure log | 插件渲染成功不等于原始脚本无条件通过，失败日志也要保留 |

这张表要训练一个判断：**先问画面从哪里来，再问它能不能作为观测数据。** viewer 截图、offscreen camera、sensor 读数、overlay adapter、GUI proxy、Nyx renderer 都可以生成图，但它们在实验报告里的证据等级不一样。

<figure class="doc-figure">
<p class="doc-figure-title">overlay 叠加：调试图元（draw debug）</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_11_draw_debug.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_11_draw_debug.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/tutorials/draw_debug.py</code>。box / line / arrow / sphere / frame 等调试图元属于 viewer，不会自动进入离屏相机，这段画面是把图元投影到相机帧的叠加结果。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">GUI proxy：ImGui 关节控制</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_01_imgui_joint_control.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/sim_01_imgui_joint_control.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/gui/imgui_joint_control.py</code>。ImGui 面板依赖交互式 viewer，无界面服务器上只能保留说明性的静态代理图。对照上一段：同样"看到画面"，来源和证据等级并不相同。</p>
</figure>

## 无界面运行先验证物理循环

如果 viewer 打不开，第一步不是反复改显卡驱动，而是先关掉 viewer：

```python
scene = gs.Scene(show_viewer=False)
```

然后确认物理循环能跑：

```python
scene.build()

for _ in range(1000):
    scene.step()
```

这一步的目的很清楚：把“仿真能不能跑”和“窗口能不能开”分开。只要无界面物理循环能跑，说明 `Scene / Entity / build / step` 主链路是通的。接下来再单独处理相机渲染或 viewer。

这个分离尤其重要。个人电脑、实验室服务器、远程桌面和容器环境的图形能力差异很大。如果验收只写“看到窗口”，会把很多图形环境问题误判成 Genesis 主链路失败。

## 无界面通过后再进入 camera

viewer 页只负责把“窗口能不能开”和“仿真能不能跑”分开。只要 `show_viewer=False` 的物理循环通过，下一步才是 camera：让程序保存 RGB、depth、segmentation 或其他传感器输出。

camera 的细节放在下一页集中讲，包括 `res`、`pos`、`lookat`、`fov`、`camera_config.json` 和图像有效性检查。这里先记住一个顺序：

```text
先证明 scene.build / scene.step 能无界面运行
  -> 再添加 camera
  -> 再保存 RGB 和 camera_config
  -> 最后再扩展 depth / segmentation / sensor
```

这个顺序能避免把图形环境、渲染参数、相机视角和物理循环混在一起排错。

## 第一次观察与渲染的验收标准

| 练习 | 验收标准 |
|---|---|
| 无界面物理循环 | `show_viewer=False` 时能 step 1000 次 |
| viewer 调试 | 本地环境能看到机器人、地面和基本运动 |
| camera RGB | 能保存一张 RGB 图，机器人在画面中可见 |
| 相机配置记录 | 保存位置、朝向、分辨率、fov 和后端信息 |
| 可选 depth | depth 输出形状与 RGB 分辨率一致，数值没有全是 0 或 NaN |

这套验收的重点不是画面效果，而是链路可控：物理、viewer、camera、文件保存能分开验证。

## 读完应能回答

1. `sim_11_draw_debug` 的画面为什么不能直接当作普通 camera RGB？
2. `sim_01_imgui_joint_control` 在无界面环境里用了 proxy，这说明 viewer 和仿真核心路径是什么关系？
3. `render_03_nyx_attached_camera` 同时保留成功视频和 no-adapter 失败日志，对实验报告有什么价值？

## 小结

- viewer 是给人调试用的，camera 是给程序读观测用的。
- 远程或无显示环境中，先用 `show_viewer=False` 验证无界面物理循环。
- camera 验收从 RGB 和 `camera_config` 开始，depth、segmentation、sensor 放到后续步骤。
- 同样是图像，viewer、camera、overlay adapter、GUI proxy 和 Nyx renderer 的证据含义不同。
- 观察与渲染不是装饰，它决定后续视觉任务和数据采集是否可信。

## 参考资料

- Genesis World Documentation, Visualization & Rendering. https://genesis-world.readthedocs.io/en/v1.0.0/user_guide/getting_started/visualization.html
- Genesis World Documentation, Hello, Genesis World. https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/hello_genesis.html

## 导航

- 上一页：[观察、渲染与传感器](../03-observation-rendering-sensors.md)
- 返回目录：[观察、渲染与传感器](../03-observation-rendering-sensors.md)
- 下一页：[camera 与图像保存](02-camera-and-image-save.md)
