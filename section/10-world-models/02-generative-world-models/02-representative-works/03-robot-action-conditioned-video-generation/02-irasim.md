# IRASim

目标：说明 IRASim 如何作为交互式真机动作模拟器，给定历史观测和动作轨迹生成机器人执行视频。

## 需要覆盖

- Action trajectory conditioning：动作轨迹如何作为生成条件。
- 真实机器人数据如何进入生成模型训练。
- Policy evaluation / action proposal selection 的使用方式。
- 和普通视频预测的区别：IRASim 面向机器人交互和动作评估。
- 代码入口：https://github.com/bytedance/IRASim

- 返回上级：[机器人动作条件视频生成](../03-robot-action-conditioned-video-generation.md)
