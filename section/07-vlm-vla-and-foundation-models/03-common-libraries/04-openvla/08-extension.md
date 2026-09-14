# 扩展方向

目标：理解原始 OpenVLA 主线之外的几类扩展，以及它们分别改动训练入口、推理加载方式还是动作表示。

这页讨论两类扩展。第一类仍在 OpenVLA 官方仓库内，可以直接落到本地训练脚本、评测脚本和部署链路中的代码对象；第二类是 OpenVLA 之后出现的外部扩展项目，它们延续 OpenVLA 的任务设定，但会改 fine-tuning 配方或动作表示。

## 原始主线和扩展方向

当前这几类扩展的差别，主要在于它们改动哪一层，以及本地还能对到哪些检查点：

| 方向 | 改动对象 | 本地检查点 | 与 vanilla 的关系 |
| --- | --- | --- | --- |
| Full fine-tuning | checkpoint 形态、训练入口、训练组织 | `openvla/openvla-7b-prismatic`、`vla-scripts/train.py` | 在现有 OpenVLA checkpoint 上继续训练全部参数 |
| Training from scratch | base VLM、data mixture、训练配置 | `prismatic/conf/vla.py`、`VLAConfig`、`save_dataset_statistics()` | 不再沿用现成 OpenVLA checkpoint 的训练起点 |
| Quantized inference | 推理加载方式、延迟和控制频率检查 | `load_in_8bit` / `load_in_4bit`、`predict_action()`、延迟统计 | 模型任务不变，部署侧成本和时延特征变化 |
| OFT | fine-tuning 配方、输入观测、连续动作路线 | 项目说明与现有 OpenVLA 动作 / 训练接口的对照点 | 保留 OpenVLA 任务方向，但重写 fine-tuning 与动作表示假设 |
| FAST | action tokenizer 表示和生成长度 | 项目说明、`ActionTokenizer`、`max_new_tokens` | 保留自回归动作生成框架，但压缩动作 token 表示 |

下面先看官方仓库内还能直接落到本地代码对象的路线，再看 OpenVLA 之后出现的外部扩展项目。

## Full fine-tuning

Full fine-tuning 仍然属于 OpenVLA 官方仓库内的训练扩展。LoRA 只训练 adapter 参数，而 full fine-tuning 会更新 75 亿级参数模型，需要 Prismatic-compatible checkpoint、`vla-scripts/train.py` 和更重的 FSDP 训练组织。

这条路线和 LoRA 的主要差别在 checkpoint 与训练入口：

| 项目 | LoRA 路线 | Full fine-tuning 路线 |
| --- | --- | --- |
| 起始 checkpoint | `openvla/openvla-7b` | `openvla/openvla-7b-prismatic` |
| 训练入口 | `vla-scripts/finetune.py` | `vla-scripts/train.py` |
| 训练组织 | HF AutoClass + PEFT LoRA | Prismatic training path + FSDP |
| 产物使用 | merged HF checkpoint 可直接进入推理 / 部署 | 需要转换成 HF-compatible checkpoint 后再走 AutoClass |

如果 LoRA 在目标域上已经能稳定拟合，并且 rollout 表现接近需求，full fine-tuning 通常放在 LoRA 之后考虑。它更适合数据分布和预训练分布差距很大、LoRA 容量不足，或者需要同时调整视觉侧、语言侧和动作预测能力的情况。这条路线依赖数据统计量、`unnorm_key`、评测口径和 checkpoint 转换流程已经分别可验证。

## Training from scratch

Training from scratch 和 full fine-tuning 都会进入 `vla-scripts/train.py`，但两者改动的起点不同：full fine-tuning 从现成的 OpenVLA checkpoint 继续训练，training from scratch 则同时改 base VLM、data mixture 和整套训练配置。`prismatic/conf/vla.py` 中的 `VLAConfig` 会决定 base VLM、数据 mixture、冻结策略、batch size、world size、学习率和训练策略。源码中默认入口会检查 `expected_world_size`，这意味着配置里的 GPU 数量和实际 `torchrun` world size 必须对齐。

这条路线的重点是检查训练系统整体准备情况，启动命令只是最后一步：

| 检查项 | 影响 |
| --- | --- |
| `vla_id` | 训练配置、日志目录和 checkpoint 名称。 |
| `base_vlm` | 从哪个 Prismatic VLM 出发。 |
| `data_mix` | 使用哪组 OXE / RLDS 数据 mixture。 |
| `expected_world_size` | 分布式训练启动时的 GPU 数量检查。 |
| `save_dataset_statistics()` | 训练产物能否带上推理时需要的动作统计量。 |

