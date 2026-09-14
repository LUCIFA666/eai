# Replicator 合成数据（SDG）

前几页讲的"数据采集"是**手动**的：自己在循环里取相机帧、存图、记字段，适合任务回合数据（observation / action / state）。但如果你的目标是**训练感知模型**（检测、分割、6D 位姿、深度），需要的是成千上万张**带精确标注、且场景被大量随机化**的图像。手写这套循环会很快失控——这正是 **Replicator** 要解决的事，也是整个任务与数据这一部分的收束。

## 本节目标

本节围绕下面几个问题展开：

1. 手动采集和 Replicator 合成数据各自适合什么场景？
2. Replicator 的「三件套」是什么，一个最小 SDG 脚本怎么写？
3. 它能随机化什么、怎么打语义标签，和 Isaac Lab 的域随机化有何区别？

阅读这一页前，最好已经会手动采集数据，并想批量产**带标注感知数据集**。代码用 `omni.replicator.core`，可在 headless 下批量跑。

## 手动采集与 Replicator

一句话类比：手动采集像你自己举着相机一张张拍、再手写标注；**Replicator 像一条自动贴标签的数据流水线**——布景、灯光、道具位置自动随机化，相机自动连拍，每张图的像素级标注自动生成。

| | 手动采集（本部分前几页）| Replicator（本页）|
|---|---|---|
| 产出 | 任务回合的 obs / action / state | 带标注的感知图像数据集 |
| 标注 | 自己记字段 | 自动产 ground truth（分割 / bbox / 深度…）|
| 随机化 | 自己写、自己记 | 内置 randomizer，按帧扰动并记录 |
| 规模 | 几十～几百条 episode | 成千上万张图 |

Replicator 就是 Isaac Sim 的合成数据生成（Synthetic Data Generation, SDG）框架：**程序化随机化场景 + 自动产出像素级标注 + 批量落盘成数据集**。

## 三件套

理解 Replicator 先抓住三个概念：

```text
render product  =  一台相机 × 分辨率（数据从哪儿来）
annotator       =  标注器（要哪些 ground truth：rgb / 分割 / bbox / 深度 / 法线 …）
writer          =  落盘器（怎么写到磁盘：BasicWriter → DiskBackend …）
```

<figure class="doc-figure">
<p class="doc-figure-title">Replicator 合成数据流水线</p>
<div class="figure-flow">
<div class="figure-node"><strong>render product：</strong>一台相机 × 分辨率，数据从哪儿来</div>
<div class="figure-node"><strong>randomizers：</strong>每帧扰动位姿 / 材质 / 光照 / 相机 / 背景，并记录采样值</div>
<div class="figure-node"><strong>annotators：</strong>rgb / 语义 / 实例 / bbox / 深度 / 法线等 ground truth（依赖语义标签）</div>
<div class="figure-node"><strong>writer → 数据集：</strong>BasicWriter + DiskBackend 落盘成带标注数据集，由 orchestrator 编排</div>
</div>
<p class="doc-figure-subtitle">和 Isaac Lab 在线域随机化不是一回事：前者训练前产感知数据，后者训练中练策略鲁棒性。</p>
</figure>

## 一个最小的 SDG 脚本

```python
import omni.replicator.core as rep

# 1) 相机 + render product
cam = rep.create.camera(position=(2.0, 2.0, 2.0), look_at=(0.0, 0.0, 0.0))
rp = rep.create.render_product(cam, (1024, 768))

# 2) writer：挂上要的标注器，指定输出目录
writer = rep.WriterRegistry.get("BasicWriter")
writer.initialize(
    output_dir="_out_sdg",
    rgb=True,
    semantic_segmentation=True,
    bounding_box_2d_tight=True,
    distance_to_image_plane=True,
)
writer.attach([rp])

# 3) 每帧随机化场景，再渲染一帧
with rep.trigger.on_frame(num_frames=200):
    cubes = rep.get.prims(semantics=[("class", "cube")])
    with cubes:
        rep.modify.pose(
            position=rep.distribution.uniform((-1, -1, 0), (1, 1, 0)),
            rotation=rep.distribution.uniform((0, 0, 0), (0, 0, 360)),
        )
    lights = rep.create.light(light_type="Sphere")
    with lights:
        rep.modify.attribute("intensity", rep.distribution.uniform(500, 3000))

# 4) 跑
rep.orchestrator.run()
```

跑完 `_out_sdg/` 里会按帧落出 `rgb/`、`semantic_segmentation/`、`bounding_box_2d_tight/`、`distance_to_image_plane/` 以及对应标注 json——这就是一份可用于感知训练的带标注数据集。下面是 Franka + 彩色基本体场景的输出示例：

