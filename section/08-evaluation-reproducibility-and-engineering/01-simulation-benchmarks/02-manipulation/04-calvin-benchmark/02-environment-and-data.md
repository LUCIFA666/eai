# 9.1.4.2 环境与数据准备

本节介绍如何在服务器上准备 CALVIN 的运行环境和数据集。

## 创建 Python 环境



```bash
conda create -n calvin python=3.8 -y
conda activate calvin
```


## 安装项目依赖

在项目根目录执行：

```bash
cd /path/to/calvin
sh install.sh
```

在安装时，会遇到一些问题，这时运行：

```bash
pip install "setuptools==57.5.0" wheel
pip install cmake==3.18.4.post1
```

再重新运行
```bash
sh install.sh
```

然后再
```bash
cd /path/to/calvin/calvin_models
pip install -e .
```
## 下载 debug 数据集

正式数据集较大，教程中使用 debug 数据集跑通流程：

```bash
cd /path/to/calvin/dataset
sh download_data.sh debug
```


下载完成后进行解压：

```bash
unzip calvin_debug_dataset.zip
```

解压后应该得到：

```text
/path/to/calvin/dataset/calvin_debug_dataset/
├── training/
└── validation/
```


## 下载正式数据集

CALVIN 总数据量过大，包含 D、ABC、ABCD 和 debug 四个数据集。

| 参数 | 数据集 | 大小 | 用途 |
|---|---|---:|---|
| `D` | `task_D_D` | 约 166 GB | 单环境 D-D 训练与评估 |
| `ABC` | `task_ABC_D` | 约 517 GB | 零样本 ABC-D 设置 |
| `ABCD` | `task_ABCD_D` | 约 656 GB | 多环境 ABCD-D 设置 |
| `debug` | `calvin_debug_dataset` | 约 1.3 GB | 快速验证环境和代码流程 |

下载方式：

```bash
cd /path/to/calvin/dataset
sh download_data.sh D
sh download_data.sh ABC
sh download_data.sh ABCD
```



