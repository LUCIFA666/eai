# 整体加速效果与评测

PD-VLA 相对基座 LLaVA-VLA 把执行频率提到 2.52×，这个提升拆成两部分：action chunking 靠减少推理次数抬高频率，并行解码把单次解码速度再提 1.28×。同样免训练的 FastV、SparseVLM 靠剪枝 token 加速，在 chunked VLA 上反而更慢。精度上 PD-VLA 没有因加速下滑，LIBERO 平均 94.7%，真机三个任务相对基座均有提升。

## 本节目标

理解 PD-VLA 的整体加速效果与评测：执行频率的提升如何拆分到 action chunking 与并行解码两个部件、与 token 剪枝路线相比为何更有效，以及 LIBERO 与真机上的成功率。

## 提速拆解（CALVIN 消融，论文报告）

| 方法 | 平均完成长度 | 平均速度（tok/s） | 频率（Hz） |
| --- | --- | --- | --- |
| LLaVA-VLA | 1.20 | 39.56 | 1.81 |
| 去掉 action chunking | 1.12 | 39.86 | 1.82 |
| 有 chunking、自回归解码 | 3.61 | 41.44 | 3.60 |
| PD-VLA | 3.54 | 52.84 | 4.56 |

两个部件的分工在这里看得清楚。action chunking 是精度杠杆：加上它，平均完成长度从 1.20 提到 3.61，频率也从 1.81 提到 3.60 Hz，靠的是一次多出几步、减少推理次数，但每次推理仍受自回归速度限制（41.44 tok/s）。并行解码是速度杠杆：在 chunking 基础上把平均速度从 41.44 提到 52.84 tok/s（1.28×），频率从 3.60 提到 4.56 Hz，完成长度 3.61 到 3.54 基本持平。两者合起来，执行频率相对基座 1.81 Hz 提到 4.56 Hz，即 2.52×。

## token 剪枝为什么在这里失效

同样免训练的 FastV、SparseVLM 是靠剪枝或合并 token 来加速的通用 VLM 方法，但在 chunked VLA 上并不奏效。CALVIN 上有 chunking、自回归解码的配置下，接 FastV 后速度反而降到 28.69 tok/s，因为对 token 做 mask 本身带来额外开销；接 SparseVLM 后速度 32.43 tok/s、成功率也下滑，剪枝、合并、回收的代价盖过了收益。相比之下 PD-VLA 在解码循环这一层加速，速度提到 52.84 tok/s、成功率基本持平。这组对比支撑一个判断：对 chunked VLA，改解码循环比剪枝 token 更有效。

## LIBERO 与真机结果（论文报告）

LIBERO 四套件上，PD-VLA 平均成功率 94.7%，其中最难的 LIBERO-Long 达 91.7%，两项均为当时最好，平均分略高于 π0（94.2%）、明显高于 π0-FAST（85.5%）。这一配置接的是 OpenVLA-OFT 式连续动作头。

真机在 Unitree Z1-Pro 六自由度机械臂加一自由度夹爪上评测三个任务，相对基座 LLaVA-VLA：push button 从 60% 提到 80%，lift block 从 40% 提到 70%，pour water 从 10% 提到 60%。提升最大的是 pour water 这类需要抓取可变形瓶体、实时微调的精细任务，更高的控制频率让动作能更连贯地随反馈调整。

PD-VLA 本身不增加训练成本：基座在 8 张 H100 上训 1 个 epoch（约 10 小时），并行解码是推理时的改动，不需要额外训练。

## 本页小结

- action chunking 是精度杠杆、并行解码是速度杠杆（1.28×），两者合起来执行频率相对基座 2.52×。
- FastV、SparseVLM 这类 token 剪枝在 chunked VLA 上反而更慢，说明对 chunked VLA 改解码循环比剪枝 token 更有效。
- LIBERO 平均 94.7%、LIBERO-Long 91.7%，均为当时最好；真机三任务均有提升，pour water 这类精细任务受益于更高的控制频率。
- 并行解码是推理时的改动，不增加训练成本（论文报告）。

## 导航

- 上一节：[Jacobi 并行解码](03-parallel-decoding.md)
- 返回上级：[PD-VLA](../05-pd-vla.md)
