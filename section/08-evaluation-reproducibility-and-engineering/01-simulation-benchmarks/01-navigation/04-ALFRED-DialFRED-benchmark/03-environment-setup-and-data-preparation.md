# 4.3 环境配置与数据准备

## 目标

ALFRED 的运行依赖 AI2-THOR 2.1.0 和官方数据集。与只需要读取静态文件的数据集不同，ALFRED 的完整复现需要环境、数据、特征、模型和评测脚本配合。

本节主要介绍 ALFRED 的基础环境配置、数据下载、目录结构和最小运行思路。这里不追求完整训练一个模型，而是帮助理解 ALFRED 的工程组成。

## 软件依赖

ALFRED 官方代码依赖较旧版本的 AI2-THOR 和 PyTorch。复现时需要注意版本一致性。

官方仓库中列出的基础依赖包括：

```text
Python 3
PyTorch 1.1.0
Torchvision 0.3.0
AI2-THOR 2.1.0
```

由于这些版本较旧，直接在当前最新 Python / PyTorch 环境中运行可能会出现兼容问题。因此建议单独创建环境，不要和当前项目环境混用。

## 克隆仓库

基础流程如下：

```bash
git clone https://github.com/askforalfred/alfred.git alfred
cd alfred
export ALFRED_ROOT=$(pwd)
```

建议把环境变量写入当前 shell：

```bash
export ALFRED_ROOT=/path/to/alfred
```

后续下载数据、训练模型和运行脚本时都需要依赖这个路径。

## 创建 Python 环境

官方 README 中使用 virtualenv，也可以根据机器情况使用 conda。

示例：

```bash
conda create -n alfred_env python=3.7 -y
conda activate alfred_env

cd $ALFRED_ROOT
pip install --upgrade pip
pip install -r requirements.txt
```

如果遇到 PyTorch 或 AI2-THOR 版本问题，应优先查看官方 requirements.txt 和 issue。ALFRED 使用的是较老的 AI2-THOR 2.1.0，因此不建议直接替换成最新 AI2-THOR。

## 下载数据

ALFRED 数据包含 trajectory JSON、视觉特征和完整数据资源。官方提供了下载脚本。

如果只想下载 JSON 和 ResNet 特征，可以执行：

```bash
cd $ALFRED_ROOT/data
sh download_data.sh json_feat
```

这部分数据大约十几 GB，适合训练和复现实验中的特征读取。

如果需要更完整的数据，可以查看：

```bash
cd $ALFRED_ROOT/data
cat README.md
```

数据下载完成后，常见目录可能包括：

```text
data/
├── json_feat_2.1.0/
├── splits/
├── traj_data.json
└── ...
```

不同下载选项会生成不同内容，具体结构以官方 data README 为准。

## 数据结构

ALFRED 的一条 trajectory 通常包含：

| 字段                        | 含义                                           |
| ------------------------- | -------------------------------------------- |
| task_id                   | 当前任务编号                                       |
| scene                     | 使用的 AI2-THOR 场景                              |
| task_type                 | 任务类型，例如 pick_and_place、pick_clean_then_place |
| goal instruction          | 高层目标指令                                       |
| step-by-step instructions | 分步语言指令                                       |
| plan                      | 高层和低层动作计划                                    |
| images / features         | 视觉观测或预提取特征                                   |
| object annotations        | 目标物体、容器和交互对象信息                               |

这些数据共同描述了一次完整专家任务执行过程。

可以把一条样本理解成：

```text
语言指令
+ 场景
+ 专家动作序列
+ 视觉观测
+ 目标物体和容器
```

## 最小理解流程

对于入门学习，不一定要一开始就完整训练模型。更合理的顺序是：

```text
先浏览官方 Data Explorer
-> 下载 json_feat 数据
-> 查看单条 trajectory JSON
-> 理解语言指令和低层动作
-> 再尝试运行训练或评测脚本
```

可以先用下面命令查看数据目录：

```bash
cd $ALFRED_ROOT
find data -maxdepth 3 -type f | head -30
```

如果已经下载了 JSON，可以尝试搜索一条轨迹：

```bash
find data -name "traj_data.json" | head
```

然后用 Python 或文本编辑器打开，观察里面的任务类型、指令和动作序列。

## 渲染与视频

