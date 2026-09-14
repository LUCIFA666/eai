# 服务器渲染（headless）

SSH 登上一台没有显示器的机器、一跑渲染就报错，是初学时常碰到的环境问题。MuJoCo 通过环境变量 `MUJOCO_GL` 选渲染后端：EGL 走 GPU，OSMesa 走 CPU 软渲染。

## 本节目标

本节按场景把 headless 渲染讲清楚：

1. `MUJOCO_GL` 这个环境变量到底决定什么？
2. EGL 和 OSMesa 各适合什么场景？
3. SSH、Docker 下有哪些常见坑？
4. 报错时按什么顺序排查？

## MUJOCO_GL 环境变量

`MUJOCO_GL` 让 MuJoCo 知道该用哪种方式来创建 OpenGL 上下文。它的取值如下：

| 值 | 含义 | 需要显示器？ | 需要 GPU？ | 适用场景 |
|---|---|---|---|---|
| `glfw` | GLFW 窗口（默认） | 需要 | 建议有 | 本地开发、有显示器的机器 |
| `egl` | EGL 上下文 | 不需要 | 建议有 | **服务器 GPU 渲染的首选** |
| `osmesa` | OSMesa 软件渲染 | 不需要 | 不需要 | CPU 渲染的退路（纯 CPU） |

设置方式（在运行命令前加上）：

```bash
MUJOCO_GL=egl python my_script.py
```

或者在 Python 脚本里设置（必须在 `import mujoco` 之前）：

```python
import os
os.environ["MUJOCO_GL"] = "egl"
import mujoco
```

## EGL：服务器 GPU 渲染

EGL（EGL Native Platform Interface）是 Khronos 的标准 API，用于在不依赖窗口系统的情况下创建 OpenGL 上下文。在配有 NVIDIA 显卡的 Linux 服务器上，这通常是首选。

```bash
MUJOCO_GL=egl python my_rendering_script.py
```

**依赖**：EGL 通常随 NVIDIA 驱动（`nvidia-driver-*`）一起安装。可以用 `eglinfo` 或 `ldconfig -p | grep libEGL` 检查是否可用。

**常见错误及处理**：

| 错误信息 | 可能原因 | 处理 |
|---|---|---|
| `Failed to initialize EGL` | EGL 库不可用 | 安装 NVIDIA 驱动或 `libegl1-mesa-dev` |
| `EGL_BAD_MATCH` 或 `EGL_BAD_CONFIG` | GPU 不支持请求的配置 | 尝试 `MUJOCO_GL=osmesa` |
| 渲染出来全是黑色 | EGL 上下文创建成功但渲染失败 | 检查 MuJoCo 版本是否匹配 |

## OSMesa：CPU 软件渲染

如果服务器根本没有 GPU（纯 CPU 云实例），或者 EGL 搞不定，可以用 OSMesa（Off-Screen Mesa），它在 CPU 上做软件渲染：

```bash
MUJOCO_GL=osmesa python my_rendering_script.py
```

**依赖**：需要安装 OSMesa 库。在 Ubuntu/Debian 上：

```bash
sudo apt install libosmesa6-dev
```

**性能预期**：OSMesa 是纯 CPU 渲染，比 GPU（EGL）慢不少。对于偶尔渲几张图做记录来说没问题；对于每步都要渲染高分辨率图像（比如训练时同步渲染）的场景，可能会成为明显的瓶颈。

## Docker / 远程开发常见问题

在 Docker 容器和远程 SSH 环境里，渲染经常遇到额外障碍：

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `Could not open GL context` | Docker 镜像里缺 OpenGL 库 | `apt install libgl1-mesa-glx libegl1-mesa` |
| EGL 报错但在宿主机上正常 | Docker 没挂载 GPU 设备 | `docker run --gpus all ...` 或挂载 `/dev/dri` |
| X11 相关错误 | MuJoCo 试图连接显示器 | 明确设置 `MUJOCO_GL=egl` 或 `osmesa` |
| `libGL error: failed to load driver` | 缺少特定驱动 | 安装 `mesa-utils`，检查 `glxinfo` |
| macOS SSH 到 Linux 渲染失败 | SSH 不会转发 GPU | 用 EGL/OSMesa，不要依赖 X11 forwarding |

## 排错顺序

遇到渲染问题时，建议按以下顺序排查：

1. **确认 MUJOCO_GL 被正确设置**：在 Python 里 `print(os.environ.get("MUJOCO_GL"))` 看看是不是预期的值。
2. **确认设置发生在 import mujoco 之前**：`import mujoco` 之后再改环境变量不会生效。
3. **试另外的后端**：`egl` 不行换 `osmesa`，`osmesa` 不行尝试 `glfw`（如果有显示器）。
4. **缩小问题范围**：用最简单的脚本（加载一个 box、渲染一帧、print pixels.shape）测试，排除模型或代码的问题。
5. **检查 MuJoCo 版本**：`python -c "import mujoco; print(mujoco.__version__)"`，确认版本和文档一致。

## 小结

- `MUJOCO_GL=egl` 是服务器 GPU 渲染的首选，`MUJOCO_GL=osmesa` 是 CPU 渲染的退路。
- 环境变量必须在 `import mujoco` 之前设置。
- Docker 里注意挂载 GPU 和安装 OpenGL 库。
- 排错顺序：确认环境变量 → 确认设置时机 → 换后端 → 最小脚本测试 → 检查版本。

## 参考资料

- [MuJoCo Documentation: Programming（Using OpenGL / MUJOCO_GL / EGL / OSMesa）](https://mujoco.readthedocs.io/en/stable/programming/index.html)

## 导航

- 上一节：[交互式 viewer](05-interactive-viewer.md)
- 返回上级：[观测与渲染](../04-observation-and-rendering.md)
- 下一节：[动手：录像管线](07-hands-on-observation.md)