<figure class="doc-figure">
<p class="doc-figure-title">同一帧场景的多种标注（Replicator annotators）</p>
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0.5em 0">
<div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-scene-rgb.png" alt="RGB" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">RGB（<code>rgb</code>）</div></div>
<div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-scene-semantic.png" alt="语义分割" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">语义分割（<code>semantic_segmentation</code>）</div></div>
<div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-scene-instance.png" alt="实例分割" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">实例分割（<code>instance_segmentation</code>）</div></div>
<div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-scene-bbox2d.png" alt="2D 包围盒" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">2D 包围盒（<code>bounding_box_2d_tight</code>）</div></div>
<div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-scene-depth.png" alt="深度" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">深度（<code>distance_to_image_plane</code>）</div></div>
<div><img src="/section/05-simulation-and-task-modeling/assets/isaac-sim-scene-normals.png" alt="法线" style="width:100%;height:auto;border-radius:6px;border:1px solid var(--line)"><div style="text-align:center;color:var(--muted);font-size:0.84rem;margin-top:4px">法线（<code>normals</code>）</div></div>
</div>
<figcaption class="doc-figure-subtitle">一台相机、一帧渲染，annotator 同时产出 RGB 与多种像素级 ground truth。分割与 bbox 依赖语义标签：机器人与每个基本体都打了 class 标签，所以分割图里各自一色、bbox 图里各有一框。深度为 distance_to_image_plane，法线为单位法向量的 RGB 编码。</figcaption>
</figure>

## 语义标签

分割和 bbox 标注**依赖语义标签**。没给物体打 label，`semantic_segmentation` / `bounding_box_*` 会是空的：

```python
from isaacsim.core.utils.semantics import add_update_semantics
add_update_semantics(prim, semantic_label="cube", type_label="class")
```

（GUI 里用 Semantics Schema Editor。）**这是新手做 Replicator 最常踩的坑：图渲染出来了，分割却全黑——多半是忘了打语义标签。**

## 随机化能随机什么

Replicator 的随机化是"程序化场景扰动 + 记录"，常见维度：

```text
位姿      rep.modify.pose(position=..., rotation=..., scale=...)
材质/颜色  rep.randomizer.materials(...) / rep.modify.material(...)
光照      create.light + modify.attribute("intensity"/"color"/...)
相机      随机相机位姿、look_at、焦距
纹理/背景  随机贴图、HDRI 背景、干扰物体
```

触发器决定每次随机化后渲染多少帧：`rep.trigger.on_frame(num_frames=N, interval=k)`。若只想在自己的循环里实时拿某种 ground truth（不落盘），用 `rep.AnnotatorRegistry.get_annotator(...)` 挂到 render product，`step` 后 `get_data()`。

## 和 Isaac Lab 域随机化的区别

两者都"随机化"，但目的不同，别混：

| | Replicator（本页）| Isaac Lab 在线域随机化 |
|---|---|---|
| 产出 | 离线**带标注图像数据集** | 训练时**在线**扰动环境 |
| 面向 | 感知模型（检测 / 分割 / 位姿 / 深度）| RL 策略的鲁棒性 |
| 随机什么 | 外观、布局、光照、相机、纹理 | 物理参数、初始状态、外力、观测噪声 |
| 何时跑 | 训练**前**批量产数据 | 训练**中**每次 reset / interval |

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 手动采集就够了 | 训感知要海量带标注随机图 | 用 Replicator 批量产 SDG |
| 渲染出图分割就有 | 分割 / bbox 依赖语义标签 | 先 `add_update_semantics` 打 label |
| 数据越多越好 | 随机维度太少会同质 | 多加光照 / 材质 / 相机 / 干扰物 |
| 自己插 step 取标注 | 标注和渲染可能错位 | 用 `on_frame` + `orchestrator` 编排 |
| Replicator = Isaac Lab DR | 一个产感知数据、一个练策略 | 训练前 SDG vs 训练中在线 DR |
| 一台机随便堆批量 | 单进程启动成本高 | 按 headless 批量页的工程建议组织批量与目录 |

## 小结

- Replicator = 程序化随机化场景 + annotator + writer，把"仿真"自动变成"可训练的带标注数据集"；手动采集管任务数据，它管感知数据。
- 三件套：render product（数据来源）、annotator（要哪些 ground truth）、writer（怎么落盘），由 orchestrator 编排。
- 分割 / bbox 依赖语义标签——忘了 `add_update_semantics` 就会全黑，这是头号坑。
- 它和 Isaac Lab 在线域随机化是两回事：前者训练前产感知数据，后者训练中练策略鲁棒性。

至此，Isaac Sim 主线已经走完：从"认识 Isaac Sim"、"场景构建与坐标约定"、"机器人资产与物理配置"、"控制"、"观测与传感器"，到"任务、数据采集与合成数据"。你已经具备从零搭场景、导入机器人资产、控制、感知、采集、复现和批量产感知数据的完整链路。第七组是可选仿真接口：需要 OmniGraph 或 ROS 2 Bridge 时再读；下一步若做 RL / 并行训练，转入 Isaac Lab。

## 参考资料

- NVIDIA Isaac Sim Documentation, [Synthetic Data Generation / Replicator](https://docs.isaacsim.omniverse.nvidia.com/latest/replicator_tutorials/index.html)
- NVIDIA Isaac Sim Documentation, [Scene Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/latest/replicator_tutorials/tutorial_replicator_scene_based_sdg.html)
- Omniverse Replicator, `omni.replicator.core` API（`rep.create` / `rep.modify` / `rep.randomizer` / `WriterRegistry` / `AnnotatorRegistry`）

## 导航

- 返回目录：[任务、数据采集与合成数据](../06-task-and-data.md)
- 上一页：[headless 批量与可复现](04-headless-and-repro.md)
- 下一页：[仿真接口](../07-ecosystem.md)
- 返回上级：[Isaac Sim](../../03-isaac-sim.md)
