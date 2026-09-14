# 观测与渲染：state、rgbd 与运行截图

前面用的是 `obs_mode="state"`，观测是一个 42 维状态向量。下面看视觉观测。视觉模式容易让人误会：以为切到 `rgbd` 后，策略只能看到图像，状态量就没了。至少在这里的 `PickCube-v1` 上，并不是这样。

## 本节目标

本节围绕下面几个问题展开：

1. `obs_mode="state"` 的观测结构是什么样的，为什么它适合入门。
2. `obs_mode="rgbd"` 的观测字典里有哪些 key，每一类数据的用途是什么。
3. `rgbd` 模式是否会自动移除状态量——这个常见误解的真相是什么。
4. `env.render()` 的渲染图和 `obs["sensor_data"]` 的观测图有什么本质区别，各自该在什么场景下使用。

## state 观测：先把闭环跑通

`state` 是最适合入门的观测模式。它把机器人关节、物体、目标等状态量整理成一个扁平向量。对初学者来说，用它能先绕开视觉编码器，把注意力放在环境交互和动作控制上。

示例输出可能类似：

```text
observation_space: Box(-inf, inf, (1, 42), float32)
action_space: Box(-1.0, 1.0, (7,), float32)
```

前面的 `1` 来自 batch 维，真正单个环境的状态维度是 42。后面如果用 MLP 策略，通常按 42 维来设计输入，再在训练代码中处理 batch 维。

## rgbd 观测：不是"图像替换状态"

把 `obs_mode` 改成 `rgbd` 后，观测空间变成字典。下面是一段示例节选：

```text
Dict(
  'agent': Dict(
    'qpos': Box(-inf, inf, (1, 9), float32),
    'qvel': Box(-inf, inf, (1, 9), float32)
  ),
  'extra': Dict(
    'goal_pos': Box(-inf, inf, (1, 3), float32),
    'is_grasped': Box(False, True, (1,), bool),
    'tcp_pose': Box(-inf, inf, (1, 7), float32)
  ),
  'sensor_data': Dict(
    'base_camera': Dict(
      'depth': Box(-32768, 32767, (1, 512, 512, 1), int16),
      'rgb': Box(0, 255, (1, 512, 512, 3), uint8)
    )
  ),
  'sensor_param': Dict(
    'base_camera': Dict(
      'cam2world_gl': Box(-inf, inf, (1, 4, 4), float32),
      'extrinsic_cv': Box(-inf, inf, (1, 3, 4), float32),
      'intrinsic_cv': Box(-inf, inf, (1, 3, 3), float32)
    )
  )
)
```

这里可以看到四类信息：

| 键 | 内容 | 用途 |
|---|---|---|
| `agent` | 机器人关节位置、速度 | 机器人本体状态 |
| `extra` | 目标位置、TCP 位姿、是否抓住物体 | 任务相关状态 |
| `sensor_data` | RGB、depth 图像 | 视觉策略或感知模块 |
| `sensor_param` | 相机内外参 | 几何计算、点云反投影等 |

> ⚠️ **易错点**：`rgbd` 更接近"状态 + 图像 + 相机参数"，不是"把状态量替换成图像"。如果训练时希望做纯视觉策略，需要在自己的数据管线或网络输入里主动选择只用图像，而不是以为环境自动删掉了状态量。

本节保存了同一时刻的 RGB 和 depth：

![rgbd 模式下的 RGB 观测](../../assets/maniskill_pickcube_rgb.png)

![rgbd 模式下的 depth 观测](../../assets/maniskill_pickcube_depth.png)

本节为了文档展示，将 sensor camera 分辨率设置为 512×512；默认任务中常见的传感器分辨率较小，训练时可按显存和速度需求调整。

depth 图需要可视化处理后才能直观看，不能把它当普通 RGB 截图解释。原始 depth 值通常以 int16 存储，单位是毫米或编码值，直接显示往往是全黑或几乎全黑的。

## 渲染图和观测图不要混在一起

ManiSkill 里常见两类图：

| 图像来源 | 典型用途 | 本节文件 |
|---|---|---|
| `env.render()` | 给人看任务运行效果，写文档、录视频 | `maniskill_pickcube_reset.png`、`rollout.mp4` |
| `obs["sensor_data"]` | 给策略或感知模块使用 | `maniskill_pickcube_rgb.png`、`depth.png` |

这两者都能"看见场景"，但含义不同。前者是渲染输出，偏展示；后者是环境观测，偏算法输入。写文档时可以都放，但图注要说清楚来源。

> ⚠️ **易错点**：把渲染图和观测图混在一起。`env.render()` 用于展示，`obs["sensor_data"]` 才是策略观测。两者来源不同，不要用渲染图替代对观测数据的检查。

## 小结

- `state` 观测是扁平向量，适合先把控制和 RL 闭环跑通。
- `rgbd` 观测是字典，包含机器人状态（`agent`）、任务额外信息（`extra`）、相机数据（`sensor_data`）和相机参数（`sensor_param`）。
- 在 `PickCube-v1` 中，`rgbd` 并没有自动移除状态量；是否只使用图像，是下游策略自己的设计。
- `env.render()` 的图适合展示任务画面，`sensor_data` 里的图才是策略观测。
- depth 图需要可视化处理后才能直观看，不能把它当普通 RGB 截图解释。

## 导航

- 上一节：[任务的五把钥匙：env_id、观测、控制、奖励与成功](03-task-interfaces.md)
- 返回上级：[ManiSkill 任务环境](../01-maniskill-tasks.md)
- 下一节：[批量接口、GPU 并行与 CPUGymWrapper](05-batch-and-gpu.md)
