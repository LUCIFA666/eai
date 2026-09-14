# 观测与渲染

机器人能动起来之后，往往就想把仿真过程留下来：此刻的状态、传感器读数，还有画面。这一章讲怎么从 MuJoCo 把这些取出来，尤其是在没有显示器的服务器上，怎么照样渲染出图。

## 前置概念

读这一节前，建议先理解：

- **mjData**（详见 [mjModel vs mjData](02-modeling/06-mjmodel-vs-mjdata.md)）：每步会变的动态状态。
- **sensor 元素**（详见 [MJCF 整体骨架](02-modeling/01-mjcf-skeleton.md)）：`<sensor>` 是 MJCF 里声明传感器的顶层节。
- **step 循环**（详见 [MuJoCo 程序怎么运转](01-overview/02-mental-model.md)）：渲染一般发生在 step 之后、下一次 step 之前。

## 学习路径

| 小节 | 读完能回答 | 重点 |
|---|---|---|
| [直接读状态](04-observation-and-rendering/01-state-from-data.md) | 关节角、末端位置、site 坐标怎么读？ | qpos / xpos / site_xpos |
| [sensor 与 sensordata](04-observation-and-rendering/02-sensors.md) | 怎么声明传感器、怎么读读数？ | sensor 类型、声明、解析 sensordata |
| [相机与多视角](04-observation-and-rendering/03-camera-and-multiview.md) | 怎么定义一个机载相机？怎么拍多视角？ | `<camera>`、fovy、pos、xyaxes |
| [离屏渲染](04-observation-and-rendering/04-offscreen-renderer.md) | 怎么在没有窗口的情况下渲染图像、视频？ | mujoco.Renderer、深度图、分割图 |
| [交互式 viewer](04-observation-and-rendering/05-interactive-viewer.md) | 本地调试时怎么用鼠标转视角、暂停、单步？ | mujoco.viewer、快捷键、passive 模式 |
| [服务器渲染](04-observation-and-rendering/06-headless-setup.md) | 远程机器渲染怎么不出问题？ | MUJOCO_GL、EGL、OSMesa、排错 |
| [动手：录像管线](04-observation-and-rendering/07-hands-on-observation.md) | 自己搭一个多视角 + sensor 记录管线 | 完整脚本与产物 |

## 导航

- 上一节：[控制与物理](03-control-and-physics.md)
- 返回上级：[MuJoCo](../02-mujoco.md)
- 下一节：[接口与生态](05-interfaces-and-ecosystem.md)
