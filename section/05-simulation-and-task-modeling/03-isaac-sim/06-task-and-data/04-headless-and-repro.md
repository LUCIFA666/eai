# headless 批量与可复现

前面几页你已经能定义任务、采集结构化数据，并把 episode 按稳定格式落盘了。这一页把任务放回**工程环境**：在没有显示器的服务器上批量跑、用随机种子保证可复现，并厘清 Isaac Sim 与 Isaac Lab 的边界。这是从"一次演示"走向"一批可信实验"的关键一步。

## 本节目标

本节围绕下面几个问题展开：

1. headless 模式怎么开，导入顺序为什么有讲究？
2. 要让一次运行可复现，需要固定哪些东西、怎么验证种子真的固定了？
3. 在可复现这件事上，Isaac Sim 和 Isaac Lab 的分工是什么？

阅读这一页前，你可能已经准备把任务搬到服务器、批量产数据或做评测。你不需要现在就搭大规模并发系统，但应该从第一天就知道"可复现"这件事要固定哪些东西。

## headless

服务器上做实验，Isaac Sim 通常不开图形界面，而是以 **headless（无界面）** 批量运行。headless 的目标不是"看不见"，而是把仿真变成**可调度的生产任务**。开关其实只有一个（第一组已见过）：

```python
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})   # 服务器 / 无显示器置 True
# —— 之后再 import 依赖 Omniverse 运行时的模块 ——
```

但"能 headless 启动"和"能稳定批量跑"是两回事。批量时要特别注意：

| 注意点 | 为什么 |
|---|---|
| 单进程启动成本高 | Isaac Sim 不是轻量脚本，别像小脚本那样频繁起停；一个进程内多跑几条 episode |
| 资源要算账 | 渲染 / 物理 / 写盘都吃 GPU·CPU·磁盘，并发数受显存和 IO 约束 |
| 输出目录隔离 | 每个任务独立目录，避免 episode 编号、日志、临时文件互相覆盖 |
| 长流程可恢复 | 至少能判断一条 episode 是否完整写完，断了能续 |
| 失败也留日志 | 否则分不清是策略失败、场景错误、资源不足还是脚本 bug |

新手不必一上来追求大规模并发：**先让单条 episode 的闭环和记录格式稳定，再考虑多进程、多 GPU、队列和断点续跑。**

## 可复现

"可复现"的判据很硬：**同一份配置 + 同一个 seed，再跑一遍，关键字段（关节轨迹 / success 标记）应当一致。** 要做到这点，得把实验的"变量"从代码里拎出来、钉死：

```python
import numpy as np, torch, random

def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)

cfg = load_yaml("exp.yaml")        # 机器人 / 场景 / 相机 / episode 数 / seed 全在这
set_seed(cfg["seed"])
for ep in range(cfg["num_episodes"]):
    set_seed(cfg["seed"] + ep)     # 每条 episode 一个确定派生 seed
    result = run_episode(world, task)
    save_episode(result, out_dir=f"{cfg['out']}/episode_{ep:06d}")
```

把这件事放进一个更大的图景里看——从"能跑"到"可复现实验"，其实有五个递进的层次：

<figure class="doc-figure">
<p class="doc-figure-title">从"能跑"到"可复现实验"的五个层次</p>
<div class="figure-flow">
<div class="figure-node"><strong>1 能显示：</strong>场景、机器人、物体能正确加载和渲染</div>
<div class="figure-node"><strong>2 能控制：</strong>机器人能按目标稳定运动、抓取、放置</div>
<div class="figure-node"><strong>3 能采集：</strong>观测 / 动作 / 状态 / 阶段按 step_index 结构化记录</div>
<div class="figure-node"><strong>4 能复现：</strong>配置外置、随机种子与资产版本可复跑同一回合</div>
<div class="figure-node"><strong>5 能解释失败：</strong>失败定位到阶段，记录原因与可回放证据</div>
</div>
<p class="doc-figure-subtitle">每一层都建立在上一层之上；停在第 1 层只是演示，不是可用的具身智能实验。</p>
</figure>

落到脚本上，可复现脚本通常会坚持几条习惯：**入口稳定**（先 `SimulationApp` 再 import 运行时模块）、**配置外置**（机器人 / 路径 / 相机 / seed / 输出目录进 YAML，代码只负责执行规律）、**任务逻辑与控制逻辑分离**（任务管场景 / 观测 / reset / 判定，控制管出动作）、**阶段切换隔离状态**（进新阶段前显式清控制器残留、等物理稳定）。这些前几页都铺垫过，这里把它们收进"工程纪律"。

## 固定种子的验证

用前面的最小 episode 做一次可复现性验证：同一个 seed 跑两遍，再换一个 seed 跑一遍。

```text
seed=42 run#1 final_pos: [0.1323, -0.0342, 0.05]  success: False
seed=42 run#2 final_pos: [0.1323, -0.0342, 0.05]  success: False
   => 同一环境下关键字段一致 REPRODUCIBLE: True
seed=7  start: [0.063, 0.199, 1.0]  final_pos: [0.0579, 0.195, 0.05]  success: False
   => 换种子初始位置/结果不同；种子已记录，随时可复现
```

这里的重点不是承诺任何机器、任何版本都能逐位相同，而是建立一个可执行的验收办法：在同一代码、资产、驱动和配置下，同一个 seed 复跑时，关键字段应保持一致或落入你预先写清楚的容差；换成 `seed=7`，初始位置随之改变、结果也不同，但因为种子和实际采样值被记录下来，这条不同的轨迹同样能重新追溯。**能随机、但每次随机都可追溯**，正是上面强调的原则。

