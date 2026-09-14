# Isaac Sim 是什么

我们先花一点时间搞清楚 Isaac Sim 到底是什么、它适合解决什么问题，以及它为什么不像 MuJoCo 那样只是 `import` 一个库就能开始 `step`。这件事先分清，后面遇到 USD、Omniverse、RTX、扩展、ROS 2 Bridge 这些名词时，就不会觉得它们是凭空冒出来的复杂度。

## 本节目标

本节围绕下面几个问题展开：

1. Isaac Sim 为什么更像机器人仿真平台，而不是单独的物理引擎？
2. 它和 MuJoCo、Isaac Lab 的职责边界在哪里？
3. USD、PhysX、RTX、传感器和 ROS 2 各自处在哪一层？

阅读本页需要基础 Python 直觉，但不要求你已经懂 USD、PhysX 或 Omniverse。你只需要先记住：Isaac Sim 是一个更大的机器人仿真平台，物理引擎只是其中一层。本页不写代码，只建立定位；下一页再亲手跑通第一个最小仿真。

## 它不只是物理引擎，而是一个仿真平台

先记住一句话：**Isaac Sim 不只是物理引擎，而是一个机器人仿真平台**。

物理引擎（像 MuJoCo、PhysX、Bullet）主要负责动力学求解：给定模型和当前状态，算出下一时刻的运动、接触和约束。Isaac Sim 的范围更大：它建立在 NVIDIA **Omniverse** 之上，把场景组织、物理、渲染、传感器和机器人生态接口组合成一个可用 Python 驱动的仿真平台。

- **USD**：描述和组织场景（地面、灯光、机器人、物体都在一个 USD 舞台里）；
- **PhysX**：负责刚体、关节、接触和约束求解的物理层（这一层才和 MuJoCo 更接近）；
- **RTX**：光线追踪渲染，相机的 RGB、深度、分割图都从这里来；
- **Omniverse Kit + 扩展**：把 ROS 2 桥接、合成数据、各类传感器当成可插拔的扩展挂上来。

一个类比：如果说 MuJoCo 像一台可以直接调用的**物理计算器**，Isaac Sim 更像一个带传感器的**机器人实验场**：有舞台（USD）、有物理规则（PhysX）、有打光和相机（RTX），也有接 ROS 2、造合成数据、挂更多传感器的扩展。用 MuJoCo 往往是 `import` 一个库就开始算；用 Isaac Sim 要先启动这个实验场，再往里面搭场景和机器人。

| 对比 | MuJoCo / PyBullet | Isaac Sim |
|---|---|---|
| 本质 | 一个物理引擎库 | 一个仿真平台（物理只是其中一层）|
| 场景怎么来 | 一个模型文件（MJCF / URDF）| USD 舞台，由多个 Prim 引用 / 分层拼出 |
| 渲染 | 简单 OpenGL 预览 | RTX 光追，更接近相机 / 深度 / 分割的传感器输出 |
| 怎么启动 | `import mujoco` 直接用 | 先创建 `SimulationApp` 启动 Kit，再 import |
| 最擅长 | 轻量、快速做算法原型 | 高保真传感器、复杂场景、合成数据、接 ROS 2 |

这张表里最该记住的是最后两行：**Isaac Sim 的代价是更重的启动和场景组织，换来的是高保真渲染、传感器输出，以及接入机器人软件生态的能力。**

## 它由四层拼成，你迟早都会碰到

把上面四样东西按学习顺序理一遍，正好就是本单元后面几章的主线：

<figure class="doc-figure">
<p class="doc-figure-title">Isaac Sim 的四层：从场景到生态</p>
<div class="figure-flow">
<div class="figure-node">USD 场景：Stage 与 Prim，描述世界里有什么（→ 场景构建）</div>
<div class="figure-node">PhysX 物理：碰撞、质量、关节、接触，让世界可信（→ 机器人资产与物理配置）</div>
<div class="figure-node">RTX 渲染：相机的 RGB / 深度 / 分割（→ 观测与传感器）</div>
<div class="figure-node">Omniverse Kit + 扩展：ROS 2、合成数据、更多传感器（→ 仿真接口）</div>
</div>
<p class="doc-figure-subtitle">本单元就沿着这四层往前走；现在只要知道它们各管一段即可。</p>
</figure>

你现在不需要理解每一层的细节，只要建立一个预期：**Isaac Sim 的能力是组合出来的，遇到问题先判断是哪一层出了问题**——是场景没搭对（USD），还是物理没配对（PhysX），还是相机没读对（RTX）。

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-scene-rgb.png" alt="Isaac Sim RTX 渲染的多物体场景" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">Isaac Sim（RTX）渲染的一个多物体场景。同一套渲染还能同时给出深度图、语义分割等（见 <a href="../05-observation.md">观测与传感器</a>）——这种高保真是 MuJoCo 的简单预览给不到的。</figcaption>
</figure>

## 三种用法

同样一套 Isaac Sim，有三种用法：

