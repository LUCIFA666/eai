# 时间同步

本节只介绍多相机画面和动作数据同步。时间戳对齐错误会导致 observation 与 action 错位，模型学到错误因果关系。

## LeRobot 架构下多传感器对齐方案

最简单可靠的方法是在数据采集主循环中统一打时间戳，如果机械臂的底层控制使用ROS的话，可以同时订阅关节角和相机的话题来实现采集数据的同步：

```python
import time
from lerobot.datasets import LeRobotDataset

obs = robot.get_observation()          # 内部已包含各相机与关节时间
action = policy(obs)
timestamp = time.time()                # 统一主机时间

episode.append({
    "observation": obs,
    "action": action,
    "timestamp": timestamp
})
```

LeRobot 的 `get_observation` 返回的字典中可加入 `timestamp` 字段，由上层保证一致性。

但很多机器人并未使用LeRobot的生态，更多的是采用 ROS 系统进行数据的管理。下面对ALOHA的代码进行拆解，讲解其使用的多传感器 ROS 系统中，数采中更精细的时间同步机制。

## 基于 ROS Header 时间戳的软同步

与 LeRobot 在主循环中统一打主机时间戳不同，ROS 生态的做法是利用每条 ROS 消息自带的 `header.stamp` 时间戳进行对齐。以下结合 ALOHA 实际代码中 `/camera_f/color/image_raw`（头部彩色相机）、`/camera_l/color/image_raw`（左腕彩色相机）、`/camera_r/color/image_raw`（右腕彩色相机）这三个相机话题，以及 `/puppet/joint_left`、`/puppet/joint_right` 这两个从臂关节角话题作为例子，逐步说明同步原理。

`RosOperator` 在初始化时为每个话题建立一个 `deque` 缓冲区，相机的三个话题分别对应 `img_front_deque`、`img_left_deque`、`img_right_deque`，关节角的两个话题分别对应 `puppet_arm_left_deque`、`puppet_arm_right_deque`。ROS 订阅初始化时设置 `queue_size=1000` 和 `tcp_nodelay=True`，前者提供足够的内部缓冲防止消息丢失，后者禁用 TCP Nagle 算法以降低传输延迟。各回调函数将收到的 `Image` 或 `JointState` 消息追加到对应的 `deque` 中，并限制最大长度为 2000，超出时从左侧丢弃最旧数据。

同步的核心逻辑在 `get_frame()` 方法中。它首先检查这五个 `deque` 是否都有至少一条消息——只要 `/camera_f`、`/camera_l`、`/camera_r`、`/puppet/joint_left`、`/puppet/joint_right` 中任意一个 `deque` 为空，`get_frame()` 直接返回 `False`，本轮不产出任何数据。接着计算同步参考时间戳 `frame_time`：比较这五个 Topic 各自最新消息的 `header.stamp`，取出其中的最小值。举例来说，假设某一时刻三个相机的最新时间戳分别是 `10.02`、`10.05`、`10.03`，两个关节角的最新时间戳分别是 `10.01` 和 `10.04`，那么 `frame_time` 就是 `10.01`——即 `/puppet/joint_left` 的最新消息最旧，整个同步就以它为基准。取最小值而不是最大值，是为了迁就最慢的那个话题，保证每个话题都至少有一条消息的时间戳在参考点之后。

然后进入验证阶段：逐一检查各 `deque[-1]` 的时间戳是否大于等于 `frame_time`。沿用上面的例子，`/puppet/joint_left` 的最新时间戳 `10.01` 等于 `frame_time`，其他四个话题的最新时间戳都大于 `10.01`，验证全部通过。但如果 `/camera_l` 的最新时间戳只有 `9.98`，说明左相机还没来得及收到足够新的数据，本轮同步失败，`get_frame()` 返回 `False`，主循环打印一次 `syn fail` 后进入下一轮等待。

验证通过后，对每个 `deque` 执行清理操作：从队列头部不断弹出时间戳早于 `frame_time` 的消息，直到队列头部的消息时间戳刚好大于等于 `frame_time`。清理完成后，从每个 `deque` 的头部取出一条消息：从 `img_front_deque` 取出 `/camera_f` 的图像帧，从 `img_left_deque` 取出 `/camera_l` 的图像帧，从 `img_right_deque` 取出 `/camera_r` 的图像帧，从 `puppet_arm_left_deque` 和 `puppet_arm_right_deque` 取出左右从臂的关节角。这五条消息的时间戳都落在 `frame_time` 附近，构成了一组时间对齐的 observation。对于实际数据采集中可能启用的深度图和末端位姿等额外话题，同步逻辑完全一致，只是在计算 `frame_time` 和验证时多加入几个 `deque` 而已。

主循环 `process()` 以 `rospy.Rate(frame_rate)` 控制频率（默认 30Hz），每次迭代调用 `get_frame()`。如果返回 `False` 则跳过本轮继续等待；如果返回对齐后的数据，则将图像和关节角组装成 `dm_env.TimeStep`，同时把主臂关节角作为 action 记录到 `actions` 列表中。第一帧使用 `StepType.FIRST` 标记，后续帧使用 `StepType.MID`。

这种方式相比 `message_filters.ApproximateTimeSynchronizer` 更加灵活：可以动态适配是否启用深度图、末端位姿、里程计等可选话题，不需要在初始化时固定同步策略；同步失败时也能清晰输出提示而不静默丢帧。但它的前提是所有 ROS 节点间的时钟已经通过 NTP 或 Chrony 完成同步，否则不同机器的 `header.stamp` 本身就不在一个时间基准上，对齐也就失去了意义。
