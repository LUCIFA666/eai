# 感知与三维视觉

目标：把“机器人看到了什么”组织成“机器人拿到了什么可执行、可追责、可复盘的观测结果”。

这一章关注的不是单个视觉模型有多强，而是整条感知链路能不能稳定进入动作系统。对具身智能来说，感知结果至少要回答下面这些问题：

- 目标在哪里。
- 这个“哪里”是在哪个坐标系里表达的。
- 结果现在还新不新鲜。
- 它能不能安全交给规划器、控制器或策略模型。
- 如果执行失败，系统能不能追溯是识别错了、几何错了，还是接触后失败了。

## 先看整条链路

```text
像素 / 深度
  -> 相机模型与标定
  -> 坐标系与手眼外参
  -> RGB-D 反投影与点云
  -> 多帧融合与场景表征
  -> 目标候选（bbox / mask / label）
  -> 6D pose
  -> 可交互区域、接触点与抓取位姿
  -> 触觉 / 力觉证据
  -> 空间定位与语义地图
  -> 感知接口与闭环
```

这条链路的每一环都在压缩一种不确定性：

- 标定在解决“像素和光学几何的关系准不准”。
- 点云和重建在解决“二维观测怎样恢复成可复用的三维表示”。
- 检测与分割在解决“场景里哪一块区域才是任务相关对象”。
- 位姿估计在解决“对象整体在空间里的位置和朝向是什么”。
- 可供性和抓取位姿在解决“该碰哪里、沿什么方向接近、怎样抓更稳”。
- 接触观测在解决“真正接触后，动作是不是成功了”。
- 空间定位与语义地图在解决“机器人自己现在在环境中的哪里，以及地图如何服务长程任务”。
- 感知接口与闭环在解决“这些结果怎样统一交给下游系统，失败时怎样重观察或降级”。

## 章节结构

| 二级单元 | 三级页面 | 说明 |
|---|---|---|
| [几何感知基础](01-geometric-perception-foundations.md) | 相机标定、手眼标定、RGB-D 与点云、点云配准、三维重建与场景表征、NeRF 与 3DGS | 把像素、深度和多帧观测变成带坐标系的几何表示 |
| [对象感知](02-object-perception.md) | 检测与分割、GroundingDINO 与 SAM、Mask 质量与时序稳定、点跟踪、位姿估计、PnP 与 ICP、FoundationPose 类方法 | 从场景中提取对象候选、稳定对象边界并恢复可执行 6D pose |
| [视觉基础模型](03-vision-foundation-models.md) | CLIP 与 SigLIP、DINO 与 DINOv2、Depth Anything、Point Foundation Model、模型差异与选型 | 说明视觉基础模型在机器人感知链中补哪一块能力 |
| [可交互感知](04-interactive-perception.md) | 可供性与交互区域、Affordance Heatmap、3D Contact Point、抓取位姿生成、触觉、力觉与接触观测、接触事件与滑移检测、力控证据链、视触融合 | 从“认出对象”走到“知道怎样碰、抓、验证和复盘” |
| [空间定位与语义地图](05-spatial-localization-and-semantic-maps.md) | 空间定位与建图、语义地图与 3D 场景图 | 维护机器人与环境的空间关系，并把几何地图升级为任务可用语义地图 |
| [感知接口与闭环](06-perception-interface-and-closed-loop.md) | 感知接口、感知输出规范、置信度与失败码、主动感知与重观察 | 把对象、地图、接触和失败信息组织成下游可消费的 observation，并形成重观察闭环 |

## 学完这一章，希望能带走什么

- 能解释内参、畸变、外参、手眼标定、深度、点云、位姿之间的因果关系。
- 能从像素坐标和深度值出发，说明一个 3D 点是怎样恢复出来的。
- 能区分检测、分割、跟踪、位姿估计、可供性、抓取位姿、接触事件各自负责什么。
- 能判断一份感知结果是不是已经足够进入机器人执行链，而不只是“模型有输出”。
- 能为对象、接触和地图结果设计统一 schema，至少包含 `frame_id`、`timestamp`、`confidence`、`staleness_ms`、`failure_code`。
- 能在抓取或移动失败时逆着链路排查：到底是目标没看见、边界不准、深度无效、位姿漂移、地图失效，还是接触后滑移。

## 建议边读边跑的最小实验

- `python labs/04-perception/camera_calibration_synthetic.py`
- `python labs/04-perception/coordinate_frame_demo.py`
- `python labs/04-perception/hand_eye_synthetic.py`
- `python labs/04-perception/rgbd_to_pointcloud.py`
- `python labs/04-perception/pnp_pose.py`
- `python labs/04-perception/icp_demo.py`
- `python labs/04-perception/clip_zero_shot.py`
- `python labs/04-perception/contact_event_demo.py`
- `python labs/04-perception/perception_observation_demo.py`

这些脚本的作用不是“炫技”，而是把抽象概念变成可以打印、可以存档、可以复盘的结果。

## 延伸阅读

- OpenCV Camera Calibration: https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html
- OpenCV calib3d: https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html
- Open3D Documentation: https://www.open3d.org/docs/latest/
- Segment Anything: https://github.com/facebookresearch/segment-anything

<!-- AUTO-TOC -->
