# 数据集

MIKASA-Robo-VLA 发布了 22500 条轨迹（每任务 250 条 × 90 个任务）、超过 6,000,000 个 timestep，提供三种可互转的格式，托管在 Hugging Face，也可本地采集。

## 三种格式

| 格式 | 随机访问 | 框架 | 适合 |
|---|---|---|---|
| NPZ（原始 episode） | 否（顺序） | NumPy / PyTorch | 查看原始采集输出、自定义预处理 |
| RLDS / TFDS | 是 | TensorFlow、JAX、Open-X 管线 | Open X-Embodiment 式 VLA 训练 |
| LeRobotDataset v3 | 是 | PyTorch、HuggingFace | LeRobot 模仿学习、现代 VLA 微调（OpenVLA-OFT、π0.5） |

多数用户从 LeRobotDataset v3 起步：图像以 MP4 存储、本体感知与动作以 Parquet 存储，随机访问快，兼容主流 VLA 训练框架。转换链是 NPZ → RLDS / TFDS → LeRobotDataset v3。

## 每步信号

每一行存的信号与在线 wrapped 环境一致：`rgb`（`[T, 128, 128, 6]` uint8，两相机沿通道拼接）、`proprio`（`[T, 7]` float32，绝对末端位姿加夹爪开度）、`action`（`[T, 7]` float32，归一化 `pd_ee_delta_pose`，范围 `[-1, 1]`）、`reward`、`success`，以及自然语言 `language_instruction`。因为与在线观测逐字节对齐，数据集上训练的模型无需 reshape 即可评测。

## Hugging Face 与下载

全部 90 个任务托管在两个仓库，每个任务是一个独立数据集仓库，可只下需要的分档：

- RLDS：`mikasa-robo/mikasa-robo-vla-rlds`
- LeRobotDataset v3：`mikasa-robo/mikasa-robo-vla-lerobot`

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="mikasa-robo/mikasa-robo-vla-lerobot",
    repo_type="dataset",
    allow_patterns="RememberColor3-VLA-v0/**",
    local_dir="data_mikasa_robo/data_lerobot",
)
```

按分档批量下载时，从分号分隔的 `mikasa_robo_vla_envs.csv` 里筛出对应 `Horizon Split` 的任务名再逐个 `snapshot_download`。

## 自采集

按任务 `Data Source` 选采集器，两者都输出统一布局的 NPZ，`--num-train-data` 默认 250。

PPO oracle 采集器 `get_mikasa_robo_datasets.py` 从 `oracle_checkpoints/` 找该任务的 `final_success_ckpt.pt`，同时开两个环境：一个 `state` 模式喂 oracle 策略拿动作，一个 `rgb` 模式记录图像与 proprio。它按批并行采集（默认每批 10 条），只有整批全部成功才保留、否则整批丢弃重采，且每条轨迹长度要不小于 10 步；seed 按批次确定性递增。这条路适合 PPO 能稳定求解的短程任务。

运动规划采集器 `get_mikasa_robo_datasets_motion_planning.py` 走三阶段子进程管线：先用任务对应的 `motion_planning_*.py` 规划出一条轨迹，再用 ManiSkill 的 `replay_trajectory` 把它转成 `pd_ee_delta_pose` 控制模式，最后在 `rgb` 环境里重放并录制。逐条判定成功，不成功就丢弃、`attempted += 1`，直到集满 `--num-train-data` 或用尽 `--max-attempts`（默认 5000）；支持从已存在的 `train_data_*.npz` 与日志里的 seed 推断续跑。这条路适合 PPO 不收敛的多阶段任务。

## NPZ 布局

每条 episode 一个 `.npz`，键包括 `rgb`、`proprio`、`action`、`reward`、`success`、`done`、`language_instruction`、`success_once`、`episode_length`、`episode_seed`。目录布局：

```text
data_mikasa_robo/data_npz/<dataset_name>/
    train_data_0.npz … train_data_{N-1}.npz
    metadata.json      # env_id、num_episodes、episode_lengths、success_once、reward_sums、episode_seeds 等
```

## 目录命名

每个任务的数据集目录名由 `env_id_to_dataset_name` 把环境 ID 从 CamelCase 转成 snake_case 得到，`v0` 保持不动、字母与数字之间断开，例如 `RememberShapeAndColor3x2-Long-VLA-v0` 变成 `remember_shape_and_color_3x2_long_vla_v0`、`BatteriesCheckerHard-3-VLA-v0` 变成 `batteries_checker_hard_3_vla_v0`。三种格式、下载筛选、HF 仓库都用这个名字定位任务。

## LeRobotDataset v3 布局

LeRobotDataset v3 版本每个任务一个目录，分三部分：`data/` 存 Parquet（`proprio`、`action`、`reward`、`success` 等低维信号），`meta/` 存 `info.json`、`stats.json`、`tasks.jsonl`、`episodes.jsonl`，`videos/` 把两路图像各存成 MP4（`observation.image` 与 `observation.wrist_image`）。图像走视频编码、低维信号走 Parquet，随机访问快，直接对接 LeRobot 的模仿学习与现代 VLA 微调。

三种格式经一条转换链得到：NPZ 先转成 RLDS / TFDS，再转成 LeRobotDataset v3，转换脚本在 `utils/convert_npz_to_rlds/` 与 `utils/convert_rlds_to_lerobot/`。

## 导航

- 返回上级：[MIKASA-Robo-VLA](../01-mikasa.md)
- 上一节：[评测协议与指标](07-evaluation-protocol.md)
- 下一节：[基线与记忆瓶颈证据](09-baselines-and-memory-bottleneck.md)
