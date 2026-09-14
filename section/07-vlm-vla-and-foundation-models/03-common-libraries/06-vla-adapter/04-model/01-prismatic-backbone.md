# Prismatic Backbone

目标：理解 VLA-Adapter 中 tiny Prismatic-VLM backbone 的位置，以及训练/评测命令里的路径参数为什么重要。

LIBERO-Pro 主线使用 tiny Prismatic-VLM。训练阶段先从两个路径拿到基础模型和配置：

```bash
--vlm_path pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b
--config_file_path pretrained_models/configs
```

`vlm_path` 指向基础 VLM 权重，`config_file_path` 指向 Prismatic / Hugging Face 相关配置和 processor。训练时，`vla-scripts/finetune.py` 读取这两个路径，创建基础模型，再注入 LoRA、action head 和 proprio projector。

评测和部署阶段换成 `pretrained_checkpoint`。它指向可推理的 checkpoint 目录或 Hugging Face repo，`openvla_utils.py` 会从这里加载模型、processor、action head、projector 和 statistics。把 `vlm_path` 当成 `pretrained_checkpoint` 用，通常会缺少评测所需的组件。

## `use_minivlm` 分支

主线训练和评测保持：

```bash
--use_minivlm True
```

这个 flag 有两层影响。训练时，它让 `finetune.py` 走 tiny Prismatic / Qwen2.5 相关加载路径；推理时，它还会影响 prompt 模板。`get_vla_action()` 中的分支可以直接看到这一点：

```python
if not use_minivlm:
    prompt = f"In: What action should the robot take to {task_label.lower()}?\nOut:"
else:
    prompt = (
        "<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. "
        "You are a helpful assistant.<|im_end|>\n"
        f"<|im_start|>user\nWhat action should the robot take to {task_label.lower()}?"
        "<|im_end|>\n<|im_start|>assistant\n"
    )
```

因此 `use_minivlm` 需要和基础模型、processor、tokenizer 和 checkpoint 配置保持一致。若基础模型目录只存在空文件、缺少 `config.json` 或权重文件，训练会在模型加载阶段失败；若 processor/config 不完整，错误可能出现在图像和 prompt 处理阶段。

## 评测时的 processor

`openvla_utils.get_processor()` 使用 checkpoint 路径加载 processor。processor 决定图像预处理和 prompt tokenization，也会受到 `num_images_in_input` 影响。checkpoint 目录如果缺少 processor / tokenizer 相关文件，模型权重可能能找到，但 `get_vla_action()` 仍会在输入处理阶段失败。

这也是本地训练产物需要保存 processor 文件的原因。step checkpoint 目录能被 `run_libero_eval.py` 直接使用，通常意味着它不仅有模型权重，还能让 `AutoProcessor.from_pretrained()` 正常返回 processor。

## 体检入口

基础 VLM 下载后，至少确认目录中存在配置和权重文件：

```bash
find pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b -maxdepth 1 -type f | sort | head
```

如果使用本地 checkpoint 做 eval，也要确认 checkpoint 目录能提供 processor / tokenizer 文件。基础 VLM、processor 和 checkpoint 组件不属于同一个检查点，但 eval 会同时依赖它们。

## 导航

- 上一节：[模型组件](../04-model.md)
- 返回上级：[模型组件](../04-model.md)
- 下一节：[Action Head 与 Action Chunk](02-action-head-and-action-chunk.md)
