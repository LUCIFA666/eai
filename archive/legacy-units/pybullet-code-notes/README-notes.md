# PyBullet / MuJoCo 控制链路源码摘录

目标：保存从公众号文章关联项目中爬取到的真实上游代码，定位“PyBullet 的关节控制指令可自动转换为 MuJoCo 的 API 格式”这句话在 MetaSim 中对应的实现路径。

## 来源

- 公众号文章：https://mp.weixin.qq.com/s/IiGBs9kqzY-segPXj363VA
- RoboVerse 主仓库：https://github.com/RoboVerseOrg/RoboVerse
- MetaSim 上游仓库：https://github.com/RoboVerseOrg/MetaSim
- 本地爬取时间：2026-06-08
- 上游许可：Apache-2.0，分发或复用时请同步保留上游许可信息。

## 本地文件

本目录只保留和“统一动作接口如何落到 PyBullet / MuJoCo 后端”直接相关的官方源码摘录：

```text
official_metasim_control_path/
└── metasim/
    ├── sim/
    │   ├── base.py
    │   ├── pybullet/
    │   │   ├── __init__.py
    │   │   └── pybullet.py
    │   └── mujoco/
    │       ├── __init__.py
    │       └── mujoco.py
    ├── utils/
    │   └── state.py
    └── test/
        └── sim/
            └── test_dof_control.py
```

这些文件是源码摘录，不是一个可独立安装的 Python 包；直接运行会缺少 MetaSim 的完整依赖和上下文。阅读它们时应把它们当作“官方实现路径证据”。

## 那句话实际对应的代码路径

文章中的说法可以更准确地理解为：MetaSim 不直接把某一条 PyBullet API 调用逐行翻译成 MuJoCo API，而是先把动作规整成统一的 `dof_pos_target` 字段，然后不同模拟器后端各自把这个统一动作落到自己的控制 API 上。

核心数据流是：

```text
上层任务 / 控制器
  -> handler.set_dof_targets(actions)
  -> 统一动作字段：dof_pos_target = {joint_name: target_position}
  -> PyBullet 后端：p.setJointMotorControlArray(..., targetPositions=...)
  -> MuJoCo 后端：physics.data.ctrl[actuator.id] = joint_target
```

重点阅读位置：

- `official_metasim_control_path/metasim/sim/base.py`
  - `BaseSimHandler.set_dof_targets(...)`
  - 作用：定义统一入口，校验动作字段，并把动作交给具体后端 `_set_dof_targets(...)`。

- `official_metasim_control_path/metasim/utils/state.py`
  - `adapt_actions_to_dict(...)`
  - `action_input_to_tensor(...)`
  - 作用：在 tensor / dict 输入之间做动作格式归一化，核心字段是 `dof_pos_target`。

- `official_metasim_control_path/metasim/sim/pybullet/pybullet.py`
  - `SinglePybulletHandler._set_dof_targets(...)`
  - `_apply_action(...)`
  - 作用：按 PyBullet joint order 取出 `dof_pos_target`，再调用 `p.setJointMotorControlArray(..., controlMode=p.POSITION_CONTROL, targetPositions=action)`。

- `official_metasim_control_path/metasim/sim/mujoco/mujoco.py`
  - `MujocoHandler._set_dof_targets(...)`
  - `get_states(...)` 中读取 `physics.data.ctrl`
  - 作用：按 MuJoCo actuator id 写入 `physics.data.ctrl[actuator.id] = joint_targets[joint_name]`，并在状态中回读 `dof_pos_target`。

- `official_metasim_control_path/metasim/test/sim/test_dof_control.py`
  - 作用：官方集成测试，验证 `set_dof_targets` 对不同后端的 DOF 控制行为。

## 阅读建议

如果只想理解“跨模拟器控制转换”，建议按这个顺序读：

1. 先读 `metasim/sim/base.py` 的 `set_dof_targets(...)`，确认统一入口。
2. 再读 `metasim/sim/pybullet/pybullet.py` 的 `_set_dof_targets(...)`，看统一动作如何落到 PyBullet。
3. 再读 `metasim/sim/mujoco/mujoco.py` 的 `_set_dof_targets(...)`，看同一个统一动作如何落到 MuJoCo。
4. 最后读 `metasim/utils/state.py`，理解动作格式为什么可以在 dict 和 tensor 之间转换。

## Code Review 关注点

- 这些文件来自上游官方仓库，当前本地没有修改源码实现。
- 这份摘录保留了完整文件，方便通过函数上下文理解控制链路，而不是只截取几行导致误读。
- 目录不包含整仓库依赖，因此不承诺可独立运行；它服务于课程阅读、溯源和人工 code review。
- 如果后续要把这些源码变成可运行 lab，应改为引入完整 MetaSim 依赖，或单独写一个最小复现脚本，不应在摘录文件里直接修改上游源码。
