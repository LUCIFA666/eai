# 准备 Benchmark 与 Judge

官方评测准备包括两部分：WorldModelBench 测试集与 `evaluation.py`，以及运行 VILA-EWM Judge 的 Python 环境。

以下组合已经完成 checkpoint 加载、单视频冒烟和 350 条正式评测，可以参考：

| 对象 | 固定版本 |
| --- | --- |
| WorldModelBench | `00b7aa17a05f9fd1ab5c8f66bcf476d04c9c33bf` |
| VILA | `c8f603b49f5dcfca8c2ee18d7979897a83aa5fa6` |
| VILA-EWM | `827be9ef964d9dff54d17551965c9d41224e3675` |
| Python / Torch | Python 3.10.14，Torch 2.3.0，CUDA 12.1 wheel |

更换 VILA、Torch 或 checkpoint 后，新的组合需要重新通过模型加载和单视频冒烟。

## 建立工作目录

```bash
mkdir -p worldmodelbench-repro
cd worldmodelbench-repro
export WMB_ROOT="$PWD"

mkdir -p \
  "$WMB_ROOT/src" \
  "$WMB_ROOT/envs" \
  "$WMB_ROOT/models" \
  "$WMB_ROOT/cache/huggingface" \
  "$WMB_ROOT/cache/pip" \
  "$WMB_ROOT/cache/uv" \
  "$WMB_ROOT/videos" \
  "$WMB_ROOT/results"
```

后续步骤使用的参考目录结构如下。`cosmos/`、Cosmos3-Nano 环境和对应产物只在执行生成示例时出现，`<model-name>` 表示实际的 `WMB_MODEL_NAME`。

```text
worldmodelbench-repro/
├── src/
│   ├── WorldModelBench/
│   ├── VILA/
│   └── cosmos/                         # 可选的 Cosmos 参考源码
├── envs/
│   ├── judge-vila-c8f603b4/
│   └── cosmos3-nano-22b0f43e/         # 可选的生成环境
├── models/
│   ├── vila-ewm-qwen2-1.5b/
│   └── Cosmos3-Nano/                   # 可选的生成模型
├── cache/
│   ├── huggingface/
│   ├── pip/
│   └── uv/
├── videos/
│   ├── judge-static-smoke/
│   ├── <model-name>/
│   └── cosmos3-nano-411f42a8/
└── results/
    ├── judge-static-smoke.json
    ├── cosmos3-nano-checksums.json
    ├── cosmos3-generation.log
    ├── <model-name>/
    │   ├── evaluation.log
    │   └── worldmodelbench_results.json
    └── cosmos3-nano-411f42a8/
        ├── evaluation.log
        └── worldmodelbench_results.json
```

新的 shell 不会保留 `WMB_ROOT`。重新进入工作目录后恢复该变量：

```bash
cd worldmodelbench-repro
export WMB_ROOT="$PWD"
```

`WMB_ROOT` 应显示绝对路径。`df -BG "$WMB_ROOT"` 可以检查工作目录所在文件系统的可用空间。

## 检查基础工具

这组命令只检查后续步骤调用的程序是否可用，不会安装软件或修改环境。前四条命令分别确认源码管理、环境管理和视频读写工具；检测到 `nvidia-smi` 时，最后一条命令还会列出 GPU 型号与显存。

```bash
set -e
git --version
conda --version
ffmpeg -version | head -n 1
ffprobe -version | head -n 1

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=index,name,memory.total,memory.free \
    --format=csv,noheader,nounits
fi
```

Git、Conda、FFmpeg 和 FFprobe 必须正常退出。当前参考栈还要求 NVIDIA 驱动能够被 `nvidia-smi` 识别；GPU 不可见时，后续的 Torch CUDA 检查会失败。

## 检出固定源码

