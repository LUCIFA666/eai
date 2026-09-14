# 8.2.2 Diffusion Policy

Diffusion Policy 可以翻译成“扩散策略”。它把机器人 policy（策略，也就是从观测到动作的控制模型）看成一个 conditional denoising diffusion model（条件去噪扩散模型）：先从随机噪声开始，逐步去噪，生成一段连续 action trajectory（动作轨迹）。这里的“条件”通常是最近几帧图像、机器人状态和环境状态；“去噪”是指模型反复把一段带噪动作轨迹变得更像专家动作。

这一节先不追求把扩散生成模型的所有数学细节讲完，而是回答机器人初学者最需要的几个问题：

- 为什么动作预测要用 diffusion（扩散）而不是普通回归？
- 训练时到底给什么加噪、模型预测什么、loss 怎么算？
- 推理时为什么要跑多步 denoising（去噪），以及怎么把生成的长动作轨迹切成可执行动作？
- LeRobot 和原始 Diffusion Policy 参考项目代码里，`horizon`、`n_obs_steps`、`n_action_steps` 分别是什么意思？
- Diffusion Policy 和上一节 ACT 的边界在哪里？

## 为什么需要扩散策略

普通 Behavior Cloning（行为克隆，BC）常常把问题写成：

```text
observation_t -> action_t
```

或者像 ACT 那样：

```text
observation_t -> action chunk
```

这些方法都可以工作，但机器人示教里经常有 multimodal action distribution（多模态动作分布）：同一个观测下存在多种合理动作。例如 Push-T 任务里，推块既可以从左侧推，也可以从右侧推；整理桌面时，先拿红块还是先拿蓝块都可能成功。用 MSE（均方误差）直接回归动作时，模型可能学到多个动作模式的平均值，而平均动作不一定对应任何一种可执行策略。

Diffusion Policy 的核心想法是：不要让模型一次性输出一个平均动作，而是让模型学习“专家动作轨迹分布”。推理时从随机噪声采样，再在当前观测条件下逐步去噪，得到一个具体的动作轨迹样本。

从控制角度看，Diffusion Policy 也使用 receding-horizon control（滚动时域控制）：模型每次预测未来一段动作，但只执行前面一小段，然后重新观测、重新规划。这一点和 ACT 的 action chunk 执行很像，但 Diffusion Policy 的动作片段是通过反复去噪生成的。

## 扩散模型的最小直觉

扩散模型有两个过程。

Forward diffusion（前向扩散）在训练时使用：给干净数据逐步加噪。这里的干净数据不是图片，而是一段专家 action trajectory：

```text
x_0 = expert action trajectory
x_t = noisy action trajectory at diffusion step t
```

一种常见公式是：

```text
x_t = sqrt(alpha_bar_t) * x_0 + sqrt(1 - alpha_bar_t) * epsilon
```

这里 `epsilon` 是从标准正态分布采样的噪声，`alpha_bar_t` 是由 beta schedule（噪声日程）累积出来的系数。`t` 越大，动作轨迹越接近噪声。

Reverse diffusion（反向扩散）在推理时使用：从随机噪声开始，按时间步逐步去噪：

```text
noise -> less noisy action trajectory -> ... -> executable action trajectory
```

在机器人里，条件信息是当前观测窗口：

```text
condition = recent images + recent robot states
```

所以完整问题是：

```text
sample action trajectory from p(actions | observations)
```

它不是“生成一张图”，而是“生成一段可执行动作”。

## 数据窗口：To、Ta、T

原始 Diffusion Policy 参考项目代码的 README 用三个符号解释接口：

| 名称 | 代码变量 | 含义 |
|---|---|---|
| Observation Horizon | `To` / `n_obs_steps` | 输入多少步历史观测 |
| Action Horizon | `Ta` / `n_action_steps` | 每次实际执行多少步动作 |
| Prediction Horizon | `T` / `horizon` | 模型一次生成多少步动作 |

举例：

```text
n_obs_steps = 2
horizon = 16
n_action_steps = 8
```

