# OpenVLA

OpenVLA 是一个开源 Vision-Language-Action 模型和代码库。它以 Prismatic-7B VLM 为基础，把图像观测、语言指令和机器人动作组织成 action token 预测任务：模型根据当前图像和指令生成一组 action tokens，再把这些 tokens 还原成连续机器人动作。

本节围绕几个核心问题展开：模型从哪里来，动作怎样进入 tokenizer，数据统计量怎样影响动作尺度，`predict_action` 在推理时做了哪些事，LoRA 微调怎样保存 checkpoint，评测和部署分别能验证到哪一步。

## 本节目标

本节目标是把 OpenVLA 从模型到实验的主线串起来：

1. 认识 OpenVLA 的定位：开源 VLA、Prismatic backbone，以及图像和语言指令到动作输出的基本形式。
2. 跑通代码、checkpoint 加载和第一次 `predict_action`，确认最小推理链路能返回动作。
3. 理解 action tokenization、`dataset_statistics.json` 和 `unnorm_key` 对动作尺度的影响。
4. 完成 LoRA 微调记录、LIBERO rollout 分析和 REST server 连通检查，记录训练状态、策略表现和接口连通情况。
5. 根据问题找到模型、数据、训练、评测、部署和扩展方向的入口。

## 学习路径

| 模块 | 负责内容 | 对应问题 |
| --- | --- | --- |
| [认识 OpenVLA](04-openvla/01-overview.md) | OpenVLA 的定位、架构与推理主线、代码入口和阅读顺序。 | 定位概念、代码入口和实操页面。 |
| [安装与第一次跑通](04-openvla/02-setup.md) | 环境、checkpoint 类型和第一次 `predict_action`。 | 模型加载、动作返回和 smoke test 结果的检查入口。 |
| [模型结构与动作推理](04-openvla/03-model-and-action-inference.md) | Prismatic backbone、action tokenizer 和 `predict_action` 动作推理。 | action token 如何生成，动作维度和反归一化统计量怎样对应。 |
| [数据与动作统计量](04-openvla/04-data-and-statistics.md) | OXE / RLDS 数据、mixture、`dataset_statistics.json` 和 custom data 入口。 | 数据集名称、统计量 key 和动作尺度之间怎样对齐。 |
| [LoRA 微调](04-openvla/05-finetuning.md) | LoRA 微调命令、`finetune.py`、训练日志、训练曲线和 checkpoint 保存。 | 训练指标、adapter、merged checkpoint、曲线和统计量文件各自说明什么。 |
| [评测](04-openvla/06-evaluation.md) | LIBERO OpenVLA eval、Bridge WidowX eval、结果和失败记录。 | rollout 成功率、单次复现实验和真实机器人评测记录的区别。 |
| [部署](04-openvla/07-deployment.md) | REST server、`/act` 请求格式、action 返回格式、延迟和控制频率。 | server 连通、动作 shape 正常和真实部署能力之间的差别。 |
| [扩展方向](04-openvla/08-extension.md) | 原始 OpenVLA 之外的动作表示、微调配方和推理速度改进。 | 区分原始 OpenVLA 主线和 OpenVLA 之后的扩展方向。 |

## References

- Kim et al. OpenVLA: An Open-Source Vision-Language-Action Model. arXiv:2406.09246, 2024. <https://arxiv.org/abs/2406.09246>
- OpenVLA project website. <https://openvla.github.io/>
- OpenVLA GitHub. <https://github.com/openvla/openvla>
- OpenVLA Hugging Face Models. <https://huggingface.co/openvla>

## 导航

- 上一节：[LeRobot](08-lerobot.md)
- 返回上级：[常用库](../03-common-libraries.md)
- 下一节：[认识 OpenVLA](04-openvla/01-overview.md)
