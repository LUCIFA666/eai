# 常用库

本组以知名开源项目为入口，说明 VLA / robot policy 的训练、数据、评测和部署接口。按"模型档案"到"完整框架"的顺序排列：

- [RT-1](03-common-libraries/01-rt1.md)：动作离散化 Transformer 策略的起点（理论 + 实践）。
- [Octo](03-common-libraries/02-octo.md)：跨具身通用策略与 Open X-Embodiment 数据（理论 + 实践）。
- [RDT](03-common-libraries/03-rdt.md)：双臂扩散基础模型（理论 + 实践 + 微调）。
- [OpenVLA](03-common-libraries/04-openvla.md)：7B 开源 VLA 全链路——安装、动作推理、数据统计、微调、评测、部署、扩展。
- [StarVLA](03-common-libraries/05-starvla.md)：乐高式 VLA 研究框架——数据契约、框架族（OFT/FAST/π/GR00T）、训练、部署与 LIBERO 端到端。
- [VLA-Adapter](03-common-libraries/06-vla-adapter.md)：小骨干高效桥接的轻量 VLA。
- [GR00T](03-common-libraries/07-groot.md)：NVIDIA 人形基础模型库（待写）。
- [LeRobot](03-common-libraries/08-lerobot.md)：Hugging Face 机器人学习全流程框架——数据格式、ACT/DP/SmolVLA/xVLA/π0 系列训练。
- [OpenPI](03-common-libraries/09-openpi.md)：Physical Intelligence π 系模型库——π0 / π0-FAST / π0.5 训练、微调与自定义数据。

## 选型提示

- 想以最小代价跑通"数据 → 训练 → 评测"闭环：先看 LeRobot。
- 想研究 VLA 架构与配比：看 StarVLA、OpenVLA。
- 想用 π 系 flow-matching 模型：看 OpenPI。
- 双臂 / 人形本体：看 RDT、GR00T。
