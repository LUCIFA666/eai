# StarVLA 是什么

官方 README 把 StarVLA 称为"像乐高一样的 VLA 开发代码库"。这个比喻很贴切：积木块的形状规格统一，可以自由拼装；StarVLA 的 VLM、动作头、数据接口、训练器和部署服务也按统一接口组织，可以按需替换某一块而不动其余部分。

StarVLA 覆盖 VLA 研究的完整链路：数据读取、模型组合、训练、部署和 benchmark 评测。核心组件如下：

| 组件 | 作用 | 典型示例 |
|---|---|---|
| 数据接口 | 把机器人轨迹整理成训练样本 | LeRobot、LIBERO、Open X-Embodiment 风格数据 |
| VLM backbone | 处理图像和语言指令 | Qwen2.5-VL、Qwen3-VL、Gemma、MiniCPM-V |
| action head | 把模型特征变成机器人动作 | MLP 回归、FAST token、flow matching |
| 训练入口 | 控制损失、优化器、冻结策略和 checkpoint | VLA 训练、VLA+VLM 协同训练 |
| 部署接口 | 把 checkpoint 封装成策略服务 | policy server、websocket 协议、动作后处理 |
| 评测入口 | 把策略接到仿真或真实机器人环境 | LIBERO、SimplerEnv、RoboCasa、RoboTwin |

## StarVLA 解决的问题

具身智能研究里有几类重复工作：
- 不同数据集的相机名、动作维度、夹爪定义不一致
- 不同 VLM 的输入格式不同
- 动作可以用连续回归、离散 token 或生成模型来预测
- 训练得到的 checkpoint 需要接到多个 benchmark 里评测
- 新实验需要替换模型组件，同时复用已有流程
  
StarVLA 把这些重复工作整理成稳定接口。

## 核心接口

理解 StarVLA 从两个函数开始：

```python
def forward(self, examples, **kwargs):
    """训练时调用，返回 action_loss 等损失。"""

def predict_action(self, examples, **kwargs):
    """推理时调用，返回 normalized_actions 等动作结果。"""
```

训练器只关心 `forward()` 返回的损失，部署服务只关心 `predict_action()` 返回的动作。图像处理、prompt 组织、动作头的具体实现都在 framework 内部，外部不需要关心。

## 训练流程

一个 VLA 样本通常长这样：

```python
example = {
    "image": [primary_image, wrist_image],
    "lang": "put the mug on the plate",
    "state": robot_state,
    "action": future_actions,
}
```

训练时，StarVLA 从 YAML 配置出发，经过这条主线：

```text
训练 YAML
  -> build_dataloader()     读出 List[dict] batch
  -> build_framework()      构建模型
  -> framework.forward()    计算 action_loss
  -> 反向传播
  -> 保存 checkpoint
```

dataloader 输出的是原始样本字典，而不是拼好的大 tensor。这样 framework 可以自己决定图像缩放、文本 prompt 格式、动作 token 化或连续动作处理方式。

## 推理流程

评测或部署时，环境只有当前观察和语言指令，没有未来动作标签：

```text
checkpoint
  -> PolicyServerWrapper 加载模型
  -> benchmark client 发送 image / lang / state
  -> framework.predict_action()
  -> 得到一段未来动作
  -> 动作反归一化
  -> 环境 step()
```

`predict_action()` 返回的 `normalized_actions` 还在训练时的归一化空间里，部署服务会根据保存的统计量把它还原成环境动作。

## checkpoint 配套文件

训练结束后，运行目录需要保留完整结构：

```text
<RUN_DIR>/
├── config.yaml
├── dataset_statistics.json
└── checkpoints/
    └── steps_*.pt
```

`config.yaml` 告诉 StarVLA 用哪个 framework、动作维度和数据混合名。`dataset_statistics.json` 记录动作和状态的统计量，用于推理时反归一化。部署时缺少这些文件，模型即使能输出数字，环境也无法正确执行。

## 学会 StarVLA 我们可以做到

StarVLA 适合用来做这些事：

- 比较 OFT、FAST、PI、GR00T 等动作预测方式在同一数据集上的差异。
- 在 LeRobot 格式数据上训练自己的 VLA。
- 把同一个 checkpoint 接到多个 benchmark 里评测。
- 做 VLA+VLM 协同训练，观察语言视觉任务和动作任务的关系。
- 接入新的 VLM、动作头或机器人数据集。

如果当前目标只是了解概念，可以先读 overview 和数据系统；如果目标是复现实验，可以直接走 LIBERO 端到端实战链路。

## 小结

- StarVLA 覆盖 VLA 的数据、模型、训练、部署和评测完整流程。
- 两个核心接口：`forward()` 返回损失，`predict_action()` 返回动作。
- checkpoint 需要配合 `config.yaml` 和 `dataset_statistics.json` 一起使用。
- `examples/` 是真实实验入口，LIBERO 是第一条推荐链路。

## 动手练习

1. 打开官方仓库 `assets/starVLA_overview.png`，找出数据、模型、训练和评测四个部分对应图中哪些方框，并说明它们的连接顺序。
2. 打开官方仓库 `assets/starvla_variants.png`，找出 OFT、FAST、PI、GR00T 四个变体在动作输出方式上的区别，不需要理解实现细节，只需说出每个变体的动作类型。
3. 根据本节内容，解释为什么 `dataset_statistics.json` 在部署时不可缺少，以及如果只保留 `.pt` 权重文件会出现什么问题。

## 参考资料

- [StarVLA 论文](https://arxiv.org/abs/2604.05014)
- [StarVLA GitHub](https://github.com/starVLA/starVLA)

## 导航

- 上一节：[认识 StarVLA](../01-overview.md)
- 返回上级：[认识 StarVLA](../01-overview.md)
- 下一节：[02 代码结构](02-code-struct.md)
