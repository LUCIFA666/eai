# 请求与 Action 格式

目标：知道 `/act` 请求应该包含哪些字段，怎样检查返回 action，以及 `unnorm_key` 错误在 REST 场景中会怎样表现。

server 启动后，客户端只需要能构造图像数组、语言指令和 HTTP 请求。模型、processor 和 GPU 都在 server 端。

## 最小客户端

OpenVLA 的部署脚本使用 `json_numpy` 处理 NumPy 数组。客户端发请求前先 patch JSON 编码：

```python
import json_numpy
import numpy as np
import requests

json_numpy.patch()

payload = {
    "image": np.zeros((256, 256, 3), dtype=np.uint8),
    "instruction": "pick up the black bowl and place it on the plate",
    "unnorm_key": "libero_spatial_no_noops",
}

action = requests.post("http://0.0.0.0:8000/act", json=payload).json()
```

这个请求只验证单步 action 预测。真实机器人客户端还要负责相机取图、时间同步、动作下发、急停和现场安全条件。

## Payload 字段

| 字段 | 类型 | 检查点 |
| --- | --- | --- |
| `image` | `np.ndarray` | 通常是 `uint8` RGB 图像，server 会转成 `PIL.Image` 并调用 processor。 |
| `instruction` | `str` | server 会套用 OpenVLA prompt，再交给 processor。 |
| `unnorm_key` | `str`，可选 | 选择 `norm_stats` 中用于动作反归一化的 key。 |

如果 fine-tuned checkpoint 只包含一个统计量 key，`unnorm_key` 可以省略；实际部署时仍建议显式传入。这样日志和客户端配置能直接看出当前使用的是哪套动作尺度。

## 返回值怎样检查

正常响应会返回一条 action。对 LIBERO / Bridge 这类 OpenVLA 常见路径，重点检查三件事：

| 检查项 | 说明 |
| --- | --- |
| shape | 是否是预期动作维度，常见为 7 维。 |
| 数值范围 | 是否出现明显异常的大数、`nan` 或全零。 |
| 语义边界 | 返回 action 只说明单步预测完成；任务成功还要看 rollout。 |

不要只看 HTTP 状态码。`deploy.py` 的异常处理会记录 traceback，然后返回字符串 `"error"`：

```python
except:
    logging.error(traceback.format_exc())
    logging.warning(...)
    return "error"
```

因此客户端需要同时检查响应内容。若 `.json()` 得到的是 `"error"`，应回到 server 日志看具体错误。

## `unnorm_key` 错误

HF `predict_action()` 会用 `unnorm_key` 选择动作统计量：

```python
assert unnorm_key in norm_stats, (
    f"The `unnorm_key` you chose is not in the set of available dataset statistics, "
    f"please choose from: {norm_stats.keys()}"
)
```

一个常见错误是 checkpoint 的统计量 key 是 `libero_spatial_no_noops`，请求却传成了 `libero_spatial`。server 日志会显示可选 key，并且该次 `/act` 返回 `"error"`。这类问题和网络连通无关，起点应放在 checkpoint 的 `dataset_statistics.json` 和请求 payload 上。

## 本页小结

- `/act` payload 的核心字段是 `image`、`instruction` 和可选 `unnorm_key`。
- 返回 action 后先检查 shape 和数值，再进入 rollout 或机器人端验证。
- REST 场景中 HTTP 200 不能单独代表请求成功，响应内容和 server 日志都要看。

## 导航

- 上一节：[REST Server](01-rest-server.md)
- 返回上级：[部署](../07-deployment.md)
- 下一节：[延迟与控制频率](03-latency-and-control-frequency.md)
