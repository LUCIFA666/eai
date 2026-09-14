# MuJoCo 程序怎么运转

一个 MuJoCo 程序，剥到最简，其实就做两件事：先把模型读进来，再反复地“给一点控制、让仿真往前走一步、读一下新的状态”。这两件事背后有几个一开始容易混的概念。这一页用一张图把它们的关系理清楚，在心里建立起“MuJoCo 程序怎么运转”的整体印象。图立住了，后面每一章无论讲 actuator、sensor 还是渲染，都能自然地挂回到它的某一块上。

## 本节目标

本节就顺着这张图，把下面几个问题弄清楚：

1. 模型文件（MJCF）经过“编译”这一步，到底变成了什么？为什么这件事整个仿真只做一次？
2. `mjModel` 和 `mjData` 各装了什么，凭什么说一个“从头到尾不变”、另一个“每步都在变”？
3. 循环里那句 `mj_step` 每调用一次，内部都发生了什么？它和 `mj_forward` 又差在哪？

## 一张主图：MuJoCo 的运转节奏

下面这张图概括了一个 MuJoCo 程序从加载模型到循环推进的全过程。建议先扫一眼整体结构，再逐块往下读。

<figure class="doc-figure figure-loop" aria-label="MuJoCo 运转主线图">
  <p class="doc-figure-title">MuJoCo 的运转主线：从 MJCF 到 step 循环</p>
  <p class="doc-figure-subtitle">一条主线：模型文件 → 编译 → 静态结构 + 动态状态 → 循环推进。</p>
  <div class="figure-pipeline">
    <div class="figure-node tone-green">
      <strong>MJCF / URDF</strong>
      <span>我们用 XML 描述机器人：有哪些 body、关节怎么连、几何长什么样、驱动怎么定义。</span>
    </div>
    <div class="figure-node tone-green">
      <strong>编译</strong>
      <span>MuJoCo 把 XML 解析、校验、编译成 <code>mjModel</code>。这一步只做一次。</span>
    </div>
    <div class="figure-node tone-blue">
      <strong>mjModel</strong>
      <span>静态结构：关节数、几何、惯性、驱动参数……整个仿真过程中基本不变。</span>
    </div>
    <div class="figure-node tone-blue">
      <strong>mjData</strong>
      <span>动态状态：<code>qpos</code>、<code>qvel</code>、<code>ctrl</code>、<code>sensordata</code>、<code>time</code>……每一步都在变。</span>
    </div>
    <div class="figure-node tone-gold">
      <strong>读观测</strong>
      <span>从 <code>data.qpos</code>、<code>data.sensordata</code> 等字段取出当前状态。</span>
    </div>
    <div class="figure-node tone-gold">
      <strong>给控制</strong>
      <span><code>data.ctrl[:] = ...</code>，告诉 actuator 下一步该怎么出力。</span>
    </div>
    <div class="figure-node tone-rose">
      <strong>mj_step</strong>
      <span>推进一个时间步：根据当前状态和控制量，按物理规律算出新的状态。</span>
    </div>
    <div class="figure-node tone-rose">
      <strong>渲染 / 记录</strong>
      <span>需要时把当前画面渲染出来，或把状态写入文件。</span>
    </div>
  </div>
  <div class="figure-note">核心循环：读状态 → 给控制 → <code>mj_step</code> → 重复。需要观察或记录时，在循环中插入渲染/日志。</div>
</figure>

如果觉得这张图里概念有点多，没关系。下面我们把每一块拆开来看。

## MJCF 是描述，mjModel 是编译结果

我们写的 MJCF 文件（就是那些 `.xml`）是对机器人和场景的**描述**，用一种人能够阅读和修改的格式，把"这个机器人有几根连杆、关节能转多少度、每段有多重"这些事情说清楚。

MuJoCo 拿到这个文件之后，会做一个类似"编译"的过程：解析 XML、检查有没有语法错误和语义矛盾，然后把所有信息整理成一份紧凑的、方便反复查询的数据结构，这就是 `mjModel`。

