# 交互式 viewer

`mujoco.viewer` 是官方提供的本地交互窗口：鼠标转视角、双击选物体、空格暂停、`[`/`]` 单步。它和离屏 Renderer 分工不同，viewer 是给人看的，Renderer 是给程序批量出图的。

## 本节目标

本节把 viewer 用顺手：

1. `launch` 和 `launch_passive` 两种模式有什么区别，各用在什么时候？
2. 窗口里有哪些常用快捷键？
3. 怎么让自己的控制循环和 viewer 实时画面配合（`sync` / `lock`）？
4. viewer 和 Renderer 的画面为什么有时对不上？

## launch vs launch_passive

MuJoCo 的 viewer 提供两种运行模式：

| 模式 | 函数 | 谁控制步进 | 适用场景 |
|---|---|---|---|
| 托管（managed） | `viewer.launch(model, data)` | viewer 内部 | 快速查看模型、做简单交互 |
| 被动（passive） | `viewer.launch_passive(model, data)` | 脚本 | 一边跑自己的控制循环，一边实时看画面 |

**托管模式**最简单：

```python
import mujoco
import mujoco.viewer

model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

mujoco.viewer.launch(model, data)  # 阻塞，直到用户关闭窗口
```

viewer 内部有自己的仿真循环，会自动调用 `mj_step`。适合快速查看模型、拖动视角，但不适合嵌入自定义控制逻辑。

**被动模式**便于掌控仿真节奏：

```python
with mujoco.viewer.launch_passive(model, data) as viewer:
    while viewer.is_running():
        # 控制逻辑
        data.ctrl[:] = compute_my_control(data)
        mujoco.mj_step(model, data)

        # 同步：把更新的状态推给 viewer 显示
        viewer.sync()
```

`viewer.sync()` 是这里的关键，它把 `data` 状态同步到 viewer 的渲染画面，同时把 viewer 里的用户交互（鼠标扰动、GUI 选项改动）同步回 `data` 和 `model`。

macOS 用户注意：在 macOS 上渲染要在主线程执行，所以用 `launch_passive` 时通常得用 `mjpython` 代替 `python` 启动脚本：

```bash
mjpython my_script.py
```

## 鼠标交互与常用操作

在 viewer 窗口里：

| 操作 | 效果 |
|---|---|
| 左键拖动 | 旋转视角 |
| 右键拖动 | 垂直平移视角 |
| Ctrl + 右键拖动 | 水平平移视角 |
| 滚轮 / 中键拖动 | 缩放 |
| 双击物体 | 选中该 body |
| Ctrl + 双击 | 跟踪选中的 body（相机自动跟随） |
| Ctrl + 左键拖动（选中后） | 对选中物体施加力/力矩扰动 |
| 空格 | 暂停 / 恢复仿真 |
| `[` / `]` | 单步后退 / 前进（暂停时） |
| Tab / Shift+Tab | 在 UI 面板间切换（具体方向以 F1 帮助为准） |
| F1 | 显示帮助面板 |
| Ctrl+L | 热加载模型文件（从磁盘重新加载） |
| Esc | 退出跟踪模式 |

其中 `Ctrl+L` 热加载在调模型参数时很实用：在另一个终端编辑 MJCF 文件，再回到 viewer 里按一下，就能看到变化。

## 与控制脚本结合

被动模式下的标准循环：

```python
import mujoco
import mujoco.viewer
import numpy as np

model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)
mujoco.mj_resetDataKeyframe(model, data, 0)
mujoco.mj_forward(model, data)

def my_controller(data, step):
    """控制逻辑：返回 ctrl 数组"""
    return np.sin(step * 0.1) * np.ones(model.nu)

with mujoco.viewer.launch_passive(model, data) as viewer:
    step = 0
    while viewer.is_running():
        data.ctrl[:] = my_controller(data, step)
        mujoco.mj_step(model, data)

        # 锁住 viewer 以安全修改可视化选项
        with viewer.lock():
            viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = 1

        viewer.sync()
        step += 1
```

这里的 `viewer.lock()` 不能省：viewer 运行在自己的线程里，修改 `model` 或 `data` 时需要持有锁。`sync()` 会帮忙管理一部分同步，但直接修改模型或可视化选项时，最好显式持有锁。

## viewer 与 Renderer 的差异

有时会发现 viewer 里看到的画面和 Renderer 出图不一样。常见原因：

| 现象 | 可能原因 |
|---|---|
| 颜色不一样 | viewer 有默认头灯（headlight），Renderer 默认没开 |
| 物体位置不一样 | viewer 可能在 sync 之前就渲染了，拿到的是上一帧状态 |
| 相机视角不一样 | viewer 使用自由相机，Renderer 使用在 `update_scene` 里指定的相机 |
| 有些 geom 看不见 | viewer 的 `mjVIS_STATIC` 等可视化标志可能关闭了某类几何的渲染 |

想让 Renderer 和 viewer 的画面尽量接近，可以在 `update_scene` 时显式传入一份可视化选项 `scene_option`，把渲染标志对齐到 viewer 的设置：

```python
renderer.update_scene(data, scene_option=mujoco.MjvOption())
```

## 小结

- `viewer.launch` 是快速查看模型的简单方式（阻塞式），`viewer.launch_passive` 适合嵌入自定义控制循环。
- 被动模式下 `viewer.sync()` 是桥梁：把状态推给 viewer，把用户交互拉回来。
- 常用快捷键：空格暂停、双击选中、Ctrl+L 热加载、Tab 切换面板。
- viewer 和 Renderer 的画面可能因光照、相机、渲染标志不同而有差异。

## 动手练习

用 `viewer.launch` 打开 Panda 模型（这一步要在本地有图形界面的机器上跑，远程或无显示器环境开不了窗口），在窗口里双击手部 body 选中它，再按住 Ctrl + 左键拖动给它施加扰动。会看到机械臂被拖着偏离原位；松开鼠标后，position actuator 又把它拉回原来的姿态。

## 参考资料

- [MuJoCo Documentation: Python Bindings（viewer / launch / launch_passive / sync）](https://mujoco.readthedocs.io/en/stable/python.html)

## 导航

- 上一节：[离屏渲染](04-offscreen-renderer.md)
- 返回上级：[观测与渲染](../04-observation-and-rendering.md)
- 下一节：[服务器渲染](06-headless-setup.md)
