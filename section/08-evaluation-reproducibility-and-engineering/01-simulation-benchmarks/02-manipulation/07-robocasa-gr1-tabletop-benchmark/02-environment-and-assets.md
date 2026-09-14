# 9.1.6.2 环境配置与 Assets


本页给出可复现的安装流程。与官方 README略微有些不同。 

## 创建环境

以下示例把环境安装到 `/path/to/env/robocasa-gr1`。如果使用普通 Conda 环境名，可跳过下面步骤，直接 `conda create -n robocasa python=3.10`就可以。

```bash
cd /path/to

mkdir -p /path/to/env/conda_pkgs
mkdir -p /path/to/env/tmp
mkdir -p /path/to/env/pip_cache

CONDA_PKGS_DIRS=/path/to/env/conda_pkgs \
CONDA_ENVS_PATH=/path/to/env \
conda create -p /path/to/env/robocasa-gr1 -c conda-forge python=3.10 -y

conda activate /path/to/env/robocasa-gr1

export TMPDIR=/path/to/env/tmp
export PIP_CACHE_DIR=/path/to/env/pip_cache
```

`TMPDIR` 和 `PIP_CACHE_DIR` 建议固定到数据盘。安装 PyTorch、TensorFlow、CUDA wheel 和 flash-attn 时会产生较大的临时文件，如果默认写到 `/tmp`，根分区空间不足时会失败。

## 安装 Isaac-GR00T

```bash

git clone https://github.com/NVIDIA/Isaac-GR00T.git
cd Isaac-GR00T

pip install --upgrade pip setuptools wheel
pip install -e ".[base]"
pip install --no-build-isolation flash-attn==2.7.1.post4
cd ..
```

`flash-attn` 要放在 `pip install -e ".[base]"` 之后安装，因为它构建时需要先能 import `torch`。

## 安装 robosuite

官方 README 没有固定 robosuite 版本，本文建议使用 `v1.5.1`：

```bash

git clone https://github.com/ARISE-Initiative/robosuite.git
cd robosuite
git checkout v1.5.1
pip install -e .
python robosuite/scripts/setup_macros.py
cd ..
```

随后固定 MuJoCo 和 mink：

```bash
pip install mujoco==3.2.6 mink==0.0.5
pip install -e robosuite --config-settings editable_mode=compat --no-deps
```

这样处理的原因是：`robocasa-gr1-tabletop-tasks` 会检查 `mujoco==3.2.6` 和 `robosuite` 的版本；而较新的 robosuite 会倾向安装更新的 MuJoCo。`editable_mode=compat` 则用于确保 `robosuite.__version__` 能从源码包中正确读取。

## 安装 RoboCasa-GR1 Tabletop Tasks

```bash

git clone https://github.com/robocasa/robocasa-gr1-tabletop-tasks.git
pip install -e robocasa-gr1-tabletop-tasks

```


## 下载 assets

```bash
cd robocasa-gr1-tabletop-tasks
python robocasa/scripts/download_tabletop_assets.py -y
```

下载脚本会获取 environment textures、fixtures、objaverse objects、generative textures、sketchfab assets 和 lightwheel assets。这些文件决定场景纹理、容器、物体模型和任务能否启动。
