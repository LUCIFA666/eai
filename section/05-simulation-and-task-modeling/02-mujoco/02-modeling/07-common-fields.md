# 常用字段速查

写 MuJoCo 代码，十有八九都在和 `data` 里那几个字段打交道：读 `qpos`/`qvel` 看状态、写 `ctrl` 发指令、取 `sensordata` 拿观测。这一页就把这些常用字段逐个梳理一遍，并配一张速查表，方便随时回来查。

## 本节目标

本节把常用字段过一遍，重点回答几个问题：

1. `qpos` / `qvel` / `ctrl` / `sensordata` / `time` 各装什么，怎么读、怎么写？
2. `qpos` 和 `qvel` 的长度为什么不一定相等？
3. 写了 `ctrl`，为什么没有立刻生效？

## 位置：qpos

`data.qpos` 是所有关节位置的拼接，长度等于 `model.nq`。它的内容取决于模型里有哪些类型的 joint：

- hinge / slide：贡献 1 个标量值（角度或位移，单位为弧度或米）。
- ball：贡献 4 个值（一个四元数 `w x y z`）。
- free：贡献 7 个值（3 个平移 + 4 个四元数）。

对于 Panda（7 个 hinge + 2 个 slide），`nq=9`，`qpos` 的 9 个数依次是：joint1 角度、joint2 角度、……、joint7 角度、finger_joint1 位移、finger_joint2 位移。

```python
import mujoco
import numpy as np

model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

# 读所有关节位置
print(f"qpos = {data.qpos}")
print(f"joint1 angle = {data.qpos[0]:.3f} rad")

# 也可以按名字读某个 joint 的位置
print(f"joint1 = {data.joint('joint1').qpos}")
```

**重要提醒**：`data.qpos` 返回的是 NumPy 数组的**视图（view）**，不是副本。如果把它赋值给一个变量然后调了 `mj_step`，变量的值会跟着变。如果需要保存历史值，记得 `.copy()`。

## 速度：qvel

`data.qvel` 是所有关节速度的拼接，长度等于 `model.nv`。和 `qpos` 不同，**所有 joint 的速度维度都是标量**，即使是 ball 和 free 关节，速度也是用 3 个角速度分量（或 3 线速度 + 3 角速度）而不是四元数。

这就是为什么 `nq` 不一定等于 `nv`：

| 场景 | nq | nv | 原因 |
|---|---|---|---|
| Panda（纯 hinge + slide） | 9 | 9 | 每个 joint 各贡献 1 个 qpos 和 1 个 qvel |
| 一个自由漂浮的方块（1 个 free joint） | 7 | 6 | qpos 用四元数（4 个数），qvel 用角速度（3 个数） |
| 手臂 + 方块（hinge×7 + free×1） | 14 | 13 | nq：7×1 + 7；nv：7×1 + 6 |

```python
# qvel 和 qpos 长度未必相同
print(f"nq = {model.nq}, nv = {model.nv}")
print(f"len(qpos) = {len(data.qpos)}, len(qvel) = {len(data.qvel)}")
```

## 控制：ctrl

`data.ctrl` 是我们写给 actuator 的控制信号，长度等于 `model.nu`。注意：写 `ctrl` **不会立刻产生效果**，它需要等到下一次 `mj_step` 时，MuJoCo 才会把它转换成力、积分出新状态。

```python
# 给所有 actuator 写控制量
data.ctrl[:] = [0.5, -0.3, 0.1, -1.57, 0.0, 1.57, -0.785, 255]

# ctrl 是持久化的，写一次会一直沿用，直到再次被覆盖
mujoco.mj_step(model, data)  # 这步会使用上面写的 ctrl
```

关于 `ctrl` 的语义（给的是力、位置还是速度），取决于 actuator 的类型，这会在第 3 章详细展开。这里只需要知道：`ctrl` 是我们和 MuJoCo 之间传递控制意图的"接口数组"。

## 传感器读数：sensordata

`data.sensordata` 是所有传感器读数的拼接，长度等于 `model.nsensordata`（传感器值的总数，可能大于传感器个数 `model.nsensor`，因为一个传感器可能输出多个值）。传感器值的含义和顺序由 MJCF 里 `<sensor>` 节的声明决定。

如果模型里没有声明任何传感器（`model.nsensor == 0`），`data.sensordata` **就是空的**。Panda 默认就是这种情况。如果需要传感器，要在 MJCF 里加上对应声明。第 4 章会详细讲传感器的定义和读取。

```python
if model.nsensor > 0:
    print(f"sensordata = {data.sensordata}")
else:
    print("这个模型没有传感器")
```

## 时间：time

`data.time` 是当前仿真时间，单位为秒（如果用的是 MKS 单位制）。每次 `mj_step` 后，`time` 增加 `model.opt.timestep`。

```python
print(f"初始时间: {data.time:.3f}")
for i in range(100):
    mujoco.mj_step(model, data)
print(f"100 步后: {data.time:.3f}  (timestep={model.opt.timestep})")
```

## 字段速查表

| 字段 | 所属 | 长度 | 内容 | 读/写 | 典型用法 |
|---|---|---|---|---|---|
| `model.nq` | mjModel | 标量 | 位置维度 | 只读 | 了解模型规模 |
| `model.nv` | mjModel | 标量 | 速度维度 | 只读 | 和 nq 对比 |
| `model.nu` | mjModel | 标量 | actuator 数量 | 只读 | 确定 ctrl 长度 |
| `model.nsensor` | mjModel | 标量 | 传感器个数 | 只读 | 判断有没有传感器 |
| `model.nsensordata` | mjModel | 标量 | 传感器值总数 | 只读 | 确定 sensordata 长度 |
| `model.opt.timestep` | mjModel | 标量 | 仿真步长 | 可读写 | 调整仿真速度/稳定性 |
| `data.qpos` | mjData | (nq,) | 关节位置 | 可读写 | 读取状态 / 初始化姿态 |
| `data.qvel` | mjData | (nv,) | 关节速度 | 可读写 | 读取状态 |
| `data.ctrl` | mjData | (nu,) | 控制信号 | 读写 | 给 actuator 写指令 |
| `data.sensordata` | mjData | (nsensordata,) | 传感器读数 | 只读 | 获取观测（需先声明 sensor） |
| `data.time` | mjData | 标量 | 仿真时间 | 可读写 | 计时、重置 |
| `data.act` | mjData | (na,) | 执行器激活 | 可读写 | 某些特殊 actuator 的内部状态（少见） |
| `data.contact` | mjData | (ncon,) | 接触信息 | 只读 | 查询碰撞（dim, geom1, geom2, dist, frame...） |

## 小结

- `qpos`（位置）和 `qvel`（速度）长度不一定相等，ball 和 free joint 会打破这个等式。
- `ctrl` 是"写入指令"的地方，效果在下一次 `mj_step` 中体现。它是持久化的，不会自动清零。
- `sensordata` 依赖于 MJCF 里声明了 `<sensor>`。Panda 默认没有传感器，所以这个数组是空的。
- `time` 每次 `mj_step` 后增加 `timestep`。

## 参考资料

- [MuJoCo Documentation: Computation](https://mujoco.readthedocs.io/en/stable/computation/index.html)
- [MuJoCo Documentation: Python Bindings](https://mujoco.readthedocs.io/en/stable/python.html)

## 导航

- 上一节：[mjModel vs mjData](06-mjmodel-vs-mjdata.md)
- 返回上级：[建模](../02-modeling.md)
- 下一节：[keyframe 与命名](08-keyframe-and-naming.md)