| 用法 | 怎么用 | 适合 |
|---|---|---|
| Python 独立脚本（standalone）| 用自带的 `python.sh` 跑一个 `.py`，代码里创建 `SimulationApp` | 自动化、批量出数据、可复现实验（**本单元默认**）|
| GUI 交互 | 打开 Isaac Sim 窗口，手动拖拽、点扩展 | 第一次探索、调试场景、手动核对 |
| 作为 Isaac Lab 的后端 | 你不直接碰 Isaac Sim，由 Isaac Lab 调用它 | 大规模并行 RL 训练（见 [Isaac Lab](../../04-isaac-lab.md)）|

本单元默认走 **standalone Python 脚本**：把 Isaac Sim 当成一个"可以被代码驱动的仿真世界"。这也是最适合学习的方式——每一步都能写进脚本、跑出可复现的结果，而不是靠点鼠标记住一串操作。

## 它在具身智能链路里站哪

把链路从上到下捋一遍：

<figure class="doc-figure">
<p class="doc-figure-title">Isaac Sim 在链路里的位置</p>
<div class="figure-flow">
<div class="figure-node">你的脚本 / 上层框架：搭场景、发动作、读观测、存数据</div>
<div class="figure-node">Isaac Sim：USD 场景 + PhysX 物理 + RTX 渲染 + 传感器输出</div>
<div class="figure-node">GPU：并行物理与光追渲染</div>
</div>
<p class="doc-figure-subtitle">要做大规模 RL 训练时，Isaac Lab 会建在 Isaac Sim 之上，替你把环境批量化。</p>
</figure>

一句话分工：**Isaac Sim 负责搭出可看、可碰撞、可采集观测的仿真世界；Isaac Lab 负责把这个世界批量化成可训练的 RL 环境。** 如果你的目标是检查资产、相机和物理、采集数据，Isaac Sim 本身就够了；如果目标是大规模训练策略，读完本单元再去 [Isaac Lab](../../04-isaac-lab.md)。

## 适合做什么、不太适合做什么

**Isaac Sim 比较适合：**

- 需要高保真视觉传感的任务，比如 RGB、深度、语义分割、实例分割、RTX Lidar。
- 需要检查机器人资产、碰撞体、质量、关节 Drive、传感器安装位置的工程流程。
- 需要和 ROS 2、OmniGraph、Replicator 等机器人软件生态打通的仿真。
- 需要在服务器上 headless 批量渲染、采集数据、生成带标注样本的任务。

**Isaac Sim 不太适合作为第一选择：**

- 只想快速验证一个 RL 算法，不依赖高保真视觉和复杂传感器。
- 机器配置较弱，只能接受秒级启动和极轻量依赖。
- 主要目标是大规模并行训练策略，而不是检查单个场景、资产和传感器；这种情况通常应该直接使用 [Isaac Lab](../../04-isaac-lab.md)。

换句话说：如果你关心的是**物理和控制本身**，MuJoCo 可能更轻；如果你关心的是**世界长什么样、相机看到什么、传感器怎么接、数据怎么批量生成**，Isaac Sim 的平台能力才真正用得上。

## 初学者常见误解

| 误解 | 实际 |
|---|---|
| Isaac Sim 就是个物理引擎 | 它是仿真平台，物理只是 PhysX 那一层 |
| 像 MuJoCo 那样 `import` 就能用 | 必须先创建 `SimulationApp` 启动 Kit，才能 import `omni.*` / `isaacsim.*`；顺序写反就报错（见 [第一次仿真](02-first-simulation.md) 和 [三个理解视角](03-three-mental-models.md)）|
| 没有显示器（服务器）就跑不了 | 支持 headless，无界面照样推进物理、出图 |
| 机器人导进来就能用 | 导入只给了外形，碰撞 / 质量 / Drive 没配好会穿地板或乱飞（见 [机器人资产与物理配置](../03-robot-and-physics.md)）|

这几条后面都会专门展开；现在先有个印象，能少踩很多坑。

## 小结

- Isaac Sim 不只是物理引擎，而是建立在 Omniverse 之上的仿真**平台**，由 USD（场景）、PhysX（物理）、RTX（渲染）、Kit 扩展（生态）四层组成。
- 和 MuJoCo 这类"库 + 单文件"相比，它启动更重、场景组织更复杂，但换来高保真传感器、复杂场景与接入机器人生态的能力。
- 三种用法里，本单元默认用 standalone Python 脚本，把它当"可被代码驱动的仿真世界"。
- 是否选择 Isaac Sim，关键看任务是否需要高保真视觉、复杂传感器、ROS 2 / Replicator 生态或资产级调试。
- 它负责搭出可看、可碰撞、可采集观测的仿真世界；大规模 RL 训练交给建在它之上的 Isaac Lab。

## 参考资料

- NVIDIA Isaac Sim Documentation, Workflows. https://docs.isaacsim.omniverse.nvidia.com/latest/introduction/workflows.html
- NVIDIA Isaac Sim Documentation, Python Scripting and Tutorials. https://docs.isaacsim.omniverse.nvidia.com/latest/python_scripting/index.html
- NVIDIA Omniverse Documentation（USD / Kit）. https://docs.omniverse.nvidia.com/
- NVIDIA PhysX SDK. https://developer.nvidia.com/physx-sdk

## 导航

- 返回目录：[一、认识 Isaac Sim](../01-getting-started.md)
- 下一页：[第一次仿真](02-first-simulation.md)
