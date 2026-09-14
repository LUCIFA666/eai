# 3. 本地安装完全指南 (Complete Local Installation Guide)

在正式运行 RLinf 之前，我们需要搭建一个稳定且高效的底层环境。RLinf 官方提供了 Docker 镜像与本地裸机安装两种方式，本节将重点对本地安装的全流程及常见编译问题进行详细说明。

## 3.1 安装方式对比与选择

在选择安装方式时，可以根据您的实际研发需求进行权衡：

* **Docker 镜像安装：**
    * *优势：* 环境一致性极高，重现性好，开箱即用，免去了繁琐的底层依赖配置。
    * *劣势：* 存在少量的性能开销；更重要的是，受限于容器隔离机制，在调用底层物理显卡渲染接口（如 Vulkan/EGL）或外接真实的机械臂 ROS 网络时，极易遇到黑屏或硬件端口丢失的问题。
    * *适用场景：* 快速原型验证、CI/CD 自动化流水线。
* **本地裸机安装（推荐）：**
    * *优势：* 灵活性极高，开发者可以自由定制 CUDA 算子，无容器开销，能完美调用物理渲染引擎和外部硬件。
    * *劣势：* 依赖宿主机的本地环境状态，配置过程有一定的学习曲线。
    * *适用场景：* 长期科研开发、具身智能算法定制、需要高频修改底层源码的场景。

鉴于具身智能任务的复杂性，本文后续将重点剖析**本地安装方法**，这对于有特定渲染需求或需要灵活定制的开发者更加友好。

## 3.2 第一步：前置环境与硬件基建检查

庞大的分布式训练对显卡驱动和编译器的版本有着严格的要求。在开始安装前，请务必核对当前节点的状态是否满足底层基线：

* **操作系统：** 推荐使用 Ubuntu 22.04 或更新版本。
* **NVIDIA 驱动：** 需要达到 535.183.06 及以上版本。
* **CUDA 工具包：** 强烈推荐使用 CUDA 12.1 或 12.4（这与后续许多预编译的 PyTorch 轮子高度兼容）。
* **cuDNN 版本：** 8.9 或更新。
* **Python 环境：** 3.10 或 3.11。

请在终端依次执行以下基础命令，快速自检您的系统状态：

```bash
lsb_release -a
nvidia-smi
nvcc --version
cat /usr/include/cudnn_version.h | grep CUDNN_MAJOR -A 2
python3 --version
pip3 --version

```

## 3.3 第二步：引入现代化包管理工具 uv

在处理包含大模型和复杂物理引擎的机器学习项目时，依赖树往往极其庞大。传统的 `pip` 在解析这些依赖时可能会耗费数十分钟甚至陷入死循环。
为了显著加快环境构建速度，我们推荐使用由 Rust 编写的现代化包管理器 `uv`。它具有极快的依赖解析速度和更好的版本管理能力。

```bash
pip install --upgrade uv
uv --version  # 确认输出 uv 0.x.x 版本即代表安装成功

```

## 3.4 第三步：克隆 RLinf 仓库

将 RLinf 的最新源码克隆至本地计算节点，并确保当前处于稳定的主分支：

```bash
git clone [https://github.com/RLinf/RLinf.git](https://github.com/RLinf/RLinf.git)
cd RLinf
git status  # 确认应位于 main 分支

```

## 3.5 第四步：场景化依赖安装与定制

RLinf 并没有将所有依赖打包进一个臃肿的 `requirements.txt` 中，而是提供了一个高度自动化的 `install.sh` 脚本。
该脚本通过核心参数组合来按需拉取依赖，保持系统整洁。核心概念包括：

* `target`：应用领域（`embodied` 代表机器人学习，`reason` 代表大语言模型推理）。
* `model`：具体模型架构（如 `openvla`, `openpi`, `pi0` 等）。
* `env`：模拟环境类型（如 `maniskill_libero`, `behavior`, `metaworld`）。
* `venv`：虚拟环境路径（默认为项目目录下的 `.venv`）。

### 3.5.1 场景 A：具身智能 + OpenVLA + ManiSkill（推荐入门）

OpenVLA 作为一个开源的视觉-语言-动作模型，在各类机器人任务上表现卓越。这是目前 RLinf 最成熟、最稳定的应用场景。安装过程通常需要 10-20 分钟（取决于网络与硬件）：

```bash
bash requirements/install.sh embodied --model openvla --env maniskill_libero

```
<img width="752" height="716" alt="dbdfc401946a4bb49ab6e40e4ddce931" src="https://github.com/user-attachments/assets/695f33da-f827-41b8-897f-2d3fa1881963" />

