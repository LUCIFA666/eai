# 9.1.5.5 Policy 训练、接入与评测

目标：把前面采集到的 RoboTwin 数据接到 policy 训练或闭环评测中，并用统一的 benchmark 口径汇报 success rate。本章只讲公共接口和评测口径；具体模型的训练与评测命令放在子章节中。

## 从采集数据到 Policy 输入

一次数据采集通常会生成：

```text
data/<task>/<config>/
├── seed.txt
├── _traj_data/
├── data/episode0.hdf5
├── video/episode0.mp4
└── scene_info.json
```

其中，`data/episode*.hdf5` 是训练 policy 的主要数据；`video/episode*.mp4` 用于人工复查；`seed.txt` 记录可复现的成功 seed；`_traj_data/episode*.pkl` 保存 scripted trajectory；`scene_info.json` 保存 episode 级场景信息。

采集时是否写入某类观测，由 `task_config/demo_clean.yml` 和 `task_config/demo_randomized.yml` 中的 `data_type` 控制：

```yaml
data_type:
  rgb: true
  third_view: false
  depth: false
  pointcloud: false
  observer: false
  endpose: true
  qpos: true
  mesh_segmentation: false
  actor_segmentation: false
```

默认配置可以概括为：

```text
RGB + qpos + endpose
```

默认训练数据中最需要关注三类信息：

| 信息 | HDF5 中的位置/含义 | 用途 |
|---|---|---|
| RGB 图像 | `/observation/<camera_name>/rgb` | policy 的视觉输入 |
| 关节状态 | `joint_action/*` | joint-control policy 的状态和动作来源 |
| 末端位姿 | `endpose/*` | 末端控制、轨迹分析或对齐 end-effector 动作 |

默认相机会采集：

```text
head_camera
left_camera
right_camera
```

以 ACT 为例，`policy/ACT/process_data.py` 会把 RoboTwin 的相机名转换成 ACT 训练格式：

| RoboTwin camera | ACT dataset name |
|---|---|
| `head_camera` | `cam_high` |
| `left_camera` | `cam_left_wrist` |
| `right_camera` | `cam_right_wrist` |

所以，采集阶段的 `camera` 和 `data_type` 必须与后续 policy 的 `process_data` / `deploy_policy.py` 对齐。比如关闭腕部相机后继续使用默认 ACT 处理脚本，就可能出现预期 key 不存在的问题。

## 动作接口

RoboTwin 的 policy 评测不是通过 `gym.make(...)` 直接 step，而是通过官方 policy 模板接入环境。`policy/Your_Policy/deploy_policy.py` 中给出了推荐接口：

```python
TASK_ENV.take_action(action, action_type='qpos') # joint control: [left_arm_joints + left_gripper + right_arm_joints + right_gripper]
```

模板也给出了末端控制形式：

```python
TASK_ENV.take_action(action, action_type='ee') # endpose control: [left_end_effector_pose (xyz + quaternion) + left_gripper + right_end_effector_pose + right_gripper]
```

接入 policy 时最重要的是确认模型输出和 `action_type` 一致：

| `action_type` | 动作含义 | 常见使用场景 |
|---|---|---|
| `qpos` | 左臂关节 + 左夹爪 + 右臂关节 + 右夹爪 | ACT、DP 等 joint-control baseline |
| `ee` | 左末端位姿 + 左夹爪 + 右末端位姿 + 右夹爪 | 末端位姿控制 policy |

模板注释还提到 `delta_ee`，但写文档或复现实验时，应以当前项目实际支持路径为准，不要把模板注释直接当作已验证 benchmark 设置。

## 具体 Policy 子章节

当前项目的 `policy/` 目录中，baseline 的入口并不完全相同。具体训练与评测命令放在下面的子文件夹中：

| 子章节 | 适用对象 | 当前项目中的入口 |
|---|---|---|
| [官方 Policy 总览](05-policy-training-and-evaluation/01-policy-overview.md) | 说明官方有哪些 policy，本手册展开哪些可执行流程 | Usage 手册与项目 `policy/` 目录 |
| [ACT：训练与评测](05-policy-training-and-evaluation/02-act.md) | ACT imitation learning baseline | `process_data.sh`、`train.sh`、`eval.sh` |
| [DP：训练与评测](05-policy-training-and-evaluation/03-dp.md) | Diffusion Policy baseline | `process_data.sh`、`train.sh`、`eval.sh` |
| [Pi0：训练与评测](05-policy-training-and-evaluation/04-pi0.md) | Pi0 / OpenPI policy | `process_data_pi0.sh`、`generate.sh`、`finetune.sh`、`eval.sh` |

## 统一评测流程

无论使用哪种 policy，多数评测脚本最终都会进入：

```text
script/eval_policy.py
```

当前 `script/eval_policy.py` 中默认：

```python
test_num = 100
```

也就是说，单任务评测默认统计 100 个可测 episode 的 closed-loop success rate。

## 结果保存与指标

`eval_policy.py` 会创建：

```text
eval_result/${task_name}/${policy_name}/${task_config}/${ckpt_setting}/${timestamp}/
```

如果 `eval_video_log: true`，视频也会保存在该目录下。最终结果文件为：

```text
_result.txt
```

单任务指标：

```text
task_success_rate = success_count / 100
```

多任务平均：

```text
average_success_rate = mean(task_success_rate_1, ..., task_success_rate_N)
```

Easy/Hard 应分开报告：

```text
easy_success_rate = success_rate(task_config = demo_clean)
hard_success_rate = success_rate(task_config = demo_randomized)
```

不要把 `demo_clean` 和 `demo_randomized` 的结果混成一个平均分，除非明确说明这是自定义综合指标。

## 推荐结果表

结果表应直接填写实际评测结果或官方给出的结果，下面以 Pi0 的官方结果为例：

| task display | task_name | Pi0 Easy | Pi0 Hard |
|---|---|---:|---:|
| Adjust Bottle | `adjust_bottle` | 90% | 56% |
| Beat Block Hammer | `beat_block_hammer` | 43% | 21% |
| Blocks Ranking RGB | `blocks_ranking_rgb` | 19% | 5% |
| Blocks Ranking Size | `blocks_ranking_size` | 7% | 1% |
| Click Alarmclock | `click_alarmclock` | 63% | 11% |

其中 Easy / Hard 应分别对应前文的 `demo_clean` / `demo_randomized`。