# RLDS

目标：理解 RLDS 用 episode/step 表达轨迹的核心语义，能正确区分 `is_first`、`is_last`、`is_terminal` 与训练样本边界。

RLDS 是 **Reinforcement Learning Datasets** 的缩写，通常和 TensorFlow Datasets（TFDS）一起出现。第一次看到它时，很多人会把它当成一种“文件格式”，类似 HDF5、Parquet 或 MP4。这样理解并不准确。RLDS 更重要的是一套**轨迹数据的组织约定**：它规定一批序列决策数据应该怎样按 episode 和 step 表达，哪些字段表示当前观察，哪些字段表示动作、奖励、终止状态，以及一条轨迹从哪里开始、在哪里结束。

在机器人学习里，RLDS 之所以常被提到，是因为大规模跨数据集训练需要一种稳定的数据接口。Open X-Embodiment、Octo、OpenVLA 等生态都大量接触 RLDS 或 RLDS 风格的数据。它适合把很多来源不同的机器人数据接进统一的数据管线，但它不会自动解决机器人本体差异、动作空间差异和任务语义差异。本节重点不是教你从零写 TFDS builder，而是让你看懂 RLDS 里一条机器人轨迹到底怎么表示，以及从 RLDS 转到 LeRobot 或其他格式时最容易错在哪里。

## 阅读目标

本节围绕几个问题展开：

1. RLDS 到底解决什么问题，为什么它不只是一个文件后缀。
2. RLDS 为什么把 episode 和 step 放在数据结构最上层。
3. `observation`、`action`、`reward`、`discount`、`is_first`、`is_last`、`is_terminal` 分别表示什么。
4. 为什么最后一个 step 在模仿学习转换中最容易出错。
5. RLDS 和 HDF5、LeRobot 的差别是什么。
6. 在 Open X、Octo、OpenVLA 这类机器人训练生态里，RLDS 扮演什么角色。
7. 从 RLDS 转 LeRobot 时，应该检查哪些字段和语义。

读完这一页后，看到一个 RLDS 数据集时，应该先判断 episode/step 边界是否清楚，再检查 observation/action 的具体含义，不要只看字段名是否叫 `action`。

## 为什么需要 RLDS

机器人数据本质上是**序列决策数据**。一条轨迹不是一堆互不相关的图片，而是一连串“观察—动作—结果”的时间过程。

例如一个机械臂完成“把杯子放到盘子里”的任务，数据大致是这样：

```text
episode_000
  step_000: 看到杯子和盘子，机械臂在初始位置
  step_001: 机械臂向杯子移动
  step_002: 夹爪接近杯子
  step_003: 夹爪闭合
  ...
  step_120: 杯子已经放到盘子里，任务结束
```

如果只是把所有 frame 拼成一个大表，训练程序就很难知道：

- 哪一帧是一条新轨迹的开始。
- 哪一帧是一条轨迹的结束。
- 最后一帧是否还有可以监督学习的动作。
- 轨迹是自然终止、成功完成、失败终止，还是被最大步数截断。
- 多个数据源混在一起后，哪些 step 属于同一条 episode。

RLDS 的核心价值就在这里：它把数据组织成 episode，每个 episode 里再包含 step。这样训练栈在 shuffle、batch、filter、streaming 时，仍然能保留轨迹边界。

```text
RLDS dataset
  episode_000
    episode metadata
    steps
      step_000
      step_001
      step_002
      ...
  episode_001
    episode metadata
    steps
      step_000
      step_001
      ...
```

这和普通图片分类数据完全不同。图片分类数据里，一张图片和另一张图片通常没有时间依赖；RLDS 面对的是序列，丢掉边界就会改变数据含义。

## 一个 RLDS episode 里有什么

一个 RLDS 数据集可以看成很多 episode 的集合。每个 episode 通常有两类信息：

```text
episode
  metadata
  steps
```

episode metadata 可以记录整条轨迹级别的信息，例如：

