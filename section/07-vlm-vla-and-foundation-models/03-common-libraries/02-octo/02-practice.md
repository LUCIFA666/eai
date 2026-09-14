# Octo 实践：跑通 debug finetune

本页把 Octo 落到一条最小验证路径：搭好 JAX 环境，跑通官方的 `--debug` finetune，并说明这一步代表了什么含义。

仓库里官方推荐的最小测试命令为：

```bash
python scripts/finetune.py \
  --config.pretrained_path=hf://rail-berkeley/octo-small-1.5 \
  --debug
```

> hint：Octo 官方代码基于 **JAX**，不是本课程其它章节常用的 PyTorch，所以环境和依赖会带上 JAX / jaxlib / cuDNN 这条线。

## 环境搭建

本次实验使用的服务器环境如下：

| 项目 | 配置 |
|---|---|
| GPU | NVIDIA A100-SXM4-80GB × 8 |
| 显存 | 单卡 80 GB |
| 操作系统 | Ubuntu 24.04.3 LTS |
| 内核 | Linux 6.8 |
| NVIDIA 驱动 | 580.x |

Octo 的 `requirements.txt` 给 `jax`、`numpy`、`tensorflow` 指定了精确版本，但 `scipy`、`transformers`、`matplotlib` 几行只给了下限。在较新的 pip 源上，这些会拿到太新的包，以至于和 `jax==0.4.20` 不兼容。下表把这几个版本提前指定好，确保可行性：

| 依赖 | 推荐版本 | 原因 |
|---|---|---|
| Python | 3.10 | Octo 官方环境 |
| jax / jaxlib | 0.4.20（`jaxlib==0.4.20+cuda11.cudnn86`） | Octo 指定的版本 |
| scipy | 1.11.4 | 更新版本删了 `scipy.linalg.tril`，`jax==0.4.20` 导入 `jax.scipy` 会报 `AttributeError` |
| transformers | 4.34.1 | 5.x 移除了 `FlaxAutoModel`，加载语言 encoder 会 `ImportError` |
| matplotlib | 3.9.4 | 3.10 移除了 `FigureCanvasAgg.tostring_rgb`，eval 的可视化回调会崩 |
| nvidia-cudnn-cu11 | 8.6.0.163 | 要匹配 `jaxlib` 的 cudnn86 构建，混进 cuDNN 9.x 会让 JAX 退回 CPU |

按下面顺序装即可：

```bash
git clone https://github.com/octo-models/octo.git
cd octo

conda create -n octo python=3.10 -y
conda activate octo

# 1. Octo 包本体 + 官方 requirements
pip install -e .
pip install -r requirements.txt

# 2. 指定 requirements 没限制好上限的三个 Python 依赖
pip install "scipy==1.11.4" "transformers==4.34.1" "matplotlib==3.9.4"

# 3. 根据服务器情况二选一
# 3.1 GPU 版 JAX：官方推荐的 CUDA 11 wheel
pip install --upgrade "jax[cuda11_pip]==0.4.20" \
  -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html

# 3.2 TPU 版 JAX
pip install --upgrade "jax[tpu]==0.4.20" \
  -f https://storage.googleapis.com/jax-releases/libtpu_releases.html

# 4. 指定 cuDNN，匹配 jaxlib 的 cudnn86 构建
pip install "nvidia-cudnn-cu11==8.6.0.163"
```

## 获取 checkpoint

`hf://rail-berkeley/octo-small-1.5` 会触发 `huggingface_hub.snapshot_download()`，把 checkpoint 拉到本地 Hugging Face cache（`~/.cache/huggingface/hub/`）。第一次需要联网下载，之后会直接命中 cache。

如果机器不通外网，会看到 `LocalEntryNotFoundError` 或 `Network is unreachable`。这不是 Octo 代码的问题，而是网络问题。可以先在有网络的机器上下好模型，或配置代理，再重跑命令。

## 运行 debug finetune

不加任何 step 设置时，debug finetune 默认会跑 50,000 step。第一次验证环境时，建议先跑一个 **200 step、单卡、小 batch** 的版本快速确认整条链路可通：

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/finetune.py \
  --config.pretrained_path=hf://rail-berkeley/octo-small-1.5 \
  --config.num_steps=200 \
  --config.optimizer.learning_rate.warmup_steps=20 \
  --config.eval_interval=100 \
  --config.save_interval=100 \
  --config.batch_size=64 \
  --config.shuffle_buffer_size=1000 \
  --config.save_dir=./checkpoints \
  --debug
