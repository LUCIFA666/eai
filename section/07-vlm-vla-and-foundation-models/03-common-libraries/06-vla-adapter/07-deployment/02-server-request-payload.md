# Server Request Payload

目标：理解 MsgPack HTTP `/act` 接口需要什么输入，以及 server 返回的 `actions` 如何进入 client 的 action queue。

ALOHA 部署主线使用 MsgPack HTTP。client 会把 observation 用 MessagePack 编码后 POST 到 `/act`：

```text
POST /act
Content-Type: application/msgpack
```

server 端在 `experiments/robot/server_deploy/deploy.py` 中解包：

```python
body = await request.body()
batch = msgpack.unpackb(body, object_hook=msgpack_numpy.decode, raw=False)
```

请求头不符合 `application/msgpack` 时，server 会返回 415。这样做的好处是图像和 numpy 数组不需要先转成低效的 JSON 字符串。

## 常见字段

| 字段 | 说明 |
| --- | --- |
| `full_image` | front camera 图像，fake client 中来自 `cam_high`。 |
| `left_wrist_image` | left wrist camera 图像。 |
| `right_wrist_image` | right wrist camera 图像。 |
| `state` | 14 维 bimanual qpos。server 的 proprio projector 也按 14 维 ALOHA state 构造。 |
| `instruction` | 自然语言任务描述，例如 `Use the right arm to stack...`。 |
| `unnorm_key` | action un-normalization 使用的 dataset statistics key，需要和训练数据 key 对齐。 |

fake client 的 `prepare_observation_for_server()` 会构造：

```python
observation = {
    "full_image": img_front,
    "left_wrist_image": left_wrist,
    "right_wrist_image": right_wrist,
    "state": obs_data["qpos"],
    "instruction": task_description,
    "unnorm_key": unnorm_key,
}
```

真实 client 构造的字段基本相同，只是图像和 qpos 来自 ROS topic。对部署联调来说，先确认字段名、图像顺序、state 维度，后续再看任务是否成功。

## Server 处理流程

`VLAServer.get_server_action()` 会先从 payload 中取出两个特殊字段：

```python
unnorm_key = batch.pop("unnorm_key")
instruction = batch.pop("instruction")
self.cfg.unnorm_key = unnorm_key
```

剩下的 `batch` 就是 observation，传给 `get_action()`：

```python
actions = get_action(
    self.cfg,
    self.model,
    batch,
    instruction,
    processor=self.processor,
    action_head=self.action_head,
    proprio_projector=self.proprio_projector,
)
```

因此 `instruction` 和 `unnorm_key` 需要放在 payload 顶层。图像和 state 保留在 `batch` 中，让 `get_action()` 和 `get_vla_action()` 继续处理。

## 返回值

server 返回 MessagePack，解包后是普通 dict：

```python
{"actions": np.array(actions).tolist()}
```

client 侧读取：

```python
response = client.infer(observation)
actions = np.array(response["actions"])
actions = actions[: cfg.num_open_loop_steps]
action_queue.extend(actions)
```

这里读取的是顶层 `actions`。如果从 StarVLA 或其他 websocket client 迁移代码，需要确认没有沿用 `response["data"]["actions"]` 或 `normalized_actions` 这类返回格式。

## Action Queue

VLA 模型通常一次返回一段 future actions。ALOHA fake/real client 不会每个控制步都请求 server，而是维护一个队列：

1. `action_queue` 为空时请求 `/act`。
2. 收到 `actions` 后截断到 `num_open_loop_steps`。
3. 每个循环 `popleft()` 取一个动作执行或打印。
4. 队列耗尽后重新请求下一段动作。

fake client 只打印动作；真实 client 会把动作拆成左右臂 joint command 并发布到 ROS topic。

## 常见错误

| 现象 | 优先检查 |
| --- | --- |
| 415 Unsupported Media Type | client 是否设置 `Content-Type: application/msgpack`。 |
| 400 Invalid MessagePack | payload 是否真的用 `msgpack.packb(..., default=msgpack_numpy.encode)` 编码。 |
| 500 Internal Server Error | 先看 server traceback，常见原因是缺字段、图像 shape 不对或 `unnorm_key` 不存在。 |
| `KeyError: actions` | client 是否按其他项目的返回格式读取，例如 `response["data"]["actions"]`。 |
| action shape 不对 | checkpoint action dim、ALOHA 14 维 joint state、`num_open_loop_steps`、`use_relative_actions` 是否一致。 |
| 动作尺度异常 | `unnorm_key`、dataset statistics、absolute/relative action 语义、图像顺序是否匹配训练数据。 |

## 小结

- ALOHA 部署请求是 MsgPack HTTP，payload 顶层需要包含 `instruction` 和 `unnorm_key`。
- 三路图像字段是 `full_image`、`left_wrist_image`、`right_wrist_image`。
- server 返回顶层 `actions`，client 再做 chunk 截断和 action queue。
- payload 能成功解析只说明通信格式正确，动作是否合理还要继续检查 shape、尺度和机器人语义。

## 动手练习

1. 在 `run_fake_cobot_client.py` 中找到 `prepare_observation_for_server()`，确认六个 payload 字段。
2. 在 `robot_utils.py` 中找到 `MsgPackHttpClientPolicy.infer()`，说明请求头和编码方式。
3. 把 `unnorm_key` 改成不存在的值，观察 server 端和 client 端分别报什么错误。

## 导航

- 上一节：[Policy Server](01-policy-server.md)
- 返回上级：[部署](../07-deployment.md)
- 下一节：[ALOHA Fake Client](03-aloha-fake-client.md)