- episode id。
- 数据来源。
- 任务名称或语言指令。
- 机器人类型。
- 场景信息。
- 成功/失败标签。
- 数据采集者或采集方式。

steps 则是一串时间步。每个 step 通常包含：

```text
step
  observation
  action
  reward
  discount
  is_first
  is_last
  is_terminal
  custom fields
```

不同数据集的字段会扩展，但这几个字段构成了 RLDS 最常见的骨架。还要注意一个工程约束：同一个 RLDS 数据集里的 step schema 通常应该一致。也就是说，最后一步即使没有有效 action，也可能仍保留一个 action 字段，只是语义上不能把它当作可监督动作。

下面是一个简化后的结构图：

```text
episode_000
  metadata:
    task: "put the cup on the plate"
    robot_type: "robot_arm"
    dataset_source: "example_dataset"

  steps:
    step_000:
      observation: image + robot_state + language
      action: move toward cup
      reward: 0
      discount: 1
      is_first: true
      is_last: false
      is_terminal: false

    step_001:
      observation: image + robot_state + language
      action: close gripper
      reward: 0
      discount: 1
      is_first: false
      is_last: false
      is_terminal: false

    step_120:
      observation: final image + final state
      action: invalid or empty
      reward: invalid or empty
      discount: invalid or empty
      is_first: false
      is_last: true
      is_terminal: true
```

注意这里的最后一步。RLDS 的最后 step 用来保存最终 observation；当 `is_last = true` 时，`action`、`reward`、`discount` 这类发生在 observation 之后的字段通常应视为无效或空值。这个细节在转换成模仿学习数据时非常关键。

## step 字段逐个看

### observation：模型看到的东西

`observation` 是当前 step 的输入。机器人数据里的 observation 往往不是单个数组，而是一个嵌套结构，可能包含：

```text
observation
  image_primary
  image_wrist
  image_left
  image_right
  robot_state
  proprio
  depth
  language_instruction
```

其中图像是外部视觉，`robot_state` 或 `proprio` 是机器人自身状态，例如关节角、末端位姿、夹爪状态。语言指令有时放在 episode metadata，有时放在每个 step 的 observation 里。不同数据集的命名并不统一，所以不能只靠字段名猜语义。

在机器人数据转换中，`observation` 最常见的错误有三类：

1. 多相机 key 被改名后视角含义丢失，例如 wrist camera 被误写成 front camera。
2. state 只保留 shape，没有保留每一维的名字。
3. 语言指令在 episode 级和 step 级之间转换时被重复、丢失或错位。

### action：当前 step 执行的动作

`action` 表示在当前 observation 下执行的动作。对行为克隆来说，最常见的训练样本就是：

```text
observation_t -> action_t
```

但不同机器人里的 action 可能完全不是同一种东西：

```text
Robot A action: [x, y, z, roll, pitch, yaw, gripper]
Robot B action: [joint1, joint2, joint3, joint4, joint5, joint6, joint7]
Robot C action: [base_v, base_w, arm_delta, gripper]
```

它们都可以叫 `action`，shape 甚至都可能是 7，但含义不同。RLDS 能统一“这里有一个 action 字段”，但不能自动统一动作语义。跨机器人训练时，必须额外记录 action space、单位、控制频率、机器人本体和夹爪语义。

### reward：一步之后得到的反馈

`reward` 来自强化学习语境，表示执行 action 后得到的即时反馈。在机器人模仿学习数据里，reward 不一定重要，有些数据集可能没有真实 reward，或者只在最后一步给成功信号。

初学者需要分清：

- 强化学习会关心 reward 的数值和累计回报。
- 行为克隆通常主要关心 observation/action 对。
- 有些 VLA 训练会更多使用语言指令和动作，不直接用 reward。

因此从 RLDS 转 LeRobot 时，reward 可以进入 metadata 或保留下来，但不一定进入策略训练输入。

### discount：未来回报折扣

