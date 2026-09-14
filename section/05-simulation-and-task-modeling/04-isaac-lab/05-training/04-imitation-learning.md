# 模仿学习与官方示例

模仿学习不是从 reward 里试错，而是从示教轨迹里学习动作。对于抓取、堆叠、倒料、装配这类操作任务，奖励函数往往很难写；此时让人或脚本先做出成功示范，再训练策略去复现这些动作，是更直接的路线。

Isaac Lab 官方已经提供了对应示例。代码主要分成三组：

| 代码入口 | 作用 |
|---|---|
| `scripts/tools/record_demos.py` | 用遥操作采集示教，保存为 HDF5 数据集 |
| `scripts/tools/replay_demos.py` | 回放数据集，检查轨迹是否可复现 |
| `scripts/imitation_learning/isaaclab_mimic/annotate_demos.py` | 给示教轨迹标注子任务边界 |
| `scripts/imitation_learning/isaaclab_mimic/generate_dataset.py` | 基于少量示教自动生成更多轨迹 |
| `scripts/imitation_learning/isaaclab_mimic/consolidated_demo.py` | 一边遥操作，一边实时生成 Mimic 数据 |
| `scripts/imitation_learning/robomimic/train.py` | 用 robomimic 训练行为克隆策略 |
| `scripts/imitation_learning/robomimic/play.py` | 加载训练好的 robomimic checkpoint 并在环境中回放 |
| `scripts/imitation_learning/robomimic/robust_eval.py` | 对视觉策略做多设置鲁棒性评估 |

## 本节目标

本节围绕下面几个问题展开：

1. 模仿学习的官方代码入口有哪些（record / replay / mimic / robomimic）？
2. 一条最小链路是什么（采集示教 → 标注 → 生成数据 → 训练 → 回放评估）？
3. 视觉策略怎么用 Isaac Lab Mimic 生成数据、用 robomimic 训 BC-RNN？
4. 回放和鲁棒性评估怎么做，数据质量要检查什么？

## 官方流程

模仿学习的最小链路如下：

```text
遥操作或已有示教
  -> HDF5 dataset
  -> 子任务标注
  -> Mimic 生成更多轨迹
  -> robomimic 训练 BC / BC-RNN
  -> play.py 回放评估
```

其中 `record_demos.py` 和 `replay_demos.py` 属于通用数据工具；`isaaclab_mimic` 负责把少量示教扩展成更多可训练轨迹；`robomimic` 负责从 HDF5 数据集中训练策略。

## 采集与回放示教

在正式记录数据集之前，可以先用遥操作脚本确认任务和输入设备能正常启动：

```bash
./isaaclab.sh -p scripts/environments/teleoperation/teleop_se3_agent.py \
    --task Isaac-Lift-Cube-Franka-IK-Rel-v0 \
    --teleop_device keyboard \
    --num_envs 1
```

运行后终端会打印 Isaac Sim / Isaac Lab 的启动信息、任务加载信息，以及键盘遥操作的控制说明：

![Isaac Lab 遥操作 Lift Cube 任务启动输出](/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-teleop-lift-output.png)

如果本地暂时无法稳定采集遥操作数据，可以直接使用官方预录数据集。Isaac Lab 官方文档提供了 `Isaac-Stack-Cube-Franka-IK-Rel-v0` 的 10 条人类示教，文件名为 `dataset.hdf5`：

```bash
mkdir -p datasets

curl -L "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/IsaacLab/Mimic/franka_stack_datasets/dataset.hdf5" \
    -o ./datasets/dataset.hdf5
```

下载后的数据集可以直接作为后续 `annotate_demos.py` 的输入。该文件是 HDF5 格式，根节点下包含 `data/`，其中有 10 条 `demo_*` 示教轨迹；每条轨迹包含 `actions`、`states`、`initial_state` 和 `obs` 等字段。

以 Franka 堆叠方块任务为例，先创建数据目录，然后采集 10 条成功示教：

```bash
mkdir -p datasets

./isaaclab.sh -p scripts/tools/record_demos.py \
    --task Isaac-Stack-Cube-Franka-IK-Rel-v0 \
    --device cpu \
    --teleop_device keyboard \
    --dataset_file ./datasets/dataset.hdf5 \
    --num_demos 10
```

