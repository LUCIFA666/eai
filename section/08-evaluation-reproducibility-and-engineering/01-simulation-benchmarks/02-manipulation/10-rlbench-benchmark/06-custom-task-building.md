# 11.6 自定义任务构建

## 目标

前面几节已经介绍了 RLBench 的环境配置、任务结构、demonstration 数据以及 policy 训练评测。最后这一节关注一个更深入的问题：如果现有任务不满足研究需求，如何在 RLBench 中构建一个新的机器人操作任务？

读完本节后，你应该能够回答下面几个问题：

```text
RLBench 中一个自定义任务由哪些文件组成？
Task class 里通常需要写哪些方法？
success condition 是怎么定义的？
waypoints 和 demonstration 有什么关系？
如何测试一个自定义任务能否 reset、执行和生成 demos？
```

简单来说，自定义 RLBench 任务需要同时考虑两部分：

```text
仿真场景文件：放置物体、机器人、waypoints、传感器等
Python task class：定义任务逻辑、variation、语言描述和成功条件
```

也就是说，RLBench 的任务不是只写一段 Python 代码就完成了。它同时依赖 CoppeliaSim 场景中的对象命名、waypoints 和 Python 代码中的任务逻辑。


## 自定义任务的基本组成

一个 RLBench 任务通常可以拆成下面几部分：

| 组成 | 作用 |
| --- | --- |
| 场景文件 | 在 CoppeliaSim 中保存物体、目标区域、waypoints、传感器等 |
| Task Python 类 | 描述任务初始化、variation、语言描述和成功条件 |
| Waypoints | 用于 motion planner 生成专家 demonstration |
| Success condition | 判断任务是否成功 |
| Variation | 同一个任务下的不同目标或场景变化 |
| Language descriptions | 给 policy 或 VLA 使用的任务描述 |

可以把自定义任务理解成：

```text
场景中有什么
-> 每次 reset 怎么变化
-> 机器人应该做什么
-> 怎么判断成功
-> 怎么生成专家演示
```

这几个问题都回答清楚后，一个 RLBench task 才算完整。


## 任务文件放在哪里

RLBench 官方任务通常位于：

```text
RLBench/rlbench/tasks/
```

一个任务一般会对应一个 Python 文件，例如：

```text
reach_target.py
open_drawer.py
push_button.py
```

自定义任务也可以放在类似位置，例如：

```text
RLBench/rlbench/tasks/press_colored_button.py
```

同时，任务还需要对应的 CoppeliaSim 场景资源。不同版本 RLBench 的目录组织可能略有差异，但一般都会有 task design 或 task scenes 相关目录，用来保存 `.ttt` 场景文件。

如果只是学习任务结构，建议先不要从零创建全新场景，而是复制一个已有任务进行修改：

```bash
cd $RLBENCH_ROOT/RLBench/rlbench/tasks
cp reach_target.py my_reach_target.py
```

然后在这个基础上逐步改任务描述、物体名称和成功条件。


## 一个 Task class 的基本结构

一个 RLBench task 通常继承自 `Task`，并实现几个核心方法：

```python
from rlbench.backend.task import Task

class MyTask(Task):

    def init_task(self):
        pass

    def init_episode(self, index: int):
        pass

    def variation_count(self):
        return 1
```

这几个方法可以这样理解：

| 方法 | 作用 |
| --- | --- |
| `init_task()` | 任务第一次加载时执行，用来获取场景对象、注册成功条件 |
| `init_episode(index)` | 每次 reset episode 时执行，用来设置 variation 并返回语言描述 |
| `variation_count()` | 返回这个任务有多少种 variation |
| success condition | 通常在 `init_task()` 中注册 |
| waypoints | 通常在 CoppeliaSim 场景文件中设置，用于生成 demonstrations |

最小理解是：

```text
init_task()：这个任务有哪些对象，成功条件是什么
init_episode(index)：这一次 episode 是哪个 variation，语言描述是什么
variation_count()：这个任务一共有多少种变化
```

## init_task：注册对象和成功条件

`init_task()` 一般负责从场景中找到物体、目标区域或传感器，并注册成功条件。

例如，一个“把物体放到目标区域”的任务，可能需要：

```text
物体 object
目标区域 target area
检测传感器 success sensor
```

教学版代码可以写成：

```python
from rlbench.backend.task import Task
from rlbench.backend.conditions import DetectedCondition
from pyrep.objects.shape import Shape
from pyrep.objects.proximity_sensor import ProximitySensor


class PutBlockInTarget(Task):

    def init_task(self):
        self.block = Shape('block')
        self.success_sensor = ProximitySensor('success_sensor')

        self.register_success_conditions([
            DetectedCondition(self.block, self.success_sensor)
        ])

    def init_episode(self, index: int):
        return ['put the block in the target area']

    def variation_count(self):
        return 1
```