`discount` 也是强化学习里的字段，用于计算未来奖励的折扣。比如某些环境中，未终止 step 的 discount 接近 1，终止 step 的 discount 可能是 0。

在纯模仿学习中，discount 常被忽略；但如果数据未来还要用于 offline RL、价值函数学习或带奖励的评估，discount 就不能随便丢。转换时至少要记录：

```text
这个数据集是否有 discount
如果没有，是不是默认 1
终止和截断时 discount 如何处理
```

### is_first：这是不是 episode 的第一步

`is_first` 标记当前 step 是否是一条 episode 的开始。

正确情况下，一条 episode 通常只有第一个 step 的 `is_first = true`：

```text
step_000: is_first = true
step_001: is_first = false
step_002: is_first = false
...
```

它的价值不是“用 index 也能看出来吗”，而是在数据经过 shuffle、filter、batch、streaming 后，训练管线仍然能知道边界。只靠 step 下标很脆弱，因为转换、截断、过滤都可能改变下标。

### is_last：这是不是 episode 的最后一步

`is_last` 标记当前 step 是否是一条 episode 的结束。它告诉训练系统：这条轨迹到这里不应该再和下一条 episode 连起来。

最容易误解的是：

```text
is_last = true 不等于这一帧一定有有效 action
```

很多 RLDS 数据里，最后一个 step 代表最终 observation。它是“动作执行后看到的结果”，不是“还要继续执行一个动作的状态”。即使数据结构里仍然有 `action` 字段，也应先检查它是否有效；如果直接把最后一步也当作 `observation -> action` 样本，可能会引入无效动作或错位动作。

### is_terminal：环境是否真正终止

`is_terminal` 和 `is_last` 关系很近，但不是同一个概念。

`is_last` 表示：

```text
这条记录到这里结束。
```

`is_terminal` 表示：

```text
环境进入了终止状态。
```

当 `is_terminal = true` 时，当前 observation 通常已经对应最终状态，因此 action、reward 和 discount 也不应该再被当作普通 transition 字段解释。换句话说，`is_terminal` 更强调环境语义，`is_last` 更强调数据记录边界。

举两个例子：

```text
任务成功完成：
  is_last = true
  is_terminal = true

最大步数到了，被截断：
  is_last = true
  is_terminal = false
```

第二种情况常叫 timeout 或 truncation。对于强化学习来说，这两种情况的价值估计不同；对于模仿学习来说，它们也会影响你如何解释失败轨迹、终止状态和最后动作。

## 为什么最后一帧最容易出错

从 HDF5 或 LeRobot 看 RLDS 时，很多人会默认每一行都有 observation 和 action，可以一一配对。但 RLDS 的最后一个 step 常常代表最终状态，即使 action 字段存在，也不一定有可监督语义。这个问题在转换成行为克隆数据时尤其重要。

先看一个正常的行为克隆配对：

```text
step_000 observation -> step_000 action
step_001 observation -> step_001 action
step_002 observation -> step_002 action
```

再看末尾：

```text
step_119 observation -> step_119 action
step_120 final observation -> no valid action
```

如果转换脚本没有处理最后一帧，可能出现三种静默错误：

1. 把最后一帧保留下来，但 action 是空值或默认 0。
2. 把前一帧 action 错配到最后一帧 observation。
3. 删除最后一帧 observation，导致 episode 长度和原始数据不一致。

这几种错误程序可能都不会报错，但训练含义已经变了。安全做法是在转换时显式检查：

```text
如果 is_last = true：
  检查 action 是否真的有效，而不是 schema 占位或默认值
  如果 action 无效，就不要把这一帧作为 BC 监督样本
  但可以保留 final observation 作为 episode 终止信息
```

## RLDS 和 TFDS 的关系

RLDS 通常和 TensorFlow Datasets 一起出现。可以把两者的关系粗略理解为：

```text
RLDS: 规定 episode/step 这类序列数据应该怎么表达
TFDS: 提供数据集构建、下载、分片、读取和 tf.data pipeline
```

