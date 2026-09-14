# PyBullet

> 难度：[基础] | 预计用时：45 分钟
> 先修：[MuJoCo 心智模型](../02-mujoco/01-overview/02-mental-model.md) ⇢ [控制与物理](../02-mujoco/03-control-and-physics.md)

目标：用 PyBullet 的 `DIRECT` 模式跑通一个“加载平面和小方块，推进物理步，读取位置日志”的最小仿真实验，并判断它适合放在课程里的哪些任务上。

## 心智模型

PyBullet 可以先理解成一个很轻的物理沙盒：你用 Python 把 URDF 模型丢进去，设置重力，然后一帧一帧调用 `stepSimulation()`，引擎就把物体的位置、速度、接触和约束往前推进。它不像 Isaac Sim 那样把高质量渲染、传感器和 Omniverse 场景管理一起带进来，也不像 Gazebo 那样天然站在 ROS 2 系统集成的中心；它更像一块随手能拿起来的实验板，适合教学验证、RL baseline、快速检查 URDF 和控制逻辑。

本页只做一个小实验：把一个小方块放在离地 1 米的位置，让它在重力下落到平面上。这个例子没有机械臂、没有 reward、没有相机，但它抓住了 PyBullet 程序的主线：连接 physics server，加载模型，设置物理参数，推进 step，读取状态。如果这条线读顺了，后面再换成 Panda、KUKA、移动机器人或自定义 Gymnasium 环境，都只是往这条线上继续加层。

## 学习目标

读完本页后，你应该能：
- 解释 PyBullet 程序中 `connect`、`loadURDF`、`stepSimulation` 和状态读取之间的关系。
- 实现一个小于 40 行的 `DIRECT` 模式物理循环，并用高度变化验证仿真确实推进了。
- 判断 PyBullet 适合轻量教学和 RL 原型，而不适合承担所有高保真渲染或复杂真机部署任务。
- 根据日志识别几个常见失败信号：没有设置重力、找不到 URDF、GUI 与 DIRECT 模式混用、关节默认 motor 影响自由运动。

## 先给任务画面

不要一开始就把 PyBullet 讲成“Bullet 物理引擎的 Python 接口”。更好的入口是一个能直接想象的场景：

```text
物理世界里有一个无限平面 plane.urdf。
小方块 cube_small.urdf 的初始位置是 (0, 0, 1)。
世界重力是 (0, 0, -9.81)。
程序推进 240 个仿真步，并读取方块前后的 z 高度。
```

读者只要看到方块高度从 `1.0` 下降到接近平面，就能确认两件事：第一，物理循环真的在跑；第二，`getBasePositionAndOrientation()` 读到的是仿真状态，而不是静态配置文件。

## 核心 API 与变量

| 字段 / API | 示例值 | 角色 | 解释 |
|---|---:|---|---|
| `p.connect(p.DIRECT)` | `0` | 入口 | 创建无窗口 physics server，适合脚本、测试和服务器环境 |
| `pybullet_data.getDataPath()` | package path | 资源路径 | 让 `loadURDF` 找到内置的 `plane.urdf`、`cube_small.urdf` |
| `p.setGravity(0, 0, -9.81)` | `-9.81` | 物理参数 | 如果忘记设置，物体默认不会因为重力下落 |
| `p.loadURDF(...)` | body id | 模型加载 | 返回整数 id，后续读取状态和控制都靠它定位 body |
| `p.stepSimulation()` | 240 次 | 时间推进 | 每调用一次，物理引擎推进一个离散时间步 |
| `p.getBasePositionAndOrientation(cube_id)` | position, orientation | 状态读取 | 读取 base link 在世界坐标系下的位置和姿态 |

这张表的重点不是背 API 名字，而是看清数据流：Python 命令发给 physics server，server 更新世界状态，程序再把状态读回来。PyBullet 的易用性主要就来自这条链路足够短。

## 程序主线：从命令到状态

PyBullet 的程序结构可以用一条线概括：