表示模型看最近 2 步观测，生成 16 步动作轨迹，但只执行从当前时刻开始的 8 步。执行完或动作队列耗尽后，再拿新观测重新生成。

低维任务的接口可以写成：

```text
obs:    (B, To, Do)
action: (B, Ta, Da)
```

这里 `B` 是 batch size（批大小），`Do` 是 observation dimension（观测维度），`Da` 是 action dimension（动作维度）。

原始 Diffusion Policy 参考项目代码的图像策略对外接口也是“观测窗口进来、可执行动作段出去”：

```text
obs["image"]:     (B, To, C, H, W)
obs["agent_pos"]: (B, To, state_dim)
returned action:  (B, Ta, Da)
```

这和模型内部训练/采样用的完整 `horizon/T` 不同。原始 image policy 训练时会用长度为 `horizon` 的动作窗口，推理时先生成完整 `horizon`，再返回 `start = n_obs_steps - 1` 到 `start + n_action_steps` 的可执行动作段。LeRobot 的 `generate_actions()` 也做同样切片，最后实际进入 action queue 的形状是 `(B, n_action_steps, action_dim)`。

在 LeRobot diffusion policy 里，训练 batch 更明确：

```text
observation.state:  (B, n_obs_steps, state_dim)
observation.images: (B, n_obs_steps, num_cameras, C, H, W)
action:             (B, horizon, action_dim)
action_is_pad:      (B, horizon)
```

`action_is_pad` 是 padding mask（补齐标记），表示动作窗口边缘哪些位置是复制或补齐出来的，不是真实 episode 内动作。LeRobot 的 `do_mask_loss_for_padding` 可以选择是否在 loss 里屏蔽这些位置；默认是 `False`，因为原始 Diffusion Policy 也没有默认做这个 mask。对初学者来说，重要的是知道：是否 mask padding 是一个明确配置，不要假设所有 policy 都自动屏蔽。

## 数据采样与归一化

原始 Diffusion Policy 参考项目代码使用 `ReplayBuffer` 和 `SequenceSampler` 准备固定长度训练样本。ReplayBuffer（回放缓冲区）把所有 episode 的字段沿时间维拼起来保存，典型磁盘格式是 Zarr。Zarr 是一种适合大数组分块读写的存储格式，常用于保存图像、状态和动作数组。SequenceSampler（序列采样器）负责从拼接后的长数组中切出长度为 `horizon` 的训练窗口，并在 episode 边界按配置补齐。

README 里的 Push-T 示例大致是：

```text
data/pusht_cchi_v7_replay.zarr
├── data
│   ├── action
│   ├── img
│   ├── keypoint
│   └── state
└── meta
    └── episode_ends
```

`episode_ends` 记录每条 episode 在拼接大数组里的结束位置。`SequenceSampler` 再根据 `horizon`、`pad_before`、`pad_after` 切出固定长度窗口；`pad_before/pad_after` 表示窗口允许在 episode 开头之前或结尾之后补多少步。窗口越靠近 episode 边界，越可能需要复制首帧或末帧来补齐。

归一化同样关键。原始仓库的 `LinearNormalizer` 会保存 observation 和 action 的 scale/bias，并作为 policy checkpoint 的一部分保存。LeRobot 的默认 diffusion 配置则是：

| 字段 | 默认归一化 |
|---|---|
| `VISUAL` | mean/std |
| `STATE` | min/max |
| `ACTION` | min/max |

Diffusion Policy 常常会把 action 裁剪到 `[-1, 1]` 附近，因此 action normalization（动作归一化）错了会非常危险：采样器生成的是归一化动作，部署前必须用同一套统计量反归一化成机器人控制接口需要的尺度。

## 模型结构

典型图像版 Diffusion Policy 的数据流是：

```text
recent images -> vision encoder -> visual features
recent robot states -> state features
features concat -> global condition
noisy action trajectory + diffusion timestep + condition -> 1D conditional U-Net
predicted noise or predicted clean action trajectory
```

vision encoder（视觉编码器）通常是 ResNet 这类 CNN backbone（卷积神经网络主干）。LeRobot 的 `DiffusionConfig` 默认使用 `resnet18`，并支持多相机时每个相机单独一个 RGB encoder。

