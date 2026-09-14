# 渲染常见问题

前两页已经讲过 camera 怎么设、sensor 怎么读。这一页专门讲**做渲染和保存图像时容易踩的坑**：现象是什么、根因通常在哪、先改什么。

## 本节目标

1. viewer 里能看见，离屏 camera 却不对——这是为什么？
2. 保存的 RGB 全黑、全白或空图，通常先查什么？
3. 远程服务器和本地桌面，渲染失败各该怎么拆？
4. 传感器预览、Nyx、GUI 示例各自容易出什么问题？

## viewer 能看，camera 图不对

这是初学者最常遇到的一类误会。

| 现象 | 常见原因 | 怎么处理 |
|---|---|---|
| viewer 里有 ImGui 面板、鼠标高亮、debug 线框 | overlay 画在 viewer 上，不属于离屏 camera | 不要指望 `cam.render()` 能截到同样内容；需要 overlay 时，从 debug primitive 或 sensor 数据自己画 |
| viewer 视角正常，camera 图里目标很小或不在画面里 | `pos / lookat / fov` 和 viewer 当前视角不是同一套参数 | 先在 viewer 里摆好视角，再把对应的世界坐标写进 camera 配置；或保存 `camera_config.json` 方便对照 |
| 动态示例有视频，静态 Nyx 示例只有 PNG | 官方条目本来就不是同一种输出 | 跟随实体、移动相机这类会产 MP4；材质、灯光、Gaussian splat 等多是静态图，没有视频不代表失败 |

记住一条边界：**viewer 给人看，camera 给程序读。** 两者可以显示同一个物理场景，但图像来源不一定相同。

## 保存的 RGB 全黑、全白或空图

文件落盘了，打开却是一片黑——通常不是渲染器“坏了”，而是相机没看到有效内容。

| 现象 | 常见原因 | 怎么处理 |
|---|---|---|
| 图像存在，但 `min == max`（全黑或全白） | 相机朝向空地、目标在视锥外、或被近裁剪面裁掉 | 查 `pos`、`lookat`、`fov`；目标很小时把相机拉近或增大 `fov` |
| 文件大小为 0 或读出来 shape 不对 | 渲染步骤没跑完、路径写错、或 dtype 异常 | 看日志里 render 阶段有没有 exception；用 `numpy` 打印 `shape`、`dtype` |
| 数值里有 NaN | 深度/normal 输出或后处理出错 | 先回到最小 RGB 链路，确认基础 camera 正常后再加 depth、segmentation |
| 改了很多次仍对不上 | 没有保存相机配置，每次凭感觉重摆 | 同时保存图像和 `camera_config.json`，黑图时先对照配置而不是乱改参数 |

可以用几行代码快速判断是不是“空图”：

```python
import imageio.v3 as iio
import numpy as np

rgb = iio.imread("04_camera_rgb.png")
print(rgb.shape, rgb.dtype, rgb.min(), rgb.max())
assert np.isfinite(rgb).all()
assert float(rgb.max()) > float(rgb.min())
```

`max > min` 只能说明图像有动态范围，不能保证构图好看；但 `max == min` 几乎可以直接断定相机没看到目标。

## 远程服务器上渲染失败

本地能跑、服务器上挂——多半是环境叠加，不是 Genesis API 本身变了。

| 现象 | 常见原因 | 怎么处理 |
|---|---|---|
| viewer 打不开 | 无显示器、无 X11、SSH 没开转发 | 先关 viewer，用离屏 camera 保存一张 RGB；GUI 问题单独处理 |
| 只有带 ImGui / 鼠标交互的示例失败 | 依赖交互 viewer 或 Xvfb | 标注“需要 GUI”；无界面环境下改用静态说明图，不要当成普通 render 失败 |
| 一上 Nyx、视频编码就报错 | 缺插件、缺 `av`、或 GPU/驱动不满足 | 先跑最小 RGB camera；视频编码缺 `av` 就 `pip install av` |
| 同时开 viewer、GPU、Nyx、复杂机器人 | 变量叠太多，报错位置不准 | 按下面顺序逐个打开 |

建议的排错顺序：

1. 关 viewer，确认 `scene.build()` 和 `scene.step()` 能跑；
2. 用离屏 camera 保存一张最小 RGB；
3. 确认图像不是全黑，相机配置合理；
4. 再开 viewer 或 Xvfb；
5. 最后才上 Nyx、视频录制、多相机或多环境。

## 传感器数据和 camera 图不是一回事

跑 LiDAR、ContactForce、Temperature 等示例时，页面上的图经常不是“camera 直接拍出来的”。

| 现象 | 常见原因 | 怎么处理 |
|---|---|---|
| LiDAR 示例的图里有点云，但 camera RGB 里没有 | 点云来自 `sensor.read()`，需要投影或单独可视化 | 训练或评估时用 sensor 返回值，不要拿预览 PNG 当 observation |
| ContactForce 示例右侧是曲线 | 力传感器更适合时序曲线，不适合硬塞进 RGB | 读 sensor 历史数据再画图 |
| 表面距离、温度场示例视频很短 | 官方示例展示的是能力入口，不是长过程动画 | 短帧数通过只说明“接口能跑”，不能按“视频够不够长”判断成败 |
| 预览图是 `1060x580`，脚本里 camera 是别的分辨率 | 页面预览为排版统一做了缩放 | 训练用的 shape 以脚本里的 `camera_config` 或 sensor 输出为准 |

