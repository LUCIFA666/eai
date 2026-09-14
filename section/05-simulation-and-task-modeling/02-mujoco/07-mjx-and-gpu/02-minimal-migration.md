# 最小迁移

把一段 CPU MuJoCo 代码改成 MJX，最少要动哪几行？这一页用一个左右对照的最小例子来回答，并在改动过程中自然引入 JAX 的两个关键概念：`jit`（即时编译，类比 PyTorch 的 `torch.compile`）和 `vmap`（自动向量化，类比 `torch.vmap`）。

## 本节目标

本节回答几个问题：

1. mujoco 和 mjx 的 API 怎么一一对应？
2. `jax.jit` 和 `jax.vmap` 各自做什么、在迁移里扮演什么角色？
3. CPU 和 MJX 跑出来的物理结果会不会一致？

## API 对应表：mujoco ↔ mjx

| 原生 mujoco | mujoco.mjx | 说明 |
|---|---|---|
| `mujoco.MjModel.from_xml_path(...)` | 同上（然后 `mjx.put_model`） | 模型仍从原生加载，再转换 |
| `mujoco.MjData(model)` | `mjx.make_data(model)` | 数据创建函数名变化 |
| `mujoco.mj_step(model, data)` | `mjx.step(model, data)` | step 变成纯函数，返回新 data |
| `data.qpos` | `mjx_data.qpos` | 字段名相同，但返回 JAX 数组 |
| `data.ctrl` | `mjx_data.ctrl` | 同上 |
| `mujoco.mj_forward(...)` | `mjx.forward(...)` | forward 也变成纯函数 |

最关键的区别在于：MJX 的 step 和 forward 是纯函数，它们接收 model 和 data，返回新的 data，不会修改输入。这里的"纯函数"指的是只看输入算输出、不改动传进来的对象，下面用到 `jit` 和 `vmap` 时都依赖这一点。

## 左右对照：迁移一个最小脚本

**CPU 版本（原生 mujoco）：**

```python
import mujoco

model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

for i in range(100):
    data.ctrl[:] = 0.1  # 就地写入
    mujoco.mj_step(model, data)  # 就地修改 data
    print(data.qpos[0])
```

**GPU 版本（MJX）：**

```python
import mujoco
import mujoco.mjx as mjx
import jax

model = mujoco.MjModel.from_xml_path("scene.xml")
mjx_model = mjx.put_model(model)
mjx_data = mjx.make_data(model)

@jax.jit  # JIT 编译：第一次慢，后面飞快
def step_fn(data, ctrl):
    data = data.replace(ctrl=ctrl)  # 纯函数：返回新对象
    data = mjx.step(mjx_model, data)  # 返回新 data，不修改输入
    return data

for i in range(100):
    ctrl = jax.numpy.array([0.1] * model.nu)
    mjx_data = step_fn(mjx_data, ctrl)  # 接收返回值
    print(mjx_data.qpos[0])
```

需要改的地方：导入 mjx、model 转换、step 用纯函数风格、使用 `data.replace()` 而非就地赋值；通常再套 `jax.jit` 加速（不加也能跑，只是慢得多）。

## jit：第一次 step 慢、后面飞快

`jax.jit` 是 JAX 的即时编译装饰器，作用和 PyTorch 2.0 的 `torch.compile` 类似，把 Python 函数编译成优化的机器码。第一次调用时会花时间做编译（tracing），之后的调用直接执行编译好的代码。

“第一次慢”具体能差多少，和模型复杂度、GPU 关系很大。下面是本教程脚本（`labs/04-simulation/mjx_minimal.py`）在**单张 RTX 4090** 上、用一个内置小模型（`nq=14`、13 个自由度）跑出来的原样输出（见 `runs/04-simulation/mjx_minimal.json`）：

```text
[1-env]   first call (JIT+step) = 15729.2 ms | cached step = 2.829 ms
[batch=256] first call (JIT+step) = 15023.9 ms | cached batch step = 1.567 ms | throughput = 163400 env-steps/s
```

也就是说：首次调用要**十几秒**做编译（带完整碰撞网格的复杂场景会更久，可达几分钟），编译后单步只要几毫秒。

