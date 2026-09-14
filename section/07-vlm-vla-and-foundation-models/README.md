# 模型训练与推理

本章讲如何把第 6 章的数据训练成可部署、可推理、可评测的机器人策略。当前框架分六个二级目录：VLA 基础、策略训练、常用库、部署推理、其他范式、形态与模态扩展。

## 章节结构

| 二级单元 | 三级页面 | 说明 |
|---|---|---|
| [VLA 基础](01-vla-foundations.md) | VA 前史、VLA 基础概念与接口规范、模型架构演变、世界模型 | 讲 VLA 的概念、接口、技术路线和演进过程 |
| [策略训练](02-behavior-cloning.md) | ACT、Diffusion Policy、DAgger、VLA 训练范式、多具身体训练、VLA-RL 后训练指针 | 一条训练主线：BC → SFT/co-training 配比 → 跨具身 → RL 后训练 |
| [常用库](03-common-libraries.md) | RT-1、Octo、RDT、OpenVLA、StarVLA、VLA-Adapter、GR00T、LeRobot、OpenPI | 以知名开源项目为入口，说明训练、数据、评测和部署接口 |
| [部署推理](04-deployment-inference.md) | 推理服务与运行时、推理加速、zero-shot 推理、TiPToP 部署推理案例 | 把 checkpoint、预处理、动作接口和执行链路连接起来 |
| [其他范式](05-advanced.md) | World Action Models（DreamZero、Fast-WAM）、双系统、视频动作模型、实时分块与异步执行、在线学习与自我改进，以及 π0.7、Gemini Robotics、国产开源 VLA 三个模型档案 | 主线之外已广泛使用的建模范式、执行与训练范式，以及旗舰模型档案 |
| [形态与模态扩展](06-embodiment-and-modality.md) | Loco-Manipulation、触觉与力觉 VLA、灵巧手基础模型 | 同样的范式，扩到更难的身体形态与感知模态 |

## 学习目标

- 能解释行为克隆为什么是机器人策略训练的基础范式。
- 能区分“训练范式”和“项目库”：范式讲学习目标，库讲工程入口、数据格式、模型配置和部署脚本。
- 能说明 VA、VLA、动作 token、flow-action 和世界模型之间的演进关系。
- 能把训练好的 checkpoint 接成推理服务，并说明 action runtime 和延迟预算如何设计。

## 本章边界

本章分 VLA 基础、策略训练、常用库、部署推理、其他范式、形态与模态扩展六组内容。训练路线、分布纠错和视觉语言定位等说明放到具体方法、感知章节或具体 VLA 库页面中处理。

## 实践产出

- 一个 state-only BC baseline，用来确认数据和 action schema 正确。
- 一个图像+状态 BC、ACT 或 Diffusion Policy 训练配置。
- 一份常用库选择记录，说明为什么用 OpenPI、LeRobot、OpenVLA、StarVLA、VLA-Adapter 或其它库。
- 一份范式阅读卡片，记录 π0.7/WAM/双系统/ECoT 等路线和当前不能工程化验证的边界。
- 一份部署推理 runbook，包含服务接口、action adapter 和延迟预算。

## 验收方式

- ACT 和 Diffusion Policy 为什么仍然应该放在行为克隆主线下？
- OpenPI、LeRobot、OpenVLA、StarVLA、VLA-Adapter 各自更像“模型库”“训练/数据框架”还是“VLA 研究代码库”？
- π0.7 在本章哪里出现，和 π0/openpi 的关系是什么？
- 一个 checkpoint 上线前，推理服务、action runtime 和延迟预算分别要验收什么？

## References

- LeRobot GitHub. https://github.com/huggingface/lerobot
- OpenPI GitHub. https://github.com/Physical-Intelligence/openpi
- OpenVLA GitHub. https://github.com/openvla/openvla
- StarVLA GitHub. https://github.com/starVLA/starVLA
- VLA-Adapter GitHub. https://github.com/OpenHelix-Team/VLA-Adapter
- Physical Intelligence π0.7 blog. https://www.pi.website/blog/pi07
- DreamZero project. https://dreamzero0.github.io/
- Fast-WAM project. https://yuantianyuan01.github.io/FastWAM/
