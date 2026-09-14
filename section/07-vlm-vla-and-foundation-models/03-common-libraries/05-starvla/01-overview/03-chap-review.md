# 章节预览

目标：知道后面每章在解决什么问题，并根据自己的目标选择阅读路线。

StarVLA 涉及的模块较多。笔者建议先按完整流程读一遍，再按照需求回到对应章节。

## 推荐顺序

第一次学习时，建议按下面顺序：

1. [安装与链路验证](../02-setup.md)：准备环境，做最小链路验证。
2. [数据系统](../03-data.md)：理解样本字段、`modality.json`、`DataConfig` 和归一化。
3. [模型框架](../04-frameworks.md)：看懂 `forward()`、`predict_action()` 和几类动作头。
4. [训练机制](../05-training.md)：从单卡小步训练进入 YAML、冻结、checkpoint。
5. [部署与推理服务](../06-deployment.md)：理解 checkpoint 怎样变成可评测策略。
6. [LIBERO 端到端实战](../07-libero-end-to-end.md)：完整走通数据、训练、评测闭环，对比 OFT、PI、WM4A。
7. [其他 Benchmark](../08-other-benchmarks.md)：SimplerEnv、RoboCasa、RoboTwin、BEHAVIOR 适配。
8. [扩展 StarVLA](../09-extension.md)：接自己的数据、机器人或模型时再看。

## 按任务选择路径

| 当前目标 | 推荐路径 |
|---|---|
| 只想跑通一次 LIBERO 评测 | 安装与链路验证 -> 部署与推理服务 -> LIBERO 端到端实战 |
| 想训练自己的 VLA | 安装与链路验证 -> 数据系统 -> 训练机制 |
| 想理解 OFT、FAST、PI、GR00T 的差异 | 模型框架 -> LIBERO 端到端实战 |
| 想接自己的机器人数据 | 数据系统 -> 扩展 StarVLA -> 部署与推理服务 |
| 想排查 checkpoint 加载失败 | 训练机制 -> 部署与推理服务 -> 速查表 |

## 贯穿全章的检查问题

读每个模块时，都可以问四个问题：

1. 这个模块接收什么输入？
2. 它输出什么结果？
3. 相关参数写在 YAML 还是 Python 文件里？
4. 换一个 benchmark 时，这里需要改吗？

这四个问题能帮助你区分通用逻辑和 benchmark 专属逻辑。

## 小结

- 入门路径以 LIBERO 为主线，覆盖数据、训练、部署和评测闭环。
- 模型细节放在理解主流程之后学习，会更容易消化。
- 扩展新数据或新模型前，先判断改动应该落在 `examples/` 还是 `starVLA/` 核心包。

## 动手练习

1. 运行 `find examples/LIBERO -maxdepth 2 -type f | sort`，把安装、训练、评测相关文件分别对应到本章后续页面。
2. 运行 `rg -n "QwenOFT|QwenFast|QwenPI|QwenGR00T" starVLA/model/framework/VLM4A examples/LIBERO/train_files/starvla_cotrain_libero.yaml`，记录一个 framework 的注册名、代码路径和动作头类型。
3. 运行 `rg -n "server_policy.py|eval_libero.py|lerobot_datasets.py|train_starvla.py" .`，确认本章四条主线在官方仓库中的入口文件。

## 导航

- 上一节：[02 代码结构](02-code-struct.md)
- 返回上级：[认识 StarVLA](../01-overview.md)
- 下一节：[安装与链路验证](../02-setup.md)
