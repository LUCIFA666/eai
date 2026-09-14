# 5.4 环境配置、Replay 与视频生成

## 目标

本节介绍如何把 TEACh 从“论文里的 benchmark”落到本地环境中：安装代码、下载数据、重放 episode、保存图像和状态，并生成视频。

TEACh 依赖 AI2-THOR simulator，因此环境配置比纯文本数据集复杂。入门时建议先以“跑通官方流程”为目标，而不是一开始就训练复杂模型。

## 基本依赖

官方 TEACh 代码通常需要：

```text
Python 3.7 到 3.8
tmux
xorg / openbox 等图形环境依赖
ffmpeg
AI2-THOR 相关依赖
TEACh Python package
```

如果在本地桌面机器上运行，图形环境通常比较直接。如果在远程服务器或无显示器环境中运行，需要额外启动 X server，否则 AI2-THOR 可能无法渲染图像。

## 安装代码

典型安装流程如下：

```bash
git clone https://github.com/alexa/teach.git
cd teach
pip install -r requirements.txt
pip install -e .
```

建议使用独立 conda 或 virtualenv 环境，避免和其他具身智能项目的依赖冲突。TEACh 对 Python 版本较敏感，如果遇到安装问题，先检查 Python 版本是否在官方要求范围内。

## 下载数据

TEACh 提供 `teach_download` 命令用于下载和解压数据：

```bash
teach_download
```

默认情况下，数据会下载到类似：

```text
/tmp/teach-dataset
```

也可以指定目录：

```bash
teach_download -d /path/to/teach-dataset
```

下载后的数据通常包含：

```text
games/
edh_instances/
tfd_instances/
images_and_states/
```

不同压缩包分别对应完整 game session、EDH 实例、TfD 实例和图像/状态数据。入门时建议先确认目录是否完整，再运行 replay 或 inference。

## 远程服务器图形环境

如果在没有显示器的远程服务器上运行 simulator，可能需要启动 X server。官方 README 中给出过类似流程：

```bash
tmux
sudo python ./bin/startx.py
```

启动后可以把 tmux 会话放到后台，再在主终端运行 replay 或 inference。常见问题是：

```text
DISPLAY 没有设置
Unity / AI2-THOR 无法启动
图像保存为空
远程环境缺少 xorg 或 openbox
```

遇到这些问题时，应先验证一个最小 AI2-THOR demo 能否启动，再运行完整 TEACh 流程。

## Episode Replay

TEACh 的 `teach_replay` 可以读取 game session，在 AI2-THOR 中重放，并保存图像和状态。

重放单个 game file 的基本形式：

```bash
teach_replay \
  --game_fn /path/to/game/file.game.json \
  --write_frames_dir /path/to/output/images \
  --write_frames \
  --write_states \
  --status-out-fn /path/to/output/status.json
```

重放一个目录中的多个 game file：

```bash
teach_replay \
  --game_dir /path/to/dir/containing/game/files \
  --write_frames_dir /path/to/output/images \
  --write_frames \
  --write_states \
  --num_processes 8 \
  --status-out-fn /path/to/output/status.json
```

其中：

| 参数 | 作用 |
| --- | --- |
| `--game_fn` | 指定单个 game file |
| `--game_dir` | 指定包含多个 game file 的目录 |
| `--write_frames_dir` | 保存帧图像和状态的目录 |
| `--write_frames` | 保存 replay 过程中的帧 |
| `--write_states` | 保存环境状态变化 |
| `--status-out-fn` | 保存 replay 状态，便于检查或恢复 |
| `--num_processes` | 多进程 replay 时使用 |

`--status-out-fn` 通常应以 `.json` 结尾。重复运行 replay 时，最好使用新的输出目录，避免旧结果和新结果混在一起。

## 生成视频

TEACh 可以通过 replay 生成视频。核心是在 replay 命令中加入：

```bash
--create_video
```

示例：

```bash
teach_replay \
  --game_fn /path/to/game/file.game.json \
  --write_frames_dir /path/to/output/images \
  --write_frames \
  --write_states \
  --create_video \
  --status-out-fn /path/to/output/status.json
```

如果本地安装了 `ffmpeg`，也可以把生成的 mp4 转成 GIF 预览：

```bash
ffmpeg -y -i /path/to/example-episode.mp4 \
  -vf "fps=8,scale=640:-1:flags=lanczos" \
  -t 8 \
  /path/to/example-episode.gif
```

GIF 适合快速预览，mp4 适合展示完整过程。本次环境没有可用的 `ffmpeg`，因此当前章节只保留从 TEACh 项目页抓取到的 mp4 示例视频：

