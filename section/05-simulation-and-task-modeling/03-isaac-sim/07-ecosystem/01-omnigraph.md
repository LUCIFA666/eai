# OmniGraph / Action Graph

前面几章你一直在"写一段 Python 顺序脚本：循环里读状态、发动作、推进物理"。但 Isaac Sim 里还有另一套组织"每帧做什么"的方式——**OmniGraph**。这一页讲它不是为了炫技：ROS 2 Bridge 这类接口能力，在 Isaac Sim 里很多都是通过 OmniGraph 节点实现的。不懂它，下一页接 ROS 2 时你会困惑"怎么全是连线、没有 Python"。

## 本节目标

本节围绕下面几个问题展开：

1. OmniGraph 和 Action Graph 分别是什么，谁负责什么？
2. 建图有哪三种方式，发布频率怎么控制？
3. 怎么用 tick 验证图在运行，图和 Python 主循环又怎么分工？

阅读这一页前，最好已经会写 Isaac Sim 独立脚本，并准备把仿真数据接到外部节点。不要求你用过节点编辑器，只要求你建立"数据沿图流动、被 tick 驱动"的理解视角。

## OmniGraph

OmniGraph 是 Omniverse / Isaac Sim 的**可视化数据流计算系统**：把"节点（node）"用"连线（connection）"接起来，数据沿连线流动，按某种"执行（tick）"规则触发计算。如果你见过虚幻引擎的蓝图、或节点式材质编辑器，它是同一类东西。

GUI 打开方式：`Window > Graph Editors > Action Graph`。

一句话类比：**Action Graph 像一条工厂流水线**——`On Playback Tick` 是节拍器，每敲一拍，挂在它下游的各个工位（节点）就按拍各做一件事：读关节、打时间戳、发布话题。

那为什么不全用 Python？因为很多事情要"**每个仿真帧都做、而且和渲染 / 物理时钟严格对齐**"——发布传感器、收发 ROS 消息、驱动关节。用一张随仿真 tick 的图来描述，比在 Python 主循环里手写更稳、更容易复用，也更容易被 GUI 工具和官方快捷方式自动生成。

## Action Graph

OmniGraph 有几种执行模型，机器人里最常用的是 **Action Graph**——执行 / 事件驱动：有一个"执行入口"节点产生 tick，连在它下游的节点才会在那一帧执行。

最常见的入口是 **On Playback Tick**：按下 Play 后，每个仿真帧产生一次 tick。它通常和另外两个几乎总会出现的节点搭配：

<figure class="doc-figure">
<p class="doc-figure-title">Action Graph：把"每帧要做什么"交给一张随物理时钟 tick 的图</p>
<div class="figure-flow">
<div class="figure-node"><strong>On Playback Tick：</strong>节奏来源——按下 Play 后每个仿真帧产生一次 tick（执行入口）</div>
<div class="figure-node"><strong>Read Simulation Time：</strong>提供仿真时间戳，发带 <code>header.stamp</code> 的消息要用它，保证下游对齐</div>
<div class="figure-node"><strong>Publish / 功能节点：</strong>发布关节状态、相机、雷达、TF……每个节点用 frameSkipCount 各自降频</div>
<div class="figure-node"><strong>下游节点：</strong>ROS 2 话题、RViz、规划 / 控制节点，或其它外部程序</div>
</div>
<p class="doc-figure-subtitle">ROS2 Context 节点（domain id 等）只在用 ROS 2 时出现，供所有 ROS 2 节点共享。</p>
</figure>

- **On Playback Tick**：节奏来源，"播放时每帧执行一次"。
- **Isaac Read Simulation Time**：提供仿真时间戳；发布带 `header.stamp` 的消息要用它，否则下游时间对不齐。
- **ROS2 Context**：ROS 2 节点共享的上下文（domain id 等），只在用 ROS 2 时需要。

## 发布频率

Action Graph 的 tick 绑定在仿真帧上。所以一个传感器 / 发布节点的频率不是随便设的，而是 `仿真帧率 ÷ 跳帧数`。Isaac Sim 用 **frameSkipCount**（或一个 Simulation Gate 节点）控制"每隔几帧才真正发布一次"：

```text
仿真 60 FPS，某 publisher frameSkipCount = 1  → 发布 ~30 Hz
                          frameSkipCount = 11 → 发布 ~5 Hz
```

这点很关键：相机、雷达、`joint_states` 往往需要不同发布频率，靠**每个发布节点各自的跳帧数**来调，而**不是去改物理步长**——改步长会动到整个物理仿真。

## 三种建图方式

| 方式 | 怎么建 | 适合 |
|---|---|---|
| **GUI 手搓** | Action Graph 编辑器里搜节点、拖出来、连线 | 学习和调试，直观看到数据流 |
| **菜单快捷方式**（推荐起步）| `Tools > Robotics > ROS 2 OmniGraphs` 下的模板（相机 / RTX Lidar / TF / Joint State），弹窗填几个参数自动建图 | 先跑通，再回头看它生成了什么 |
| **Python 建图** | standalone 脚本里用 `omni.graph.core` 的 `og.Controller.edit` 程序化建节点 + 连线 | 批量、可复现的流水线 |

