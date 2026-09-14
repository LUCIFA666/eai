# 部署与推理服务

目标：理解 StarVLA 怎样把训练好的 checkpoint 变成 benchmark 可以调用的策略。

训练脚本保存的是模型权重和相关配置。评测时，StarVLA 会启动一个推理服务：服务端负责加载模型并预测动作，LIBERO 等 benchmark 作为客户端发送当前观察并接收动作。

这种分工很实用。模型环境通常依赖 PyTorch、Transformers 和 CUDA；仿真环境可能依赖 MuJoCo、robosuite 或其它包。拆成两个进程后，两边只需要通过轻量通信传递图像、语言和动作。

## 本节目标

本节围绕下面几个问题展开：

1. policy server 启动后加载了哪些文件？
2. client 会给 server 发送哪些字段？
3. `PolicyServerWrapper` 怎样调用 `predict_action()`？
4. 动作反归一化、action chunk 和夹爪后处理分别在哪里做？
5. 联调部署时应该按什么顺序排错？

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [01 server 启动流程](06-deployment/01-server-startup.md) | checkpoint 如何变成 policy | `server_policy.py`、`PolicyServerWrapper` |
| [02 websocket 协议](06-deployment/02-websocket-protocol.md) | client/server 如何传数据 | metadata、`infer` 请求、返回动作 |
| [03 动作后处理](06-deployment/03-action-postprocess.md) | 动作怎样变成环境可执行值 | 反归一化、chunk cache、gripper |
| [04 调试部署](06-deployment/04-debug-deployment.md) | server 和 client 常见错误怎么排 | 端口、路径、shape、环境 |

## 架构图

![StarVLA policy server](assets/starVLA_PolicyServer.png)

图里可以看到三层：

- 控制端：LIBERO、SimplerEnv 或真实机器人控制循环。
- 通信层：client 把观察发给 server，server 把动作发回 client。
- 模型层：checkpoint 被还原成 framework，并调用 `predict_action()`。

注意：图中 `PolicyClinent.py` 是官方图的拼写错误，实际文件名是 `deployment/model_server/tools/websocket_policy_client.py`。图中 `acction` 同样是笔误，应为 `action`。

## 导航

- 上一节：[训练机制](05-training.md)
- 返回上级：[StarVLA](../05-starvla.md)
- 下一节：[01 server 启动流程](06-deployment/01-server-startup.md)
