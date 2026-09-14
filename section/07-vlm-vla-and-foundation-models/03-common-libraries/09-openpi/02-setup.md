# 8.5.1.2 环境安装

目标：安装 OpenPI 并固定代码版本，配置可复现的开发和训练环境。


## 学习目标

- 使用两种方式（官方 uv 和 conda）搭建 OpenPI 环境。
- 理解 `GIT_LFS_SKIP_SMUDGE` 和 git submodule 的作用。
- 固定代码版本和依赖版本，确保后续实验可复现。
- 通过简单验证确认环境安装成功。

## 获取代码

首先从 GitHub 克隆 OpenPI 源码：

```bash
git clone https://github.com/Physical-Intelligence/openpi.git
cd openpi
```


## 环境安装

OpenPI 使用 `uv` 管理 Python 依赖，Python 版本要求 3.11。下面介绍两种安装方式：官方推荐的 `uv sync` 方式，以及更适合国内用户的 conda 方式。

### 方式一：官方安装（uv sync）

如果你已经安装了 `uv`，可以直接使用官方推荐的 `uv sync` 命令同步所有依赖：

```bash
uv sync
```

如果需要使用 RLDS 格式的大规模数据集（如完整版 DROID），还需要安装 RLDS 相关依赖：

```bash
uv sync --group rlds
```

这种方式会自动创建虚拟环境并安装所有依赖，环境隔离由 `uv` 管理，不需要手动创建 conda 环境。

### 方式二：Conda 安装

如果你更习惯使用 conda 管理环境，或者网络环境不方便直接使用 `uv sync`，可以先用 conda 创建 Python 3.11 环境，再在环境内用 `uv pip install` 安装：

```bash
# 创建 conda 环境
conda create -n pi0 python=3.11 -y
conda activate pi0

# 在 conda 环境中安装 uv 和 OpenPI
pip install uv
GIT_LFS_SKIP_SMUDGE=1 uv pip install -e .
pip install pytest

```

> **说明**：`GIT_LFS_SKIP_SMUDGE=1` 的作用是跳过 LeRobot 依赖中的 Git LFS 大文件下载。OpenPI 依赖 LeRobot 作为数据格式层，但 LeRobot 仓库中包含大量机器人数据集的 LFS 指针文件，这些文件体积很大且在本教程中不需要，设置该环境变量可以显著加快安装速度并节省磁盘空间。

两种方式的区别：

| | 官方安装（uv sync） | Conda 安装 |
|---|---|---|
| 环境管理 | uv 自动管理虚拟环境 | conda 管理，更灵活 |
| 依赖解析 | uv.lock 锁定，复现性好 | `uv pip install -e .` 解析，依赖版本可能有浮动 |
| 适用场景 | 网络通畅、追求可复现 | 需要 conda 生态、网络受限 |



## 导航

- 返回父页：[OpenPI](../09-openpi.md)
- 上一节：[整体介绍](01-overview.md)
- 下一节：[π0 训练](03-pi0.md)