原始 OpenVLA checkpoint 背后是大规模机器人数据和高成本训练。课程复现更适合从官方 checkpoint 出发，先把数据统计量、LoRA、rollout 和 deployment 这条链路逐段核对清楚；training from scratch 更直接对应训练系统本身的配置、数据和分布式组织。

## Quantized inference

量化推理更适合看成部署侧的推理选项，而不是和 OFT、FAST 同类的训练或动作表示路线。当前本地 OpenVLA 代码里，量化加载直接落在评测脚本中的 `load_in_8bit` / `load_in_4bit` 参数；动作链路本身仍然走 `predict_action()`，但显存占用、单步延迟和控制频率判断会随加载方式变化。

显存只是量化推理的一项指标。OpenVLA 的动作仍然是自回归生成的，生成 token 的耗时会进入闭环控制周期；部署页记录 mean、median、p95，也是在检查这条链路是否适合当前控制频率。机器人控制的总时延还会受请求往返、图像获取、动作下发和环境反馈影响。OpenVLA 当前 troubleshooting 建议里，和 action chunking 相关的经验性说明指向的是 `5-10Hz` 一带的数据采集 / 控制频率讨论，不应直接写成所有部署场景都成立的通用结论。

沿着本地代码和部署记录，量化推理至少要分三步检查：

1. 单步 `predict_action()` 能返回预期 action shape。
2. REST 或本地推理延迟能稳定记录 mean、median、p95 这类指标。
3. rollout 或机器人端记录能说明策略表现是否还能成立。

第一步说明量化加载后的动作链路仍然可用，第二步说明部署侧性能，第三步才开始回答任务表现。

## OFT

OFT 是 OpenVLA 之后出现的一条后续 fine-tuning 路线。相对 vanilla OpenVLA fine-tuning，它更关注更快推理、更高成功率、多图像输入、高频双臂控制和连续动作路线。

OFT 属于 OpenVLA 之后的外部扩展项目。vanilla OpenVLA 里的 LoRA、action token、`predict_action` 和 REST server，是理解 OFT 的基础；真正切换到 OFT 时，下面四件事会重新影响实现和结果：

| 检查项 | 原因 |
| --- | --- |
| 动作表示 | OFT 使用连续动作路线，需要重新建立和 vanilla OpenVLA 256-bin action tokenizer 对应的判断标准。 |
| 输入观测 | 多图像输入会改变 processor、batch 字段和部署 payload。 |
| checkpoint 产物 | 训练产物是否仍能被当前推理 / 部署入口直接加载，需要按 OFT 项目说明核对。 |
| 评测口径 | 成功率、控制频率和硬件条件要和 vanilla OpenVLA 结果分开记录。 |

## FAST

FAST 是 OpenVLA 之后出现的一条 action tokenizer 改进方向。它针对 vanilla OpenVLA 的 256-bin 离散动作 token 路线，目标是把 action chunks 压缩成更少 token，降低自回归生成开销。

FAST 也是 OpenVLA 之后的外部扩展项目，但它改的不是 fine-tuning 配方，而是动作表示本身。vanilla OpenVLA 每个动作维度都要生成 token，动作维度越高，自回归步数越多；对照 FAST 时，OpenVLA 里有三个直接相关的位置：

1. 原始 `ActionTokenizer` 怎样把归一化动作变成 token。
2. `predict_action()` 的 `max_new_tokens` 怎样跟 action 维度相连。
3. 部署延迟中有多少来自动作 token 的逐步生成。

FAST 改的是动作表示和生成效率。对应的数据统计量、评测口径和真实机器人安全条件，仍然需要分别核对现有数据、评测和部署证据。

## 本页小结

- 官方仓库内的扩展，主要改训练入口、checkpoint 形态或推理加载方式；对应检查点仍然能落到 `train.py`、评测脚本和部署链路。
- Full fine-tuning 与 training from scratch 都进入 Prismatic 训练路径，但前者从现成 OpenVLA checkpoint 继续训练，后者同时改 base VLM、data mixture 和训练配置。
- Quantized inference 改的是部署侧推理成本与时延特征，动作链路仍然要通过 `predict_action()`、延迟统计和 rollout 记录分别验证。
- OFT 和 FAST 属于 OpenVLA 之后的外部扩展项目，前者改 fine-tuning 配方与连续动作路线，后者改更紧凑的 action token 表示。

## 导航

- 上一节：[延迟与控制频率](07-deployment/03-latency-and-control-frequency.md)
- 返回上级：[OpenVLA](../04-openvla.md)
