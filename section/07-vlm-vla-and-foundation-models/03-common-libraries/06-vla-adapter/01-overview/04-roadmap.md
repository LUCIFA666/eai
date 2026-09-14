# 学习路线图

目标：按跑通第一条链路、理解数据与模型、训练、评测、部署和扩展的顺序学习 VLA-Adapter。

## 第一阶段：建立第一条可运行链路

可以先准备环境、LIBERO 数据、基础 VLM 和官方 Pro checkpoint，再运行 Spatial smoke test。这个阶段重点确认环境、LIBERO benchmark、EGL 渲染、checkpoint 加载、动作输出和结果保存都能正常工作。

## 第二阶段：理解数据与模型组件

跑通之后再回到数据和模型页，重点看数据样本如何进入训练 batch，以及图像、proprio、Pro 配置和 statistics 分别影响哪一层组件。

## 第三阶段：训练并保存可评测 checkpoint

进入 LoRA 微调前，先理解训练配置如何连接 RLDS dataloader、action L1 loss、LoRA merge 和 checkpoint 保存。短程验证主要检查 dataloader、forward、backward、日志和保存链路；策略质量需要放到完整 eval 中判断。

## 第四阶段：用 LIBERO 完整评测验证 checkpoint

本地微调 checkpoint 可以先用 `run_libero_eval.py` 做 Spatial 评测，建立一个可比较的基准，再扩展到 Object、Goal 或 Long。smoke test、official baseline 和本地 checkpoint eval 在记录中的角色不同，适合分开记录和解读。

## 第五阶段：部署为 policy server

`deploy.py` 会启动 policy server，client 通过 `/act` 请求动作。fake client 可以验证 server-client 通信和 action shape；真实机器人 client 还需要 ROS、相机、joint state、限位和急停。policy server 连通说明接口链路正常，benchmark 成功率仍要通过 LIBERO rollout 评测判断。

## 第六阶段：扩展到新数据或新 client

扩展时可以先判断这次改动落在哪一层：数据注册和 transform、模型输入/动作维度、评测适配器、部署 client。更稳妥的做法是每次改一层，并用最小 smoke test 缩小问题范围。

## 导航

- 上一节：[代码地图](03-code-map.md)
- 返回上级：[认识 VLA-Adapter](../01-overview.md)
- 下一节：[安装与第一次跑通](../02-setup.md)