### 3.5.2 场景 B：具身智能 + π₀.₅ 模型

π₀.₅ 是最新一代的模型架构，其性能得到了进一步提升，并且全面支持 LoRA 轻量级微调，适合算力有限但希望探索前沿架构的团队：

```bash
bash requirements/install.sh embodied --model openpi --env maniskill_libero

```
<img width="2012" height="1226" alt="image" src="https://github.com/user-attachments/assets/23543b99-62cb-4f9c-805f-2df30c143504" />

### 3.5.3 场景 C：推理增强 + Megatron + SGLang/vLLM

此配置专为大模型数学逻辑推理增强（Reasoning）设计。它会自动安装 Megatron-LM（大规模训练引擎）、SGLang 和 vLLM（高吞吐推理引擎），以及相应的强化学习框架（如 GRPO 算法）。

**⚠️ 编译排错指南：** 在编译此类底层环境时，最常见的报错是找不到 C++ 头文件导致编译中断。为避免踩坑，请务必在运行脚本前，将 CUDA 和 cuDNN 的路径显式注入环境变量：

```bash
# 注入编译所需的路径变量
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export CPATH=$CUDA_HOME/include:$CPATH

# 更新系统工具链
sudo apt-get update
sudo apt-get install build-essential

# 替换为您实际的 Python 环境路径以链接 cuDNN 头文件
export CPLUS_INCLUDE_PATH=/root/my_experiments/reason_env/lib/python3.11/site-packages/nvidia/cudnn/include:$CPLUS_INCLUDE_PATH
export C_INCLUDE_PATH=/root/my_experiments/reason_env/lib/python3.11/site-packages/nvidia/cudnn/include:$C_INCLUDE_PATH

# 正式执行安装
bash requirements/install.sh reason

```
<img width="1546" height="956" alt="image" src="https://github.com/user-attachments/assets/9c33446a-5aff-4ed7-b123-0684e0530c52" />

### 3.5.4 自定义虚拟环境位置

默认情况下，脚本会在当前目录下创建 `.venv` 文件夹。如果您需要管理多个不同配置的实验环境，可以通过 `--venv` 参数自定义路径：

```bash
bash requirements/install.sh reason --env maniskill_reason --venv ~/my_experiments/reason_env
source ~/my_experiments/reason_env/bin/activate

```
<img width="2122" height="1336" alt="image" src="https://github.com/user-attachments/assets/b0524845-78a4-4662-b889-02c1d776c14d" />

## 3.6 第五步：激活环境与 Flash-Attention 安装优化

依赖安装完毕后，请激活您的虚拟环境。
在这一步，许多开发者会在从源码编译 `flash-attention` 时卡住。由于该库包含大量的 CUDA C++ 算子，源码编译通常需要半小时以上，且极易因节点内存不足（OOM）而失败。

为了提高效率，强烈建议绕过源码编译，直接根据您的 CUDA 和 PyTorch 版本下载预编译好的 `.whl` 文件进行安装：

```bash
# 激活环境
source .venv/bin/activate
which python  # 确认输出路径指向刚才创建的虚拟环境

# 下载并安装与 CUDA 12 和 PyTorch 2.6 匹配的 flash-attention 预编译包
wget [https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp311-cp311-linux_x86_64.whl](https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp311-cp311-linux_x86_64.whl)
python -m pip install flash_attn*.whl

# 确认 PyTorch 版本
python -c "import torch; print(torch.__version__)"  # 预期输出 2.6 或更高版本

```

## 3.7 第六步：最终系统健康检查

在正式投入耗时漫长的分布式训练之前，执行一次全面的系统健康自检是非常必要的。这能帮您排除诸如驱动掉线、动态链接库缺失等底层隐患。

请在终端依次执行以下 Python 测试代码：

```python
# 1. 检查物理 GPU 的可用性与识别情况
python -c "import torch; print(f'GPUs available: {torch.cuda.device_count()}')"
python -c "import torch; print([torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())])"

# 2. 检查 RLinf 核心组件的加载状态
python -c "from rlinf.models import get_model; print('Model loading: OK')"
python -c "from rlinf.trainer import PPOTrainer; print('PPO Trainer: OK')"
python -c "from rlinf.envs import make_env; print('Environment creation: OK')"

```

如果您在终端中看到了所有预期的硬件名称以及连续的三个 `OK` 输出，恭喜您！您的服务器已经成功配置好下一代强化学习基础设施。接下来，即可进入正式的模型训练与评测环节。

```

```
