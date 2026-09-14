# LIBERO 端到端实战

目标：以 LIBERO 为主线，完整走通 StarVLA 的数据准备、训练、部署、评测和实验记录。

LIBERO 是基于 Franka 机械臂的桌面操作 benchmark，共 4 个 suite：

| Suite | 测什么 |
|---|---|
| Spatial | 空间关系理解 |
| Object | 物体识别和操作 |
| Goal | 目标条件推理 |
| Long Horizon | 长序列操作 |

StarVLA 使用同一个训练框架覆盖多个 suite，通过切换 `data_mix` 和 `framework.name` 比较不同动作头在相同数据上的表现。

前面章节已经分别讲了数据系统、模型框架、训练机制和部署服务。本章把这些内容组织成一次可复现的实验链路：从 LIBERO 数据开始，到对比 OFT、PI、WM4A 三条路线的评测结果。

## 本章目标

本章回答这几个问题：

1. LIBERO 数据和模型怎么准备？
2. 训练命令怎样写成可复现的实验记录？
3. policy server 和 LIBERO client 如何配合评测？
4. OFT、PI、WM4A 三条路线的训练现象和评测结果有什么区别？
5. 怎样从 loss 曲线和失败视频定位问题？

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [01 数据准备](07-libero-end-to-end/01-data-prep.md) | 数据怎么下载、目录怎么组织 | LeRobot 子集、modality.json、DataConfig、模型下载 |
| [02 训练](07-libero-end-to-end/02-training.md) | 训练命令怎么写、loss 怎么看 | YAML、命令行覆盖、WandB、checkpoint |
| [03 部署与评测](07-libero-end-to-end/03-deployment-eval.md) | 如何用两个终端评测 | server、LIBERO client、结果解读、失败排查 |
| [04 Qwen-OFT 实战](07-libero-end-to-end/04-qwen-oft.md) | OFT 训练和评测的完整记录 | MLP 连续回归、训练曲线、最小 baseline |
| [05 Qwen-PI 实战](07-libero-end-to-end/05-qwen-pi.md) | PI 训练和评测的完整记录 | flow matching、多层 hidden states、显存 |
| [06 WM4A 实战](07-libero-end-to-end/06-wm4a.md) | WM4A 训练和评测的完整记录 | world model backbone、长期训练、闭环成功率 |

## 三条路线对比

| 实战页 | framework 配置名 | 动作输出方式 | 重点观察 |
|---|---|---|---|
| Qwen-OFT | `QwenOFT` | VLM hidden state + MLP 回归连续动作 | 最小 baseline，先跑通链路 |
| Qwen-PI | `QwenPI` | 多层 VLM 表征条件下的 flow matching | 更重的计算，看采样稳定性 |
| WM4A | `CosmoPredict2GR00T` | world model backbone + flow matching | 替换 backbone，看闭环成功率 |

建议先跑 Qwen-OFT，确认链路，再跑 Qwen-PI，最后跑 WM4A。

## 共用路径变量

本章统一使用下面这些占位变量：

```bash
export STARVLA_DIR=<STARVLA_ROOT>
export LIBERO_HOME=<LIBERO_ROOT>
export LIBERO_DATA_ROOT=<DATA_ROOT>/LEROBOT_LIBERO_DATA
export RUN_ROOT_DIR=<RUN_DIR>
export PORT=10093
```

部署时，checkpoint 所在的运行目录必须保留完整结构：

```text
<RUN_DIR>/<run_id>/
├── checkpoints/
│   └── steps_*_pytorch_model.pt
├── config.yaml
├── config.full.yaml
└── dataset_statistics.json
```

不要只保留 `.pt` 权重文件。

## 导航

- 上一节：[部署与推理服务](06-deployment.md)
- 返回上级：[StarVLA](../05-starvla.md)
- 下一节：[01 数据准备](07-libero-end-to-end/01-data-prep.md)