一个最小的 Python 建图例子（发布 `/clock`）：

```python
import omni.graph.core as og

og.Controller.edit(
    {"graph_path": "/World/ActionGraph", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnTick", "omni.graph.action.OnPlaybackTick"),
            ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
            ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
        ],
        og.Controller.Keys.CONNECT: [
            ("OnTick.outputs:tick", "PublishClock.inputs:execIn"),
            ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
        ],
    },
)
```

**版本提醒**：节点类型 ID 与版本相关。课程锁定的 Isaac Sim 5.1.0 使用 `isaacsim.*` 命名空间（如 `isaacsim.ros2.bridge.ROS2PublishClock`、`isaacsim.core.nodes.IsaacReadSimulationTime`），4.5 之前是 `omni.isaac.*`。拿不准就用 GUI 节点搜索框确认当前版本的确切名字，或直接用菜单快捷方式生成。

## tick 验证

把一张最小 Action Graph 建出来跑一下，就能看到“tick 驱动”不是抽象概念。下面用 `og.Controller.edit` 建了 `OnPlaybackTick → Counter` 外加一个 `IsaacReadSimulationTime`，`timeline.play()` 后推进 30 帧：

```text
图中节点 (prim_path : node_type):
   /ActionGraph/OnTick      : omni.graph.action.OnPlaybackTick
   /ActionGraph/Counter     : omni.graph.action.Counter
   /ActionGraph/ReadSimTime : isaacsim.core.nodes.IsaacReadSimulationTime

Counter.outputs:count = 30   # 推进 30 帧后计到 30，说明每帧 tick 都驱动了下游
```

`Counter.count` 从 0 涨到 **30**，正好等于推进的帧数——这说明 `OnPlaybackTick` 每个仿真帧确实产生了一次 tick，并通过 execution 连线驱动了下游 `Counter`。这就是后面 ROS 2 发布节点“每帧自动发一次”的底层机制：你不用在 Python 里手写循环，图被 tick 推着走。（注意 `OnPlaybackTick` 只有在 `timeline.play()` 之后才会 tick——这也是新手“图建好了却不动”的常见原因。）

## 图与 Python

两者不是二选一，而是各管一摊，且常常共存：

- **纯 Python 顺序脚本**：任务闭环、数据采集、评测、批量实验（前五章一直在做的）。
- **OmniGraph / Action Graph**：ROS 2 收发、需要和渲染 / 物理时钟严格对齐、或要被官方工具 / RViz 直接读取的数据流。

典型用法是：standalone 脚本里启动应用、加载场景、跑主循环，**同时**建一张 Action Graph 负责把传感器数据发到 ROS 2。下一页的 ROS 2 Bridge 就是这么用的。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| Isaac Sim 全靠 Python 主循环 | 发布 / 收发类的事多走 OmniGraph | 接 ROS 2 前先理解 Action Graph |
| 图和脚本只能二选一 | 两者常共存 | 主循环跑任务，图负责发布数据 |
| 发布频率靠改物理步长 | 步长动整个物理 | 改各节点的 `frameSkipCount` |
| 发消息不用时间戳 | 缺 `header.stamp` 下游对不齐 | 接 `Read Simulation Time` 打仿真时间 |
| 一上来就手连几十个节点 | 容易连错、难调 | 先用菜单快捷方式生成，再看图 |
| 节点名照抄老教程 | 4.x 是 `omni.isaac.*` | 5.x 用 `isaacsim.*`，以 GUI 搜索为准 |

## 小结

- OmniGraph 是 Isaac Sim 的可视化数据流系统；Action Graph 是其中执行驱动的一种，把"每帧要做什么"从 Python 主循环挪进一张随物理时钟 tick 的图。
- 三个常驻节点：`On Playback Tick`（节拍）、`Read Simulation Time`（时间戳）、`ROS2 Context`（ROS 2 上下文）。
- 发布频率 = 仿真帧率 ÷ `frameSkipCount`，每个节点各自降频，别去改物理步长。
- 三种建图方式（GUI / 菜单快捷方式 / `og.Controller.edit`）按场景选；图和纯 Python 主循环常常共存。

## 参考资料

- NVIDIA Isaac Sim Documentation, [OmniGraph](https://docs.isaacsim.omniverse.nvidia.com/latest/omnigraph/index.html)
- NVIDIA Isaac Sim Documentation, [ROS 2 Tutorials](https://docs.isaacsim.omniverse.nvidia.com/latest/ros2_tutorials/index.html)
- Omniverse Kit, `omni.graph.core`（`og.Controller` 程序化建图 API）

## 导航

- 返回目录：[仿真接口](../07-ecosystem.md)
- 下一页：[ROS 2 Bridge](02-ros2-bridge.md)
