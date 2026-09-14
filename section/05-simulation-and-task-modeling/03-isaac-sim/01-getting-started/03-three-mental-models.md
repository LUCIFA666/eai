# 三个理解视角

你已经用前一节的脚本让方块掉了下来，但对“为什么 `SimulationApp` 要第一行、为什么物体要写 `prim_path`、为什么 `reset` 之后才有物理”可能还只是照抄。这一页先给出贯穿全单元的主线图，再把这三处“反直觉”变成可排错的直觉。

## 本节目标

本节围绕下面几个问题展开：


1. 这些模型分别对应代码里的哪些对象、配置或日志？
2. 初学者最容易把哪些概念混在一起？
3. 读后续代码时，应该按什么路线定位问题？

MuJoCo 里你几乎不需要单独建立这些概念：`mj_step` 就是步进，`data.qpos` 就是状态，所见即所得。Isaac Sim 的门槛在于它有几处不同：不先启动不能用、物体要挂到舞台树上、不初始化就没有物理。但这几处都长在同一条主线上。先看清主线，再看这三处，入门阶段的大部分报错就能自己定位。

## 运转主线

这一条线值得最先记住：**描述场景（USD）→ 初始化仿真（reset）→ 控制循环（发送动作 → step → 读取状态）**。上一页的脚本和后面所有页面，都落在这条线的某一段上。

<figure class="doc-figure figure-loop" aria-label="Isaac Sim 运转主线主图">
  <p class="doc-figure-title">Isaac Sim 主线：描述场景 → 初始化仿真 → 循环推进</p>
  <p class="doc-figure-subtitle">前两步在开头各做一次，后三步在循环里反复跑。</p>
  <div class="figure-pipeline">
    <div class="figure-node tone-green">
      <strong>① 描述场景（USD Stage / Prim）</strong>
      <span>用 USD 把场景组织成一棵树：地面、灯光、方块、机器人都是挂在 <code>/World</code> 下的 Prim。这是静态描述，此刻还没有进入物理仿真。</span>
    </div>
    <div class="figure-node tone-blue">
      <strong>② 初始化仿真（SimulationApp 启动 → world.reset 初始化物理）</strong>
      <span>SimulationApp 启动 Kit 运行时；调用 <code>reset</code> 后，PhysX 才把静态场景实例化成可仿真的对象（刚体、关节、自由度等）。在这之前读状态都拿不到值。</span>
    </div>
    <div class="figure-node tone-gold">
      <strong>③ 发送动作</strong>
      <span>给关节目标 / 力或施加动作（<code>set_joint_position_targets</code> / <code>apply_action</code>）。本页的自由落体方块没有控制，这一步先空着，到后面的控制部分驱动机器人才用上。</span>
    </div>
    <div class="figure-node tone-rose">
      <strong>④ step 推进一帧</strong>
      <span><code>world.step(render=True)</code>：按物理规律往前算一个时间步，顺带渲染。不 step 就永远冻结。</span>
    </div>
    <div class="figure-node tone-gold">
      <strong>⑤ 读取状态</strong>
      <span>取位姿 / 速度 / 传感器（<code>get_world_pose</code>、<code>get_joint_positions</code>…），喂给下一次决策。</span>
    </div>
  </div>
  <div class="figure-note">核心循环：③发送动作 → ④step → ⑤读取状态 → 重复；前两步（描述场景、初始化仿真）只在开头各做一次。这条线和 MuJoCo 同构：<strong>USD ≈ MJCF</strong>（静态描述）、<strong>reset 后的运行时对象 ≈ mjData</strong>（动态状态），读过 MuJoCo 篇的话可以直接迁移过来。</div>
</figure>

这条主线上有三处最“反直觉”、也最容易出错的地方，正好对应下面三个理解视角：第一处在第 ② 步（得先启动），第二处在第 ① 步（场景是 Prim 树），第三处横跨 ①②（配了物理，且 `reset` 之后才算数）。

## 先启动

