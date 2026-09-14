# 观测与传感器

机器人能按目标运动之后，下一步是把世界、机器人和任务状态读回来。观测不是简单截图：相机和 RTX Lidar 要经过渲染管线，IMU 和接触传感器来自 PhysX，关节状态和物体状态还要和动作、step、时间戳对齐。否则图像和点云能存下来，数据却未必能训练。

## 本节目标

本节围绕下面几个问题展开：

1. 相机、深度、分割、Lidar、IMU 或状态量各自适合什么任务？
2. 观测和 action、step、时间戳之间应该怎样对齐？
3. 如何判断读到的数据不是空帧、旧帧或错误坐标系？

这一部分专门讲“读回来”：先讲相机与多通道图像，再补齐 Lidar / IMU / 接触传感器，最后把观测和动作接成一条最小闭环，为下一部分的任务定义和数据采集做准备。

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [相机与传感器观测](05-observation/01-cameras-and-sensors.md) | 怎么创建相机、预热渲染、读取 RGB / 深度 / 分割？ | Camera prim、render product、frame buffer、多视角 |
| [RTX Lidar / IMU / 接触传感器](05-observation/02-lidar-imu.md) | 相机之外还常用哪些传感器？ | RTX Lidar 点云、IMU、ContactSensor、渲染 vs PhysX |
| [Observation → Action 闭环](05-observation/03-observation-loop.md) | 观测、决策、动作、step、记录之间怎么对齐？ | `obs_t + action_t -> obs_{t+1}`、step_index、传感器频率 |

## 和前后部分的关系

| 前后关系 | 分工 |
|---|---|
| 上一部分控制 | 负责把动作发出去，让机器人按目标动 |
| 本部分观测与传感器 | 负责把状态、图像、点云、IMU、接触读回来，并和动作对齐 |
| 下一部分任务与数据 | 在观测闭环外面加 episode、成功判定、采集、回放、质检和合成数据生成 |

## 导航

- 返回上级：[Isaac Sim](../03-isaac-sim.md)
- 上一页：[控制](04-control.md)
- 下一页：[任务、数据采集与合成数据](06-task-and-data.md)
