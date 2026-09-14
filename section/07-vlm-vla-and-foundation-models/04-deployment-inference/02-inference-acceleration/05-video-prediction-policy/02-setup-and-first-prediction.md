# 环境准备与第一次视频预测

目标：完成第一阶段最小复现，理解 `make_prediction.py` 的输入输出，并用第一次推理结果建立对论文第一阶段的直观认识。

这一页只回答一个问题：**如何最小成本地验证论文第一阶段确实在工作。**

对 VPP 这样的两阶段项目来说，第一次动手不建议直接进入训练。更合理的做法是先跑通第一阶段视频预测，因为这一步同时承担三件事：

- 验证模型目录和依赖是否正确
- 帮助理解论文第一阶段到底在产生什么
- 为后续第二阶段评测建立直观参照

## 这一页要完成的最小目标

第一次动手时，只需要完成下面三件事：

1. 模型和依赖能够正确加载
2. `make_prediction.py` 能够正常运行
3. 能够区分“真实未来”和“模型预测未来”

做到这三点，就已经完成了第一阶段的最小复现。

## 需要准备哪些模型

如果只做最小复现，通常至少需要下面几个模型目录：

1. `clip-vit-base-patch32`
2. `svd-robot`
3. `svd-robot-calvin`
4. `dp-calvin`

其中：

- `svd-robot` 主要用于第一阶段视频预测示例
- `svd-robot-calvin` 与 `dp-calvin` 主要用于第二阶段 CALVIN 评测

可以按下面的方式组织本地目录：

```text
models/vpp/
├── clip-vit-base-patch32/
├── svd-robot/
├── svd-robot-calvin/
└── dp-calvin/
```

只要目录满足 `from_pretrained(...)` 的要求，具体存放路径可以自行决定。

## 环境里最常见的版本问题

第一次复现最常见的故障不是脚本本身，而是依赖版本组合。

### `numpy 2.x` 与旧版 `torchvision`

这一问题的典型表现是：

- 导入 `torchvision` 时出现 ABI 相关 warning
- 后续触发 `RuntimeError: Numpy is not available`

如果出现这一问题，通常说明：

- 环境里装的是 `numpy 2.x`
- 但 `torch` / `torchvision` 链路仍按 `numpy 1.x` ABI 构建

在这种情况下，较常见的处理方式是把 `numpy` 回退到 `<2`。

### 文本编码器或模型目录不完整

如果 `clip` 或视频模型目录缺少关键文件，可能会出现：

- `model_index.json` 缺失
- tokenizer 加载失败
- 某个子模块目录不存在

遇到这类错误，首先应检查下载得到的是不是完整模型目录，而不仅仅是单个权重文件。

## 第一次视频预测的推荐命令

推荐先使用仓库自带的 `xhand` 样例：

```bash
python make_prediction.py \
  --config video_conf/val_svd.yaml \
  --video_model_path /path/to/models/vpp/svd-robot \
  --clip_model_path /path/to/models/vpp/clip-vit-base-patch32 \
  --val_dataset_dir video_dataset_instance/xhand \
  --val_idx 0+50+100+150
```

这条命令的目的不是跑 benchmark，而是确认论文第一阶段是否能够：

- 读取样例数据
- 编码文本指令
- 根据当前观测预测未来视频
- 将结果写出到输出目录

## 这条命令在论文主线中的位置

运行这条命令时，可以把它理解成论文第一阶段的一个可视化切片：

- 输入：当前观测和语言指令
- 模型：已经训练好的第一阶段视频模型
- 输出：真实未来和预测未来的对比结果

因此，这一步的价值不是得到数值指标，而是回答一个更基础的问题：**这个视频模型是否学到了与任务相关的未来动态。**

## 这条命令的关键参数是什么意思

| 参数 | 作用 |
|---|---|
| `--video_model_path` | 指定第一阶段视频模型目录 |
| `--clip_model_path` | 指定文本编码器目录 |
| `--val_dataset_dir` | 指定验证样例所在的数据目录 |
| `--val_idx` | 指定要可视化的样本 ID，可用 `+` 拼接多个 |
| `--config` | 控制分辨率、帧数、扩散步数和输出路径 |

