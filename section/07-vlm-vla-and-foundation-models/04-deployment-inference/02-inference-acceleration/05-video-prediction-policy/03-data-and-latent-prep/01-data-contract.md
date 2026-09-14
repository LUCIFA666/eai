# 数据 contract

目标：明确 VPP 这一类项目期待的数据目录长什么样，annotation JSON 里最关键的字段有哪些。

## 最常见的目录形状

可以先把目标目录想象成这样：

```text
dataset_root/
├── annotation/
│   ├── train/
│   └── val/
├── videos/
│   ├── train/
│   └── val/
└── latent_videos/
    ├── train/
    └── val/
```

如果有多相机，每个 episode 下面往往还会再分相机编号或相机文件。

## annotation 里最关键的字段

从项目代码可以反推出，一个样本最常用的字段通常包括：

- `texts`
- `videos`
- `latent_videos`
- `episode_id`
- `video_length`
- `states`
- `actions`

其中：

- 第一阶段更关心文本、视频和 latent
- 第二阶段还会继续依赖状态和动作

## `videos` 和 `latent_videos` 为什么要同时存在

- `videos`：更适合可视化和调试
- `latent_videos`：更适合正式训练和高效读取

这也是为什么很多时候你会看到项目一边保存 mp4，一边保存 `.pt` latent 文件。

## 多相机要特别注意什么

这类 VPP 项目的一个常见隐含假设是：

- 相机数量和顺序是稳定的
- annotation 里的顺序和训练时读取顺序一致

如果训练时是：

1. 静态相机
2. 夹爪相机
3. 侧视相机

但部署时传入顺序变了，模型通常不会报 shape 错，但效果会明显异常。

## CALVIN 路线和 xbot 路线的数据 contract 不同吗

方法思想相同，但接口细节不同：

- CALVIN 路线更多依赖它自己的数据模块和 benchmark 约定
- xbot / xhand 路线更依赖作者自定义的 JSON、状态和动作定义

所以“能跑 CALVIN”并不自动等于“你已经知道怎么迁自己的机器人数据”。

## 小结

- VPP 的数据核心是 `annotation + videos + latent_videos`。
- 多相机顺序、状态定义和动作定义都属于 contract 的一部分。
- 这一步如果没定义清楚，后面训练很容易看起来“能跑但不对”。

## 导航

- 上一节：[数据组织与 latent 预处理](../03-data-and-latent-prep.md)
- 返回上级：[数据组织与 latent 预处理](../03-data-and-latent-prep.md)
- 下一节：[`step1_prepare_latent.py` 做了什么](02-step1-prepare-latent.md)