`--teleop_device` 可换成 `spacemouse` 或任务配置中支持的其他输入设备。键盘可以跑通流程；如果要采集更平滑的 6D 末端运动，SpaceMouse 通常更适合。

采集完成后先回放：

```bash
./isaaclab.sh -p scripts/tools/replay_demos.py \
    --task Isaac-Stack-Cube-Franka-IK-Rel-v0 \
    --device cpu \
    --dataset_file ./datasets/dataset.hdf5 \
    --validate_success_rate
```

`replay_demos.py` 的作用是把 HDF5 里的状态和动作重新送回环境，并用任务的成功判据验证轨迹是否可复现。它不会自动导出 mp4；可视化结果出现在 Isaac Sim 窗口中，终端输出的是回放进度和成功率检查。

在无窗口服务器上，官方 `replay_demos.py` 可能因为键盘/窗口接口初始化失败。课程里提供一个无键盘依赖的检查脚本，只做数据集 replay 和成功率统计：

```bash
./isaaclab.sh -p labs/06_isaac_lab/replay_demos_headless.py \
    --dataset_file datasets/dataset.hdf5 \
    --select_episodes 0 \
    --validate_success_rate \
    --headless
```

它适合 CI 或无显示服务器验证数据通路；如果你要肉眼观察轨迹，再使用官方交互式 replay 或 `xvfb-run`。

<video src="/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-task-stack.mp4" controls muted loop playsinline style="max-width:100%;height:auto;display:block;margin:0.75em 0"></video>

上面的视频展示的是 Franka 方块堆叠任务的策略效果。对数据集而言，回放这一步不是形式检查，而是确认数据集里的状态、动作和任务成功判据能在环境中重新走通。失败轨迹、误操作轨迹、过长停顿都会直接降低后续策略质量。

## 用 Isaac Lab Mimic 生成更多数据

少量人工示教通常不够训练稳定策略。Isaac Lab Mimic 的作用，是根据示教中的子任务结构生成更多变体。对于堆叠任务，流程先标注，再生成。

本页只走视觉策略路线：启用相机，使用视觉版本的 Mimic 任务，让生成的数据直接服务后面的 visuomotor BC-RNN 训练。视觉任务会初始化渲染管线，命令行里看到 `Completed setting up the environment...` 只表示环境已经创建完成，还没有进入逐条示教标注；继续运行后应当出现 `Annotating episode #...`。

```bash
./isaaclab.sh -p scripts/imitation_learning/isaaclab_mimic/annotate_demos.py \
    --headless \
    --enable_cameras \
    --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-Mimic-v0 \
    --auto \
    --input_file ./datasets/dataset.hdf5 \
    --output_file ./datasets/annotated_dataset.hdf5
```

下面是使用 `--headless` 后继续进入 episode 标注流程的终端输出：

![Isaac Lab Mimic headless 标注输出](/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-mimic-annotate-headless-output.png)

如果长时间停在 `Completed setting up the environment...` 之后没有继续打印 episode 信息，通常是相机渲染初始化太慢或图形界面占用了额外资源。先使用 `--headless` 跑标注，需要肉眼确认标注质量时，再去掉 `--headless` 在 GUI 里抽查少量 episode。

生成数据时，`annotate_demos.py` 的 `--output_file` 会作为 `generate_dataset.py` 的 `--input_file`：

```bash
./isaaclab.sh -p scripts/imitation_learning/isaaclab_mimic/generate_dataset.py \
    --headless \
    --enable_cameras \
    --num_envs 10 \
    --generation_num_trials 1000 \
    --input_file ./datasets/annotated_dataset.hdf5 \
    --output_file ./datasets/generated_dataset.hdf5
```

下面是 `generate_dataset.py` 开始生成 Mimic 数据集时的终端输出：

![Isaac Lab Mimic 生成数据集输出](/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-mimic-generate-dataset-output.png)

`--generation_num_trials` 表示尝试生成的轨迹数量；最终可用轨迹数量取决于任务是否成功、子任务边界是否合理、场景随机化是否过强。

## 训练 robomimic 策略

Isaac Lab 的任务注册里带有 robomimic 配置入口。这里继续沿用视觉路线：`Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0` 对应图像输入配置，训练时指定任务、算法和生成数据集即可。