核心去噪网络通常是 conditional U-Net 1D。U-Net 是一种带下采样和上采样路径的网络结构；这里的 1D 不是处理图像二维空间，而是沿动作时间序列处理 `horizon` 维度。Conditional（条件）表示网络不仅看 noisy action trajectory，还看观测编码后的条件向量。

下面这张表是 LeRobot 0.5.2 参考实现中 `DiffusionConfig` 的默认预设。源码注释说明这些 defaults 面向 PushT 风格任务，也就是 proprioceptive state（本体状态）加单相机观测的起步配置；它们不是所有机器人任务的通用最优参数。

| 配置 | 默认值 | 含义 |
|---|---:|---|
| `n_obs_steps` | 2 | 输入最近 2 步观测 |
| `horizon` | 64 | 模型生成 64 步动作轨迹 |
| `n_action_steps` | 32 | 每次实际执行 32 步动作 |
| `vision_backbone` | `resnet18` | 图像编码主干 |
| `use_separate_rgb_encoder_per_camera` | `True` | 多相机分别编码再拼接 |
| `down_dims` | `(512, 1024, 2048)` | U-Net 每层通道数 |
| `noise_scheduler_type` | `DDPM` | 默认使用 DDPM scheduler（DDPM 调度器，负责定义加噪/去噪时间步和每步噪声大小） |
| `num_train_timesteps` | 100 | 训练扩散步数，也就是训练时可采样的噪声等级数量 |
| `prediction_type` | `epsilon` | prediction type（预测目标类型）为 `epsilon`，表示默认预测噪声 |
| `clip_sample` | `True` | 推理每步把样本裁剪到指定范围 |

配置里还有一个容易忽略的约束：`horizon` 必须能被 U-Net 下采样因子整除。LeRobot 的检查是让 `horizon % (2 ** len(down_dims)) == 0`，否则时间维下采样和上采样对不齐。

## 训练目标

Diffusion Policy 的训练目标是 denoising MSE（去噪均方误差）。这里的 scheduler（调度器）是控制扩散时间步、加噪强度和反向去噪更新公式的组件；`prediction_type` 是训练目标类型，决定网络预测噪声 `epsilon` 还是干净样本 `x_0`。流程可以写成：

```text
1. 取专家动作轨迹 x_0
2. 采样噪声 epsilon
3. 采样扩散步 t
4. 用 scheduler 得到带噪动作轨迹 x_t
5. 网络输入 x_t、t、observation condition
6. 网络输出 pred
7. 根据 prediction_type 计算 MSE
```

如果 `prediction_type = "epsilon"`，模型预测噪声：

```text
target = epsilon
loss = MSE(pred, epsilon)
```

如果 `prediction_type = "sample"`，模型预测干净动作轨迹：

```text
target = x_0
loss = MSE(pred, x_0)
```

LeRobot 和原始仓库都支持这两类目标，但默认常用 `epsilon`。原始 Diffusion Policy 参考项目代码的 image Push-T 配置里：

```yaml
noise_scheduler:
  _target_: diffusers.schedulers.scheduling_ddpm.DDPMScheduler
  num_train_timesteps: 100
  beta_schedule: squaredcos_cap_v2
  prediction_type: epsilon
policy:
  horizon: 16
  n_obs_steps: 2
  n_action_steps: 8
  num_inference_steps: 100
```

`num_inference_steps` 是推理去噪步数，也就是部署时从随机动作噪声反复更新到最终动作轨迹要走多少个反向扩散 step。它可以和 `num_train_timesteps` 相同，也可以更少；更少通常更快，但需要实测动作质量。

下面是一个最小的前向扩散和 loss 选择示例：

```python
import math


def add_noise(x0, eps, alpha_bar):
    return [
        math.sqrt(alpha_bar) * clean + math.sqrt(1.0 - alpha_bar) * noise
        for clean, noise in zip(x0, eps)
    ]


def diffusion_target(x0, eps, prediction_type):
    if prediction_type == "epsilon":
        return eps
    if prediction_type == "sample":
        return x0
    raise ValueError(f"unsupported prediction_type: {prediction_type}")


def mse(pred, target):
    return sum((p - y) ** 2 for p, y in zip(pred, target)) / len(pred)
```