这个过程只要做一次。换句话说：

```text
MJCF 文件  ──[解析 + 编译]──>  mjModel
```

编译完以后，`mjModel` 里存的是"这个机器人是什么"，比如一共有几个关节（`nq`）、几个驱动（`nu`）、重力加速度是多少、每个关节的限位在哪里。在一次仿真过程中，这些信息通常不会改变。可以把 `mjModel` 理解成棋盘和规则：开局时定好，整盘棋都按这套规则走。

实际代码里，加载模型最常见的方式是：

```python
import mujoco

model = mujoco.MjModel.from_xml_path("scene.xml")
```

这一行背后，MuJoCo 替我们做了 XML 解析、校验、编译的全部工作。得到的 `model` 就是 `mjModel`。

有一个容易混淆的地方值得提一下：MJCF 文件里写的角度单位可能是度（degree）也可能是弧度（radian），由 `<compiler angle="...">` 决定。但编译进 `mjModel` 之后，所有角度统一变成弧度。也就是说，之后在代码里读到的 `qpos` 永远是弧度，不用再操心单位转换。

## mjData 是动态状态：每一步都会变

如果说 `mjModel` 是"棋盘和规则"，那 `mjData` 就是"此刻的棋局"，每一步都不同。

`mjData` 由 `mjModel` 创建，里面存的是仿真在某一时刻的全部动态信息：

```python
data = mujoco.MjData(model)
```

`mjData` 里最常用的几个字段如下：

| 字段 | 含义 | 变还是不变 |
|---|---|---|
| `data.qpos` | 关节位置（各关节当前的角度/位移） | 每步都变 |
| `data.qvel` | 关节速度 | 每步都变 |
| `data.ctrl` | 我们给 actuator 的控制量 | 我们每步写入 |
| `data.sensordata` | 传感器读数（如果模型里定义了传感器） | 每步更新 |
| `data.time` | 当前仿真时间 | 每步递增 |
| `data.contact` | 当前发生的接触信息 | 每步更新 |

所有跟"此刻"有关的东西都在 `mjData` 里。所以如果发现读出来的状态怎么一直不变，很可能是忘记调 `mj_step` 推进仿真了，`mjData` 不会自己更新。

这两个结构体的分工，是 MuJoCo 设计上很干净的一点：想换初始状态，不需要重新编译模型，只需要新建一个 `mjData` 或调用重置函数就行；想做并行采样，多个线程各持一份 `mjData`、共享同一份 `mjModel` 即可。

## step 循环把所有东西串起来

有了 `mjModel`（规则）和 `mjData`（当前局面），剩下的就是反复做一件事：**给控制 → 推进一步 → 读状态 → 重复**。

这就是 `mj_step` 的角色。每次调用 `mj_step(model, data)`，MuJoCo 内部会做这些事情：

1. 检查位置和速度有没有异常（发散了就重置）
2. 跑一遍正向运动学，算出各 body 在世界坐标系里的位置和朝向
3. 计算传感器读数
4. 把 `data.ctrl` 里的控制量转换成关节力
5. 跑正向动力学，算出加速度
6. 数值积分，把状态（`qpos`、`qvel`、`time` 等）往前推一个时间步

所以 `mj_step` 不是一个简单的"加一下"，而是一整套流水线。好在我们不用管中间细节，调用它就完事了。

和 `mj_step` 容易混淆的是 `mj_forward`。两者的区别很简单：

- `mj_forward(model, data)`：**不推进时间**，只根据当前的 `qpos` 和 `ctrl` 把派生量（各 body 位置、传感器值等）刷新一遍。典型用法是手动设好初始姿态后，调用它刷新一次，再去读取或渲染。
- `mj_step(model, data)`：**推进时间**，先做 `mj_forward` 的工作，再算动力学、做积分，把状态更新到下一时刻。

一个简化的循环骨架大致是这样：

