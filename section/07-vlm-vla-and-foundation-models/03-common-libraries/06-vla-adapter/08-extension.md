# 扩展边界

目标：说明从 LIBERO 主线走向 CALVIN、ALOHA 或自定义动作/状态前，需要先确认哪些边界。

本单元以 LIBERO Spatial、Pro checkpoint、LoRA 微调、LIBERO eval 和 policy server sanity check 为主线。跑通这条闭环后，读者已经能检查数据、模型、checkpoint、评测和部署请求是否对齐。继续扩展时，重点是先判断改动落在哪一层，再决定是否需要单独准备环境、数据格式或机器人 client。

## 常见扩展方向

| 方向 | 边界 |
| --- | --- |
| CALVIN 或更多 benchmark | 评测环境、任务成功判定、gripper 处理和 action queue 可能与 LIBERO 不同，需要单独核对评测入口和动作后处理。 |
| ALOHA fake client | 可以检查 policy server 请求、图像数量、state/action shape 和返回字段，不能替代真实任务成功率评测。 |
| ALOHA 真机 | 需要 ROS topic、真实相机、joint state、动作发布、限位、急停和人工接管流程，适合独立设计安全检查。 |
| 自定义 action / proprio | 需要同步核对 RLDS 字段、statistics、常量、action head、proprio projector、eval action 格式和部署 payload。 |

扩展时可以沿着“数据能读 -> batch shape 正确 -> 短程训练能保存 checkpoint -> 少量 rollout 能加载 -> server 能响应请求”的顺序检查。每次只改一层，日志和中间产物会更容易对应到具体问题。

## 导航

- 上一节：[真实 Client 边界](07-deployment/04-real-client-boundary.md)
- 返回上级：[VLA-Adapter](../06-vla-adapter.md)