这段代码没有实现完整 DDPM scheduler，只展示训练目标的本质：给干净动作加噪，然后训练网络预测噪声或干净动作。

## 推理与滚动执行

推理时没有专家动作 `x_0`。模型从随机高斯噪声开始，逐步 denoise：

```text
sample = Gaussian noise with shape (B, horizon, action_dim)
for diffusion step t:
    model_output = unet(sample, t, observation_condition)
    sample = scheduler.step(model_output, t, sample)
actions = sample
```

`num_inference_steps` 是推理去噪步数。它可以等于 `num_train_timesteps`，也可以更少。步数越多，采样通常越慢；步数太少，动作质量可能下降。DDIM（Denoising Diffusion Implicit Models，一种可用更少步数采样的扩散采样器）常用于加速推理；DDPM（Denoising Diffusion Probabilistic Models，经典概率扩散采样器）通常更直接但可能更慢。LeRobot 支持 `DDPM` 和 `DDIM` 两种 scheduler。

生成完整 `horizon` 后，不会全部执行。LeRobot 的 `generate_actions()` 做：

```text
start = n_obs_steps - 1
end = start + n_action_steps
actions_to_execute = actions[:, start:end]
```

这是因为 `horizon` 是从最早那帧观测开始计数的。如果 `n_obs_steps=2`，当前时刻是窗口里的第 2 帧，所以当前动作从 index `1` 开始取。

一个最小窗口切片函数：

```python
def execution_slice(actions, n_obs_steps, n_action_steps):
    start = n_obs_steps - 1
    end = start + n_action_steps
    if end > len(actions):
        raise ValueError("n_action_steps exceeds available generated actions")
    return actions[start:end]
```

LeRobot 还要求：

```text
n_action_steps <= horizon - n_obs_steps + 1
```

否则从当前时刻开始，生成轨迹里没有足够动作可执行。

## 和 ACT 的区别

ACT 和 Diffusion Policy 都预测一段未来动作，但它们的生成方式不同：

| 维度 | ACT | Diffusion Policy |
|---|---|---|
| 输出方式 | Transformer 一次前向输出 action chunk | 从噪声开始多步去噪生成 action trajectory |
| 训练目标 | masked L1 + 可选 KL | denoising MSE |
| 多模态表达 | VAE latent 表达一定多样性 | 通过采样动作轨迹分布表达多模态 |
| 推理成本 | 通常一次网络前向生成 chunk | 多个 denoising steps，通常更慢 |
| 时间窗口 | `chunk_size` / `n_action_steps` | `horizon` / `n_obs_steps` / `n_action_steps` |
| 调参重点 | chunk 长度、KL、temporal ensemble | scheduler、采样步数、horizon、normalization |

可以这样理解：ACT 更像“直接预测接下来怎么做”，Diffusion Policy 更像“在当前观测条件下，从许多可能动作轨迹中采样出一条”。如果任务动作模式很清晰，ACT 往往更简单；如果同一状态下存在多种合理轨迹，Diffusion Policy 的优势会更明显。

## 原始仓库训练流程

Diffusion Policy 参考项目代码以 Push-T 为例给出完整流程。

1. 下载训练数据。

```bash
mkdir data
cd data
wget https://diffusion-policy.cs.columbia.edu/data/training/pusht.zip
unzip pusht.zip
cd ..
```

2. 下载或准备配置。

```bash
wget -O image_pusht_diffusion_policy_cnn.yaml \
  https://diffusion-policy.cs.columbia.edu/data/experiments/image/pusht/diffusion_policy_cnn/config.yaml
```

3. 单 seed 训练。

```bash
python train.py \
  --config-dir=. \
  --config-name=image_pusht_diffusion_policy_cnn.yaml \
  training.seed=42 \
  training.device=cuda:0 \
  hydra.run.dir='data/outputs/${now:%Y.%m.%d}/${now:%H.%M.%S}_${name}_${task_name}'
```

