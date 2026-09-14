# Checkpoint 准备

目标：下载官方 LIBERO checkpoint 到 `outputs/`，确认 `pretrained_checkpoint` 路径和 `use_pro_version` 参数能对上。

这一页默认在 VLA-Adapter 源码根目录下操作。教程主线使用 LIBERO Pro checkpoint，并让评测脚本从 `outputs/` 目录读取模型。

## Pro checkpoint 主线

VLA-Adapter 官方提供了四个 LIBERO Pro checkpoint。后续评测页默认使用这些 checkpoint，并保持 `--use_pro_version True`。

| Suite | Pro checkpoint repo | 本地目录 | `task_suite_name` |
| --- | --- | --- | --- |
| Spatial | `VLA-Adapter/LIBERO-Spatial-Pro` | `outputs/LIBERO-Spatial-Pro` | `libero_spatial` |
| Object | `VLA-Adapter/LIBERO-Object-Pro` | `outputs/LIBERO-Object-Pro` | `libero_object` |
| Goal | `VLA-Adapter/LIBERO-Goal-Pro` | `outputs/LIBERO-Goal-Pro` | `libero_goal` |
| Long | `VLA-Adapter/LIBERO-Long-Pro` | `outputs/LIBERO-long-Pro` | `libero_10` |

Long 的本地目录沿用官方评测命令里的 `outputs/LIBERO-long-Pro`。后续命令里大小写保持一致，可以减少路径不匹配带来的排查成本。

## 下载 Spatial-Pro

下面示例保留 `HF_ENDPOINT=https://hf-mirror.com`，用于无法直连 Hugging Face 时走镜像站；如果机器可以直连 Hugging Face，可以省略这一行。

把 checkpoint 下载到 `outputs/` 下：

```bash
cd /path/to/VLA-Adapter
mkdir -p outputs
export HF_ENDPOINT=https://hf-mirror.com

hf download VLA-Adapter/LIBERO-Spatial-Pro \
  --local-dir outputs/LIBERO-Spatial-Pro
```

后续评测命令用下面这个参数读取 checkpoint：

```bash
--pretrained_checkpoint outputs/LIBERO-Spatial-Pro
```

## 其他 Pro checkpoint

Object、Goal、Long 的下载方式相同，只需要替换 repo 和评测侧本地路径：

| Suite | 下载 repo | 评测侧本地路径 |
| --- | --- | --- |
| Object | `VLA-Adapter/LIBERO-Object-Pro` | `outputs/LIBERO-Object-Pro` |
| Goal | `VLA-Adapter/LIBERO-Goal-Pro` | `outputs/LIBERO-Goal-Pro` |
| Long | `VLA-Adapter/LIBERO-Long-Pro` | `outputs/LIBERO-long-Pro` |

例如 Object-Pro 可以这样下载：

```bash
hf download VLA-Adapter/LIBERO-Object-Pro \
  --local-dir outputs/LIBERO-Object-Pro
```

## 常规版 checkpoint 对照

官方也提供仓库名不带 `-Pro` 后缀的 VLA-Adapter checkpoint，本页称为“常规版 checkpoint”。第一次复现建议先沿着 Pro 主线走；如果后续评测常规版 checkpoint，`--pretrained_checkpoint` 和 `--use_pro_version` 需要一起调整。

| Suite | 常规版 checkpoint repo | 本地目录 | `use_pro_version` |
| --- | --- | --- | --- |
| Spatial | `VLA-Adapter/LIBERO-Spatial` | `outputs/LIBERO-Spatial` | `False` |
| Object | `VLA-Adapter/LIBERO-Object` | `outputs/LIBERO-Object` | `False` |
| Goal | `VLA-Adapter/LIBERO-Goal` | `outputs/LIBERO-Goal` | `False` |
| Long | `VLA-Adapter/LIBERO-Long` | `outputs/LIBERO-Long` | `False` |

以 Spatial 常规版为例，下载命令可以写成：

```bash
hf download VLA-Adapter/LIBERO-Spatial \
  --local-dir outputs/LIBERO-Spatial
```

对应评测参数应改成：

```bash
--pretrained_checkpoint outputs/LIBERO-Spatial
--use_pro_version False
```

## Checkpoint 体检

下载完成后，可以做一次只读检查：

```bash
find outputs/LIBERO-Spatial-Pro -maxdepth 1 -type f | sort
```

参考输出如下：

```text
outputs/LIBERO-Spatial-Pro/action_head--checkpoint.pt
outputs/LIBERO-Spatial-Pro/added_tokens.json
outputs/LIBERO-Spatial-Pro/config.json
outputs/LIBERO-Spatial-Pro/configuration_prismatic.py
outputs/LIBERO-Spatial-Pro/dataset_statistics.json
outputs/LIBERO-Spatial-Pro/generation_config.json
outputs/LIBERO-Spatial-Pro/.gitattributes
outputs/LIBERO-Spatial-Pro/Inference--Spatial_Pro--99.6.log
outputs/LIBERO-Spatial-Pro/merges.txt
outputs/LIBERO-Spatial-Pro/modeling_prismatic.py
outputs/LIBERO-Spatial-Pro/model.safetensors
outputs/LIBERO-Spatial-Pro/preprocessor_config.json
outputs/LIBERO-Spatial-Pro/processing_prismatic.py
outputs/LIBERO-Spatial-Pro/processor_config.json
outputs/LIBERO-Spatial-Pro/proprio_projector--checkpoint.pt
outputs/LIBERO-Spatial-Pro/README.md
outputs/LIBERO-Spatial-Pro/special_tokens_map.json
outputs/LIBERO-Spatial-Pro/tokenizer_config.json
outputs/LIBERO-Spatial-Pro/tokenizer.json
outputs/LIBERO-Spatial-Pro/vocab.json
```

预期能看到模型配置、权重文件、`action_head--checkpoint.pt`、`proprio_projector--checkpoint.pt`、`model.safetensors`、`tokenizer.json` 等文件。具体文件名以实际下载结果为准；如果目录为空，或者只看到很小的说明文件，后续评测通常无法正常加载模型。

## 直接使用 Hugging Face repo id

评测脚本也支持把 Hugging Face repo id 直接传给 `--pretrained_checkpoint`，例如：

```bash
--pretrained_checkpoint VLA-Adapter/LIBERO-Spatial-Pro
```

这种方式依赖运行时网络和 Hugging Face 缓存。教程主线使用本地 `outputs/...` 路径，主要是为了让下载位置、评测命令和结果记录更容易复查。

## 导航

- 上一节：[基础 VLM 与 Prismatic 配置](03-pretrained-backbone.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[官方 Checkpoint 链路检查](05-checkpoint-smoke-test.md)