这段逻辑可以理解为：

```text
找到场景中的 block
找到 success_sensor
当 block 被 success_sensor 检测到时，任务成功
```

这里的对象名称必须和 CoppeliaSim 场景文件中的对象名称一致。如果场景里没有叫 `block` 或 `success_sensor` 的对象，任务加载时就会报错。


## init_episode：设置 variation 和语言描述

`init_episode(index)` 会在每次 reset 当前任务时调用。它通常负责两件事：

```text
根据 index 设置当前 variation
返回当前任务的语言描述
```

例如，一个按不同颜色按钮的任务可以写成：

```python
COLORS = ['red', 'green', 'blue']


def init_episode(self, index: int):
    color = COLORS[index]

    # 这里可以根据 color 改变目标按钮、颜色或位置
    # 具体操作依赖场景对象和 PyRep API

    return [f'press the {color} button']
```

对应：

```python
def variation_count(self):
    return len(COLORS)
```

这样 RLBench 就知道这个任务有 3 个 variation：

```text
variation 0: press the red button
variation 1: press the green button
variation 2: press the blue button
```

语言描述对于 VLA 或语言条件 policy 很重要。因为模型不仅要看图像，还需要知道这次目标是什么。


## variation 的作用

`variation` 不是简单的数据增强，而是 RLBench 中组织任务变化的核心机制。

常见 variation 包括：

| Variation 类型 | 例子 |
| --- | --- |
| 目标颜色变化 | 按红色按钮、绿色按钮、蓝色按钮 |
| 目标位置变化 | 把物体放到左边、右边、中间 |
| 目标物体变化 | 拿起杯子、拿起方块、拿起瓶子 |
| 初始状态变化 | 抽屉半开、物体位置随机 |
| 语言描述变化 | 同一目标用不同说法描述 |

variation 的意义在于测试模型是否真的理解任务，而不是只记住固定轨迹。


## success condition：如何判断任务成功

success condition 是 RLBench 任务中非常关键的一部分。它决定了 episode 是否完成。

常见成功条件包括：

| 成功条件 | 含义 |
| --- | --- |
| 物体被传感器检测到 | 例如物体进入目标区域 |
| 夹爪抓住物体 | 例如成功抓取目标 |
| 关节达到某个角度 | 例如抽屉被拉开、门被打开 |
| 多个条件同时满足 | 例如拿起物体并放入容器 |
| 没有抓着任何东西 | 例如任务结束时夹爪为空 |

最常见的是基于 proximity sensor 的条件：

```python
from rlbench.backend.conditions import DetectedCondition

self.register_success_conditions([
    DetectedCondition(self.block, self.success_sensor)
])
```

它的含义是：

```text
当 block 被 success_sensor 检测到时，任务成功
```

如果任务需要多个条件同时成立，可以注册多个 condition。比如：

```python
self.register_success_conditions([
    DetectedCondition(self.block, self.success_sensor),
    NothingGrasped(self.robot.gripper)
])
```

这表示：

```text
物体到达目标区域
并且夹爪没有继续抓着物体
```

具体可用的 condition 类型可以参考 RLBench 官方任务代码。学习自定义任务时，最好的方式是先打开几个已有任务，看它们如何定义成功条件。


## Waypoints：专家演示从哪里来

RLBench 的 demonstration 通常依赖 waypoints。waypoints 可以理解成专家轨迹中的关键路径点。

例如一个“拿起方块放到目标区域”的任务，可能需要：

```text
waypoint0：移动到方块上方
waypoint1：下降到抓取位置
waypoint2：闭合夹爪
waypoint3：移动到目标区域上方
waypoint4：下降放置
waypoint5：打开夹爪
```

motion planner 会根据这些 waypoints 生成连续轨迹，从而得到 expert demonstration。

所以如果一个自定义任务可以 reset，但 `get_demos()` 失败，很可能不是 task class 的问题，而是 waypoints 或 motion planning 出了问题。

常见原因包括：

| 问题 | 说明 |
| --- | --- |
| waypoint 命名不符合要求 | RLBench 找不到需要的 waypoint |
| waypoint 位置不可达 | 机械臂无法规划到该点 |
| waypoint 离物体太远 | 抓取或放置动作失败 |
| 中途发生碰撞 | motion planner 无法生成有效路径 |
| success condition 不匹配 | 演示执行完也无法触发成功 |

因此，自定义任务时要同时检查 Python 逻辑和 CoppeliaSim 场景中的 waypoints。


## CoppeliaSim 场景中要注意什么