在实际生态中，很多 RLDS 数据会通过 TFDS builder 暴露出来。用户可以用类似 `tfds.load(...)` 的方式读取，然后得到一个 episode 数据流。每个 episode 里包含一个 steps 数据集，steps 里再是 observation、action、reward、discount、flag 等字段。

这也是 RLDS 对大规模机器人数据有吸引力的原因：它不只是一个本地文件组织方式，还能接入 TensorFlow 的数据管线，方便做 shuffle、batch、prefetch、filter 和 map。Open X-Embodiment 这类多数据源工程，也正是依赖这种 episode/step 语义，把很多机器人数据源接到统一训练接口下。

不过，这里也要注意边界。TFDS 可以帮你高效读取数据，RLDS 可以帮你保留 episode/step 结构，但它们都不会自动解决下面这些问题：

- 不同机器人 action space 是否可比。
- 不同数据集相机视角是否一致。
- 不同数据集控制频率是否一致。
- 语言指令是否具有相同粒度。
- success、terminal、timeout 的定义是否一致。

这些仍然要靠数据转换层和 dataset card 写清楚。

## RLDS 在机器人生态里的位置

RLDS 最早面向强化学习和序列决策数据，但在机器人学习里，它的作用已经不局限于传统 RL。它经常出现在以下场景：

```text
Open X-Embodiment
  多个机器人数据集统一成 episode/step 形式

Octo / OpenVLA 等训练栈
  需要从统一数据管线中读取大规模机器人轨迹

已有 HDF5 / 自定义格式数据
  转成 RLDS 以便接入 TFDS 或跨数据集混合训练

RLDS -> LeRobot
  为了使用 LeRobot 的可视化、编辑、训练或数据托管工具
```

RLDS 的意义主要有两点。

第一，它让你明白大规模机器人数据不是“一个目录里放很多视频”，而是一批 episode，每条 episode 里有明确的 step、flag 和 metadata。

第二，它提醒你，统一格式只是第一步。真正困难的是统一语义，尤其是 action、本体、频率、任务和成功定义。

## RLDS、HDF5 和 LeRobot 的差别

三者经常互相转换，但关注点不同。

| 维度 | HDF5 | LeRobot | RLDS |
|---|---|---|---|
| 核心关注 | 层次化大容器 | 工程化数据目录与训练工具链 | episode/step 语义 |
| 常见形态 | 一个或少量 `.hdf5` 文件 | `meta/ data/ videos/` | TFDS/RLDS 数据集 |
| 轨迹边界 | 常靠 `demo_0`、`demo_1` group | 靠 episode metadata | 靠 episode 和 step flags |
| 图像存储 | 数组、JPEG/PNG bytes 或外部文件 | 通常是 MP4 | 取决于 TFDS feature 设计 |
| 适合场景 | 仿真、旧 benchmark、快速归档 | 可视化、编辑、训练、共享 | 大规模跨数据源训练管线 |
| 主要风险 | 字段语义藏在代码里 | metadata / stats 不一致 | 本体和 action 语义不能自动统一 |

可以这样记：

```text
HDF5 更像“把轨迹装进一个大箱子”。
LeRobot 更像“把机器人数据组织成可训练、可查看、可维护的工程目录”。
RLDS 更像“把序列决策数据统一表达成 episode 和 step”。
```

## 从 RLDS 转 LeRobot 时怎么想

从 RLDS 转 LeRobot，不是把字段复制到另一个目录，而是把 episode/step 语义重新落到 LeRobot 的 frame/episode metadata 上。

一个常见流程是：

```text
read RLDS episode
  -> inspect episode metadata
  -> iterate steps in order
  -> map observation fields
  -> map action fields
  -> handle is_first / is_last / is_terminal
  -> write LeRobot frames
  -> write meta/info.json
  -> write meta/tasks and meta/episodes
  -> recompute stats
  -> sample visualization / replay
```

