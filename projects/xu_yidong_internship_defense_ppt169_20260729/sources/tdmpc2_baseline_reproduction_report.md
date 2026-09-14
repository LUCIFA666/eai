# tdmpc2_baseline_reproduction_report

# TD-MPC2 Baseline复现报告

环境配置、踩坑记录、验证结果与核心源码走读 xuyidong 2026-07-05 **Abstract** 本文记录在A100服务器上复现TD-MPC2 baseline的过程。复现目标是先跑通官方TD- MPC2的dog-runbaseline，包括仓库克隆、依赖环境、MuJoCo/DMControl验证、官方checkpoint 评估、短步数训练smoke test，以及后续正式复现实验命令。文档只覆盖原始baseline代码路径， 不讨论后续新增的Planner Distillation变体。

## 复现目标与代码位置 1

本次复现的baseline是TD-MPC2原始实现，任务为DMControl的dog-run。代码根目录为：

1/home/xuyidong/tdmpc2/tdmpc2 baseline只使用原始文件：

- train.py：训练入口。
- evaluate.py：评估入口。
- tdmpc2.py：TD-MPC2 agent，包括planning和update。
- common/world_model.py：encoder、dynamics、reward、policy prior、Q ensemble。
- common/buffer.py：TorchRL replay buffer。
- trainer/online_trainer.py：单任务在线RL训练循环。

## 硬件与软件环境 2

服务器检测结果如下：

项目 结果 8张NVIDIA A100-SXM4-80GB GPU 单卡显存 81920 MiB NVIDIA Driver

580. 159.03

系统CUDA显示

13. 0

Conda环境 tdmpc2 Python

3. 9.23

PyTorch

2. 6.0.dev20241112

MuJoCo Python

3. 1.2

CUDA可用 True 可见GPU数量 8 激活环境命令：

1

<!-- Page 2 -->

1source ~/miniforge3/etc/profile.d/conda.sh 2conda activate tdmpc2 3cd ~/tdmpc2/tdmpc2 4export MUJOCO_GL=egl 其中MUJOCO_GL=egl对无显示器服务器很重要，否则MuJoCo/DMControl渲染和环境初始化 可能出问题。

## 环境配置过程与遇到的坑 3

### 仓库克隆 3.1

最初在终端执行：

1git clone https://github.com/nicklashansen/tdmpc2 曾停在Cloning into 'tdmpc2'...。判断为服务器到GitHub连接握手阶段不稳定。重新发起 clone后成功，当前仓库位于：

1/home/xuyidong/tdmpc2

### Docker权限不可用 3.2

仓库推荐Docker，但当前用户不在docker组，直接运行docker ps报：

1permission denied while trying to connect to the docker API at unix:///var/run/docker.

sock sudo docker也需要密码。因此最后采用用户目录下的Miniforge + mamba方案，不依赖管理 员权限。

### Conda环境创建中的nightly包问题 3.3

仓库的docker/environment.yaml里包含：

1tensordict-nightly==2025.1.1 2torchrl-nightly==2025.1.1 其中torchrl-nightly==2025.1.1当前pip索引找不到，报错：

1ERROR: Could not find a version that satisfies the requirement torchrl-nightly==2025.1.1 2ERROR: No matching distribution found for torchrl-nightly==2025.1.1 解决办法是保留conda已创建出的tdmpc2环境，然后补装正式版：

1python -m pip install torchrl==0.6.0 tensordict==0.6.2 最终核心包可正常导入：

1python -c "import torch, mujoco, dm_control, tensordict, torchrl, kornia; print(torch.

__version__); print(torch.cuda.is_available())" 输出显示CUDA可用，且可见8张GPU。

### Hydra launcher缺失 3.4

原始config.yaml默认包含：

1defaults:

- override hydra/launcher: submitit_local

2 2

<!-- Page 3 -->

但环境里没有hydra-submitit-launcher时，直接运行会报：

1In 'hydra/config': Could not find 'hydra/launcher/submitit_local' 2Available options in 'hydra/launcher': basic 本次baseline复现统一在命令行显式覆盖：

1hydra/launcher=basic 这样不需要修改原始config.yaml。

### Hugging Face checkpoint下载超时 3.5

