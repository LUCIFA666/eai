# 空间定位与语义地图

目标：把几何地图升级成带空间记忆和任务语义的长期环境表示，让机器人不仅知道“环境长什么样”，还知道“自己在哪里、目标在哪里、关系是否还有效”。

这一节是整章里最偏“长期记忆”的部分。前面几节主要关心单帧或短时感知是否可靠；这里开始处理更长程的问题：

- 机器人自己在环境中的位置如何持续维护。
- 地图如何在多次任务之间继续复用。
- 语义标签、对象实例和空间关系怎样叠到几何地图上。
- 下游如何从“地图里有东西”升级到“地图里有可查询任务关系”。

## 这一节的主线

```text
relative motion
  -> localization
  -> map maintenance
  -> semantic lifting
  -> scene graph
  -> long-horizon task query
```

这条线拆成两页：

- [空间定位与建图](05-spatial-localization-and-semantic-maps/01-spatial-localization-mapping.md) 负责讲 VO、VIO、SLAM、重定位和地图维护。
- [语义地图与 3D 场景图](05-spatial-localization-and-semantic-maps/02-semantic-scene-graphs.md) 负责讲开放词汇 3D 语义、实例融合和场景图查询。

## 这一节和前后几节怎么分工

这一节不重新展开：

- 局部几何怎样构建，那是 [几何感知基础](01-geometric-perception-foundations.md) 的问题。
- 单个对象怎样检测和 pose，那是 [对象感知](02-object-perception.md) 的问题。
- 最终怎样把地图和对象装进统一 observation，那是 [感知接口与闭环](06-perception-interface-and-closed-loop.md) 的问题。

这一节补的是“长期空间上下文”这一层。没有这一层，前面很多结果只能在当前帧成立，很难支撑长程任务和跨回合复盘。

## 学完这一节，最好能带走什么

- 能区分 VO、VIO、SLAM、relocalization、semantic map、scene graph 各自负责什么。
- 能解释为什么语义地图依赖稳定定位，而不是“对象越多越好”。
- 能设计最小 `localization_state` 和 `scene_graph_query_result`。
- 能判断地图失配、语义错位和重定位失败分别会怎样伤到下游。

## 建议阅读顺序

1. 先读 [空间定位与建图](05-spatial-localization-and-semantic-maps/01-spatial-localization-mapping.md)。
2. 再读 [语义地图与 3D 场景图](05-spatial-localization-and-semantic-maps/02-semantic-scene-graphs.md)。
3. 读完后再回到 [感知接口](06-perception-interface-and-closed-loop/01-perception-interface.md)，会更容易理解为什么 observation 里一定要带 `map_id`、`frame_graph` 和 `tracking_state`。

## 导航

- 上一节：[视触融合](04-interactive-perception/08-visuo-tactile-fusion.md)
- 下一节：[空间定位与建图](05-spatial-localization-and-semantic-maps/01-spatial-localization-mapping.md)
- 返回本章：[感知与三维视觉](README.md)