`WMB_BENCHMARK` 和 `WMB_VILA` 分别指向评测仓库与 Judge 运行时源码。下面的命令依次克隆两个仓库、以 detached HEAD 检出固定 commit，再打印实际 commit 并确认工作树没有改动。detached HEAD 可以避免当前分支随后移动到其他 revision。

```bash
export WMB_BENCHMARK_REV=00b7aa17a05f9fd1ab5c8f66bcf476d04c9c33bf
export WMB_VILA_REV=c8f603b49f5dcfca8c2ee18d7979897a83aa5fa6
export WMB_BENCHMARK="$WMB_ROOT/src/WorldModelBench"
export WMB_VILA="$WMB_ROOT/src/VILA"

git clone https://github.com/WorldModelBench-Team/WorldModelBench.git \
  "$WMB_BENCHMARK"
git -C "$WMB_BENCHMARK" checkout --detach "$WMB_BENCHMARK_REV"

git clone --filter=blob:none --no-recurse-submodules \
  https://github.com/NVlabs/VILA.git "$WMB_VILA"
git -C "$WMB_VILA" checkout --detach "$WMB_VILA_REV"

git -C "$WMB_BENCHMARK" rev-parse HEAD
git -C "$WMB_VILA" rev-parse HEAD
test -z "$(git -C "$WMB_BENCHMARK" status --short)"
test -z "$(git -C "$WMB_VILA" status --short)"
```

两个 revision 输出必须分别等于表中的完整 commit，两个工作树必须为空。目录已经存在时，不要覆盖或混用旧源码；先检查其 remote、revision 和工作树状态。

## 验证测试集

测试集检查覆盖五类信息：

1. 记录数量与必需字段，确认 350 条记录都能提供领域、生成条件和首帧路径；
2. `first_frame` stem，确认 350 个输出文件名不会发生冲突；
3. 首帧文件，确认每条 I2V 输入都能在数据集目录中找到；
4. 领域分布，确认测试集仍由 7 个领域、每个领域 50 条记录以及 56 个子领域组成；
5. JSON 的 SHA256，确认内容与固定 revision 下经过验证的数据文件完全一致。

这些检查同时使用 `WMB_DATASET` 指定文件位置，并用 `WMB_DATASET_SHA` 保存预期摘要：

```bash
export WMB_DATASET="$WMB_BENCHMARK/worldmodelbench.json"
export WMB_DATASET_SHA=56cf38e7fc8cb3a485d71de890a38d2857752cc168addda8900b89f9809a842b

python3 - <<'PY'
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path

dataset = Path(os.environ["WMB_DATASET"])
records = json.loads(dataset.read_text(encoding="utf-8"))
required = {
    "domain",
    "subdomain",
    "text_first_frame",
    "text_instruction",
    "first_frame",
}

assert len(records) == 350, len(records)
for index, record in enumerate(records):
    missing = required - record.keys()
    assert not missing, (index, sorted(missing))

stems = [Path(record["first_frame"]).stem for record in records]
assert len(stems) == len(set(stems)) == 350
missing_images = [
    record["first_frame"]
    for record in records
    if not (dataset.parent / record["first_frame"]).is_file()
]
assert not missing_images, missing_images[:5]

domains = Counter(record["domain"] for record in records)
subdomains = {(record["domain"], record["subdomain"]) for record in records}
assert len(domains) == 7, domains
assert set(domains.values()) == {50}, domains
assert len(subdomains) == 56, len(subdomains)

digest = sha256(dataset.read_bytes()).hexdigest()
assert digest == os.environ["WMB_DATASET_SHA"], digest
print({
    "records": len(records),
    "unique_stems": len(set(stems)),
    "domains": len(domains),
    "subdomains": len(subdomains),
    "dataset_sha256": digest,
})
PY
```

成功输出应包含 350 条记录、350 个唯一 stem、7 个领域和 56 个子领域。断言失败表示数据文件、首帧目录或 revision 与固定测试集不一致。

## 创建 Judge 环境