下载官方dog-run-1.pt时，wget曾连接Hugging Face超时，并留下0字节文件：

1Connecting to huggingface.co ... failed: Connection timed out.

解决方式是删除空文件后，用带重试的curl -L下载；最终checkpoint大小约32 MB：

1mkdir -p ~/tdmpc2/checkpoints 2curl -L --retry 5 --retry-delay 3 \ -o ~/tdmpc2/checkpoints/dog-run-1.pt \ 3 https://huggingface.co/nicklashansen/tdmpc2/resolve/main/dmcontrol/dog-run-1.pt 4 5ls -lh ~/tdmpc2/checkpoints/dog-run-1.pt

### 日志不刷新 3.6

使用nohup python train.py > log 2>&1 &时，日志长时间只有：

1nohup: ignoring input 原因是Python输出被缓冲。后续后台训练建议使用python -u：

1nohup python -u train.py ... > train.log 2>&1 &

### 为什么eval.csv一直是step 0 3.7

eval.csv不是训练进度条，只在评估时写入。如果设置：

1steps=10000 eval_freq=10000 则只会写两次：step=0和step=10000。中间训练步不会写入该CSV。

## Baseline配置 4

原始配置中的关键默认值如下：

1task: dog-run 2obs: state 3eval_episodes: 10 4eval_freq: 50000 5steps: 10_000_000 6batch_size: 256 7buffer_size: 1_000_000 8mpc: true 9iterations: 6 num_samples: 512 10 num_elites: 64 11 num_pi_trajs: 24 12 horizon: 3 13 model_size: ???

14 3

<!-- Page 4 -->

compile: true 15 save_video: true 16 seed: 1 17 Listing 1: config.yaml中的baseline关键配置 README中给dog-run的训练示例是：

1python train.py task=dog-run steps=7000000 因此正式复现建议至少使用700万环境步；本文中的1万步实验仅用于smoke test。

## 官方Checkpoint评估验证 5

下载官方checkpoint后，使用原始evaluate.py验证：

1cd ~/tdmpc2/tdmpc2 2export MUJOCO_GL=egl 3 4python evaluate.py \ hydra/launcher=basic \ 5 task=dog-run \ 6 model_size=5 \ 7 checkpoint=~/tdmpc2/checkpoints/dog-run-1.pt \ 8 eval_episodes=1 \ 9 save_video=true \ 10 compile=false 11 得到结果：

1Task: dog-run 2Model size: 5 3Checkpoint: /home/xuyidong/tdmpc2/checkpoints/dog-run-1.pt 4Episode length: 500 5Discount factor: 0.99 6Evaluating agent on dog-run:

dog-run R: 762.2 S: 0.00 7 视频输出：

1~/tdmpc2/tdmpc2/logs/dog-run/1/default/videos/dog-run-0.mp4 这说明baseline的环境、模型加载、planning、MuJoCo渲染链路均已跑通。

## Baseline训练Smoke Test 6

为了验证训练流程，运行了1万步baseline：

1CUDA_VISIBLE_DEVICES=0 nohup python -u train.py \ hydra/launcher=basic \ 2 task=dog-run \ 3 model_size=5 \ 4 steps=10000 \ 5 seed=1 \ 6 exp_name=baseline_10k_seed1 \ 7 eval_freq=10000 \ 8 save_video=false \ 9 enable_wandb=false \ 10 compile=false \ 11 > ~/tdmpc2/train_baseline_10k.log 2>&1 & 12 4

<!-- Page 5 -->

评估CSV为：

1step,episode_reward

20. 0,7.995296478271484
310000. 0,6.3938422203063965

Table 2: Baseline 1万步smoke test结果 Step Episode Reward 0

7. 9953

10000

6. 3938

该结果很低，属于正常现象：1万环境步对TD-MPC2的dog-run太短，只能验证训练流程可 运行，不能代表算法最终性能。

## Baseline 14万步训练曲线 7

除1万步smoke test外，还启动了一个计划30万步的baseline训练：

