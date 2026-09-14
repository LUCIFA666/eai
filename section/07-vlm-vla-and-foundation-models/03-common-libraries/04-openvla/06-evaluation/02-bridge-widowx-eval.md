# Bridge WidowX 评测入口

目标：了解 OpenVLA 的 BridgeData V2 WidowX 真机评测入口，以及它和 LIBERO 仿真评测的差别。

BridgeData V2 评测面向真实 WidowX 机械臂。模型侧仍然是图像、语言指令和 7D action，但环境侧从 MuJoCo 仿真换成真实相机、机器人控制器和硬件安全条件。运行这条路径需要 WidowX 硬件、相机、controller 容器、robot server、现场复位和急停条件；没有这些条件时，可以先用这里的流程和源码入口核对参数与接口。

## 三段式启动

官方 README 给出的 BridgeData V2 路线通常分三个终端：

| 终端 | 负责内容 |
| --- | --- |
| WidowX Docker | 启动 `bridge_data_robot` 提供的硬件控制容器。 |
| robot server | 在容器里运行 `widowx_env_service --server`，对外提供相机和机械臂接口。 |
| OpenVLA eval | 运行 `experiments/robot/bridge/run_bridgev2_eval.py`，加载 checkpoint 并循环预测 action。 |

第三段的模型评测命令形状如下：

```bash
python experiments/robot/bridge/run_bridgev2_eval.py \
  --model_family openvla \
  --pretrained_checkpoint openvla/openvla-7b \
  --host_ip localhost \
  --port 5556
```

真实运行前，还要按 BridgeData V2 controller 仓库准备 Docker、USB 配置、相机和 WidowX 服务。没有硬件时，这条命令主要用于定位 Bridge 评测入口、默认参数和调用链。真机控制效果仍取决于真实设备验证。

## 评测参数

`run_bridgev2_eval.py` 的 `GenerateConfig` 把真机评测的默认设置集中在一起：

| 参数 | 默认值 | 含义 |
| --- | --- | --- |
| `unnorm_key` | `bridge_orig` | OpenVLA action 反归一化使用 BridgeData V2 统计量。 |
| `center_crop` | `False` | Bridge eval 源码断言这里应关闭 center crop。 |
| `host_ip` / `port` | `localhost` / `5556` | robot server 地址。 |
| `control_frequency` | `5` | 控制频率，决定每秒发送多少次 action。 |
| `max_episodes` | `50` | 最多运行多少个 episode。 |
| `max_steps` | `60` | 单个 episode 最多执行多少步。 |
| `save_data` | `False` | 是否保存图像、proprio 和 action 数据。 |

Bridge 路径不自动给出 benchmark 成功率表。脚本会让操作者输入任务描述，按 Enter 开始 episode，结束后保存视频；是否成功、是否需要重做 episode，需要结合现场和保存结果记录。

## 机器人环境入口

源码里通过 `get_widowx_env()` 创建 `WidowXGym`。这一层会连接 `WidowXClient`，把 workspace bounds、相机 topic、起始末端位姿和 blocking 控制传给底层服务。

评测循环每隔 `1 / control_frequency` 秒取一次最新观测，做图像预处理，调用 `get_action()`，再把 action 发给 `env.step()`。如果打开 `save_data`，脚本还会保存预处理图像、proprio 和 action，便于回看。

## 和 LIBERO 的主要差别

| 项目 | LIBERO | Bridge WidowX |
| --- | --- | --- |
| 环境 | 仿真 | 真实机械臂和相机 |
| 初始状态 | benchmark 提供 | 现场复位和人工确认 |
| 成功判断 | 环境返回 `done` | 需要现场或记录判断 |
| `unnorm_key` | suite 名，可能 fallback 到 `_no_noops` | 固定为 `bridge_orig` |
| 图像处理 | LIBERO image + 可选 center crop | Bridge 相机图像 resize，center crop 关闭 |
| 风险 | 仿真耗时和依赖问题 | 碰撞、夹爪、物体、急停和场地安全 |

因此 Bridge 评测更接近真实部署，结果也受模型之外的条件影响。相机、控制器、网络连接、workspace bounds、物体摆放和人工安全流程都会影响结果。

## 本页小结

- Bridge WidowX eval 需要 Docker controller、robot server 和 OpenVLA eval 三段配合。
- 模型侧使用 `bridge_orig` 统计量，`center_crop` 默认关闭。
- 没有 WidowX 硬件时，可以先用这页理解源码入口和真机评测约束。
- 真机结果需要单独记录任务、现场条件、视频、失败原因和安全处理。

## 导航

- 上一节：[LIBERO OpenVLA 评测](01-libero-openvla-eval.md)
- 返回上级：[评测](../06-evaluation.md)
- 下一节：[结果与失败记录](03-results-and-failure-records.md)
