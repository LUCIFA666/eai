# 架构与组件

目标：理解 VLA-Adapter 的 VLM、condition、Bridge Attention、proprio projector 和 action head 如何组成动作生成链路。

![The Policy with Bridge Attention](../assets/framework.png)

这张图是 VLA-Adapter 的 Policy with Bridge Attention，展示了 RGB、Instruction 和 ActionQuery 进入 VLM 后，condition 如何作为 `KV` 送入 Policy，并在 Bridge Attention、FFN、LN & MLP 之后生成 Action。

本页围绕这张架构图，梳理 VLM condition、Bridge Attention、proprio projector、action head 和关键配置之间的关系。

## 输入侧：VLM 提供 condition

VLA-Adapter 的输入侧由 Prismatic VLM 处理。以 LIBERO 设置为例，一个时间步通常包含 third-view image、wrist image、instruction 和 ActionQuery。图像经过 DINOv2 / SigLIP 视觉编码，instruction 经过 tokenizer，ActionQuery 作为额外 token 进入 VLM。

VLM 输出中有两类信息会进入 Policy：

- `Raw latent`：来自 VLM 中间或多层 hidden states，保留视觉语言融合后的表征。
- `ActionQuery latent`：由 ActionQuery token 聚合出的动作相关表征。

`Raw latent` 和 `ActionQuery latent` 是本教程对应源码 `h_t`（task tokens）和 `h_a`（adapter tokens）给出的命名，`prismatic/models/action_heads.py` 的类里查不到这两个名字。

这两类 latent 是 VLA-Adapter 的 condition。后续看到 `use_minivlm`、`num_images_in_input`、processor 或 backbone 配置时，可以把它们放回这一层理解：它们决定 VLM 能看到哪些图像、怎样处理 prompt，以及输出给 Policy 的 hidden states 是否符合预期。

## Policy 侧：Bridge Attention 连接 condition 和 action latent

Policy 会先构造 action latent，再通过 Bridge Attention 接收 VLM condition。Bridge Attention 包含三条注意力路径：

- Raw latent 经过一条 cross attention 注入 action latent，注入比例由可学习参数调节。
- ActionQuery latent 和 proprio embedding 进入另一条 cross attention，提供更直接的任务与状态条件。
- action latent 还会经过 self attention，保持动作块内部各步之间的关系。

在代码实现里，这部分对应 L1 action head 内部的 `MLPResNetBlock` / `MLPResNetBlock_Pro`。普通版本共享部分投影结构，Pro 版本拆分 self / adapter / task 的投影，并加入 RoPE。配置中的 `use_pro_version` 主要影响这里的 block 结构和 checkpoint 权重能否匹配。`MLPResNetBlock_Pro` 里还定义了 FiLM 生成器，但它在 forward 中被注释掉（`prismatic/models/action_heads.py:403-406`，源码注释写的是 FiLM is useless），因此 Pro block 实际参与计算的是拆分投影加 RoPE，FiLM 并未生效。

## 状态侧：proprio projector 进入 condition

VLA-Adapter 把 proprio state 当作动作策略的重要输入。proprio projector 会把机器人状态映射到 LLM hidden dimension，再和 ActionQuery latent 一起进入 Bridge Attention。

这解释了 `use_proprio` 为什么需要和 checkpoint 组件一起看：开启 proprio 后，模型侧需要 `proprio_projector`，输入侧需要 observation 里有对应 state，checkpoint 目录里也需要保存或提供 projector 权重。LIBERO 主线使用 8D proprio，ALOHA 使用 14D proprio，具体维度由 `prismatic/vla/constants.py` 根据平台选择。

## 输出侧：continuous action chunk

VLA-Adapter 主线使用 L1 regression action head 输出连续动作块。action head 一次预测多个未来动作，评测或部署端再按 open-loop 步数执行。

| 场景 | 图像输入 | action chunk / 动作维度 | 说明 |
| --- | --- | --- | --- |
| LIBERO train / eval | `num_images_in_input=2` | `NUM_ACTIONS_CHUNK=8`，`ACTION_DIM=7` | third-view 与 wrist 图像输入，评测通常按 8 步 action chunk 执行。 |
| ALOHA / policy server | `DeployConfig.num_images_in_input=3` | `NUM_ACTIONS_CHUNK=25`，`ACTION_DIM=14` | fake / real client 通常发送 front、left wrist、right wrist 三路图像。 |
| CALVIN | `evaluate_calvin.py` 默认 `num_images_in_input=2` | `NUM_ACTIONS_CHUNK=8`，`ACTION_DIM=7` | 评测入口在 `vla-scripts/evaluate_calvin.py`。 |

这些值需要放在同一条输入输出链路里核对。图像数量会影响 processor 和 vision backbone 的输入；action chunk 与 action dimension 会影响 action head 输出形状；proprio dimension 会影响 projector 输入；statistics 决定动作反归一化时使用哪组范围。

## checkpoint 组件如何对应架构

VLA-Adapter 的 checkpoint 通常不只是一个 backbone 目录。评测和部署还会加载 action head、proprio projector 和 `dataset_statistics.json`。从架构角度看，可以把它们对应到下面几层：

| 组件 | 对应架构层 | 典型文件或配置 |
| --- | --- | --- |
| Prismatic VLM / processor | VLM 输入和 hidden states | `pretrained_checkpoint`、`vlm_path`、`config_file_path` |
| action head | Policy 与 action chunk 输出 | `action_head--checkpoint.pt`、`use_l1_regression`、`use_pro_version` |
| proprio projector | proprio state 到 hidden dimension | `proprio_projector--checkpoint.pt`、`use_proprio` |
| statistics | action / proprio normalization | `dataset_statistics.json`、`unnorm_key` |

这张表也可以帮助我们区分不同问题的来源：checkpoint 加载问题通常对应某一层组件缺失；动作尺度异常则通常需要核对 statistics、`unnorm_key` 和 platform constants 是否匹配。

## 本页小结

- VLA-Adapter 的结构可以按 VLM condition、Bridge Attention、proprio projector、continuous action head 四层理解。
- Raw latent 和 ActionQuery latent 是 Policy 的主要 condition，proprio embedding 会进入 ActionQuery 侧的 attention 路径。
- `use_proprio`、`use_pro_version`、`num_images_in_input`、`ACTION_DIM` 和 `NUM_ACTIONS_CHUNK` 分别影响输入、组件结构和动作输出。
- LIBERO eval 和 policy server 复用部分模型组件，但图像数量、动作维度和 open-loop 步数需要按各自入口核对。

## 导航

- 上一节：[VLA-Adapter 是什么](01-what-is-vla-adapter.md)
- 返回上级：[认识 VLA-Adapter](../01-overview.md)
- 下一节：[代码地图](03-code-map.md)