VILA 的安装脚本包含开放式传递依赖。参考组合先固定 Torch，再执行脚本，最后固定已验证的 NumPy、OpenCV 和辅助包版本。

安装过程分为三层：Conda 在 `WMB_JUDGE_ENV` 创建独立的 Python 3.10 环境；PyTorch CUDA 12.1 wheel 提供 GPU 运行时；VILA 安装脚本及最后一组固定版本提供 Judge 所需的模型和视频依赖。`PIP_CACHE_DIR` 只改变下载缓存位置，不改变环境中的安装路径。

```bash
export WMB_JUDGE_ENV="$WMB_ROOT/envs/judge-vila-c8f603b4"
export PIP_CACHE_DIR="$WMB_ROOT/cache/pip"

eval "$(conda shell.bash hook)"
conda create --prefix "$WMB_JUDGE_ENV" python=3.10.14 -y
conda activate "$WMB_JUDGE_ENV"

python -m pip install \
  --timeout 120 --retries 10 \
  --index-url https://download.pytorch.org/whl/cu121 \
  torch==2.3.0 torchvision==0.18.0

(
  cd "$WMB_VILA"
  bash environment_setup.sh
)

python -m pip install \
  numpy==1.26.4 \
  opencv-python==4.8.0.76 \
  mmengine==0.10.7 \
  rich==15.0.0 \
  huggingface_hub==0.36.2
```

安装命令成功退出仍不足以说明这些依赖可以共同导入。下面的检查先导入 VILA 及其关键依赖，再核对固定版本；最后两个 CUDA 断言分别确认 Torch 能访问 GPU，并且该 GPU 支持参考组合使用的 BF16。

```bash
python - <<'PY'
import cv2
import llava
import mmengine
import numpy
import sys
import torch
import torchvision
import transformers

assert torch.__version__.startswith("2.3.0"), torch.__version__
assert torchvision.__version__.startswith("0.18.0"), torchvision.__version__
assert transformers.__version__ == "4.46.0", transformers.__version__
assert numpy.__version__ == "1.26.4", numpy.__version__
assert cv2.__version__ == "4.8.0", cv2.__version__
assert mmengine.__version__ == "0.10.7", mmengine.__version__
assert torch.cuda.is_available()
assert torch.cuda.is_bf16_supported()
print({
    "python": sys.version.split()[0],
    "torch": torch.__version__,
    "torch_cuda": torch.version.cuda,
    "judge_environment": "verified",
})
PY
```

`judge_environment=verified` 表示 Python 模块和 CUDA 可以共同加载。

## 下载并加载 VILA-EWM

`HF_HOME` 保存 Hugging Face 缓存，`WMB_JUDGE_REV` 固定模型仓库 revision，`WMB_JUDGE` 是评测命令实际读取的 checkpoint 目录。`hf download` 会把该 revision 的文件下载到这个目录：

```bash
export HF_HOME="$WMB_ROOT/cache/huggingface"
export WMB_JUDGE_REV=827be9ef964d9dff54d17551965c9d41224e3675
export WMB_JUDGE="$WMB_ROOT/models/vila-ewm-qwen2-1.5b"

hf download Efficient-Large-Model/vila-ewm-qwen2-1.5b \
  --revision "$WMB_JUDGE_REV" \
  --local-dir "$WMB_JUDGE"
```

下载完成后分两层验证 checkpoint。第一层检查目录结构：固定 checkpoint 应包含 16 个文件，总大小为 3,967,218,367 bytes，并且语言模型、视觉投影器和视觉编码器三个主要权重都存在。

```bash
python - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["WMB_JUDGE"])
files = [
    path for path in root.rglob("*")
    if path.is_file() and ".cache" not in path.parts
]
required = [
    root / "llm/model.safetensors",
    root / "mm_projector/model.safetensors",
    root / "vision_tower/model.safetensors",
]
assert all(path.is_file() for path in required)
assert len(files) == 16, len(files)
assert sum(path.stat().st_size for path in files) == 3_967_218_367
print({"files": len(files), "bytes": sum(path.stat().st_size for path in files)})
PY
```

