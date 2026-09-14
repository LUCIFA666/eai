# 数据集

RoboMME 放出两套数据：一套仿真演示（1600 条、每任务 100 条、约 770k 个 timestep），托管在 Hugging Face 的 `Yinpei/robomme_data_h5`，供模仿学习与记忆方法训练；另有一套配对的真机演示，用于验证方法能否迁移到真实机器人。

## 组织与格式

仿真数据每任务一个 `record_dataset_<EnvID>.h5`，按 `episode_<N>/{setup, timestep_<K>/{obs, action, info}}` 组织。`setup` 存该 episode 的 seed、difficulty、task_goal 与相机内参；每个 timestep 的 `obs` 存前视与腕部的 RGB 与深度、关节与末端状态、夹爪开度。

一个特点是同一条轨迹同时存下四种动作空间的动作，训练时按需取用：`joint_action`（8 维，关节角 + 夹爪）、`eef_action`（7 维，`[x,y,z,r,p,y,gripper]`）、`waypoint_action`（7 维，关键帧格式）、`choice_action`（VideoQA 式的 JSON）。字段的形状、单位与坐标系约定与在线观测一致，同一条轨迹因此既能训练也能直接评测。

## 切分

数据分 train / val / test 三档，每任务分别 100 / 50 / 50 个 episode，难度按比例混合（train 约 easy 50 / medium 25 / hard 25，val 与 test 约 26 / 12 / 12）；发布的 1600 条即 16 个任务的 train 档。每个 episode 的 seed 与 difficulty 固定，记在 `src/robomme/env_metadata/` 里。

## 子目标与关键帧标注

除轨迹本身，数据还带记忆方法要用的标注，存在每步的 `info` 里，符号记忆的子目标预测器就在这些标注上训练。子目标有简单与 grounded 两档，各自又分离线与在线两个字段。

简单子目标 `simple_subgoal` 是纯文本的当前子目标，来自任务 `task_list` 里每步的 `name`。grounded 子目标 `grounded_subgoal` 在同一句里嵌入目标的前视图像素坐标，来自 `task_list` 里对应的 `subgoal_segment` 模板：模板先留一个 `<>` 占位，运行时用目标物体的分割掩码质心填成 `<y, x>`（`center_y = int(coords[:,0].mean())`、`center_x` 同理），坐标是前视 256×256 图上的整数、范围 0 到 255；若某步取不到质心，就退回不带坐标的简单文本。以 PickXTimes 为例：

```text
simple_subgoal    :  pick up the red cube for the first time
grounded_subgoal  :  pick up the red cube at <134, 88> for the first time
                     press the button at <210, 96> to stop
```

一句里可以有多个坐标占位，例如 MoveCube 的 `Hook the cube at <142, 70> to the target at <98, 160> with the peg` 同时标出方块与目标两个位置。离线字段（`simple_subgoal` / `grounded_subgoal`）是运动规划器视角下的当前子目标，在线字段（`simple_subgoal_online` / `grounded_subgoal_online`）可能更早推进到下一子目标，两者并存、供不同训练口径取用。此外每步还带 `is_video_demo`（是否演示帧）、`is_subgoal_boundary`（是否子目标切换点）、`is_completed` 等标记。

## 生成与筛选

仿真演示由运动规划器自动生成：每个子目标先用 `move_to_pose_with_screw` 规划，失败退到 `move_to_pose_with_RRTStar`，各重试若干次仍失败就丢弃整条轨迹。生成时注入少量扰动再恢复，以增加失败恢复行为的多样性。只有成功的 episode 才写入数据集，因此库里的轨迹都是完整成功的示范。

## 真机数据集

RoboMME 配了 4 个真机任务，对应仿真里的计数、遮挡追踪、重拾、路径复现（PutFruits、TrackCube、RepickBlock、DrawPattern），共约 350 条演示、约 78400 个 timestep（PutFruits 约 50 条，其余各约 100 条）。采集平台是 Franka Emika Panda 加 UMI 的 fin-ray 夹爪，按 DROID 布局配三个 RGB-D 相机（双肩部 D435 + 腕部 D405），用 Oculus Quest 2 以 15 Hz 遥操作。这套真机数据用于评估记忆方法从仿真到真机的迁移。

## 下载与回放

数据从 Hugging Face 的 `Yinpei/robomme_data_h5` 下载；用 Docker 时挂到容器的 `/app/data/robomme_data_h5`（只读）。`scripts/dataset_replay.py` 按目录、动作空间与条数在仿真里回放这些 HDF5 轨迹，用来核对数据或可视化，默认参数如下：

```bash
# scripts/dataset_replay.py 默认值
uv run scripts/dataset_replay.py --h5-data-dir data/robomme_data_h5 \
    --action-space-type joint_angle --replay-number 10
```

回放时它跳过标了 `is_video_demo` 的演示帧，按动作空间读对应的动作列：joint_angle 读 `action/joint_action`、ee_pose 读 `action/eef_action`、waypoint 读 `action/waypoint_action`（去掉相邻重复），multi_choice 只在 `is_subgoal_boundary` 处读 `action/choice_action`。

## 导航

- 返回上级：[RoboMME](../02-robomme.md)
- 上一节：[结果与发现](08-results-and-findings.md)