```bash
./isaaclab.sh -p scripts/imitation_learning/robomimic/train.py \
    --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0 \
    --algo bc \
    --dataset ./datasets/generated_dataset.hdf5 \
    --name bc_rnn_image_franka_stack
```

训练启动后，终端会打印 robomimic 配置、数据集信息、观测键、训练轮次和日志目录：

![Isaac Lab robomimic 训练输出](/section/05-simulation-and-task-modeling/04-isaac-lab/assets/isaac-lab-robomimic-train-output.png)

训练日志和模型默认保存在 `logs/robomimic/` 下。`--epochs` 可以覆盖配置文件里的训练轮数，`--normalize_training_actions` 可用于动作归一化训练。

## 回放与评估

训练完成后，用 `play.py` 加载 checkpoint。视觉策略回放必须启用相机：

```bash
./isaaclab.sh -p scripts/imitation_learning/robomimic/play.py \
    --headless \
    --enable_cameras \
    --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0 \
    --checkpoint logs/robomimic/Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0/bc_rnn_image_franka_stack/<run>/models/model_best.pth \
    --horizon 400 \
    --num_rollouts 1
```

如果暂时不想等待完整训练，可以直接下载 NVIDIA 官方提供的 robomimic visuomotor checkpoint 进行回放。这个 checkpoint 来自 Hugging Face 数据集 `nvidia/PhysicalAI-Robotics-Manipulation-Augmented`，对应 Franka Stack 的 Mimic 1k 视觉策略：

```bash
mkdir -p logs/robomimic/official/franka_stack_mimic_1k_table_only

curl -L \
    "https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-Manipulation-Augmented/resolve/main/robomimic_bc_rnn_visuomotor_models/franka_stack_mimic_1k_table_only/20250416141542/models/model_epoch_600.pth?download=true" \
    -o logs/robomimic/official/franka_stack_mimic_1k_table_only/model_epoch_600.pth
```

下载后可用下面的命令回放：

```bash
./isaaclab.sh -p scripts/imitation_learning/robomimic/play.py \
    --headless \
    --enable_cameras \
    --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0 \
    --checkpoint logs/robomimic/official/franka_stack_mimic_1k_table_only/model_epoch_600.pth \
    --horizon 400 \
    --num_rollouts 1
```

该 checkpoint 的示教来源是 Mimic 数据，但回放时使用普通视觉策略环境 `Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0`。Mimic 环境负责生成数据，策略环境负责加载 checkpoint 并执行策略。从目录名 `table_only` 可知该模型只用桌面相机（观测键为 `eef_pos`、`eef_quat`、`gripper_pos` 和 `table_cam`，以 checkpoint 内的 config 为准），因此回放时需要保持任务和相机输入一致。

回放阶段如果看到 `torchvision` 关于 `pretrained` / `weights` 的 warning，它只是版本兼容提示，不是运行失败。视觉策略第一次加载 ResNet、相机和渲染管线会比较慢；先用 `--num_rollouts 1` 和 `--horizon 400` 验证 checkpoint 能加载、环境能创建、策略能完成一次推理闭环。

单次 rollout 的结果不能代表策略质量。出现下面这种输出，说明流程已经跑通，但这一条轨迹没有成功：

```text
[INFO] Trial 0: False

Successful trials: 0, out of 1 trials
Success rate: 0.0
Trial Results: [False]
```

正式评估时应增加 rollout 数量，并比较多个 checkpoint epoch：

```bash
./isaaclab.sh -p scripts/imitation_learning/robomimic/play.py \
    --headless \
    --enable_cameras \
    --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0 \
    --checkpoint logs/robomimic/official/franka_stack_mimic_1k_table_only/model_epoch_600.pth \
    --horizon 800 \
    --num_rollouts 50
```

视觉策略如果需要比较光照、纹理、背景扰动，可使用 `robust_eval.py`：

```bash
./isaaclab.sh -p scripts/imitation_learning/robomimic/robust_eval.py \
    --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0 \
    --input_dir logs/robomimic/Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0/bc_rnn_image_franka_stack/<run>/models \
    --horizon 400 \
    --num_rollouts 15
```

