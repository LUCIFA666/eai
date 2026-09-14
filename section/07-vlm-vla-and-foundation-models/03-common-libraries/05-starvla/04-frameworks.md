# 模型框架

目标：读懂 StarVLA 怎样把不同 VLA 模型放进同一套训练和部署流程里。

在 StarVLA 中，一个 framework 可以理解为“一套完整的模型包装”。它接收 dataloader 给出的样本字典，内部完成图像处理、文本组织、VLM 前向和动作预测，对外提供两个核心入口：

```python
def forward(self, examples, **kwargs):
    """训练入口，返回 action_loss 等损失。"""

def predict_action(self, examples, **kwargs):
    """推理入口，返回一段未来动作。"""
```

只要这两个入口稳定，训练器和部署服务就可以复用。framework 内部可以使用 MLP 连续回归、FAST 动作 token、flow matching 或 world model 表征。

## 本节目标

本节围绕下面几个问题展开：

1. `baseframework` 规定了哪些接口？
2. `framework.name` 怎样选择具体模型？
3. QwenOFT、QwenFast、QwenPI、QwenGR00T 的动作输出方式有什么区别？
4. VLM wrapper 和 action head 怎样组合？
5. world model 路线怎样接入同一套流程？

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [01 baseframework 与 registry](04-frameworks/01-baseframework-and-registry.md) | framework 如何被构建 | `build_framework()`、注册表、核心接口 |
| [02 Qwen-OFT](04-frameworks/02-qwen-oft.md) | MLP 连续动作回归怎么做 | action placeholder、hidden state、L1 loss |
| [03 Qwen-FAST](04-frameworks/03-qwen-fast.md) | 动作 token 路线怎么做 | FAST tokenizer、自回归生成 |
| [04 Qwen-PI](04-frameworks/04-qwen-pi.md) | layer-wise flow matching 怎么用 | 多层 VLM hidden states、action chunk |
| [05 Qwen-GR00T](04-frameworks/05-qwen-gr00t.md) | DiT flow matching 动作头怎么用 | 最后一层 hidden state、cross attention、action chunk |
| [06 VLM 封装与动作头](04-frameworks/06-vlm-and-action-heads.md) | 组件如何按配置选择 | VLM wrapper、动作头组件 |
| [07 WM4A](04-frameworks/07-wm4a.md) | world model 如何接入动作预测 | Cosmos/Wan、视频 DiT、动作头 |

## 框架变体总览

![StarVLA variant architectures](assets/starvla_variants.png)

| 变体 | 配置名 | 动作输出方式 | 入门理解 |
|---|---|---|---|
| StarVLA-OFT | `QwenOFT` | VLM hidden state + MLP 回归连续动作 | 最容易作为 baseline 阅读 |
| StarVLA-FAST | `QwenFast` | 连续动作编码为离散 token，再自回归预测 | 把动作也放进 token 序列 |
| StarVLA-PI | `QwenPI`/`QwenFM` | 多层 VLM 表征条件下的 flow matching | 用生成过程建模连续动作 |
| StarVLA-GR00T | `QwenGR00T` | VLM 表征 + flow matching DiT 动作头 | 面向更复杂的 action chunk 生成 |
| WM4A | `CosmoPredict2GR00T` | World model backbone + flow matching DiT 动作头 | 用视频世界模型替换 VLM backbone |

## 阅读建议

初学时建议先读 `QwenOFT`。它的动作头最直接，能帮你看清样本怎样进入 VLM，hidden state 怎样变成动作。之后再读 `QwenFast` 和 flow matching 变体，理解动作 token 与连续动作生成的差异。

## 导航

- 上一节：[数据接口](03-data.md)
- 返回上级：[StarVLA](../05-starvla.md)
- 下一节：[01 baseframework 与 registry](04-frameworks/01-baseframework-and-registry.md)
