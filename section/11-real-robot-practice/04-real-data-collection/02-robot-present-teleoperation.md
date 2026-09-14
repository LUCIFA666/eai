# 机器人在场遥操作采集

本组讲机器人在采集现场、由人实时操控产生数据的方式——直接得到真实机器人的 observation/state/action/timestamp,是训练 ACT/Diffusion Policy/OpenVLA/π0/SmolVLA 最直接的数据来源,也是本章重点。按上手成本与表达力从低到高列 7 种。有名系统(ALOHA/GELLO/VR)的硬件与设计见第 6 章遥操作系统,本组从真机采集视角讲选型与现场记录。

## 本组页面

| 四级页面 | 重点 |
|---|---|
| [SpaceMouse](02-robot-present-teleoperation/01-spacemouse.md) | 最低成本单臂遥操作 |
| [VR 遥操作](02-robot-present-teleoperation/02-vr-teleoperation.md) | 符合 3D 直觉,适合双臂/移动 |
| [GELLO](02-robot-present-teleoperation/03-gello.md) | 运动学等比 leader,数据质量高 |
| [主从同构 / ALOHA](02-robot-present-teleoperation/04-leader-follower-aloha.md) | 双臂高质量数据标杆 |
| [手把手拖动示教](02-robot-present-teleoperation/05-kinesthetic-teaching.md) | 轨迹最干净,最直觉 |
| [手柄 / 键盘](02-robot-present-teleoperation/06-gamepad-keyboard.md) | 最小可运行 teleop |
| [手机 / Web 远程](02-robot-present-teleoperation/07-phone-web-remote.md) | 远程与众包采集 |
