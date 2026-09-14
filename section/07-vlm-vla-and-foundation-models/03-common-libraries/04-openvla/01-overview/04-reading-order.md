# 阅读顺序

目标：根据学习目标选择 OpenVLA 后续页面的阅读路线。

OpenVLA 涉及模型结构、动作 token、数据统计量、微调、评测和部署等多个模块，可以按自己的目标选择入口。

## 理解原理

先读 [OpenVLA 是什么](01-what-is-openvla.md)，熟悉它的组成和使用范围；再读 [架构与推理主线](02-architecture-and-inference.md)，把图像、指令、action tokens、`predict_action` 和连续动作输出放到同一条主线上。

接着进入 [模型结构与动作推理](../03-model-and-action-inference.md)，重点看 Prismatic backbone、action tokenizer 和 `predict_action`。随后读 [数据与动作统计量](../04-data-and-statistics.md)，理解 OXE / RLDS、mixture 和 `dataset_statistics.json`。最后再进入 [LoRA 微调](../05-finetuning.md)，把模型设计和 LoRA 适配联系起来。

这条路线重点处理三个问题：动作怎样 token 化，统计量怎样影响动作尺度，训练指标和 rollout 成功率怎样分开解释。

## 跑通最小推理

先从 [安装与第一次跑通](../02-setup.md) 准备环境，再到 [下载代码与 checkpoint](../02-setup/02-download-and-cache.md) 处理源码、权重和缓存目录。随后读 [Checkpoint 与模型加载](../02-setup/03-checkpoints-and-model-loading.md)，对齐 checkpoint 类型和加载入口。完成这些准备后，运行 [第一次 `predict_action`](../02-setup/04-first-predict-action.md) 中的最小脚本，检查 `AutoProcessor`、prompt、图像和 `predict_action` 是否能返回 7 维动作。

看到动作输出后，可以回到 [架构与推理主线](02-architecture-and-inference.md)，把刚才的输出放回单步推理、统计量和 rollout 证据的关系里。继续验证策略表现时，再进入 [LIBERO OpenVLA 评测](../06-evaluation/01-libero-openvla-eval.md)。

最小推理属于 smoke test。它说明调用链路正常，任务完成情况还要看 LIBERO、Bridge 或真实机器人环境中的 rollout。

## 读代码和定位问题

遇到参数、shape、统计量或 checkpoint 问题时，先读 [代码地图](03-code-map.md)。这页现在按 OpenVLA 仓库源码入口组织，可以从 HF 接口、模型主体、backbone、RLDS / OXE 数据、训练、评测部署和工具脚本几个方向进入。

动作 token 相关问题看 `prismatic/vla/action_tokenizer.py`；HF 推理、`unnorm_key` 和 action 维度问题看 `prismatic/extern/hf/modeling_prismatic.py`；数据统计量问题看 `prismatic/vla/datasets/datasets.py` 和 `prismatic/vla/datasets/rlds/utils/data_utils.py`。训练和 checkpoint 保存看 `vla-scripts/finetune.py`；rollout 和部署分别看 LIBERO / Bridge eval 脚本和 `vla-scripts/deploy.py`。

第一次读源码时，可以先从配置类和短函数开始。OpenVLA 的常用排查入口集中在 `ActionTokenizer`、`predict_action()`、`FinetuneConfig`、LIBERO `GenerateConfig` 和 `OpenVLAServer`。

## 复现评测

评测路线从最小 `predict_action` 开始，先确认模型在当前环境中能加载并返回 action。随后进入 [LIBERO OpenVLA 评测](../06-evaluation/01-libero-openvla-eval.md)，重点看 OpenVLA checkpoint、`center_crop`、`unnorm_key`、gripper 处理和结果记录。

真实机器人评测对应 [Bridge WidowX 评测入口](../06-evaluation/02-bridge-widowx-eval.md)。结果整理放在 [结果与失败记录](../06-evaluation/03-results-and-failure-records.md)，训练日志、rollout 成功率和失败样例分开记录。

LIBERO 通用背景留给 LIBERO 章节。OpenVLA 章节只解释 checkpoint、图像处理和动作反归一化这些与 OpenVLA 直接相关的部分。

## 部署验证

部署路线从本地 `predict_action` 开始。确认模型能返回动作后，读 [REST Server](../07-deployment/01-rest-server.md)，看 `vla-scripts/deploy.py` 如何把模型包装成 `/act` 接口。

接着读 [请求与 Action 格式](../07-deployment/02-request-and-action-format.md)，核对 payload 中的 `image`、`instruction` 和可选 `unnorm_key`。最后读 [延迟与控制频率](../07-deployment/03-latency-and-control-frequency.md)，把单步延迟和控制频率联系起来。

policy server 连通只能说明模型服务可以收到请求并返回 action。真实机器人部署还需要硬件接口、控制周期、安全边界和环境侧验证。

## 扩展阅读

跑通 vanilla OpenVLA 主线后，可以读 [扩展方向](../08-extension.md)。这页把 full fine-tuning、training from scratch、quantized inference、OFT 和 FAST 放在一起，重点看它们分别改动训练入口、动作表示还是部署效率。

## 通用的阅读路径

下面这个顺序可以作为通用的阅读路径：

1. [OpenVLA 是什么](01-what-is-openvla.md)
2. [架构与推理主线](02-architecture-and-inference.md)
3. [代码地图](03-code-map.md)
4. [下载代码与 checkpoint](../02-setup/02-download-and-cache.md)
5. [第一次 `predict_action`](../02-setup/04-first-predict-action.md)
6. [Action Tokenizer](../03-model-and-action-inference/02-action-tokenizer.md)
7. [`dataset_statistics.json`](../04-data-and-statistics/03-dataset-statistics.md)
8. [LoRA 启动命令](../05-finetuning/01-lora-command.md)
9. [LoRA 训练参考](../05-finetuning/04-training-reference.md)
10. [LIBERO OpenVLA 评测](../06-evaluation/01-libero-openvla-eval.md)
11. [REST Server](../07-deployment/01-rest-server.md)

这个顺序先建立 OpenVLA 的主线，再通过最小推理和代码入口把概念落到可检查的文件，最后进入微调、评测和部署。

## 导航

- 上一节：[代码地图](03-code-map.md)
- 返回上级：[认识 OpenVLA](../01-overview.md)
- 下一节：[安装与第一次跑通](../02-setup.md)
