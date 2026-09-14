# 训练机制

目标：从一次最小训练命令出发，理解 StarVLA 怎样把 YAML、dataloader、framework、优化器和 checkpoint 串起来。

StarVLA 的训练入口接近普通 PyTorch 项目。它会读取 YAML 配置，创建数据加载器和 framework，计算 `action_loss`，反向传播，并定期保存 checkpoint。多卡训练、混合精度和 DeepSpeed 是在这条主线外层提供加速和显存优化。

## 本节目标

本节围绕下面几个问题展开：

1. YAML 和命令行覆盖项如何合并？
2. `train_starvla.py` 和 `train_starvla_cotrain.py` 该怎么选？
3. 一步训练里 `forward()`、loss 和 backward 怎样连接？
4. 学习率分组和模块冻结怎样设置？
5. checkpoint 保存哪些文件，部署为什么需要它们？

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [01 配置系统](05-training/01-config-system.md) | YAML 和 CLI 如何合并 | OmegaConf、dotlist、配置覆盖 |
| [02 训练入口](05-training/02-train-entrypoints.md) | 训练脚本怎么选 | VLA、VLA+VLM、VLM |
| [03 训练循环](05-training/03-training-loop.md) | 每一步训练发生了什么 | `forward()`、loss、backward、scheduler |
| [04 优化器与冻结](05-training/04-optimizer-freeze.md) | 如何设置不同学习率和冻结模块 | 参数组、冻结列表 |
| [05 checkpoint 与恢复](05-training/05-checkpoint-and-resume.md) | 保存目录里每个文件有什么用 | state dict、config、statistics |

## 训练主线

```text
读取 YAML
  -> 合并命令行覆盖项
  -> 创建 framework
  -> 创建 dataloader
  -> 创建 optimizer 和 scheduler
  -> batch 进入 framework.forward()
  -> 得到 action_loss
  -> backward + step
  -> 保存 checkpoint、config 和 statistics
```

## 导航

- 上一节：[模型框架](04-frameworks.md)
- 返回上级：[StarVLA](../05-starvla.md)
- 下一节：[01 配置系统](05-training/01-config-system.md)
