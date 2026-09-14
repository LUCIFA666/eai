# 硬件检查与标定

本节把机器人从"通电"带到"可编程、观测可信"的状态:先做 bring-up 与健康检查(上电清单、驱动/看门狗/急停、低速动作测试),再做传感器部署与标定(相机/IMU 安装、内参与手眼标定、时间同步)。产物是一份可复用的 `bringup_report.yaml` 与标定结果。一句话:采集出问题,多半不是模型不行,而是相机、时间戳、坐标系、动作对齐错了。

## 本组页面

| 三级页面 | 重点 |
|---|---|
| [上电检查](03-hardware-checks-and-calibration/01-power-on-checklist.md) | 上电前检查、通信检查、关节/夹爪状态、低速动作测试 |
| [Driver、Watchdog 与 E-stop](03-hardware-checks-and-calibration/02-driver-watchdog-estop.md) | 驱动、看门狗与急停链路(E-stop 概念在此定义) |
| [RGB-D 与 IMU 部署](03-hardware-checks-and-calibration/03-rgbd-imu.md) | 相机/IMU 选择与安装、避遮挡与刚性支架 |
| [时间同步与外参标定](03-hardware-checks-and-calibration/04-time-sync-calibration.md) | 内参/手眼标定、多路时间戳对齐、外参维护 |

标定算法原理见第 3 章相机标定。