1CUDA_VISIBLE_DEVICES=0 nohup python -u train.py \ hydra/launcher=basic \ 2 task=dog-run \ 3 model_size=5 \ 4 steps=300000 \ 5 seed=1 \ 6 exp_name=baseline_300k_seed1 \ 7 eval_freq=1000 \ 8 eval_episodes=5 \ 9 save_video=false \ 10 enable_wandb=false \ 11 compile=false \ 12 > ~/tdmpc2/train_baseline_300k.log 2>&1 & 13 该实验的eval.csv当前记录到154000步，共155个评估点。每个评估点使用eval_episodes=5， 评估频率为每1000环境步一次。关键结果如下：

Table 3: Baseline 14万余步训练曲线摘要 指标 数值 最后记录步数 154000 最后记录reward

134. 0047

当前最高reward

157. 2973

最高reward对应步数 151000 评估点数量 155 从曲线看，baseline在约100k步后开始明显高于1万步smoke test的水平，154k步时reward 为134.0，当前最高点为151k步的157.3。这个结果已经比1万步更有参考意义，但仍不能替代 README推荐的700万步正式复现。

## 正式Baseline复现命令 8

正式复现实验建议使用README中的dog-run训练步数，即700万步：

1source ~/miniforge3/etc/profile.d/conda.sh 2conda activate tdmpc2 5

<!-- Page 6 -->

TD-MPC2 Baseline on dog-run

|bas|eline eval rew|ard|
|---|---|---|
|la<br>b|st: 154k, 134.<br>est: 151k, 157|0<br>.3|
150 Episode Reward 100 50 0 0 20 40 60 80 100 120 140 160 环境步数（千步） Figure 1: Baseline从0到154k环境步的评估reward曲线。该曲线说明训练已经超过14万步，并 且reward从初始约8提升到百级水平；但距离官方checkpoint的762.2仍有明显差距，说明仍属 于较早训练阶段。

3cd ~/tdmpc2/tdmpc2 4export MUJOCO_GL=egl 5 6CUDA_VISIBLE_DEVICES=0 nohup python -u train.py \ hydra/launcher=basic \ 7 task=dog-run \ 8 model_size=5 \ 9 steps=7000000 \ 10 seed=1 \ 11 exp_name=baseline_7m_seed1 \ 12 eval_freq=50000 \ 13 eval_episodes=10 \ 14 save_video=false \ 15 enable_wandb=false \ 16 compile=false \ 17 > ~/tdmpc2/train_baseline_7m_seed1.log 2>&1 & 18 输出位置：

1~/tdmpc2/tdmpc2/logs/dog-run/1/baseline_7m_seed1/ 评估曲线：

1~/tdmpc2/tdmpc2/logs/dog-run/1/baseline_7m_seed1/eval.csv 最终模型：

1~/tdmpc2/tdmpc2/logs/dog-run/1/baseline_7m_seed1/models/final.pt

## Baseline核心源码走读 9

### 训练入口：train.py 9.1

训练入口负责构建环境、agent、buffer和logger。关键逻辑位于train.py第52–60行：

1trainer_cls = OfflineTrainerifcfg.multitaskelseOnlineTrainer 6

<!-- Page 7 -->

