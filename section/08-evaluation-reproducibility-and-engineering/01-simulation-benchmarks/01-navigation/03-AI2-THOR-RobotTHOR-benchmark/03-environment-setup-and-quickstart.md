# 3.3 环境配置与快速运行

## 目标

AI2-THOR 的优点是入门运行相对直接。和一些需要额外下载大型场景数据、编译复杂仿真器的环境不同，AI2-THOR 可以直接通过 Python 包安装，并在第一次初始化 Controller 时自动下载 Unity build。

本节主要介绍 AI2-THOR 的基础安装、headless 服务器运行方式、最小 demo。
## 基础环境准备

建议使用 conda 创建独立环境：

```bash
conda create -n ai2thor_env python=3.9 -y
conda activate ai2thor_env
```

安装 AI2-THOR：

```bash
pip install ai2thor
```

或者使用 conda：

```bash
conda install -c conda-forge ai2thor
```

安装后可以通过 Python 导入测试：

```bash
python -c "import ai2thor; print('ai2thor ok')"
```

第一次启动 Controller 时，AI2-THOR 会自动下载对应的 Unity build 到本地缓存目录。这个过程可能需要网络连接，时间取决于网络速度。

## 最小运行示例

可以先写一个最小脚本，验证 Controller 是否能正常启动。

```bash
cat > minimal_ai2thor_demo.py <<'PY'
from ai2thor.controller import Controller

controller = Controller(scene="FloorPlan10")

event = controller.step(action="RotateRight")

print("Last action success:", event.metadata["lastActionSuccess"])
print("Agent position:", event.metadata["agent"]["position"])
print("Frame shape:", event.frame.shape)

controller.stop()
PY
```

运行：

```bash
python minimal_ai2thor_demo.py
```

如果环境正常，终端会打印动作是否成功、agent 位置和 RGB 图像尺寸。

这个最小例子体现了 AI2-THOR 的基本交互流程：

```text
Controller 初始化场景
-> step 执行动作
-> event 返回图像和 metadata
-> 继续执行下一步动作
```



## 服务器 headless 运行

在服务器上运行 AI2-THOR 时，常见问题是没有显示器。默认情况下，Unity 环境可能会尝试打开窗口，这在远程服务器或计算集群上经常会失败。

AI2-THOR 支持 CloudRendering，用于 headless / off-screen 渲染。可以这样写：

```bash
cat > minimal_ai2thor_headless.py <<'PY'
from ai2thor.controller import Controller
from ai2thor.platform import CloudRendering

controller = Controller(
    scene="FloorPlan10",
    platform=CloudRendering,
    width=800,
    height=600
)

event = controller.step(action="MoveAhead")

print("Last action success:", event.metadata["lastActionSuccess"])
print("Agent position:", event.metadata["agent"]["position"])
print("Frame shape:", event.frame.shape)

controller.stop()
PY
```

运行：

```bash
python minimal_ai2thor_headless.py
```

如果服务器 GPU、驱动和渲染环境匹配，这种方式通常比依赖桌面显示更适合远程运行。

## 常见环境问题

AI2-THOR 虽然安装简单，但在服务器上仍然可能遇到一些问题。

| 问题                | 可能原因                       | 处理思路                              |
| ----------------- | -------------------------- | --------------------------------- |
| Controller 初始化失败  | Unity build 下载失败或缓存损坏      | 检查网络，删除缓存后重新下载                    |
| 没有显示器无法启动         | 默认渲染需要窗口                   | 使用 CloudRendering 或 Docker        |
| frame 为空或渲染失败     | GPU / 驱动 / OpenGL / EGL 问题 | 检查服务器图形环境                         |
| import ai2thor 失败 | Python 环境没装对               | 确认当前 conda 环境和 pip 路径             |
| 动作失败              | 物体不可见、距离过远或状态不满足           | 查看 event.metadata["errorMessage"] |
| 版本不一致             | 示例代码与安装版本不匹配               | 查看官方文档或固定 ai2thor 版本              |

调试时建议先运行最小 Controller 示例，不要一开始就跑复杂 ObjectNav 或 ManipulaTHOR 任务。这样更容易判断问题来自安装、渲染还是任务配置。

## RoboTHOR 场景运行思路

RoboTHOR 属于 AI2-THOR 框架中的 sim-to-real 环境。它的重点不是普通 iTHOR 房间，而是仿真场景与真实物理房间的对应关系。

在 RoboTHOR 中，常见任务是 ObjectNav：

```text
agent 从随机位置出发
-> 给定目标物体类别
-> 在仿真公寓中寻找目标
-> 根据导航成功率和路径效率评测
```

使用 RoboTHOR 时，通常需要确认：

```text
场景名称是否属于 RoboTHOR
任务 episode 是否来自 RoboTHOR 数据集
评测时是否使用正确的 split
传感器输入是否与 challenge 设置一致
```

RoboTHOR 更适合在已经理解 iTHOR 基础交互之后学习。

## ManipulaTHOR 运行思路

ManipulaTHOR 随 AI2-THOR 一起安装，但它的任务和动作更复杂。它包含机械臂，因此不只是移动 agent，还要控制机械臂接近或操作物体。

学习顺序建议是：

```text
先跑通普通 iTHOR Controller
-> 理解 event.frame 和 metadata
-> 再看 ManipulaTHOR Controller 初始化
-> 再学习 ArmPointNav 或简单机械臂动作
```

不要一开始就直接跑复杂操作任务。ManipulaTHOR 涉及机械臂位姿、末端执行器、物体可达性和碰撞等问题，调试难度比普通导航更高。

## 本节小结

AI2-THOR 的基础运行流程可以概括为：安装 ai2thor，初始化 Controller，执行 action，读取 event.frame 和 event.metadata。这个流程比完整 challenge 复现简单，但已经能体现具身智能中的闭环交互。

在服务器上运行时，需要重点关注 headless 渲染、Unity build 下载、GPU / 驱动环境和 Python 版本。建议先跑通最小 iTHOR demo，再逐步扩展到 ObjectNav、RoboTHOR 和 ManipulaTHOR。
