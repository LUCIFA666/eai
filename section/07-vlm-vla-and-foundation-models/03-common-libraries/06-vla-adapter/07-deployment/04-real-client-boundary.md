# 真实 Client 边界

目标：明确真实 ALOHA / Cobot Magic client 需要哪些额外条件，避免把 fake client 误当作真机教程或安全流程。

真实 client 入口是：

```text
experiments/robot/aloha/run_cobot_client.py
```

它依赖 ROS、真实相机、joint state topic、动作发布 topic，以及机器人本体的安全流程。本教程当前不展开真机执行，只说明源码边界和上线前需要确认的检查项。

## Real Client 数据流

真实 client 和 fake client 使用同一个 server 协议，区别在 observation 来源：

1. ROS subscriber 读取三路相机图像和左右臂 joint state。
2. `prepare_observation_for_server()` 把图像 resize 成 policy 输入尺寸。
3. payload 增加 `instruction` 和 `unnorm_key` 后，通过 `MsgPackHttpClientPolicy.infer()` 请求 `/act`。
4. client 读取 `response["actions"]`，截断到 `num_open_loop_steps` 并放入 `action_queue`。
5. 每个控制周期取一个 action，拆成左右臂 command 并发布到 ROS topic。

这条链路和 fake client 的接口一致，所以 fake client 通过是进入真机前的最低门槛。但 fake client 没有验证 ROS、硬件和安全条件。

## 真机前提

| 条件 | 说明 |
| --- | --- |
| ROS 环境 | 需要 `rospy`、`cv_bridge`、`sensor_msgs` 等。 |
| 相机输入 | ALOHA client 使用 front / left wrist / right wrist 三路图像，顺序要和训练数据一致。 |
| proprio/state | 需要真实左右臂 joint state，拼成 14 维 qpos，并与训练维度一致。 |
| action 发布 | 需要明确 absolute / relative action、左右臂拆分方式、发布频率和 topic。 |
| 安全策略 | 先设计限位、急停、人工接管、低速测试和空场景测试，再进入真实机器人执行。 |

## 默认 ROS Topic

`OpenVLAConfig` 中默认 topic 如下：

| Topic | 类型 | 作用 |
| --- | --- | --- |
| `/camera_f/color/image_raw` | `Image` | front camera 图像。 |
| `/camera_l/color/image_raw` | `Image` | left wrist camera 图像。 |
| `/camera_r/color/image_raw` | `Image` | right wrist camera 图像。 |
| `/puppet/joint_left` | `JointState` | 左臂 joint state。 |
| `/puppet/joint_right` | `JointState` | 右臂 joint state。 |
| `/master/joint_left` | `JointState` | 左臂 command 发布 topic。 |
| `/master/joint_right` | `JointState` | 右臂 command 发布 topic。 |
| `/odom_raw` | odometry 相关消息 | 可选底盘状态。 |
| `/cmd_vel` | velocity command | 可选底盘控制。 |

不同机器人或 ROS bridge 的 topic 命名可能不同。适配时可以先改 `OpenVLAConfig`，再用只读方式确认 topic 数据频率、时间戳和坐标语义，确认无误后再进入动作发布测试。

## 动作语义边界

真实 client 的动作拆分逻辑大致是：

```python
if cfg.use_relative_actions:
    target_state = curr_state + action
    left_action = target_state[:7]
    right_action = target_state[7:14]
else:
    left_action = action[:7]
    right_action = action[7:14]
```

因此部署前需要确认 checkpoint 训练的是 absolute joint target 还是 relative joint delta。这个配置错了，不一定会在软件层报错，但会让机器人执行完全不同的运动。

如果 `use_robot_base=True` 且 action 长度大于 14，client 还会把 `action[14:16]` 当作底盘速度发布。没有底盘或没有验证底盘控制协议时，不应打开这条路径。

## 真机前 Checklist

在真实机器人上执行前，至少应逐项确认：

| 检查项 | 要求 |
| --- | --- |
| fake client | 已经能稳定收到 `actions`，并记录 action shape。 |
| 低速策略 | 控制频率、速度限制、单步最大位移有明确上限。 |
| 急停 | 操作人员能在任何时刻物理急停或软件停止当前 trial。 |
| 人工接管 | client 支持人工停止，现场有明确接管流程。 |
| 空场景测试 | 不放任务物体，先验证动作方向和左右臂映射。 |
| topic 方向 | 订阅的是 state，发布的是 command，左右臂没有反接。 |
| 相机顺序 | front、left wrist、right wrist 与训练数据顺序一致。 |
| action 尺度 | `unnorm_key`、absolute/relative 语义、gripper/底盘通道都已确认。 |
| 日志记录 | 保存 server 命令、client 命令、task label、action shape、停止原因。 |

这些检查不保证任务成功，但能避免把部署通信问题、坐标错位和安全问题混在一起。

## 本教程如何处理

本节只把真实 client 作为后续扩展方向。当前可执行目标是 policy server + fake client sanity check；真机部署应单独成章，并先写完整安全 checklist、硬件适配说明和现场回滚流程。

## 小结

- real client 和 fake client 使用相同的 MsgPack HTTP `/act` 协议。
- 真机差异主要在 ROS topic、传感器同步、动作发布和安全策略。
- `use_relative_actions` 决定 action 是 delta 还是 target，需要和 checkpoint 训练语义一致。
- fake client 通过只是进入真机检查前的最低门槛，不能替代上机安全流程。

## 动手练习

1. 在 `run_cobot_client.py` 中找到 `OpenVLAConfig`，列出与你的机器人不同的 topic。
2. 找到 `use_relative_actions` 分支，解释 absolute 和 relative 两种语义对机器人运动的影响。
3. 根据本页 checklist，写出一次真机试运行前需要保存的五项证据。

## 导航

- 上一节：[ALOHA Fake Client](03-aloha-fake-client.md)
- 返回上级：[部署](../07-deployment.md)
- 下一节：[扩展边界](../08-extension.md)