训练输出目录通常包含：

```text
checkpoints/
.hydra/config.yaml
logs.json.txt
media/*.mp4
train.log
```

这正是机器人实验需要保留的最小证据：配置、日志、checkpoint、rollout 视频。rollout（闭环试跑/评估）是把策略放进仿真环境或真机控制循环，完整跑完 episode 并记录成功率、reward 和视频。README 还提供多 seed Ray 训练和预训练 checkpoint 评估流程；论文表格里的数值来自多次训练的聚合指标，而不是某一次最好看的视频。

真实机器人流程也强调安全边界：UR 机器人需要急停在手边，RealSense 相机和 SpaceMouse 先确认工作，再用 `demo_real_robot.py` 采集、`train.py` 训练、`eval_real_robot.py` 评估。真机评估时按键开始/停止 episode，不能让策略无监督长时间运行。

## LeRobot 工作流中的 Diffusion Policy

LeRobot 把 Diffusion Policy 封装为 `policy.type=diffusion`。它的 `DiffusionPolicy.select_action()` 会维护两个队列：

- observation queue：缓存最近 `n_obs_steps` 步观测。episode 刚开始时，如果历史不够，会复制当前观测填满窗口。
- action queue：缓存本次生成后要执行的 `n_action_steps` 个动作。队列空了才重新采样一段动作。

训练时，`DiffusionPolicy.forward()` 把图像字段堆叠成统一的 `OBS_IMAGES`，然后调用 `compute_loss()`。`compute_loss()` 做的核心步骤是：

```text
trajectory = batch["action"]
eps = random noise with same shape
timesteps = random diffusion steps
noisy_trajectory = scheduler.add_noise(trajectory, eps, timesteps)
pred = unet(noisy_trajectory, timesteps, global_condition)
target = eps if prediction_type == "epsilon" else trajectory
loss = MSE(pred, target)
```

如果启用 `do_mask_loss_for_padding=True`，LeRobot 会用 `action_is_pad` 屏蔽 copy-padded action；如果没启用，则直接对全部位置求平均。这和 ACT 默认总是用 action mask 的直觉不同，所以迁移 policy 时要读配置。

## 调参顺序

Diffusion Policy 的参数很多，建议按下面顺序排查：

| 项 | 先看什么 | 常见调整 |
|---|---|---|
| action normalization | 动作是否都落在合理范围 | 先修 stats，再调模型 |
| horizon | 轨迹是否覆盖完整局部技能 | 太短学不到技能，太长训练更难 |
| n_obs_steps | 是否需要历史速度/接触趋势 | 图像任务常从 2 开始 |
| n_action_steps | 闭环频率是否足够 | 越小越频繁重规划，越大越平滑但滞后 |
| num_inference_steps | 推理延迟与动作质量 | 真机上常需要在质量和速度间折中 |
| scheduler | DDPM 还是 DDIM | DDIM 常用于少步加速，需实测 |
| prediction_type | 预测噪声还是样本 | 默认 `epsilon`，不要无依据频繁切换 |
| crop/resize | 目标是否被裁掉 | 图像增强必须保留任务关键区域 |
| batch size/lr | loss 是否稳定 | 扩散训练常用较大 batch 和 warmup |
| EMA（指数滑动平均参数） | eval 是否更稳 | 原始配置常用 EMA 版本评估 |

EMA 是 Exponential Moving Average（指数滑动平均），会维护一份更平滑的模型参数副本。原始 Diffusion Policy 配置默认使用 EMA，评估时常用 EMA 模型，因为它比最后一步训练权重更稳定。

## 常见错误

