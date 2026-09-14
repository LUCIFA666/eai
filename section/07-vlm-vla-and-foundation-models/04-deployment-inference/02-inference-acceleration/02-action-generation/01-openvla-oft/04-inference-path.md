# 推理调用链

推理时所有动作生成步骤汇集在 `prismatic/extern/hf/modeling_prismatic.py` 的 `OpenVLAForActionPrediction.predict_action()`。它把输入准备、视觉编码、本体投影、单次前向和反归一化按顺序串起来：前三步向序列里填入视觉、本体和占位动作 token，第四步做主干前向并切出动作段，第五步把归一化动作还原成真实量纲。前面几节讲的并行解码收益落在第四步。

## 输入序列怎么拼出来

`predict_action()` 在做主干前向前，先把一条多模态序列拼齐。以 LIBERO 默认配置（单张图像、开启本体状态）为例，序列布局是：

```
[ 视觉 patch 256 | proprio 1 | prompt tokens | 占位动作 token 56 | stop 1 ]
```

前三步分别填这几段：

- `_process_vision_features()`（`modeling_prismatic.py:438-447`）过视觉 backbone 得到 patch embedding，再经 projector 接到主干输入空间。开启 FiLM 时，backbone 换成 `FiLMedPrismaticVisionBackbone`，额外接收从非动作位置抽出的 `language_embeddings`，用其序列均值调制每个 ViT block；调制不改变 patch 数，单图仍是 256 个 patch。FiLM 的结构见[架构](02-architecture.md)。
- `_process_proprio_features()`（`:449-459`）把本体状态投影到主干维度后 `unsqueeze` 成 1 个 token，拼在视觉 patch 末尾。这一个 token 就是开启 `use_proprio` 后 `NUM_PATCHES` 加一的来源。
- `_prepare_input_for_action_prediction()` 在序列尾部拼上 `ACTION_DIM * NUM_ACTIONS_CHUNK` 个占位动作 token（LIBERO 下为 56 个）和一个 `STOP_INDEX` token。占位 token 的清零和动作位置的双向注意力见[并行解码](03-parallel-decoding.md)。

## 单次前向与三条动作头分支

序列拼齐后，`predict_action()` 按有没有配 diffusion 头分派到两个函数：

```python
use_diffusion = noisy_action_projector is not None and hasattr(action_head, "noise_scheduler")
```

无 diffusion 走 `_regression_or_discrete_prediction()`，有 diffusion 走 `_run_diffusion_prediction()`。三条动作头分支从同一段动作 hidden states 出发，但读取内容和前向次数不同：

| 分支 | 入口函数 | 读取内容 | 主干前向次数 | 输出 |
| --- | --- | --- | --- | --- |
| 连续回归 | `_regression_or_discrete_prediction()` | 动作段 hidden states → L1 MLP 头 | 1 | 连续动作 |
| 离散 token | `_regression_or_discrete_prediction()` | 动作段 logits → argmax → 分箱中心 | 1 | 反量化后的连续动作 |
| diffusion | `_run_diffusion_prediction()` | 每步 hidden states → 噪声预测头 | N（去噪步数） | 连续动作 |

连续回归是 OFT 默认，读最后一层 hidden states 交给 L1 回归头，只做一次前向。离散 token 是原始 OpenVLA 的路径，改读动作位置的 logits 取 argmax，再按分箱中心反量化，同样只做一次前向、不经过独立回归头。diffusion 沿 `noise_scheduler.timesteps` 反向去噪，每一步先经 `_replace_input_embeddings()` 把投影后的噪声动作写回动作位置，再做一次主干前向，N 步即 N 次前向。三条路径的延迟对比见[架构](02-architecture.md)。

动作段的位置对三条路径一致：从 `NUM_PATCHES + NUM_PROMPT_TOKENS` 起切 `ACTION_DIM * NUM_ACTIONS_CHUNK` 宽（切片代码见[并行解码](03-parallel-decoding.md)）。这个偏移就是它前面所有 token 的总长：视觉 patch 加上可选的 proprio token，再加上 prompt token；diffusion 分支还会为时间步 token 让 `NUM_PATCHES` 再加一，切片起点随之后移。

## 反归一化还原量纲

动作头输出的是归一化到 [-1, 1] 的动作，`_unnormalize_actions()`（`:772-791`）把它还原成真实量纲。它按 `unnorm_key` 取数据集统计量，由 `ACTION_PROPRIO_NORMALIZATION_TYPE` 决定用哪套边界：`BOUNDS` 取 [min, max]，`BOUNDS_Q99` 取 [q01, q99]。还原公式 `0.5 * (a + 1) * (high - low) + low` 只作用在动作维度上，返回整段 chunk 的真实动作值。

## constants.py 决定链路上的所有形状

链路里反复出现的 `ACTION_DIM`、`NUM_ACTIONS_CHUNK`、`STOP_INDEX`、归一化类型都来自 `prismatic/vla/constants.py`。它在加载时从 `sys.argv` 匹配 `libero` / `aloha` / `bridge` 自动选平台（都不匹配则默认 LIBERO），绑定这一组常量：

| 平台 | NUM_ACTIONS_CHUNK | ACTION_DIM | PROPRIO_DIM | 归一化类型 |
| --- | --- | --- | --- | --- |
| LIBERO | 8 | 7 | 8 | BOUNDS_Q99 |
| ALOHA | 25 | 14 | 14 | BOUNDS |
| BRIDGE | 5 | 7 | 7 | BOUNDS_Q99 |

这组常量在链路各步被消费：`ACTION_DIM * NUM_ACTIONS_CHUNK` 是占位动作 token 数，也是动作段切片的宽度；`STOP_INDEX` 是尾部补的 stop token；归一化类型选 `_unnormalize_actions()` 的边界分支。换机器人或换数据集改的是 `constants.py` 这一处，训练拼占位 token、算 mask 和推理切 hidden states、reshape 进动作头共用同一套，一处改动同时贯穿两端，避免一套 chunk 训练、另一套推理导致动作错位。

## 本页小结

- `predict_action()` 先由视觉、proprio、占位动作三步拼出多模态序列，再做主干前向，最后反归一化，返回整段 chunk。
- 三条动作头分支从 `NUM_PATCHES + NUM_PROMPT_TOKENS` 起切同一段动作 hidden states：连续回归和离散 token 各做一次前向，diffusion 每去噪步一次前向。
- `constants.py` 按平台绑定 chunk 长度、动作维度和归一化类型，是链路上所有形状的单一来源，训练与推理共用。

## 导航

- 上一节：[并行解码](03-parallel-decoding.md)
- 返回上级：[OpenVLA-OFT](../01-openvla-oft.md)
- 下一节：[环境与数据准备](05-environment-and-data.md)
