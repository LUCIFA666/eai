# RDT 理论基础

## 本节目标

- 能画出 RDT 从语言指令、多视角图像、机器人本体状态到未来动作 chunk 的数据流，说清每个环节的输入输出维度。
- 能解释统一动作空间（128 维 physically interpretable state vector）、T5-XXL / SigLIP 双编码器、Diffusion Transformer 主干和 DDPM / DPM-Solver 采样各自的作用。
- 能说清语言和图像条件为什么通过 cross-attention 注入主干而不进入 token 序列，以及为什么要交替注入。
- 能解释 `prediction_type=sample`（预测干净动作）和预测噪声 `epsilon` 的工程差别，以及 `ctrl_freqs` 为什么需要显式编码进主干。

## 解决什么问题

RDT（Robotics Diffusion Transformer）要解决的问题，和 Octo 是一致的：真实数据来自不同实验室、不同本体——单臂和双臂、关节控制和末端控制、位置控制和速度控制，甚至带轮式底盘的移动操作。不同数据集的动作维度、物理含义、控制频率都不一样。每次针对性训练很麻烦，因此要有不只绑死在一台机器人上的策略。

但是 RDT 的解决方案比 Octo 更加全备。统一动作空间方面：把所有这些异构动作塞进一个**统一的 128 维动作向量**：每一维都对应一个固定的物理量（右臂第 0 个关节角、右夹爪开合、末端位置 x……），某个机器人没有的维度就留空并用 mask 标记。这样一来，1M+ 个多机器人 episode 就能喂进同一个模型，而不必为每种本体单独设计动作头。动作生成方面：做成**扩散模型**：主干是一个 1B 级参数的 Diffusion Transformer，给定语言和图像条件，从噪声里采样生成未来 64 步动作。

回顾前两节。RT-1 把连续动作离散成 token 做分类；Octo 用 Transformer 主干接一个 diffusion action head，动作头本身较小；RDT 则把整个主干都做成 Diffusion Transformer，并且能兼容几乎所有现代操作臂。由此我们可以清晰地看到整个技术路线的发展历程。

## 输入和输出规格

从部署接口看，RDT 一次推理需要三类输入，产出一段未来动作：

| 对象 | 典型内容 | 作用 |
|---|---|---|
| 语言条件 | T5-XXL 编码后的指令 embedding，形状 `(1, L, 4096)` | 本次任务条件 |
| 图像条件 | 最近 2 帧 × 最多 3 个相机视角，经 SigLIP 编码 | 当前观测 |
| 本体状态 | 当前 proprio，填进 128 维状态向量 | 机器人当前关节 / 末端状态 |
| 输出动作 | `(1, 64, 128)` 的动作 chunk，按 mask 取回有效维度 | 未来 64 步动作，128维 |

几个关键超参来自 `configs/base.yaml`：`action_chunk_size=64`（一次预测 64 步）、`num_cameras=3`、`img_history_size=2`、`state_dim=128`、语言 token 维度 `lang_token_dim=4096`（T5-XXL 输出维度）、图像 token 维度 `img_token_dim=1152`（SigLIP 输出维度）。

一次预测 64 步是 RDT 的一个特点：它给出的是较长的 action chunk。部署时既可以执行整段，也可以只执行前几步再重新采样（滚动时域控制 receding horizon control）。ManiSkill 评测脚本里就用了后者的变体：预测一整段 64 步后做下采样（`actions[::4]`，每隔 4 步取一个），每次只执行其中一部分动作，再重新观测和预测。

## 统一动作空间

RDT 通过在 `configs/state_vec.py` 里的 `STATE_VEC_IDX_MAPPING` （一张把状态映射到向量下标的表）统一动作空间。128维的动作映射如下：

```txt
[0, 10)   右臂关节角        right_arm_joint_{0..9}_pos
[10, 15)  右夹爪关节        right_gripper_joint_{0..4}_pos（其中 10 = right_gripper_open）
[15, 25)  右臂关节速度      right_arm_joint_{0..9}_vel
[30, 33)  右末端位置        right_eef_pos_{x,y,z}
...       左臂 / 左夹爪 / 底盘 等对称槽位
```

任何一个数据集，只要把自己的动作填进对应槽位、其余留空，就能使用同一个模型。这体现在复现时 `maniskill_model.py` 里的两段代码：`MANISKILL_INDICES` 把 ManiSkill 的 7 个关节角 + 1 个夹爪开合映射到统一向量的对应下标；`_format_joint_to_state` 把原始 qpos 归一化后写入这些槽位，同时生成一个 `state_elem_mask` 标记哪些维度是真的有意义的。模型输出后，再用同一组下标 `_unformat_action_to_joint` 把动作取回 ManiSkill 的关节空间。

用伪代码把填充 / 取回这两步写清楚：

```python
import numpy as np

STATE_DIM = 128

# ManiSkill：7 个关节角（槽位 0-6）+ 1 个夹爪开合（槽位 10）
# 对应 right_arm_joint_{0..6}_pos 和 right_gripper_open
MANISKILL_INDICES = list(range(7)) + [10]   # 共 8 个有效维度

def format_to_state(qpos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """把 8 维 ManiSkill qpos 填进 128 维统一向量，返回 (state_vec, mask)。"""
    assert qpos.shape == (8,)
    state_vec = np.zeros(STATE_DIM)
    mask = np.zeros(STATE_DIM, dtype=bool)

    state_vec[MANISKILL_INDICES] = qpos
    mask[MANISKILL_INDICES] = True
    return state_vec, mask

def unformat_action(action_128: np.ndarray) -> np.ndarray:
    """从 128 维输出动作取回 8 维 ManiSkill 动作。"""
    return action_128[MANISKILL_INDICES]

# 示例
qpos = np.array([0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7, 0.9])   # 7 关节 + 夹爪
state_vec, mask = format_to_state(qpos)

print("有效维度下标:", np.where(mask)[0])   # [0 1 2 3 4 5 6 10]
print("state_vec[0:12]:", state_vec[:12])   # 索引 7 / 8 / 9 / 11 为 0；索引 10 是夹爪值 0.9

# 模型输出 action_128 后
action_128 = np.random.randn(STATE_DIM)     # 假设模型输出
action_8   = unformat_action(action_128)
print("取回的 8 维动作:", action_8)
```

