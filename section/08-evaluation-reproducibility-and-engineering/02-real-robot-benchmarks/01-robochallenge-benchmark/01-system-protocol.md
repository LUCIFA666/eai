# 系统与评测协议

RoboChallenge 把真实机器人作为在线服务开放给参评策略。评测侧维护机器人、道具、相机、复位流程和任务排期；策略侧维护模型、推理代码、动作后处理和算力环境。这个分工减少了模型上传、Docker 运行环境和公网回调接口带来的不确定性，也让策略能够直接管理自己的推理延迟、显存占用和动作生成方式。

## remote robot 范式

传统真机评测常见三种提交形态：模型权重提交、完整系统镜像提交、评测侧调用参评方提供的模型 API。RoboChallenge 没有采用这三种方式。模型不离开参评方环境，评测系统也不运行参评方的 glue code。参评客户端主动访问 RoboChallenge 的机器人接口，获取观测并提交动作。

这种 remote robot 范式把接口暴露为机器人低层服务。观测请求返回带时间戳的图像、本体状态和动作队列状态，动作请求把一个动作片段压入机器人动作队列。动作队列按 FIFO 顺序执行，队列长度会回到观测响应中。策略因此可以根据时间戳、当前动作状态和队列长度组织闭环控制，而不是被固定成一次观测对应一次立即执行动作。

一次在线任务的控制流程可以概括为下面的接口顺序：

```text
job assigned/prepare
  -> client polls job collection
  -> job ready
  -> client syncs robot clock and starts robot
  -> repeated: capture request -> local inference -> action queue
  -> job finished/cancelled/failed
```

这个顺序把模型推理和机器人执行分开。job scheduling 决定模型何时加载和运行，capture request 决定策略看到哪一组观测，action queue 决定真实机器人按什么顺序消耗动作片段，视觉复位决定每次 rollout 从什么初始场景开始。

## 异步观测与动作队列

RoboChallenge 的控制流程由 capture request 和 action queue 组成。capture request 产生当前观测，action queue 保存已经提交但尚未执行完成的动作。动作一旦进入队列，就会按提交顺序执行；后续观测只能看到队列状态，不能把已经提交的动作改成另一段轨迹。

capture request 和 action queue 分离后，策略可以使用 action chunking、时间对齐或多模型集成。策略可以等待队列清空后再采集下一帧，也可以在队列仍有动作时继续规划后续动作。接口暴露的是低层控制请求，因此动作 shape、`action_type`、相机选择和机器人平台共同构成推理接口的约束。

## 机器人与传感器

RoboChallenge 初始系统覆盖 UR5、Franka Panda、Cobot Magic ALOHA 和 ARX5。这些平台都围绕桌面操作任务配置，但控制方式、自由度、夹爪和相机布局并不相同。UR5 侧重工业机械臂的稳定性，Franka 提供 7 DoF 机械臂控制接口，ALOHA 与 ARX5 提供更低成本但维护复杂度更高的平台。

传感器默认以 RealSense RGBD 相机为主。系统层面保留 RGB 和 depth 传感器输入；当前推理接口示例中，所请求视角以 PNG image bytes 进入 `state.pkl`，并和时间戳、本体状态、动作队列长度一起组成策略输入。每个工作站连接对应机器人和相机，系统软件负责示教数据采集与在线测试。典型视角包括俯视或主视角、腕部视角，以及单臂设置中的侧视角。相机数量和命名在 Table30 与 Table30 v2 中存在差异，这些差异会影响任务数据和推理输入。

## 视觉复位与测试稳定性

真机 benchmark 的主要变量来自物体初始位置、道具选择、光照、相机外参漂移、夹爪状态和人工操作。RoboChallenge 的复位协议使用 demonstration episode 中留出的参考初始帧，把参考图像叠加到 tester 的实时预览画面上。tester 按视觉重合程度调整物体和场景，使不同模型在接近的初始条件下运行同一任务。

这种视觉复位降低了 tester 经验差异带来的分数波动。经验 tester 可能更接近训练数据分布，陌生 tester 可能引入额外偏差，模型作者参与复位时还可能找到特定物体位置的有利区域。参考图像叠加把复位目标从口头描述变成可见状态，但它不能消除所有环境扰动；光照、背景、相机漂移和硬件磨损仍会进入真机结果。

## stability 与 fairness

RoboChallenge 区分 stability 和 fairness。stability 描述同一模型在同一任务上重复评测时结果波动有多大，直接关系到某个分数是否能被再次得到。fairness 描述多个模型在同一任务集上的相对顺序是否稳定，直接关系到模型比较是否可信。

当前 RoboChallenge 的 benchmark protocol 更偏向 stability。它通过固定任务集、集中维护的机器人和视觉复位协议，让单个模型的任务完成度更容易追溯。comparative protocol 则面向 fairness：同一初始状态下随机选择模型运行，tester 不知道当前运行的是哪个模型，从而减少人为复位对模型相对顺序的影响。这个协议更接近竞赛式比较，但初始系统主要服务固定 benchmark 结果。

## 已知限制

remote robot 范式把模型和推理代码留在参评方环境中，评测侧无法直接验证实际运行的模型是否等于提交名称。多任务 generalist 设置中，参评方也可能为不同任务切换专门策略。RoboChallenge 依赖公开模型、代码和 rollout 材料来提高结果可核查性。

固定参考初始状态也带来另一类限制。测试分布越固定，策略越可能针对这些参考状态或道具配置做适配。视觉复位提高了重复评测的稳定性，但它并不等于开放真实世界泛化测试。RoboChallenge 分数因此应和任务版本、机器人平台、复位协议和 episode 记录一起解释。

## 小结

RoboChallenge 的系统协议把真实机器人变成远程可调用的低层服务：策略保留在参评方环境中，评测侧提供带时间戳的观测、动作队列、机器人状态和复位流程。benchmark protocol 偏向提高同一模型重复测试的 stability，comparative protocol 面向不同模型相对顺序的 fairness；两类结果都需要绑定机器人平台、相机配置、队列状态、视觉复位、tester 操作和 rollout 材料解释。

## 导航

- 返回上级：[RoboChallenge](../01-robochallenge-benchmark.md)
- 上一页：[RoboChallenge](../01-robochallenge-benchmark.md)
- 下一页：[Table30 任务与数据](02-table30-task-data.md)