ALFRED 的数据可以包含视频和图像观测，也可以使用预提取视觉特征进行训练。DialFRED 的流程中也会涉及渲染 trajectory 图像。

常见渲染命令示例：

```bash
cd $ALFRED_ROOT
python -m alfred.gen.render_trajs
```

这个命令会调用 AI2-THOR 环境重放轨迹并渲染图像。由于涉及仿真器，服务器上可能需要图形渲染支持。

如果只做教程介绍，可以优先使用公开视频示例，不一定要本地重新渲染。

## 服务器运行注意事项

ALFRED 复现常见问题主要来自版本和渲染环境。

| 问题             | 说明                                  |
| -------------- | ----------------------------------- |
| AI2-THOR 版本不一致 | ALFRED 依赖 AI2-THOR 2.1.0，最新版接口可能不兼容 |
| PyTorch 版本过旧   | 官方 baseline 使用较旧 PyTorch，需单独环境      |
| Unity 渲染失败     | 服务器无显示器时可能需要 headless / X server 配置 |
| 数据下载失败         | 数据较大，网络不稳定时容易中断                     |
| 路径配置错误         | ALFRED_ROOT、data 路径和 splits 路径需要对应  |
| 特征文件缺失         | 训练脚本可能依赖 json_feat 或预提取视觉特征         |
| 评测输入不合规        | 测试阶段只能使用允许的输入，例如 RGB 和语言指令          |

因此，ALFRED 的环境配置比普通 Python 包更重。建议在服务器上单独创建环境，并严格按照官方版本运行。

## 训练脚本概念

官方仓库提供了 baseline 训练脚本，例如 seq2seq 模型训练。

示例命令形式如下：

```bash
cd $ALFRED_ROOT

python models/train/train_seq2seq.py \
  --data data/json_feat_2.1.0 \
  --model seq2seq_im_mask \
  --dout exp/model:{model},name:pm_and_subgoals_01 \
  --splits data/splits/oct21.json \
  --gpu \
  --batch 8 \
  --pm_aux_loss_wt 0.1 \
  --subgoal_aux_loss_wt 0.1
```

这个命令不一定需要在教程中实际运行，但它展示了 ALFRED 训练的基本组成：

```text
数据路径
模型类型
输出目录
数据划分
是否使用 GPU
batch size
辅助损失权重
```

## 与前面几个 benchmark 的环境配置差异

ALFRED 的环境配置和前面几个 benchmark 有一定区别。

| Benchmark           | 主要依赖                                           | 入门重点                         |
| ------------------- | ---------------------------------------------- | ---------------------------- |
| OmniNavBench        | Isaac Sim、导航场景、机器人模型、任务数据                      | 理解组合式导航和跨机器人形态评测             |
| Habitat Challenge   | Habitat-Sim、Habitat-Lab、场景数据和 challenge 配置     | 理解导航 / 重排任务的在线评测流程           |
| AI2-THOR / RoboTHOR | ai2thor Python package、Unity build、RoboTHOR 场景 | 初始化 Controller，执行动作并读取 event |
| ALFRED              | AI2-THOR 2.1.0、trajectory JSON、语言指令、专家动作序列     | 从语言指令学习长程动作序列                |

相比前面几个 benchmark，ALFRED 的重点不只是仿真环境本身，而是语言、视觉、动作和专家轨迹之间的对应关系。它使用 AI2-THOR 作为底层环境，但在其上增加了高层目标指令、分步语言指令、低层动作序列和任务成功判断。

因此，配置 ALFRED 时需要同时关注两部分：

```text
底层环境：
AI2-THOR 版本、Unity 渲染、场景加载

任务数据：
trajectory JSON、语言标注、视觉特征、数据划分和评测脚本
```

这也是 ALFRED 比普通 AI2-THOR demo 更复杂的地方。

## 本节小结

ALFRED 的工程结构可以概括为：使用 AI2-THOR 作为底层环境，使用 trajectory JSON 和视觉特征作为训练数据，使用官方 splits 做训练和评测，并通过完整动作序列判断任务是否成功。

对于入门者来说，先理解数据结构和任务流程，比直接完整训练 baseline 更重要。等理解了语言指令、低层动作和 trajectory JSON 之间的关系后，再尝试本地复现会更稳。
