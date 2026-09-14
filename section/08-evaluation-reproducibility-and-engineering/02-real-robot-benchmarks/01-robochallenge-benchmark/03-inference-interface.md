# 推理接口与运行循环

RoboChallengeInference 把参评策略接到 RoboChallenge 的在线机器人服务上。策略代码不运行在评测侧机器上，而是在参评方环境中加载模型、轮询 job 状态、获取机器人观测、执行本地推理，并把动作片段提交给真实机器人。观测字段、动作 shape 和队列状态共同决定一次 rollout 实际执行了什么。

## 客户端结构

RoboChallengeInference 的核心入口由三类对象组成。`InterfaceClient` 负责 HTTP 请求、时钟同步、机器人状态获取、动作提交和 job 状态查询。策略包装层负责把 `state.pkl` 解包后的字典送入模型，并返回符合动作接口的二维数组。`job_loop` 负责轮询评测任务集合，把 ready 状态的 job 交给单个 job 处理函数。

`demo.py` 中的 `DummyPolicy` 和 `GPUClient` 只是策略接入点。真正的模型加载发生在 policy 初始化阶段，真正的推理发生在 `GPUClient.infer(state)`。这层包装让评测循环不关心模型来自 OpenVLA、π 系列、CogACT 还是自定义策略；接口只关心输入 state 字典和输出 action list 是否满足机器人约束。

`InterfaceClient` 把 online job 系统和 direct robot 接口收束在同一个客户端对象中：

| 方法 | 接口职责 | 对运行循环的影响 |
|---|---|---|
| `update_job_info` | 根据 `robot_id` 切换 direct robot URL | job 分配到具体机器人后，状态和动作请求才会指向对应工作站 |
| `cal_clockoffset` / `/clock-sync` | 估计本地时间和机器人时间差 | rollout 日志可以把本地推理耗时和机器人侧时间戳对齐 |
| `get_job_status` | 查询 job 当前状态 | `running` 之外的状态会让单个 job 循环退出 |
| `wait_for_robot_running` | 等待机器人服务进入可运行状态 | start 请求之后，客户端不会在机器人未运行时直接提交动作 |
| `get_state` | 获取 `/state.pkl` | 返回图像 bytes、本体状态、时间戳和动作队列长度 |
| `post_actions` | 提交 `/action` | 把模型输出的动作片段压入 FIFO 队列 |

## job scheduling

一次评测从 Web 侧提交 request 开始，评测系统生成 run id 或 job collection id。客户端使用这个 id 轮询 job collection。job 状态处于 `assigned`、`prepare`、`ready`、`running` 时属于活跃任务；`finished`、`cancelled`、`failed` 代表任务已经结束或不可继续执行。

当某个 job 进入 `ready` 状态，客户端读取对应 `robot_id`，更新 direct robot URL，并通过 `/clock-sync` 估计本地时间和机器人时间的 offset。随后客户端向 job 系统发送 start 请求。job 进入 `running` 后，客户端持续执行状态获取、策略推理和动作提交循环，直到 job 状态离开 `running` 或本地循环达到最大等待时间。

## `state.pkl`

机器人状态由 direct robot 接口的 `/state.pkl` 返回。请求参数包括图像尺寸、相机位置和动作类型：`width`、`height` 控制返回图像分辨率，`image_type` 选择 `high`、`left_hand`、`right_hand` 等相机视角，`action_type` 指定关节控制或末端位姿控制，以及单臂 / 双臂选择。

响应体是 pickle 序列化后的字典，主要字段包括 `state`、`timestamp`、`pending_actions`、`action` 和 `images`。`state == normal` 表示机器人状态可用；`fault` 或 `abnormal` 表示机器人侧存在异常；`size_none` 表示请求参数或图像尺寸尚未正确建立。`timestamp` 是机器人侧时间，`pending_actions` 是动作队列中尚未执行完成的动作数量，`images` 保存所请求视角的 PNG bytes。

状态响应是带有运行状态和队列信息的控制回路输入，不只是普通观测张量。策略前处理会把图像 bytes 解码成模型输入，把 `action` 字段或本体状态映射到 proprioception，把 `pending_actions` 用作是否继续推理的运行条件。

```python
{
    "state": "normal",
    "timestamp": 0.0,
    "pending_actions": 0,
    "action": [0.0, 0.0, ...],
    "images": {
        "high": b"PNG",
        "left_hand": b"PNG",
        "right_hand": b"PNG"
    }
}
```

## 动作提交

动作通过 direct robot 接口的 `/action` 提交。请求参数中的 `action_type` 和 `/state.pkl` 使用的控制模式保持一致。请求体包含 `actions` 和 `duration`：`actions` 是二维浮点数组，第一维是动作步数，第二维是每步动作的目标值；`duration` 是每个动作持续时间。

