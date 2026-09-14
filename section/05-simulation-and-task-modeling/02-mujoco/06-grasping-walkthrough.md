# 抓取实战

让机械臂把桌上的方块抓起来、搬到指定位置再放下，是操作类任务里最基本的一课。接下来就把这套完整流程从零搭出来、跑通，并学会在它出错时怎么排查。

## 前置概念

读这一节前，建议先理解：

- **MJCF 场景拼装**（详见 [MJCF 整体骨架](02-modeling/01-mjcf-skeleton.md)）：include + worldbody。
- **actuator 与接触**（详见 [控制与物理](03-control-and-physics.md)）：抓取这一节里一直在和这两个东西打交道。
- **多视角渲染**（详见 [相机与多视角](04-observation-and-rendering/03-camera-and-multiview.md)）：失败排错时往往最有用的工具。

## 学习路径

| 小节 | 读完能回答 | 重点 |
|---|---|---|
| [搭场景](06-grasping-walkthrough/01-scene-setup.md) | 抓取场景的最小构成？ | 桌子、方块、目标位、相机、光源 |
| [末端控制](06-grasping-walkthrough/02-end-effector-control.md) | 怎么让末端到达一个目标位置？ | 关节空间 vs 末端空间、IK 简介 |
| [夹爪控制](06-grasping-walkthrough/03-gripper-control.md) | 怎么稳定夹住物体？ | 夹爪 actuator、接触力反馈、防滑 |
| [完整抓取流程](06-grasping-walkthrough/04-full-pick-pipeline.md) | reach → grasp → lift → place 怎么拼？ | 状态机、失败检测、完整代码 |
| [调试与调参](06-grasping-walkthrough/05-debug-and-tune.md) | 失败了怎么排查？ | 多视角观察、接触可视化、调参顺序 |

## 导航

- 上一节：[接口与生态](05-interfaces-and-ecosystem.md)
- 返回上级：[MuJoCo](../02-mujoco.md)
- 下一节：[MJX 与 GPU 并行](07-mjx-and-gpu.md)
