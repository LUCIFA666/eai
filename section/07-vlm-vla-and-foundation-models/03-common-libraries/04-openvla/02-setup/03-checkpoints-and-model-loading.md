# Checkpoint 与模型加载

目标：区分 OpenVLA 常见 checkpoint 类型，知道 HF AutoClass、本地目录和 Prismatic 训练路径分别怎样加载。

OpenVLA 的 checkpoint 名称容易混在一起。最小推理、LoRA 微调、full fine-tuning、LIBERO 评测和本地部署使用的 checkpoint 形态不同，加载路径也不同。本页先把这些类型分开，后面检查 `unnorm_key`、processor 和 action shape 时，可以直接对到对应的加载路径。

## 常见 checkpoint

| Checkpoint | 主要用途 | 读取方式 |
| --- | --- | --- |
| `openvla/openvla-7b` | 主模型，HF 推理和 LoRA 微调的常用起点。 | `AutoProcessor` + `AutoModelForVision2Seq`。 |
| `openvla/openvla-7b-v01` | 早期模型，README 也写作 `openvla-v01-7b`。 | HF AutoClasses；prompt 格式走 v0.1 分支。 |
| `openvla/openvla-7b-prismatic` | full fine-tuning / Prismatic 训练路径。 | `vla-scripts/train.py` 和 `prismatic.models.load_vla()`。 |
| `openvla/openvla-7b-finetuned-libero-*` | 官方 LIBERO suite 微调 checkpoint。 | HF AutoClasses；评测时配合对应 suite 的统计量。 |
| 本地 fine-tuned checkpoint 目录 | LoRA 或 full fine-tuning 后的本地推理与部署。 | HF AutoClasses；本地目录还要带上 processor 和统计量文件。 |

`openvla/openvla-7b` 对应当前主线的 DINOv2 + SigLIP + Llama 2 结构，通常走 Hugging Face AutoClass 加载路径。`openvla/openvla-7b-v01` 是较早版本，视觉 backbone 和 prompt 处理分支都不同；遇到旧 checkpoint 时，要先确认它是不是 v0.1 系列。

## HF AutoClass 加载

主模型和 Hugging Face 上的 fine-tuned checkpoint 可以直接用 AutoClasses：

```python
import torch
from transformers import AutoModelForVision2Seq, AutoProcessor

model_id = "openvla/openvla-7b"

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
vla = AutoModelForVision2Seq.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
).to("cuda:0")
```

`trust_remote_code=True` 会加载 checkpoint 中声明的 OpenVLA 自定义代码。对应源码在本地仓库的 `prismatic/extern/hf/processing_prismatic.py`、`configuration_prismatic.py` 和 `modeling_prismatic.py`。

装好 FlashAttention 后，可以在 `from_pretrained` 中加入：

```python
attn_implementation="flash_attention_2"
```

如果这项报错，先回到环境页检查 `flash_attn`，或者先去掉该参数验证基础加载。

## 本地 checkpoint 目录

本地 fine-tuned checkpoint 目录至少要包含下面几类内容：

| 内容 | 作用 |
| --- | --- |
| `config.json` | 记录 `model_type="openvla"`、backbone、action bins 和统计量字段。 |
| model weights | 通常是 `model.safetensors.index.json` 加多个 `.safetensors` shard。 |
| tokenizer / processor 文件 | 支持 `AutoProcessor.from_pretrained(...)`。 |
| `dataset_statistics.json` | 保存目标数据集动作统计量，供推理和部署反归一化。 |

`vla-scripts/finetune.py` 会在训练目录保存 processor、模型权重和 `dataset_statistics.json`。LoRA 路线还会先保存 adapter，再 merge 回完整模型，最后把可推理 checkpoint 写到 `run_dir` 或单独的 checkpoint 目录。

`vla-scripts/deploy.py` 对本地目录还有一个额外行为：如果 `openvla_path` 是本地目录，它会读取该目录下的 `dataset_statistics.json` 并写入 `vla.norm_stats`。所以本地部署前要先确认这个文件存在，并且里面的 key 与推理时的 `unnorm_key` 对得上。

## Prismatic checkpoint

`openvla/openvla-7b-prismatic` 面向 full fine-tuning 和 Prismatic 训练路径。README 中的 full fine-tuning 命令会把它作为 `--pretrained_checkpoint`，再通过 `vla-scripts/train.py` 继续训练。

这类 checkpoint 训练结束后，还要用 `vla-scripts/extern/convert_openvla_weights_to_hf.py` 转成 Hugging Face 格式，才能像上面的 AutoClass 示例一样加载。转换后的本地目录如果没有推到 Hugging Face Hub，README 示例会先手动注册：

```python
from transformers import AutoConfig, AutoImageProcessor, AutoModelForVision2Seq, AutoProcessor

from prismatic.extern.hf.configuration_prismatic import OpenVLAConfig
from prismatic.extern.hf.modeling_prismatic import OpenVLAForActionPrediction
from prismatic.extern.hf.processing_prismatic import PrismaticImageProcessor, PrismaticProcessor

AutoConfig.register("openvla", OpenVLAConfig)
AutoImageProcessor.register(OpenVLAConfig, PrismaticImageProcessor)
AutoProcessor.register(OpenVLAConfig, PrismaticProcessor)
AutoModelForVision2Seq.register(OpenVLAConfig, OpenVLAForActionPrediction)
```

## `unnorm_key` 和统计量

`predict_action()` 会先生成 action tokens，再把 token id 还原成归一化动作，最后用 `unnorm_key` 选择统计量做反归一化。`OpenVLAForActionPrediction._check_unnorm_key()` 的规则很直接：

- checkpoint 只有一套统计量时，可以省略 `unnorm_key`。
- checkpoint 保存多套统计量时，要传入其中一个 key。
- 传入的 key 不在统计量里时，会抛出断言错误并列出可选 key。

主模型 `openvla/openvla-7b` 的 `norm_stats` 包含多套 OXE 数据统计量，例如 `bridge_orig`。官方 LIBERO fine-tuned checkpoint 通常只对应一个 suite，例如本地 `openvla-7b-finetuned-libero-spatial` 的 `dataset_statistics.json` 只有 `libero_spatial` 这个 key。

## 导航

- 上一节：[下载代码与 checkpoint](02-download-and-cache.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[第一次 `predict_action`](04-first-predict-action.md)
