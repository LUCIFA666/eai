# 4. 具身智能实战闭环：多模型 PPO 训练与推理评测 (End-to-End Embodied AI Practice: Multi-Model Training to Inference)

在掌握了底层架构与环境安装之后，我们将进入真正的实战环节。在当前的具身智能研究中，从零开始训练（Train from scratch）一个百亿参数的模型是不切实际的。在茫茫的连续动作空间中，智能体通过随机探索偶然成功抓取物体的概率微乎其微。因此，行业标准做法是：先使用大量人类遥操作数据进行监督微调（SFT），赋予模型基础的动作直觉，然后再通过强化学习（RL）在物理仿真器中进行不断试错与纠正，从而大幅提升任务的最终成功率。

为了全面覆盖目前业界主流的具身模型研究范式，本节将为您提供两条完整的实战训练链路：
* **实战 A：** 基于经典自回归架构的 OpenVLA 模型，在 ManiSkill3 环境中进行全参数 PPO 训练。
* **实战 B：** 基于前沿连续流匹配架构的 π₀.₅ 模型，在 LIBERO 环境中结合 LoRA 进行轻量级强化微调。

---

## 4.1 实战 A：OpenVLA 在 ManiSkill3 的 PPO 训练闭环

本小节将以 OpenVLA 模型在 ManiSkill3 仿真环境中执行典型的具身任务为例，带你走完从基座模型下载、配置文件修改、启动分布式训练，一直到日志监控和最终实盘测试的完整科研闭环。

### 4.1.1 为什么选择 OpenVLA 与 ManiSkill3？

OpenVLA 作为目前最成熟的开源视觉-语言-动作模型，配合渲染吞吐量极高的 ManiSkill3 仿真引擎，构成了验证 RLinf 框架性能的最佳基准测试（Benchmark）组合。这套组合不仅考验了框架对大规模自回归模型的分布式显存管理能力，也验证了物理仿真引擎在并行采集时的数据吞吐极限。

### 4.1.2 第一步：准备高质量的“初始大脑”

如前所述，我们需要一个经过 SFT 预训练的基座模型作为 PPO 训练的起点。官方提供了一个专门用于 RL 热身的权重版本 `openvla-7b-rlvla-warmup`。

首先，安装 Hugging Face 的命令行工具，并将该基座模型下载到本地。由于模型体积较大（约 15GB），请确保目标磁盘至少留有 30GB 的可用空间以应对后续的缓存和解压。

```bash
# 安装并更新 Hugging Face CLI 工具
pip install -U "huggingface_hub[cli]"

# 将模型权重下载至指定的本地工作目录
huggingface-cli download gen-robot/openvla-7b-rlvla-warmup \
  --local-dir /workspace/models/openvla-7b-rlvla-warmup/ \
  --repo-type model

# 验证下载是否完整
ls -lh /workspace/models/openvla-7b-rlvla-warmup/


```

### 4.1.3 第二步：驯服 YAML 配置文件

RLinf 摒弃了硬编码的训练参数，所有的资源调度与算法超参数都集中在 YAML 文件中管理。打开快速启动配置 `examples/embodiment/config/maniskill_ppo_openvla_quickstart.yaml`，在直接运行之前，请务必理解以下几个决定训练成败的关键配置块：

```yaml
# 【集群硬件与算力分配】
cluster:
  num_nodes: 1  # 单机训练模式
  component_placement:
    # 这里定义了 RLinf 核心的“解耦调度”
    # 如果你是 4 卡服务器，标准配置如下：0、1号卡做推理采样，2、3号卡做梯度计算
    actor,rollout: 0-1  
    learner: 2-3  
    # 注意：如果你只有 2 张卡，必须将其修改为 "actor,rollout: 0" 和 "learner: 1"

# 【模型路径配置】
rollout:
  model_dir: /workspace/models/openvla-7b-rlvla-warmup/  # 推理引擎加载的权重路径
actor:
  checkpoint_load_path: /workspace/models/openvla-7b-rlvla-warmup/ # 训练引擎加载的权重路径

# 【强化学习算法超参数 (PPO)】
ppo_config:
  batch_size: 32           # 单次梯度更新的样本数量。受限于 VLA 的显存消耗，不宜过大。
  learning_rate: 1.0e-5    # 大模型 RL 的学习率必须设置得极低（如 1e-5 或 5e-6），过高会导致模型原有的视觉语言表征遭到破坏（灾难性遗忘）。
  num_train_epochs: 4      # 在同一批采集到的数据上，重复进行几次 PPO 梯度下降。
  entropy_coef: 0.01       # 策略熵系数。用于鼓励模型在训练初期进行探索，防止过早收敛到次优解。

# 【物理仿真环境设置】
env:
  num_envs: 16             # 在物理引擎中并行实例化 16 个机械臂。数值越大采集越快，但会显著增加 GPU 渲染显存的压力。
  horizon: 200             # 环境的交互上限。如果机械臂 200 步还未完成任务，环境将强制重置。


```
<img width="1818" height="1412" alt="image" src="https://github.com/user-attachments/assets/d67b7031-d356-4b53-a803-d0a3513ab3d9" />
### 4.1.4 第三步：启动分布式训练