接口返回 `result` 和 `message`。`result == success` 表示动作片段进入机器人侧处理流程；`error` 的 message 可能来自机器人未运行、动作 shape 不匹配、动作队列已满或其它接口异常。动作进入队列后按 FIFO 顺序执行，因此客户端不能把已提交动作当作可撤销计划。

下面的请求体以单臂 `joint` 动作为例。双臂或末端位姿控制会改变每步动作的长度。

```json
{
  "actions": [
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  ],
  "duration": 0.05
}
```

## `action_type` 与机器人差异

`action_type` 同时影响状态返回和动作提交。`joint` 表示关节控制，`pos` 表示末端位姿控制；`leftjoint`、`leftpos`、`rightjoint`、`rightpos` 只控制指定单臂。单臂机器人在接口中仍使用 `leftjoint` 或 `leftpos` 这类名称，双臂机器人在不指定左右时返回或接收双臂拼接后的动作。

| 平台 | 关节动作 shape | 位姿动作 shape | 相机视角 |
|---|---|---|---|
| ALOHA | 单臂 7，双臂 14 | 单臂 8，双臂 16 | 左腕、右腕、俯视 |
| ARX5 | 7 | 7 | 腕部、对侧、侧视 |
| UR5 | 7 | 8 | 腕部、对侧 |
| Franka | 8 | 8 | 腕部、对侧、侧视 |

这个表只描述接口层 shape，数据集 JSONL 中还包含更多状态字段。训练数据中的状态键、推理接口的 `action` 字段和提交给 `/action` 的动作数组共同决定策略适配层的输入输出映射。

## 运行循环

单个 running job 的循环包含四个条件。第一，job 状态仍为 `running`。第二，`get_state` 能返回有效字典。第三，`state` 字段为 `normal`。第四，`pending_actions == 0`。这些条件满足后，客户端记录观测时间差，把 state 交给 `gpu_client.infer(state)`，再把模型输出提交给 `/action`。

这个默认循环偏保守：它等待动作队列清空再进行下一次推理。这样做能减少观测和动作执行之间的重叠，便于把图像、动作和评分结果对应到更稳定的 rollout 片段。更复杂的策略可以围绕时间戳和队列长度安排闭环频率，但动作 shape、duration 和机器人状态检查仍然约束接口调用。

```python
while True:
    device, status = client.get_job_status(job_id)
    if status != "running":
        break

    state = client.get_state(image_size, image_type, action_type)
    if not state:
        continue

    if state["state"] != "normal" or state["pending_actions"] != 0:
        continue

    actions = gpu_client.infer(state)
    client.post_actions(actions, duration, action_type)
```

## mock 测试

RoboChallengeInference 提供 mock robot server，用于在真实评测前检查客户端和策略包装层。mock 设置通过 `ROBOT_TAG` 和 `RECORD_DATA_DIR` 选择机器人类型和本地数据目录。测试服务会模拟 direct robot 接口，使 `test.py` 能执行完整的 job loop、状态获取、推理调用和动作提交路径。

mock 测试验证的是接口契约，不是策略在真实任务中的完成表现。它能发现相机名不匹配、动作 shape 错误、policy 返回空值、状态解码失败、job loop 无法退出等问题；它不能证明策略在真实物体、真实复位和真实机器人延迟下会得到同样表现。

## 接口口径

RoboChallenge 的推理接口把模型输出和系统工程耦合在一起。相同模型在不同 `image_type`、分辨率、`action_type`、duration 和等待策略下，可能生成不同 rollout。评测结果中的分数因此不能脱离接口配置解释；至少应保留 run id、机器人平台、相机集合、动作类型、动作频率或 duration、客户端版本和异常日志。

## 小结

RoboChallengeInference 的在线循环由 job 状态、`state.pkl`、本地策略推理和 `/action` 共同构成。`state.pkl` 不只是图像观测，还包含机器人状态、时间戳、当前动作和 `pending_actions`；`/action` 接收的动作数组又受 `action_type`、机器人平台和 duration 约束。队列长度和 job 状态因此直接决定策略何时推理、何时等待、何时退出。

接口配置本身会进入结果解释。相机集合、图像尺寸、动作类型、动作 shape、动作持续时间和等待策略都会改变真实 rollout 的轨迹；mock server 可以验证接口契约，但不能替代真实物体、复位误差和机器人延迟下的在线评测。

## 导航

- 返回上级：[RoboChallenge](../01-robochallenge-benchmark.md)
- 上一页：[Table30 任务与数据](02-table30-task-data.md)
- 下一页：[评分与复现口径](04-scoring-reproducibility.md)
