# 安装与渲染依赖

目标：安装 ManiSkill3、PyTorch 和渲染相关依赖。


## 固定路径环境

本教程不使用 conda 管理 ManiSkill3，而是把 venv 固定到：

```bash
/path/to/env/maniskill3
```

配套目录：

```bash
/path/to/env/pip_cache
/path/to/env/maniskill_data
/path/to/env/sapien_cache
```

源码目录：

```bash
/path/to/ManiSkill
```

## 克隆源码

如果服务器还没有源码：

```bash
cd /path/to
git clone https://github.com/mani-skill/ManiSkill.git
cd ManiSkill
```


## 创建 venv

```bash
python3 -m venv /path/to/env/maniskill3
source /path/to/env/maniskill3/bin/activate

export PIP_CACHE_DIR=/path/to/env/pip_cache
python -m pip install --upgrade pip setuptools wheel
```

## 安装 Torch 和 ManiSkill

```bash
python -m pip install torch

cd /path/to/ManiSkill
python -m pip install -e .
```

## 设置环境变量

```bash
mkdir -p /path/to/env/maniskill_data

export PIP_CACHE_DIR=/path/to/env/pip_cache
export MS_ASSET_DIR=/path/to/env/maniskill_data
export CUDA_VISIBLE_DEVICES=0
```

## Vulkan 渲染依赖

无渲染的 state-based 仿真不依赖 Vulkan。但如果要使用：

```text
render_mode="human"
obs_mode="rgb"
obs_mode="rgbd"
obs_mode="pointcloud"
--save-video
```

就需要检查：

```bash
vulkaninfo
```

如果没有安装环境，则需要
```bash
sudo apt-get install -y libvulkan1 vulkan-tools
```

后续运行baselin，需要安装
pip install tensorboard

## 导航

- 上一节：[ManiSkill Task 种类](02-task-types.md)
- 返回上级：[ManiSkill3](../08-maniskill3-benchmark.md)
- 下一节：[用 Gymnasium 创建任务](04-gymnasium-create-task.md)
