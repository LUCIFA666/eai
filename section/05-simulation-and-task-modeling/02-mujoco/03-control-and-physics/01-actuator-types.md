# 三类 actuator

前面几节我们一直在写 `data.ctrl[:] = ...`（第 1 章的正弦控制和运转主线一页的循环骨架里都有它），但一直没说清楚写进去的这个数到底是什么意思。先把 **actuator** 说清楚：它就是 MJCF 里定义的“驱动器”（可以理解成电机）；我们写进 `data.ctrl` 的控制量，正是经由对应的 actuator，被转换成施加到关节上的力。

那这个控制量到底代表力、目标角度、还是目标速度？这取决于 actuator 是哪种类型。MuJoCo 里最常用的是 **三类**：`motor` / `position` / `velocity`，区别就在这个语义上；除此之外还有一个底层、通用的 `<general>`，前面三类本质上都是它的“预设简写”。所以这一页先把三类讲清楚，最后再看 `general`。

## 本节目标

本节回答几个问题：

1. 最常用的三类 actuator，`motor` / `position` / `velocity`，分别是什么？写进 `ctrl` 的同一个数，在它们之下各代表力、目标角度还是目标速度？
2. `ctrlrange` 在做什么，为什么“关节追不上目标”时第一个要查它？
3. 更通用的 `<general>` 是怎么回事，为什么 Panda 用它？

## 三类各是什么

三类 actuator 的区别集中在一点：它们如何解释写进 `ctrl` 的那个数，也就是控制信号的**语义**不同。同一个 `ctrl` 值，换一类 actuator，物理含义就完全变了。

- `motor`（力控）：`ctrl` 直接作为施加到关节上的**力（或力矩）**，不做二次处理。
- `position`（位置伺服）：`ctrl` 是**目标角度（或位移）**，actuator 内部相当于一个 PD 控制器，根据位置误差自动算出力矩，把关节驱动到目标。
- `velocity`（速度伺服）：`ctrl` 是**目标速度**，actuator 根据速度误差出力，使关节维持该转速。

下面把三类放在一起跑（从左到右：`motor` / `position` / `velocity`）：同一根摆杆、同样的设置，只换 actuator 类型，行为就完全不同。`motor` 持续加力、越转越快，`position` 摆到目标角就停住，`velocity` 稳定匀速旋转。

<video src="../assets/mujoco-actuator-compare.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

选型也与此一一对应：关节的位置控制几乎都用 `position`；需要直接下发力矩、或想观察"力 → 加速度 → 速度 → 位置"这条物理链路时用 `motor`；轮子、传送带等要求恒定转速的场合用 `velocity`。

下面先用一个可直接复制运行的 `position` 最小例子上手代码，再逐类拆解（最后说明它们底层共同的 `general`）。

## 先跑一个最小例子

上面的三联对比是从外部看三类行为的差别，这里再亲手把 `position` 落到代码上。下面是一根单关节摆杆，配一个 `position`（位置伺服）actuator，把目标角度写进 `data.ctrl`，看关节怎么被拉过去（为专注看 actuator，先把重力关掉）：

```python
import mujoco

xml = """
<mujoco>
  <option gravity="0 0 0"/>
  <worldbody>
    <body>
      <joint name="hinge" type="hinge" axis="0 0 1"/>
      <geom type="capsule" size="0.03" fromto="0 0 0 0.3 0 0"/>
    </body>
  </worldbody>
  <actuator>
    <position name="servo" joint="hinge" kp="20" kv="2" ctrlrange="-3.14 3.14"/>
  </actuator>
</mujoco>
"""

model = mujoco.MjModel.from_xml_string(xml)
data = mujoco.MjData(model)

data.ctrl[0] = 1.0          # 用的是 position actuator，这个 1.0 是“目标角度”（rad）
for i in range(500):
    mujoco.mj_step(model, data)
    if i % 100 == 0:
        print(f"step {i:3d}: qpos = {data.qpos[0]:.3f} rad (target 1.0)")
```

运行输出如下，关节被位置伺服稳稳拉到目标 1.0：

