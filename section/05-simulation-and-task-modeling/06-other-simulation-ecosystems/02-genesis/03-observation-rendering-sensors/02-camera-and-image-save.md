# camera 与图像保存

本页讲 camera 作为程序观测入口时，如何设置位置、朝向、分辨率和视场角，并把 RGB / depth 等结果保存到文件。

## 本节目标

本节围绕下面几个问题展开：

1. camera 和 viewer 的职责有什么区别？
2. 相机的 `pos`、`lookat`、`res`、`fov` 各自影响什么？
3. 为什么要同时保存图像和相机配置？
4. `labs/06_genesis/04_observation_and_rendering.py` 应该输出哪些产物？

## camera 是程序的眼睛，不是 viewer 的截图

viewer 的目标是让人看见场景，camera 的目标是让程序拿到观测。它们经常显示同一个世界，但用途不同：

| 路径 | 主要对象 | 典型用途 |
|---|---|---|
| viewer | 人 | 交互检查、拖动视角、调试姿态和接触 |
| camera | 程序 | 保存 RGB / depth / segmentation，作为训练或评估输入 |
| sensor | 程序 | 读取相机、IMU、LiDAR、ContactForce 等结构化数据 |

官方 showcase 的复现记录中，很多问题都来自这条边界：离屏 camera 可以稳定保存画面，但 viewer 的 ImGui 面板、鼠标点选、debug overlay 不一定会进入 camera 图像。写实验报告时，必须说明画面从哪里来。

## 四个最小相机参数

配套脚本 `labs/06_genesis/04_observation_and_rendering.py` 使用的是一条最小 camera 链路。下面片段默认已经完成 `import genesis as gs` 并创建好 `scene`；完整上下文以配套脚本为准：

```python
cam_cfg = {
    "res": [640, 480],
    "pos": [3.5, 0.0, 2.5],
    "lookat": [0.0, 0.0, 0.5],
    "fov": 30,
}
cam = scene.add_camera(
    res=tuple(cam_cfg["res"]),
    pos=tuple(cam_cfg["pos"]),
    lookat=tuple(cam_cfg["lookat"]),
    fov=cam_cfg["fov"],
)
```

先把这四个参数记牢：

| 参数 | 含义 | 常见问题 |
|---|---|---|
| `res` | 输出图像宽高 | 分辨率太高会拖慢渲染；太低不利于检查细节 |
| `pos` | 相机在世界坐标系中的位置 | 放得太近会裁切，放得太远目标太小 |
| `lookat` | 相机看向的世界坐标点 | 目标不在视野里，通常先查这里 |
| `fov` | 视场角 | 太小像长焦，太大畸变明显 |

官方 Rendering showcase 里的 `follow_entity.py` 和 `moving_camera.py` 本质上就是在这四个参数上继续变化：前者让相机跟随一个实体，后者在 step 循环里不断修改相机位姿。初学时先掌握固定相机，再看动态相机。

<figure class="doc-figure">
<p class="doc-figure-title">相机跟随实体（follow entity）</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_00_follow_entity.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_00_follow_entity.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/rendering/follow_entity.py</code> 的真实运行（1060×580，75 帧）。相机不是固定截图工具，它可以锁定并跟随场景里的一个实体。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">相机在仿真循环中运动（moving camera）</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_01_moving_camera.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_01_moving_camera.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/rendering/moving_camera.py</code> 的真实运行。相机位姿在 step 循环里被不断修改，因此能做出运镜效果。</p>
</figure>

## 保存图像，也保存配置

配套脚本不是只保存一张 `png`，还会保存相机配置和摘要：

```text
runs/genesis_codecheck_YYYYmmdd_HHMMSS/
  artifacts/
    04_camera_rgb.png
    04_camera_config.json
  summaries/
    04_observation_and_rendering.json
```

摘要里至少应该有这些字段：

```json
{
  "camera_config": {
    "res": [640, 480],
    "pos": [3.5, 0.0, 2.5],
    "lookat": [0.0, 0.0, 0.5],
    "fov": 30
  },
  "rgb_shape": [480, 640, 3],
  "rgb_dtype": "uint8",
  "rgb_min": 0.0,
  "rgb_max": 255.0,
  "render_seconds": 0.12,
  "result": "passed"
}
```

数字不要求完全一致，重点是字段齐全。以后如果图像变黑、视角不对或目标消失，`camera_config.json` 能复现同一个视角，而不是凭记忆重新摆相机。

## 为什么官方素材要统一分辨率

官方 showcase 复现统一生成了 `1060x580` 预览图。原因不是这个分辨率有什么特殊物理意义，而是页面排版和横向比较需要稳定尺寸：

| 做法 | 好处 |
|---|---|
| 原始输出保留 | 不丢官方示例的原始分辨率和视频 |
| 统一预览尺寸 | contact sheet 不会因为大小不一难以比较 |
| 日志和摘要分开保存 | 图片好看时仍能追溯运行命令、版本和 adapter |

Nyx 示例尤其明显：有的原始输出是 `1920x1080`，有的是 `1600x600`，还有 `multi-camera multi-env` 的大拼图。统一预览只服务页面展示，原始输出仍保留在 `runs/genesis_readme_showcase_rendering_full_20260608_052306/artifacts/`。

因此，写报告时不要把 `1060x580` 预览当成“模型训练时真实拿到的 observation shape”。它只是统一后的页面视图。真正用于训练、评估或排错的 shape，要回到对应脚本的 `camera_config`、`summary.json` 或 sensor 返回值里确认。尤其是 LiDAR、ContactForce、Temperature 这类传感器，预览图往往是把结构化数据可视化后的结果，不是原始观测张量本身。

## 读完应能回答

1. 如果一张图是 `1060x580`，为什么仍然不能推出训练 observation 的 shape？
2. `camera_config.json` 在排查黑图或空图时有什么作用？
3. viewer 能看到 overlay，为什么 offscreen camera 不一定能保存同样内容？

## 小结

- camera 是程序读取观测的入口，viewer 是给人调试的窗口。
- 最小 camera 配置先抓住 `res`、`pos`、`lookat`、`fov`。
- 保存图像时必须保存配置和摘要，否则很难复现实验视角。
- 官方 Rendering 素材既要保留原始输出，也要生成统一预览，方便横向比较。
- 统一预览尺寸不等于原始 observation shape；训练或评估时必须回到配置和摘要。

## 导航

- 上一页：[viewer 与无界面运行](01-viewer-headless.md)
- 返回目录：[观察、渲染与传感器](../03-observation-rendering-sensors.md)
- 下一页：[Genesis 1.x 传感器接口](03-genesis-1-sensor-api.md)
