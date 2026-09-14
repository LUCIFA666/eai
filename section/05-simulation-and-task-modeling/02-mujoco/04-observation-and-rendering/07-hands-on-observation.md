# 动手：录像管线

把前面几节学到的东西串成一个真实可跑的脚本：给 Panda 加多视角相机和力 sensor，运行一段控制，同时录视频、记录 sensor 读数、保存对齐的 RGB + Depth。

## 本节目标

做完这三个练习，应该能搭出一个能用的录像管线：

1. 在一个 MJCF 里同时声明多相机和多种 sensor。
2. 写一个循环，每帧渲染多视角并记录 sensor 读数。
3. 把图像、深度、sensor 按时间戳对齐存盘，形成一份可用于模仿学习的记录。

每个练习都给了起点和验收信号，跑出对应结果即可。

## 练习 1：加 3 个机位 + 1 个力 sensor

**目标**：在 Panda 的场景文件里加入多视角相机和腕部力矩传感器。

**步骤**：把 menagerie 的 `franka_emika_panda/` 整个目录复制到工作目录（要带上 `assets/`，否则 mesh 找不到），把里面的 `panda.xml` 另存为 `scene_with_cams.xml`，然后做下面三处改动。相机名要和练习 2 的代码**完全一致**（`top_down` / `side_view` / `wrist_rgb`），否则练习 2 会找不到相机。

**① 在 `<worldbody>` 开头补上地面、灯光和两个第三人称相机：**

```xml
<geom type="plane" size="2 2 0.1" pos="0 0 0"/>
<light pos="0 0 2" dir="0 0 -1"/>
<camera name="top_down"  pos="0.4 0 1.2"    xyaxes="1 0 0 0 1 0"             fovy="55"/>
<camera name="side_view" pos="1.2 -0.6 0.7" xyaxes="0.4 0.9 0 -0.2 0.1 0.97" fovy="55"/>
```

**② 在 `<body name="hand" ...>` 内部加一个 site（stock Panda 没有现成 site）和一个机载相机：**

```xml
<site name="wrist_site" pos="0 0 0" size="0.01"/>
<camera name="wrist_rgb" pos="0 -0.05 0.02" xyaxes="1 0 0 0 0 1" fovy="70"/>
```

**③ 在文件末尾 `</mujoco>` 之前加一个 `<sensor>` 节，力和力矩都指向 `wrist_site`：**

```xml
<sensor>
  <force  name="wrist_force"  site="wrist_site"/>
  <torque name="wrist_torque" site="wrist_site"/>
</sensor>
```

改完加载 `scene_with_cams.xml`，打印 `model.ncam`、`model.nsensor` 确认。

**验收信号**：`ncam == 3`（`top_down` / `side_view` / `wrist_rgb`；自由相机不计入 `model.ncam`），`nsensor == 2`（force + torque，对应 `nsensordata == 6`）。

## 练习 2：写录像循环

**目标**：在一个循环里同时执行控制、渲染多视角、记录 sensor 数据。

```python
import mujoco
import numpy as np
import imageio          # 录 mp4 需先安装：pip install imageio imageio-ffmpeg
import json
import os

model = mujoco.MjModel.from_xml_path("scene_with_cams.xml")
data = mujoco.MjData(model)
mujoco.mj_resetDataKeyframe(model, data, 0)
mujoco.mj_forward(model, data)

# 控制策略（占位：保持当前 home 位姿；换成自己的控制器即可）
def compute_control(data, step):
    return data.ctrl.copy()

cam_names = ["top_down", "side_view", "wrist_rgb"]
os.makedirs("records", exist_ok=True)

# 为每个相机创建一个 video writer
writers = {
    name: imageio.get_writer(f"records/{name}.mp4", fps=30)
    for name in cam_names
}

sensor_log = []

with mujoco.Renderer(model, height=480, width=640) as renderer:
    for step in range(300):  # 300 帧，每帧 5 个物理步 → 约 3 秒仿真
        # 控制逻辑
        data.ctrl[:] = compute_control(data, step)

        # 物理步进（每渲染帧走 5 个物理步）
        for _ in range(5):
            mujoco.mj_step(model, data)

        # 多视角渲染
        for cam_name in cam_names:
            renderer.update_scene(data, camera=cam_name)
            frame = renderer.render()
            writers[cam_name].append_data(frame)

        # 记录 sensor 数据
        sensor_log.append({
            "step": step,
            "time": float(data.time),
            "sensors": data.sensordata.copy().tolist(),
        })

# 清理
for w in writers.values():
    w.close()

with open("records/sensors.jsonl", "w") as f:
    for entry in sensor_log:
        f.write(json.dumps(entry) + "\n")
```

