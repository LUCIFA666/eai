# 环境与数据准备

在 LIBERO 上复现 OpenVLA-OFT 之前，需要先备齐三部分：装好 PyTorch 与 Flash Attention 2 的 conda 环境、LIBERO 仿真依赖、RLDS 格式的 LIBERO 数据。这套依赖的版本互相牵制，本页给出每一步的命令、预期结果和需要固定的版本。

## conda 环境

```bash
conda create -n openvla-oft python=3.10 -y
conda activate openvla-oft

# PyTorch 按本机 CUDA 选命令；论文结果用 2.2.0
pip3 install torch==2.2.0 torchvision torchaudio

git clone https://github.com/moojink/openvla-oft.git
cd openvla-oft
pip install -e .

# 训练需要 Flash Attention 2
pip install packaging ninja
ninja --version; echo $?      # 应返回 0
pip install "flash-attn==2.5.5" --no-build-isolation
```

`flash-attn` 通过源码编译安装，`ninja --version` 退出码不是 0 时编译会异常缓慢或失败；编译报错时先 `pip cache remove flash_attn` 清掉残留缓存再重装。论文结果在 Python 3.10.14、PyTorch 2.2.0 和作者的 transformers v4.40.1 fork 上得到，版本尽量对齐，换用其他 GPU 时成功率可能有小幅波动。

## LIBERO 仿真环境

```bash
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git
pip install -e LIBERO
pip install -r experiments/robot/libero/libero_requirements.txt
```

LIBERO 的 `setup.py` 没有正确声明 packages，`pip install -e` 生成的 editable finder 映射为空，装完后 `import libero` 仍报 `No module named 'libero'`。把 LIBERO 源码根目录加入 `PYTHONPATH` 即可解析，写进环境激活脚本或每次运行前 export：

```bash
export PYTHONPATH=/PATH/TO/LIBERO:$PYTHONPATH
```

无显示器的服务器需启用离屏渲染，否则 LIBERO 无法建立仿真环境：

```bash
export MUJOCO_GL=egl
export MUJOCO_EGL_DEVICE_ID=0     # 必须与 CUDA_VISIBLE_DEVICES 指同一张物理卡
```

`robosuite` 初始化时断言 `MUJOCO_EGL_DEVICE_ID in CUDA_VISIBLE_DEVICES`，渲染卡和计算卡必须是同一张，换卡时两个变量一起改。

## 版本固定

LIBERO 的依赖会与 PyTorch、TensorFlow 对 numpy、protobuf、mujoco 的版本要求冲突，一次性固定到兼容版本即可：

```bash
pip install "numpy==1.26.4" "opencv-python==4.11.0.86" \
            "protobuf==3.20.3" "tensorflow-metadata==1.16.1" "wandb==0.19.8" \
            "mujoco==2.3.7"
```

其中 protobuf 的冲突只在实际运行评测或训练脚本、加载到 tensorflow-datasets 时才暴露成 `ImportError: cannot import name 'runtime_version' from 'google.protobuf'`，裸 `import` 不会触发，因此不能只凭裸 import 通过就判定环境就绪。

## LIBERO 数据（RLDS）

微调用的是 RLDS 格式的 LIBERO 数据，四个套件（Spatial、Object、Goal、10）约 10 GB：

```bash
hf download openvla/modified_libero_rlds \
  --repo-type dataset \
  --local-dir /PATH/TO/RLDS
```

`--repo-type dataset` 必须加，`hf` 默认按 model 仓库查找，`modified_libero_rlds` 是 dataset 仓库，漏掉会解析失败。数据集名带 `_no_noops` 后缀，表示滤掉了近零动作的样本。评测官方 checkpoint 不需要这份数据，只有自己微调时才用。

## 导航

- 上一节：[推理调用链](04-inference-path.md)
- 返回上级：[OpenVLA-OFT](../01-openvla-oft.md)
- 下一节：[训练](06-training.md)
