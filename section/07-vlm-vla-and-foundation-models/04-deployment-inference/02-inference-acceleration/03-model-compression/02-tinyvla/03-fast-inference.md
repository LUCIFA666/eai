# 降低推理延迟

骨干缩小和动作头换成 diffusion 都直接作用在单次前向上：前者降低每次前向的规模，后者把逐维自回归的动作解码换成一次并行去噪。除这两处，少步 DDIM 扩散、动作分块与 LoRA 合并再从推理侧降低延迟。

## 本节目标

理解 TinyVLA 单动作延迟从 292ms 降到 14ms 由哪些改动构成，每处改动降低推理路径的哪一段、对应哪个源码入口、各自贡献多少延迟差。

## 延迟分解：两条杠杆各占多少

单动作预测延迟的对比如下（单卡 A6000，论文报告）：

| 模型 | 单动作延迟 |
| --- | --- |
| OpenVLA-7B | 292ms |
| OpenVLA 换成 1B 骨干 | 140ms |
| TinyVLA-1B | 14ms |

两条杠杆据此分开。第一条是骨干规模：把 OpenVLA 的 Prismatic-7B 换成 TinyVLA 同架构的 1B 骨干，延迟从 292ms 降到 140ms，约 2 倍。第二条是动作生成方式：同为 1B 骨干，OpenVLA 仍要 140ms，TinyVLA 只要 14ms，相差约 10 倍。缩小骨干只占两条杠杆里较小的一条，把动作 token 自回归换成 diffusion 头才是延迟差的主体。这约 10 倍来自动作生成方式，机制与源码见下一节。

## 骨干只前向一次，去噪在小 U-Net 上迭代

自回归为什么慢：OpenVLA 把连续动作离散成一串 token，像生成语言一样逐个解码，后一个 token 依赖前一个，无法并行；每生成一个 token 都要把整个骨干前向一次。一个动作要多次经过 7B 骨干，昂贵的骨干前向次数随动作 token 数增长。

TinyVLA 把骨干前向和动作生成拆开。骨干在 `forward()` 里只前向一次，产出末层特征 `hidden_states`，之后送入动作头：

```python
outputs = self.get_model()(...)        # VLM 骨干前向一次
hidden_states = outputs[0]             # 末层特征，作为动作头的条件
if self.head_type == 'droid_diffusion':
    action = self.forward_diffusion_head(actions, hidden_states, states, is_pad)
```

动作头内部的去噪循环不再涉及骨干。推理时它从高斯噪声出发，反复调用的是小 U-Net `self.embed_out`，`global_cond` 始终复用同一份 `hidden_states`：

```python
naction = torch.randn((B, Tp, action_dim)).cuda()      # 与动作块同形状的噪声
self.noise_scheduler.set_timesteps(self.num_inference_timesteps)   # =10
for k in self.noise_scheduler.timesteps:               # 只循环 10 步
    noise_pred = self.embed_out(naction, k, global_cond=hidden_states, states=states)  # 只前向 U-Net
    naction = self.noise_scheduler.step(noise_pred, k, naction).prev_sample
```

昂贵的骨干前向由此从 OpenVLA 的每个动作 token 一次，降到 TinyVLA 的每个动作块一次，循环里执行的只是参数量远小于骨干的 U-Net（`down_dims=[256, 512, 1024]`）。这就是同为 1B 骨干、OpenVLA 仍慢约 10 倍的来源。

## 少步 DDIM 扩散

骨干出循环之后，剩下的推理成本主要在去噪步数。扩散的每一步都要前向一次 U-Net，成本随步数近似线性，步数直接决定这一段的推理成本。TinyVLA 训练用 DDPM、`num_train_timesteps=100`，推理换成 DDIM 调度器、只做 `num_inference_timesteps=10` 步：

```python
self.noise_scheduler = DDIMScheduler(
    num_train_timesteps=100,
    beta_schedule='squaredcos_cap_v2',
    prediction_type='epsilon',
)
self.num_inference_timesteps = 10
```

DDIM 的采样是确定性的、非马尔可夫的，允许在训练所用步数的子集上去噪，因而能把 100 步减到 10 步，约减少一个数量级。每一步都在整段动作块上并行去噪，步数固定为 10，与动作维度和动作块长度无关；对照自回归解码，其骨干前向次数随自由度和块长增长。

## 动作分块与开环执行

diffusion 头一次预测 `chunk_size` 步动作块。执行时不必每个控制步都重新前向一次骨干，而是预测一块、开环执行其中若干步再回到骨干重新预测。评测代码里 `query_frequency = chunk_size / 2`，即执行约半块后重新预测。骨干前向本就每块一次，再分摊到多个控制步上，平均每个控制步的网络开销进一步下降，有效控制频率随之提高。

## LoRA 合并

微调用 LoRA 只更新注意力的低秩增量。若在推理时保留这些低秩分支，会多出一路矩阵乘。TinyVLA 在训练后把 LoRA 权重重参数化，合并回基座权重，推理时只有一套合并后的权重，低秩微调不带来额外的推理开销。

## 整体收益与代价

收益集中在延迟和显存：骨干变小降低显存占用；骨干前向从每 token 一次降到每块一次、少步 DDIM 把去噪减到 10 步、动作分块进一步分摊骨干前向，共同把单动作延迟降到 14ms，约为 7B OpenVLA 的二十分之一（论文报告）。代价在骨干容量：0.4B 档会因语言理解不足而误解指令，到 1.3B 才稳定，复杂任务的精度和泛化仍受骨干规模约束。延迟换来的余量，需要足够大的骨干来维持成功率。

## 本页小结

- 单动作延迟 292ms 降到 14ms 来自两条杠杆：缩骨干 7B 到 1B 约贡献 2 倍，diffusion 头替代逐维自回归动作 token 再贡献约 10 倍，是延迟差的主体（单卡 A6000，论文报告）。
- 那 10 倍的机制是把骨干前向移出去噪循环：`forward()` 里骨干只前向一次得到 `hidden_states`，`forward_diffusion_head` 的 10 步循环只反复计算小 U-Net `self.embed_out`；昂贵骨干前向从每 token 一次降到每块一次。
- 扩散推理换 DDIM 调度器，训练 100 步、推理只做 `num_inference_timesteps=10` 步，每步在整段动作块上并行去噪，步数与动作维度、块长无关。
- 动作分块加开环执行（`query_frequency = chunk_size / 2`）把每块一次的骨干前向再分摊到多个控制步，提高有效控制频率。
- LoRA 权重训练后合并回基座，推理期零额外开销；整体以延迟和显存换骨干容量，复杂任务依赖足够大的骨干维持成功率。

## 导航

- 上一节：[整体架构](02-architecture.md)
- 返回上级：[TinyVLA](../02-tinyvla.md)