```text
Python 脚本
  -> connect: 连接 physics server
  -> loadURDF: 把 plane / cube / robot 放进 world
  -> setGravity / setJointMotorControl2: 写入物理参数或控制命令
  -> stepSimulation: 推进一个离散时间步
  -> getBasePositionAndOrientation / getJointState: 读取最新状态
  -> 日志、reward、控制器或可视化
```

这条线和 MuJoCo 的 `model/data/step` 心智模型很像，但 PyBullet 更强调“命令式调用”：你不一定先拿到一个完整的内存结构再操作，而是不断向 physics server 发命令，拿回 body id、joint state、camera image 或 contact point。写教学脚本时，这种风格很友好，因为每一步都可以打印和断言；写大型系统时，也要更小心地管理 id、模式和状态重置。

## Body、Joint、Link 怎么编号

一旦从小方块换成机器人，最容易卡住的不是物理公式，而是“我要控制的是哪个关节”。PyBullet 的索引习惯可以先记成下面这张表：

| 概念 | PyBullet 里的常见表示 | 读法 |
|---|---|---|
| body | `robot_id = p.loadURDF(...)` | 一个 URDF 加载后返回一个整数 id |
| base | link index `-1` | 机器人根部，不算普通 link |
| joint | `0 ... p.getNumJoints(robot_id)-1` | 每个可查询关节都有一个 joint index |
| link | 通常和对应 joint index 一起出现 | 读取 link state、接触点时会用到 |
| joint state | `p.getJointState(robot_id, joint_index)` | 返回位置、速度、反作用力和 motor torque 等信息 |

调试机器人时，第一步通常不是直接写控制器，而是先把关节表打印出来：

```python
for joint_index in range(p.getNumJoints(robot_id)):
    info = p.getJointInfo(robot_id, joint_index)
    name = info[1].decode("utf-8")
    joint_type = info[2]
    print(joint_index, name, joint_type)
```

这个小片段能帮你避免两个常见错误：把 link index 当 joint index 用，或者凭 URDF 文件里的视觉顺序猜关节编号。真实项目里，控制器、观测向量和动作空间都应该从这张关节表出发，而不是从“我觉得第 3 个应该是手腕”出发。

## 最小可运行例子

本页不把 `pybullet` 加进课程固定依赖；如果你想运行下面的实验，可以在当前环境里额外安装：

```bash
pip install pybullet
```

下面脚本采用 `DIRECT` 模式，所以不会弹出窗口，适合放在课程实验、CI 或服务器里跑。

```python
# 用 PyBullet 的 DIRECT 模式验证最小物理循环：加载、步进、读取状态。
import pybullet as p
import pybullet_data

client_id = p.connect(p.DIRECT)

try:
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)

    plane_id = p.loadURDF("plane.urdf")
    cube_id = p.loadURDF("cube_small.urdf", [0, 0, 1])

    initial_pos, _ = p.getBasePositionAndOrientation(cube_id)

    for _ in range(240):
        p.stepSimulation()

    final_pos, _ = p.getBasePositionAndOrientation(cube_id)

    initial_z = round(initial_pos[2], 3)
    final_z = round(final_pos[2], 3)

    assert plane_id >= 0
    assert cube_id >= 0
    assert final_z < initial_z
    assert final_z < 0.10

    print("initial_z:", initial_z)
    print("final_z:", final_z)
finally:
    p.disconnect(client_id)

# 示例输出，不同版本可能有微小差异:
# initial_z: 1.0
# final_z: 0.025
```

这段代码的设计意图是把 PyBullet 的核心闭环压到最小：先连接，再加载，再推进，再验收。`assert final_z < initial_z` 验证方块确实在重力下落；`assert final_z < 0.10` 验证它已经接近平面，而不是只下降了一点点。教程里保留这些断言很重要，因为它们把“仿真是否真的工作”变成了可检查的失败信号。

## 代码走读

不要把上面的代码逐行翻译成“第 1 行导入 pybullet”。更有用的阅读路线是看四个节点：入口、输入、核心循环、输出。

### 1. 先看入口

