# 架构

Consistency Policy 涉及两个网络：一个多步教师和一个少步学生。两者都沿用 Diffusion Policy 的 1D 卷积 UNet 主干，在动作维度上去噪，用 FiLM 把观测和时间注入网络。差异在时间条件：教师是一个 EDM 模型，只接收当前时间；学生是一个一致性轨迹模型（CTM），额外接收一个停止时间 `s`，用来指定要还原到轨迹上的哪个位置。本页交代主干与条件、教师为什么必须给出确定性轨迹、学生多出的那一路条件，以及两者相对 Diffusion Policy 的结构差异。

## 主干与观测条件

主干是 Diffusion Policy 的条件式 1D 卷积 UNet：卷积沿动作序列的时间维展开，把一段带噪动作逐层去噪。视觉观测先经图像编码器得到特征，与本体状态、扩散时间一起作为条件，通过 FiLM 块调制 UNet 各层的激活。教师策略是 `teacher/edm_policy.py` 的 `KarrasUnetHybridImagePolicy`，学生策略是 `student/ctm_policy.py` 的 `CTMPPUnetHybridImagePolicy`，二者共用同一套 backbone 结构，`edm_square.yaml` 与 `ctmp_square.yaml` 里的 `down_dims` 都是 `[512, 1024, 2048]`、`diffusion_step_embed_dim` 都是 128。

## 教师：EDM 与确定性 ODE

教师采用 EDM 框架，而非 Diffusion Policy 原来的 DDPM。这一步替换决定了后续能否做蒸馏。DDPM 把去噪看成在反解一条随机微分方程，每步注入布朗噪声，同一个起点会得到不同轨迹，轨迹不唯一，无法作为蒸馏目标。EDM 与 DDiM 走另一条路，把去噪看成积分一条确定性的概率流 ODE，同一个起点沿同一条轨迹只会到同一个终点，并且允许训练时用多步、推理时改用更少步。一致性蒸馏要求轨迹确定，教师因此必须用 EDM。

教师网络 `s_φ(x_t, t; o)` 接收轨迹上的当前位置 `x_t`、时间 `t` 和观测 `o`，用来估计这条 ODE 的导数：

```
dx_t / dt = -(x_t - s_φ(x_t, t; o)) / t
```

有了每一点的导数，借助数值积分器就能沿轨迹从噪声积分到动作。教师的噪声调度、数值求解与训练目标（Karras 时间离散、Heun 二阶求解、pseudo-Huber 距离等）属于训练侧细节，与推理延迟无关，这里不展开；对架构而言，教师提供的就是一条可复用的确定性轨迹和一个能估计其导数的网络。

## 学生：CTM 与停止时间 s

学生要跨过中间的积分步。它的网络 `g_θ(x_t, t, s; o)` 在教师的输入之外多接收一个停止时间 `s`：给定轨迹上时间 `t` 处的位置 `x_t`，直接输出更早时间 `s` 处的位置 `x_s`。单步推理是这个函数在 `s=0` 的特例，一次前向从噪声得到动作。

多出的 `s` 反映在网络结构上，就是第二路时间嵌入。学生用的 `ctm_unet.py` 中 `CTMConditionalUnet1D` 同时接收 timestep 与 stoptime 两个时间，条件维度相应翻倍。这些为 `s` 新扩出的 FiLM 层零初始化，使它们在训练初期不干扰 warm-start 得到的教师权重。因为条件维度要对齐，教师和学生的 `diffusion_step_embed_dim` 必须一致，warm-start 时的权重扩展（`base_workspace.py`）才能把教师权重对上学生的结构。

## 输入输出

教师和学生的输入输出一致，沿用 Diffusion Policy 的设定：观测取 2 帧，动作维度 10（3 维位置、6 维旋转、1 维夹爪），一次生成 horizon 16 的动作序列，实际执行其中 8 步。视觉观测经图像编码器成为条件，动作序列在 UNet 的时间维上被去噪。

## 与 Diffusion Policy 的结构差异

同一套 1D 卷积 UNet 主干下，Consistency Policy 相对 Diffusion Policy 的结构改动集中在两处：教师把去噪框架从 DDPM 换成 EDM，使轨迹从随机变为确定；学生在时间条件上多接一路停止时间 `s`，从而能一次前向还原到轨迹上任意更早的位置。视觉编码器、FiLM 条件注入、UNet 去噪主体这些部分不变。

## 本页小结

- 教师与学生共用 Diffusion Policy 的 1D 卷积 UNet 主干和 FiLM 观测条件，差异在时间条件。
- 教师用 EDM 而非 DDPM，使去噪对应一条确定性 ODE 轨迹，这是蒸馏的前提；网络 `s_φ` 估计该 ODE 的导数。
- 学生多接一路停止时间 `s`（第二路时间嵌入，零初始化），一次前向就能还原到轨迹上更早的位置，`s=0` 即单步生成。

## 导航

- 上一节：[Consistency Policy 是什么](01-what-is-consistency-policy.md)
- 返回上级：[Consistency Policy](../02-consistency-policy.md)
- 下一节：[一致性蒸馏](03-consistency-distillation.md)
