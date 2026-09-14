# Observation → Action 闭环

前面讲动作怎么发出去，本部分前两页讲相机、Lidar、IMU、接触和状态怎么读回来。这一页把两条线凑成一个回路——**读观测 → 决策 → 发动作 → 步进 → 再读观测**。这个最小闭环是后面"任务与数据"部分的地基：有了它，才谈得上记录回合、判定成功、采集数据集。

## 本节目标

本节围绕下面几个问题展开：

1. 观测到动作的闭环是哪五步在不断循环？
2. 在一个 step 里，`obs_t` 和 `action_t` 到底谁领先一步？
3. 搭这个闭环时，时间戳和对齐方面有哪些坑？

阅读这一页前，最好已经能单独发动作、单独读相机；这里要解决的是如何把两者串成一个能连续运行的回路。

## 闭环就是这五步在转

具身智能里几乎所有控制和数据采集，本质都是同一个回路在反复转：

<figure class="doc-figure">
<p class="doc-figure-title">observation → action 闭环</p>
<div class="figure-flow">
<div class="figure-node">① 读观测：joint_positions、相机 RGB / 深度、物体状态</div>
<div class="figure-node">② 决策：策略 / 控制器 / 运动生成，算出这一步的动作</div>
<div class="figure-node">③ 发动作：apply_action(ArticulationAction(...))</div>
<div class="figure-node">④ 步进：world.step(render=True) 推进物理与渲染</div>
<div class="figure-node">⑤ 对齐保存：step_index + obs + action 一起记录，回到 ①</div>
</div>
<p class="doc-figure-subtitle">控制页负责动作，观测页负责相机 / 传感器 / 状态；本页把它们接起来转。</p>
</figure>

## 最小闭环

把前面几页的零件拼起来：加载机器人和传感器 → reset → 预热 → 进入循环，每一步读状态和图、算一个动作、发出去、step、再对齐记录。

```python
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.robots import Robot
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.utils.nucleus import get_assets_root_path
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.sensors.camera import Camera

world = World()
world.scene.add_default_ground_plane()

assets_root = get_assets_root_path()
add_reference_to_stage(
    assets_root + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd", "/World/Franka"
)
robot = world.scene.add(Robot(prim_path="/World/Franka", name="franka"))
camera = Camera(prim_path="/World/Franka/panda_hand/cam", resolution=(256, 256))

world.reset()
camera.initialize()
for _ in range(8):            # 预热渲染，避免第一帧是黑的
    world.step(render=True)

home = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785, 0.04, 0.04])
robot.set_joint_positions(home)

log = []
for step_index in range(200):
    # ① observation：先读"动作之前"的状态和图
    q = robot.get_joint_positions()
    rgb = camera.get_rgb()

    # ② 决策：这里用一个占位策略（朝 home 收敛）；换成网络输出就是在跑 policy
    action_q = home

    # ③ action
    robot.apply_action(ArticulationAction(joint_positions=action_q))

    # ④ step：推进一拍物理与渲染
    world.step(render=True)

    # ⑤ 对齐保存：obs_t 与 action_t 同属本 step
    log.append({
        "step_index": step_index,
        "joint_positions": q.tolist(),
        "action": np.asarray(action_q).tolist(),
        "rgb_ok": rgb is not None and rgb.size > 0,
    })

simulation_app.close()
```

把 `action_q = home` 换成 IK / RMPflow 的输出，就是闭环跟踪一个目标；换成神经网络的输出，就是在仿真里跑一个 policy。回路结构不变。

## obs_t 和 action_t 谁领先一步

闭环里最容易出错、也最隐蔽的，是**时间对齐**。一个 step 里观测和动作的因果关系必须写清楚，常见约定是：

```text
obs_t  +  action_t  ->  obs_{t+1}
```

也就是：`obs_t` 是**执行动作之前**读到的状态，`action_t` 是基于它发出的动作，`obs_{t+1}` 是 step 之后的结果。上面脚本特意**先读 `q` / `rgb`、再 `apply_action`**，就是为了让记录的观测严格对应"动作前"。

如果你把 `image_t` 和 `action_{t-1}` 或 `action_{t+1}` 存到了一起，数据看起来没报错，但拿去做模仿学习时，模型看到的图和动作不是同一时刻的因果关系，会学到混乱的对应。所以**对齐方式必须固定并写进 metadata**，整个数据集保持一致，下游才能正确使用。

## 闭环里的几个坑

- **读太早**：相机要先 `step(render=True)` 预热，否则第一帧是黑的（见上一页）。reset 后丢掉前几帧再开始记录。
- **频率不一致**：物理可能 120 Hz、相机 30 Hz、控制 60 Hz，不是每个 action 都对应一张新图。要决定"每个控制步存一帧"还是"每隔几步存"，必要时记 `camera_frame_id` 标明图是否复用。
- **状态读在 step 后**：若把"动作前状态"误读成了 step 之后的状态，`obs_t` 实际成了 `obs_{t+1}`，对齐就错位了。
- **每条记录带上时间来源**：保存 `step_index`、`simulation_time`、`sensor_timestamp` 等，即使传感器频率不同，也能复原图、状态、动作之间的关系。

## 初学者常见误解

| 你以为 | 实际 | 正解 |
|---|---|---|
| 先 step 再读状态也一样 | 那读到的是 `obs_{t+1}`，和 `action_t` 错位 | 先读 obs、再 apply、最后 step |
| 每个动作都对应一张新图 | 相机帧率常低于物理，会复用上一帧 | 记 frame_id / 决定采样策略 |
| 闭环不跑 step 也能转 | 不 step 物理与渲染都不前进 | 每轮必须 `world.step()` |
| 对齐方式无所谓，能存就行 | obs/action 错位会毁掉模仿学习数据 | 固定 `obs_t+action_t→obs_{t+1}` 并写进 metadata |
| 第一帧就能记录 | reset 后渲染未稳定，易混入黑图 | 预热若干帧后再开始记录 |

## 小结

- 闭环 = 读观测 → 决策 → 发动作 → step → 对齐保存，循环往复；控制页和观测页正是这条回路上的零件。
- 最小闭环把机器人 + 相机加载好后，在循环里"先读 obs、再 apply_action、然后 step、最后对齐记录"。
- 必须固定并记录时间对齐约定（`obs_t + action_t → obs_{t+1}`），否则数据无法用于模仿学习。
- 注意预热黑帧、传感器与物理频率不一致、状态读取时机等坑，每条记录都带上时间来源。

## 参考资料

- NVIDIA Isaac Sim 5.1.0 Documentation, [Python Scripting and Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/index.html)
- Isaac Lab Documentation, [Sensors](https://isaac-sim.github.io/IsaacLab/main/source/overview/core-concepts/sensors/index.html)

## 导航

- 返回目录：[观测与传感器](../05-observation.md)
- 上一页：[RTX Lidar / IMU / 接触传感器](02-lidar-imu.md)
- 下一页：[任务、数据采集与合成数据](../06-task-and-data.md)