在 CoppeliaSim 中构建任务场景时，要特别注意对象命名。Python task class 会通过名称查找场景对象，例如：

```python
Shape('block')
ProximitySensor('success_sensor')
```

这要求场景里必须存在同名对象：

```text
block
success_sensor
waypoint0
waypoint1
...
```

建议命名时遵循下面规则：

| 对象 | 命名建议 |
| --- | --- |
| 主要操作物体 | `block`、`button`、`cube` |
| 目标区域 | `target`、`target_area` |
| 成功传感器 | `success_sensor` |
| 路径点 | `waypoint0`、`waypoint1`、`waypoint2` |
| 临时参考点 | `spawn_boundary`、`target_boundary` |

不要随意改已有对象名称，否则 Python 代码可能找不到对象。

---

## 自定义任务的最小开发流程

建议按下面顺序开发自定义任务：

```text
1. 复制一个已有任务
2. 修改 Python task class 名称和文件名
3. 在 CoppeliaSim 中准备对象、传感器和 waypoints
4. 在 init_task() 中获取对象并注册 success condition
5. 在 init_episode() 中返回语言描述
6. 先测试 reset()
7. 再测试 step()
8. 最后测试 get_demos()
```

不要一开始就写复杂任务。先让一个最小任务能成功 reset 和判断 success，再逐渐加 variation 和随机化。


## 测试 1：能否 reset

自定义任务写好后，先测试能否加载和 reset。

示例脚本：

```bash
cat > test_custom_task_reset.py <<'PY'
from rlbench.environment import Environment
from rlbench.action_modes.action_mode import MoveArmThenGripper
from rlbench.action_modes.arm_action_modes import JointVelocity
from rlbench.action_modes.gripper_action_modes import Discrete
from rlbench.observation_config import ObservationConfig

# 这里替换成你自己的任务类
from rlbench.tasks.my_task import MyTask


action_mode = MoveArmThenGripper(
    arm_action_mode=JointVelocity(),
    gripper_action_mode=Discrete()
)

obs_config = ObservationConfig()
obs_config.set_all(False)
obs_config.front_camera.rgb = True

env = Environment(
    action_mode=action_mode,
    obs_config=obs_config,
    headless=True
)

env.launch()

task = env.get_task(MyTask)

descriptions, obs = task.reset()

print("Descriptions:", descriptions)
print("Reset ok")

env.shutdown()
PY
```

运行：

```bash
python test_custom_task_reset.py
```

如果这一步失败，优先检查：

```text
任务类是否能 import
文件名和类名是否正确
CoppeliaSim 场景文件是否存在
Shape / Sensor 名称是否和场景一致
```


## 测试 2：能否 step

reset 成功后，可以测试环境能否接收 action：

```bash
cat > test_custom_task_step.py <<'PY'
import numpy as np

from rlbench.environment import Environment
from rlbench.action_modes.action_mode import MoveArmThenGripper
from rlbench.action_modes.arm_action_modes import JointVelocity
from rlbench.action_modes.gripper_action_modes import Discrete
from rlbench.observation_config import ObservationConfig

from rlbench.tasks.my_task import MyTask


action_mode = MoveArmThenGripper(
    arm_action_mode=JointVelocity(),
    gripper_action_mode=Discrete()
)

obs_config = ObservationConfig()
obs_config.set_all(False)
obs_config.front_camera.rgb = True

env = Environment(
    action_mode=action_mode,
    obs_config=obs_config,
    headless=True
)

env.launch()

task = env.get_task(MyTask)
descriptions, obs = task.reset()

for t in range(10):
    # 这里只是随机 / 零动作测试接口，不代表能完成任务
    action = np.zeros(8, dtype=np.float32)
    obs, reward, terminate = task.step(action)
    print(f"step={t}, reward={reward}, terminate={terminate}")

    if terminate:
        break

env.shutdown()
PY
```

运行：

```bash
python test_custom_task_step.py
```

如果 step 时报 action shape 错误，说明你的 action 维度和 action mode 不匹配。


## 测试 3：能否生成 demonstration

最后测试 `get_demos()`：

```bash
cat > test_custom_task_demo.py <<'PY'
from rlbench.environment import Environment
from rlbench.action_modes.action_mode import MoveArmThenGripper
from rlbench.action_modes.arm_action_modes import JointVelocity
from rlbench.action_modes.gripper_action_modes import Discrete
from rlbench.observation_config import ObservationConfig

from rlbench.tasks.my_task import MyTask


action_mode = MoveArmThenGripper(
    arm_action_mode=JointVelocity(),
    gripper_action_mode=Discrete()
)

obs_config = ObservationConfig()
obs_config.set_all(False)
obs_config.front_camera.rgb = True
obs_config.joint_positions = True
obs_config.gripper_open = True

env = Environment(
    action_mode=action_mode,
    obs_config=obs_config,
    headless=True
)

env.launch()

task = env.get_task(MyTask)

demos = task.get_demos(
    amount=1,
    live_demos=True
)

print("Number of demos:", len(demos))
print("Demo length:", len(demos[0]))

env.shutdown()
PY
```