```python
client_id = p.connect(p.DIRECT)
```

PyBullet 的第一步是连接 physics server。`DIRECT` 表示不创建 GUI 窗口，命令直接发给同一进程里的物理引擎；如果你在教学脚本、远程服务器或自动测试里跑，这是最稳的入口。想看可视化时可以换成 `p.GUI`，但那时程序就会依赖本地显示环境，不能再假设它适合无头运行。

### 2. 再看输入

```python
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.81)

plane_id = p.loadURDF("plane.urdf")
cube_id = p.loadURDF("cube_small.urdf", [0, 0, 1])
```

这一段定义了仿真世界的最小输入：资源路径、重力、平面、小方块和初始位置。`loadURDF` 返回的是 body id，不是模型对象本身；后面要读取方块位置、控制关节或检查碰撞，都要用这个 id 找回对应 body。

### 3. 核心循环只有一步

```python
for _ in range(240):
    p.stepSimulation()
```

`stepSimulation()` 是 PyBullet 程序的心跳。没有这一步，加载出来的世界只是静止在初始状态；调用它 240 次，物理引擎才会持续积分速度、处理接触，并把方块从空中推进到平面附近。

### 4. 最后看输出

```text
initial_z: 1.0
final_z: 0.025
```

输出不是“程序能运行”这么模糊，而是一个可以判断的状态变化：方块初始在 1 米高，最后接近平面。读者看到这个日志后，应该能回答两个问题：第一，重力有没有生效？第二，step 循环有没有推进足够长？如果答案不确定，就要回到输入和核心循环检查。

## 常见失败信号

| 现象 | 最可能原因 | 优先检查 |
|---|---|---|
| `initial_z` 和 `final_z` 几乎一样 | 忘记 `p.setGravity(...)`，或没有调用 `p.stepSimulation()` | 重力设置、循环步数 |
| `Cannot load URDF file` | 没有设置 `pybullet_data` 搜索路径，或文件名写错 | `p.setAdditionalSearchPath(...)` |
| 脚本在服务器或 CI 中卡住 | 使用了 `p.GUI`，但环境没有可用显示窗口 | 改用 `p.DIRECT` |
| 机器人关节不按预期自由运动 | URDF 里的 revolute / prismatic joint 默认可能带 motor | 检查 `setJointMotorControl2`，必要时将 force 设为 0 |
| 结果和教程数字略有差异 | PyBullet 版本、URDF 尺寸或求解器参数不同 | 看趋势和断言，不只盯最后一位小数 |

失败案例也可以写进最小脚本里。例如下面这段去掉重力后，方块不会主动下落：

```python
# 错误示例：没有设置重力，方块会停在初始高度附近。
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.loadURDF("plane.urdf")
cube_id = p.loadURDF("cube_small.urdf", [0, 0, 1])

for _ in range(240):
    p.stepSimulation()

final_pos, _ = p.getBasePositionAndOrientation(cube_id)
print(round(final_pos[2], 3))

# 预期输出:
# 1.0
```

这个失败案例的价值在于提醒读者：PyBullet 不会替你自动补齐物理世界的全部条件。模型加载只是第一步，重力、时间步、控制器、接触参数和日志检查都要明确写出来。

## 第二个最小例子：控制一个关节

方块下落只能说明物理循环能跑。机器人任务还要多一步：把动作写到关节 motor，再从 `getJointState` 里读回关节位置。下面用 `pybullet_data` 里自带的 KUKA iiwa 模型控制第 0 个关节转向 `0.5 rad`。

