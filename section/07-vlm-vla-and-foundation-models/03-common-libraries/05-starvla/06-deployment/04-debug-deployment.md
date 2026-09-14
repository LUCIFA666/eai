# 调试部署

目标：整理 policy server 和 benchmark client 联调时最常见的问题，并给出定位顺序。

部署问题通常出现在四个边界：

```text
checkpoint -> server -> websocket -> benchmark client -> environment
```

排错时先确认边界是否没问题。

## 检查顺序

1. server 是否能单独启动。
2. client 是否能连上 server 并收到 metadata。
3. 一次最小 `examples` 请求是否能返回 `actions`。
4. `actions.shape` 是否等于 `[B, action_chunk_size, action_dim]`。
5. benchmark 是否正确拆分动作维度。
6. gripper 和 delta/absolute 语义是否匹配环境。

## server 启动失败

| 报错 | 可能原因 |
|---|---|
| `FileNotFoundError: Pretrained checkpoint ... does not exist` | `--ckpt_path` 错 |
| `Missing config.yaml` | checkpoint 脱离 run 目录 |
| `Missing dataset_statistics.json` | 训练输出不完整 |
| `Framework ... is not implemented` | `framework.name` 不在 registry |
| `Missing keys in state_dict` | 配置和权重版本不匹配 |
| CUDA OOM | 模型太大、GPU 选错、未用 bf16 |

## client 连不上

client 会循环等待 server：

```python
logging.info(f"Still waiting for server {self._uri} ...")
```

常见原因：

- server 没启动。
- port 不一致。
- client 用了 `0.0.0.0` 作为连接地址。
- 跨机器时防火墙或网络不可达。
- server 启动后因 checkpoint 错误退出。

本机连接应使用：

```bash
--host 127.0.0.1 --port 10093
```

## 推理请求失败

server 错误响应会包含：

```python
"error": {"message": str(e)}
```

常见原因：

| 错误 | 检查 |
|---|---|
| `Payload must be a dict` | client 发送格式 |
| `predict_action: unnorm_key not specified` | 多 statistics key，需要传 `unnorm_key` |
| 图像转换失败 | `example["image"]` 类型不符合 ndarray/list 约定 |
| shape mismatch | `action_dim/state_dim/action_horizon` 不一致 |
| token 相关错误 | FAST 模型词表不匹配 |

## 环境执行异常

如果 server 返回动作，但环境表现异常，重点检查：

- 图像是否按训练时同样旋转、裁剪、resize。
- 多视角顺序是否一致。
- action 维度拆分是否一致。
- gripper 开闭方向是否一致。
- 模型训练的是 delta action 还是 absolute action。
- `unnorm_key` 是否匹配当前机器人。

LIBERO 中有一段图像处理：

```python
img = np.ascontiguousarray(obs["agentview_image"][::-1, ::-1])
wrist_img = np.ascontiguousarray(obs["robot0_eye_in_hand_image"][::-1, ::-1])
```

这类旋转/翻转如果和训练数据不一致，会严重影响评测结果。

## 最小请求测试

可以写一个最小 client 请求，用随机图像验证 server 返回格式：

```python
import numpy as np
from deployment.model_server.tools.websocket_policy_client import WebsocketClientPolicy

client = WebsocketClientPolicy("127.0.0.1", 10093)
print(client.get_server_metadata())

example = {
    "image": [np.zeros((224, 224, 3), dtype=np.uint8)],
    "lang": "test instruction",
}
resp = client.predict_action({"examples": [example]})
print(resp.keys(), resp["data"].keys(), resp["data"]["actions"].shape)
```

如果这个测试失败，先修 server/client 通信；如果它成功而 benchmark 失败，再看环境适配。

## 小结

- 部署排错先查 server，再查 websocket，再查 benchmark adapter。
- 当前返回动作 key 是 `response["data"]["actions"]`。
- `unnorm_key`、图像顺序、gripper 语义是最常见的评测错位来源。
- 最小随机图像请求能快速区分通信问题和环境问题。

## 动手练习

1. 在 server 已启动后，用最小 websocket 请求或 `deployment/model_server/tools/debug_server_policy.py` 打印 server metadata 和动作 shape。成功输出应包含 `action_chunk_size`；有效请求还应返回 `actions`。
2. 如果 checkpoint 的 `dataset_statistics.json` 含多个 key，故意传错 `unnorm_key`。成功现象是 server 返回带错误信息的响应，便于定位归一化 key 问题。
3. 在 LIBERO 最小评测中保存 rollout 视频，并确认视频视角与训练数据相机顺序一致。成功输出应在 `video_out_path` 下生成 mp4 文件。

## 导航

- 上一节：[03 动作后处理](03-action-postprocess.md)
- 返回上级：[部署与推理服务](../06-deployment.md)
- 下一节：[LIBERO 端到端实战](../07-libero-end-to-end.md)
