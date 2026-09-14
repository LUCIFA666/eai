# CALVIN 评测与排障

目标：把第二阶段最小闭环复现跑通，并系统整理 VPP 路线在实际评测时最容易遇到的坑。

## 标准入口

第二阶段较常用的测试入口是：

```bash
python policy_evaluation/calvin_evaluate.py \
  --video_model_path /path/to/models/vpp/svd-robot-calvin \
  --action_model_folder /path/to/models/vpp/dp-calvin \
  --clip_model_path /path/to/models/vpp/clip-vit-base-patch32 \
  --calvin_abc_dir /path/to/calvin_debug_dataset
```

这里关注的不是视频生成质量，而是完整闭环：

1. 当前观测进入策略
2. 策略调用视频模型中间特征
3. 输出动作
4. 环境执行 `step(action)`
5. 统计任务完成情况

## 一个可参考的命令

下面这条命令可以作为最小闭环评测的参考入口：

```bash
python policy_evaluation/calvin_evaluate.py \
  --video_model_path /path/to/models/vpp/svd-robot-calvin \
  --action_model_folder /path/to/models/vpp/dp-calvin \
  --clip_model_path /path/to/models/vpp/clip-vit-base-patch32 \
  --calvin_abc_dir /path/to/datasets/calvin/calvin_debug_dataset
```

对应日志目录是：

```text
/path/to/models/vpp/dp-calvin/logs/<timestamp>
```

## CALVIN 数据集从哪里下载

这一项目涉及两类 CALVIN 数据：

1. `calvin_debug_dataset`
2. `task_ABC_D`

它们的用途不同：

- `calvin_debug_dataset`：体积较小，适合最小复现和排障
- `task_ABC_D`：更接近论文正式评测所用的数据组织

如果只是第一次跑通闭环评测，建议优先下载 `calvin_debug_dataset`。

## 下载 `calvin_debug_dataset`

CALVIN 官方项目自带了下载脚本。先进入你本地的 `calvin/dataset` 目录：

```bash
cd /path/to/calvin/dataset
```

然后执行：

```bash
sh download_data.sh debug
```

执行后会得到：

```text
calvin_debug_dataset/
├── training/
└── validation/
```

如果希望把它放到统一数据目录下，可以手动移动：

```bash
mkdir -p datasets/calvin
mv calvin_debug_dataset datasets/calvin/
```

## 下载完整的 `task_ABC_D`

如果要接近论文正式评测路线，可以使用同一个脚本下载 `ABC`：

```bash
cd /path/to/calvin/dataset
sh download_data.sh ABC
```

执行后会得到：

```text
task_ABC_D/
├── training/
└── validation/
```

同样可以把它整理到统一目录：

```bash
mkdir -p datasets/calvin
mv task_ABC_D datasets/calvin/
```

## 如果下载脚本不可用，直接下载 zip

CALVIN 官方项目里的 `download_data.sh` 本质上就是下载官方 zip 文件，因此也可以直接执行：

### debug 数据

```bash
mkdir -p datasets/calvin
cd datasets/calvin
wget http://calvin.cs.uni-freiburg.de/dataset/calvin_debug_dataset.zip
unzip calvin_debug_dataset.zip
```

### `task_ABC_D`

```bash
mkdir -p datasets/calvin
cd datasets/calvin
wget http://calvin.cs.uni-freiburg.de/dataset/task_ABC_D.zip
unzip task_ABC_D.zip
```

## 评测前建议先检查什么

无论下载的是 debug 数据还是完整数据，评测前都建议先检查：

- 是否同时存在 `training/` 和 `validation/`
- 是否存在 `lang_annotations/auto_lang_ann.npy`
- 目录层级是否与脚本期望一致

例如：

```text
datasets/calvin/calvin_debug_dataset/
├── training/
│   └── lang_annotations/
└── validation/
    └── lang_annotations/
```

## 为什么第一次建议用 debug 数据

因为完整 `1000` 条序列评测很慢，而且原脚本默认更接近论文 benchmark，而不是本地最小复现。