由于 ManiSkill3 高度依赖底层 GPU 的图形 API 进行场景和物理张量的渲染，在启动训练前，系统必须安装 Vulkan 相关的图形库支持。

```bash
# 补充环境底层图形依赖（仅限 Ubuntu/Debian 系统）
sudo apt-get install libvulkan1 vulkan-tools vulkan-validationlayers

# 激活虚拟环境
source .venv/bin/activate

# 一键启动 PPO 训练基线
bash examples/embodiment/run_embodiment.sh maniskill_ppo_openvla_quickstart


```

当你按下回车后，系统不会立刻开始疯狂打印 Loss。分布式架构的启动遵循严格的阶段流转：

1. **初始化阶段（约 1-2 分钟）：** 各个 Worker 节点被拉起，系统开始跨 GPU 划分 FSDP 模型碎片，并初始化 Adam 优化器状态。
2. **预热阶段（约 2-5 分钟）：** 环境开始并行步进，收集无梯度的初始随机交互数据，用于填充经验池并确立初始的奖励基线。
3. **主训练循环：** 系统正式进入“采集 -> 算优势 -> PPO 梯度更新 -> 权重同步”的稳态异步流转阶段。

<img width="2040" height="1406" alt="image" src="https://github.com/user-attachments/assets/3d92fd5c-f557-4ed0-8541-98c58db33a0f" />
### 4.1.5 第四步：训练日志与关键指标监控 (Monitoring)

强化学习的损失函数（Loss）并不像图像分类那样直观，Loss 下降不代表智能体变聪明了，可能只是找到了某种“作弊”的捷径。因此，我们需要通过 TensorBoard 实时监控训练的健康状态。

请重新打开一个终端，激活环境并启动 TensorBoard：

```bash
tensorboard --logdir=runs/


```

在浏览器中打开监控看板，你需要重点关注以下三个核心指标的走向：

* **`env/success_rate`（任务成功率）：** 这是唯一的金标准。在最初的几千步，该指标通常是 0。当看到它从 0 开始呈现爬坡趋势（如稳定在 0.2 以上）时，说明训练走上了正轨。
* **`train/entropy`（策略熵）：** 正常的趋势应该是一条极其缓慢下降的平缓曲线。如果该指标在训练初期瞬间跌至接近 0，说明模型过早失去了探索能力（策略坍塌），此时通常需要调低 `learning_rate` 或适当调高配置文件中的 `entropy_coef`。
* **`train/kl_divergence`（KL 散度）：** 反映了新旧策略更新的步伐大小。健康的 PPO 训练中，该值通常会被裁剪机制稳定控制在 `0.01` 到 `0.02` 之间。

### 4.1.6 第五步：提取 Checkpoint 与实盘推理 (Evaluation)

许多教程往往忽略了训练后的验证环节。当 `success_rate` 达到预期水平，或者训练脚本按计划正常结束后，我们需要提取训练好的权重（Checkpoints），将其重新放入环境中进行纯粹的推理测试。

此时，我们不再需要启动沉重的 Learner 节点算梯度，只需使用 RLinf 提供的评估脚本，加载最新的模型快照并录制执行视频。

```bash
# 假设训练过程中保存了 epoch_100 的模型快照
python -m rlinf.evaluate \
    --config examples/embodiment/config/maniskill_ppo_openvla_quickstart.yaml \
    --checkpoint_path ./runs/experiment_1/checkpoints/epoch_100 \
    --num_eval_episodes 50 \
    --save_video True


```

评估脚本执行完毕后，系统会在输出的 `videos/` 目录下生成 `.mp4` 格式的录像文件。通过查看这些视频，你可以直观地分析机械臂的动作连贯性以及强化学习策略在实际抓取任务中的鲁棒性。这标志着您已成功走通了整个大模型具身强化学习的闭环。

---

## 4.2 实战 B：π₀.₅ 在 LIBERO 环境下的 Flow-Noise 强化微调

OpenVLA 的全参数训练对硬件要求极高，通常需要 4 到 8 张高端显卡才能流畅运行。为了应对算力受限的场景，最新集成的 π₀.₅ 模型代表了另一条极具工程价值的前沿路径。

π₀.₅ 摒弃了传统的离散自回归动作生成，采用了更为平滑的连续流匹配（Flow-Matching）架构。更为关键的是，RLinf 框架为其深度适配了 LoRA（低秩自适应）微调技术以及专用的 Flow-Noise 强化算法。这意味着，在单张或两张 24G 消费级显卡上，即可完成具身大模型的强化后训练。我们将使用专为灵巧操作设计的 LIBERO 仿真环境组来验证这一流程。

