# 少步推理

蒸馏出的学生在推理时可以用速度换精度，不必重新训练。最快的是单步：一次前向从噪声得到动作。需要更高精度时，把输出重新加噪、再去噪，链式多做两步。本页交代这两条推理路径的写法与取舍、部署时的调用链，以及少步生成带来的收益与代价。

## 单步推理

单步采一个初始噪声 `z`，计算 `x = g_θ(z, T, 0; o)`，把 `x` 作为动作发给机器人。`T` 是训练时的最大时间，`o` 是当前观测。

采样这一步有一个不显眼但重要的选择：初始噪声取自低方差高斯 `N(0, I)`，而非 EDM 标准的 `N(0, T²I)`。`consistency_policy/diffusion.py` 的 `sample_inital_position()` 直接返回 `randn`、不乘 `time_max`，正是这个低方差采样：

```python
traj = torch.randn(size=trajectory.shape, dtype=trajectory.dtype,
                   device=trajectory.device, generator=generator)
return traj  ## * self.time_max ## Reducing Initial Variance by not multiplying by time_max
```

被注释掉的 `* self.time_max` 就是低方差的来处：标准 EDM 采样会乘上 `time_max` 得到 `N(0, T²I)`，这里省去。让起点更接近分布中心，能使轨迹更贴近训练分布覆盖的区域、减少离群。论文报告的对照中，低方差相对高方差在 Robomimic Square 上把单步成功率从 0.90 提到 0.92，三步从 0.91 提到 0.96，对多步的增益更明显。

单步的调用集中在 `ctm_policy.py` 的 `conditional_sample()`：先取初始噪声，令 `t=time_max`、`s=time_min`，调一次前向得到动作预测；`self.chain` 为 `False` 时直接返回，全过程只有这一次学生前向。

```python
t = torch.tensor([self.noise_scheduler.time_max], device=condition_data.device)   # T
s = torch.tensor([self.noise_scheduler.time_min], device=condition_data.device)   # 0
out = self._forward(self.model, trajectory, t, s, clamp=True)   # 一次学生前向
if self.chain == False:
    return out                                                  # 单步到此结束
```

## 三步链式细化

需要更高精度时，把单步输出再链上两步。给定链接时刻 `{t_1, t_2}`，先照常从 `T` 去噪到 0，再加噪到 `t_1`、去噪回 0，对 `t_2` 重复一次。这一加噪再去噪的来回，相当于对初始预测反复细化。三步推理仍比 DDiM、DDPM 快得多。

链接时刻的选择有明确依据。扩散过程的不同时间段负责不同粒度：最早的时段只调整不易察觉的细节，最晚的时段决定大致轮廓，早中时段贡献了大部分重要特征。Consistency Policy 因此把链接时刻放在早中段，并且在离散化后的时间格点上均分，而非在连续时间上均分。它的离散调度本就在时间起点附近分布了更多格点，早中段因此对应更靠前的格点。对 80 个 bin 的三步生成，链接落在约 `N/3` 与 `2N/3` 处，对应 `ctmp_square.yaml` 里的 `chaining_times: ['D', 27, 54]`：首项 `'D'` 表示按离散时间取点，后两个是链接的 bin。论文报告的对照中，离散均分相对连续均分在难任务 Tool Hang 上把成功率从 0.72 提到 0.77，在 Square 上是 0.96 对 0.94。

多步路径在 `conditional_sample()` 里紧接单步之后：`self.chain` 为真时遍历后续链接时刻，每个时刻先把上一步输出加噪到该时刻，再去噪回 `time_min`。`chain` 默认关闭，需调 `enable_chaining()` 显式打开。

```python
for t in self.chaining_times[1:]:            # 后续链接时刻，如 27、54
    t = torch.tensor([float(t)], device=condition_data.device)
    if self.chaining_times[0] == "C":        # 'C' 按连续时间，'D' 按离散 bin
        t = self.noise_scheduler.timesteps_to_times(t)
    s = torch.tensor([self.noise_scheduler.time_min], device=condition_data.device)
    trajectory = self.noise_scheduler.add_noise(out, t)            # 上一步输出加噪到 t
    out = self._forward(self.model, trajectory, t, s, clamp=True)  # 再去噪回 0
return out
```

