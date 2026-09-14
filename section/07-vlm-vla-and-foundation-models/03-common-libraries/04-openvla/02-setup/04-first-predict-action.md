# 第一次 `predict_action`

目标：用一张图像和一条语言指令调用 OpenVLA，确认 `predict_action` 能返回 7 维动作。

这一页做的是 smoke test。它验证 processor、prompt、模型加载、action token 生成和反归一化可以连起来；任务完成情况还要通过 LIBERO、Bridge 或真实机器人 rollout 判断。

## 最小脚本

下面的脚本使用 `openvla/openvla-7b` 和全零占位图像。占位图像没有真实场景含义，只用于确认调用链路。替换成真实相机图像后，动作数值才有环境含义。

```python
import numpy as np
import torch
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor

model_id = "openvla/openvla-7b"
device = "cuda:0"

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
vla = AutoModelForVision2Seq.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
).to(device)

image = Image.fromarray(np.zeros((256, 256, 3), dtype=np.uint8))
prompt = "In: What action should the robot take to pick up the red block?\nOut:"

inputs = processor(prompt, image).to(device, dtype=torch.bfloat16)
action = vla.predict_action(**inputs, unnorm_key="bridge_orig", do_sample=False)

print(action)
print(action.shape)
```

装好 FlashAttention 后，可以在 `from_pretrained` 里加入 `attn_implementation="flash_attention_2"`。如果这一步报错，先回到环境页检查 `flash_attn`，或者先用普通 attention 跑通最小链路。

## 这段脚本验证什么

| 代码对象 | 验证内容 |
| --- | --- |
| `AutoProcessor.from_pretrained(...)` | checkpoint 的 processor、tokenizer 和图像预处理能加载。 |
| `AutoModelForVision2Seq.from_pretrained(...)` | OpenVLA 的 HF 模型类、权重和 config 能加载。 |
| `processor(prompt, image)` | prompt 和 PIL 图像能组成 `input_ids`、`attention_mask`、`pixel_values`。 |
| `predict_action(...)` | 模型能生成 action tokens，并按 `unnorm_key` 还原成连续动作。 |
| `action.shape` | OpenVLA 主线默认返回 7D end-effector action。 |

这段脚本没有接入环境 step、gripper 后处理、碰撞检查或真实机器人控制，所以输出 shape 正常只说明接口通了。动作表现要等评测章节进入闭环 rollout 后再判断。

## `unnorm_key` 怎么选

`openvla/openvla-7b` 带有多套 OXE 数据统计量，README quickstart 使用 `bridge_orig`。如果改用 LIBERO fine-tuned checkpoint，`unnorm_key` 要换成对应 suite，例如 `libero_spatial`、`libero_object`、`libero_goal` 或 `libero_10`。

`unnorm_key` 选错时有两种表现：

- key 缺失于 checkpoint 的统计量，`predict_action` 会直接报错，并列出可用 key。
- key 存在但数据域不匹配，模型仍会返回 shape 正常的 action，但动作尺度会偏掉。

第一种适合用来检查当前 checkpoint 支持哪些统计量；第二种更危险，因为 Python 层通常没有异常，后面评测时可能表现成动作幅度异常。

## 原始输出

下面是本地 smoke test 的一次原始终端输出。这个脚本同样使用全零占位图像，checkpoint 换成已下载的 `openvla/openvla-7b-finetuned-libero-spatial`，并额外打印加载时间、显存和 5 次单步推理延迟。

```text
=== loading processor ===
processor load (s): 2.26
=== loading model ===
Loading checkpoint shards: 100%|██████████| 4/4 [00:00<00:00,  7.16it/s]
model load (s): 4.3
GPU mem allocated (GB): 15.13
GPU mem reserved  (GB): 15.17

=== unnorm_key mismatch demo (wrong key on purpose) ===
AssertionError : The `unnorm_key` you chose is not in the set of available dataset statistics, please choose from: dict_keys(['libero_spatial'])

=== correct inference (unnorm_key=libero_spatial), 5 runs ===
run 0: latency 0.566s
run 1: latency 0.195s
run 2: latency 0.195s
run 3: latency 0.197s
run 4: latency 0.194s

action: [ 0.2412  0.3483 -0.0027  0.     -0.0225 -0.1202  0.9961]
shape: (7,)
first-call latency (s): 0.566
steady-state latency (s, mean of runs 1-4): 0.195
implied control freq (Hz, steady): 5.12
```

占位图像下的动作数值没有任务解释价值。这里重点看三件事：模型能加载，`predict_action` 调用完成，返回 shape 为 `(7,)`。`unnorm_key` 报错也说明 checkpoint 里的统计量 key 能被检查出来。

## 常见现象

| 现象 | 先看哪里 |
| --- | --- |
| `flash_attn` 导入或加载报错 | 回到 [准备环境](01-environment.md)，或先去掉 `attn_implementation` 参数。 |
| `trust_remote_code` 相关报错 | 检查 checkpoint 是否完整，或看 [Checkpoint 与模型加载](03-checkpoints-and-model-loading.md) 的本地目录说明。 |
| `unnorm_key` assertion | 检查 checkpoint 里的 `norm_stats` / `dataset_statistics.json` 支持哪些 key。 |
| action shape 异常 | 先看 `unnorm_key` 对应统计量的 action 维度，再看 `predict_action()`。 |

## 导航

- 上一节：[Checkpoint 与模型加载](03-checkpoints-and-model-loading.md)
- 返回上级：[安装与第一次跑通](../02-setup.md)
- 下一节：[模型结构与动作推理](../03-model-and-action-inference.md)
