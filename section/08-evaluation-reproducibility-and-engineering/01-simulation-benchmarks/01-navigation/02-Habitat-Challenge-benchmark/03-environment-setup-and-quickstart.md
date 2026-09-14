# 2.3 环境配置与快速运行

## 目标

Habitat Challenge 不是单纯下载数据文件后离线计算指标，而是需要在 Habitat-Sim 和 Habitat-Lab 中运行 agent。因此，理解环境配置对于复现实验和阅读 benchmark 结果都很重要。

本节主要介绍 Habitat 的基本软件栈、常见安装方式、数据资源和快速运行思路。这里不追求完整复现某一年 challenge，而是帮助读者建立基本工程概念。

## Habitat 软件栈

Habitat 平台主要由两个部分组成：

| 组件 | 作用 |
| --- | --- |
| Habitat-Sim | 高性能三维仿真器，负责场景加载、渲染、传感器和物理交互 |
| Habitat-Lab | 高层任务库，负责定义任务、配置 agent、训练策略和计算评测指标 |

可以理解为：

```text
Habitat-Sim：
让 agent 在 3D 环境中“看见”和“移动”

Habitat-Lab：
告诉 agent 要做什么任务，并记录训练与评测结果
```

实际使用时，通常先安装 Habitat-Sim，再安装 Habitat-Lab。Habitat-Sim 更偏底层仿真，Habitat-Lab 更偏任务和算法接口。

## 推荐环境准备

官方推荐使用 Linux 和 conda 环境。不同 Habitat 版本之间依赖差异较大，因此复现某一年 challenge 时，应该优先查看该年份 challenge 页面或对应 GitHub 分支中的安装说明。

一个基础环境可以这样理解：

```text
conda 环境
-> Habitat-Sim
-> Habitat-Lab
-> 场景数据
-> 任务配置
-> agent / baseline
-> evaluation script
```

如果只是学习教程，不一定要一开始就完整跑通所有 challenge。可以先跑 Habitat-Lab quickstart 或 PointNav 示例，确认基本环境可用。

## Habitat-Sim 安装思路

Habitat-Sim 通常可以通过 conda 安装。官方文档中推荐使用 conda packages，并区分普通显示环境、headless 服务器和是否需要 physics 支持。

常见安装思路如下：

```bash
conda create -n habitat python=3.9 cmake=3.22
conda activate habitat
```

有显示器的机器可以尝试：

```bash
conda install habitat-sim -c conda-forge -c aihabitat
```

如果是在服务器上运行，没有显示器，通常需要 headless 版本：

```bash
conda install habitat-sim headless -c conda-forge -c aihabitat
```

如果任务涉及 physics 或 rearrangement，通常需要 bullet physics 支持：

```bash
conda install habitat-sim withbullet headless -c conda-forge -c aihabitat
```

注意：不同时间的官方版本可能会更新，具体命令应以当前 Habitat-Sim README 和对应 challenge 分支为准。这里的命令主要用于理解安装逻辑。

## Habitat-Lab 安装

Habitat-Lab 通常从 GitHub 克隆并安装。基础流程可以写成：

```bash
git clone https://github.com/facebookresearch/habitat-lab.git
cd habitat-lab
pip install -e habitat-lab
pip install -e habitat-baselines
```

如果只运行简单任务，可能只需要 Habitat-Lab 的基础部分；如果要运行 baseline 训练和评测，则还需要安装 habitat-baselines 相关依赖。

复现 challenge 时要特别注意版本对应关系：

```text
Habitat-Sim 版本
Habitat-Lab 版本
challenge starter code 分支
数据集版本
配置文件路径
```

这些版本不一致时，很容易出现 import error、配置文件找不到、scene 加载失败或指标不一致的问题。

## 数据集与场景资源

Habitat 任务通常需要下载对应场景数据。不同任务使用的数据集可能不同，例如 Matterport3D、Gibson、Replica、HM3D、HM3D-Semantics 或 ReplicaCAD 等。

可以把数据资源分成两类：

```text
场景数据：
三维房间、网格、纹理、语义标注等

任务数据：
episode 起点、目标位置、目标物体、目标图像、任务配置等
```

例如 ObjectNav 和 ImageNav 需要语义场景和 episode 文件；Rearrangement 则还需要可交互物体、容器、机器人和物理配置。

数据路径通常需要在配置文件中指定，例如：

```text
data/
├── scene_datasets/
├── datasets/
└── checkpoints/
```

环境能否正常运行，往往取决于数据路径是否与配置文件匹配。

## 快速运行思路

官方 Quickstart 中通常会通过 PointNav 任务展示 Habitat-Lab 的基本运行方式。一个最简流程可以理解为：

```text
加载任务配置
-> 创建 habitat.Env
-> reset 环境
-> 获取 observation
-> 输入动作
-> step 环境
-> 判断 episode 是否结束
```

伪代码形式如下：

```python
import habitat

config = habitat.get_config("benchmark/nav/pointnav/pointnav_habitat_test.yaml")
env = habitat.Env(config=config)

observations = env.reset()

while not env.episode_over:
    action = "move_forward"
    observations = env.step(action)

env.close()
```

这个示例的重点不是训练一个强 agent，而是理解 Habitat 任务的闭环交互形式：

```text
observation
-> action
-> new observation
-> next action
```

和静态数据集不同，agent 的每一步动作都会改变后续输入。

## 服务器运行注意事项

在服务器上运行 Habitat 时，常见问题主要来自显示和 GPU 渲染。

需要特别注意：

| 问题 | 说明 |
| --- | --- |
| headless 渲染 | 无显示器服务器通常需要 headless / EGL 支持 |
| CUDA 与驱动 | GPU 渲染和深度学习框架都依赖正确驱动 |
| 数据路径 | scene dataset 路径必须和配置文件一致 |
| Habitat-Sim / Habitat-Lab 版本 | 两者版本不匹配会导致接口或配置报错 |
| physics 支持 | Rearrangement 任务通常需要 withbullet |
| 内存与显存 | 大规模评测或高分辨率渲染会占用较多资源 |

如果只是学习 benchmark，可以先运行小规模 quickstart，不要一开始就运行完整 challenge 评测。

## 复现时的版本意识

Habitat Challenge 不同年份可能使用不同任务、不同数据集和不同代码分支。因此，复现时不能只安装最新版本，而要确认目标任务对应的版本。

比较稳妥的复现顺序是：

```text
确定要复现的 challenge 年份
-> 打开对应 challenge 页面
-> 找到 starter code 或 GitHub 分支
-> 按该分支要求安装 Habitat-Sim / Habitat-Lab
-> 下载对应数据集
-> 运行官方 quickstart 或 baseline
-> 再尝试修改模型
```

对于课程或教程介绍来说，只需要说明这个逻辑即可，不必强行完整复现所有年份任务。

## 本节小结

Habitat Challenge 的环境配置主要围绕 Habitat-Sim、Habitat-Lab、场景数据和任务配置展开。Habitat-Sim 提供三维仿真和传感器输出，Habitat-Lab 提供任务定义、训练接口和评测流程。

复现时最重要的是版本一致性。尤其是 challenge 年份、Habitat-Sim 版本、Habitat-Lab 分支、数据集路径和任务配置文件需要互相匹配。对于初学者来说，先跑通官方 quickstart，再理解 challenge 评测流程，是更稳妥的学习方式。