```python
# 用 PyBullet 的 position motor 控制 KUKA iiwa 的第 0 个关节。
import pybullet as p
import pybullet_data

client_id = p.connect(p.DIRECT)

try:
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)

    robot_id = p.loadURDF("kuka_iiwa/model.urdf", useFixedBase=True)
    joint_index = 0
    target_q = 0.5

    assert p.getNumJoints(robot_id) > joint_index

    initial_q = p.getJointState(robot_id, joint_index)[0]

    p.setJointMotorControl2(
        bodyUniqueId=robot_id,
        jointIndex=joint_index,
        controlMode=p.POSITION_CONTROL,
        targetPosition=target_q,
        force=200,
    )

    for _ in range(240):
        p.stepSimulation()

    final_q = p.getJointState(robot_id, joint_index)[0]

    assert abs(final_q - target_q) < abs(initial_q - target_q)

    print("num_joints:", p.getNumJoints(robot_id))
    print("initial_q:", round(initial_q, 3))
    print("final_q:", round(final_q, 3))
finally:
    p.disconnect(client_id)

# 示例输出，不同版本可能有微小差异:
# num_joints: 7
# initial_q: 0.0
# final_q: 0.5
```

这段代码和方块例子的差别只有一层：`cube_id` 换成了 `robot_id`，base 状态读取换成了 joint 状态读取，`setGravity` 之外又多了一个 `setJointMotorControl2`。这就是 PyBullet 适合入门教学的地方：机器人控制的最小闭环可以在几十行里说清楚。

不过，这个例子也暴露了 PyBullet 的一个坑：`POSITION_CONTROL` 是引擎内部帮你做的 motor 控制，不等于你自己实现了低层 torque controller。做强化学习或控制实验时，要明确动作到底是目标位置、目标速度还是力矩；如果要直接做 torque control，通常还需要先关闭默认 motor，再用 `TORQUE_CONTROL` 写入力矩。

## PyBullet 控制能不能改成 MuJoCo

可以，但不要把它理解成“把一行 `p.setJointMotorControl2(...)` 机械替换成一行 MuJoCo API”。更稳的做法是先把控制语义抽出来：控制的是哪个关节、动作是目标位置还是速度/力矩、关节名和动作顺序是什么，然后再分别落到 PyBullet 或 MuJoCo 的后端 API 上。

公众号文章里提到的 RoboVerse / MetaSim 采用的就是这种中间层思路。本地已经把相关上游源码摘录放在同级目录：

```text
03-pybullet-code/
├── README-notes.md
└── official_metasim_control_path/
    └── metasim/
        ├── sim/base.py
        ├── sim/pybullet/pybullet.py
        ├── sim/mujoco/mujoco.py
        ├── utils/state.py
        └── test/sim/test_dof_control.py
```

这条链路的核心字段是 `dof_pos_target`。上层任务不用直接关心当前后端是 PyBullet 还是 MuJoCo，而是提交统一动作：

```python
actions = [
    {
        "franka": {
            "dof_pos_target": {
                "panda_joint1": 0.5,
                "panda_joint2": -0.2,
            }
        }
    }
]

handler.set_dof_targets(actions)
```

进入 PyBullet 后端时，MetaSim 会按 PyBullet 的关节顺序取出目标值，再调用：

```python
p.setJointMotorControlArray(
    object,
    range(action.shape[0]),
    controlMode=p.POSITION_CONTROL,
    targetPositions=action,
)
```

进入 MuJoCo 后端时，同一个 `dof_pos_target` 会按 MuJoCo 的 actuator 写进控制数组：

```python
self.physics.data.ctrl[actuator.id] = joint_pos
```

所以，如果你给一个 PyBullet 项目，要改成 MuJoCo，真正要转换的是四层内容：

| PyBullet 项目里的内容 | MuJoCo 版本里要对应到 |
|---|---|
| `loadURDF(...)` 加载的模型 | MJCF/XML 模型，或先从 URDF 转换并校对 actuator |
| `setJointMotorControl2/Array` | `data.ctrl[...]`、`data.qpos[...]` 或 MuJoCo actuator target |
| `getJointState(...)` | `data.qpos`、`data.qvel`、joint / actuator 索引 |
| `stepSimulation()` | `mujoco.mj_step(model, data)` |

最容易自动化的是“关节目标位置”这种动作接口；最需要人工检查的是模型转换、actuator 配置、关节顺序、碰撞几何和控制增益。课程里把 MetaSim 这段源码摘出来，不是为了直接运行它，而是为了让你看到一个真实框架如何把 PyBullet 和 MuJoCo 都接到同一套 `set_dof_targets` 语义下面。

