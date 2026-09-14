# 安装与第一次跑通

目标：准备 OpenVLA 的最小推理环境，下载代码和 checkpoint，区分 checkpoint 类型，并用 `predict_action` 跑通一次图像到 7 维动作的调用。

这一单元先完成最小推理前的几项检查：环境能导入，代码和 checkpoint 在本地，checkpoint 能加载，`predict_action` 能返回动作。LoRA 训练、LIBERO rollout、Bridge 真机评测和 REST server 连通都需要额外证据。

## 学习路径

| 页面 | 重点 |
| --- | --- |
| [准备环境](02-setup/01-environment.md) | 最小推理、LoRA、LIBERO / Bridge 评测各自依赖哪些包。 |
| [下载代码与 checkpoint](02-setup/02-download-and-cache.md) | 克隆源码，下载或缓存 HF checkpoint，处理本地目录和离线加载。 |
| [Checkpoint 与模型加载](02-setup/03-checkpoints-and-model-loading.md) | HF 主模型、早期 checkpoint、Prismatic checkpoint、本地 fine-tuned checkpoint 的差别。 |
| [第一次 `predict_action`](02-setup/04-first-predict-action.md) | 用 `AutoProcessor`、`AutoModelForVision2Seq` 和 `predict_action` 跑通一次 smoke test。 |

## 最小推理的验证范围

最小推理能返回一个 shape 为 `(7,)` 的 action，说明 processor、prompt、模型加载、action token decode 和反归一化这几步可以连起来。这个结果还没有进入仿真或真实机器人环境，只能作为调用链路正常的证据。

动作返回只覆盖调用链路；模型结构、动作统计量和 rollout 结果需要分别检查。

## 相关文件和入口

| 入口 | 作用 |
| --- | --- |
| `requirements-min.txt` | 最小 HF 推理依赖。 |
| `pyproject.toml` | 完整源码安装、LoRA、RLDS、训练和评测依赖。 |
| Hugging Face Hub | `openvla/openvla-7b`、LIBERO fine-tuned checkpoints 和 Prismatic checkpoint。 |
| `prismatic/extern/hf/processing_prismatic.py` | `AutoProcessor`、图像预处理和文本 tokenization。 |
| `prismatic/extern/hf/modeling_prismatic.py` | HF 模型、`predict_action()`、action decode 和反归一化。 |
| `vla-scripts/finetune.py` | LoRA 微调入口，以及本地 fine-tuned checkpoint 的保存方式。 |
| `vla-scripts/deploy.py` | REST server 加载本地 checkpoint 和调用 `predict_action` 的方式。 |

## 导航

- 上一节：[阅读顺序](01-overview/04-reading-order.md)
- 返回上级：[OpenVLA](../04-openvla.md)
- 下一节：[准备环境](02-setup/01-environment.md)
