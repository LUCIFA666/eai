# TinyVLA 是什么

TinyVLA 属于小型 VLA 这条压缩路线：不压缩一个已有的大模型，而是在设计上就选小骨干，再配一个轻量的动作生成模块。它的骨干是十亿参数级以下的 Llava-Pythia，动作端是一个 diffusion policy 头。同一条路线上，SmolVLA 是紧凑预训练 VLM 加 flow matching action expert，TinyVLA 换成 Llava-Pythia 加 diffusion policy 头，两者都在设计上采用小骨干。

## 本节目标

理解 TinyVLA 在小型 VLA 里的定位、它针对的两处延迟根源、免机器人预训练加 LoRA 的训练取舍，以及相对 OpenVLA 的加速量级。

## 延迟来自哪两处

TinyVLA 把此前 VLA（RT-2、OpenVLA）的高推理延迟归到两个根源，也据此定下两处改动：

- 骨干规模大。RT-2、OpenVLA 建在 7B 级甚至更大的 VLM 上，单次前向的计算量本身就大。TinyVLA 换成 70M 到 1.4B 的 Llava-Pythia 骨干。
- 动作按 token 逐维自回归。OpenVLA 把连续动作离散成 token，再像生成语言一样一个自由度一个自由度地解码，每一维都要一次前向。TinyVLA 换成 diffusion policy 头，一次并行输出整段连续动作块，不再逐 token 解码。

这两处分别对应骨干规模和动作生成方式，[降低推理延迟](03-fast-inference.md)会给出各自贡献了多少延迟差。

## 免机器人预训练，靠 LoRA 微调

OpenVLA 依赖 OpenX 的约 970K 条机器人轨迹做大规模预训练。TinyVLA 跳过这一步，Llava-Pythia 只按 LLaVA 流程做视觉-语言预训练，之后直接在目标任务数据上微调（真机每任务约 100 条轨迹）。微调时用 LoRA 只更新注意力的低秩增量，可训练参数约占 transformer 的 5%，其余权重冻结；diffusion 头则全参数训练。骨干冻结保留了 VLM 在预训练中学到的知识，这也是 TinyVLA 泛化能力的来源。

免预训练还带来一处 OpenVLA 无法覆盖的场景：OpenX 只含单臂数据，OpenVLA 迁到双臂任务上三项成功率均为 0；TinyVLA-H 不依赖这份预训练，在同样的双臂任务上仍能完成（论文报告）。

## 加速的整体量级

单动作推理延迟从 OpenVLA-7B 的 292ms 降到 TinyVLA-1B 的 14ms，约 20 倍（单卡 A6000，论文报告）。参数上，TinyVLA-H 为 1.3B 总参、143M 可训练，OpenVLA 为 7.2B 总参、195M 可训练，总参少约 5.5 倍。精度并未因骨干变小而落后：Franka 五个真机任务上，TinyVLA-H 平均成功率 94.0，OpenVLA 68.3（论文报告）。

Franka 五任务的完整对比如下（论文报告）：

| 模型 | 机器人预训练 | 总参 | 可训练参数 | 五任务平均成功率 |
| --- | --- | --- | --- | --- |
| Diffusion Policy | 无 | 111M | 111M | 35.3 |
| OpenVLA | 970K OpenX | 7.2B | 195M | 68.3 |
| TinyVLA-S | 无 | 422M | 101M | 23.3 |
| TinyVLA-B | 无 | 740M | 138M | 77.4 |
| TinyVLA-H | 无 | 1.3B | 143M | 94.0 |

免机器人预训练、总参少约 5.5 倍，TinyVLA-H 仍高出 OpenVLA 25.7 个百分点；三档 S、B、H 成功率依次上升，即规模律。

代价也在这条规模律上：骨干越小成功率越低。TinyVLA-S 仅 23.3，甚至低于同样免预训练的 Diffusion Policy；0.4B 档会因语言理解不足而误解指令，到 1.3B 才稳定，复杂任务对骨干规模仍有依赖。

## 本页小结

- TinyVLA 是小型 VLA 路线的方法：从设计上选十亿参数级以下的 Llava-Pythia 骨干，配一个 diffusion policy 动作头。
- 它从两处延迟根源着手：把 7B 级骨干缩小，把逐维自回归的动作 token 解码换成 diffusion 头一次并行生成动作块。
- 训练上跳过 OpenX 大规模机器人预训练，用 LoRA 在目标任务数据上微调，可训练参数约占 5%，骨干冻结以保留预训练知识。
- 单动作延迟 292ms 降到 14ms（约 20 倍，单卡 A6000），参数少约 5.5 倍，Franka 五任务成功率 94.0 对 68.3（论文报告）；代价是小骨干容量有限，复杂任务依赖骨干规模。

## 导航

- 返回上级：[TinyVLA](../02-tinyvla.md)
- 下一节：[整体架构](02-architecture.md)
