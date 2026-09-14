# 安装与第一次跑通

目标：准备 VLA-Adapter 环境、LIBERO 数据、基础 VLM、官方 checkpoint，并用 Spatial smoke test 建立第一条可运行链路。

本单元的参考输出来自已经跑通对应检查的验证环境，用来说明输出形态和关键检查点。不同机器的 GPU 型号、日志顺序和部分依赖解析结果可能不同，阅读时优先看正文说明的判断条件。

## 学习路径

| 页面 | 重点 |
| --- | --- |
| [环境安装](02-setup/01-environment.md) | conda、PyTorch、FlashAttention、LIBERO 和评测依赖 |
| [LIBERO 数据](02-setup/02-libero-data.md) | RLDS 数据下载、放置、体检 |
| [基础 VLM 与 Prismatic 配置](02-setup/03-pretrained-backbone.md) | `--vlm_path`、`--config_file_path`、基础模型体检 |
| [Checkpoint 准备](02-setup/04-checkpoint-setup.md) | 官方 Pro checkpoint 下载、体检 |
| [官方 Checkpoint 链路检查](02-setup/05-checkpoint-smoke-test.md) | 最小 10 episodes 链路检查 |
| [路径与环境变量](02-setup/06-paths-and-env.md) | 路径约定、outputs、rollouts、PYTHONPATH、EGL |

## 导航

- 上一节：[学习路线图](01-overview/04-roadmap.md)
- 返回上级：[VLA-Adapter](../06-vla-adapter.md)
- 下一节：[环境安装](02-setup/01-environment.md)