<video src="assets/teach-example-episode.mp4" controls width="100%"></video>

也可以直接打开：[TEACh example episode](assets/teach-example-episode.mp4)。

## Inference 和 Evaluation

TEACh 提供 `teach_inference` 和 `teach_eval` 两个命令。

基本流程是：

```text
teach_inference：
加载 EDH 或 TfD instance，让模型在 simulator 中执行动作，并保存输出

teach_eval：
读取 inference 输出，计算任务成功率和其他指标
```

一个 SampleModel 的运行示例：

```bash
export DATA_DIR=/path/to/teach-dataset
export OUTPUT_DIR=/path/to/output/valid_seen
export METRICS_FILE=/path/to/output/valid_seen/metrics

teach_inference \
  --data_dir $DATA_DIR \
  --output_dir $OUTPUT_DIR \
  --split valid_seen \
  --metrics_file $METRICS_FILE \
  --model_module teach.inference.sample_model \
  --model_class SampleModel

teach_eval \
  --data_dir $DATA_DIR \
  --inference_output_dir $OUTPUT_DIR \
  --split valid_seen \
  --metrics_file $METRICS_FILE
```

如果要运行 TfD，可以在 inference 命令中加入：

```bash
--benchmark tfd
```

对入门学习来说，先跑 SampleModel 的意义不是得到高分，而是确认数据路径、simulator、inference 和 evaluation 流程是否连通。

## Docker Challenge 形式

TEACh challenge 中，参赛者通常需要提交 Docker image。评测时，系统会启动提交的容器，并通过 HTTP API 调用模型获取下一步动作。

可以理解为：

```text
参赛者模型容器：
负责接收当前 EDH instance 和图像，返回下一步 action

评测容器：
负责运行 simulator、发送请求、记录输出和计算指标
```

这种方式适合在线 challenge，因为它可以统一运行环境，避免参赛者直接接触测试集。

对入门者来说，不需要一开始就写 Docker submission。先理解本地 `teach_inference` 和 `teach_eval` 更重要。

## 常见问题

TEACh 复现常见问题包括：

| 问题 | 可能原因 |
| --- | --- |
| Python 版本不兼容 | TEACh 依赖 Python 3.7 到 3.8 |
| simulator 无法启动 | 远程服务器没有 X server 或图形环境 |
| replay 没有图像 | `--write_frames` 或输出路径设置不正确 |
| 视频没有生成 | 没有加 `--create_video` 或 ffmpeg 不可用 |
| 数据路径错误 | games、edh_instances、tfd_instances 目录不匹配 |
| inference 结果为空 | 模型接口或 split 配置错误 |
| 评测结果异常 | 输出目录、metrics 文件或 split 不对应 |

调试时建议按下面顺序：

```text
先确认 teach_download 数据完整
-> 再确认 teach_replay 能重放单个 episode
-> 再生成一段视频
-> 再运行 SampleModel inference
-> 最后尝试自己的模型
```

## 与前面几个 benchmark 的环境配置差异

TEACh 的环境配置和前面几个 benchmark 有明显区别。

| Benchmark | 主要依赖 | 入门重点 |
| --- | --- | --- |
| OmniNavBench | Isaac Sim、导航场景、机器人模型、任务数据 | 理解组合式导航和跨机器人形态评测 |
| Habitat Challenge | Habitat-Sim、Habitat-Lab、场景数据和 challenge 配置 | 理解导航 / 重排任务的在线评测流程 |
| AI2-THOR / RoboTHOR | ai2thor Python package、Unity build、RoboTHOR 场景 | 初始化 Controller，执行动作并读取 event |
| ALFRED / DialFRED | AI2-THOR、trajectory JSON、语言指令、专家动作序列 | 从语言指令学习长程动作序列 |
| TEACh | teach package、AI2-THOR simulator、game sessions、EDH / TfD instances、X server | 从对话历史和环境观察中继续执行任务 |

TEACh 比普通 AI2-THOR demo 更复杂，因为它不仅需要 simulator，还需要完整的对话数据、game session、instance 文件和评测流程。它也比单纯指令跟随更强调对话历史和协作过程。

## 本节小结

TEACh 的本地流程可以概括为：

```text
安装 teach
-> 下载 dataset
-> 配置图形环境
-> replay game session
-> 生成图像 / 状态 / 视频
-> 运行 inference
-> 用 teach_eval 计算指标
```

只要先跑通一个最小 episode，就能逐步理解 TEACh 的数据和评测管线。
