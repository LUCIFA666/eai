# 安装与链路验证

目标：准备 StarVLA 环境，确认模型和数据入口能跑通。

StarVLA 上手时可以分成两类环境：一类负责加载模型和训练，另一类负责运行 benchmark 仿真。把这两类环境分开理解，能减少依赖冲突带来的困扰。

## 本节目标

本节围绕下面几个问题展开：

1. StarVLA 环境需要哪些基础依赖？
2. 怎样确认 framework、dataloader 和训练循环能运行？

## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [01 环境安装](02-setup/01-install.md) | 怎么创建 StarVLA Python 环境 | conda、PyTorch、requirements、editable install |
| [02 链路验证](02-setup/02-link-validation.md) | 如何确认模型和数据入口能运行 | import 检查、framework 检查、dataloader 检查、10 step 训练、server 启动 |

## 两类环境

| 环境 | 负责什么 | 典型命令 |
|---|---|---|
| StarVLA 环境 | 训练模型、启动推理服务 | `python starVLA/training/train_starvla.py` |
| Benchmark 环境 | 运行 LIBERO 等仿真环境 | `python examples/LIBERO/eval_files/eval_libero.py` |

训练通常只需要 StarVLA 环境。评测时常常需要两个终端：一个终端启动 StarVLA 推理服务，另一个终端运行 benchmark 环境。

## 导航

- 上一节：[认识 StarVLA](01-overview.md)
- 返回上级：[StarVLA](../05-starvla.md)
- 下一节：[01 环境安装](02-setup/01-install.md)