不同机器人只需换 `MANISKILL_INDICES`，其余逻辑完全复用。这是 128 维统一空间让多机器人数据共用一个模型的工程本质。

## 总体结构

RDT 的数据流如下：

```txt
语言指令
  -> language condition tokens (4096 维) （through T5-XXL text encoder）

多视角图像（2 帧 × 最多 3 视角）
  -> image condition tokens (1152 维) （through SigLIP vision encoder)

本体状态 -> 统一 128 维状态向量 + action mask

[state token, noisy action tokens] + 控制频率 + diffusion timestep
  -> Diffusion Transformer（28 层）
       每层交替 cross-attention 到 language / image 条件
  -> 预测的动作（去噪目标）
  -> DPM-Solver 反复去噪
  -> 未来 64 步动作 chunk
```

三个条件分别用一个 adaptor（`lang_adaptor`、`img_adaptor`、`state_adaptor`，都是小 MLP）投影到主干隐藏维度 2048。语言和图像条件不进入主干的 token 序列，而是作为 cross-attention 的 key / value。

## Diffusion Transformer 主干

RDT 的主干是一个为动作生成定制的 DiT（Diffusion Transformer）（`models/rdt/model.py` 的 `RDT` 类，`models/rdt/blocks.py` 的 `RDTBlock`）。1B 配置是 `hidden_size=2048`、`depth=28`、`num_heads=32`。

主干输入序列在状态 / 动作 token 前面拼上两个特殊 token：

```python
t   = self.t_embedder(t)       # diffusion timestep embedding
freq = self.freq_embedder(freq) # 控制频率 embedding
x = torch.cat([t, freq, x], dim=1)   # 再加多模态位置编码
```

把控制频率显式编码进去，是为了让同一个模型适配不同采样频率的机器人，这个对应推理时要传入的 `ctrl_freqs`。

每个 `RDTBlock` 的结构是三段式：

1. `RmsNorm` + 自注意力（带 QK-Norm）为序列内部建模；
2. `RmsNorm` + cross-attention 考虑外部条件；
3. `RmsNorm` + FFN。

关键细节在 `forward` 里：条件按层**交替**注入：偶数层看语言条件、奇数层看图像条件。这样 28 层下来，动作 token 交替从语言和视觉里取信息。最后，`FinalLayer` 将 hidden states 映射到动作空间，只保留末尾 `horizon` 个动作 token 作为输出。

相比 Octo 把 diffusion 放在一个小 action head 里，RDT 是把整个 1B 主干都做成扩散模型，条件化方式也从读 readout token 换成了 cross-attention 到 T5 / SigLIP 条件。

## 训练与采样

噪声调度的配置在 `base.yaml` 的 `noise_scheduler` 段，在 `models/rdt_runner.py` 里则体现为两个 scheduler：

| 阶段 | scheduler | 步数 | 说明 |
|---|---|---|---|
| 训练加噪 | `DDPMScheduler` | `num_train_timesteps=1000` | 1000 步的 cosine（`squaredcos_cap_v2`）调度 |
| 推理采样 | `DPMSolverMultistepScheduler` | `num_inference_timesteps=5` | 用 DPM-Solver 把采样压到 5 步，推理快 |

>hint：`prediction_type` 是 `sample` 而不是 `epsilon`。也就是说，RDT 的网络直接预测**去噪后的干净动作**，而不是预测加进去的噪声。这和 Octo 默认 action head 预测噪声 `eps` 相反，读源码时要注意。`clip_sample=False`，因为动作已经归一化到 `[-1, 1]`，不需要再裁剪。

采样循环（conditional_sample）从高斯噪声开始，对每个 timestep：把当前带噪动作和 state token 拼成序列，过主干，得到预测；再用 `DPMSolver.step` 更新。只要 5 步，就能从噪声得到一段动作 chunk。

## 动手练习

1. 用正文里的 `format_to_state` / `unformat_action` 代码，把 `MANISKILL_INDICES` 改成只包含右臂关节 0–6（去掉夹爪，即去掉 `10`），重新运行并打印 `np.where(mask)[0]`。对比前后 mask 变化，思考如果训练时夹爪维度的 mask 全为 0，模型对夹爪动作的输出会有什么影响。
2. 解释 RDT 主干里偶数层 cross-attention 看语言、奇数层看图像的设计——如果改成所有层都只看语言，28 层参数量不变，哪些能力会退化？
3. `prediction_type=sample`（预测干净动作）和 `prediction_type=epsilon`（预测噪声）在数学上等价，但工程上有什么实际差别？结合 `clip_sample=False` 一起解释。
4. 训练用 DDPM 1000 步、推理用 DPM-Solver 5 步，这样做的动机是什么？如果推理也用 1000 步 DDPM，控制频率会怎么变？

## References

- [RDT 项目主页](https://rdt-robotics.github.io/rdt-robotics/)

## 导航

- 上一节：[RDT](../03-rdt.md)
- 返回上级：[RDT](../03-rdt.md)
- 下一节：[RDT 实践（一）：微调环境与数据准备](02-practice.md)
