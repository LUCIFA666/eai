# 安装与版本检查

SimplerEnv 的安装链路涉及多个依赖，其中最关键的是 NumPy 版本。这一节从零开始，把创建 conda 环境、克隆仓库、安装依赖、验证版本走通，并把最常见的 NumPy 版本冲突问题提前说明。

## 前置概念

读这一节前，建议先理解（详见 [SimplerEnv 是什么](01-what-is-simplerenv.md)）：

- **SimplerEnv 的定位**：它是一个 real-to-sim 评测环境，依赖 ManiSkill2_real2sim 提供底层任务。
- **smoke test 的目标**：验证环境链路，不是让策略完成任务。

## 本节目标

读完并跑完本节后，你应该能做到：

1. 从零创建一个干净的 conda 环境，安装 SimplerEnv 及其依赖。
2. 理解为什么 `numpy<2.0` 是本节最关键的版本约束。
3. 在 NumPy 被意外升级后，执行修复命令降回正确版本。
4. 通过版本检查脚本确认 `simpler_env` 能正常导入、任务表正确加载。

## 1. 创建 conda 环境

```bash
conda create -n simpler_env_clean python=3.10 -y
conda activate simpler_env_clean
```

## 2. 克隆仓库

SimplerEnv 依赖子模块，所以克隆时要带上 `--recurse-submodules`。

```bash
git clone https://github.com/simpler-env/SimplerEnv --recurse-submodules
cd SimplerEnv
```

## 3. 安装依赖

官方安装说明要求 `numpy<2.0`。实际排错时，如果 NumPy 被升级到 2.x，`env.reset()` 可能正常，但 `env.step()` 会在 IK 求解阶段崩溃。因此本节固定为 `numpy==1.24.4`，并把 OpenCV 固定到不会强制升级 NumPy 2.x 的版本。

```bash
python -m pip install --upgrade pip
python -m pip install "numpy==1.24.4" "opencv-python==4.9.0.80" imageio imageio-ffmpeg "setuptools<81"

cd ManiSkill2_real2sim
python -m pip install -e .

cd ..
python -m pip install -e .
```

如果装完后发现 NumPy 又变成了 2.x，执行下面的修复命令：

```bash
python -m pip uninstall -y numpy opencv-python opencv-python-headless opencv-contrib-python opencv-contrib-python-headless
python -m pip install --no-cache-dir --force-reinstall "numpy==1.24.4" "opencv-python==4.9.0.80" imageio imageio-ffmpeg "setuptools<81"

cd ~/SimplerEnv/ManiSkill2_real2sim
python -m pip install -e . --no-deps

cd ~/SimplerEnv
python -m pip install -e . --no-deps
```

## 4. 检查版本

```bash
python - <<'PY'
import sys
import numpy
import cv2
import simpler_env

print("Python:", sys.executable)
print("NumPy:", numpy.__version__)
print("OpenCV:", cv2.__version__)
print("Number of tasks:", len(simpler_env.ENVIRONMENTS))
PY
```

本次输出：

```text
Python: /home/hndx/anaconda3/envs/simpler_env_clean/bin/python
NumPy: 1.24.4
OpenCV: 4.9.0
Number of tasks: 25
```

这里看到 `Number of tasks: 25`，说明 `simpler_env` 已经能正常导入，并且任务表被正确加载。如果 NumPy 显示 `2.x`，说明依赖链条里某个包把它升级了——返回第 3 步执行修复命令。

## 小结

- 安装验证的核心证据是：`simpler_env` 能导入、任务表能加载、`Number of tasks` 输出为 25。
- NumPy 版本是本节最关键的依赖约束，应固定在 `numpy==1.24.4`，避免 IK 求解阶段崩溃。
- 如果 OpenCV 安装后把 NumPy 升级到 2.x，需要重新锁定 `opencv-python==4.9.0.80` 并用 `--no-deps` 安装 editable 包。

## 导航

- 上一节：[SimplerEnv 是什么](01-what-is-simplerenv.md)
- 返回上级：[SimplerEnv](../09-simplerenv-benchmark.md)
- 下一节：[代码架构](03-architecture.md)
