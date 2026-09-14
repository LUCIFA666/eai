# 扩展 StarVLA

目标：学习如何把 StarVLA 用到自己的机器人、自己的数据集或自己的模型结构上。扩展时建议沿着接口边界逐步接入，避免一次修改太多文件。

官方“使用自己的 LeRobot 数据集”文档把流程分成五步：

```text
转换数据到 LeRobot 格式
  -> 创建 Robot Type Config
  -> 创建 Data Mix
  -> 创建训练配置
  -> 运行训练
```

本章在这个基础上补充代码边界和调试顺序。

## 本节目标

本节围绕下面几个问题展开：

1. 自己的数据集需要满足什么格式？
2. `modality.json`、`DataConfig`、`DATASET_NAMED_MIXTURES` 怎么写？
3. 新 framework 最小实现是什么？
4. 新 VLM 或 action head 应该接在哪里？
5. 扩展时如何验证接口是否跑通？

## 学习路径

| 端页 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [01 接入自有 LeRobot 数据](09-extension/01-custom-lerobot-dataset.md) | 自有数据如何进 StarVLA | LeRobot、modality、DataConfig、mixture |
| [02 新 framework](09-extension/02-new-framework.md) | 如何添加自己的模型结构 | `baseframework`、registry、接口验证 |
| [03 新 backbone 或 action head](09-extension/03-new-backbone-or-head.md) | 如何替换组件 | VLM wrapper、动作头组件、模块路径 |
| [04 扩展调试顺序](09-extension/04-extension-debug-order.md) | 如何逐步定位问题 | 数据、forward、训练、server、benchmark |

## 导航

- 上一节：[其他 Benchmark](08-other-benchmarks.md)
- 返回上级：[StarVLA](../05-starvla.md)
- 下一节：[01 接入自有 LeRobot 数据](09-extension/01-custom-lerobot-dataset.md)
