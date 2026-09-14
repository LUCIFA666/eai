# 直接读状态

不是所有“观测”都需要在 MJCF 里声明 sensor。最常用的关节角、body 位置、末端坐标，`data` 对象上已经有现成的字段，直接读就行。

## 本节目标

本节把 `data` 上几个最常读的字段过一遍：

1. 关节角和速度、body 的世界位姿、site 位置，分别怎么读？
2. 读之前要不要先调一次 `mj_forward`？
3. 按下标和按名字访问，各适合什么场景？

## 读关节角与关节速度

关节位置和速度是最基础的观测，直接在 `data.qpos` 和 `data.qvel` 上读即可，不需要提前声明任何东西：

```python
import mujoco

model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

mujoco.mj_step(model, data)

# 读所有关节位置和速度
print(f"qpos = {data.qpos}")
print(f"qvel = {data.qvel}")

# 按名字读单个关节
print(f"joint1 angle = {data.joint('joint1').qpos[0]:.4f} rad")
print(f"joint1 velocity = {data.joint('joint1').qvel[0]:.4f} rad/s")
```

**要不要先刷新一次派生量？** 如果是初始化后第一次读（还没调过 `mj_step`），建议调一次 `mj_forward` 让派生量刷新。如果是循环里每次 `mj_step` 之后读，就不需要了，`mj_step` 内部已经跑完了正向运动学。

一个容易忽视的细节：`data.qpos` 和 `data.qvel` 返回的是 NumPy 视图，不是副本。如果想保存某一步的历史值，记得加 `.copy()`，否则所有"历史值"都会指向同一块内存，最终都变成最新值：

```python
history = []
for _ in range(100):
    mujoco.mj_step(model, data)
    history.append(data.qpos.copy())  # .copy() 很重要！
```

## 读 body 的世界位姿

每个 body 在世界坐标系里的位置和朝向可以直接读，不需要提前声明 sensor：

```python
hand = data.body("hand")
print(f"hand position:  {hand.xpos}")   # (3,)  世界坐标
print(f"hand quaternion: {hand.xquat}")  # (4,)  wxyz 顺序
print(f"hand rotation matrix:\n{hand.xmat}")  # (9,) 展平旋转矩阵，reshape(3,3) 当矩阵用
```

`xpos` 和 `xquat` 返回的是**世界坐标系**下的值，所有祖先 body 的位移和旋转都已经累积进去了。如果在 MJCF 里写 `<body pos="0 0 0.1">`，这是局部坐标；而 `data.body("name").xpos` 才是经过正向运动学后在世界坐标系里的最终位置。

选择用 `xquat`（四元数）还是 `xmat`（旋转矩阵）取决于下游算法。做 IK（逆运动学，根据末端位姿反解关节角）时矩阵往往更方便，做插值时四元数更自然。两者都是从同一个朝向算出来的，选顺手的用即可。

## 读 site 的位置与朝向

site 可以理解为"贴在 body 上的标记点"，它的世界位置通过 `data.site("name").xpos` 读取：

```python
# 在 MJCF 里定义了 <site name="tcp" pos="0 0 0.1"/>
tcp_pos = data.site("tcp").xpos
print(f"TCP world position: {tcp_pos}")
```

site 很适合用作末端执行器（TCP，工具中心点）的标记。它的位姿会自动跟随它所属的 body，只需要在 MJCF 里把它放在合适的位置即可。

对比 body 和 site：

| | body | site |
|---|---|---|
| 参与碰撞 | 否（body 本身没几何） | 否 |
| 有质量和惯性 | 有 | 无 |
| 渲染可见 | 否（除非挂了 geom） | 是（可渲染为小标记） |
| 适用于 | 构建运动学树、承载 geom/joint | 标记关注点（TCP、传感器安装点、腱路径点） |

## 下标 vs 名字

访问 body、joint、site 等对象有两种方式：

```python
# 方式 1：按下标
hand_pos = data.xpos[hand_id]    # 需要先查出 hand_id

# 方式 2：按名字（推荐）
hand_pos = data.body("hand").xpos
```

按名字访问的好处是代码更可读、不容易因为模型改动（增加了新 body 导致下标偏移）而悄悄出错。按名字查找有极微小的开销（内部是哈希表查找），但在绝大多数场景下这个开销可以忽略。

按下标更适合循环遍历（比如 `for i in range(model.nbody)`），因为这时候本来就不要名字。另外也可以用 `mujoco.mj_name2id` 先查出 ID，然后在下标访问里复用，这在每步需要访问大量对象时稍微快一点。

## 小结

- 最基本的观测，关节角、关节速度、body 位姿、site 位置，直接从 `data` 读即可，不需要声明传感器。
- `xpos` 和 `xquat` 返回的是世界坐标系中的值，所有祖先的变换都已累积。
- site 是轻量标记点，适合标注 TCP 等关注位置。
- 日常代码推荐按名字访问（更可读、更安全），循环遍历时按下标。

## 动手练习

给 Panda 的末端加一个 site，看看局部偏移换算到世界坐标会变成什么。复制一份 menagerie 的 `panda.xml`，找到 `<body name="hand" ...>` 这一行，在它下面（作为第一个子元素）加一行 `<site name="fingertip" pos="0 0 0.05" size="0.01"/>`，加载这份改过的模型、重置到 `home` 位姿，再比较 `data.site("fingertip").xpos` 和 `data.body("hand").xpos`：

- **home 位姿**：夹爪正好竖直朝下，局部的 `+z` 偏移会变成世界的 `-z`，两点差向量约 `[0, 0, -0.05]`，看着像“原样落在 z 上”（只是翻了个号）。
- 再弯几个关节让 hand 歪过来（比如 `data.qpos[0] += 0.7; data.qpos[3] += 0.8` 后再 `mj_forward`）：差向量变成约 `[0.027, 0.023, -0.035]`，三个轴都不为零，和局部的 `(0, 0, 0.05)` 完全对不上了。

两种姿态下，两点距离都约等于 `0.05`（局部偏移的模长）。要点就在这里：局部偏移经过 body 的世界旋转后，**方向会跟着 body 转、各轴分量一般和局部值对不上，唯一不变的是它的长度**。所以读末端位置要用 `data.site("...").xpos`（已经算好的世界坐标），而不是把局部 `pos` 当世界坐标用。

## 参考资料

- [MuJoCo Documentation: Python Bindings（named access / MjData）](https://mujoco.readthedocs.io/en/stable/python.html)
- [MuJoCo Documentation: Computation（xpos / xquat 等派生量）](https://mujoco.readthedocs.io/en/stable/computation/index.html)

## 导航

- 上一节：[观测与渲染](../04-observation-and-rendering.md)
- 返回上级：[观测与渲染](../04-observation-and-rendering.md)
- 下一节：[sensor 与 sensordata](02-sensors.md)