首项 `'D'` 表示按离散 bin 取点，`chaining_times[1:]` 即链接的 bin（27、54）。

## 单步与三步的取舍

步数不是越多越好。论文报告中，简单任务 Robomimic Can 上单步 0.98 反而略高于三步 0.95：首步已经足够准确时，额外的链接步改进空间有限，偶尔还会略微降低成功率。难任务 Tool Hang 上三步 0.77 明显高于单步 0.70；长时程的 Franka Kitchen 后段子任务单步会退化，需要三步才能恢复精度。是否链式，取决于任务对精度和延迟的相对要求。

## 部署调用链

部署从 `utils.py` 的 `get_policy()` 开始：读入 checkpoint，默认加载训练时的配置、打开推理模式、关闭在线 rollout，返回一个可直接推理的策略。外层套一个 `policy_wrapper.py` 的 `PolicyWrapper` 处理动作与观测的分块：`ObsChunker` 累积满 2 帧观测，`ActionChunker` 缓存一段动作、按控制步逐个输出。一次推理由 `get_action()` 触发，进入学生的 `predict_action()`：归一化观测、经图像编码器得到条件、调 `conditional_sample()` 生成整段动作、反归一化，再切出 8 步交给机器人。需要三步推理时，`PolicyWrapper` 也提供 `enable_chaining()` 打开链式路径。

## 收益与代价

收益直接：动作生成的去噪步数从 DDiM 的约 15、DDPM 的约 100 降到 1 或 3，延迟随步数近似成比例下降。端到端提速受视觉编码等固定开销限制，论文报告在 3070 Ti 上约为九倍。按各段拆分（3070 Ti，论文报告），15 步 DDiM 的图像编码约 6 ms、去噪网络约 179 ms、合计约 192 ms；Consistency Policy 图像编码同为约 6 ms、网络降到约 13.5 ms、合计约 21 ms。去噪网络本身快约 13 倍，端到端因固定的编码开销收敛到约 9 倍。真实机器人上，Consistency Policy 与 15 步 DDiM 在垃圾清理、插头插接任务上成功率相当（论文报告 0.8 对 0.8、0.7 对 0.6），单次推理从约 190 ms 降到约 20 ms。

代价有三方面。一是要先有一个多步教师，蒸馏是额外一轮训练，且学生比 Diffusion Policy 需要更多 epoch 才能达到相当的成功率，每步训练还要多算一次教师，整体训练时间更长。二是多样性受损：DDPM 的多模态来自其随机微分方程，而 EDM 与 CTM 学的是确定性 ODE，教师和学生都会损失一部分多模态，例如在 Push-T 上偏向一侧；论文报告这一点在常规评测任务上没有明显降低成功率。三是训练稳定性略低于 Diffusion Policy，源于一致性目标的自引用性质。是否接受这些代价，取决于任务对动作生成速度的要求，以及能否容忍多样性上的细微变化。

## 本页小结

- 单步一次前向得到动作，初始噪声用低方差高斯而非 EDM 标准方差，论文报告在 Square 上把单步 0.90 提到 0.92、三步 0.91 提到 0.96。
- 三步在离散格点的早中段（80 bin 取 27、54）加噪再去噪细化，难任务上离散均分优于连续均分；步数并非越多越好，简单任务单步可能反超三步。
- 去噪网络提速约 13 倍，端到端因固定的图像编码开销约为 9 倍（3070 Ti，论文报告）；代价是额外的蒸馏训练、多模态丢失和略低的训练稳定性。

## 导航

- 上一节：[一致性蒸馏](03-consistency-distillation.md)
- 返回上级：[Consistency Policy](../02-consistency-policy.md)
- 下一节：[FAST](../03-fast.md)