下载失败时重新执行同一个 `hf download` 命令，已完成文件会被复用。

第二层实际调用 VILA 的加载入口。这个过程会读取模型配置和权重，但不加载视频，也不发送评测问题：

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
python - <<'PY'
import os
import llava

model = llava.load(os.environ["WMB_JUDGE"])
print({"model_loaded": True, "model_type": type(model).__name__})
del model
PY
```

输出包含 `model_loaded: True`，说明 checkpoint 和当前 VILA 环境能够共同加载。

## 运行单视频 Judge 冒烟

静态视频不测试视频生成能力，只验证视频解码、8 次问答和结果保存。

冒烟命令依次完成四个动作：

1. 从测试集第一条记录取得首帧路径及其 stem；
2. 用 FFmpeg 将该图像编码为 16 帧静态 MP4；
3. 将只包含这个 MP4 的目录传给 `evaluation.py`；
4. 把 Judge 回答保存到 `WMB_SMOKE_RESULT.json`。

静态视频文件沿用首帧 stem，因此评测脚本能把它与第一条测试记录关联：

```bash
export WMB_SMOKE_DIR="$WMB_ROOT/videos/judge-static-smoke"
export WMB_SMOKE_RESULT="$WMB_ROOT/results/judge-static-smoke"
mkdir -p "$WMB_SMOKE_DIR"
test ! -e "$WMB_SMOKE_RESULT.json"

export WMB_SMOKE_IMAGE="$(
  python - <<'PY'
import json
import os
from pathlib import Path

dataset = Path(os.environ["WMB_DATASET"])
record = json.loads(dataset.read_text(encoding="utf-8"))[0]
print(dataset.parent / record["first_frame"])
PY
)"
export WMB_SMOKE_STEM="$(basename "${WMB_SMOKE_IMAGE%.*}")"

ffmpeg -y -loop 1 -i "$WMB_SMOKE_IMAGE" \
  -frames:v 16 -r 8 -c:v libx264 -pix_fmt yuv420p \
  "$WMB_SMOKE_DIR/$WMB_SMOKE_STEM.mp4"

(
  cd "$WMB_BENCHMARK"
  "$WMB_JUDGE_ENV/bin/python" evaluation.py \
    --model_name judge-static-smoke \
    --video_dir "$WMB_SMOKE_DIR" \
    --judge "$WMB_JUDGE" \
    --save_name "$WMB_SMOKE_RESULT"
)
```

官方脚本会扫描全部测试记录，并提示其余 349 个视频缺失。这是单视频冒烟的预期行为。最终 JSON 只应包含目标 stem；下面的检查还确认该 stem 下有 1 个 Instruction、5 个 Physics 和 2 个 Common Sense 回答，合计 8 个：

```bash
export WMB_RESULT="$WMB_SMOKE_RESULT.json"
"$WMB_JUDGE_ENV/bin/python" - <<'PY'
import json
import os
from pathlib import Path

result = json.loads(Path(os.environ["WMB_RESULT"]).read_text(encoding="utf-8"))
assert len(result["preds"]) == 1
item = next(iter(result["preds"].values()))
assert len(item["instruction"]) == 1
assert len(item["physical_laws"]) == 5
assert len(item["common_sense"]) == 2
print({"samples": 1, "answers": 8, "judge_smoke": "passed"})
PY
```

冒烟分数会受静态画面和 Judge 随机采样影响，不作为模型质量结果。结果文件缺失时，检查评测进程退出状态、视频路径和 checkpoint 加载日志；回答数量不足时，不应进入正式评测。

## 导航

- 返回上级：[评测复现](../06-reproduction.md)
- 下一节：[准备评测视频](02-prepare-evaluation-videos.md)