```text
step   0: qpos = 0.003 rad (target 1.0)
step 100: qpos = 0.892 rad (target 1.0)
step 200: qpos = 0.990 rad (target 1.0)
step 300: qpos = 0.999 rad (target 1.0)
step 400: qpos = 1.000 rad (target 1.0)
```

跑起来的画面，就是关节被一点点拉到目标角度（这里关掉了重力以专注看伺服）：

<video src="../assets/mujoco-servo-pendulum.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

这段正好坐实了前面的说法：`position` 把 `ctrl` 当成目标角度，actuator 自己出力、把关节拉到 1.0 就停。下面逐类看它们具体怎么写、有哪些关键参数。

## motor：直接给力或力矩

`motor` 的写法最简单，给 joint 配一个 motor、设好力的范围 `ctrlrange` 即可：

```xml
<actuator>
  <motor name="motor1" joint="joint1" ctrlrange="-10 10"/>
</actuator>
```

```python
data.ctrl[0] = 5.0   # 直接施加 5 的力（转动关节是 N·m，平动关节是 N）
mujoco.mj_step(model, data)
```

写进 `ctrl` 的值原样变成关节力，中间不做任何反馈。常用属性也就两个：`ctrlrange` 限定输入范围，`gear` 把 `ctrl` 按倍数放大后再施加（相当于齿轮比，默认 1）。

要点在于 motor **没有位置或速度反馈**：给多大力就一直加多大力，因此它**不会自己停在某个角度**。恒定的 `ctrl` 在无重力时会让关节匀加速，有重力时则一直和重力较劲。想让关节稳稳停在目标位，得自己在 Python 端写控制律（最常见的就是 PD，见 [动手：写一个 PD 控制器](07-hands-on-control.md)）。也正因为“给的就是力”，它最适合底层力矩控制，以及用来理解“力 → 加速度 → 速度 → 位置”这条物理链路。

## position：把关节拉向目标角度

本页开头那个例子用的就是 `position`。它在 `motor` 之上内置了一个 PD 控制器，于是 `ctrl` 的含义从“力”变成了“目标位置”，由 `kp`、`kv` 两个增益自动算出该出多大力：

```xml
<actuator>
  <position name="pos1" joint="joint1" kp="100" kv="10" ctrlrange="-1.57 1.57"/>
</actuator>
```

```python
data.ctrl[0] = 0.785   # 目标角度 45°（转动关节单位是 rad，平动关节是 m）
mujoco.mj_step(model, data)
# actuator 内部：力 = kp * (目标 - 当前位置) - kv * 当前速度
```

两个增益分工明确：`kp` 是位置增益（刚度），决定“追得多猛”；`kv` 是速度增益（阻尼），决定“收得多稳”。`kp` 越大越“硬”地冲向目标，但太大会过冲甚至振荡；`kv` 越大越不容易振荡，但响应也越慢。`kp` 大、`kv` 小容易抖，`kp` 小、`kv` 大又慢吞吞，怎么配出“又快又不抖”要靠调，[动手：写一个 PD 控制器](07-hands-on-control.md) 会专门演示欠阻尼、临界阻尼、过阻尼三种手感。

position 的出力同样受 `forcerange` 约束：目标太远、算出的力被截断时，关节也会追不到目标（和后面 `ctrlrange` 那个坑同理）。如果接触过 Isaac Sim，它的 joint drive（用 stiffness/damping 把关节驱到目标）和这里的 position 是同一套思路，可以互相印证。

## velocity：保持目标速度

`velocity` 在内部维持的是速度而不是位置，`ctrl` 就是目标转速（或线速度），靠唯一的增益 `kv` 自动出力：

```xml
<actuator>
  <velocity name="vel1" joint="joint1" kv="10" ctrlrange="-3.14 3.14"/>
</actuator>
```

```python
data.ctrl[0] = 2.0   # 目标速度（转动关节单位是 rad/s，平动关节是 m/s）
mujoco.mj_step(model, data)
# actuator 内部：力 = kv * (目标速度 - 当前速度)
```

`kv` 越大，越“硬”地把当前速度拽向目标、达到目标转速越快。它适合轮子、传送带这类要“保持恒定转速”的场景，一般不太适合机械臂的位置控制。

要注意 velocity **只管速度、不管位置**：把 `ctrl` 设回 0 只是让关节减速停下，停在哪个角度并不确定。想精确停在某个位置，还得用 `position`。

