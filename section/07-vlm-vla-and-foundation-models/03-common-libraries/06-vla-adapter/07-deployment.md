# 部署

目标：理解 VLA-Adapter checkpoint 如何变成可被 client 查询的 policy server，并用 ALOHA fake client 做部署 sanity check。

部署和 LIBERO eval 的边界不同。eval script 在同一进程里创建环境、加载模型并执行 rollout；部署则把模型包装成 server，client 通过 HTTP 请求动作。

policy server 能验证的是 checkpoint 组件加载、`/act` payload、processor、proprio/state 输入、action shape 和 `unnorm_key`。它不等同于 LIBERO benchmark 成功率，也不等同于真实机器人安全流程。fake client 只检查 server-client 通信和动作返回形态，真实 ALOHA / Cobot Magic client 还需要 ROS、相机、joint state、限位、急停和现场监控。

## 学习路径

| 页面 | 重点 |
| --- | --- |
| [Policy Server](07-deployment/01-policy-server.md) | `DeployConfig`、模型加载、`/act` 接口 |
| [Server Request Payload](07-deployment/02-server-request-payload.md) | image、instruction、state/proprio、`unnorm_key` |
| [ALOHA Fake Client](07-deployment/03-aloha-fake-client.md) | 不接 ROS 的 server-client sanity check |
| [真实 Client 边界](07-deployment/04-real-client-boundary.md) | ROS、真实相机、joint state、安全前提 |

## 导航

- 上一节：[Rollout 视频与失败案例](06-evaluation/04-rollout-video-and-failure-cases.md)
- 返回上级：[VLA-Adapter](../06-vla-adapter.md)
- 下一节：[Policy Server](07-deployment/01-policy-server.md)
