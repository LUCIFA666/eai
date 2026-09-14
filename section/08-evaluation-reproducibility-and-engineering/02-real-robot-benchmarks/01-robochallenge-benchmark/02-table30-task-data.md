# Table30 任务与数据

Table30 是 RoboChallenge 的固定桌面操作任务集。任务数据同时承担训练材料和评测口径两种职责：训练侧使用示教 episode、相机视频和机器人状态微调策略；评测侧用同一任务定义、机器人平台和复位协议解释 `success rate` 与 `progress score`。Table30 v2 延续 30 任务设置，但更新了任务列表、机器人集合、相机命名和 metadata 字段。

## 任务集合

Table30 v1 覆盖整理、堆叠、抽屉、插拔、开关、清洁、软物体和双臂协作等桌面操作。任务名称包括 `arrange_flowers`、`open_the_drawer`、`plug_in_network_cable`、`make_vegetarian_sandwich`、`shred_scrap_paper`、`stack_bowls`、`wipe_the_table` 等。任务标签用于描述主要难点，例如 `temporal`、`softbody`、`precise3d`、`bimanual`、`multiview`、`repeated`、`classification` 和 `simple-pick`。

Table30 v2 仍保留 30 个 manipulation task，但任务集合更偏向日常桌面和办公场景，例如 `put_the_books_back`、`tie_a_knot`、`stamp_positioning`、`pack_the_items`、`scoop_with_a_small_spoon`、`fold_the_clothes`、`place_objects_into_desk_drawer`、`item_classification`。少数任务名称与 v1 接近，例如 `arrange_flowers`、`stack_bowls`、`wipe_the_table`，但具体目标、物体数量和数据字段不一定相同。

| 版本 | 任务数量 | 任务组织方式 | 结果解释 |
|---|---:|---|---|
| Table30 v1 | 30 | 固定桌面 / 桌边 manipulation 任务，覆盖单臂和双臂平台 | 已有公开结果主要对应 v1 任务和当时的机器人集合 |
| Table30 v2 | 30 | 更新后的任务集合，覆盖更多日常桌面物体和 DOS-W1 平台 | 数据 schema 和平台集合更新，不能直接并入 v1 结果表 |

## 机器人平台

Table30 v1 的机器人平台包括 ARX5、UR5、Franka 和 ALOHA。ARX5、UR5、Franka 是单臂配置，ALOHA 是双臂配置。Table30 v2 移除了 Franka，加入 DOS-W1，形成 ARX5、UR5、ALOHA、DOS-W1 四类平台。这个变化会影响 action shape、状态文件数量、相机视角和数据字段。

| 版本 | 单臂平台 | 双臂平台 | 主要变化 |
|---|---|---|---|
| Table30 v1 | ARX5、UR5、Franka | ALOHA | Franka 使用 7 DoF 单臂状态，ALOHA 使用左右臂状态文件 |
| Table30 v2 | ARX5、UR5 | ALOHA、DOS-W1 | DOS-W1 加入双臂平台，Franka 不在 v2 平台集合中 |

机器人平台会改变任务数据和评测输入。同一个任务名如果换到不同机器人，观测视角、状态字段和动作维度都会变化；跨版本比较任务表现时，机器人集合先于分数本身进入解释。

## 数据层级

两个版本的数据层级基本一致：任务目录下保存任务描述、任务级 metadata 和多个示教 episode。每个 episode 下再拆成 `meta/`、`states/` 和 `videos/`。这层结构把任务定义、机器人本体状态和视觉观测分开保存，便于训练代码只读取所需模态，也便于评测结果回到 episode 级材料中解释。

```text
<task_name>/
  task_desc.json
  meta/
    task_info.json
  data/
    episode_000000/
      meta/
        episode_meta.json
      states/
        states.jsonl 或 left_states.jsonl + right_states.jsonl
      videos/
        <camera_name>.mp4
```

