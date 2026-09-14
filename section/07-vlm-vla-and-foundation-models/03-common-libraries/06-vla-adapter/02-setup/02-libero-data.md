# LIBERO 数据

目标：把 VLA-Adapter 训练脚本能读取的 LIBERO RLDS 数据放到 `data/libero/`，并确认 `data_root_dir` 和 `dataset_name` 对得上。

本页聚焦于 LoRA 微调需要的 RLDS / TFDS 演示数据。

## 下载 RLDS 数据

LIBERO RLDS 数据在 Hugging Face dataset repo。进入源码根目录后下载到 `data/`：

```bash
cd /path/to/VLA-Adapter
mkdir -p data

git clone git@hf.co:datasets/openvla/modified_libero_rlds data/modified_libero_rlds
```

如果无法连接 Hugging Face，可以通过镜像站下载：

```bash
export HF_ENDPOINT=https://hf-mirror.com

hf download openvla/modified_libero_rlds \
  --repo-type dataset \
  --local-dir data/modified_libero_rlds
```

这批数据包含四个训练脚本会读取的目录：`libero_spatial_no_noops`、`libero_object_no_noops`、`libero_goal_no_noops`、`libero_10_no_noops`，合计约 10GB。

## 放置数据

下载得到的 `modified_libero_rlds/` 外层目录要去掉，让四个数据集目录直接落在 `data/libero/` 下：

```bash
mkdir -p data/libero
mv data/modified_libero_rlds/libero_*_no_noops data/libero/
```

整理后的结构：

```text
VLA-Adapter/
└── data/
    └── libero/
        ├── libero_10_no_noops/
        ├── libero_goal_no_noops/
        ├── libero_object_no_noops/
        └── libero_spatial_no_noops/
```

训练命令据此读取数据：

```bash
--data_root_dir data/libero
--dataset_name libero_spatial_no_noops
```

`data/libero` 下必须直接是这四个 `*_no_noops` 目录。如果多一层 `modified_libero_rlds/`，或者数据集目录仍带 `modified_` 前缀，训练脚本会找不到 builder。

## 数据体检

进入 VLA-Adapter 源码根目录后，可以做一次只读检查：

```bash
ls data/libero
find data/libero -maxdepth 2 -type d | sort | head -40
```

`ls data/libero` 应该能看到四个目标训练数据集目录：`libero_10_no_noops`、`libero_goal_no_noops`、`libero_object_no_noops`、`libero_spatial_no_noops`。

`find` 的预期输出里通常会看到每个数据集下的 `1.0.0` 子目录，例如：

```text
data/libero/libero_10_no_noops/1.0.0
data/libero/libero_goal_no_noops/1.0.0
data/libero/libero_object_no_noops/1.0.0
data/libero/libero_spatial_no_noops/1.0.0
```

如果希望进一步确认 Spatial 数据集是否完整，可以运行：

```bash
ls data/libero/libero_spatial_no_noops
ls data/libero/libero_spatial_no_noops/1.0.0
find data/libero/libero_spatial_no_noops -type f | wc -l
```

`libero_spatial_no_noops` 下可以看到 `1.0.0`。`1.0.0/` 下可以看到 `dataset_info.json`、`features.json` 和 16 个 `libero_spatial-train.tfrecord-xxxxx-of-00016` 分片。`find ... | wc -l` 输出 `18` 是合理结果，表示 16 个 tfrecord 文件加 2 个 json 元数据文件。不同数据集的分片数不同，这里的 `18` 只用于判断 Spatial 目录是否符合当前官方数据结构。

`1.0.0` 这层目录不是可选命名。RLDS pipeline 里 `--dataset_name` 经 `tfds.builder(name, data_dir=...)`（`prismatic/vla/datasets/rlds/dataset.py:202`）按 `data_root_dir/<dataset_name>/<version>/` 的 TFDS 目录约定定位数据，`1.0.0` 是 TFDS 的版本目录写法，`dataset_info.json` 里的 `version` 字段也是 `1.0.0`。因此数据集目录名和 `1.0.0` 都要保持原样，多一层 `modified_libero_rlds/` 或改掉版本号，builder 都会找不到数据。每个 dataset 的 image / state 字段映射由 OXE registry（`prismatic/vla/datasets/rlds/oxe/configs.py`）记录，`libero_spatial_no_noops` 的 primary image、wrist image 和 EEF / gripper state key 都在那里。

## 训练和评测使用的名称

评测和训练会用到两套相近但不同的名称。VLA-Adapter 的评测脚本使用 `task_suite_name`：

| 评测 suite | `run_libero_eval.py` 参数 |
| --- | --- |
| Spatial | `--task_suite_name libero_spatial` |
| Object | `--task_suite_name libero_object` |
| Goal | `--task_suite_name libero_goal` |
| Long | `--task_suite_name libero_10` |

训练脚本使用 `dataset_name`，对应的是 RLDS 数据集目录名：

| 训练数据 | `finetune.py` 参数 |
| --- | --- |
| Spatial | `--dataset_name libero_spatial_no_noops` |
| Object | `--dataset_name libero_object_no_noops` |
| Goal | `--dataset_name libero_goal_no_noops` |
| Long | `--dataset_name libero_10_no_noops` |

`*_no_noops` 出现在训练的 `dataset_name` 中；评测的 `task_suite_name` 使用不带 `_no_noops` 的名称。

## 导航

- 上一节：[环境安装](01-environment.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[基础 VLM 与 Prismatic 配置](03-pretrained-backbone.md)