## 从 PyBullet 到 Gymnasium 环境

很多机器人学习代码不会直接把 PyBullet 调用散落在训练脚本里，而是把它包成一个 `gymnasium.Env`。包装后的数据流通常是：

```text
reset()
  -> resetSimulation / loadURDF
  -> 设置初始关节、物体位置、目标位置
  -> 返回 observation

step(action)
  -> action 转成 setJointMotorControl2 或外力
  -> 连续调用若干次 stepSimulation
  -> 读取 joint state / body pose / contact
  -> 计算 reward、terminated、truncated、info
```

这层包装的关键不是“继承一个类”本身，而是把仿真器状态和学习接口分开。PyBullet 负责推进世界，Gymnasium 负责规定 `observation`、`action`、`reward` 和 episode 边界。读别人写的 PyBullet RL 环境时，可以按下面四个问题拆：

| 问题 | 去哪里看 |
|---|---|
| 每个 episode 怎么重置？ | `reset()` 里是否重新加载模型、随机化目标、重置关节 |
| action 是什么语义？ | `step(action)` 里是位置控制、速度控制还是力矩控制 |
| observation 包含什么？ | 是否包含关节、物体位姿、目标、接触或图像 |
| reward 有没有泄漏信息？ | reward 用到的量是否也出现在 observation，是否符合任务设定 |

如果这四个问题答不上来，先不要急着调算法。很多“RL 不收敛”的问题，本质上是环境包装没有讲清楚：动作尺度太大、episode 没有正确 reset、目标坐标系前后不一致，或者 reward 和观测定义互相打架。

## 什么时候选 PyBullet

| 任务 | PyBullet 是否合适 | 判断理由 |
|---|---|---|
| 教学中快速演示 URDF、接触、关节控制 | 合适 | 安装轻、Python API 短、最小例子容易复现 |
| 搭一个轻量 RL baseline 或 Gymnasium 环境 | 合适 | 很多历史基线和机器人学习环境曾围绕它构建 |
| 精细调接触动力学并追求稳定高性能训练 | 谨慎 | 常需要和 MuJoCo、Isaac Lab 等方案比较 |
| ROS 2 系统集成、传感器插件、仿真到真机链路 | 通常不作为首选 | Gazebo 更贴近 ROS 生态的系统测试 |
| 高质量视觉渲染、合成数据、大规模 GPU 场景 | 通常不作为首选 | Isaac Sim / Isaac Lab 更适合这类任务 |

所以，本课程里遇到 PyBullet 时，不要只问“它强不强”，而要问“它能不能让这个教学问题尽快变成可运行脚本”。如果答案是检查 URDF、写一个最小控制循环、复现一个旧 RL baseline，它往往很顺手；如果答案是高保真视觉、复杂传感器或成规模训练，就应该认真比较其他仿真栈。

## 自检练习

读完本页后，建议用 10 分钟做三个小改动：

1. 把方块例子里的初始高度从 `[0, 0, 1]` 改成 `[0, 0, 2]`，观察 `final_z` 是否仍然接近平面。
2. 把 step 次数从 `240` 改成 `30`，解释为什么方块还没落到底。
3. 把 KUKA 例子里的 `target_q` 改成 `-0.5`，确认 `final_q` 会朝新的目标方向移动。

每个练习都应该有一个可以写进日志的判断标准，而不是只看“窗口里动没动”。这是学习仿真器最重要的习惯：可视化帮助建立直觉，日志和断言负责验收。

## 参考入口

- 官方仓库：[bulletphysics/bullet3](https://github.com/bulletphysics/bullet3)
- 官方 Quickstart：[PyBullet Quickstart Guide](https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet_quickstart_guide/PyBulletQuickstartGuide.md.html)

## 导航

- 上一节：[Genesis](02-genesis.md)
- 返回上级：[其他仿真生态](../06-other-simulation-ecosystems.md)
- 下一节：[Gazebo](04-gazebo.md)
