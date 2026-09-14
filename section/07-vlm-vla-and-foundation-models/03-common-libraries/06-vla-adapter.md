# VLA-Adapter

目标：以 LIBERO Spatial 和 Pro checkpoint 为主线，跑通 VLA-Adapter 的训练、评测和部署闭环，并理解关键配置如何影响数据、模型和 checkpoint 加载。

[VLA-Adapter](https://github.com/OpenHelix-Team/VLA-Adapter) 是 OpenHelix-Team 发布的 tiny-scale Vision-Language-Action model 实现。本课程以 `prism-qwen25-extra-dinosiglip-224px-0_5b`、LIBERO Spatial、Pro checkpoint、continuous action head 和 LoRA 微调为主线。围绕这条主线，后续页面会依次讲解 LIBERO RLDS 数据、模型组件、checkpoint 组件、LIBERO eval 和 policy server。

## 本节目标

本节围绕下面目标展开：

1. 跑通 LIBERO Spatial 的 checkpoint smoke test、短跑训练、本地 checkpoint 评测和部署 sanity check。
2. 看懂 `dataset_name`、OXE registry、`RLDSBatchTransform` 和 `dataset_statistics.json` 如何连接训练与评测。
3. 分清 Prismatic backbone、proprio projector、action head、LoRA checkpoint 和 Pro flags 的加载关系。
4. 面对 ALOHA fake client、CALVIN 或自定义数据时，可以判断它们与当前 LIBERO 主线的边界。

## 学习路径

| 模块 | 阅读定位 | 主要内容 |
| --- | --- | --- |
| [认识 VLA-Adapter](06-vla-adapter/01-overview.md) | 理解课程为什么选择 LIBERO Spatial、tiny Prismatic、continuous action head 和 Pro checkpoint 作为主线。 | 架构入口、代码地图、学习路线图 |
| [安装与第一次跑通](06-vla-adapter/02-setup.md) | 准备环境、数据、基础 VLM 和 checkpoint，并完成官方 smoke test。 | 环境、路径、数据、基础 VLM、checkpoint |
| [数据接口与管线](06-vla-adapter/03-data.md) | 理解 VLA-Adapter 如何定义数据接口、标准化字段并共享 statistics。 | `dataset_name`、OXE registry、`RLDSBatchTransform`、statistics、自定义数据 |
| [模型组件](06-vla-adapter/04-model.md) | 梳理 VLM、action head 和 proprio projector 的协作关系。 | Prismatic、action chunk、Pro flags、组件加载 |
| [LoRA 微调训练](06-vla-adapter/05-training.md) | 理解 LoRA 微调脚本如何连接参数、batch、loss 和 checkpoint 保存。 | 训练参数、训练循环、短跑、保存与 merge |
| [评测](06-vla-adapter/06-evaluation.md) | 评测本地 checkpoint，并整理日志、视频和结果记录。 | 完整 eval、官方 baseline、失败案例 |
| [部署](06-vla-adapter/07-deployment.md) | 把 checkpoint 加载成 policy server，并检查 `/act` 请求链路。 | `DeployConfig`、`/act`、payload、fake client |
| [扩展边界](06-vla-adapter/08-extension.md) | 接入更多 benchmark 或调整机器人输入输出前，先判断它们和 LIBERO 主线的差异。 | CALVIN、ALOHA、自定义动作/状态 |

## 快速闭环路线

如果当前目标是先建立可运行链路，可以从 [环境安装](06-vla-adapter/02-setup/01-environment.md)、[LIBERO 数据](06-vla-adapter/02-setup/02-libero-data.md)、[基础 VLM 与 Prismatic 配置](06-vla-adapter/02-setup/03-pretrained-backbone.md) 和 [Checkpoint 准备](06-vla-adapter/02-setup/04-checkpoint-setup.md) 开始，再运行 [官方 Checkpoint 链路检查](06-vla-adapter/02-setup/05-checkpoint-smoke-test.md)。

进入训练和评测闭环后，重点看 [LoRA 微调](06-vla-adapter/05-training/01-lora-finetune-command.md)、[短程训练链路检查](06-vla-adapter/05-training/03-short-run-smoke-test.md)、[微调 Checkpoint 评测](06-vla-adapter/06-evaluation/01-finetuned-checkpoint-eval.md) 和 [读评测日志](06-vla-adapter/06-evaluation/02-read-eval-logs.md)。

部署 sanity check 可以继续阅读 [Policy Server](06-vla-adapter/07-deployment/01-policy-server.md)、[Server Request Payload](06-vla-adapter/07-deployment/02-server-request-payload.md) 和 [ALOHA Fake Client](06-vla-adapter/07-deployment/03-aloha-fake-client.md)，重点关注 `/act` 请求、响应和 action shape。

如果目标是完整理解和后续改动，可以先读 [代码地图](06-vla-adapter/01-overview/03-code-map.md)，再进入数据、模型、训练、评测和部署模块。

## 参考环境

| 项目 | 参考值 |
| --- | --- |
| Python | 3.10.16 |
| PyTorch | 2.2.0 |
| FlashAttention | 2.5.5 |
| VLM backbone | `prism-qwen25-extra-dinosiglip-224px-0_5b` |
| 第一条训练数据 | `libero_spatial_no_noops` |
| 第一条评测 suite | `libero_spatial` |
| 第一条部署 sanity check | policy server + ALOHA fake client |

## References

- [VLA-Adapter: An Effective Paradigm for Tiny-Scale Vision-Language-Action Model](https://arxiv.org/abs/2509.09372)
- [OpenHelix-Team/VLA-Adapter GitHub repository](https://github.com/OpenHelix-Team/VLA-Adapter)
- [VLA-Adapter project page](https://vla-adapter.github.io/)
- [VLA-Adapter Hugging Face collection](https://huggingface.co/VLA-Adapter)
- [LIBERO benchmark](https://github.com/Lifelong-Robot-Learning/LIBERO)

## 导航

- 上一节：[StarVLA](05-starvla.md)
- 返回上级：[常见库与框架](../03-common-libraries.md)
- 下一节：[认识 VLA-Adapter](06-vla-adapter/01-overview.md)
