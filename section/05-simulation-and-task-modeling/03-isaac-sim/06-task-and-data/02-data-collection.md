# 数据采集、回放与质检

上一页你能把一段仿真定义成有判定的 episode 了。这一页解决下一个问题：**怎么把这些 episode 存成"别人敢用、半年后自己还看得懂"的数据**。具身智能数据最怕的不是数量少，而是看起来很多，里面却混着黑图、旧帧、动作错位、字段缺失、阶段混乱和无法复现的失败。

## 本节目标

本节围绕下面几个问题展开：

1. 为什么说采集出来的数据集不是「一个视频文件夹」？
2. `step_index`、字段约定和 metadata 为什么一旦被下游用上就不能随便改？
3. 采集完怎么做质检，及时挡住黑图、错位和缺字段？

阅读这一页前，最好已经能跑通一个任务，并准备开始攒数据集。这一页基本不写仿真代码，重点是**数据的语义约定**——字段、对齐、回放和质检——这是从"能跑演示"迈向"能产数据"的关键一步。

## 数据集不是一个视频文件夹

新手常先存一个 `.mp4`，觉得"我已经采集到数据了"。视频确实有用——适合快速浏览和展示——但它通常不够：模型训练和任务分析需要知道**每一帧**对应的动作、关节状态、物体位姿、相机名、任务阶段和成功标签。

更准确的理解是：**视频只是 episode 的一个视图，episode 本身应该是结构化数据。**

<figure class="doc-figure">
<p class="doc-figure-title">一条 episode = 视频 + 一组按 step_index 对齐的结构化字段</p>
<div class="figure-flow">
<div class="figure-node"><strong>video.mp4：</strong>给人看的视图，快速浏览，但不够训练</div>
<div class="figure-node"><strong>观测 / 动作 / 状态：</strong>camera_rgb、robot_state、actions、object_state，按 step_index 对齐</div>
<div class="figure-node"><strong>阶段 / 成功：</strong>phase、success、failure_reason——让数据有步骤语义、标签可信</div>
<div class="figure-node"><strong>metadata：</strong>任务、机器人、相机、随机种子、资产版本——复现的入口</div>
</div>
<p class="doc-figure-subtitle">关键不是用 HDF5 还是文件夹，而是字段名、形状、单位稳定，且能按 step_index 对齐。</p>
</figure>

<figure class="doc-figure">
<p class="doc-figure-title">同一 pick episode 的完整流程（UR16e 航点序列）</p>
<img src="/section/05-simulation-and-task-modeling/assets/episode-ur16e-pick-beaker-waypoints.gif" alt="UR16e pick beaker episode 的航点流程" style="max-width:100%;height:auto;display:block;margin:0.5em 0;border-radius:6px">
<figcaption class="doc-figure-subtitle">这段动图展示同一 UR16e pick beaker 流程中的接近、对齐、下降、闭合夹爪和抬起等阶段。采集成数据时，这些帧应属于同一条 episode，并通过 step_index 与 action、robot_state、object_state 和 metadata 对齐。</figcaption>
</figure>

只存视频，后面会处处卡：看得到机器人动了，却不知道当时发的 action；看得到夹爪靠近了，却不知道关节角和末端位姿；看得到失败了，却不知道失败在哪个阶段；画面很漂亮，却没有相机内外参，无法做几何推理。

至于存成 HDF5、Zarr、Parquet、npz 还是 jsonl 都行——**格式不重要，语义才重要**：每个字段有稳定的名字、稳定的形状、稳定的单位，并且能通过 `step_index` 对齐。

## step_index

前一页反复出现的 `step_index`，就是数据的时间骨架。没有它，相机帧、动作、状态和 debug event 就像几条散开的线，谁也对不上谁。

一个实用的回放原则是：任意打开一条 episode，都能从第一帧看到最后一帧，并且每一帧旁边都能同步显示——

```text
当前是第几帧（step_index）
当前任务阶段（phase）
这一帧的 action 摘要
机器人关节 / 末端位姿
目标物体位置
相机画面是否对应这一帧
success / failure 在哪一帧发生
```

判断数据质量有一条朴素标准：**如果你的数据不能回放，它大概率也不能被信任。** 回放不必重新跑物理，只要能按时间顺序把状态、动作、图像、阶段、判定同步重现即可。能稳定回放，数据质量就上了一个台阶。

## 字段一旦被下游使用，就成了长期约定

刚写脚本时字段名常常随手起：`img`、`image`、`camera`、`obs`、`q`、`state`。短期能跑，但一旦训练脚本、可视化脚本、评测脚本开始读它们，字段名和 shape 就变成了**长期约定**，改一个就连锁出错。

这些约定里，最容易埋雷的是"形状 / 单位 / 顺序"。建议在 metadata 或文档里**显式钉死**：

| 约定项 | 要写清的两种可能 | 说明 |
|---|---|---|
| 图像布局 | `HWC` 还是 `CHW` | 训练框架常要 CHW，可视化常用 HWC |
| 图像 dtype / 范围 | `uint8 0–255` 还是 `float32 0–1` | 错了图像会偏色或全黑 |
| 位置单位 | **米** | 与上一部分"坐标系与单位"一致 |
| 角度单位 | 弧度还是角度 | 程序里一律弧度 |
| 四元数顺序 | `wxyz` 还是 `xyzw` | Isaac core 是 `wxyz`，跨库先转 |
| action 含义 | 关节目标 / 关节增量 / 末端位姿增量 / 夹爪命令 | 决定下游怎么用这份动作 |
| 时间约定 | `obs_t + action_t → obs_{t+1}` | 动作和观测谁对谁，差一帧训练就废 |

