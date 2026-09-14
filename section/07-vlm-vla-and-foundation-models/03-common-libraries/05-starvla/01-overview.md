# 认识 StarVLA

目标：先从一个 VLA 任务出发，理解 StarVLA 为什么要把数据、模型、训练、部署和评测分开组织。

假设机器人要完成一句指令："把杯子放到盘子上"。一个 VLA 系统通常需要：从相机图像里看见桌面、杯子、盘子和机械臂；读懂语言指令，知道目标物体和目标位置；结合当前机械臂状态，预测接下来几步动作；把动作送回仿真环境或真实机器人执行。

StarVLA 把这条流程拆成几个清楚的部分。数据负责提供样本，framework 负责把样本送进模型，训练器负责优化参数，部署服务负责加载 checkpoint 并输出动作，benchmark 适配器负责把动作交给环境。


## 学习路径

| 页面 | 读完要能回答的问题 | 重点 |
|---|---|---|
| [01 StarVLA 是什么](01-overview/01-what-is-starvla.md) | StarVLA 的定位、接口和完整流程 | 两个核心接口、训练流程、推理流程、相邻框架 |
| [02 代码地图](01-overview/02-code-struct.md) | 常看的代码入口在哪里 | `starVLA/`、`examples/`、`deployment/` |
| [03 章节预览](01-overview/03-chap-review.md) | 后续章节怎样衔接 | 推荐顺序、任务路径 |

## 代码主线

StarVLA 仓库里有一个 `examples/` 目录，每个 benchmark（比如 LIBERO、SimplerEnv）都在里面放了训练配置、评测脚本和数据注册文件。所有实验从这里出发。

实验主流程为：

```text
examples/<bench>/train_files/*.yaml  <- 训练配置
  -> dataloader 读出样本字典
  -> framework.forward() 计算训练损失
  -> 保存 checkpoint 和结果统计
  -> framework.predict_action() 预测动作
  -> benchmark 环境执行动作
```

这里的 `framework` 可以先理解为"一套完整的 VLA 模型包装"。它内部可以是 Qwen + MLP 动作头，也可以是 Qwen + FAST 动作 token，还可以是 Qwen + flow matching 动作生成器。对外仍然保持相同的训练和推理入口。

![StarVLA dataflow](assets/starVLA_dataflow.png)

这张图展示了 StarVLA 的数据和模型如何连接。后面的章节会多次回到这条连接关系：读数据时看字段，读模型时看 `forward()` 和 `predict_action()`，读评测时看动作怎样送回环境。

## 导航

- 上一节：[StarVLA](../05-starvla.md)
- 返回上级：[StarVLA](../05-starvla.md)
- 下一节：[01 StarVLA 是什么](01-overview/01-what-is-starvla.md)