`task_info.json` 保存任务名、自然语言 prompt、评分描述、任务标签和视频编码信息。v1 中 `robot_id` 位于任务级 metadata 顶层；v2 的示例把 `robot_id` 放入 `episode_meta.json`，并在 episode metadata 中加入 `features`，用于记录相机 intrinsics / extrinsics 等信息。这个变化说明 v2 更强调 episode 级传感器配置和机器人实例信息。

metadata 字段的位置变化会影响数据加载器如何确定机器人实例、episode 编号和相机标定：

| 字段 | Table30 v1 示例位置 | Table30 v2 示例位置 | 字段作用 |
|---|---|---|---|
| `robot_id` | `meta/task_info.json` 顶层 | `data/episode_*/meta/episode_meta.json` | v2 把机器人实例放到 episode 级，便于同一任务承载不同采集实例 |
| `episode_index` | `episode_meta.json` | v2 示例未显式列出 | v1 直接记录 episode 序号，v2 更依赖 episode 目录名和时间字段 |
| `features` | v1 示例未显式列出 | `episode_meta.json` | v2 用它保存相机和状态字段的结构化描述 |
| intrinsics / extrinsics | v1 示例未显式列出 | `features.<camera_name>.intrinsics` / `extrinsics` | v2 把相机内参、外参纳入 episode metadata，转换脚本可以从 metadata 恢复传感器配置 |

任务级 metadata 的最小信息可以概括为下面这组字段：

```json
{
  "task_desc": {
    "task_name": "arrange_flowers",
    "prompt": "Put the 4 flowers into the vase.",
    "scoring": "...",
    "task_tag": ["repeated", "single-arm", "ARX5", "precise3d"]
  },
  "video_info": {
    "fps": 30,
    "ext": "mp4"
  }
}
```

episode 级 metadata 在 v2 中承载更多传感器和机器人实例信息：

```json
{
  "start_time": 1750405586.3430033,
  "end_time": 1750405642.5247612,
  "frames": 1672,
  "robot_id": "rc_arx5_5",
  "features": {
    "cam_global": {
      "intrinsics": [],
      "extrinsics": {"arms": {"arm": []}}
    }
  }
}
```

## 视频与相机命名

视频文件名体现机器人平台和数据版本。v1 的 ARX5 使用 `arm_realsense_rgb.mp4`、`global_realsense_rgb.mp4`、`right_realsense_rgb.mp4`；UR5 使用 `global_realsense_rgb.mp4` 和 `handeye_realsense_rgb.mp4`；Franka 使用 `handeye_realsense_rgb.mp4`、`main_realsense_rgb.mp4`、`side_realsense_rgb.mp4`；ALOHA 使用 `cam_high_rgb.mp4`、`cam_wrist_left_rgb.mp4`、`cam_wrist_right_rgb.mp4`。

v2 的命名更统一。ARX5 使用 `cam_arm_rgb.mp4`、`cam_global_rgb.mp4`、`cam_side_rgb.mp4`；UR5 使用 `cam_global_rgb.mp4` 和 `cam_arm_rgb.mp4`；ALOHA 与 DOS-W1 使用 `cam_high_rgb.mp4`、`cam_left_wrist_rgb.mp4`、`cam_right_wrist_rgb.mp4`。模型训练或转换脚本如果把相机名写死在代码中，v1 到 v2 的迁移会首先暴露在视频字段映射上。

| 平台 | Table30 v1 视频名 | Table30 v2 视频名 |
|---|---|---|
| ARX5 | `arm_realsense_rgb.mp4`、`global_realsense_rgb.mp4`、`right_realsense_rgb.mp4` | `cam_arm_rgb.mp4`、`cam_global_rgb.mp4`、`cam_side_rgb.mp4` |
| UR5 | `global_realsense_rgb.mp4`、`handeye_realsense_rgb.mp4` | `cam_global_rgb.mp4`、`cam_arm_rgb.mp4` |
| ALOHA | `cam_high_rgb.mp4`、`cam_wrist_left_rgb.mp4`、`cam_wrist_right_rgb.mp4` | `cam_high_rgb.mp4`、`cam_left_wrist_rgb.mp4`、`cam_right_wrist_rgb.mp4` |
| Franka / DOS-W1 | Franka: `handeye_realsense_rgb.mp4`、`main_realsense_rgb.mp4`、`side_realsense_rgb.mp4` | DOS-W1: `cam_high_rgb.mp4`、`cam_left_wrist_rgb.mp4`、`cam_right_wrist_rgb.mp4` |

