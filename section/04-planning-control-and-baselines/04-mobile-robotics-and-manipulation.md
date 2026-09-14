# 移动机器人与移动操作

本节介绍移动机器人导航、视觉/语义地图接口、视觉语言导航与移动操作，说明底盘导航、环境理解、语言目标、机械臂规划和全身协调之间的关系。

本节不是把所有 SLAM、导航、VLN 方法都展开成综述，而是围绕具身智能系统里最常见的一条执行链路组织：

```text
任务目标 / 语言指令
  -> 目标地点、对象或语义区域
  -> 定位与地图 / 语义地图
  -> 全局路径
  -> 局部避障与速度控制
  -> 到达后移动操作或交互
```

## 章节结构

| 页面 | 要写的内容 | 边界 |
|---|---|---|
| [移动机器人导航栈](04-mobile-robotics-and-manipulation/01-navigation-stack.md) | Nav2 风格导航管线、全局规划、局部规划、costmap、恢复行为、导航日志与失败分类 | 不展开完整 SLAM 数学推导 |
| [视觉 SLAM 与语义地图接口](04-mobile-robotics-and-manipulation/02-visual-slam-and-semantic-map-interface.md) | 视觉/视觉惯性定位、地图坐标系、语义地图、对象/区域到导航目标的转换、与第 3 章感知接口的衔接 | 不做 SLAM 算法大全 |
| [视觉语言导航与长程任务](04-mobile-robotics-and-manipulation/03-vln-and-long-horizon-navigation.md) | VLN/VLM 导航任务、语言目标 grounding、子目标选择、长程任务进度、仿真 benchmark 与真实导航差异 | 不把 VLN benchmark 细节搬进本章，评测回第 8 章 |
| [移动操作](04-mobile-robotics-and-manipulation/04-mobile-manipulation.md) | 导航到位、base placement、机械臂可达性、分段规划与全身规划、导航失败对操作的影响 | 不重复机械臂运动规划和全身控制细节 |