其中最关键的是四件事。

### 第一，保留 episode 边界

RLDS 中的每个 episode 转成 LeRobot 后，应该仍然是一条 episode。不能为了方便读取，把所有 steps 展平成一个大表后忘记原始边界。

如果你丢掉 episode 边界，后续会影响：

- train/val/test 切分。
- episode 级成功标签。
- 任务文本映射。
- 最后一帧处理。
- replay 和可视化。

### 第二，处理最后一帧

如果 RLDS 的最后 step 没有有效 action，转 LeRobot 时要明确策略：

```text
保留 final observation 但不作为 BC 样本
或删除该 frame，并记录删除原因
或标记 action_valid = false
```

不要让转换脚本默默填 0。填 0 会让模型学到错误动作，尤其在夹爪或末端位姿控制中影响很大。

### 第三，稳定命名 observation

RLDS 里的 observation key 可能来自原数据集命名，例如：

```text
image
image_primary
image_wrist
natural_language_instruction
proprio
state
```

转成 LeRobot 时最好统一成稳定 feature 名：

```text
observation.images.front
observation.images.wrist
observation.state
task
```

但统一命名不代表可以改变语义。比如某个数据集的 `image_primary` 是侧视角，另一个数据集的 `image_primary` 是前视角。它们都映射成 `observation.images.front` 之前，必须人工确认视角含义。

### 第四，写清 action 语义

LeRobot 的 `action` 不能只写 shape。例如：

```json
"action": {
  "dtype": "float32",
  "shape": [7]
}
```

这不够。至少应该在 `info.json` 或 dataset card 中写清：

```text
action 是关节位置、关节速度，还是末端位姿增量
action 的单位是什么
gripper 维度表示开合宽度、二值命令，还是归一化量
控制频率是多少
action 是否经过归一化或裁剪
```

否则转成 LeRobot 后，数据虽然能读，但训练和部署都会变得危险。

## 一个最小检查脚本思路

下面是概念性伪代码，用来说明从 RLDS 转出前可以先检查什么。不同项目的实际 API 会不同，这里关注检查逻辑。

```python
def audit_rlds_episode(steps):
    errors = []

    if len(steps) == 0:
        errors.append("empty episode")
        return errors

    # episode 起点和终点
    if not steps[0].get("is_first", False):
        errors.append("first step is not marked as is_first")
    if not steps[-1].get("is_last", False):
        errors.append("last step is not marked as is_last")

    # 中间不应该反复出现边界标记
    for i, step in enumerate(steps[1:], start=1):
        if step.get("is_first", False):
            errors.append(f"unexpected is_first at step {i}")
    for i, step in enumerate(steps[:-1]):
        if step.get("is_last", False):
            errors.append(f"unexpected is_last before final step: {i}")

    # 检查 action 是否适合 BC 训练
    for i, step in enumerate(steps):
        is_last = step.get("is_last", False)
        has_action = "action" in step and step["action"] is not None
        if is_last:
            # 最后一步即使有 action 字段，也不应默认作为 BC 监督样本
            continue
        if not is_last and not has_action:
            errors.append(f"missing action at non-terminal step {i}")

    return errors
```

真实项目还要检查：

- 多相机帧数是否一致。
- 图像和 action 是否同频。
- language instruction 是否为空。
- reward / discount 是否缺失。
- `is_terminal` 是否和 timeout / success 标签一致。
- action shape 是否在同一子数据集内一致。
- 不同子数据集是否有不同 robot type。

## 一个例子：为什么不能直接混训两个 RLDS 数据集

假设有两个 RLDS 数据集，它们字段都长这样：

```text
observation
  image
  state
action
is_first
is_last
is_terminal
```

看起来完全一致。但进一步检查后发现：

```text
Dataset A:
  robot: Franka
  action: [delta_x, delta_y, delta_z, delta_roll, delta_pitch, delta_yaw, gripper]
  fps: 10

Dataset B:
  robot: UR5
  action: [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6, gripper]
  fps: 20
```

