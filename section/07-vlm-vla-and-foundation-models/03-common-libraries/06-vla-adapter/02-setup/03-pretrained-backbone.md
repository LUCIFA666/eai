# 基础 VLM 与 Prismatic 配置

目标：准备 LoRA 微调命令里的 `--vlm_path` 和 `--config_file_path`，区分基础 VLM、Prismatic 配置和 LIBERO task checkpoint。

VLA-Adapter 使用 Prismatic-VLM architecture，LLM backbone 是 `Qwen2.5-0.5B`。官方 README 建议从 Hugging Face 下载 `Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b`，并放到 `pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b`。

## 下载基础 VLM

VLA-Adapter 官方仓库根目录已经有 `pretrained_models/`，其中包含两个子目录：

| 目录 | 作用 |
| --- | --- |
| `pretrained_models/configs/` | Prismatic 配置和自定义建模文件。 |
| `pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b/` | 基础 VLM 目标目录；仓库初始状态下通常只有 `README.md` 说明文件。 |

下面示例保留 `HF_ENDPOINT=https://hf-mirror.com`，用于无法直连 Hugging Face 时走镜像站；如果机器可以直连 Hugging Face，可以省略这一行。

把真实模型文件下载到 `pretrained_models/` 下的目标目录。仓库初始的 `pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b/` 通常只有 `README.md`，不需要先删除这个目录；下载后以 `config.json` 和权重文件是否出现为准。

```bash
cd /path/to/VLA-Adapter
export HF_ENDPOINT=https://hf-mirror.com

hf download Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b \
  --local-dir pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b
```

训练命令据此读取基础 VLM：

```bash
--vlm_path pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b
```

## 基础 VLM 体检

下载完成后，先确认目录下直接有 `config.json`：

```bash
ls pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b/config.json
find pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b -maxdepth 1 -type f | sort | head
```

预期至少能看到 `config.json`、tokenizer / processor 相关文件和模型权重文件。具体文件名以 Hugging Face 下载结果为准。

## Prismatic 配置目录

训练命令还会使用：

```bash
--config_file_path pretrained_models/configs
```

`pretrained_models/configs` 是 VLA-Adapter 使用的 Prismatic 配置和自定义建模文件目录，通常随仓库准备好。它和基础 VLM 权重目录不是同一个东西，也不能用来替代 `--vlm_path`。

可以做一次只读检查：

```bash
ls pretrained_models/configs/config.json
ls pretrained_models/configs/modeling_prismatic.py
ls pretrained_models/configs/configuration_prismatic.py
```

如果 `pretrained_models/configs` 缺失，训练命令中的 `--config_file_path pretrained_models/configs` 也会失效。后续训练页会同时使用 `--vlm_path` 和 `--config_file_path`，两者都需要准备好。

训练主线的 `--use_minivlm True` 分支还有一个隐含约束：模型 config 从硬编码路径 `pretrained_models/configs/config.json` 加载（`vla-scripts/finetune.py:788`），`--config_file_path` 在这条分支上只影响 processor 和 auto_map 注册。因此 `pretrained_models/configs/config.json` 必须存在，且与 `--config_file_path` 指向的目录保持一致。把 config 换到别处而只改 `--config_file_path`，模型仍会读硬编码路径下的那份 config，两边配置会不一致。

## 导航

- 上一节：[LIBERO 数据](02-libero-data.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[Checkpoint 准备](04-checkpoint-setup.md)
