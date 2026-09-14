# 怎么跑第一次视频预测

目标：用仓库自带样例把第一阶段推理跑通，并读懂核心命令和配置文件。

## 最小命令

推荐从仓库自带的 `xhand` 样例开始：

```bash
python make_prediction.py \
  --config video_conf/val_svd.yaml \
  --video_model_path /path/to/models/vpp/svd-robot \
  --clip_model_path /path/to/models/vpp/clip-vit-base-patch32 \
  --val_dataset_dir video_dataset_instance/xhand \
  --val_idx 0+50+100+150
```

这条命令的目标不是复现 benchmark 数值，而是验证：

- 视频模型能否加载
- 文本编码器能否加载
- 样例数据路径是否正确
- 输出视频是否生成成功

## 一个可参考的命令

下面这条命令可作为第一阶段最小推理的参考入口：

```bash
python make_prediction.py \
  --config video_conf/val_svd.yaml \
  --video_model_path /path/to/models/vpp/svd-robot \
  --clip_model_path /path/to/models/vpp/clip-vit-base-patch32 \
  --val_dataset_dir video_dataset_instance/xhand \
  --val_idx 0+50+100+150
```

对应输出视频落在：

```text
./video_output/xhand/<timestamp>_vpp_svd-robot_5.mp4
```

## 每个参数在控制什么

| 参数 | 控制什么 |
|---|---|
| `--video_model_path` | 下半部分预测视频由哪个视频模型生成 |
| `--clip_model_path` | 文字指令由哪个 CLIP 模型编码 |
| `--val_dataset_dir` | 样本从哪个数据集目录读取 |
| `--val_idx` | 输出视频为什么会有多列，每一列取哪条样本 |
| `--config` | 分辨率、帧数、采样步数、输出路径等推理细节 |

## `val_idx` 为什么写成 `0+50+100+150`

这是作者脚本的一个小习惯：它用 `+` 拼接多个样本索引。也就是说：

- `0`
- `50`
- `100`
- `150`

对应视频里的 4 列样本。每一列通常对应一条不同的语言任务和视频片段。

## `video_conf/val_svd.yaml` 最值得先看的字段

| 字段 | 含义 |
|---|---|
| `width` / `height` | 推理分辨率 |
| `num_frames` | 生成多少帧 |
| `start_idx` | 从轨迹哪个位置开始取片段 |
| `skip_step` | 相邻帧采样间隔 |
| `num_inference_steps` | 视频扩散去噪步数 |
| `guidance_scale` | 条件引导强度 |
| `output_path` | 输出视频目录 |

如果你只是做连通性检查，最值得先动的是 `num_inference_steps`。把它调低，可以更快确认主链路有没有问题。

## 跑通后应该看到什么

正常情况下，日志里会出现类似信号：

- pipeline 加载完成
- 样例数据读取成功
- 扩散推理步数正常走完
- 最终在 `video_output/<dataset_name>/` 下生成 `mp4`

这说明第一阶段“从首帧和指令预测未来”的流程已经打通。

## 第一次推理最常见的报错

### 模型目录不是完整 `from_pretrained` 目录

表现：

- 找不到 `model_index.json`
- 某个子模块目录缺失

### CLIP 路径不完整

表现：

- 文本编码器或 tokenizer 加载失败

### `numpy` ABI 问题

表现：

- `RuntimeError: Numpy is not available`

这类问题通常不是脚本逻辑错误，而是环境版本冲突。

## 成功标准是什么

对第一次视频推理来说，成功不等于“论文效果复现完毕”。这里只要求三件事：

1. 命令能跑完
2. 输出视频生成出来
3. 预测视频和指令大致相关，不是纯噪声

## 小结

- 第一次推理的目标是打通链路，而不是比较最终指标。
- `make_prediction.py` 是理解 VPP 的高效入口。
- `val_idx` 决定多列样本，`val_svd.yaml` 决定推理行为。

## 导航

- 上一节：[环境和模型怎么配](01-environment-and-models.md)
- 返回上级：[环境准备与第一次视频预测](../02-setup-and-first-prediction.md)
- 下一节：[怎么读输出视频](03-read-the-output-video.md)
