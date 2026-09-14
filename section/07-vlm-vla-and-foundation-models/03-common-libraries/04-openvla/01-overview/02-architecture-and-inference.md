# 架构与推理主线

目标：把 OpenVLA 的输入、模型主体、动作输出和验证边界连成一条清晰主线。

下面这张图是 OpenVLA 的模型结构图。图像观测和语言指令从这里进入同一条推理主线：图像经过融合 DINOv2 和 SigLIP 的视觉编码器，视觉特征通过 projector 接到 LLM 上下文，模型生成 action tokens，最后还原成连续机器人动作。

![OpenVLA model](../assets/openvla_model.jpg)

## 输入：图像和语言指令

OpenVLA 的最小推理输入包括两部分：当前图像观测和任务指令。图像侧提供当前环境状态，语言侧提供任务目标；两者一起决定模型这一时刻要预测什么动作。常见 prompt 形如 `In: What action should the robot take to ...?\nOut:`，省略号位置放具体任务。

OpenVLA 的最小推理路径使用单张图像和一条文字指令，不包含多帧历史，也不把额外状态作为这条最小输入接口的默认输入。不同 checkpoint 和不同运行路径对 prompt 格式、图像处理方式还有额外要求，这些要求会直接影响推理结果。

## 主体：Prismatic Backbone 到 Action Tokens

主线 checkpoint `openvla/openvla-7b` 使用 Prismatic backbone。图像侧由 DINOv2 + SigLIP 提供视觉特征，projector 把视觉特征接到 Llama 2 的输入空间，语言指令也进入同一个上下文。

OpenVLA 的模型主体由视觉编码器、projector 和 Llama 2 7B 语言模型主干组成。视觉编码器先把输入图像映射成一组 image patch embeddings。projector 再把这些视觉特征映射到 language embedding space，让图像信息能够接入后续语言模型。最后，Llama 2 7B 主干在接入视觉特征和语言指令之后，继续沿用自回归生成接口输出 action tokens。Prismatic 采用 fused DINOv2 + SigLIP。这样做除了整合两路视觉特征，也利用了 DINOv2 在 spatial reasoning 上的优势，这对机器人控制很重要。

OpenVLA 把输出训练成 action tokens，从而直接复用 LLM 的生成接口：给定图像和指令后，模型生成一段 token 序列，这段序列在 OpenVLA 中被解释为机器人动作。

## 输出：Action Tokens 到 7D Action

OpenVLA 不直接回归连续动作，而是先把连续动作写成 LLM 可以生成的 action tokens。按论文的训练设定，每个动作维度会先离散到 256 个 bins，再交给语言模型按 next-token prediction 的方式预测；训练时计算损失的重点也是这些 predicted action tokens，而不是额外再接一个连续动作 head。

推理时，`predict_action` 承担最后的转换工作：它让模型生成 action tokens，再把这些 tokens 解码成归一化动作。随后，`unnorm_key` 指向的统计量会把归一化动作恢复到对应数据集的动作尺度。

在默认 checkpoint 和常见评测路径里，返回值通常表现为 7 维 end-effector action；但动作维度最终仍由 `unnorm_key` 选中的统计量决定。看到 shape 正常，只能说明模型加载、processor、prompt、action token decode 和反归一化这几步能连起来。动作是否能完成任务，还要放进仿真或真实机器人环境里验证。

## 验证边界

在本章的单步推理、评测和部署语境里，有三类证据比较容易混在一起：

| 证据 | 能说明什么 |
| --- | --- |
| `predict_action` 返回 7D action | 单步调用链路能跑通。 |
| LIBERO / Bridge rollout 成功率 | 策略在环境闭环中完成任务的比例。 |
| REST server 返回 action | 服务请求和响应链路正常。 |

这三类证据不能互相替代。单步推理正常时，统计量、图像分布、控制频率或环境接口仍然可能让 rollout 失败；server 能返回 action，也还没有证明真实机器人部署完成。

## 本页小结

- OpenVLA 的输入是图像观测和语言指令。
- Prismatic backbone 提供视觉语言上下文，模型输出 action tokens。
- `predict_action` 把 action tokens 还原成连续动作，并依赖统计量恢复尺度。
- 单步推理、rollout 成功率和 server 连通属于不同证据。

## 导航

- 上一节：[OpenVLA 是什么](01-what-is-openvla.md)
- 返回上级：[认识 OpenVLA](../01-overview.md)
- 下一节：[代码地图](03-code-map.md)
