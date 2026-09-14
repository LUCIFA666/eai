# 部署

目标：理解 OpenVLA 的 REST policy server 怎样接收图像和指令、返回单步 action，以及 server 连通能验证到哪一步。

前面几节里的推理和评测都在同一个 Python 进程中完成：脚本加载模型，拿到图像和指令，直接调用 `predict_action()`。`vla-scripts/deploy.py` 换了一种组织方式，把模型常驻在 GPU server 上，客户端通过 HTTP 请求拿 action。

这种方式适合把 GPU 推理端和机器人控制端分开。它能检查请求格式、模型加载、`unnorm_key`、动作返回和单步延迟；策略是否能完成任务，还要回到 LIBERO rollout、Bridge 真机评测或机器人端记录。

## REST Server、请求格式和延迟记录

| 页面 | 重点 |
| --- | --- |
| [REST Server](07-deployment/01-rest-server.md) | `deploy.py` 怎样加载模型、读取本地统计量，并把 `predict_action` 包装成 `/act`。 |
| [请求与 Action 格式](07-deployment/02-request-and-action-format.md) | 客户端 payload、`json_numpy`、`unnorm_key`、返回 action 和错误响应。 |
| [延迟与控制频率](07-deployment/03-latency-and-control-frequency.md) | 怎么测单步请求延迟，mean / median / p95 怎样影响控制频率判断。 |

## 部署验证能说明什么

REST server 跑通后，可以确认下面几件事：

| 现象 | 说明 |
| --- | --- |
| server 启动并监听端口 | 模型、processor、FastAPI 和运行环境能加载。 |
| `/act` 返回 7D action | 请求格式、图像编码、prompt、`predict_action` 和 JSON 返回链路正常。 |
| 错误请求在日志中出现 traceback | server 能接收请求，但 payload 或 `unnorm_key` 还没有对齐。 |
| 顺序请求延迟稳定 | 这台机器上的单步推理和 HTTP 开销可以被记录下来。 |

这些检查仍然是单步 policy server 检查。真实闭环还要看客户端怎样取图、怎样发送控制命令、控制周期是否稳定，以及环境是否能根据动作进入下一帧。

## 本页小结

- `deploy.py` 提供 OpenVLA 原生 REST policy server，核心端点是 `/act`。
- server 端负责加载模型和执行 `predict_action`，客户端负责发送图像、指令和可选 `unnorm_key`。
- server 连通和 action shape 正常只能说明请求响应链路可用，任务表现还要看 rollout 或真机记录。

## 导航

- 上一节：[评测](06-evaluation.md)
- 返回上级：[OpenVLA](../04-openvla.md)
- 下一节：[REST Server](07-deployment/01-rest-server.md)
