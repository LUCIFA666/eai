# sensor 与 sensordata

MuJoCo 把传感器抽象成 MJCF 里的顶层元素 `<sensor>`，运行时所有 sensor 的读数汇总在 `data.sensordata` 这个一维数组里。要从"这个机器人能测到什么"变成"能在 Python 里读到什么数据"，就得在 MJCF 里把 sensor 声明出来。

## 本节目标

本节把 sensor 这条线走通：

1. MuJoCo 有哪些常用的内置 sensor 类型？
2. 怎么在 MJCF 里声明它们？
3. 运行时 `data.sensordata` 这个一维数组，怎么按 sensor 切片对齐？
4. 怎么给读数加噪声，贴近真实传感器？

## sensor 类型一览

MuJoCo 提供了多种内置传感器类型。以下是常用的一览：

| sensor 类型 | 测量内容 | 输出维度 | 典型用途 |
|---|---|---|---|
| `jointpos` | 指定关节的位置 | 1 | 读取关节角 |
| `jointvel` | 指定关节的速度 | 1 | 读取关节速度 |
| `actuatorfrc` | 指定 actuator 输出的力 | 1 | 监测电机力矩 |
| `touch` | 指定 site 处的法向接触力（标量） | 1 | 指尖触觉 |
| `force` | 指定 site 处的力 | 3 | 腕部力传感 |
| `torque` | 指定 site 处的力矩 | 3 | 腕部力矩传感 |
| `accelerometer` | 指定 site 处的加速度 | 3 | IMU（惯性测量单元）的一部分 |
| `gyro` | 指定 site 处的角速度 | 3 | IMU 的一部分 |
| `framepos` | 指定 body/site 的世界位置 | 3 | 末端位置反馈 |
| `framequat` | 指定 body/site 的世界朝向 | 4 | 末端朝向反馈 |
| `framelinvel` | 指定 body/site 的世界线速度 | 3 | 速度反馈 |
| `rangefinder` | 类似激光测距 | 1 | 高度测量、避障 |

## 声明一个 sensor

在 MJCF 里加 `<sensor>` 节。下面是一个加在 Panda 上的例子，在夹爪指尖各放一个 touch sensor，再加一个腕部的 force-torque sensor：

```xml
<sensor>
  <!-- 指尖触觉：测法向接触力（标量） -->
  <touch name="left_touch"  site="left_touch_site"/>
  <touch name="right_touch" site="right_touch_site"/>

  <!-- 腕部力矩传感器 -->
  <force name="wrist_force" site="wrist_site"/>
  <torque name="wrist_torque" site="wrist_site"/>

  <!-- 关节位置传感器 -->
  <jointpos name="joint1_pos" joint="joint1"/>
</sensor>
```

需要在对应的 body 上先定义好 site（sensor 会用到 site 的位置）。这些 sensor 声明完之后，编译出来的 `model.nsensor` 就不再是 0 了。

## 解析 data.sensordata

所有 sensor 的读数按声明顺序拼接在 `data.sensordata` 的一维数组里。要知道每个 sensor 的数据从哪开始、占多长，需要用到 `model.sensor_adr` 和 `model.sensor_dim`：

```python
import numpy as np

for i in range(model.nsensor):
    name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SENSOR, i)
    adr = model.sensor_adr[i]
    dim = model.sensor_dim[i]
    value = data.sensordata[adr:adr + dim].copy()
    print(f"sensor[{i}] {name}: adr={adr}, dim={dim}, value={value}")
```

更简单的方式是用 `data.sensor("name")`：

```python
# 直接按名字读取 sensor 值
touch_data = data.sensor("left_touch").data   # numpy 数组
print(f"left touch (法向接触力): {touch_data}")
```

**重要提示**：和 `data.qpos` 一样，`data.sensordata` 也是视图。如果要把 sensor 数据保存下来，记得 `.copy()`。

## 真实输出示例

上面的 sensor 声明加上 Panda 模型后，跑 100 步（不加控制），打印此时的 sensor 读数：

```text
left_touch   = 0.0              # touch 是 1 维标量；没接触，读数为 0
right_touch  = 0.0
wrist_force  = [fx, fy, fz]     # force 是 3 维；手臂受重力，这里通常非零
wrist_torque = [tx, ty, tz]     # torque 是 3 维
```

只有在产生接触时，`touch` sensor 才会读到非零值。要看到非零读数，需要让指尖碰到物体。在后面的[抓取实战](../06-grasping-walkthrough.md)里，我们会实际触发接触并观察 sensor 读数的变化。

## 加噪声

MuJoCo 的 sensor 可以配置噪声，模拟真实传感器的非理想特性：

```xml
<sensor>
  <jointpos name="joint1_pos" joint="joint1" noise="0.001" cutoff="5"/>
</sensor>
```

- `noise`：高斯噪声的标准差。**注意**：MuJoCo 3.8.1 的仿真步**并不会自动**给读数加噪，`noise` 只是存进 `model.sensor_noise` 的元数据；要模拟噪声，得自己在 Python 端加（例如 `读数 + noise * np.random.randn(dim)`）。
- `cutoff`：对输出做对称裁剪，读数会被限制在 `[-cutoff, cutoff]` 范围内（设为 0 表示不裁剪）。

给仿真 sensor 加噪声是 sim2real 里常见的一步，往往用来缩小仿真读数和真实传感器之间的分布差距。

## 小结

- sensor 在 MJCF `<sensor>` 节里声明，运行时读数在 `data.sensordata` 里。
- 常用 sensor 包括 `jointpos`/`jointvel`（关节状态）、`touch`（触觉）、`force`/`torque`（力/力矩）、`framepos`/`framequat`（末端位姿）。
- 多个 sensor 的读数拼接在一维数组里，可以用 `data.sensor("name").data` 按名字读取。
- `noise` 是噪声标准差的元数据（仿真步不会自动加噪，需自己加），`cutoff` 把输出裁剪到 `[-cutoff, cutoff]`；两者都用来贴近真实传感器的行为。

## 动手练习

给一个 sensor 设 `noise="0.1"`，跑几步会发现读数**没有**波动（仿真步不自动加噪）；再读出 `model.sensor_noise`，自己在 Python 端按它加噪（`读数 + 0.1 * np.random.randn()`），统计波动的标准差是否约等于 0.1。

## 参考资料

- [MuJoCo Documentation: XML Reference（sensor）](https://mujoco.readthedocs.io/en/stable/XMLreference.html)
- [MuJoCo Documentation: Computation（sensors）](https://mujoco.readthedocs.io/en/stable/computation/index.html)

## 导航

- 上一节：[直接读状态](01-state-from-data.md)
- 返回上级：[观测与渲染](../04-observation-and-rendering.md)
- 下一节：[相机与多视角](03-camera-and-multiview.md)