## general：底层的通用 actuator

其实前面的 motor / position / velocity 都是 `<general>` 的**预设简写**，`<general>` 才是它们底层那个最灵活的形式。它不把 `ctrl` 的语义钉死成力、位置还是速度，而是让我们自己配置“控制量怎么一步步变成力”，所以几乎能表达各种驱动方式。

Panda 用的就是 `<general>`（下面这段就是 `panda.xml` 里的 `actuator1`，可用 `mjcf_inspect.py` 加载核对）：

```xml
<actuator>
  <general class="panda" name="actuator1" joint="joint1"
           gainprm="4500" biasprm="0 -4500 -450"
           dyntype="none" biastype="affine"/>
</actuator>
```

结合 `<default>` 里 `biastype="affine"`，这段定义的实际效果是：

```text
力 = gainprm[0] * ctrl + biasprm[0] + biasprm[1] * qpos + biasprm[2] * qvel
```

也就是一个**仿射（affine）函数**：力随 `ctrl` 线性变化，同时加上位置和速度的偏置项。对 Panda 来说，这正好凑成一个位置伺服：`gainprm[0]*ctrl` 把关节往目标推、`biasprm[1]*qpos` 把它往零位拉，两项合起来就是 `kp*(目标 - 当前)` 形式的恢复力。

不需要完全理解 `gainprm`、`biasprm` 的每个分量才能用 actuator。初学时，记住这一点就够了：`general` 的 `ctrl` 通常代表目标位置（取决于 `biastype`），内部像一个可调的伺服。

## ctrlrange 与饱和

每个 actuator 都可以设定 `ctrlrange`：

```xml
<general joint="joint1" ctrlrange="-2.8973 2.8973"/>
```

**超出范围的控制量会被截断（clamp）到最近的边界。** 不会报错，不会警告，就是静默地截断。举个例子，Panda 的 `joint4`，它对应 actuator 的 `ctrlrange` 是 `[-3.07, -0.07]`，并不包含 0，所以默认 `ctrl=0` 会被静默截到 -0.07。

这个截断在位置伺服里尤其要留意：如果 `ctrl` 被截了，关节也就到不了设定的目标角度。所以排查“关节为什么追不上目标”时，`ctrlrange` 往往是第一个值得查的地方。

## 各类速查表

| 类型 | ctrl 的语义 | 常用参数 | 适合场景 |
|---|---|---|---|
| `motor` | 力或力矩 | `ctrlrange`、`gear` | 底层力矩控制、理解物理过程 |
| `position` | 目标位置 | `kp`、`kv`、`ctrlrange` | 关节位置控制（最常见） |
| `velocity` | 目标速度 | `kv`、`ctrlrange` | 轮子、传送带 |
| `general` | 取决于 `biastype` | `gainprm`、`biasprm`、`dyntype` | 需要精细调参或特殊驱动模型时 |

## 小结

- `motor`：ctrl = 力，最直接。
- `position`：ctrl = 目标角度，actuator 内部做 PD 伺服。
- `velocity`：ctrl = 目标速度，适合持续转动。
- `general`：最灵活，Panda 用它通过仿射 biastype 实现位置伺服。
- `ctrlrange` 会静默截断，是排查“追不上目标”时第一个要查的值。

## 动手练习

查看 Panda 的 `actuator8`（夹爪）的 `ctrlrange` 是多少。提示：`[0, 255]` 不是物理单位（米/弧度），而是 Franka 真机沿用的指令刻度（整数 0~255 线性映射到手指 0~0.04m 的开度）；说说这样定有什么好处。

## 参考资料

- [MuJoCo Documentation: XML Reference（actuator）](https://mujoco.readthedocs.io/en/stable/XMLreference.html)
- [MuJoCo Documentation: Computation（actuation model）](https://mujoco.readthedocs.io/en/stable/computation/index.html)
- [MuJoCo Menagerie: Franka Emika Panda](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda)

## 导航

- 上一节：[控制与物理](../03-control-and-physics.md)
- 返回上级：[控制与物理](../03-control-and-physics.md)
- 下一节：[step 与流水线](02-step-and-pipeline.md)
