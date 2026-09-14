# `finetune.py` 训练流程

目标：沿着源码读懂 OpenVLA LoRA 微调从模型加载到训练 step 的主要过程。

`vla-scripts/finetune.py` 把 LoRA 微调压在一个脚本里：配置、模型加载、LoRA 包装、RLDS 数据、collator、optimizer、DDP 和训练循环都在这里。读这个文件时，可以先抓住四段：配置、模型、数据、训练 step。

## 配置入口

脚本用 `FinetuneConfig` 收集命令行参数。下面这段默认值决定了 LoRA 微调的基础形状。

```python
@dataclass
class FinetuneConfig:
    vla_path: str = "openvla/openvla-7b"
    data_root_dir: Path = Path("datasets/open-x-embodiment")
    dataset_name: str = "droid_wipe"
    run_root_dir: Path = Path("runs")
    batch_size: int = 16
    max_steps: int = 200_000
    save_steps: int = 5000
    learning_rate: float = 5e-4
    use_lora: bool = True
    lora_rank: int = 32
    use_quantization: bool = False
```

这里能看到两个重要默认值：LoRA 默认开启，`vla_path` 默认指向 Hugging Face 主 checkpoint。数据集默认值是脚本示例，实际训练时通常会通过命令行改成目标数据集。

## Hugging Face 加载路径

LoRA 微调沿用 Hugging Face AutoClass 路径。脚本先注册 OpenVLA 的 config、processor 和 model 类，再调用 `from_pretrained()`。

```python
AutoConfig.register("openvla", OpenVLAConfig)
AutoImageProcessor.register(OpenVLAConfig, PrismaticImageProcessor)
AutoProcessor.register(OpenVLAConfig, PrismaticProcessor)
AutoModelForVision2Seq.register(OpenVLAConfig, OpenVLAForActionPrediction)

processor = AutoProcessor.from_pretrained(cfg.vla_path, trust_remote_code=True)
vla = AutoModelForVision2Seq.from_pretrained(
    cfg.vla_path,
    torch_dtype=torch.bfloat16,
    quantization_config=quantization_config,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
)
```

这段代码说明 LoRA 路径从 HF checkpoint 出发，和 setup 里的最小 `predict_action` 属于同一类加载方式。模型加载失败时，先检查 `vla_path`、缓存、本地 checkpoint 文件和 `trust_remote_code`。

## LoRA 包装

模型加载后，脚本根据 `use_lora` 把 PEFT LoRA 接到模型上。

```python
if cfg.use_lora:
    lora_config = LoraConfig(
        r=cfg.lora_rank,
        lora_alpha=min(cfg.lora_rank, 16),
        lora_dropout=cfg.lora_dropout,
        target_modules="all-linear",
        init_lora_weights="gaussian",
    )
    vla = get_peft_model(vla, lora_config)
    vla.print_trainable_parameters()
```

`target_modules="all-linear"` 表示 LoRA 会作用到线性层。`lora_alpha` 被限制在 `min(rank, 16)`，所以改 `lora_rank` 时，训练参数规模会变，LoRA scaling 也会跟着这条规则变化。

## 数据进入训练 batch

数据侧由 `ActionTokenizer`、`RLDSBatchTransform` 和 `RLDSDataset` 接起来。

```python
action_tokenizer = ActionTokenizer(processor.tokenizer)

batch_transform = RLDSBatchTransform(
    action_tokenizer,
    processor.tokenizer,
    image_transform=processor.image_processor.apply_transform,
    prompt_builder_fn=PurePromptBuilder if "v01" not in cfg.vla_path else VicunaV15ChatPromptBuilder,
)
vla_dataset = RLDSDataset(
    cfg.data_root_dir,
    cfg.dataset_name,
    batch_transform,
    resize_resolution=tuple(vla.module.config.image_sizes),
    shuffle_buffer_size=cfg.shuffle_buffer_size,
    image_aug=cfg.image_aug,
)
```

这一段把前面数据章节的内容接到训练脚本里：`dataset_name` 选中数据，`RLDSBatchTransform` 把图像、语言和动作处理成模型输入，`ActionTokenizer` 把连续动作转成 action token 监督信号。`image_aug` 也在这里传入数据集。

## Collator 和 DDP

OpenVLA 的训练 batch 需要对文本序列做 padding。脚本用 `PaddedCollatorForActionPrediction` 生成 DataLoader，再把模型包进 DDP。

```python
vla = DDP(vla, device_ids=[device_id], find_unused_parameters=True, gradient_as_bucket_view=True)

collator = PaddedCollatorForActionPrediction(
    processor.tokenizer.model_max_length,
    processor.tokenizer.pad_token_id,
    padding_side="right",
)
dataloader = DataLoader(
    vla_dataset,
    batch_size=cfg.batch_size,
    collate_fn=collator,
    num_workers=0,
)
```

`num_workers=0` 是 RLDS 路径里的一个实现选择，源码注释说明 TFDS 自己管理并行加载。排查数据加载卡住时，可以先看 RLDS / TFDS 的日志，而不是先改 PyTorch DataLoader worker。

## 单个训练 step

训练循环的核心仍然是 causal LM loss：输入 `input_ids`、`attention_mask`、`pixel_values` 和 `labels`，模型返回 `output.loss`。

```python
with torch.autocast("cuda", dtype=torch.bfloat16):
    output: CausalLMOutputWithPast = vla(
        input_ids=batch["input_ids"].to(device_id),
        attention_mask=batch["attention_mask"].to(device_id),
        pixel_values=batch["pixel_values"].to(torch.bfloat16).to(device_id),
        labels=batch["labels"],
    )
    loss = output.loss

normalized_loss = loss / cfg.grad_accumulation_steps
normalized_loss.backward()
```

`labels` 里包含 action token 监督信号。梯度累积通过 `normalized_loss` 处理，optimizer step 会等到累计到 `grad_accumulation_steps` 后执行。

## 本页小结

- `finetune.py` 的 LoRA 路径从 HF AutoClass 加载 `openvla/openvla-7b`。
- PEFT LoRA 默认作用到 `all-linear`，默认 rank 是 `32`。
- `RLDSBatchTransform` 和 `RLDSDataset` 把图像、语言、动作和统计量接到训练循环。
- 训练 loss 来自 causal LM 输出，action token 监督信号放在 `labels` 中。

## 导航

- 上一节：[LoRA 启动命令](01-lora-command.md)
- 返回上级：[LoRA 微调](../05-finetuning.md)
- 下一节：[训练日志与 checkpoint](03-logs-and-checkpoints.md)