所以通常在正式跑之前先"预热"一步：

```python
# 预热
mjx_data = step_fn(mjx_data, jax.numpy.zeros(model.nu))
# 正式跑，现在很快了
for i in range(10000):
    mjx_data = step_fn(mjx_data, ctrl)
```

## vmap：一次跑 N 个环境

`jax.vmap` 是 JAX 的自动向量化函数，作用和 PyTorch 的 `torch.vmap` 类似，把一个处理单个样本的函数自动变成处理一批样本的函数。

```python
# 单环境 step（纯函数）
def single_step(data, ctrl):
    data = data.replace(ctrl=ctrl)
    return mjx.step(mjx_model, data)

# vmap 沿第 0 维（批量维）把它向量化，外面再套 jit 把整段编译到 GPU
batch_step = jax.jit(jax.vmap(single_step))

# 把单份 mjx_data 复制成 N 份：mjx_data 是一棵由数组字段组成的树，
# 对每个字段在最前面加一维、广播到 N，就得到 N 份相同的初始状态
N = 1024
batch_data = jax.tree_util.tree_map(
    lambda x: jax.numpy.broadcast_to(x, (N,) + x.shape), mjx_data)
batch_ctrl = jax.numpy.zeros((N, model.nu))

# 一次推进 N 个环境
batch_data = batch_step(batch_data, batch_ctrl)
```

这里有两步要分开看。`jax.vmap(single_step)` 把单环境函数沿第 0 维并行化，外面的 `jax.jit` 把整段编译到 GPU（少了 `jit` 也能跑，但每步都回到 Python，慢得多）。批量数据用 `jax.tree_util.tree_map` + `broadcast_to` 造出来：本教程的 `mjx_minimal.py` 和 `mjx_speed_benchmark.py` 用的正是这个写法。不用手写 for 循环，也不用改 step 的内部实现，这就是 JAX 函数式设计带来的好处。这里广播出的是 N 份**相同**的初始状态；想让每个环境起点不同，把广播换成按环境生成即可（例如给每个环境的 `qpos` 取不同随机值）。

## 数值差异：CPU vs GPU 的对照

MJX 默认用单精度 float32（CPU MuJoCo 用双精度），GPU 上浮点运算的执行顺序也和 CPU 不完全一致，所以同样的初始状态，CPU 和 MJX 跑若干步后的 `qpos` 会有差异。**差异有多大，强烈取决于场景**。定性地说：

- **无接触的平滑动力学**（如双摆自由摆动）：差异很小，短期内几乎察觉不到。
- **有接触的场景**（落地、抓取等）：求解器在接触处会分岔，差异随步数明显放大，步数一多可能大到与状态本身同量级。

想知道自己的场景里差多少，把上面“左右对照”的两段代码从同一初始状态各推进若干步、对比 `qpos` 的最大绝对差即可。

这个差异在大多数 RL 训练场景中**不影响最终策略性能**，策略学的是"在什么状态做什么动作"的模式，而不是精确的逐帧轨迹。但如果在做精确的动力学分析或系统辨识，需要注意这个差异。

## 小结

- MJX 的核心变化：`mj_step` → 纯函数 `mjx.step`，就地修改 → `data.replace()` + 接收返回值。
- `jax.jit`（类比 `torch.compile`）让仿真循环编译加速，第一次慢、后续快。
- `jax.vmap`（类比 `torch.vmap`）让单环境 step 自动变成批量 step。
- CPU 和 GPU 有浮点差异：无接触场景极小、接触场景明显；但在 RL 场景中通常不影响最终策略性能。

## 参考资料

- [MuJoCo Documentation: MJX（put_model / make_data / step、jit / vmap）](https://mujoco.readthedocs.io/en/stable/mjx.html)
- [MuJoCo mjx/tutorial.ipynb](https://github.com/google-deepmind/mujoco/blob/main/mjx/tutorial.ipynb)
- [JAX Documentation](https://jax.readthedocs.io/)

## 导航

- 上一节：[为什么 MJX](01-why-mjx.md)
- 返回上级：[MJX 与 GPU 并行](../07-mjx-and-gpu.md)
- 下一节：[速度与 benchmark](03-speed-and-benchmarks.md)