## Isaac Sim 与 Isaac Lab

两者常被混为一谈，其实分工清楚：

| | Isaac Sim | Isaac Lab |
|---|---|---|
| 定位 | 底层仿真与机器人应用平台 | 建在 Isaac Sim 之上的机器人**学习**框架 |
| 提供 | 场景 / 物理 / 传感器 / 渲染 / USD / Replicator / 可选 ROS 2 Bridge | 并行环境、任务封装、RL 训练工作流 |
| 你怎么用 | 直接写 Python 独立脚本 | 用它的任务抽象做向量化训练 |
| 适合 | 理解场景 / 传感器 / 数据采集 / 自定义任务流水线 | 快速训练 RL policy、大规模并行 |

一句话：**Sim 负责"单进程把一件事读懂"，Lab 负责"向量化大规模训练"。** 本单元一直讲 Sim 独立脚本，正是为了让你看清 Isaac Lab 这类上层框架底下到底发生了什么。读完任务与数据这一部分，按目标转场：

| 你的目标 | 下一步去哪 |
|---|---|
| 批量产带标注感知数据 | [下一页：Replicator 合成数据（SDG）](05-replicator-sdg.md) |
| RL / 并行训练 | Isaac Lab |
| 大规模示教采集 | 课程后续章节的数据采集部分 |
| 接 RViz / 外部 ROS 2 节点 | [仿真接口](../07-ecosystem.md) |

## 调试地图

仿真出问题时，最怕一上来同时改资产、控制器、相机、摩擦和任务逻辑。更好的办法是**先判断问题属于哪一层，再只改那一层**：

| 现象 | 更可能在哪一层 | 第一轮检查 |
|---|---|---|
| 程序启动就报错 | 运行时顺序 | `SimulationApp` 是否先启动，依赖 Kit 的模块是否过早 import |
| 对象找不到 | USD / prim path | stage 里是否有对应 prim，路径大小写 / 层级是否一致 |
| 看得见碰不到 | 资产物理 | collider 是否存在、绑定对象，rigid body 是否启用 |
| 全白 / 纹理丢失 | reference / 材质 | `Looks`、纹理路径、外部 layer 是否随资产加载 |
| 物体尺寸离谱 | 单位 / scale | 是否米制，scale 是否被重复应用 |
| reset 就抖 / 飞 | 物理 / 碰撞 | collision 是否交叠，质量惯量是否异常 |
| 末端目标方向不对 | frame / IK | world / base / ee frame 是否一致，四元数顺序对不对 |
| 目标合理但跟不上 | drive / 控制 | stiffness / damping / max force / 控制模式是否合理 |
| 相机黑屏 / 看空 | sensor / render | camera 朝向、clipping、`initialize()`、`step(render=True)` |
| 图像和动作对不上 | 数据时间线 | `obs_t + action_t → obs_{t+1}` 约定，缓存是否刷新 |
| 成功率高但视频不对 | 任务评测 | success 条件是否太松，是否记录 object pose / 阶段 |
| 换机 / 换目录就坏 | 工程复现 | USD 依赖、配置路径、seed、资产版本、字段约定是否固定 |

原则只有一句：**先定位层级，再修具体参数。** "机器人没抓住杯子"可能来自航点偏、IK 跳、drive 太软、指尖没 collider、摩擦太低、相机看不到、判定太松——分层之后，调试才不会变成靠感觉乱试。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| headless 就是"看不见" | 它是把仿真变成可调度的生产任务 | `headless=True` 批量产数据，按需另存视频 |
| Isaac Sim 像小脚本随起随停 | 单进程启动成本高 | 一个进程多跑几条 episode，规划好资源 |
| 固定 seed 就一定可复现 | 代码 / 资产 / 驱动 / 采样顺序变了就可能不一致 | 同时固定配置、资产版本，并存实际采样值和容差 |
| Isaac Sim 和 Isaac Lab 差不多 | 一个是平台、一个是学习框架 | Sim 读懂底层，Lab 做向量化训练 |
| 出问题就全方位一起改 | 改动一多就无法归因 | 先用调试地图定位层级，再改那一层 |
| 失败 episode 没用，删掉 | 失败最能暴露薄弱环节 | 失败也留日志和可回放证据 |

## 小结

- headless 的意义是把仿真变成可调度的生产任务；批量跑要注意启动成本、资源账、目录隔离、可恢复、失败留日志。
- 可复现 = 同配置 + 同 seed 复跑关键字段一致：配置外置、固定资产版本、记录采样值，五层能力模型逐层往上走。
- Isaac Sim 负责单进程读懂底层，Isaac Lab 负责向量化训练；按目标（RL / 采集 / 资产 / 外部接口）决定转场。
- 调试先定位层级再改参数；下一页进入 Replicator，把仿真场景批量变成带标注感知数据。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Standalone Examples Reference List](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/standalone_examples_list.html)
- Isaac Lab Documentation, [Overview](https://isaac-sim.github.io/IsaacLab/main/index.html)

## 导航

- 返回目录：[任务、数据采集与合成数据](../06-task-and-data.md)
- 上一页：[数据存放格式](03-data-storage-format.md)
- 下一页：[Replicator 合成数据（SDG）](05-replicator-sdg.md)