## Nyx 与路径规划报错

Nyx 渲染器能做出更丰富的画面，但也多一层依赖。`render_03_nyx_attached_camera`（官方 `examples/02_attached_camera.py`）是一个典型例子：脚本在路径规划接触查询里可能直接失败：

```text
RuntimeError: gather(): Expected dtype int64 for index
File ".../genesis/utils/path_planning.py", line 122, in get_exclude_geom_pairs
scene_contact_info = self._entity.get_contacts()
```

| 现象 | 常见原因 | 怎么处理 |
|---|---|---|
| 上述 `gather()` / `int64` 报错 | 路径规划模块里 contact 查询的张量类型不匹配 | 这是路径规划问题，不是相机参数问题；先查 Genesis 版本，或查阅该示例是否有跳过 path planner 的说明 |
| Nyx 示例 import 失败 | 未安装 Nyx 插件 | 先掌握 Genesis 自带 camera；Nyx 作为可选扩展单独装 |
| 材质、灯光类示例只有 PNG | 本来就是静态渲染条目 | 能出 preview 即可，不必强求 MP4 |

下面 6 张是 Nyx 静态渲染示例的常见效果，供对照“正常长什么样”：

<figure class="doc-figure">
<p class="doc-figure-title">Nyx：hello（入门）</p>
<img src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_02_nyx_hello.png" alt="Nyx hello">
<p class="doc-figure-subtitle">官方 <code>examples/01_hello_nyx.py</code>。Nyx 渲染器的最小入口。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">Nyx：PBR 材质</p>
<img src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_04_nyx_materials.png" alt="Nyx PBR materials">
<p class="doc-figure-subtitle">官方 <code>examples/03_materials.py</code>。不同渲染后端下材质表现会不同。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">Nyx：光源类型</p>
<img src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_05_nyx_light_types.png" alt="Nyx light types">
<p class="doc-figure-subtitle">官方 <code>examples/04_light_types.py</code>。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">Nyx：高斯泼溅（Gaussian splat）</p>
<img src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_06_nyx_gaussian_splat.png" alt="Nyx gaussian splat">
<p class="doc-figure-subtitle">官方 <code>examples/05_gaussian_splat.py</code>。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">Nyx：物体拾取</p>
<img src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_07_nyx_object_picking.png" alt="Nyx object picking">
<p class="doc-figure-subtitle">官方 <code>examples/06_object_picking.py</code>。依赖交互 viewer。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">Nyx：多相机多环境</p>
<img src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_08_nyx_multi_camera_multi_env.png" alt="Nyx multi camera multi env">
<p class="doc-figure-subtitle">官方 <code>examples/07_multi_camera_multi_env.py</code>。</p>
</figure>

挂载相机若最终能出视频，也要知道中间可能改过脚本或跳过了 path planner。成功画面和原始报错日志要一起看，避免误以为“官方示例零修改就能跑”。

<figure class="doc-figure">
<p class="doc-figure-title">Nyx 挂载相机</p>
<video src="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_03_nyx_attached_camera.mp4" poster="/section/05-simulation-and-task-modeling/06-other-simulation-ecosystems/02-genesis/assets/render_03_nyx_attached_camera.png" controls muted loop playsinline preload="none"></video>
<p class="doc-figure-subtitle">官方 <code>examples/02_attached_camera.py</code>（Nyx 插件）。原脚本可能在路径规划接触查询处失败；若使用变通写法生成视频，要知道和官方原版的差别。</p>
</figure>

## 按日志快速归类

看到报错不知道改哪，可以先对号入座：

| 日志或现象 | 更可能的问题 | 先做什么 |
|---|---|---|
| `ModuleNotFoundError: av` | 缺视频编码库 | `pip install av`，重跑 |
| `RuntimeError: gather(): Expected dtype int64 for index` | 路径规划 / contact 查询 | 不要先改相机；查版本、查示例说明 |
| RGB 全黑但 viewer 正常 | 相机位姿或裁剪 | 改 `pos / lookat / fov` |
| viewer 有 overlay，camera 没有 | viewer 与 camera 职责不同 | 从 sensor 或 debug 数据自己画 |
| 只有 GUI 示例挂 | 无界面环境 | 关 viewer，或标注 GUI 依赖 |

渲染问题不总是“渲染器坏了”，也可能是依赖、相机配置、viewer 边界，或机器人路径规划。

## 读完应能回答

1. viewer 里能看见 debug 线框，为什么离屏 camera 保存的 PNG 里没有？
2. RGB 文件存在但全黑，应先改 `pos / lookat / fov`，还是先装 Nyx？
3. LiDAR 预览图里的点云，能直接当作训练用的 observation 吗？
4. 远程服务器第一次跑渲染，为什么要先关 viewer、只保存一张 RGB？

## 小结

- viewer 和 camera 是两条路：前者方便人调试，后者给程序读观测。
- 全黑图多半是相机没看到目标，先查位姿和裁剪，不要一上来换渲染后端。
- 传感器预览、Nyx 图、GUI 截图来源各不同，不能混当成同一种 observation。
- 远程环境一次只开一个变量：先物理循环，再离屏 RGB，再 viewer，最后 Nyx 和视频。

## 导航

- 上一页：[Genesis 1.x 传感器接口](03-genesis-1-sensor-api.md)
- 返回目录：[观察、渲染与传感器](../03-observation-rendering-sensors.md)
- 下一页：[并行环境](../04-parallel-envs.md)
