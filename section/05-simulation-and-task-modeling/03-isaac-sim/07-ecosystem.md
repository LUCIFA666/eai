# 仿真接口

前面几章已经能搭场景、导入机器人、控制、观测和采集数据。大多数 Isaac Sim 入门实验到这里就够了；只有当你需要把仿真里的状态、传感器或控制接口接到外部节点时，才需要这一章。

## 本节目标

本节围绕下面几个问题展开：

1. Python 主循环、Action Graph / OmniGraph 和 ROS 2 各自适合负责什么？
2. 数据发布或图节点运行时，时间同步和 topic 应该怎么检查？
3. 什么时候需要接外部生态，什么时候继续用纯脚本更合适？

这一章只讲仿真接口，不展开真机部署：先用 OmniGraph / Action Graph 理解 Isaac Sim 里“每帧数据流”如何组织，再用 ROS 2 Bridge 把 `/clock`、`/joint_states`、`/tf`、相机等仿真数据发布成标准 topic，方便接 RViz、MoveIt / Nav2 或自写 ROS 2 节点。

## ROS 2 在本单元里的边界

ROS 2（Robot Operating System 2）不是机器人硬件，而是一套机器人软件框架。它提供节点（node）、话题（topic）、服务、参数、时间同步等通信与组织机制，让感知、定位、规划、控制等模块可以通过标准接口组合起来。RViz（可视化）、Nav2（导航）、MoveIt（机械臂规划）等工具，也都建立在这套生态之上。

本单元只使用 ROS 2 的“仿真接口”这一部分：让 Isaac Sim 发布和订阅标准 topic。它不讲硬件驱动、不讲真机部署，也不把 ROS 2 当作必须路径。你只有在需要外部 ROS 2 节点、RViz 可视化或复用 ROS 2 算法栈时，才需要进入这一章。

## 学习路径

| 页面 | 重点 | 学习产出 |
|---|---|---|
| [OmniGraph / Action Graph](07-ecosystem/01-omnigraph.md) | 节点图、tick、传感器 / ROS 节点的底层机制 | 看懂数据流图与节点连法 |
| [ROS 2 Bridge](07-ecosystem/02-ros2-bridge.md) | 发布 clock / joint_states / TF / 相机、RMW / DDS | 把仿真数据接到外部 ROS 2 节点 |

## 导航

- 返回上级：[Isaac Sim](../03-isaac-sim.md)
- 上一页：[任务、数据采集与合成数据](06-task-and-data.md)
