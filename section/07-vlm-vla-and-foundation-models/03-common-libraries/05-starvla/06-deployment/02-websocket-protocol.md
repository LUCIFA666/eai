# websocket 协议

目标：理解 StarVLA client 和 server 之间传什么消息，以及图像为什么通常用 ndarray 传输。

StarVLA 使用 websocket 做双向通信，并用 `msgpack_numpy` 序列化 numpy 数组。这样可以传图像数组和动作数组，而不必把数据转成低效的 JSON 字符串。

## client 建连

`WebsocketClientPolicy` 初始化：

```python
self._uri = f"ws://{host}:{port}"
self._ws, self._server_metadata = self._wait_for_server()
```

`_wait_for_server()` 会循环连接 server，成功后先收一条 metadata：

```python
metadata = msgpack_numpy.unpackb(conn.recv())
return conn, metadata
```

所以 benchmark client 一启动就能知道：

- action chunk 长度。
- 可用 unnorm keys。
- server 当前加载的 checkpoint。

## 请求消息

client 调用：

```python
response = self.client.predict_action(vla_input)
```

其中 `vla_input` 在 LIBERO 中类似：

```python
vla_input = {
    "examples": [example],
    "unnorm_key": self.unnorm_key,
    "do_sample": False,
    "use_ddim": self.use_ddim,
    "num_ddim_steps": self.num_ddim_steps,
}
```

当前 `WebsocketClientPolicy.predict_action()` 直接打包这个 dict：

```python
data = self._packer.pack(query_info)
self._ws.send(data)
```

server 端如果没有显式 `type` 字段，会默认当成 `infer` 请求：

```python
mtype = msg.get("type", "infer")
payload = msg.get("payload", msg)
output_dict = self._policy.predict_action(**payload)
```

所以 flat dict 和带 `{"type": "infer", "payload": ...}` 的格式都可以被路由。

## 响应消息

server 成功时返回：

```python
{
    "status": "ok",
    "ok": True,
    "type": "inference_result",
    "request_id": req_id,
    "data": output_dict,
}
```

对当前 `PolicyServerWrapper`，`output_dict` 是：

```python
{
    "actions": np.ndarray(shape=(B, T, action_dim))
}
```

注意这里 key 是 `actions`。当前 server wrapper 已经完成反归一化，client 收到的是环境动作。

## 图像格式

官方评测文档强调：websocket payload 无法直接序列化 PIL 对象，因此 client 应发送 `np.ndarray`。framework 内部会用工具函数转换：

```python
from deployment.model_server.tools.image_tools import to_pil_preserve
batch_images = [to_pil_preserve(example["image"]) for example in examples]
```

所以 benchmark 侧一般构造：

```python
example = {
    "image": [np.asarray(primary), np.asarray(wrist)],
    "lang": task_description,
}
```

不要把自定义环境对象、PIL 对象或不可序列化类直接塞进 `example`。

## 错误响应

如果 policy 推理报错，server 会返回：

```python
{
    "status": "error",
    "ok": False,
    "type": "inference_result",
    "error": {"message": str(e)}
}
```

如果 `_handler` 外层捕获到异常，可能会把 traceback 字符串发给 client 并关闭连接。client 收到字符串响应时会抛：

```python
raise RuntimeError(f"Error in inference server:\n{response}")
```

## 小结

- client 建连后第一条消息是 server metadata。
- 请求可以是 flat dict，server 默认按 infer 处理。
- 当前 server 成功响应在 `response["data"]["actions"]`。
- 图像应通过 `np.ndarray` 传输，PIL 转换放在服务端或 framework 内部。

## 动手练习

1. 运行 `rg -n "def _route_message|mtype = msg.get|infer|predict_action|ping" deployment/model_server/tools/websocket_policy_server.py`，找到默认 `mtype="infer"` 的逻辑。
2. 在 server 已启动后，用 LIBERO client 或 debug client 打印 metadata。成功输出应包含 `action_chunk_size` 和可用反归一化 key。
3. 构造一个 payload 类型不正确的请求，观察 server 返回的错误响应。成功现象是响应中包含 `status: error` 和 `error.message`。

## 导航

- 上一节：[01 server 启动流程](01-server-startup.md)
- 返回上级：[部署与推理服务](../06-deployment.md)
- 下一节：[03 动作后处理](03-action-postprocess.md)