因此，较常见的顺序是：

1. 先用 `calvin_debug_dataset`
2. 先确认脚本能在较小评测规模上跑通
3. 确认评测链路能跑通、能落结果
4. 再考虑更大规模评测

## 输出指标怎么读

常见输出会像这样：

```text
1/5 : 100.0%
2/5 : 100.0%
3/5 : 100.0%
4/5 : 80.0%
5/5 : 80.0%
Average: 4.6
```

含义是：

- 连续完成至少 1 个子任务的比例
- 连续完成至少 2 个子任务的比例
- ...
- 平均连续完成长度

如果只评测极少量序列，那么只能说明“链路通了”，不能说明论文性能已经复现。

## 一组 50 条 debug 序列的示例结果

下面给出一组 `results.json` 核心内容示例：

```json
{
  "last": {
    "avg_seq_len": 4.4,
    "chain_sr": {
      "1": 0.96,
      "2": 0.94,
      "3": 0.92,
      "4": 0.8,
      "5": 0.78
    }
  }
}
```

可以将其解释为：

- 平均每条 long-horizon 序列能连续完成 `4.4 / 5` 个子任务
- 至少完成 1 个子任务的比例是 `96%`
- 至少完成 5 个子任务的比例是 `78%`

这说明在 `calvin_debug_dataset` 上，第二阶段闭环链路不仅跑通了，而且策略表现已经相当强，说明闭环评测结果具有一定参考价值。

## 示例结果中相对较难的任务

从 `task_info` 看，这次 debug 评测里比较明显的弱项主要集中在“向右推”的子任务：

| 任务 | 成功 / 总数 | 成功率 |
|---|---:|---:|
| `push_blue_block_right` | `0 / 3` | `0.0%` |
| `push_red_block_right` | `0 / 1` | `0.0%` |
| `push_pink_block_right` | `1 / 3` | `33.3%` |
| `push_into_drawer` | `4 / 5` | `80.0%` |

而大量别的任务已经接近或达到 `100%`，例如：

- `open_drawer`
- `close_drawer`
- `move_slider_left`
- `move_slider_right`
- `lift_blue_block_slider`
- `place_in_drawer`

这类结果较常见：即便整体平均性能较高，局部动作类型仍然可能暴露出偏好或弱项。

## 两段实际 rollout 可视化

该评测脚本还保存了两段 long-horizon rollout 视频。下面给出压缩后的 gif 和关键帧拼图。

### 序列 6

![CALVIN rollout 序列 6 关键帧](../assets/vpp-calvin-rollout-seq6-contact.png)

![CALVIN rollout 序列 6 gif](../assets/vpp-calvin-rollout-seq6.gif)

### 序列 8

![CALVIN rollout 序列 8 关键帧](../assets/vpp-calvin-rollout-seq8-contact.png)

![CALVIN rollout 序列 8 gif](../assets/vpp-calvin-rollout-seq8.gif)

这些素材的价值不在于“做漂亮展示”，而在于让我们直接看到：

- 闭环控制过程中机械臂是否持续接近正确目标
- 子任务切换时策略是否稳定
- 某些任务失败时，是卡在接近、抓取还是放置阶段

## 如何解释这组结果

如果目标是“最小复现是否成功”，答案已经是肯定的。因为下面几件事都成立了：

1. 视频模型加载成功
2. 动作模型加载成功
3. CALVIN debug 环境启动成功
4. 50 条序列完整跑完
5. 结果正常打印并写入 `results.json`

但如果目标是“复现论文最终数字”，那这还不够。原因是：

- 这里使用的是 `calvin_debug_dataset`
- 只跑了 `50` 条序列
- 统计规模和论文完整 benchmark 不同

## 实际复现中遇到的常见问题

下面这些问题在实际复现中较常见。

### 1. `numpy 2.x` 导致 `RuntimeError: Numpy is not available`

现象：

- `torchvision` 导入阶段就出现 ABI warning
- 后面 `torch.from_numpy(...)` 直接失败

处理思路：