**现象**：02 脚本第一行一定是 `SimulationApp({...})`，而且 `from isaacsim.core.api import World` 必须写在它后面。顺序反过来，import 直接失败。

**类比**：MuJoCo 是一个**库**，`import` 进来就能用。Isaac Sim 是一个**平台**：`SimulationApp` 负责启动 Kit 运行时（USD、PhysX、RTX 这一整套），`isaacsim.*` 这些模块要等运行时起来之后才会被注册进来。运行时还没启动就 import，自然找不到模块。

**常见报错 / 反例**：

- 把 `import isaacsim.core.api` 写到 `SimulationApp(...)` 前面 → `ModuleNotFoundError` 或直接崩。
- 用没有安装 Isaac Sim 的 `python` 跑 → 即使顺序对也起不来；pip 安装用当前环境的 `python`，预编译包用它自带的 `python.sh`。

锚点：**先启动，再 import**。`SimulationApp` 永远是第一行。

## Prim 路径

**现象**：02 里建方块时写了 `prim_path='/World/Cube'`。这个看着像文件路径的字符串，就是物体在场景里的“地址”。

**类比**：Isaac Sim 的世界是一个 **USD 舞台（Stage）**，舞台上的一切——地面、灯光、方块、机器人——都是挂在一棵树上的节点，叫 **Prim**，用 `/World/Cube` 这样的路径寻址，跟文件系统的目录树一模一样。MuJoCo 的 MJCF 是“一个文件描述整个场景”；USD 是“一棵可以分层、可以互相引用的场景树”，所以后面加载机器人时，是把一份 USD “引用”到某个 `prim_path` 下，而不是把 XML 拼进来。

**常见报错 / 反例**：

- 两个物体用了同一个 `prim_path` → 后者覆盖前者，或拿到的句柄不是你以为的那个。
- 路径写错（如大小写不符、漏了 `/World`）→ 后续按路径查找时找不到这个 Prim。

锚点：**一切皆 Prim，靠路径寻址**。`prim_path` 是物体在舞台树上的唯一地址。

## 物理初始化

**现象**：02 里方块会掉，是因为用的是 `DynamicCuboid`（带刚体 + 碰撞）；而且 `world.reset()` 之前，`get_world_pose()` / `get_linear_velocity()` 取不到有效值。

**类比**：在舞台上摆一个物体，默认它只是个“道具外形”。要让它受重力、会碰撞，得给它配上物理属性（刚体、碰撞体、质量）；`DynamicCuboid` 就是替你配好了的，`VisualCuboid` 则只有外形、不受力。而 `world.reset()` 的作用是初始化物理：调用之后物理引擎才把场景准备好，在那之前物体状态都还没就绪。

**常见报错 / 反例**：

- 用 `VisualCuboid` 期待它下落 → 它没有刚体，永远不动。
- 在 `world.reset()` 之前调 `get_*` 读状态 → 取不到值 / 报错。
- 机器人导进来直接乱飞或穿地板 → 碰撞 / 质量 / Drive 没配好（见 [机器人资产与物理配置](../03-robot-and-physics.md)）。

下面这张图展示了同一个场景里 `DynamicCuboid` 和 `VisualCuboid` 的差异。`reset` 后步进一段时间，动态方块落到地面，视觉方块仍然悬空：

<figure class="doc-figure">
<img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-dynamic-vs-visual.png" alt="DynamicCuboid 落地、VisualCuboid 悬空的对比" style="max-width:100%;height:auto;display:block;margin:0.5em 0">
<figcaption class="doc-figure-subtitle">Isaac Sim headless 运行效果：右边蓝色 <code>DynamicCuboid</code> 受重力落到地面（终端读数 z=0.250），左边橙色 <code>VisualCuboid</code> 只有外形、不参与物理，原地悬在空中（z=1.000）。</figcaption>
</figure>

锚点：**没配物理 = 只是道具；没 reset = 物理还没初始化**。

## 三个模型怎么落到你刚跑的脚本上