```

参数解析：

- `--config.num_steps=200`：只跑 200 step，几分钟出结果。
- `--config.optimizer.learning_rate.warmup_steps=20`：**这一项要随着num_steps改动**。默认 `warmup_steps=2000`，而学习率 schedule 的 `decay_steps` 跟着 `num_steps` 走；只把 `num_steps` 改小却不动 warmup，cosine schedule 会拿到 `decay_steps - warmup_steps < 0`，直接报 `cosine_decay_schedule requires positive decay_steps`。所以把 warmup 调到比 num_steps 小即可。
- `--config.eval_interval=100` / `--config.save_interval=100`：让 200 step 里触发两次 eval 和两次保存，把评估、动作采样、可视化、checkpoint 保存都走到。
- `--config.batch_size=64` + `CUDA_VISIBLE_DEVICES=0`：单卡就够。多卡训练时 batch size 会按设备数平分。

`--debug` wandb 以 disabled 模式初始化（不向外部服务记录），数据目录使用仓库内置的 `./tests/debug_dataset`。

启动后日志开头会打印这次运行的配置，确认它和你的参数一致：

```txt
Octo Finetuning Script
======================
Pretrained model: hf://rail-berkeley/octo-small-1.5
Finetuning Dataset: bridge_dataset
Finetuning Mode: full

# Devices: 1
Batch size: 64 (64 per device)
# Steps: 200
```

接着会打印参数冻结信息：

```txt
Freezing parameters that include the following keys: ['*hf_model*'].
Num trainable params: 27,042,060.
Num frozen params: 109,628,544.
```

>回顾：`Finetuning Mode: full` 表示不额外冻结 Octo transformer / head 这类策略参数；但脚本在 `optimizer.frozen_keys is None` 时会继承 checkpoint config 的 `frozen_keys`，而 Octo-1.5 的 checkpoint 里冻结了 Hugging Face text encoder，所以 `*hf_model*` 不参与训练。这也呼应理论篇说的：`full` 微调并不等于无差别训练所有参数。

## 跑通

JAX 第一次编译较慢，第一个 train step 可能要几十秒；编译完后速度会稳定下来（单卡 200 step 总共几分钟）。完整跑完会看到进度条到 `200/200`。

怎么判断跑通：

- 训练在编译后稳定推进，没有 `Traceback`。
- 每隔 `eval_interval` 进入一次评估（`Evaluating...`），且能看到 `jit_sample_actions` 被编译——说明动作采样路径也跑到了。
- 每隔 `save_interval` 落盘一次 checkpoint。

这一步跑通，说明整条工程链路是通的。依赖无冲突、JAX 能用 GPU、checkpoint 能加载、debug 数据能读、训练和评估 / 采样都能跑、checkpoint 能存。但这不算复现了 Octo 论文的成功率或 800k 轨迹预训练，也不代表生成了能直接部署到真实机器人的策略；`tests/debug_dataset` 上的 loss 和速度同样不能外推到真实数据集。因为完全复现还是需要一定时间（Octo-S 用 TPUv4-128 约 8 小时，Octo-B 约 14 小时），感兴趣的读者可以下载数据集自行复现。

传入 `--config.save_dir` 时，checkpoint 会存到 `<save_dir>/<wandb.project>/<wandb.group>/<run_name>/`，每个保存点是一个以 step 数命名的子目录（约 500 MB / 个）；不传则日志提示 `save_dir not passed in, not saving checkpoints`，训练照常进行但不留产物。

确认无误后，可以用官方命令跑完整 debug finetune（建议配合 `nohup` 保存日志、多卡加速）。

> 仓库里官方推荐的最小测试命令是：
```bash
python scripts/finetune.py \
  --config.pretrained_path=hf://rail-berkeley/octo-small-1.5 \
  --debug
```

## 小结

- `--debug` 跑通说明：依赖无冲突、JAX 能用 GPU、checkpoint 能加载、debug 数据集能读、训练 + 评估 + 采样 + checkpoint 保存整条链路可用。不证明：800k 预训练效果可复现、生成的策略能部署到真实机器人。
- `num_steps` 和 `warmup_steps` 必须联动修改，cosine schedule 的 `decay_steps = num_steps - warmup_steps`，warmup 不调就会出现负数 decay_steps 报错。
- `full` finetune 不等于无差别训练所有参数。脚本会继承 checkpoint config 的 `frozen_keys`，Hugging Face text encoder 默认冻结。

## 动手练习

1. 把 `--config=finetune_config.py:head_only,multimodal` 和默认 `full,multimodal` 对比，观察 `Num trainable params` 怎么变化。
2. 只改 `--config.num_steps=200` 而不改 `warmup_steps`，复现 `positive decay_steps` 报错，理解 `decay_steps` 和 `num_steps` 的联动。

## References

- [Octo project page](https://octo-models.github.io/)

## 导航

- 上一节：[Octo 理论基础](01-theory.md)
- 返回上级：[Octo](../02-octo.md)
- 下一节：[RDT](../03-rdt.md)