如果直接把它们混在一起训练，模型会面对一个矛盾监督：同样叫 `action[0]`，在 A 里是末端 x 方向增量，在 B 里是第一个关节角。这样训练得到的策略很可能既不能正确输出末端增量，也不能正确输出关节角。

更合理的做法有几种：

```text
方案 1：分机器人本体训练，不直接混 action。
方案 2：把不同机器人 action 映射到统一中间表示，但必须验证可行性。
方案 3：在模型输入中加入 robot type，并让策略头按机器人分开。
方案 4：只使用同本体或相近本体的数据。
```

RLDS 解决的是“数据结构统一”，不是“控制空间统一”。这一点是读 Open X、DROID、BridgeData 等 RLDS 风格数据时最重要的判断。

## 常见误解

- **误解 1：RLDS 是一种和 HDF5 一样的文件后缀。** 不是。RLDS 更重要的是 episode/step 结构和字段语义，实际常通过 TFDS 管线暴露。
- **误解 2：只要两个数据集都是 RLDS，就可以直接混训。** 不一定。action、本体、相机、频率和任务文本都可能不同。
- **误解 3：`is_last` 就等于任务成功。** 不对。`is_last` 只是 episode 结束；成功、失败、timeout 需要额外字段或语义判断。
- **误解 4：最后一帧一定能作为 BC 样本。** 不一定。最后一帧可能只有 final observation，没有有效 action。
- **误解 5：最后一步有 `action` 字段就说明 action 有效。** 不一定。RLDS 为了保持 schema 一致，可能保留字段，但 `is_last = true` 时这些字段不应默认用于监督。
- **误解 6：reward 对模仿学习没用，所以可以直接删。** 要看后续用途。如果数据还要用于 offline RL、评估或过滤，reward 仍然有价值。
- **误解 7：语言指令放在哪里都一样。** 不一样。episode 级语言和 step 级语言在转换时要保持一致，否则可能出现任务文本重复、丢失或错位。

## 小结

RLDS 的核心不是某个具体文件名，而是把序列决策数据组织成 episode 和 step。它让训练系统能稳定知道一条轨迹从哪里开始、在哪里结束，哪些 step 是终止状态，哪些字段是当前观察、动作和奖励。

在机器人学习里，RLDS 的价值主要体现在大规模跨数据源训练。它适合 Open X、Octo、OpenVLA 这类需要统一读取多来源轨迹的生态。但 RLDS 只统一结构，不统一机器人语义。不同数据集之间的 action space、控制频率、相机视角、任务语言和 success 定义，都需要在转换和训练前明确审计。

如果只记一句话，可以记住：

```text
RLDS 解决 episode/step 结构问题，不自动解决机器人本体和 action 语义问题。
```

## 实践任务

找一个 RLDS 或 RLDS 风格机器人数据集，完成下面几步：

1. 列出 episode metadata 中有哪些字段。
2. 随机检查一条 episode，确认第一步是否 `is_first = true`，最后一步是否 `is_last = true`。
3. 查看最后一步是否有有效 action。
4. 列出 observation 中有哪些 key，例如图像、状态、语言。
5. 写清 action 的 shape、单位和语义。
6. 判断这个数据集如果转成 LeRobot，哪些字段进入 `observation.images.*`，哪些进入 `observation.state`，哪些进入 task 或 metadata。

## 自查问题

1. RLDS 为什么要把 episode 和 step 放在最上层，而不是只存一个大表？
2. `is_first`、`is_last`、`is_terminal` 三者分别表示什么？
3. 为什么 `is_last = true` 不等于一定有可监督 action？
4. 为什么两个 RLDS 数据集都叫 `action`，仍然不能直接混训？
5. 从 RLDS 转 LeRobot 时，语言指令、多相机和最后一帧分别容易出什么问题？
6. `is_terminal = false` 但 `is_last = true` 通常说明什么情况？
