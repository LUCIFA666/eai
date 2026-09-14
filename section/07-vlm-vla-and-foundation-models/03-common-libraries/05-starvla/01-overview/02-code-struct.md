# 代码结构

目标：知道 StarVLA 的关键目录在哪里，以及每个目录在完整流程中负责什么。


## 占位符约定

在这里我们对占位符进行说明和约定，读者可以根据将占位符替换为自己的路径。

| 占位符 | 含义 | 示例 |
|---|---|---|
| `<STARVLA_ROOT>` | StarVLA 仓库根目录 | `/workspace/starVLA` |
| `<MODEL_ROOT>` | 预训练模型保存位置 | `/data/pretrained_models` |
| `<DATA_ROOT>` | 数据集保存位置 | `/data/robot_datasets` |
| `<RUN_DIR>` | 训练输出根目录 | `/data/starvla_runs` |
| `<CKPT_PATH>` | 某次训练保存的具体权重文件 | `<RUN_DIR>/<run_id>/checkpoints/steps_*.pt` |

## 克隆仓库

```bash
git clone https://github.com/starVLA/starVLA.git <STARVLA_ROOT>
cd <STARVLA_ROOT>
```

克隆完成后，后续命令默认在 `<STARVLA_ROOT>` 下执行。

## 顶层结构

```text
<STARVLA_ROOT>/
├── starVLA/        # 核心 Python 包：数据、模型、训练
├── deployment/     # 把 checkpoint 包装成推理服务
├── examples/       # 各 benchmark 的数据、训练和评测入口
├── docs/           # 官方说明文档
└── assets/         # 官方图和结果图
```

我们先看三个目录：`examples/`、`starVLA/`、`deployment/`。`examples/` 是实验启动的原点，`starVLA/` 里是核心实现，`deployment/` 负责推理服务。

## 初步理解

建议先从 LIBERO 部分的代码入门。它的目录通常包含：

```text
examples/LIBERO/
├── data_preparation.sh              # 下载或整理 LIBERO 数据
├── train_files/
│   ├── starvla_cotrain_libero.yaml  # 指定模型、数据和训练超参
│   ├── run_libero_train.sh
│   ├── modality.json                # 说明哪些字段是图像、状态、动作和语言
│   └── data_registry/
│       └── data_config.py           # 定义动作维度、归一化方式和数据混合名
└── eval_files/
    ├── run_policy_server.sh
    ├── eval_libero.sh         
    ├── eval_libero.py               # 运行 LIBERO 环境评测
    └── model2libero_interface.py    # 把环境观察转换成 StarVLA 推理请求
```

## 核心包

训练用包：

| 路径 | 作用 |
|---|---|
| `starVLA/dataloader/__init__.py` | `build_dataloader()` 怎样创建数据加载器 |
| `starVLA/dataloader/lerobot_datasets.py` | LeRobot 样本怎样变成 StarVLA batch |
| `starVLA/model/framework/base_framework.py` | `build_framework()`、`forward()`、`predict_action()` |
| `starVLA/model/framework/VLM4A/` | QwenOFT、QwenFast、QwenPI、QwenGR00T |
| `starVLA/model/modules/action_model/` | MLP、FAST、flow matching 等动作头 |
| `starVLA/training/train_starvla.py` | 纯 VLA 训练入口 |
| `starVLA/training/train_starvla_cotrain.py` | VLA+VLM 协同训练入口 |

评测用包：

| 路径 | 作用 |
|---|---|
| `deployment/model_server/server_policy.py` | 启动推理服务 |
| `deployment/model_server/policy_wrapper.py` | 加载 checkpoint，并调用 `predict_action()` |
| `deployment/model_server/policy_norm_processor.py` | 根据训练统计量还原动作尺度 |
| `deployment/model_server/tools/websocket_policy_client.py` | benchmark 侧请求模型 |

部署部分的分工很清楚：服务端加载模型并输出动作，benchmark 侧负责运行环境并发送观察。

## 常用搜索

```bash
# 找所有 framework 名称
rg "FRAMEWORK_REGISTRY.register" starVLA/model/framework

# 找某个模型的训练配置
rg "QwenGR00T|QwenOFT|QwenFast|QwenPI" examples

# 找数据混合注册
rg "DATASET_NAMED_MIXTURES|data_mix" examples starVLA

# 找推理接口
rg "def predict_action" starVLA/model/framework
```

## 小结

- `examples/` 是实验入口，先从 LIBERO 读最顺。
- `starVLA/` 是核心实现，重点看 dataloader、framework 和 training。
- `deployment/` 负责把 checkpoint 变成可被 benchmark 调用的策略。
- 读代码时从一个 YAML 配置开始，沿着数据、模型、训练、部署向后追。

## 动手练习

1. 在 `<STARVLA_ROOT>` 下运行 `rg -n "FRAMEWORK_REGISTRY.register" starVLA/model/framework`，记录出现的 framework 名称。
2. 运行 `rg -n "name:|data_mix|data_root_dir" examples/LIBERO/train_files/starvla_cotrain_libero.yaml`，找到模型名称、数据混合名和数据根目录字段。
3. 运行 `rg -n "image|lang|state|unnorm_key|action_chunk_size" examples/LIBERO/eval_files/model2libero_interface.py`，记录 client 给 server 的字段。

## 导航

- 上一节：[01 StarVLA 是什么](01-what-is-starvla.md)
- 返回上级：[认识 StarVLA](../01-overview.md)
- 下一节：[03 章节预览](03-chap-review.md)
