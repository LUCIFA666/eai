# 任务定义与观测/数据格式

RoboMemArena 建立在 LIBERO 之上，任务用 BDDL 定义、环境用 LIBERO 的渲染环境实例化，数据以 HDF5 存储、可转成 RLDS。这一页说明这几层各是什么样子。

## BDDL 任务定义

每个任务是一个 `bddl/*.bddl` 文件，沿用 LIBERO 的 PDDL 风格格式，分几个区块：`:language` 给自然语言目标，`:regions` 定义各物体的初始摆放区域（坐标范围加朝向），`:fixtures` 声明家具、`:objects` 声明可操作物体，`:obj_of_interest` 标出与任务相关的关键对象，`:init` 用谓词给初始状态，`:goal` 用逻辑合取给成功条件。以 `4_drawer_butter` 为例，关键区块如下：

```lisp
(:language Prepare the coffee serving area by organizing tableware and cleaning out any residual liquid)
...
(:fixtures
  wooden_cabinet_1 - wooden_cabinet_tall_bottom
  ...
)
(:objects
  butter_1 - butter
  cream_cheese_1 - cream_cheese
  ...
)
(:obj_of_interest
  wooden_cabinet_1 butter_1 rack_1 milk_1 bowl_drainer_1
)
(:init
  (On butter_1 coffee_table_butter_init_region)
  (In cream_cheese_1 wooden_cabinet_1_top_region)
  ...
)
(:goal
  (And (In butter_1 wooden_cabinet_1_top_region))
)
```

谓词是理解任务的关键：`On x region` 表示 `x` 摆在某区域上，`In x region` 表示 `x` 在某容器区域内。这个例子里 `:init` 声明 cream_cheese 一开始就在柜子顶层（`wooden_cabinet_1_top_region`），也就是顶层是那个非空抽屉；`:goal` 要求 butter 最终进入同一个顶层区域。谓词化的目标同时是评测时的成功检查基础：`:goal` 里的每个谓词都对应一个可判定的检查。

需要注意的是，BDDL 只规定初始与目标状态，并不写出中间步骤。任务名里"放进非空抽屉"这层记忆语义，是靠初始状态（哪个抽屉非空）加目标状态（butter 要进那个抽屉）隐式表达的——策略必须自己探查、记住、再动作。

评测 harness 把随仓分发的 `libero_fork/` 插入 `sys.path`、用 LIBERO 的 `OffScreenRenderEnv` 实例化环境，并从包内 `bddl/` 目录按任务号解析对应 BDDL 文件（`{tid}_*.bddl`），因此不需要外部安装完整 LIBERO 就能跑评测。

## 观测与动作

评测时每步观测包含两路 RGB 与机器人本体状态：俯视相机 `agentview_rgb` 与腕部相机 `eye_in_hand_rgb`，均为 256×256×3；本体状态含末端位姿 `ee_states`、夹爪 `gripper_states`、关节角 `joint_states`。策略适配器拿到观测时，末端状态被整理成 `[eef_pos(3), eef_axisangle(3), gripper(1)]` 共 7 维（四元数经 `_quat2axisangle` 转成轴角），图像做上下翻转并 resize 到 `resize_size`（默认 256）。动作是 7 维末端增量控制 `[x, y, z, r, p, y, gripper]`，策略每次返回形如 `[horizon, action_dim]` 的动作块。

## HDF5 数据格式

放出的数据有两种粒度：`full_trajectory/` 存完整的长时程轨迹，`subtask_data/` 存带关键帧标注的子片段（用于训练）。`subtask_data` 里每个 HDF5 按 `data/demo_{id}` 组织：

```text
data/demo_{id}/actions                 # (T, 7) 末端动作
data/demo_{id}/obs/agentview_rgb        # (T, 256, 256, 3) 俯视
data/demo_{id}/obs/eye_in_hand_rgb      # (T, 256, 256, 3) 腕部
data/demo_{id}/obs/ee_states, gripper_states, joint_states   # 机器人状态
```

## RLDS 转换

`RoboMemArena_dataset_builder.py` 把 `subtask_data/*.hdf5` 转成 RLDS（TFDS）格式，供 OpenVLA、π0 这类以 RLDS 为输入的框架训练。它扫描 `*_dataset/subtask_data/*.hdf5`，逐条 demo 展开成 step 序列，观测里的 `state` 由末端状态与夹爪拼接而成、共 8 维：

```python
'state': np.asarray(
    np.concatenate((states[i], gripper_states[i]), axis=-1), np.float32),
'joint_state': np.asarray(joint_states[i], dtype=np.float32),
```

对应的特征声明是 `image` / `wrist_image` 为 256×256×3 的 JPEG、`state` 为 8 维、`joint_state` 为 7 维、`action` 为 7 维；`language_instruction` 从 HDF5 文件名去掉 variant / seed / task 后缀后解析得到。RLDS 转换是纯数据步骤，只需 CPU Python 环境（README 给的 pin 为 Python 3.9、`tensorflow==2.13.0`、`tensorflow-datasets==4.9.2`、`h5py==3.9.0`、`numpy==1.24.3`），转好后用 `tfds` 的 `download_and_prepare` 落盘。

## 导航

- 返回上级：[RoboMemArena](../03-robomemarena.md)
- 上一节：[数据生成管线](04-data-generation.md)
- 下一节：[评测协议与指标](06-evaluation-protocol.md)
