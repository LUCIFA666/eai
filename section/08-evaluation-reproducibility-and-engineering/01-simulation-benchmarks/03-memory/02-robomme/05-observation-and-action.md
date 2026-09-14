# 观测与动作接口

RoboMME 用一台 7 自由度 Franka Panda，前视 `base_camera` 与腕部相机各输出 256×256 RGB。多数任务用带腕部相机的 `panda_wristcam`，两个用棒状末端的任务 PatternLock 与 RouteStick 改用 `panda_stick`（`DemonstrationWrapper` 把这两个任务识别为 `is_stick_env` 并将夹爪状态置零）。底层环境以 ManiSkill 的 `obs_mode="rgb+depth+segmentation"`、`control_mode="pd_joint_pos"` 构建，外面套一层 `DemonstrationWrapper` 统一观测与动作的呈现，再按选定的动作空间套不同 wrapper。接口规范在 `doc/env_format.md` 与 `doc/h5_data_format.md`。

## 观测:视频条件与单帧

观测里每个键的值都是一个列表，最新一帧取 `[-1]`。视频条件任务（Imitation 套件与带 Video 前缀的任务）在 episode 开头把一段历史帧序列放进列表作为演示，其余任务开头只给单帧；执行阶段所有任务每步都是单帧。常驻的观测键：

- `front_rgb_list`、`wrist_rgb_list`：前视与腕部 RGB（256×256×3，uint8）。
- `eef_state_list`：末端位姿 `[x, y, z, roll, pitch, yaw]`。
- `joint_state_list`：7 维关节角。
- `gripper_state_list`：夹爪状态（2 维）。

深度、相机内外参默认关闭，通过 `include_*` 开关打开后进入观测或 `info`（`front_depth_list`、`wrist_depth_list`、`front_camera_extrinsic_list` 等）。`info` 还带 `task_goal`（可能的语言目标列表）、在线子目标 `simple_subgoal_online` / `grounded_subgoal_online`、多选项 `available_multi_choices` 和 `status`。

## 四种动作空间

同一套环境对动作空间无关，由外层选择，对应不同 wrapper：

| 动作空间 | 维度 | wrapper | 说明 |
|---|---|---|---|
| `joint_angle` | 8 | `DemonstrationWrapper` | 7 关节角 + 夹爪，绝对量 |
| `ee_pose` | 7 | `EndeffectorDemonstrationWrapper(action_repr="rpy")` | 末端 xyz + rpy + 夹爪，绝对量 |
| `waypoint` | 7 | `MultiStepDemonstrationWrapper` | 同 ee_pose 格式，按离散关键帧执行（planner 先 screw 再退 RRT*） |
| `multi_choice` | 字典 | `OraclePlannerDemonstrationWrapper` | `{"choice": "A", "point": [y, x]}`，point 是前视图像素坐标 |

夹爪约定：闭合为 `-1`、张开为 `+1`，都是绝对指令。`multi_choice` 的候选来自 `info["available_multi_choices"]`，由 `utils/vqa_options.py` 的 `OPTION_BUILDERS`（16 个任务各一个 `_options_<task>` 构造器）生成，每个选项是 `{"label", "action", ...}`，`multi_choice` 动作写成 `{"choice": "A", "point": [y, x]}`。选项数按任务而异：PickXTimes 给三个（`a` 拾取方块、`b` 放到目标、`c` 按按钮停），PatternLock 给八个方向（前后左右加四个斜向），RouteStick 给四个（就近的左/右目标 × 顺时针/逆时针绕行）。带 `available` 的选项（如"拾取方块"要指定拾哪个）需要点击提供 `point` 像素坐标，`need_parameter` 标出这一点。因为要用到真值分割把点击映射到物体，`multi_choice` 属于 Video-QA 式的诊断评测，不用于常规的策略动作评测。所有 wrapper 最外层再套 `FailAwareWrapper` 捕获执行异常。

## 坐标系

世界系右手系，原点在桌面中心（物体在此附近生成），+x 指向前方（从机器人指向物体）、+y 指向机器人左侧、+z 向上，桌面为 z=0，地面在 z=-0.92。Panda 底座 `panda_link0` 固定在世界系 `(-0.615, 0, 0)`。欧拉角用外旋 XYZ，且为时间连续做了解缠，可能超出 ±π。

## HDF5 数据结构

演示数据存成每任务一个 `record_dataset_<EnvID>.h5`，按 `episode_<N>/{setup, timestep_<K>/{obs, action, info}}` 组织：

- `setup/`：`seed`、`difficulty`、`task_goal`、相机内参 `front/wrist_camera_intrinsic`（3×3）、`available_multi_choices`。
- `obs/`：`front_rgb` / `wrist_rgb`（256×256×3 uint8）、`front_depth` / `wrist_depth`（256×256×1 int16，毫米）、`joint_state`（7）、`eef_state`（6）、`gripper_state`（2，开度 `[0, 0.04]`）、`is_gripper_close`、相机外参（3×4）。
- `action/`：同时存四种动作空间的动作 `joint_action`（8）、`eef_action`（7，`[x,y,z,r,p,y,gripper]`）、`waypoint_action`（7）、`choice_action`（JSON 字符串），方便按不同接口训练。
- `info/`：离线与在线的子目标文本、`is_video_demo`、`is_subgoal_boundary`、`is_completed`。

## 环境交互主循环

环境由 `BenchmarkEnvBuilder` 按任务和动作空间构建，`make_env_for_episode` 取某个 episode，`reset()` 返回带 `task_goal` 的观测；之后每步 `env.step(action)` 返回新的观测与 `status`，观测里每个键是列表、当前帧取 `[-1]`。`scripts/run_example.py` 的核心循环如下：

```python
# scripts/run_example.py
env_builder = BenchmarkEnvBuilder(
    env_id=tid, dataset=dataset, action_space=action_space_type,
    gui_render=GUI_RENDER, max_steps=MAX_STEPS,
)
env = env_builder.make_env_for_episode(ep)
obs, info = env.reset()
task_goal = info["task_goal"][0]

action_gen = generate_sample_actions(action_space_type, env=env)
for action in action_gen:
    obs, _, terminated, truncated, info = env.step(action)
    status = info.get("status", "unknown")
    if status == "error":          # 常见于 ee_pose 下的 IK 失败
        break
    if terminated or truncated:
        break
env.close()
```

这里的 `generate_sample_actions` 只产出占位动作：joint_angle 与 ee_pose 给当前位姿加小噪声，waypoint 给末端位姿加 xyz 噪声，multi_choice 给一串 `{"choice", "point"}`。真正的策略把 `obs["front_rgb_list"][-1]`、`obs["wrist_rgb_list"][-1]` 与 `task_goal` 映射成动作。`make_env_for_episode` 还带一组 `include_*` 开关（`include_front_depth`、`include_front_camera_intrinsic` 等），默认关闭，打开后深度和相机内外参才进入观测与 `info`。

## 导航

- 返回上级：[RoboMME](../02-robomme.md)
- 上一节：[记忆负载机制](04-memory-load.md)
- 下一节：[评测协议与指标](06-evaluation-protocol.md)
