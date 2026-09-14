# StarVLA

StarVLA 是一个面向具身智能研究的开源 VLA 代码库：模型接收图像和语言指令，输出机器人可以执行的动作。学习 StarVLA 时，先把它当成一套完整的 VLA 实验流程来看：

```text
流程
  -> 图像、语言、状态、动作
  -> VLA 模型
  -> 训练得到 checkpoint
  -> 推理服务
  -> LIBERO 等 benchmark 评测
```

StarVLA 的官方定位是 **A Lego-like Codebase for Vision-Language-Action Model Developing**。意为：研究者可以在 StarVLA 里替换视觉语言模型、动作预测方式、数据集和评测环境，在同一套训练与部署框架里比较不同设计。

![StarVLA overview](05-starvla/assets/starVLA_overview.png)

## 本章怎么读

本章前几节先建立直观认识，后几节再进入配置、训练、部署和扩展。

| 章节 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [认识 StarVLA](05-starvla/01-overview.md) | StarVLA 解决什么问题，完整流程怎么走 | VLA 样本、主流程、代码地图 |
| [安装与链路验证](05-starvla/02-setup.md) | 怎么准备环境并做最小检查 | 环境安装、链路验证 |
| [数据接口](05-starvla/03-data.md) | 一个机器人轨迹怎样变成训练样本 | LeRobot、字段映射、归一化、数据混合 |
| [模型框架](05-starvla/04-frameworks.md) | StarVLA 怎样组织不同 VLA 模型 | `forward()`、`predict_action()`、OFT、FAST、PI、GR00T |
| [训练机制](05-starvla/05-training.md) | 一次训练命令背后发生了什么 | YAML、单卡小步训练、checkpoint、冻结模块 |
| [部署与推理服务](05-starvla/06-deployment.md) | checkpoint 怎样变成可评测策略 | policy server、client 请求、动作后处理 |
| [LIBERO 端到端实战](05-starvla/07-libero-end-to-end.md) | 怎么完整走通数据、训练、评测并对比三条路线 | 数据准备、训练命令、评测、OFT / PI / WM4A |
| [其他 Benchmark](05-starvla/08-other-benchmarks.md) | SimplerEnv、RoboCasa、RoboTwin、BEHAVIOR 怎么适配 | benchmark 目录模式、各环境差异 |
| [扩展 StarVLA](05-starvla/09-extension.md) | 怎么接自己的数据、机器人或动作头 | 最小改动路径、调试顺序 |
| [速查表](05-starvla/99-cheat-sheet.md) | 常用命令和排错入口在哪里 | 命令模板、路径占位符、常见错误 |

## 参考资料

- [StarVLA 论文](https://arxiv.org/abs/2604.05014)
- [StarVLA GitHub](https://github.com/starVLA/starVLA)

## 导航

- 上一节：[OpenVLA](04-openvla.md)
- 返回上级：[常见库与框架](../03-common-libraries.md)
- 下一节：[认识 StarVLA](05-starvla/01-overview.md)