这些看着不像"仿真"，但它们正是具身工程的核心能力：能跑演示是第一步，能产出别人敢用、自己半年后还看得懂的数据，才算真正工程化。

## metadata

metadata 是最容易被低估的部分。它不是"有空再补的说明"，而是一条失败样例**能不能被重跑**的关键。一条 episode 至少应保存：

```text
task_name        # 任务名
instruction      # 语言指令（如果有）
robot_type       # 机器人类型
scene_id         # 场景 / USD 版本
object_ids       # 目标物体 + 干扰物体
camera_configs   # 相机名、分辨率、位姿、内参
controller_config# 控制器 / 运动生成参数
random_seed      # 随机种子
asset_versions   # 关键资产版本或路径
success / failure_reason
```

同样是"抓取失败"，原因可能天差地别：物体初始太偏、相机看不到把手、RMPflow 避障太保守、夹爪摩擦太低、collision 不合理、阶段切换太早。没有 metadata，这些只能靠猜。

## 质检

成功率重要，但不是唯一指标。一个流程可能成功率很高却有严重数据问题，也可能成功率一般但失败样例极有价值。更好的质检同时看四类：

```text
任务结果：success rate、failure_reason 分布、失败发生的阶段
观测质量：黑图比例、目标可见比例、遮挡、depth/segmentation 是否可用
动作质量：是否平滑、是否超限、是否频繁卡在同一阶段
数据结构：字段是否齐全、shape 是否一致、step_index 是否连续
```

有些问题看视频时不明显，却会直接伤害训练——相机偶尔黑一帧、某条 episode 少一个相机字段、action 比图像晚一帧、phase 从中间才开始记录、失败 episode 没保存。落地成一份可勾的清单：

```text
1.  每条 episode 是否都有 metadata / camera / action / robot_state / success
2.  每个字段的时间长度是否一致
3.  step_index 是否从头到尾连续
4.  图像是否存在全黑 / 全白 / 旧帧 / 尺寸异常
5.  多相机字段是否在所有 episode 中一致
6.  action 是否和 observation 对齐（时间约定）
7.  phase 是否覆盖完整任务过程
8.  success 和 failure_reason 是否可信
9.  失败 episode 是否同样保存完整
10. 随机种子 + 资产版本是否足以复现
```

## 随机化要可复现

具身数据常要随机化：物体位置、材质、光照、相机扰动、桌面布局、干扰物体、初始关节姿态。随机化提升泛化，但也让问题更难查。原则是：**可以随机，但要能记录；可以变化，但要知道变了什么。**

只存 seed 往往不够——代码版本、资产列表或采样顺序一变，同一个 seed 可能产生不同结果。所以对关键变量要直接存**采样后的值**：

```text
random_seed     # 这一条用的随机种子
sampled_params  # 实际采样到的：物体初始位姿、相机扰动、材质名、障碍物位置 ...
```

记住一句话：**随机化是为了制造多样性，不是为了制造不可解释性。**

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 存了 mp4 就是采集到数据 | 视频只是一个视图 | 同时存对齐的结构化字段 |
| 用什么格式很关键 | 格式不重要，语义才重要 | 钉死字段名 / 形状 / 单位，按 step_index 对齐 |
| 字段名随手起没关系 | 下游一用就成长期约定 | 显式写清 layout / dtype / 单位 / 四元数 / action 含义 |
| 数据不用回放也行 | 不能回放就不能被信任 | 保证任意 episode 可逐帧同步回放 |
| 质检就是看成功率 | 黑图 / 错位 / 缺字段它都查不出 | 按四类指标 + 10 条清单质检 |
| 随机化只存 seed 就够 | 版本一变 seed 不保证一致 | 同时存 `sampled_params` |

## 小结

- 数据集不是视频文件夹：视频只是一个视图，episode 本身是按 `step_index` 对齐的结构化数据。
- 字段一旦被下游使用就成了长期约定，要钉死图像布局 / dtype / 单位 / 四元数顺序 / action 含义 / 时间约定。
- metadata 是复现入口，随机化要同时存 seed 和采样后的值。
- 质检别只看成功率：任务结果 / 观测质量 / 动作质量 / 数据结构四类一起查；能稳定回放是数据可信的底线。

## 参考资料

- ManiSkill Documentation, [Custom Tasks: Intro](https://maniskill.readthedocs.io/en/latest/user_guide/tutorials/custom_tasks/intro.html)
- Isaac Lab Documentation, [Sensors](https://isaac-sim.github.io/IsaacLab/main/source/overview/core-concepts/sensors/index.html)
- NVIDIA Isaac Sim 5.1.0 Documentation, [Data Generation / Synthetic Data](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/index.html)

## 导航

- 返回目录：[任务、数据采集与合成数据](../06-task-and-data.md)
- 上一页：[任务、episode 与成功判定](01-task-episode-success.md)
- 下一页：[数据存放格式](03-data-storage-format.md)
