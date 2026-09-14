# 场景构建与坐标约定

Isaac Sim 的场景不是写在一个文件里，而是用 USD 的 Stage 和 Prim "搭"出来的。这一章先讲清 USD / Stage / Prim 的组合思维，再动手往世界里加地面、灯光和物体，最后厘清坐标系与单位这个最容易埋雷的细节。

## 本节目标

本节围绕下面几个问题展开：

1. 场景世界由哪些对象、路径和坐标关系组成？
2. 最小场景应该先放哪些元素，为什么？
3. 地面、光源、动态物体、单位和坐标系分别影响什么结果？
4. 如何用画面、位置数值或日志判断场景搭对了？

## 学习路径

| 页面 | 重点 | 学习产出 |
|---|---|---|
| [USD、Stage 与 Prim](02-building-a-world/01-usd-stage-prim.md) | Stage、Prim、属性、引用 / 分层组合 | 看懂并定位场景树里的任意一项 |
| [搭一个场景](02-building-a-world/02-build-a-scene.md) | `World`、地面 / 光照、动态物体、step 循环 | 跑通一个最小场景，并能继续拆读光源、物体和验证细节 |
| [坐标系与单位](02-building-a-world/03-frames-and-units.md) | 世界 / 局部坐标、朝向、米 / 千克单位约定 | 避免位姿与尺度类错误 |

## 导航

- 返回上级：[Isaac Sim](../03-isaac-sim.md)
- 上一页：[认识 Isaac Sim](01-getting-started.md)
- 下一页：[机器人资产与物理配置](03-robot-and-physics.md)
