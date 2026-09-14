# 几何感知基础

目标：把像素、深度和多帧观测整理成带坐标系、可查询、可进入下游执行链的几何结果。

这一节是整章里最偏“底座”的一组页面。它回答的是下面这些更基础、也更硬的几何问题：

- 一张图里的像素为什么能对应到空间射线。
- 相机坐标系怎样和机器人基座、末端执行器坐标系连起来。
- 深度图怎样变成点云，点云怎样变成可复用场景表示。
- 多视角几何结果怎样对齐、融合并持续维护。

如果这一层没有打稳，后面的检测、位姿、抓取位姿和避障距离都会被系统性拖偏。因为后面所有“对象在哪里”“接触点在哪里”“抓取朝哪个方向接近”，最终都要回到几何坐标上。

## 这一节的主线

可以把这一节理解成一条从像素到场景记忆的连续链路：

```text
像素
  -> 相机模型与标定
  -> 手眼外参
  -> RGB-D 反投影
  -> 点云对齐
  -> 多帧融合
  -> 场景表示
```

沿着这条链往前走，每一页都在压缩一种几何不确定性：

- [相机标定](01-geometric-perception-foundations/01-camera-calibration.md) 负责把像素和光学几何关系校准到位。
- [手眼标定](01-geometric-perception-foundations/02-hand-eye-calibration.md) 负责把相机看到的结果转换到机器人真正执行的坐标系。
- [RGB-D 与点云](01-geometric-perception-foundations/03-rgbd-pointcloud.md) 负责把二维观测反投影成带 `frame_id` 的三维点。
- [点云配准](01-geometric-perception-foundations/04-pointcloud-registration.md) 负责把多次观测对齐到同一几何参考系。
- [三维重建与场景表征](01-geometric-perception-foundations/05-3d-reconstruction.md) 负责把多帧观测变成可查询的空间记忆。
- [NeRF / 3DGS 在机器人中的应用](01-geometric-perception-foundations/06-nerf-3dgs-robotics.md) 负责说明高保真辐射场表示什么时候值得进入具身系统。

## 这一节和后面几节怎么分工

这一节只讲“几何基础层”，不讲：

- 哪个对象是任务目标。
- 目标该不该抓、从哪抓。
- 接触后动作是否成功。

这些问题会分别在后面几节处理：

- [对象感知](02-object-perception.md) 负责从场景中提取对象候选与 6D pose。
- [可交互感知](04-interactive-perception.md) 负责从对象进一步走到接触点、抓取位姿和接触验证。
- [感知接口与闭环](06-perception-interface-and-closed-loop.md) 负责把前面所有几何和语义结果统一打包成 observation。

## 学完这一节，最好能带走什么

- 能解释内参、畸变、外参、点云、体素、场景表示之间的关系。
- 能说清一个几何结果至少要带什么元数据，例如 `frame_id`、`timestamp`、`pose_source`。
- 能判断一份几何结果是不是已经足够进入 pose、抓取或避障链路。
- 能在下游出错时反查：问题出在标定、外参、深度、配准，还是多帧融合。

## 建议阅读顺序

1. 先读 [相机标定](01-geometric-perception-foundations/01-camera-calibration.md) 和 [手眼标定](01-geometric-perception-foundations/02-hand-eye-calibration.md)。
2. 再读 [RGB-D 与点云](01-geometric-perception-foundations/03-rgbd-pointcloud.md) 与 [点云配准](01-geometric-perception-foundations/04-pointcloud-registration.md)。
3. 然后读 [三维重建与场景表征](01-geometric-perception-foundations/05-3d-reconstruction.md)。
4. 最后用 [NeRF / 3DGS 在机器人中的应用](01-geometric-perception-foundations/06-nerf-3dgs-robotics.md) 建立“高保真表示什么时候值得上”的判断。

## 导航

- 上一节：[感知与三维视觉](README.md)
- 下一节：[相机标定](01-geometric-perception-foundations/01-camera-calibration.md)
- 返回本章：[感知与三维视觉](README.md)
