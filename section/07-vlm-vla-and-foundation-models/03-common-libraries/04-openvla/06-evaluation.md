# 评测

目标：理解 OpenVLA 的 rollout 评测入口、Bridge WidowX 真机评测链路，以及训练结果和评测结果怎样分开记录。

LoRA 微调页记录的是训练侧结果：loss、`action_accuracy`、`l1_loss` 和 checkpoint 保存。评测页关注闭环执行：模型每一步根据当前图像和任务指令输出 action，环境执行后产生下一帧，再继续查询模型。成功率来自这一整条 rollout；单步 `predict_action` 和训练日志属于前置检查。

## 评测入口

| 页面 | 重点 |
| --- | --- |
| [LIBERO OpenVLA 评测](06-evaluation/01-libero-openvla-eval.md) | `run_libero_eval.py` 命令、`center_crop`、`unnorm_key`、gripper 处理和日志。 |
| [Bridge WidowX 评测入口](06-evaluation/02-bridge-widowx-eval.md) | BridgeData V2 真机评测的三段式启动方式和源码参数。 |
| [结果与失败记录](06-evaluation/03-results-and-failure-records.md) | 官方报告值、本地单种子结果、每任务成功率和失败观察。 |

## 评测结果的记录口径

评测结果需要分开记录不同来源和统计口径：

| 结果来源 | 能说明什么 |
| --- | --- |
| smoke eval | 模型加载、仿真渲染、`center_crop`、`unnorm_key`、日志和视频保存链路能跑通。 |
| full rollout | 在指定 seed、任务集和 episode 数下的闭环成功率。 |
| 官方报告值 | 论文或 README 给出的统计结果，通常有明确 seed 数、rollout 数和环境版本要求。 |

这些结果来源需要分开记录。一次 smoke eval 说明链路可以运行；策略表现要看 full rollout。单个 seed 的本地成功率可以用来对照同环境下的 checkpoint 差异，官方多 seed 平均值则用于报告级比较。

## 本页小结

- LIBERO 评测能给出仿真闭环成功率，是 LoRA checkpoint 进入任务验证的第一站。
- Bridge WidowX 评测接近真实机器人使用，但需要硬件、相机、Docker controller 和安全条件。
- 结果页要把训练曲线、smoke eval、单种子 rollout 和官方多种子结果分开记录。

## 导航

- 上一节：[LoRA 微调](05-finetuning.md)
- 返回上级：[OpenVLA](../04-openvla.md)
- 下一节：[LIBERO OpenVLA 评测](06-evaluation/01-libero-openvla-eval.md)