其中 `--val_idx 0+50+100+150` 的含义是：从样例集中取 4 个样本并排展示，因此输出视频里会看到多列结果。

## `val_svd.yaml` 应该先关注什么

第一次阅读配置文件时，不必试图理解所有字段。建议优先关注：

- `width` / `height`
- `num_frames`
- `start_idx`
- `skip_step`
- `num_inference_steps`
- `guidance_scale`
- `output_path`

如果只是做连通性检查，最值得先调整的是 `num_inference_steps`。把它设小一些，可以更快确认主链路是否正常。

## 成功运行后应该看到什么

正常情况下，日志里会出现以下信号：

- pipeline 加载完成
- 样例数据读取成功
- 扩散推理步数正常走完
- 最终在 `video_output/<dataset_name>/` 下生成 `mp4`

这说明第一阶段“根据当前观测和指令预测未来”的链路已经跑通。

## 如何理解输出视频

`make_prediction.py` 输出的通常不是单纯的生成视频，而是一个对比视频。常见布局是：

- 横向多列：不同任务样本
- 纵向两行：
  - 上面是真实未来片段
  - 下面是模型预测未来片段

下面这张图是一个实际样例的关键帧拼图：

![VPP 第一阶段关键帧拼图](assets/vpp-first-prediction-contact.png)

如需查看动态过程，可以参考下面的 gif：

![VPP 第一阶段预测对比 gif](assets/vpp-first-prediction.gif)

这里需要特别分清两个概念：

- 这不是第二阶段策略在环境中真实执行得到的 rollout
- 这是第一阶段视频模型根据当前观测和文字指令预测得到的未来

也就是说，它回答的是“如果模型来想象未来，画面会如何演化”，而不是“策略已经在环境里真实执行了这些动作”。

## 如何判断第一阶段结果是否合理

第一次观察输出视频时，建议重点看三件事：

1. 机械臂是否朝正确区域运动
2. 目标物体是否出现合理的趋势变化
3. 多帧之间是否保持基本的时序一致性

不必要求逐像素精确重建。对 VPP 来说，第一阶段最重要的是形成有用的未来表征，而不是产出完全逼真的视频。

## 为什么这一页放在整章前面

因为它是连接“论文方法”和“代码复现”的第一座桥梁：

- 如果只读论文，这一步会把抽象的“未来表征”变成可观察的现象
- 如果要继续复现，这一步会告诉读者第一阶段模型是否已经基本正常

读完并跑通这一页后，再进入第二阶段评测会更顺，因为读者已经知道第一阶段到底提供了什么。

## 第一次推理最常见的失败模式

### 模型目录不完整

表现：

- 缺少 `model_index.json`
- 某些子模块找不到

### 文本编码器路径错误

表现：

- tokenizer 或文本模型加载失败

### 依赖版本冲突

表现：

- `RuntimeError: Numpy is not available`
- 与视频解码或图像处理相关的 warning / error

这类问题通常与环境版本有关，而不是脚本逻辑本身错误。

## 补充阅读

如需更细的说明，可以继续阅读：

- [环境和模型怎么配](02-setup-and-first-prediction/01-environment-and-models.md)
- [怎么跑第一次视频预测](02-setup-and-first-prediction/02-run-make-prediction.md)
- [怎么读输出视频](02-setup-and-first-prediction/03-read-the-output-video.md)

## 小结

- 第一阶段最小复现的核心入口是 `make_prediction.py`。
- 这一阶段的输出视频主要用于理解和验证未来动态表征，而不是做最终评测。
- 只要模型能加载、推理能完成、输出视频与指令大致相关，就说明论文第一阶段已经以最小形式复现成功。

## 导航

- 上一节：[项目总览](01-overview.md)
- 返回上级：[Video Prediction Policy](../05-video-prediction-policy.md)
- 下一节：[数据组织与 latent 预处理](03-data-and-latent-prep.md)
