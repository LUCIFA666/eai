# 数据准备

目标：下载 LIBERO 数据集和基础模型，整理成 StarVLA 训练所需的目录结构。

## 克隆仓库

```bash
git clone https://github.com/StarVLA-Official/starVLA.git <STARVLA_ROOT>
cd <STARVLA_ROOT>
```

## 下载 LIBERO 数据

**前置条件**：机器可以访问数据下载源，`<DATA_ROOT>` 有足够空间。

```bash
cd <STARVLA_ROOT>
export DEST=<DATA_ROOT>
bash examples/LIBERO/data_preparation.sh
```

这个脚本会准备：

1. 四个 LIBERO LeRobot 数据集：`libero_spatial`、`libero_object`、`libero_goal`、`libero_10`。
2. VLM 协同训练数据，例如 `LLaVA-OneVision-COCO`。
3. 每个子数据集需要的 `meta/modality.json` 字段映射文件。

准备完成后，目录结构如下：

```text
<DATA_ROOT>/
├── LEROBOT_LIBERO_DATA/
│   ├── libero_spatial_no_noops_1.0.0_lerobot/
│   │   └── meta/modality.json
│   ├── libero_object_no_noops_1.0.0_lerobot/
│   │   └── meta/modality.json
│   ├── libero_goal_no_noops_1.0.0_lerobot/
│   │   └── meta/modality.json
│   └── libero_10_no_noops_1.0.0_lerobot/
│       └── meta/modality.json
└── LLaVA-OneVision-COCO/
```

`modality.json` 告诉 StarVLA 哪些字段是相机图像、哪些字段是状态、哪些字段是动作。来源是：

```text
examples/LIBERO/train_files/modality.json
```

## 数据注册

`examples/LIBERO/train_files/data_registry/data_config.py` 中定义了数据混合名：

```python
DATASET_NAMED_MIXTURES = {
    "libero_all": [
        ("libero_object_no_noops_1.0.0_lerobot", 1.0, "libero_franka"),
        ("libero_goal_no_noops_1.0.0_lerobot", 1.0, "libero_franka"),
        ("libero_spatial_no_noops_1.0.0_lerobot", 1.0, "libero_franka"),
        ("libero_10_no_noops_1.0.0_lerobot", 1.0, "libero_franka"),
    ],
}
```

`libero_franka` 对应 7 维动作（`x, y, z, roll, pitch, yaw, gripper`），状态通常是 8 维（多一个 `pad`）。

训练时通过 `--datasets.vla_data.data_mix libero_all` 使用全量数据，调试时用 `libero_goal` 减小数据量。

## 下载基础模型

LIBERO 示例常用 Qwen 系列 VLM：

```bash
huggingface-cli download Qwen/Qwen3-VL-4B-Instruct \
  --local-dir <MODEL_ROOT>/Qwen3-VL-4B-Instruct
```

如果训练 FAST 变体，需要带动作 token 的版本：

```bash
huggingface-cli download StarVLA/Qwen3-VL-4B-Instruct-Action \
  --local-dir <MODEL_ROOT>/Qwen3-VL-4B-Instruct-Action
```

下载完成后，本地模型目录应包含 `config.json`、tokenizer/processor 文件和权重文件。OFT、PI、GR00T 这类连续动作头通常用普通 VLM 即可，只有 FAST 需要带 `<robot_action_*>` 特殊 token 的版本。

## 小结

- LIBERO 数据通过 `data_preparation.sh` 下载，完成后检查每个子集的 `meta/modality.json`。
- `data_config.py` 定义 `data_mix` 名字和对应子数据集的权重与 robot type。
- 调试时先用 `libero_goal`，正式训练用 `libero_all`。
- OFT / PI / GR00T 用普通 VLM；FAST 需要带动作 token 的版本。

## 动手练习

1. 运行 `find <DATA_ROOT>/LEROBOT_LIBERO_DATA -name "modality.json" | sort`，确认四个子数据集都有 `meta/modality.json`。
2. 运行 `rg -n "libero_franka|action_keys|state_keys" examples/LIBERO/train_files/data_registry/data_config.py`，找到 robot type 的动作维度和字段定义。
3. 用 `ls <MODEL_ROOT>/Qwen3-VL-4B-Instruct` 确认模型目录存在且包含 `config.json`。

## 导航

- 上一节：[LIBERO 端到端实战](../07-libero-end-to-end.md)
- 返回上级：[LIBERO 端到端实战](../07-libero-end-to-end.md)
- 下一节：[02 训练](02-training.md)