2trainer = trainer_cls( cfg=cfg, 3 env=make_env(cfg), 4 agent=TDMPC2(cfg), 5 buffer=Buffer(cfg), 6 logger=Logger(cfg), 7

8. 

9trainer.train() Listing 2: train.py：构建trainer并启动训练 单任务dog-run会使用OnlineTrainer。

### Agent初始化：tdmpc2.py 9.2

原始TD-MPC2 agent固定使用当前进程可见的cuda:0。这也是为什么一个进程不会自动用8张 GPU；如果设置CUDA_VISIBLE_DEVICES=3，代码里的cuda:0会映射到物理GPU 3。

1self.device = torch.device('cuda:0') 2self.model = WorldModel(cfg).to(self.device) 3self.optim = torch.optim.Adam([ {'params': self.model._encoder.parameters(),'lr': self.cfg.lr*self.cfg.enc_lr_scale 4 }, {'params': self.model._dynamics.parameters()}, 5 {'params': self.model._reward.parameters()}, 6 {'params': self.model._termination.parameters()ifself.cfg.episodicelse[]}, 7 {'params': self.model._Qs.parameters()}, 8 {'params': self.model._task_emb.parameters()ifself.cfg.multitaskelse[]} 9 ], lr=self.cfg.lr, capturable=True) 10 self.pi_optim = torch.optim.Adam(self.model._pi.parameters(), lr=self.cfg.lr, eps=1e-5, 11 capturable=True) Listing 3: tdmpc2.py：agent初始化和优化器

### World Model：common/world_model.py 9.3

baseline的world model由encoder、dynamics、reward、policy prior和Q ensemble构成。关键逻 辑在common/world_model.py第25–32行：

1self._encoder = layers.enc(cfg) 2self._dynamics = layers.mlp(cfg.latent_dim + cfg.action_dim + cfg.task_dim, 2*[cfg.

mlp_dim], cfg.latent_dim, act=layers.SimNorm(cfg)) 3self._reward = layers.mlp(cfg.latent_dim + cfg.action_dim + cfg.task_dim, 2*[cfg.mlp_dim ],max(cfg.num_bins, 1)) 4self._termination = layers.mlp(cfg.latent_dim + cfg.task_dim, 2*[cfg.mlp_dim], 1)ifcfg.

episodicelseNone 5self._pi = layers.mlp(cfg.latent_dim + cfg.task_dim, 2*[cfg.mlp_dim], 2*cfg.action_dim) 6self._Qs = layers.Ensemble([layers.mlp(cfg.latent_dim + cfg.action_dim + cfg.task_dim, 2*[cfg.mlp_dim],max(cfg.num_bins, 1), dropout=cfg.dropout)for_in range(cfg.num_q) ]) Listing 4: world_model.py：TD-MPC2 world model组件 语义对应为：

- encoder:*h*(*s**t*)*→**z**t*。
- dynamics:*d*(*z**t**, a**t*)*→**z**t*+1。
- reward:*R*(*z**t**, a**t*)。

7

<!-- Page 8 -->

- pi: policy prior，用于产生policy trajectories。
- Qs: Q函数ensemble，用于planning末端bootstrap和训练target。

### Planning：tdmpc2.py 9.4

act()会在cfg.mpc=true时调用plan()，也就是_plan()：

1ifself.cfg.mpc:

returnself.plan(obs, t0=t0, eval_mode=eval_mode, task=task).cpu() 2 3z = self.model.encode(obs, task) 4action, info = self.model.pi(z, task) Listing 5: tdmpc2.py：动作选择入口 _estimate_value()用learned world model在latent空间rollout，并在horizon末端用Q bootstrap：

1G, discount = 0, 1 2fortin range(self.cfg.horizon):

reward = math.two_hot_inv(self.model.reward(z, actions[t], task), self.cfg) 3 z = self.model.next(z, actions[t], task) 4 G = G + discount * (1-termination) * reward 5 discount = discount * discount_update 6 7action, _ = self.model.pi(z, task) 8returnG + discount * (1-termination) * self.model.Q(z, action, task, return_type='avg') Listing 6: tdmpc2.py：估计候选动作序列价值 CEM/MPPI的核心是采样动作序列、选elite、根据value soft weighting更新mean和std：

1r = torch.randn(self.cfg.horizon, self.cfg.num_samples-self.cfg.num_pi_trajs, self.cfg.

action_dim, device=std.device) 2actions_sample = mean.unsqueeze(1) + std.unsqueeze(1) * r 3actions_sample = actions_sample.clamp(-1, 1) 4actions[:, self.cfg.num_pi_trajs:] = actions_sample 5 6value = self._estimate_value(z, actions, task).nan_to_num(0) 7elite_idxs = torch.topk(value.squeeze(1), self.cfg.num_elites, dim=0).indices 8elite_value, elite_actions = value[elite_idxs], actions[:, elite_idxs] 9 max_value = elite_value.max(0).values 10 score = torch.exp(self.cfg.temperature*(elite_value - max_value)) 11 score = score / score.sum(0) 12 mean = (score.unsqueeze(0) * elite_actions).sum(dim=1) / (score.sum(0) + 1e-9) 13 std = ((score.unsqueeze(0) * (elite_actions - mean.unsqueeze(1)) ** 2).sum(dim=1) / ( 14 score.sum(0) + 1e-9)).sqrt() Listing 7: tdmpc2.py：CEM/MPPI elite更新 最后从elite中按Gumbel-softmax采样一条动作序列，执行第一步动作：

1rand_idx = math.gumbel_softmax_sample(score.squeeze(1)) 2actions = torch.index_select(elite_actions, 1, rand_idx).squeeze(1) 3a, std = actions[0], std[0] 4if noteval_mode:

a = a + std * torch.randn(self.cfg.action_dim, device=std.device) 5 6self._prev_mean.copy_(mean) 7returna.clamp(-1, 1) Listing 8: tdmpc2.py：选择执行动作 8

<!-- Page 9 -->

### 训练更新：tdmpc2.py 9.5

_update()从replay buffer取短序列，训练dynamics consistency、reward、Q value，并更新policy prior。主损失是：

1total_loss = ( self.cfg.consistency_coef * consistency_loss + 2 self.cfg.reward_coef * reward_loss + 3 self.cfg.termination_coef * termination_loss + 4 self.cfg.value_coef * value_loss 5

6. 

7 8total_loss.backward() 9grad_norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.

grad_clip_norm) self.optim.step() 10 self.optim.zero_grad(set_to_none=True) 11 Listing 9: tdmpc2.py：baseline主损失 policy prior的更新使用Q值作为优化信号：

1action, info = self.model.pi(zs, task) 2qs = self.model.Q(zs, action, task, return_type='avg', detach=True) 3self.scale.update(qs[0]) 4qs = self.scale(qs) 5 6rho = torch.pow(self.cfg.rho, torch.arange(len(qs), device=self.device)) 7pi_loss = (-(self.cfg.entropy_coef * info["scaled_entropy"] + qs).mean(dim=(1,2)) * rho).

mean() 8pi_loss.backward() Listing 10: tdmpc2.py：policy prior更新

### Replay Buffer：common/buffer.py 9.6

Replay buffer使用TorchRL的ReplayBuffer和SliceSampler，每次采样长度为horizon+1的 子序列：

1self._sampler = SliceSampler( num_slices=self.cfg.batch_size, 2 end_key=None, 3 traj_key='episode', 4 truncated_key=None, 5 strict_length=True, 6 cache_values=cfg.multitask, 7

8. 

9self._batch_size = cfg.batch_size * (cfg.horizon+1) 10 ...

11 12 defsample(self):

13 td = self._buffer.sample().view(-1, self.cfg.horizon+1).permute(1, 0) 14 returnself._prepare_batch(td) 15 Listing 11: buffer.py：采样horizon+1的短轨迹

### Online Training Loop：trainer/online_trainer.py 9.7

单任务在线训练逻辑如下：前seed_steps用随机动作收集数据，之后使用agent planning选动作， 并开始更新模型。

9

<!-- Page 10 -->

1ifself._step > self.cfg.seed_steps:

action = self.agent.act(obs, t0=len(self._tds)==1) 2 3else:

action = self.env.rand_act() 4 5obs, reward, done, info = self.env.step(action) 6self._tds.append(self.to_td(obs, action, reward, info['terminated'])) 7 8ifself._step >= self.cfg.seed_steps:

ifself._step == self.cfg.seed_steps:

9 num_updates = self.cfg.seed_steps 10 print('Pretraining agent on seed data...') 11 else:

12 num_updates = 1 13 for_in range(num_updates):

14 _train_metrics = self.agent.update(self.buffer) 15 Listing 12: online_trainer.py：交互与更新循环

## 复现结论 10

本次baseline复现已经完成以下验证：

1. 成功克隆TD-MPC2仓库并建立用户级tdmpc2环境。
2. 修复了torchrl-nightly不可用、Hydra launcher缺失、Hugging Face下载超时等环境问题。
3. DMControl/MuJoCo在MUJOCO_GL=egl下可正常运行。
4. 官方dog-run-1.ptcheckpoint可正常加载并评估，单episode reward为762.2。
5. 原始baseline训练流程已通过1万步smoke test，生成eval.csv和models/final.pt。

需要强调的是，1万步结果只证明代码链路可用，不代表TD-MPC2的最终性能。正式复现 dog-runbaseline应使用README示例中的700万步或至少更长训练步数，并建议多seed报告 均值和方差。

10
