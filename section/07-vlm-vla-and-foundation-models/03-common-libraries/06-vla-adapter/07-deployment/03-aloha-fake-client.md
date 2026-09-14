# ALOHA Fake Client

目标：不接真实机器人，先用 ALOHA fake client 验证 MsgPack HTTP 通信、模型推理和 action shape。

相关入口：

```text
experiments/robot/aloha/run_fake_cobot_client.py
experiments/robot/aloha/eval_files/run_eval_client_fake.sh
```

fake client 会生成合成三视角图像、14 维 fake qpos 和 task description，然后向 policy server 请求 actions。它适合验证：

- server 地址是否可达。
- MsgPack payload 是否能被解析。
- checkpoint 是否能完成一次推理。
- 返回的 `actions` 数量和维度是否符合 ALOHA client 预期。

## 基本流程

先在 server 终端启动 policy server：

```bash
PRETRAINED_CHECKPOINT=/path/to/checkpoint_dir \
PORT=8888 \
DEVICE=0 \
bash experiments/robot/aloha/eval_files/deploy_server.sh
```

再在另一个终端运行 fake client：

```bash
bash experiments/robot/aloha/eval_files/run_eval_client_fake.sh
```

可以用环境变量覆盖默认配置：

```bash
VLA_SERVER_URL=http://127.0.0.1:8888 \
UNNORM_KEY=bowl_stack_and_shelf_aloha_realworld_50 \
TASK_LABEL="Use the right arm to stack the red bowl on the blue one." \
bash experiments/robot/aloha/eval_files/run_eval_client_fake.sh
```

`VLA_SERVER_URL` 应该是 client 能访问的地址。本机测试通常使用 `http://127.0.0.1:8888`；`0.0.0.0` 适合 server 监听，不适合作为 client 连接地址。

## Fake Stream

`FakeOpenVLAConfig` 默认生成一段 fake episode：

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| `sequence_length` | `260` | fake observation 序列长度。 |
| `num_joints` | `14` | ALOHA 双臂 qpos 维度。 |
| `image_height` / `image_width` | `480` / `640` | fake camera 原始图像大小。 |
| `num_open_loop_steps` | `25` | 每次请求后最多执行的动作数。 |
| `task_label` | `open the box` | 默认任务指令，可由 `TASK_LABEL` 覆盖。 |

每一帧 observation 包含：

```text
images/cam_high
images/cam_left_wrist
images/cam_right_wrist
qpos
```

进入 server 前，三路图像会 resize 到模型期望尺寸，并被包装成 `/act` payload。

## 核心循环

fake client 的主循环在 `run_inference_loop()`：

```python
if len(action_queue) == 0:
    observation = prepare_observation_for_server(...)
    response = client.infer(observation)
    actions = np.array(response["actions"])
    actions = actions[: cfg.num_open_loop_steps]
    action_queue.extend(actions)

action = action_queue.popleft()
```

这里有两个关键检查点：

1. `client.infer()` 能否成功完成一次 MsgPack HTTP 请求。
2. `response["actions"]` 能否转换成 numpy array，并切出至少一个动作。

如果这一步失败，优先查 server 日志、payload 字段和 `UNNORM_KEY`。如果这一步成功但真机失败，排查重点通常会转向 ROS topic、相机同步、动作发布或安全策略。

## 成功判据

一次 fake-client sanity check 可以按下面的标准判断是否通过：

| 检查 | 通过表现 |
| --- | --- |
| server 连接 | client 日志显示连接到 `http://127.0.0.1:8888/act` 或实际 server 地址。 |
| 请求成功 | 日志出现 `Requerying OpenVLA server...` 后没有 HTTP 异常。 |
| 动作返回 | 日志出现 `Received N actions from server`，且 `N > 0`。 |
| action queue | 后续步骤能持续打印 `Step t: action=...`。 |
| 维度合理 | 每个 action 能和 ALOHA 14 维双臂控制预期对齐，或能解释多出的底盘/其他通道。 |

fake client 不计算任务成功率。它的价值是把问题定位在“部署接口是否通”这一层。

## 失败定位

| 现象 | 优先检查 |
| --- | --- |
| `Connection refused` | server 是否启动、端口是否一致、URL 是否写成真实可访问地址。 |
| 415 或 400 | client 是否使用 `MsgPackHttpClientPolicy`，请求是否为 MessagePack。 |
| 500 | server traceback，通常是 checkpoint、payload 字段、图像 shape 或 `unnorm_key` 问题。 |
| 收到动作但维度不对 | checkpoint action dim、`num_open_loop_steps`、ALOHA 14 维 qpos、是否带底盘通道。 |
| 动作数少于预期 | 模型 action horizon 和 client `num_open_loop_steps` 是否一致，client 会截断但不会补齐。 |

## 边界

fake client 不验证真实机器人控制效果，也不验证：

- ROS topic 是否存在。
- 三路真实相机是否同步。
- joint state 是否和训练数据同坐标系。
- action limit、急停、人工接管是否可用。
- gripper 或底盘控制是否符合硬件协议。
- 真实任务是否成功。

它能证明部署通信链路、序列化方式、模型推理入口和 action shape 基本可用。进入真机部署前，还需要单独设计安全流程。

## 小结

- fake client 是 ALOHA 部署的第一道 sanity check。
- 它发送三路 fake 图像、14 维 fake qpos、任务指令和 `unnorm_key`。
- server 返回顶层 `actions` 后，client 按 `num_open_loop_steps` 放入 action queue。
- fake client 通过说明 server-client 推理链路可用；真机安全还需要单独验证。

## 动手练习

1. 用不同 `TASK_LABEL` 运行 fake client，确认 payload 中 instruction 会随环境变量改变。
2. 把 `VLA_SERVER_URL` 改成错误端口，观察 client 的连接错误。
3. 在 fake client 日志里记录第一次返回的 action shape，并说明它和 ALOHA 控制维度的关系。

## 导航

- 上一节：[Server Request Payload](02-server-request-payload.md)
- 返回上级：[部署](../07-deployment.md)
- 下一节：[真实 Client 边界](04-real-client-boundary.md)