**验收信号**：跑完后 `records/` 目录下应有 3 个 mp4 文件和 1 个 `sensors.jsonl` 文件。

## 练习 3：对齐时间戳保存

**目标**：确保所有数据（图像、深度、sensor）严格按时间戳对齐。

在练习 2 的基础上，给每个相机除了 RGB，再多抓深度和分割。注意深度、分割是 Renderer 的**模式**（见离屏渲染一节），构造函数没有 `depth=` / `segmentation=` 参数；每切一次模式都要重新 `update_scene` 再 `render`。把下面这段放进练习 2 的 `for step` 循环里、紧跟在多视角渲染之后，用 step 编号命名就能让各路数据天然对齐：

```python
import numpy as np
import os

# 放进练习 2 的 for step 循环内（复用循环里的 step、data、renderer、cam_names）
for cam_name in cam_names:
    os.makedirs(f"records/{cam_name}", exist_ok=True)

    renderer.update_scene(data, camera=cam_name)
    rgb = renderer.render()                       # (H, W, 3) uint8

    renderer.enable_depth_rendering()
    renderer.update_scene(data, camera=cam_name)
    depth = renderer.render().copy()              # (H, W) float32
    renderer.disable_depth_rendering()

    renderer.enable_segmentation_rendering()
    renderer.update_scene(data, camera=cam_name)
    seg = renderer.render().copy()                # (H, W, 2) int32
    renderer.disable_segmentation_rendering()

    np.save(f"records/{cam_name}/{step:06d}_rgb.npy", rgb)
    np.save(f"records/{cam_name}/{step:06d}_depth.npy", depth)
    np.save(f"records/{cam_name}/{step:06d}_seg.npy", seg)
```

每帧、每相机都要切两次模式、渲三遍，开销不小；调试时把练习 2 的总步数调小（如 `range(30)`）、或每隔几帧才存一次即可。

**验收信号**：

- `records/<相机名>/` 下出现一批 `XXXXXX_rgb.npy` / `_depth.npy` / `_seg.npy`，文件名带 step 编号。
- 同一个 step 的三视角图像、深度、分割，和练习 2 记录的 sensor 读数都对应同一时刻（同一个 step、同一个 `data.time`）。
- 目录结构清晰，可以直接拿去做模仿学习的数据集。

## 验收清单

| 练习 | 验收标准 |
|---|---|
| 练习 1 | MJCF 里加了多相机和 sensor，`ncam == 3`, `nsensor > 0` |
| 练习 2 | `records/` 下有 3 个 mp4 + 1 个 `sensors.jsonl` |
| 练习 3 | 深度和分割数据也正确保存，时间戳对齐 |

## 参考资料

- [MuJoCo Documentation: Python Bindings（Renderer / sensor）](https://mujoco.readthedocs.io/en/stable/python.html)
- [MuJoCo Documentation: Programming（rendering / 数据记录）](https://mujoco.readthedocs.io/en/stable/programming/index.html)

## 导航

- 上一节：[服务器渲染](06-headless-setup.md)
- 返回上级：[观测与渲染](../04-observation-and-rendering.md)
- 下一节：[接口与生态](../05-interfaces-and-ecosystem.md)