| 错误 | 表现 | 修正 |
|---|---|---|
| 把 `horizon` 当作实际执行步数 | 策略执行过长、闭环慢 | 区分 `horizon` 和 `n_action_steps` |
| 忽略 `n_obs_steps` 偏移 | 执行动作从错误 index 开始 | 使用 `start = n_obs_steps - 1` |
| 训练/部署归一化不一致 | 动作幅度完全错 | checkpoint 同步保存 normalizer/stats |
| action 超出 `clip_sample_range` | 推理被裁剪，动作饱和 | 确认 action normalization 到裁剪范围 |
| 推理步数太多 | 真机控制延迟大 | 测 `num_inference_steps` 与控制频率 |
| 推理步数太少 | 轨迹噪声大、不稳定 | 增加步数或换 scheduler |
| 忽略 padding | 边界窗口训练污染 | 明确 `pad_before/pad_after` 和 mask 策略 |
| 只看 train loss | rollout 不成功 | 看成功率、视频、接触阶段失败 |
| 随机 crop 裁掉目标 | 图像 loss 正常但策略失败 | 固定评估 crop，训练增强不过界 |
| 多相机顺序变化 | 部署完全错位 | 固定 camera key 和 encoder 输入顺序 |

Diffusion Policy 最容易被误判的问题是推理慢。慢不一定说明模型错，而是采样步数、U-Net 大小、图像编码器、GPU/CPU 数据搬运和控制频率共同决定了延迟。真机部署前必须测端到端 latency（端到端延迟）。

## 何时使用 Diffusion Policy

适合使用 Diffusion Policy 的情况：

- 同一观测下有多种合理动作轨迹，普通回归容易平均掉。
- 任务需要连续平滑动作，但又需要滚动闭环。
- 数据量和算力足以训练图像编码器和扩散 U-Net。
- 可以接受多步采样带来的推理延迟，或能用 DDIM/蒸馏/更小模型优化。
- 有严格的 rollout 视频和失败分类来调参。

不适合直接上 Diffusion Policy 的情况：

- 数据很少，连单步 BC 或 ACT baseline 都没跑通。
- action schema、相机顺序、时间戳对齐还不稳定。
- 控制频率很高，但推理设备无法满足延迟要求。
- 任务其实是简单单峰动作，扩散模型增加了不必要复杂度。
- 真机安全边界还没建好，无法承受采样策略探索。

实用建议是：先跑一个 state-only 或小图像 BC baseline，再跑 ACT，再跑 Diffusion Policy。这样如果 Diffusion Policy 失败，你能判断是扩散模型问题，还是数据和控制接口本来就没对齐。

## 本节实践任务

用一批 LeRobot 或 Push-T 风格数据训练 Diffusion Policy baseline。实践产出至少包括：

- 数据说明：episode 数、成功率、FPS、相机、state/action 维度、是否有 padding。
- 窗口配置：`n_obs_steps`、`horizon`、`n_action_steps`、`pad_before`、`pad_after`。
- 模型配置：视觉 encoder、U-Net `down_dims`、scheduler、`prediction_type`、`num_train_timesteps`、`num_inference_steps`。
- 归一化说明：每个 observation/action 字段用 mean/std 还是 min/max，统计量保存在哪里。
- 训练证据：config、train/val loss、checkpoint、EMA 设置、训练 seed。
- Rollout 证据：成功率、平均 reward/score、失败视频、延迟统计。
- 对比实验：至少比较不同 `num_inference_steps` 或不同 `n_action_steps` 的效果。
- 结论：当前瓶颈是数据、多模态、采样延迟、模型容量，还是真机控制。

验收标准是：另一个人可以拿到你的 config、normalizer/stats、checkpoint 和评估脚本，在同一数据版本上复现实验指标，并能从视频看出扩散策略是否生成了连贯动作轨迹。

## 学习检查清单

- 能解释 Diffusion Policy 为什么不是普通动作回归。
- 能写出 `x_t = sqrt(alpha_bar_t) x_0 + sqrt(1 - alpha_bar_t) epsilon` 的含义。
- 能区分 `n_obs_steps`、`horizon`、`n_action_steps`。
- 能说明 `prediction_type="epsilon"` 和 `"sample"` 的训练目标差别。
- 能解释 `num_train_timesteps` 和 `num_inference_steps` 的区别。
- 能说明为什么只执行生成轨迹中的一段动作。
- 能列出 DDPM、DDIM、U-Net、EMA、normalizer 的作用。
- 能指出 Diffusion Policy 相比 ACT 的优势和代价。