运行：

```bash
python test_custom_task_demo.py
```

如果 reset 和 step 都正常，但 demo 生成失败，重点检查 waypoints。


## 一个完整任务的开发检查表

自定义任务写完后，可以按下面清单检查：

| 检查项 | 是否完成 |
| --- | --- |
| Python 文件放在 `rlbench/tasks/` 下 |  |
| 任务类继承自 `Task` |  |
| 实现了 `init_task()` |  |
| 实现了 `init_episode(index)` |  |
| 实现了 `variation_count()` |  |
| 返回了清晰的语言描述 |  |
| 场景中存在所有 Python 代码引用的对象 |  |
| 注册了 success condition |  |
| waypoints 命名正确 |  |
| waypoints 位置可达 |  |
| `task.reset()` 可以成功运行 |  |
| `task.step(action)` 可以成功运行 |  |
| `task.get_demos()` 可以成功生成专家轨迹 |  |

如果这些都通过，这个任务基本就可以进入后续数据生成和 policy 训练阶段。


## 常见错误

### 1. 找不到对象

报错类似：

```text
Object does not exist: block
```

通常是因为 Python 中写了：

```python
Shape('block')
```

但 CoppeliaSim 场景里没有叫 `block` 的对象。

解决方法：

```text
检查场景对象名称
检查大小写
检查对象是否在正确 scene 中
```

### 2. reset 可以，demo 生成失败

这通常和 waypoints 有关。可能是：

```text
waypoint 不存在
waypoint 不可达
waypoint 路径中发生碰撞
夹爪没有正确开合
success condition 没有触发
```

建议先打开 CoppeliaSim 可视化检查 waypoint 位置，再减少任务复杂度。

### 3. success condition 一直不触发

如果机器人看起来完成了任务，但 reward 一直为 0，通常是 success condition 设置不对。

可能原因：

```text
sensor 位置不对
检测对象不是目标物体
需要多个条件但只满足了一个
任务结束时夹爪状态不符合要求
```

这种问题要回到 CoppeliaSim 场景里看传感器位置和检测范围。

### 4. variation index 越界

如果 `variation_count()` 返回 3，但 `init_episode(index)` 里只处理了 0 和 1，就可能在采样 variation 2 时出错。

建议写 variation 时保持：

```text
variation_count()
和
init_episode(index)
逻辑一致
```

### 5. 语言描述和任务目标不一致

例如 description 写的是：

```text
press the red button
```

但场景中目标实际设置成了蓝色按钮。这会影响语言条件 policy 的训练，尤其是 VLA 模型。

---

## 自定义任务和 policy 训练的关系

自定义任务不是只为了“能跑一个新场景”，更重要的是它会影响后续数据和训练。

一个新任务会决定：

| 影响项 | 说明 |
| --- | --- |
| observation 分布 | 模型会看到什么场景和物体 |
| action 分布 | 专家轨迹如何移动 |
| language descriptions | 语言条件 policy 学到什么指令 |
| success rate | 评测时如何判断策略是否成功 |
| variation 难度 | 模型需要多强泛化能力 |
| demo 质量 | imitation learning 的监督信号是否可靠 |

所以任务设计本身也是 benchmark 设计的一部分。一个好的自定义任务应该：

```text
目标清晰
成功条件明确
waypoints 可生成稳定 demos
variation 有意义但不过分随机
语言描述和场景目标一致
```


## 本节小结

RLBench 自定义任务可以概括为：

```text
准备 CoppeliaSim 场景
-> 命名物体、传感器和 waypoints
-> 编写 Task Python 类
-> 在 init_task() 中注册对象和 success condition
-> 在 init_episode() 中设置 variation 和语言描述
-> 测试 reset / step / get_demos
```

其中最容易出问题的不是 Python 语法，而是 Python 代码和 CoppeliaSim 场景之间的对应关系：

```text
对象名称要一致
waypoints 要可达
success condition 要准确
语言描述要和目标一致
```

理解这些之后，就可以把 RLBench 从一个现成 benchmark 扩展成一个可自定义的机器人任务开发环境。后续如果需要构建新的 manipulation benchmark、生成新任务 demonstrations，或者为 VLA 模型设计新的评测场景，都可以基于这一套机制继续扩展。