## 状态字段

单臂机器人通常使用一个 `states.jsonl`，双臂机器人使用 `left_states.jsonl` 和 `right_states.jsonl`。每行记录一帧或一个时间点的本体状态，常见字段包括 joint position、end-effector pose、gripper 状态和 timestamp。字段名称、shape 和坐标约定随机器人变化。

v1 中 ARX5 的末端位姿字段是 `end_effector_pose`，使用位置加 roll / pitch / yaw；UR5 和 Franka 使用 `ee_positions`，以位置加 quaternion 表示末端位姿。v1 的 ALOHA 同时包含 master / puppet 相关字段，如 `joint_positions`、`qpos`、`ee_pose_quaternion`、`ee_pose_rpy`。v2 把多个平台的字段进一步收敛到 `joint_positions`、`joint_velocities`、`ee_positions`、`gripper_width`、`efforts` 等名称，但字段可用性和精度说明仍随平台变化。

状态字段决定数据加载器读取哪些文件、动作适配层接收哪些本体状态。训练代码不能只按任务名推断状态维度；机器人平台、版本和单臂 / 双臂配置共同决定 `states/` 目录中有哪些文件、每行 JSONL 中有哪些键，以及这些键如何映射到模型输入。

## LeRobot 转换

两个版本都提供 `convert_to_lerobot.py`，示例转换目标主要面向 ARX5 数据。v1 示例依赖 `lerobot==0.1.0`，默认使用 `$LEROBOT_HOME`；v2 示例依赖指定 commit 的 LeRobot，默认使用 `$HF_LEROBOT_HOME`。转换脚本会把原始任务目录、视频和状态信息写入 LeRobot 数据集目录，并调用 `dataset.consolidate(run_compute_stats=False)`。

LeRobot 转换属于训练数据接入方式，不属于评测协议本身。转换后的 dataset 方便复用 LeRobot 的加载、处理和统计工具；原始 RoboChallenge 数据仍保留任务描述、机器人平台、相机命名和 episode metadata。跨版本训练时，转换脚本的字段映射比命令行参数更关键，尤其是相机名、状态键和双臂数据的左右臂文件。

## 数据口径

Table30 / Table30 v2 的分数、训练数据和接口行为不能只按任务名合并。稳定的数据口径至少同时包含四个对象：任务版本、机器人平台、相机集合和状态 schema。缺少其中一个对象时，同名任务可能对应不同物体数量、不同视角、不同状态维度或不同动作空间。

这些对象也影响结果解释。Table30 v1 的公开模型表现来自 v1 任务、v1 平台集合和当时的评分协议；Table30 v2 的数据更新不能自动继承这些结果。课程中引用 RoboChallenge 结果时，任务版本和数据版本应和分数表放在同一段说明中。

## 小结

Table30 的任务数据同时定义训练材料、测试场景和结果解释条件。任务版本定义语言目标和任务集合，机器人平台定义状态文件和动作维度，相机命名定义视觉输入，metadata 和 JSONL 字段定义 episode 级传感器、机器人实例和本体状态。

Table30 v1 和 Table30 v2 都保留固定 30 任务的评测思路，但平台集合、相机名称、metadata 位置和状态字段已经发生变化。同名任务跨版本出现时，任务描述、物体数量、机器人配置和数据 schema 仍可能不同，分数和训练数据都应按版本、平台、相机集合和状态 schema 共同解释。

## 导航

- 返回上级：[RoboChallenge](../01-robochallenge-benchmark.md)
- 上一页：[系统与评测协议](01-system-protocol.md)
- 下一页：[推理接口与运行循环](03-inference-interface.md)
