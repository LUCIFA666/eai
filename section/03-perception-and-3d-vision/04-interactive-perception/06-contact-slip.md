# 接触事件与滑移检测

> 难度：[中级] | 预计用时：55 分钟
> 先修：[触觉、力觉与接触观测](05-tactile-force-sensing.md)

目标：理解怎样把连续接触观测转换成 `contact_onset`、`stable_grasp`、`slip_detected`、`collision` 这类离散事件，并用它们驱动抓取监督、失败分析和安全逻辑。

## 先建立主问题

前一页回答的是“有哪些接触观测可用”；这一页回答的是另一件事：

**怎样把这些连续信号翻译成系统真正能消费的阶段事件和失败判断。**

在机器人里，很多上层模块并不直接消费整条原始波形，它们更需要的是：

- 是否已经接触；
- 是否形成稳定夹持；
- 是否出现滑移；
- 是否发生空抓、过抓或环境碰撞。

这就是接触事件检测的职责边界。

## 本页目标

本页聚焦四件事：

- 画清抓取或接触任务中的阶段时间顺序。
- 理解接触 onset、稳定夹持、滑移、过抓和碰撞的最小判据。
- 学会把多种信号组合成事件，而不是只盯单一阈值。
- 写出一份可供 supervisor、controller 或 evaluator 消费的 `contact_event`。

## 先看接触事件的时间顺序

机器人夹爪抓取一个物体时，典型时间顺序可以整理为：

```text
gripper closing
   |
   +--> no_contact
   |
   +--> contact_onset
   |       force rises / current rises / tactile patch appears
   |
   +--> stable_grasp
   |       signals plateau in a reasonable band
   |
   +--> lift / transport
   |       if object drops or tangential evidence grows -> slip_detected
   |
   +--> success or failure
```

关键点只有一个：  
**滑移不是静态类别，而是接触之后的动态事件。**  
它通常发生在 `lift` 或 `transport` 阶段，而不是在“刚碰到”那一瞬间就能完全判断。

## 哪些信号最常被拿来做事件判断

这一页不再重讲传感器定义，只强调“哪些信号更常被用来触发哪些事件”：

| 事件 | 常用证据 |
|---|---|
| `contact_onset` | 法向力突增、夹爪电流上升、触觉 patch 出现 |
| `stable_grasp` | 法向力进入稳定区间，夹爪开口和任务阶段一致 |
| `slip_detected` | 切向力变化、触觉质心漂移、物体高度下沉 |
| `over_grip` | 法向力持续超阈值、受力上升过快 |
| `collision` | 腕部 F/T 或关节力矩出现异常尖峰 |

高质量系统通常不会依赖单一信号，而是组合多种证据。

## 运行 demo 感受接触事件时间线

运行以下命令模拟一次完整的抓取时间线：

```bash
python labs/04-perception/contact_event_demo.py
```

输出摘要（前 15 行）：

```text
  t_ms    phase              event_type        force_N    width_m   failure
---------------------------------------------------------------------------
    0    no_contact         no_contact          0.00    0.1000
   10    no_contact         no_contact          0.00    0.0950
   ...
   60    contact_onset      contact_onset       0.30    0.0650
   70    contact_onset      contact_onset       0.60    0.0600
   80    stable_grasp       stable_grasp        0.90    0.0550
   ...
  760    lift               slip_detected       0.60    0.0250   slip_after_lift
```

事件统计：

```text
  no_contact: 6
  contact_onset: 6
  stable_grasp: 31
  slip_detected: 1
  lift: 6
```

从这段日志至少能读出三件事：

- `0–50 ms` 仍在 `no_contact`，说明闭手动作尚未形成接触。
- `60–80 ms` 出现 `contact_onset`，说明接触开始建立。
- `760 ms` 才出现 `slip_detected`，说明问题不是“没夹到”，而是“夹到了但抬起后守不住”。

## 一个最小的事件检测逻辑

```python
# 基于夹爪电流、法向力和物体高度变化的简化事件判断
def detect_grasp_event(normal_force, finger_current, obj_height_delta):
    if normal_force < 1.0 and finger_current < 0.2:
        return "no_contact"
    if normal_force >= 1.0 and abs(obj_height_delta) < 0.002:
        return "contact_onset"
    if normal_force >= 1.0 and obj_height_delta < -0.01:
        return "slip_detected"
    if normal_force > 8.0:
        return "over_grip"
    return "stable_grasp"

# 预期输出:
# 'contact_onset' / 'slip_detected' / 'over_grip' ...
```