普通回放看的是“能不能完成任务”；鲁棒性评估看的是“换光照、换材质、换背景后还能不能完成任务”。这也是视觉模仿学习比低维状态模仿学习更容易暴露问题的地方。

## 官方任务示例

官方示例中常见的模仿学习任务包括：

| 任务 | 用途 |
|---|---|
| `Isaac-Stack-Cube-Franka-IK-Rel-v0` | 官方预录示教的数据来源任务 |
| `Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0` | 图像输入策略训练环境 |
| `Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-Mimic-v0` | 图像输入的 Mimic 数据生成环境 |
| `Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-Cosmos-v0` | 面向视觉增强和鲁棒性评估的策略环境 |
| `Isaac-Stack-Cube-Bin-Franka-IK-Rel-Mimic-v0` | bin cube stacking 的 Mimic 示例 |
| `Isaac-NutPour-GR1T2-Pink-IK-Abs-v0` | GR1T2 倒料视觉模仿任务 |
| `Isaac-ExhaustPipe-GR1T2-Pink-IK-Abs-v0` | GR1T2 exhaust pipe 视觉模仿任务 |

教材中先用 Franka 堆叠任务，因为它把动作空间、示教采集、Mimic 生成、robomimic 训练串得最清楚。掌握这条视觉模仿学习链路后，再换成 GR1T2、G1 或其他操作任务，本质上是换任务配置、观测键和数据规模。

## 数据质量检查

训练前至少检查五件事：

```text
[ ] 示教是否成功完成任务
[ ] 轨迹是否短而连续
[ ] action 维度是否和环境动作空间一致
[ ] observation 键名是否和 robomimic 配置一致
[ ] 视觉数据是否启用了相机，且图像没有严重遮挡
```

模仿学习会认真学习数据里的行为。示教轨迹越干净，BC 策略越容易稳定；示教里混入失败、停顿和无意义动作，策略也会把这些模式学进去。

## HDF5 回放闭环

使用官方 HDF5 示例数据时，不要只验证“文件下载完成”。更可靠的验收顺序是：先检查 HDF5 结构，再运行 Mimic annotation，最后用一条 demo 做 headless replay。

| 验收点 | 预期现象 | 排错提示 |
|---|---|---|
| HDF5 下载 | 文件存在，能被 `h5py` 打开 | 数据集应放在仓库外或被忽略的目录，避免误提交 |
| HDF5 结构检查 | 能看到 demo 数量、task 名和 action / observation 键 | task 名必须和 replay / annotation 命令一致 |
| `annotate_demos.py --auto` | 输出新的 annotated HDF5，并包含 `processed_actions` | 若找不到 episode 或 action 键，先查数据集 schema |
| 单条 demo replay | 能打印 replay episode、action 数量和 success 状态 | 远程或 CI 环境可用无键盘 headless replay；肉眼检查再开 GUI 或视频 |

示例输出应类似：

```text
dataset.hdf5: 10 demos
task: Isaac-Stack-Cube-Franka-IK-Rel-v0
annotated_dataset.hdf5: contains processed_actions
Replayed episode #0 (...) with 236 actions; success=True
Successfully replayed: 1/1
```

`teleop_se3_agent.py` 和 `record_demos.py` 需要键盘、手柄或 3D 输入设备参与，不适合写成无人值守的自动化验收。完整 robomimic 训练、官方大 checkpoint 回放和鲁棒性评估会占用更长 GPU 时间和大量模型文件，建议单独保存命令、日志、checkpoint 路径和评估结果。

## 参考

- Isaac Lab 官方文档：[Teleoperation and Imitation Learning with Isaac Lab Mimic](https://isaac-sim.github.io/IsaacLab/main/source/overview/imitation-learning/teleop_imitation.html)
- Isaac Lab 官方文档：[Augmented Imitation Learning with Isaac Lab Mimic and Cosmos](https://isaac-sim.github.io/IsaacLab/main/source/overview/imitation-learning/augmented_imitation.html)
- robomimic 项目文档：[robomimic](https://robomimic.github.io/)

## 导航

- 上一页：[训练库对接](03-rl-libraries.md)
- 返回目录：[训练与评测](../05-training.md)
- 下一页：[域随机化](05-domain-randomization.md)