### 4.2.1 第一步：获取 π₀.₅ 预训练底座

与 OpenVLA 类似，我们需要先拉取 π₀.₅ 的基础权重。由于其架构相对紧凑，下载与加载的耗时会显著减少。

```bash
# 确保在预先设定的 models 目录下执行
huggingface-cli download gen-robot/pi0_5-base-warmup \
  --local-dir /workspace/models/pi0_5-base-warmup/ \
  --repo-type model

# 检查模型文件完整性
ls -lh /workspace/models/pi0_5-base-warmup/

```

### 4.2.2 第二步：解析 LoRA 与 Flow-Noise 配置文件

π₀.₅ 的训练参数有着完全不同的逻辑。请打开专用配置文件 `examples/embodiment/config/libero_flownoise_pi0_5.yaml`，重点关注以下针对显存优化和算法调整的参数：

```yaml
# 【集群硬件与算力分配】
cluster:
  num_nodes: 1
  component_placement:
    # 得益于 LoRA 大幅降低了梯度图的尺寸，Learner 的显存压力骤减。
    # 在双卡环境下即可流畅运行：0卡负责环境渲染与推理，1卡负责更新 LoRA 参数。
    actor,rollout: 0
    learner: 1

# 【模型与微调配置】
model_config:
  base_model_dir: /workspace/models/pi0_5-base-warmup/
  use_lora: True        # 显式开启 LoRA 轻量级微调
  lora_config:
    r: 16               # LoRA 矩阵的秩（Rank），数值越大拟合能力越强，但显存开销越大
    lora_alpha: 32      # 缩放系数
    target_modules: ["q_proj", "v_proj", "out_proj"] # 仅对注意力机制的特定层注入可训练参数

# 【连续控制强化算法参数】
algorithm_config:
  name: flow_noise      # 指定使用专为 Flow-Matching 架构设计的强化算法
  noise_scale: 0.1      # 控制动作生成的探索方差，相当于 PPO 中的 entropy 机制
  learning_rate: 5.0e-5 # 由于是 LoRA 微调（更新参数极少），学习率可以比全参数训练适当调高

# 【物理仿真环境设置】
env:
  name: libero_spatial  # 指定使用 LIBERO 空间推理任务组
  num_envs: 8           # 适当降低并行环境数，以匹配单卡 Rollout 的推理吞吐瓶颈

```

### 4.2.3 第三步：启动轻量级训练与专属日志监控

环境准备就绪后，执行针对 π₀.₅ 模型的启动脚本。启动流程与前文类似，但模型加载阶段会额外打印 LoRA 参数的注入信息。

```bash
source .venv/bin/activate
bash examples/embodiment/run_embodiment.sh libero_flownoise_pi0_5

```

**监控指标的差异性：**
对于基于 Flow-Matching 的架构，在执行 `tensorboard --logdir=runs/` 后，除了关注通用的 `env/success_rate` 之外，你需要将注意力转移到以下专属指标：

* **`train/flow_loss`（流匹配损失）：** 该指标反映了模型预测的动作轨迹与环境反馈的理想动作流之间的偏差。在正常训练下，它应当呈现出平滑下降的趋势。
* **`train/lora_grad_norm`（LoRA 梯度范数）：** 由于冻结了大部分主干网络，监控 LoRA 层的梯度状态尤为重要。如果该值出现巨大的毛刺（Spikes）或长期趋近于 0，说明设定的学习率可能过高，或者模型陷入了梯度消失的状态。

### 4.2.4 第四步：权重合并与评测验证

这也是 LoRA 训练与全参数训练在工程落地上最大的区别。使用 LoRA 训练结束后，系统保存在 `checkpoints/` 目录下的仅仅是体积几百兆的 LoRA 适配器（Adapter）权重文件，而非完整的数十 GB 模型。

在评测阶段，为了恢复完整的推理能力，模型需要同时读取底座和适配器。RLinf 的评估脚本在解析到 `use_lora: True` 的配置时，会在显存中自动执行“底座权重 + LoRA 权重”的动态合并（Merge），随后将其载入 LIBERO 环境进行实盘推理测试：

```bash
python -m rlinf.evaluate \
    --config examples/embodiment/config/libero_flownoise_pi0_5.yaml \
    --checkpoint_path ./runs/pi0_5_libero/checkpoints/epoch_80 \
    --num_eval_episodes 20 \
    --save_video True

```

通过这套平行的实战流程，我们不仅掌握了传统的全参数 PPO 范式，也打通了在算力受限场景下，利用前沿连续流架构和 LoRA 技术进行高效强化的现代路径。

```

```
