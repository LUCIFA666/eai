# Python API 巡览

`import mujoco` 之后，到底有哪些东西可以用？这些对象并不是平铺的一堆，按职责能分成几类。先把这张地图认清，用到具体某个时就好对号入座。

## 本节目标

本节把 `mujoco` 包逛一遍：

1. 包里有哪些常用的顶层对象，各自管什么？
2. `MjSpec`（用代码建模、不写 XML）怎么用，什么时候用得上？
3. `rollout`（批量采样）解决什么问题？

## mujoco 模块全貌

`mujoco` 包里的主要对象可以分为几类：

<figure class="doc-figure" aria-label="mujoco 模块地图">
  <p class="doc-figure-title">mujoco 包的核心模块</p>
  <table>
    <tr><th>类别</th><th>主要对象</th><th>职责</th></tr>
    <tr><td>数据结构</td><td><code>MjModel</code>, <code>MjData</code>, <code>MjOption</code>, <code>MjvScene</code></td><td>模型、状态、选项、渲染场景</td></tr>
    <tr><td>仿真函数</td><td><code>mj_step</code>, <code>mj_forward</code>, <code>mj_resetData</code></td><td>推进仿真、刷新派生量、重置状态</td></tr>
    <tr><td>渲染</td><td><code>Renderer</code>, <code>viewer</code></td><td>离屏渲染、交互式查看器</td></tr>
    <tr><td>建模</td><td><code>MjSpec</code> + <code>add_body</code>/<code>add_geom</code> 等方法</td><td>编程式创建和编辑模型</td></tr>
    <tr><td>并行</td><td><code>rollout</code> 模块</td><td>CPU 多线程并行 rollout</td></tr>
    <tr><td>MJX (GPU)</td><td><code>mujoco.mjx</code></td><td>JAX 后端的 GPU 并行仿真</td></tr>
    <tr><td>枚举/常量</td><td><code>mjtObj</code>, <code>mjtJoint</code>, <code>mjtVisFlag</code> 等</td><td>类型常量</td></tr>
  </table>
</figure>

前两类（数据结构 + 仿真函数）在前面几节里已经大量用到了。后面几页会重点讲建模（MjSpec）、并行（rollout），以及上层封装（dm_control、Gymnasium）。

## MjSpec：编程式建模

`MjSpec` 是 MuJoCo 3.2 引入的程序化建模接口，可以用 Python 代码来创建和修改模型，而不是手写 XML（在 C API 里它对应 `mjSpec` 结构体，Python 绑定里则是 `MjSpec` 类，没有零散的 `mjs_*` 函数，建模动作都收进了 `add_body` 这类方法）：

```python
import mujoco

spec = mujoco.MjSpec()
# 也可以从已有 XML 解析：spec = mujoco.MjSpec.from_file("model.xml")

# 在 worldbody 下加一个 body
body = spec.worldbody.add_body(name="my_box", pos=[0, 0, 1])

# 给它加一个 free joint
body.add_joint(type=mujoco.mjtJoint.mjJNT_FREE)

# 加一个 box geom
body.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.1, 0.1, 0.1])

# 编译成 mjModel
model = spec.compile()
```

这种方式适合这些场景：
- 需要程序化地生成大量变体模型（比如随机化质量、尺寸）。
- 在运行时动态修改模型结构（改完 spec 再重新 `compile`）。
- 不喜欢手写 XML，更习惯用 Python 表达模型。

对于大多数日常使用，尤其是要加载已有的机器人模型，直接用 XML 和 `MjModel.from_xml_path` 更方便。`MjSpec` 是一个"需要时可用"的工具，不必强求。

## rollout：批量并行采样

`mujoco.rollout` 模块提供了批量 rollout：共享一份 `mjModel`，一次把多条轨迹滚出来，配合 `Rollout` 类还能多线程并行。

```python
import mujoco
from mujoco import rollout
import numpy as np

model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

nbatch, nstep = 4, 100
# 每条轨迹一份初始状态（完整物理状态）和一段控制序列
nstate = mujoco.mj_stateSize(model, mujoco.mjtState.mjSTATE_FULLPHYSICS)
initial_state = np.zeros((nbatch, nstate))
control = np.random.randn(nbatch, nstep, model.nu)

# 一次性把 nbatch 条轨迹滚出来；state 形状 (nbatch, nstep, nstate)
state, sensordata = rollout.rollout(model, data, initial_state, control)

# 想显式多线程：with rollout.Rollout(nthread=4) as r: r.rollout(model, datas, ...)
# （datas 是长度等于 nthread 的 MjData 列表）
```

rollout 是纯 CPU 的方案（相当于把单线程的 step 循环并行化），优点是代码改动很小。当环境数量到几千级别时，MJX 的 GPU 批量方案通常会更高效。

## viewer / Renderer 在包里的位置

- `mujoco.viewer`：交互式查看器子模块，提供 `launch()` 和 `launch_passive()`。适合本地调试。
- `mujoco.Renderer`：离屏渲染类，提供 `update_scene()` + `render()`。适合服务器批量出图。

这两者在前面"观测与渲染"一节里已经详细展开过，这里不再重复。

## 小结

- `mujoco` 包的核心是数据结构 + 仿真函数 + 渲染。
- `MjSpec` 提供了不依赖 XML 的程序化建模能力，适合动态生成模型变体。
- `rollout` 模块提供 CPU 多线程并行采样，是 GPU 并行（MJX）之前的简单提速手段。
- `mujoco.viewer` 和 `mujoco.Renderer` 分别服务于交互调试和批量出图。

## 参考资料

- [MuJoCo Documentation: Python Bindings（MjSpec / rollout）](https://mujoco.readthedocs.io/en/stable/python.html)
- [MuJoCo（GitHub）](https://github.com/google-deepmind/mujoco)

## 导航

- 上一节：[接口与生态](../05-interfaces-and-ecosystem.md)
- 返回上级：[接口与生态](../05-interfaces-and-ecosystem.md)
- 下一节：[mujoco_menagerie](02-menagerie.md)
