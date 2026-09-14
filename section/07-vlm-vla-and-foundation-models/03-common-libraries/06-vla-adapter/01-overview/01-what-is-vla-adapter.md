# VLA-Adapter 是什么

目标：理解 VLA-Adapter 如何把视觉语言表征连接到连续机器人动作策略。

VLA-Adapter 是一种面向 tiny-scale VLA 的 VL-to-action bridging 方法。它处理的问题很具体：VLM 可以从图像和语言指令中形成 multimodal latent features，机器人控制还需要连续动作、动作块和 proprio state。VLA-Adapter 在中间加入轻量 Policy，把这些 latent features 接到动作生成过程。

VLA-Adapter 默认使用 Prismatic VLM 作为视觉语言主干，在 Qwen2.5-0.5B 级别 backbone 上组织完整的 VLA 输入输出链路。本页关注它的基本定位：VLM latent features 如何经过 condition、Policy 和 action head，变成可执行的连续动作。

## 核心特点

VLA-Adapter 的特点主要体现在四个方面：

- 使用 tiny-scale backbone。默认的 Qwen2.5-0.5B 级 Prismatic VLM 降低了对大规模 VLM 和机器人数据预训练的依赖。
- 关注 condition 的选择。Raw latent、ActionQuery latent、single-layer features 和 all-layer features 会影响 Policy 接收到的信息。
- 用 Bridge Attention 连接动作分支。action latent 在这个模块中接收 Raw latent、ActionQuery latent 和 proprio embedding。
- 强调效率与可训练性。轻量 Policy、连续 action chunk 和 L1-based action head 让训练和推理成本更低，也便于围绕具体任务调整。

## VLM 特征、状态与动作块

VLA-Adapter 的 VL-to-action 链路需要把 VLM features、机器人状态和连续动作块放到同一个生成过程中。在一个时间步里，下面几类信息会一起进入这条链路：

- 图像输入：third-view image 和 gripper / wrist image 提供场景与末端视角。
- 语言输入：instruction 描述当前任务。
- ActionQuery：额外插入的 query token，用来聚合和传递与动作相关的 multimodal 信息。
- proprio state：机器人当前状态，后续通过 projector 映射到和 policy 相容的表示空间。
- action chunk：Policy 一次预测未来若干步连续动作。

这些信息共同决定 action policy 能看到什么、如何接收 condition，以及最终输出什么样的连续动作块。

## VLM features 如何进入 Policy

下面这张图可以先看作 VLA-Adapter 的整体结构：左侧是 VLM 与 Policy 的连接，右侧是四类 condition 的比较。

![VLA-Adapter model](../assets/model.png)

接下来按两条线读这张图。第一条线是 VLM 到 Policy 的连接：图像、instruction 和 ActionQuery 进入 Prismatic VLM 后，会产生 Raw latent 和 ActionQuery latent。这些 latent features 会作为 Policy 的 condition。

第二条线是 condition 的选择：VLA-Adapter 比较了不同层的 features，也比较了 Raw latent 和 ActionQuery latent。多层视觉语言信息能给动作策略提供更完整的上下文，ActionQuery latent 对动作生成尤其关键，Raw latent 也能为部分任务提供补充信息。

## Policy 负责生成动作

VLA-Adapter 的 Policy 接收 VLM condition 后输出连续动作块。该 Policy 的核心是 Bridge Attention：action latent 在每一层同时和 Raw latent、ActionQuery latent 以及自身进行 attention，proprio embedding 也会进入 condition 侧。这样动作分支就可以在预测连续动作时使用视觉、语言、ActionQuery 和状态信息。

VLA-Adapter 默认采用 L1-based Policy，用连续 action head 直接回归 action chunk。这样可以把动作预测放在一个较轻的回归分支里完成，减少额外生成步骤。

## Pro 版本的含义

VLA-Adapter-Pro 是 VLA-Adapter 的增强版本。它保留 VLA-Adapter 的基本连接方式，同时在 Policy 内部使用更细的投影设计，并加入 RoPE，让 attention 对动作序列中的位置信息更敏感。在代码里，Pro 版本会影响 action head 内部 block 的选择，也会影响 checkpoint 组件是否匹配。

## 能力边界

VLA-Adapter 的优势来自轻量连接层和 tiny-scale backbone。它的动作质量仍然依赖 VLM condition、训练数据、动作归一化统计和目标平台的输入输出维度。迁移到新 benchmark 或真实机器人时，需要重新核对图像数量、proprio 维度、action 维度、action chunk 长度和 statistics。

读到这里，可以先把 VLA-Adapter 看作一层连接机制：它把 VLM 里的视觉语言信息转成 Policy 可以使用的 condition。下一页会继续看架构图，把 VLM、Policy、Bridge Attention、proprio projector 和 action head 放到同一条组件链路里。

## 本页小结

- VLA-Adapter 是面向 tiny-scale VLA 的 VL-to-action bridging 方法。
- 它用轻量 Policy 和 Bridge Attention，把多层 VLM condition 接到连续动作生成。
- Raw latent、ActionQuery latent 和 proprio embedding 是理解 Policy 输入的关键线索。
- Pro 版本主要影响 Policy / action head 的内部结构。

## 导航

- 上一节：[认识 VLA-Adapter](../01-overview.md)
- 返回上级：[认识 VLA-Adapter](../01-overview.md)
- 下一节：[架构与组件](02-architecture-and-components.md)
