# `step1_prepare_latent.py` 做了什么

目标：理解为什么 VPP 要先做 latent 预处理，以及这个脚本通常会产出什么。

## 它不是训练脚本

这个脚本的作用是把原始示教加工成项目真正能读的格式。常见输出包括：

1. 规范化后的视频文件
2. VAE 编码后的 latent `.pt`
3. 对应的 annotation JSON

## 为什么要提前保存 latent

原因很现实：

1. 第一阶段视频训练已经很吃算力
2. 如果每个 batch 都重新走一遍 VAE 编码，会明显变慢
3. 第二阶段真实机器人路线也常常优先读取 latent

所以在这类 VPP 项目里，`latent_videos` 更像正式训练输入，而不只是可选缓存。

## 这一步通常包含哪些子流程

常见流程可以概括成：

1. 读原始图像、状态、动作和文本
2. 对图像做 resize / crop / pad
3. 保存 mp4
4. 用 VAE 编码成 latent
5. 写 annotation JSON

## 为什么说它更接近模板，而不是通用 CLI

这类脚本里往往会有不少针对作者原始数据的默认假设，例如：

- 原始数据路径
- 相机键名
- 固定的采样步长
- 文本处理规则

这意味着如果你迁自己的机器人数据，较合理的预期不是“原样运行”，而是“按其处理逻辑改写为自定义版本”。

## 第一阶段和第二阶段都依赖它吗

在很多场景下，是的。

- 第一阶段直接依赖它产出的 `videos` 和 `latent_videos`
- 第二阶段至少会继续依赖同一套 episode、文本、状态和动作对应关系

## 小结

- `step1_prepare_latent.py` 本质上是数据标准化和压缩脚本。
- 它的关键价值在于统一视频、latent 和 annotation 的对应关系。
- 真正迁移自定义数据时，通常需要改它，而不是期待它原样适配。

## 导航

- 上一节：[数据 contract](01-data-contract.md)
- 返回上级：[数据组织与 latent 预处理](../03-data-and-latent-prep.md)
- 下一节：[`step2_prepare_json.py` 做了什么](03-step2-prepare-json.md)