这段代码非常粗，但它表达了一个关键原则：  
接触事件必须和动作阶段、对象运动结果一起解释，不能只盯一个传感器阈值。

## 为什么事件检测不能只盯单一阈值

单一阈值最容易在三类场景里失效：

| 场景 | 只盯单一阈值会怎样 |
|---|---|
| 轻触桌沿或遮挡物 | 会把环境碰撞误判成目标接触 |
| 软物体抓取 | 法向力上升不代表已经稳定夹持 |
| 物体被夹住后缓慢下沉 | 接触成立，但真正的问题是后续滑移 |

因此更稳妥的做法通常是：

- 用任务阶段约束候选事件；
- 用至少两种信号交叉确认；
- 把原始观测和事件结论同时保留。

## 视觉为什么无法替代接触证据

| 场景 | 图像看起来 | 真正发生了什么 |
|---|---|---|
| 空抓 | 手爪位置接近目标 | 手指之间其实什么都没夹到 |
| 轻触即滑 | 目标已被碰到 | 法向力不足，抬起时掉了 |
| 过抓 | 视觉仍正常 | 物体被挤压变形或超载 |
| 侧撞 | 相机没看清遮挡面 | 腕部力突然上升，应立即停机 |

所以“视觉成功但执行失败”的 case，经常要靠接触日志来解释。

## 触觉事件记录应该至少记什么

```yaml
contact_event:
  event_type: slip_detected
  timestamp: 2026-05-26T11:12:03.442Z
  frame_id: gripper_tcp
  signals:
    normal_force_n: 2.8
    tangential_force_n: 1.4
    finger_current_a: 0.36
    object_height_delta_m: -0.013
  context:
    object_id: mug_01
    grasp_phase: lift
  confidence: 0.79
  failure_code: slip_after_lift
```

只要把事件和任务阶段关联起来，很多“为什么明明看见了还是失败”的问题就有了证据。

## 四种常见异常

| 异常 | 信号模式 | 推荐动作 |
|---|---|---|
| 空抓 | 夹爪闭合但法向力不上升 | 重新对准或重观察 |
| 过抓 | 法向力持续升高并超阈值 | 立即停止继续闭合 |
| 滑移 | 法向力存在但切向变化大，物体位姿下落 | 增加夹持力或重抓 |
| 环境碰撞 | 腕部 F/T 突然尖峰 | 紧急减速或停机 |

## 事件结果如何进入策略或 supervisor

| 下游 | 需要什么形式 |
|---|---|
| 规则式 supervisor | 离散事件，如 `slip_detected` |
| 低层控制器 | 高频连续力信号 + 必要事件标志 |
| 策略模型 | 归一化的短时间窗口序列或事件片段 |
| 评测系统 | 时间戳对齐后的事件日志与视频索引 |

这说明系统最好同时保留“原始信号”和“离散解释”。  
只有离散事件，不利于复盘；只有原始波形，下游又不一定会直接消费。

## 自检问题

1. 为什么滑移检测不能只依赖一帧视觉结果？
2. 如果法向力很高但物体仍在下落，最可能说明什么？
3. 在没有高端触觉阵列时，为什么 joint torque 或 motor current 仍然有教学价值？

## 练习

### [观察] 设计一次抓取的事件时间线

1. 选择“闭手抓杯子并抬起”这个动作。
2. 画出时间线：闭手、接触、稳定夹持、抬起、滑移或成功。
3. 在每个阶段标出期望看到的信号变化。

完成后，可以先用下面几条检查这一部分是否已经到位：
- 能指出至少两个能证明“已接触”的信号。
- 能说明“滑移”和“空抓”在日志上如何区分。

### [复现] 输出最小 `contact_event` schema

1. 为抓取任务写一份 `contact_event` 或 `grasp_status` schema。
2. 至少包含 `timestamp`、`frame_id`、`event_type`、`signals`、`failure_code`。
3. 写出 supervisor 接收到 `slip_detected` 后的动作。

完成后，可以先用下面几条检查这一部分是否已经到位：
- schema 足以支持一次失败复盘。
- 能解释为什么要记录任务阶段，例如 `lift` 或 `close`。

## 导航

- 上一节：[触觉、力觉与接触观测](05-tactile-force-sensing.md)
- 返回本章：[感知与三维视觉](../README.md)
- 下一节：[力控证据链](07-force-control-evidence.md)
