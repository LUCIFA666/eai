# 观测与动作接口

MIKASA-Robo-VLA 提供两种观测模式，动作与奖励接口在两种模式下相同。VLA 训练和评测统一用 `rgb` 模式加上一套规范的 wrapper 链，源码在 `mikasa_robo_suite/vla/utils/`。

## 两种观测模式

- `obs_mode="state"`：特权仿真状态，一个扁平张量，含场景完整物理状态，没有相机图像。用于 PPO oracle 训练、快速调试和奖励校准。
- `obs_mode="rgb"`：俯视 `base_camera` 与腕部 `hand_camera` 的 RGB，加上本体感知。这是 VLA 训练与评测的标准模式。

两种模式在 `gym.make` 时二选一。

## 规范 wrapper 链

`apply_mikasa_vla_wrappers(env, include_overlays=True)` 在 `gym.make` 之后按 env id 从 `VLA_WRAPPER_CONFIGS` 取该任务的配置，由内向外套上：

```text
StateOnlyTensorToDictWrapper                      # 注入 task_cue + oracle_info
  └─ config.curriculum_wrapper                    # 仅短程课程式任务有
      └─ config.overlays（include_overlays=True 时）# 渲染叠加，评测关闭
          └─ FlattenRGBDObservationWrapper(rgb=True, depth=False, state=False,
                                            oracle=False, joints=True)
              └─ ConvertJointsToEEFXyzRpyGripperWrapper
```

overlay 只用于渲染和录像、不改观测与奖励，规范评测用 `include_overlays=False` 关掉。curriculum wrapper 只挂在短程课程式变体上，作用是在 cue 与 memory 阶段冻结动作。经这条链后观测被拉平成一个字典，VLA 侧要消费的键（`B = num_envs`）：

| 键 | 形状 / dtype | 含义 |
|---|---|---|
| `obs["rgb"]` | `(B, 128, 128, 6)` uint8 | 俯视与腕部相机沿通道维拼接，`[..., :3]` 是 `base_camera`，`[..., 3:6]` 是 `hand_camera` |
| `obs["proprio"]` | `(B, 7)` float32 | 绝对末端位姿加夹爪开度 |
| `obs["task_cue"]` | `(B, P)` float32 | 仅 RL、仅 Rotate* 系列保留，其余任务被丢弃 |

## obs["rgb"] 与相机

`FlattenRGBDObservationWrapper` 用 `rgb=True` 把原始观测里 `sensor_data` 下每个相机的 `rgb` 沿最后一维拼接。`panda_wristcam` 机器人有两个相机，各 128×128×3，拼成 6 通道，通道 `[:3]` 是俯视 `base_camera`、`[3:6]` 是腕部 `hand_camera`。`base_camera` 由环境的 `_default_sensor_configs` 定义，位姿 `look_at(eye=[0.3,0,0.6], target=[-0.1,0,0.1])`，分辨率 128×128、fov `π/2`；另有一个 512×512 的 `render_camera` 只用于人看的录像，不进入观测。

## obs["proprio"] 与四元数换算

`ConvertJointsToEEFXyzRpyGripperWrapper` 把拉平后的关节观测改写成 7 维：前三维取末端 TCP 的绝对 xyz，中间三维由 TCP 的姿态四元数（wxyz 顺序）转成 roll、pitch、yaw，最后一维是夹爪开度（Panda 两根手指 qpos 之和，范围 0 到 0.08 米，不归一化）：

```python
# wxyz 四元数 → rpy（弧度）
roll  = atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
pitch = asin(clamp(2*(w*y - z*x), -1, 1))
yaw   = atan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
gripper = qpos[-2:].sum()      # 两根手指之和，0 闭合、约 0.08 张开
```

这 7 维是绝对量，不是关节角、也不是动作增量。

## 动作接口

发给 `env.step(action)` 的动作也是 7 维，但语义不同，走 Panda 的 `pd_ee_delta_pose` 控制器，各分量都在 `[-1, 1]`：

```text
action = [delta_eef_x, delta_eef_y, delta_eef_z,
          delta_eef_roll, delta_eef_pitch, delta_eef_yaw,
          gripper_command]
```

- 前三维是末端平移的相对指令，Panda 把 `[-1, 1]` 映射到每步 `[-0.1, 0.1]` 米。
- 第 4 到 6 维是姿态的相对指令，控制器按 0.1 弧度的单步上限裁剪。
- 第 7 维是夹爪的位置指令，`-1` 朝闭合、`+1` 朝张开；它是位置指令而非开度增量，和 `obs["proprio"][..., 6]` 不是同一个量。

## 奖励模式

| 模式 | 说明 |
|---|---|
| `sparse` | 成功给 1.0、否则 0.0，用于模仿学习 |
| `dense` | 按子目标累加的稠密奖励，量纲随任务而异 |
| `normalized_dense` | 稠密奖励归一化到 `[0, 1]`，PPO 训练推荐，跨任务学习率可比 |

dense 奖励由若干塑形项累加而成，例如趋近项 `reaching = 1 - tanh(10 * tcp_to_obj_dist)` 与静止项 `static = 1 - tanh(5 * |qvel|)`，成功时把总奖励置为该任务的成功奖励值（多数任务为 `3.0`，量纲随任务而异）。`normalized_dense` 就是 dense 除以这个成功奖励值，于是成功对应 `1.0`、各任务量纲可比。

## 哨兵值与特权字段

最内层的 `StateOnlyTensorToDictWrapper` 在环境不暴露 `task_cue` / `oracle_info` 时，用哨兵值 `4242424242` 填充这两个键。随后 `FlattenRGBDObservationWrapper` 做剥离：`oracle_info` 对所有任务都移除（VLA 传 `oracle=False`），值等于哨兵的 `task_cue` 也移除，只有 Rotate* 系列因为要暴露目标角度而保留 `task_cue`。所以规范评测里 VLA 策略只读相机图像、`obs["proprio"]` 和 `info["language_instruction"]`。有意思的是，这个哨兵值同时也是评测的起始 seed。

## cue 阶段的动作冻结

短程且属课程式的变体（ShellGame*、非 Long 的 RememberColor / RememberShape / RememberShapeAndColor、FindImposter* 等）会在链里加一层 `CurriculumPhaseNoopActionWrapper`，在 `elapsed < cue_steps + empty_steps` 期间把动作清零，强制策略在 cue 与 memory 阶段保持不动，只在 action 阶段行动。Long 变体不套这层。

## 导航

- 返回上级：[MIKASA-Robo-VLA](../01-mikasa.md)
- 上一节：[难度与时间跨度](05-difficulty-and-horizon.md)
- 下一节：[评测协议与指标](07-evaluation-protocol.md)
