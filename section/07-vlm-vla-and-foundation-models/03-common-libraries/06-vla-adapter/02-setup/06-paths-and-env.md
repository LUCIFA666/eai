# 路径与环境变量

目标：统一 VLA-Adapter 运行中的数据、checkpoint、日志、视频和环境变量约定，减少后续命令随机器变化。

## 常见路径

| 路径 | 用途 | 建议 |
| --- | --- | --- |
| `data/libero/` | RLDS / TFDS 训练数据（输入） | 相对路径传给 `--data_root_dir`；已被 gitignore。 |
| `outputs/` | 官方 checkpoint（下载的输入） | 相对路径传给 `--pretrained_checkpoint`；已被 gitignore。 |
| `$ARTIFACT_ROOT/runs/` | 训练 run 目录和 checkpoint（产物） | `--run_root_dir` 指向；放在代码树外。 |
| `$ARTIFACT_ROOT/logs/` | 训练 shell 日志（产物） | 训练命令重定向写入。 |
| `eval_logs/` | 评测 shell 重定向日志 | 官方仓库已有参考日志，本地命令使用新的文件名。 |
| `experiments/logs/` | 评测脚本内部日志 | 文件名带时间戳，用于读 `Final results`；未被 gitignore。 |
| `rollouts/` | 评测和 smoke test mp4 | 临时文件，已被 gitignore；需要长期保留的复制到产物根 `$ARTIFACT_ROOT`。 |

## 推荐约定

输入放在源码仓库的默认目录下：数据 `data/libero`、基础 VLM `pretrained_models/...`、官方 checkpoint `outputs/...`，用这些相对路径作为命令参数。训练产物（checkpoint、日志）通过 `--run_root_dir` 等参数写到产物根 `$ARTIFACT_ROOT`，和源码分开。

`data/`、`outputs/`、`rollouts/` 都在 `.gitignore` 里，不会污染 `git status`。训练产物写在代码树外的 `$ARTIFACT_ROOT`，天然不进源码仓库。评测脚本内部日志默认写在 `experiments/logs/`，未被 gitignore，评测后会以未跟踪状态出现，属正常现象。`rollouts/` 里的 mp4 是临时文件，需要长期保留的可以复制到产物根 `$ARTIFACT_ROOT`（例如 `$ARTIFACT_ROOT/rollouts/`）。

## 常用环境变量

```bash
export PYTHONPATH=$PWD/LIBERO:$PYTHONPATH
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export TOKENIZERS_PARALLELISM=false
```

`PYTHONPATH` 让评测脚本找到 `libero.libero`；`MUJOCO_GL` 和 `PYOPENGL_PLATFORM` 用于无显示器服务器上的 EGL 离屏渲染；`TOKENIZERS_PARALLELISM=false` 用于减少 tokenizer fork warning 噪声。

## 多卡服务器

如果前几张 GPU 正在被占用，可以用 `CUDA_VISIBLE_DEVICES` 指定空闲 GPU。比如 `CUDA_VISIBLE_DEVICES=4` 会让当前进程只看到物理 4 号卡，并在进程内部把它当作 `cuda:0` 使用。

## 导航

- 上一节：[官方 Checkpoint 链路检查](05-checkpoint-smoke-test.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[数据接口与管线](../03-data.md)