- 优先把 `numpy` 降到 `<2`

### 2. `pkg_resources` 缺失

现象：

```text
ModuleNotFoundError: No module named 'pkg_resources'
```

常见原因：

- `setuptools` 太新

### 3. `pyhash` 装不上

现象：

```text
ModuleNotFoundError: No module named 'pyhash'
```

现实情况：

- 原包在新 Python 上往往不可直接安装
- 项目实际上只依赖很小一部分功能

### 4. CALVIN debug 数据的旧下载地址失效

现象：

- 代码尝试下载 `50steps.tar.xz`
- 解压时报 `not an lzma file`

根因：

- 作者代码里旧的 debug 数据 URL 已经过期，下载回来的是 HTML 而不是数据包

更稳妥的方式是直接使用 CALVIN 仓库当前 `download_data.sh` 对应的官方 zip 下载链接，或者直接下载 `calvin_debug_dataset.zip`。

### 5. `dp-calvin` 目录结构不符合脚本预期

现象：

- 明明有 `last.pt`
- 但脚本仍然找不到 checkpoint

原因：

- 脚本默认按 `saved_models/last.pt` 这一层目录找

### 6. `num_sequences` 默认是 `1000`

现象：

- 第一次复现就要跑很久

原因：

- 作者把完整 benchmark 默认值直接写进了配置
- 原始命令行还没有暴露一个方便修改的参数

### 7. `last.pt` 导致结果保存阶段崩掉

现象：

- 评测已经跑完
- 最后在 `checkpoint.stem.split("=")[1]` 这里崩

原因：

- 作者默认 checkpoint 名字像 `epoch=...`
- 但最小下载模型往往就叫 `last.pt`

典型代码片段是：

```python
epoch = checkpoint.stem.split("=")[1]
```

这在作者自己的命名约定下可以工作，但对公开下载模型并不稳健。

### 8. `wandb.log()` 在 `wandb.init()` 之前调用

现象：

```text
Error: You must call wandb.init() before wandb.log()
```

原因：

- 原始脚本更像作者实验环境里的片段代码
- 不是完整打磨好的公共评测 CLI

这也是为什么即使你已经 `wandb login`，如果脚本没有先初始化 run，照样会在记录阶段崩掉。

### 9. `float16` pipeline 的 CPU warning

现象：

- 日志提示 `Pipelines loaded with dtype=torch.float16 cannot run with cpu device`

说明：

- 这条 warning 在很多情况下不是致命错误
- 更重要的是看评测是否真的继续向前推进

## 关于评测规模和日志控制

原仓库更偏研究代码风格，命令行默认不会暴露所有评测规模和日志控制开关。实际复现时，常见做法包括：

1. 修改配置文件中的默认值
2. 直接改动脚本中的评测参数
3. 在本地自行加入额外的命令行参数

阅读仓库或编写教程时，应区分：

1. 原仓库原样支持的接口
2. 使用者为便于排障而自行增加的接口

## 用 `wandb` 时还要注意什么

如果你想把评测同步到 `wandb`：

1. 先 `wandb login`
2. 最好显式指定自己的 `entity` 和 `project`

否则脚本可能沿用作者配置里的默认 entity。

如果使用原仓库代码，需要根据其配置文件和脚本逻辑处理 `wandb` 记录，而不能默认假设存在额外的命令行参数。

## 小结

- `calvin_evaluate.py` 是第二阶段最核心的最小复现入口。
- 原始脚本更适合作者自己的 benchmark 环境，不够适合新手第一次排障。
- 真正稳定的做法是：小数据、小序列数、先验证结果能完整落盘。
- 一组 `50` 条 debug 序列的示例结果达到 `avg_seq_len = 4.4`，说明闭环链路不仅能够运行，而且可以得到稳定的闭环评测结果。

## 导航

- 上一节：[第二阶段动作策略训练](02-stage2-action-policy.md)
- 返回上级：[训练视频模型与动作策略](../04-training.md)
- 下一节：[自定义机器人与部署](../05-custom-robot-and-deployment.md)