```python
import mujoco

model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

# 初始化：摆好初始姿态，刷新一次派生量
# （模型需定义 keyframe；没有就改用 mj_resetData）
mujoco.mj_resetDataKeyframe(model, data, 0)
mujoco.mj_forward(model, data)

# 主循环
for i in range(200):
    data.ctrl[:] = compute_control(i)   # 根据当前状态算控制量
    mujoco.mj_step(model, data)         # 推进一步
    # 需要时在这里读状态、渲染、记录
```

大多数 MuJoCo 程序的骨架都和它类似。后面的章节会在这个骨架上不断加东西，不同的 actuator 类型、不同的传感器、不同的渲染方式，但骨架本身大体不变。

## 这张图后面怎么用

后续每一章，都可以理解成在给这张主图补某一块的细节：

| 章节 | 对应主图的哪一块 | 主要补什么 |
|---|---|---|
| 建模（第 2 章） | MJCF → mjModel | MJCF 文件里每个节的写法；body 树、关节、几何、default 继承；mjModel 和 mjData 的常用字段怎么读 |
| 控制与物理（第 3 章） | 给控制 → mj_step | actuator 有哪些类型、ctrl 怎么变成力、接触和摩擦怎么算、仿真参数怎么调 |
| 观测与渲染（第 4 章） | 读观测 + 渲染/记录 | 怎么从 data 取状态、怎么定义传感器、怎么离屏渲染出图、无显示器怎么办 |
| 接口与生态（第 5 章） | 整条主线外围 | 现成机器人模型库、dm_control 等上层封装、什么时候用原生 MuJoCo 什么时候用上层 |
| 抓取实战（第 6 章） | 整条主线实战 | 从前到后完整走一遍：搭场景 → 控制末端 → 夹爪 → 完整抓取管线 → 调试 |
| MJX 与 GPU（第 7 章） | mj_step 的加速版 | 怎么用 GPU 批量并行跑仿真、JAX 版 mj_step 怎么用、速度能快多少 |
| 训练教程（第 8 章） | 循环外面包一层 RL | 怎么把 step 循环嵌入 PPO/SAC 训练、怎么从 demo 学、sim2real 注意事项 |

读后面各章时，如果不确定某一页在讲什么位置，可以回到这一页看一眼这张表，它应该能快速定位。

## 小结

- MuJoCo 程序的主线很清晰：**MJCF → 编译 → mjModel（规则）+ mjData（局面）→ 循环{读状态 → 给控制 → mj_step → 重复}**。
- `mjModel` 存"这个机器人是什么"，整个仿真过程中基本不变。`mjData` 存"此刻是什么状态"，每一步都在变。
- `mj_step` 推进时间和物理；`mj_forward` 只刷新派生量，不推进时间。初始化摆姿态用后者，循环推进用前者。
- 后续每一章都是在这条主线的不同位置补细节。遇到不确定某页在讲什么的时候，回到这一页对着表查即可。

## 动手练习

创建 `mjData` 后打印 `data.qpos`，看看初始关节位置。把 `data.qpos[0]` 改成一个新值，调一次 `mj_forward` 再打印，看 `qpos[0]` 是停在刚设的值，还是被改动了？再把 `mj_forward` 换成 `mj_step` 跑一步对比，这次 `qpos` 的变化有什么不同？（提示：一个只刷新派生量、不推进时间，一个会真正推进物理。）

## 参考资料

- [MuJoCo Documentation: Overview](https://mujoco.readthedocs.io/en/stable/overview.html)
- [MuJoCo Documentation: Computation](https://mujoco.readthedocs.io/en/stable/computation/index.html)
- [MuJoCo Documentation: Python Bindings](https://mujoco.readthedocs.io/en/stable/python.html)

## 导航

- 上一节：[MuJoCo 是什么](01-what-is-mujoco.md)
- 返回上级：[认识 MuJoCo](../01-overview.md)
- 下一节：[MuJoCo 安装与第一个仿真实验](03-install-and-first-run.md)