把 02 的 `hello_isaac.py` 拆开，每一行背后都站着一个理解视角——记住“写错时的信号”，报错时就能反查是哪个模型出了问题：

| 脚本里的这一行 | 背后的理解视角 | 写错时的信号 |
|---|---|---|
| `SimulationApp({...})` 先创建 | ① 平台要先启动 | import 崩 / 进程起不来 |
| `from isaacsim.core.api import World`（运行时启动后）| ① 启动顺序敏感 | `ModuleNotFoundError` |
| `DynamicCuboid(prim_path='/World/Cube', ...)` | ② USD 舞台 + Prim 寻址 | 找不到 / 覆盖 Prim |
| 用 `DynamicCuboid` 而非 `VisualCuboid` | ③ 物理要配 | 物体不下落 |
| `world.reset()` | ③ reset 才初始化物理 | `get_*` 取不到值 |
| `world.step(render=True)` 循环 | ①③ 平台推进物理 + 渲染 | 不 step = 画面冻结 |

## 这张主图后面怎么用

后面每一章，都可以理解成在给这条主线补某一段细节。读到不确定某页在讲哪一步时，回这张表对一下：

| 页面 | 对应主线的哪一段 | 主要补什么 |
|---|---|---|
| 场景构建（第二部分） | ① 描述场景（USD） | Stage / Prim / 引用，搭地面光照物体，坐标与单位 |
| 机器人与物理（第三部分） | ① 描述场景 + ② 初始化仿真 | 导入机器人、articulation、碰撞 / 质量 / Drive 审计 |
| 控制（第四部分） | ③ 发送动作 + ④ step | 关节控制、运动生成、把目标变成 articulation action |
| 观测（第五部分） | ⑤ 读取状态 | 相机与传感器、状态读取、把观测和动作对齐成稳定闭环 |
| 任务与数据（第六部分） | 整条循环外面包一层 | episode / 成功判定、批量采数、headless 可复现 |
| 生态（第七部分） | 主线外围接生态 | OmniGraph、ROS2 桥、Lidar / IMU、Replicator 合成数据 |

## 小结

- 一条主线串起全单元：**描述场景（USD）→ 初始化仿真（reset）→ 控制循环（发送动作 → step → 读取状态）**；后面每章都在补这条线的某一段。
- 三个反直觉点，对应入门阶段的大部分坑：**它是平台（先启动）、场景是 USD 舞台（Prim 寻址）、像不像真看物理配置（`reset` 初始化物理）**。
- 这三条就是 02 脚本“为什么这么写”的答案；遇到报错，先问“是哪个模型出了问题”。
- 跨平台锚点记牢：USD ≈ MJCF（静态），`reset` 后的运行时对象 ≈ mjData（动态）。

## 动手练习

1. 不看本页，用自己的话把主线五步（描述场景 → 初始化仿真 → 发送动作 → step → 读取状态）默写一遍，再对照主图看漏了哪步。
2. 把 02 的 `hello_isaac.py` 里 `world.reset()` 注释掉再跑，观察 `get_world_pose()` 的异常或空值——这对应主线哪一步、三个理解视角里的哪一个？
3. 把这条主线和 MuJoCo 的 `MJCF → mjModel/mjData → mj_step` 对齐：哪一步对应“编译”、哪一步对应“建 mjData”、哪一步对应“mj_step”？

## 参考资料

- NVIDIA Isaac Sim Documentation, Workflows. https://docs.isaacsim.omniverse.nvidia.com/latest/introduction/workflows.html
- NVIDIA Omniverse Documentation（USD：Stage 与 Prim）. https://docs.omniverse.nvidia.com/
- NVIDIA PhysX SDK（刚体 / 碰撞 / 关节）. https://developer.nvidia.com/physx-sdk

## 导航

- 返回目录：[一、认识 Isaac Sim](../01-getting-started.md)
- 上一页：[第一次仿真：运行与验证](02-first-simulation.md)
- 下一页：[安装与版本对照](04-install-and-versions.md)
