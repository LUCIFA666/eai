# Data Engine

Data Engine 评估世界模型生成的数据能否改善下游策略。最终对象不是视频观感，而是由生成的图像—动作轨迹训练出的策略在 RoboTwin 中的成功率。

## 两阶段数据链

第一阶段以首帧和指令为条件生成未来视频。第二阶段冻结世界模型，并使用 VPP 风格的逆动力学模型（IDM）从中间视频特征恢复动作。IDM 的扩散动作头在去噪过程中同时接收世界模型特征、机器人状态和指令，形成与图像序列对齐的动作标签。

```text
first frame + instruction
        ↓
world model → synthetic video + intermediate feature
        ↓
IDM / VPP action head → action label
        ↓
image-action trajectory → fine-tune π0.5
        ↓
RoboTwin execution → success rate
```

视频清晰但特征不包含控制信息时，动作标签可能偏离；动作标签近似正确但视频状态持续漂移时，策略学到的观测—动作对也不可靠。Data Engine 因而同时检验可见状态和动作可恢复性。

## 论文设置

论文 v2 使用 `adjust_bottle` 和 `click_bell` 两个任务。每个世界模型、每个任务生成 25 条轨迹，固定 π0.5 基础策略在这些数据上训练，再各执行 100 次。零样本 π0.5 和真实数据训练结果分别提供下、上参照。

以 `click_bell` 为例，零样本策略成功率为 5%，真实数据训练为 66%。WoW 生成数据训练得到 71%，RoboMaster 得到 68%；这一结果说明特定生成数据在该任务和训练配置下有效，不表示合成数据普遍优于真实示范。`adjust_bottle` 上所有生成数据策略仍低于真实数据的 77%。

## 公开接口契约

公开 Data Engine 协议使用五个 RoboTwin 2.0 子任务：`adjust_bottle`、`click_bell`、`blocks_ranking_rgb`、`open_laptop` 和 `pick_dual_bottles`。评测数据包含每帧高位相机图像、当前状态、指令和长度为 40 的 `joint14` 动作序列。`joint14` 的布局为左右臂各 6 个关节角与 1 个夹爪状态。

官方评测使用统一预训练 checkpoint，将 π0.5 微调 10,000 步；视觉输入只启用高位相机，不使用腕部相机。每个任务在 RoboTwin clean 设置下执行 100 次，报告逐任务成功率。模型之间的比较要求生成样本数量、训练配置和执行协议一致。

## 具体失败边界

- 图像逼真但动作标签与接触时刻错位时，训练损失仍可能下降，执行阶段却在抓取前闭合夹爪。
- 少量高质量轨迹和大量重复轨迹可能产生相近训练样本数，但任务覆盖不同；成功率不能只归因于单帧质量。
- 仿真器随机化、策略优化和动作归一化会共同影响最终结果，同一生成数据集的一次训练结果不是无噪声估计。

Data Engine 测量生成数据在固定训练链中的边际效用。它不能区分改进究竟来自视频状态、动作标签、样本多样性还是策略对某类伪影的适应。

## 导航

- 返回上级：[具身任务评测](../04-embodied-task-evaluation.md)
- 上一节：[具身任务评测](../04-embodied-task-evaluation.md)
- 下一节：[Policy Evaluator](02-policy-evaluator.md)
