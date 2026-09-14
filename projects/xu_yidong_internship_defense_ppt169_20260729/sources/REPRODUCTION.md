# Δ-IRIS 完整复现报告

> 参考实测快照时间：2026-07-10 10:33 UTC  
> 官方论文：[Efficient World Models with Context-Aware Tokenization](https://proceedings.mlr.press/v235/micheli24a.html)  
> 官方代码：[vmicheli/delta-iris](https://github.com/vmicheli/delta-iris)  
> 官方预训练模型：[Hugging Face vmicheli/delta-iris](https://huggingface.co/vmicheli/delta-iris)

## 1. 复现结论

本次已经完成以下内容：

- 固定官方源码版本和完整软件环境。
- 实测 Crafter、Atari Breakout 环境 reset/step。
- Crafter 端到端 smoke：环境采集、tokenizer、world model、actor-critic、checkpoint 全链路通过。
- Atari Breakout 端到端 smoke：同样完成三组件反向更新和 checkpoint 落盘。
- Crafter smoke 的模型、三个 optimizer、dataset 和 episode count 恢复成功。
- 官方 Crafter 5M checkpoint 完成文件大小、SHA256、434 项 state dict 严格加载检查。
- 官方 checkpoint 完成真实策略单步、tokenizer 条件重建、world-model burn-in 和单步想象。
- Crafter 名义 5M 从头训练已经验证启动，并持续产出多个 durable checkpoint。

截至参考快照还不能宣称“论文最终性能已经复现”：

- 从头训练尚未跑满名义 5M 环境帧。
- 官方配置首次正式 evaluation 在 epoch 50；参考快照尚未产生最终 Crafter benchmark score。
- Atari 只完成了端到端 smoke，没有完成官方 600 epochs 长训。
- 官方 checkpoint 的可视化结果是参考权重验证，不是本次 scratch 训练的最终成绩。

因此，本报告的准确结论是：

> **工程复现链路成功，官方预训练模型验证成功，并已证明 scratch 长训能够稳定产出 checkpoint；论文最终分数仍待完整长训和正式评估。**

![复现流程](repro/report_assets/reproduction_pipeline.png)

*图 1：实际完成的复现关卡。每一项均有命令输出或落盘产物作为证据。*

## 2. 复现范围与成功标准

本次将“复现成功”拆成四层，避免只看到程序启动就误判成功。

| 层级 | 成功标准 | 本次状态 |
|---|---|---|
| 环境层 | 依赖闭包无冲突，CUDA/BF16 可用，Crafter/Atari 可 step | 通过 |
| 工程层 | 采集、三个模型组件反向、checkpoint、resume 全部可用 | 通过 |
| 预训练推理层 | 官方文件哈希正确，严格加载，策略和世界模型可前向 | 通过 |
| 论文性能层 | scratch 训练完成 5M，并产生可对照论文的正式评估 | 未完成 |

![验证矩阵](repro/report_assets/validation_matrix.png)

*图 2：已经实际执行的验证矩阵。*

## 3. 源码、硬件与软件环境

### 3.1 固定源码

固定提交：

<code>f8d417321717a3d7012488785d7cdc66b62455dd</code>

该仓库是 Δ-IRIS，不是 2023 年原版 IRIS；二者不能混用。

本报告不假设用户名、Home 目录、Conda 安装目录或数据盘挂载点。克隆后统一初始化以下变量：

命令适用于带 Bash、Conda、GNU coreutils、tmux 和 NVIDIA CUDA 的 Linux 主机，也适用于配置了相同工具链的 WSL2。不同机器可以使用不同用户名、仓库目录、Conda 目录、数据盘和 GPU 编号；原生 Windows PowerShell 或无 NVIDIA GPU 的 macOS 不在这组命令的直接适用范围内。

~~~bash
export REPO_ROOT="$(git rev-parse --show-toplevel)"
export DELTA_IRIS_DATA_ROOT="$REPO_ROOT/outputs/long_runs"
~~~

如果另一台电脑有容量更大的数据盘，只需在启动前通过环境变量覆盖 <code>DELTA_IRIS_DATA_ROOT</code>；报告不写入任何机器的实际挂载路径。

<code>RUN_DIR</code>、<code>LOG_FILE</code> 和 <code>SESSION_NAME</code> 由 tmux 启动器计算并返回，避免修改数据根后仍意外沿用旧路径。后文所有路径都相对于 <code>$REPO_ROOT</code> 或由这些变量推导。

### 3.2 实测硬件

| 项目 | 实测值 |
|---|---|
| OS | Ubuntu 24.04.3 LTS |
| Kernel | Linux 6.8.0-117-generic |
| CPU | 2 × Intel Xeon Platinum 8358P，128 线程 |
| RAM | 约 1 TiB |
| GPU | 8 × NVIDIA A100-SXM4-80GB |
| Driver | 580.159.03 |
| 长训卷 | 本次实测快照约 1.46 TiB 可用；重跑时由 <code>$DELTA_IRIS_DATA_ROOT</code> 指定 |

### 3.3 实测软件

| 软件 | 版本 |
|---|---:|
| Python | 3.9.23 |
| pip | 23.0 |
| setuptools | 65.5.0 |
| wheel | 0.38.4 |
| torch | 2.1.2+cu121 |
| torchvision | 0.16.2+cu121 |
| gym | 0.21.0 |
| ale-py | 0.7.4 |
| crafter | 1.8.3 |
| hydra-core | 1.1.1 |
| wandb | 0.17.0 |

完整传递依赖锁文件：

<code>repro/requirements-lock-py39.txt</code>

![硬件环境](repro/report_assets/hardware_snapshot.png)

*图 3：本次参考主机的硬件和运行时快照；这是实测证据，不是其他机器必须满足的固定路径或硬件要求。*

## 4. 复现过程

### 4.1 获取并确认官方代码

执行并核对：

~~~bash
git clone https://github.com/vmicheli/delta-iris.git
cd delta-iris
git checkout --detach f8d417321717a3d7012488785d7cdc66b62455dd
export REPO_ROOT="$(git rev-parse --show-toplevel)"
git rev-parse HEAD
~~~

实测输出：

~~~text
f8d417321717a3d7012488785d7cdc66b62455dd
~~~

官方仓库没有稳定 tag/release，因此报告直接固定 commit。

### 4.2 创建隔离环境

本次没有污染系统 Python，也没有复用旧 IRIS 环境。

~~~bash
conda create -y -n delta-iris python=3.9
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate delta-iris
export PYTHON_BIN="$(command -v python)"
python -m pip install pip==23.0 setuptools==65.5.0 wheel==0.38.4
python -m pip install -r "$REPO_ROOT/requirements.txt"
python -m pip check
~~~

依赖检查实测：

~~~text
No broken requirements found.
~~~

### 4.3 环境与 GPU 探针

实际检查了：

- torch/torchvision 导入。
- CUDA runtime 和驱动兼容。
- A100 BF16 支持。
- Crafter reset 和 step。
- Breakout ROM 加载、reset 和 step。

核心实测输出：

~~~text
torch 2.1.2+cu121
torchvision 0.16.2+cu121
cuda_runtime 12.1
CUDA available True
GPU NVIDIA A100-SXM4-80GB
BF16 True
Crafter observation (64, 64, 3), actions 17
Breakout observation (210, 160, 3), actions 4
~~~

### 4.4 Crafter 与 Atari 端到端 smoke

两个 smoke 都保留官方模型尺寸，只把采样缩短到 64 steps，并把三个组件各缩短为一次 optimizer step。

实际重新执行：

~~~bash
cd "$REPO_ROOT"
./repro/smoke_crafter.sh
./repro/smoke_atari.sh
~~~

两条命令退出码均为 0。

脚本默认使用当前激活环境中的 <code>python</code>。如需指定解释器或可见 GPU：

~~~bash
export PYTHON_BIN="$(command -v python)"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export DEVICE="${DEVICE:-cuda:0}"
./repro/smoke_crafter.sh
~~~

如果目标 GPU 不是物理编号 0，请在执行前由目标机器用户或作业调度器设置 <code>CUDA_VISIBLE_DEVICES</code>；程序内部默认使用映射后的逻辑设备 <code>cuda:0</code>。

覆盖链路：

~~~text
environment collection
  -> EpisodeDataset persistence
  -> tokenizer forward/backward/update
  -> world model forward/backward/update
  -> imagination actor-critic backward/update
  -> model + optimizer + dataset checkpoint
~~~

![Smoke 轨迹](repro/report_assets/smoke_trajectories.png)

*图 4：从两次实际执行的 64-step smoke dataset 读回的原始帧，不是项目宣传图。*

### 4.5 Smoke checkpoint 恢复

在最新 Crafter smoke 目录中实际运行：

~~~bash
SMOKE_RUN="$(ls -dt "$REPO_ROOT"/outputs/smoke_crafter_* | head -n 1)"
cd "$SMOKE_RUN"
./scripts/resume.sh
~~~

实测输出：

~~~text
(train_dataset) 1 episodes, 64 steps.
Successfully loaded model and optimizer from .../checkpoints.
~~~

恢复内容包括：

- tokenizer 权重和 optimizer。
- world model 权重和 optimizer。
- actor-critic 权重和 optimizer。
- epoch。
- dataset info。
- episode sampling counts。

### 4.6 官方 Crafter 5M checkpoint

固定 Hugging Face revision：

<code>ded10a5a17b1d2433115961b2fd5813db07316ee</code>

下载命令：

~~~bash
cd "$REPO_ROOT"
mkdir -p pretrained/crafter_5m

curl -fL --retry 3 -o pretrained/crafter_5m/last.pt 'https://huggingface.co/vmicheli/delta-iris/resolve/ded10a5a17b1d2433115961b2fd5813db07316ee/last.pt?download=true'
~~~

文件验证：

| 检查 | 实测值 |
|---|---|
| 文件大小 | 99,875,046 bytes |
| SHA256 | <code>1d45e9496e2b97c1e59327d4f3e7f356baf04d74b1b5f0c1861c3232dc8aaf3d</code> |
| state dict 项数 | 434 |
| strict load | 通过 |
| 浮点 tensor | 全部 finite |

实际验证命令：

~~~bash
cd "$REPO_ROOT"
"$PYTHON_BIN" repro/verify_pretrained.py
~~~

关键输出：

~~~text
state_dict_keys=434 strict_load=ok
greedy_action=5 value=11.399431
world_model_step=ok
frames=(1, 1, 3, 64, 64)
sequence=(1, 4, 512)
done=[False]
~~~

### 4.7 正式 Crafter 名义 5M 长训

正式脚本：

<code>repro/train_crafter_5m.sh</code>

主要配置：

| 参数 | 值 |
|---|---:|
| seed | 0 |
| epochs | 491 |
| train envs | 16 |
| test envs | 32 |
| 首轮采样 | 名义 100,000 |
| 后续每轮采样 | 名义 10,000 |
| W&B | disabled |
| device | cuda:0 |

名义帧预算：

~~~text
100,000 + 490 × 10,000 = 5,000,000
~~~

16 个并行环境可能在单轮多采最多 15 steps；源码会把 excess 从下一轮扣除。因此应写“名义 5M 预算”，最终实际步数以 dataset 的 <code>num_steps</code> 为准。

正式包提供可移植 tmux 启动器；它会自动定位仓库根，并允许通过环境变量覆盖 Python、GPU、数据根、run 目录和日志路径：

~~~bash
cd "$REPO_ROOT"
eval "$(./repro/launch_crafter_5m_tmux.sh)"
~~~

启动后会在当前 shell 中导出：

~~~text
REPO_ROOT
PYTHON_BIN
DELTA_IRIS_DATA_ROOT
RUN_DIR
LOG_FILE
SESSION_NAME
~~~

需要自定义数据位置时，由目标机器或作业调度器预先提供 <code>DELTA_IRIS_DATA_ROOT</code>，启动命令本身无需修改。

## 5. 复现结果

### 5.1 Smoke 结果

| 项目 | Crafter | Atari Breakout |
|---|---:|---:|
| epoch | 1 | 1 |
| 实际 steps | 64 | 64 |
| dataset segments | 1 | 3 |
| segment lengths | 64 | 30 / 25 / 9 |
| tokenizer optimizer step | 1 | 1 |
| world model optimizer step | 1 | 1 |
| actor-critic optimizer step | 1 | 1 |
| last.pt | 99,851,116 B | 59,920,620 B |
| optimizer.pt | 169,128,333 B | 90,311,949 B |
| 状态 | 通过 | 通过 |

Crafter smoke 参数量：

| 组件 | 参数量 |
|---|---:|
| tokenizer | 5,409,611 |
| world model | 11,948,457 |
| actor-critic | 7,490,432 |
| 合计 | 24,848,500 |

### 5.2 正式长训的持久化结果

本报告纳入的稳定 durable checkpoint 快照：

| 项目 | 实测值 |
|---|---:|
| epoch.pt | 27 |
| dataset steps | 360,006 |
| episodes/segments | 2,032 |
| tokenizer 累计 optimizer step | 18,000 |
| world model 累计 optimizer step | 15,500 |
| actor-critic 累计 optimizer step | 13,500 |
| 名义 5M 进度 | 7.20% |
| run folder | 约 6.6 GiB |
| train dataset | 约 6.3 GiB |

本报告计入的稳定结果止于 epoch 27 checkpoint。checkpoint 之后尚未持久化的计算不计入复现结果；静态 Markdown 也不用于判断任务当前是否仍在运行。

![长训进度](repro/report_assets/training_progress_snapshot.png)

*图 5：checkpoint 27 对应的稳定参考快照。重新运行时应从自己的 <code>$RUN_DIR</code> 读取最新值。*

### 5.3 实测训练耗时

Epoch 1：

| 阶段 | 工作量 | 实测耗时 | 实测速度 |
|---|---:|---:|---:|
| collection | 100,007 steps | 02:55 | 570.83 step/s |
| tokenizer | 5,000 updates | 22:30 | 3.70 update/s |
| world model | 2,500 updates | 03:56 | 10.56 update/s |
| actor-critic | 500 updates | 05:52 | 1.42 update/s |

Epoch 2：

| 阶段 | 工作量 | 实测耗时 | 实测速度 |
|---|---:|---:|---:|
| collection | 9,999 steps | 00:19 | 504.25 step/s |
| tokenizer | 500 updates | 02:15 | 3.68 update/s |
| world model | 500 updates | 00:48 | 10.39 update/s |
| actor-critic | 500 updates | 05:55 | 1.41 update/s |

![首轮耗时](repro/report_assets/epoch1_stage_times.png)

*图 6：首轮包含 100k 随机预填充和额外的 tokenizer/world-model 更新，因此不能直接当作稳态 epoch。*

![阶段耗时对比](repro/report_assets/epoch_stage_comparison.png)

*图 7：epoch 1 与 epoch 2 的实测阶段耗时。稳态训练中 actor-critic 是主要耗时之一。*

### 5.4 早期采样行为

Epoch 1 在 Collector 源码中强制 <code>epsilon=1</code>，所以动作近似均匀随机。

Epoch 2 新增 9,999 个动作中：

- <code>do</code>：7,851 次，78.518%。
- <code>place_plant</code>：1,824 次，18.242%。
- 其余动作占比较低。

![动作分布变化](repro/report_assets/action_distribution_shift.png)

*图 8：动作分布已由随机预填充转为高度非均匀，只能说明策略行为发生变化，不能作为最终性能证明。*

参考快照中保存的最佳真实环境训练轨迹：

- 保存于 epoch 27。
- 320 frames。
- episode return 9.1。
- 它来自训练采集，不是正式 evaluation。

![最佳真实轨迹](repro/report_assets/formal_best_episode_events.png)

*图 9：参考 checkpoint 保存的真实环境训练轨迹；从全部非零奖励事件中均匀选取十个时刻。*

### 5.5 官方 checkpoint 的视觉验证

验证轨迹：

~~~text
Crafter seed = 0
history actions = [left, up, right, down, left]
target action = up
history observations = (1, 6, 3, 64, 64)
history actions = (1, 5)
~~~

![上下文序列](repro/report_assets/context_sequence.png)

*图 10：用于 tokenizer/world-model 单步比较的真实 Crafter 上下文。*

每个 transition 被编码成 4 个 Δ-token，每个 token 的 codebook 大小为 1024。

![Delta token](repro/report_assets/delta_token_ids.png)

*图 11：六个 transition 的四个离散 Δ-token ID。相同动作/相近上下文可以得到重复 token 组合。*

#### Tokenizer 条件重建

单个固定样本：

| 指标 | 值 |
|---|---:|
| MAE | 0.00043786 |
| PSNR | 57.5892 dB |

![Tokenizer 重建](repro/report_assets/tokenizer_reconstruction.png)

*图 12：Tokenizer 条件重建。编码器输入包含真实下一帧，因此这是量化/解码重建，不是未来预测。*

#### World model 单步想象

同一固定上下文、同一动作，生成时不输入真实下一帧：

| 指标 | 值 |
|---|---:|
| MAE | 0.00358743 |
| PSNR | 30.4654 dB |
| 输出 frame | (1, 1, 3, 64, 64) |
| WM sequence | (1, 4, 512) |

![World model 单步](repro/report_assets/world_model_prediction.png)

*图 13：世界模型单步想象与真实下一帧。误差主要集中在具有随机性的实体位置。*

![重建与想象总览](repro/report_assets/model_visual_comparison.png)

*图 14：同一 transition 上的真实帧、tokenizer 重建与 world-model 想象总览。*

WorldModelEnv 内部使用分类分布采样 Δ-token 和 done，因此相同历史/动作可生成不同结果：

![随机样本](repro/report_assets/world_model_stochastic_samples.png)

*图 15：八个随机种子的单步世界模型样本。该图展示的是模型的随机生成分布，不应只挑最好的一张报告。*

## 6. 复现遇到的坑

| 坑 | 表现或原因 | 解决办法 |
|---|---|---|
| 仓库代际混淆 | 已有旧目录可能是原版 IRIS，而不是 Δ-IRIS | 单独克隆 <code>vmicheli/delta-iris</code>，固定 commit |
| Gym 0.21 安装失败 | 新版 setuptools 拒绝旧 Gym 的 metadata | 固定 pip 23.0、setuptools 65.5.0、wheel 0.38.4 |
| Python 版本过新 | Gym/pygame/ale-py 对新 Python wheel 支持差 | 使用 Python 3.9.23 隔离环境 |
| Atari ROM 许可 | accept-rom-license 会下载 ROM | 仅在确认拥有 ROM 使用许可时安装 |
| W&B 默认联网 | 官方配置默认 online，可能卡登录/网络 | 所有自动测试和长训设置 <code>wandb.mode=disabled</code> |
| Hydra 输出目录随机 | 默认按日期时间生成，不便恢复和自动化 | smoke 自动带时间戳；正式长训显式指定 run dir |
| 输出目录覆盖 | 重跑可能覆盖 checkpoint 和 dataset | 正式脚本在目录存在时拒绝启动 |
| CUDA 编号重映射 | 设置 CUDA_VISIBLE_DEVICES 后物理编号会变化 | 暴露目标物理 GPU，程序内部仍用 cuda:0 |
| 普通 nohup 未持久 | 当前执行环境结束后后台进程被回收 | 使用 detached tmux session |
| resume 工作目录 | 脚本用相对路径读取 config/checkpoint | 必须 cd 到具体 run folder 后执行 |
| resume 不能并发 | 原任务和 resume 会同时写 checkpoint/dataset | 只在原 PID/tmux 已停止后恢复 |
| epochs 含义 | common.epochs 是总目标，不是追加轮数 | 5M 恢复时仍保持总目标 491 |
| 5M 不一定严格等于实际帧 | 16 env 并行采样会小幅 overshoot | 写“名义 5M”，最终读 dataset num_steps |
| 早期 return 易误判 | epoch 1 强制随机，正式 eval 每 50 epochs | 不把 warm-up episode 当论文分数 |
| main.log 为空 | stdout/tqdm 被外层重定向 | 读取启动器导出的 <code>$LOG_FILE</code> |
| 数据盘快速增长 | 360k steps 已约 6.3 GiB dataset | 将 <code>$DELTA_IRIS_DATA_ROOT</code> 指向大容量卷；5M 至少预留约 100 GiB |
| Tokenizer 图被误称预测 | encoder 输入包含真实下一帧 | 明确标注“条件重建”，预测只看 WorldModelEnv.step |
| Quantizer 会静默改 codebook | train 模式下 no_grad 也会更新 buffer | 所有可视化前调用 tokenizer.eval() |
| WorldModel action 形状 | Tensor action [B] 不会自动 reshape | 必须使用 LongTensor [B, 1] |
| burn-in 对齐 | obs 和 act 时间长度不匹配会断言失败 | 必须满足 obs_T = act_T + 1 |
| num_actions 初始为 null | 直接实例化 checkpoint 模型会尺寸错误 | 实例化前写入 Crafter 的 17 |
| checkpoint 前缀 | 完整 Agent key 带 tokenizer./world_model. 等前缀 | 整体 strict load，或对子模型显式提取前缀 |
| GUI 依赖显示服务器 | play.sh 在纯 headless 环境可能打不开 | 自动检查使用 dummy SDL；交互播放需桌面/X 转发 |
| DataLoader 警告 | Torch 2.1 提示 sampler data_source 将废弃 | 当前只是 warning，不影响本次训练 |

## 7. 已检查的复现命令

### 7.1 状态总表

| 命令或脚本 | 检查方式 | 结果 |
|---|---|---|
| 源码 commit | git rev-parse HEAD | 通过 |
| 环境安装 | 实际安装 | 通过 |
| pip check | 实际执行 | 通过 |
| Crafter reset/step | 实际执行 | 通过 |
| Breakout reset/step | 实际执行 | 通过 |
| repro/smoke_crafter.sh | 本次再次实际执行 | 通过 |
| repro/smoke_atari.sh | 本次再次实际执行 | 通过 |
| smoke resume.sh | 本次再次实际执行 | 通过 |
| 下载与 sha256sum | 实际执行 | 通过 |
| repro/verify_pretrained.py | 实际执行 | 通过 |
| repro/generate_report_assets.py | 实际执行 | 通过，生成 16 张 PNG |
| repro/train_crafter_5m.sh | 实际执行 | 已产出多个 durable checkpoint |
| repro/launch_crafter_5m_tmux.sh | bash -n，并验证已有路径拒绝覆盖 | 通过 |
| tmux/ps/tail/nvidia-smi | 多次实际执行 | 通过 |
| 四个 repro shell 脚本 | bash -n | 通过 |
| 报告内全部 bash 代码块 | 提取后整体执行 bash -n | 通过 |
| 两个 repro Python 脚本 | py_compile | 通过 |
| requirements lock | 去除说明注释后与 pip freeze diff | 包版本行完全一致 |
| play.sh GUI | 仅 bash -n | 未做真实 GUI 交互 |
| Atari 600 epochs | 未执行 | 只有 smoke |
| Crafter 5M 完整结果 | 未完成 | 不在本报告已完成范围内 |

### 7.2 重新生成本报告图片

先指向待分析的 run；路径可以位于仓库内，也可以位于任意挂载卷：

~~~bash
cd "$REPO_ROOT"
export DELTA_IRIS_RUN_DIR="$RUN_DIR"
export DELTA_IRIS_LOG_FILE="$LOG_FILE"
MONITOR_GPU="${CUDA_VISIBLE_DEVICES:-0}"
DELTA_IRIS_MONITOR_GPU="${MONITOR_GPU%%,*}" \
  SDL_VIDEODRIVER=dummy MPLBACKEND=Agg \
  "$PYTHON_BIN" repro/generate_report_assets.py
~~~

脚本会：

- 校验官方 checkpoint 大小和 SHA256。
- 严格加载官方 Agent。
- 生成 tokenizer/world-model 真实可视化。
- 解析正式 launch log。
- 读取 durable checkpoint 和 dataset info。
- 读取 smoke dataset 与正式 episode。
- 查询 nvidia-smi、RAM 和磁盘。
- 生成报告中的全部 PNG。

### 7.3 监控长训

~~~bash
tmux list-panes -t "$SESSION_NAME" -F 'pid=#{pane_pid} command=#{pane_current_command} dead=#{pane_dead}'
tail -f "$LOG_FILE"
nvidia-smi
~~~

进入 tmux：

~~~bash
tmux attach -t "$SESSION_NAME"
~~~

不停止训练地退出 tmux：按 <code>Ctrl-b</code>，再按 <code>d</code>。

### 7.4 正式长训恢复命令

不要并发执行 resume。只有确认同名 tmux session 不存在后，才执行：

~~~bash
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "Training session is still running; refusing concurrent resume." >&2
  exit 1
fi
cd "$RUN_DIR"
"$PYTHON_BIN" src/main.py params.common.resume=True hydra.output_subdir=null hydra.run.dir=.
~~~

该命令已通过 Crafter smoke 的完整恢复验证；正式目录未故意中断测试。

## 8. 产物与证据索引

![产物布局](repro/report_assets/artifact_layout.png)

*图 16：smoke、预训练参考权重和正式长训分开保存，避免相互覆盖。*

| 内容 | 路径 |
|---|---|
| 代码仓库 | <code>$REPO_ROOT</code> |
| Python 环境 | <code>$CONDA_PREFIX</code> |
| 精确依赖锁 | <code>$REPO_ROOT/repro/requirements-lock-py39.txt</code> |
| Crafter smoke | <code>$REPO_ROOT/outputs/smoke_crafter_*</code> |
| Atari smoke | <code>$REPO_ROOT/outputs/smoke_atari_*</code> |
| 官方 checkpoint | <code>$REPO_ROOT/pretrained/crafter_5m/last.pt</code> |
| 预训练验证脚本 | <code>$REPO_ROOT/repro/verify_pretrained.py</code> |
| 图片生成脚本 | <code>$REPO_ROOT/repro/generate_report_assets.py</code> |
| 报告图片 | <code>$REPO_ROOT/repro/report_assets/</code> |
| 正式 run | <code>$RUN_DIR</code> |
| 正式 launch log | <code>$LOG_FILE</code> |
| 正式配置快照 | <code>$RUN_DIR/config/trainer.yaml</code> |

## 9. 最终边界声明

本报告已经验证：

- 环境兼容性。
- 数据采集与持久化。
- 上下文 tokenizer 的训练和重建。
- autoregressive world model 的训练、burn-in 和随机想象。
- 想象中的 actor-critic 更新。
- checkpoint 与完整恢复链路。
- 官方预训练权重的文件完整性和推理能力。
- scratch 正式训练已经持续产出多个 durable epochs。

本报告尚未验证：

- scratch 5M 最终 checkpoint。
- epoch 50 及之后的正式 Crafter evaluation。
- 论文表格中的最终均值和标准差。
- Atari 600 epochs 最终成绩。
- pygame 的真实交互式 GUI 播放。

后续判断“论文性能复现成功”的条件应为：

1. 正式 run 完成名义 5M 环境预算。
2. 使用最终 checkpoint 运行足够数量的 Crafter test episodes。
3. 按论文定义计算 Crafter score，而不是使用单条 episode return。
4. 使用多个 seed 时报告均值、方差和原始 per-seed 数据。
