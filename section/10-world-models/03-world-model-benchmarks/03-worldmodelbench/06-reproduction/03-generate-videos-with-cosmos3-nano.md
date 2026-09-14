# 使用 Cosmos3-Nano 生成视频

Cosmos3-Nano 提供一套完整的 I2V 输入生成示例。它是可替换的被测模型，不是 WorldModelBench 的协议要求；已有其他模型的 350 个 MP4 时，无需安装这套生成环境。

参考运行固定以下版本：

| 对象 | Revision |
| --- | --- |
| Cosmos | `22b0f43eb2923fa63df320a94807fa9b9782e4e5` |
| Cosmos3-Nano | `411f42a8fdfb8c5b2583cb8786e0938f49796eaa` |
| Diffusers | `623213d29f8323f4003ffc7d0eadf260ab5aec9d` |

## 创建生成环境

环境创建命令先定义数据集、源码、checkpoint、视频输出和缓存路径，再固定 Cosmos 源码 revision。随后，`uv venv` 在 `WMB_COSMOS_ENV` 创建 Python 3.13 环境，`uv pip install` 将固定 Diffusers revision 及其推理依赖安装到该环境。最后创建的视频目录和结果目录分别保存 MP4 与运行记录。

```bash
cd worldmodelbench-repro
export WMB_ROOT="$PWD"
export WMB_BENCHMARK="$WMB_ROOT/src/WorldModelBench"
export WMB_DATASET="$WMB_BENCHMARK/worldmodelbench.json"

export WMB_COSMOS_REV=22b0f43eb2923fa63df320a94807fa9b9782e4e5
export WMB_COSMOS_MODEL_REV=411f42a8fdfb8c5b2583cb8786e0938f49796eaa
export WMB_DIFFUSERS_REV=623213d29f8323f4003ffc7d0eadf260ab5aec9d
export WMB_COSMOS_ENV="$WMB_ROOT/envs/cosmos3-nano-22b0f43e"
export WMB_COSMOS_MODEL="$WMB_ROOT/models/Cosmos3-Nano"
export WMB_VIDEO_ROOT="$WMB_ROOT/videos/cosmos3-nano-411f42a8"
export HF_HOME="$WMB_ROOT/cache/huggingface"
export UV_CACHE_DIR="$WMB_ROOT/cache/uv"

uv --version
df -BG "$WMB_ROOT"

git clone --filter=blob:none --no-checkout \
  https://github.com/NVIDIA/cosmos.git "$WMB_ROOT/src/cosmos"
git -C "$WMB_ROOT/src/cosmos" checkout --detach "$WMB_COSMOS_REV"
git -C "$WMB_ROOT/src/cosmos" rev-parse HEAD

uv venv --python 3.13 --seed "$WMB_COSMOS_ENV"
UV_LINK_MODE=copy uv pip install \
  --python "$WMB_COSMOS_ENV/bin/python" \
  --torch-backend=cu130 \
  "diffusers @ git+https://github.com/huggingface/diffusers.git@$WMB_DIFFUSERS_REV" \
  accelerate av cosmos-guardrail==0.3.1 \
  huggingface_hub imageio imageio-ffmpeg \
  torch torchvision transformers

mkdir -p "$WMB_VIDEO_ROOT" "$WMB_ROOT/results"
```

`uv --version` 失败表示当前 shell 尚未安装或找不到 uv，生成环境不能继续创建。Cosmos checkout 固定参考源码和配置来源；实际推理入口由表中固定的 Diffusers revision 提供。

源码 revision 输出必须等于 `WMB_COSMOS_REV`。安装后的检查读取 Diffusers 安装元数据，确认实际安装的是表中 commit；导入 `Cosmos3OmniPipeline` 可以发现安装缺失，CUDA 和 BF16 断言则核对参考配置所需的 GPU 能力：

```bash
"$WMB_COSMOS_ENV/bin/python" - <<'PY'
import importlib.metadata
import json
import os
import torch
from diffusers import Cosmos3OmniPipeline

direct = json.loads(
    importlib.metadata.distribution("diffusers").read_text("direct_url.json") or "{}"
)
revision = direct.get("vcs_info", {}).get("commit_id")
assert revision == os.environ["WMB_DIFFUSERS_REV"], revision
assert torch.cuda.is_available()
assert torch.cuda.is_bf16_supported()
print({
    "pipeline": Cosmos3OmniPipeline.__name__,
    "torch": torch.__version__,
    "cuda": torch.version.cuda,
    "diffusers_revision": revision,
})
PY
```

CUDA 或 BF16 断言失败时，当前设备不能直接运行这个参考组合。更换 Torch 后端或 precision 会形成新的生成配置，需要单独验证显存和输出。

## 下载并记录 checkpoint

下载命令把 `WMB_COSMOS_MODEL_REV` 对应的仓库快照写入 `WMB_COSMOS_MODEL`。模型随后以离线方式从这个目录加载，因此这里固定的 revision 也确定了生成阶段读取的配置和权重。

```bash
"$WMB_COSMOS_ENV/bin/python" - <<'PY'
import os
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="nvidia/Cosmos3-Nano",
    revision=os.environ["WMB_COSMOS_MODEL_REV"],
    local_dir=os.environ["WMB_COSMOS_MODEL"],
    max_workers=4,
)
PY
```

固定 revision 包含 68 个文件，总大小为 34,986,890,326 bytes。文件数和总大小用于发现明显缺失，SHA256 清单为每个文件保存可重复比较的内容摘要。下面的命令以 1 MiB 数据块读取文件，不会把约 5 GB 的权重分片一次性载入内存，清单写入 `WMB_COSMOS_CHECKSUMS`：

```bash
export WMB_COSMOS_CHECKSUMS="$WMB_ROOT/results/cosmos3-nano-checksums.json"

"$WMB_COSMOS_ENV/bin/python" - <<'PY'
from hashlib import sha256
import json
import os
from pathlib import Path

root = Path(os.environ["WMB_COSMOS_MODEL"])
destination = Path(os.environ["WMB_COSMOS_CHECKSUMS"])
files = sorted(
    path for path in root.rglob("*")
    if path.is_file() and ".cache" not in path.parts
)
assert len(files) == 68, len(files)
assert sum(path.stat().st_size for path in files) == 34_986_890_326

def file_sha(path):
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

manifest = {
    str(path.relative_to(root)): {
        "bytes": path.stat().st_size,
        "sha256": file_sha(path),
    }
    for path in files
}
destination.write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)
print({"files": len(files), "bytes": sum(path.stat().st_size for path in files)})
PY
```

再次下载后，可以重新生成清单并比较 SHA256。文件数或总大小不符时，重新执行下载命令，不要开始生成。

## 生成配置

参考运行使用以下设置：

| 配置 | 取值 |
| --- | --- |
| 输入 | `first_frame` 与原始 `text_instruction` |
| Precision | BF16 |
| 帧数 / FPS | 189 / 24 |
| 推理步数 | 35 |
| Guidance / flow shift | 6.0 / 10.0 |
| Seed | 每条记录均为 1234 |
| 分辨率 | 与首帧宽高比最近的 480p bucket |
| Prompt 模板 | system prompt 开启，分辨率和时长模板关闭 |
| Safety checker | 加载与调用阶段均关闭 |

五个输出 bucket 为 `832×480`、`640×480`、`480×480`、`480×640` 和 `480×832`。按对数宽高比距离选择最近项，可以避免把所有首帧统一拉伸为 16:9。关闭 safety checker 是本次参考实验的生成设置，不代表 WorldModelBench 的要求；公开结果时必须披露。

## 定义单卡生成命令

`generate_cosmos3_videos` 是内嵌在 Markdown 中的单卡批处理程序。外层 shell 函数保留命令入口，内层 Python 完成数据读取、推理、视频写入和验收。`WMB_DATASET`、`WMB_COSMOS_MODEL` 与 `WMB_VIDEO_ROOT` 分别提供测试记录、checkpoint 和输出目录；可选的 `WMB_LIMIT` 控制本次处理测试集开头的多少条记录，未设置或设为 0 时处理全部 350 条。

程序按以下顺序执行：

1. 读取 350 条测试记录，根据每张首帧的宽高比选择最近的 480p bucket；
2. 查找上次异常中断可能留下的隐藏临时文件，发现后在加载模型前停止；
3. 检查本次范围内已有的 MP4，将通过当前生成规格与完整解码检查的文件标记为已完成，将缺失文件加入待生成列表；
4. 仅在存在待生成样本时加载一次 Pipeline，并为整个顺序生成过程复用；
5. 按数据集顺序生成每条缺失记录，将结果先写入 `.<stem>.partial.mp4`；
6. 检查临时视频的 codec、分辨率、帧数、FPS、时长和完整解码，通过后再用 `os.replace()` 发布为 `<stem>.mp4`；
7. 本次范围处理完毕后重新验证全部已选视频，并汇总分辨率 bucket 数量。

每条记录都会重新创建 seed 为 1234 的 CUDA Generator，因此固定的是单条记录的初始随机状态，不会让后一条记录继承前一条记录已经推进的生成器状态。视频先写入输出目录中的隐藏临时文件，只有在结构检查和完整解码通过后才移动到最终文件名。

已有 MP4 会按照当前记录的预期 bucket 检查 codec、分辨率、189 帧、24 FPS、7.875 秒时长和完整解码。全部通过时跳过；任何一项不符时立即停止，不会覆盖原文件。

```bash
generate_cosmos3_videos() {
  "$WMB_COSMOS_ENV/bin/python" - <<'PY'
from collections import Counter
from fractions import Fraction
import gc
import json
import math
import os
from pathlib import Path
import subprocess
import time

import torch
from diffusers import Cosmos3OmniPipeline
from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
from diffusers.utils import export_to_video, load_image
from PIL import Image

dataset = Path(os.environ["WMB_DATASET"])
model = Path(os.environ["WMB_COSMOS_MODEL"])
video_root = Path(os.environ["WMB_VIDEO_ROOT"])
limit = int(os.environ.get("WMB_LIMIT", "0"))

buckets = {
    "16:9": (832, 480),
    "4:3": (640, 480),
    "1:1": (480, 480),
    "3:4": (480, 640),
    "9:16": (480, 832),
}

def choose_bucket(image_path):
    with Image.open(image_path) as image:
        ratio = image.width / image.height
    name = min(
        buckets,
        key=lambda key: abs(
            math.log(ratio / (buckets[key][0] / buckets[key][1]))
        ),
    )
    return name, buckets[name]

def validate_video(path, width, height):
    assert path.is_file() and path.stat().st_size > 0, path
    payload = json.loads(subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-count_frames",
            "-select_streams", "v:0",
            "-show_entries",
            "stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration",
            "-of", "json",
            str(path),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout)
    assert len(payload.get("streams", [])) == 1, path
    stream = payload["streams"][0]
    assert stream["codec_name"] == "h264", (path, stream)
    assert int(stream["width"]) == width, (path, stream)
    assert int(stream["height"]) == height, (path, stream)
    assert Fraction(stream["avg_frame_rate"]) == Fraction(24, 1), (path, stream)
    assert int(stream["nb_read_frames"]) == 189, (path, stream)
    assert abs(float(stream["duration"]) - 7.875) < 1e-3, (path, stream)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"],
        check=True,
    )

records = json.loads(dataset.read_text(encoding="utf-8"))
assert len(records) == 350
samples = []
for index, record in enumerate(records):
    image_path = dataset.parent / record["first_frame"]
    bucket, (width, height) = choose_bucket(image_path)
    samples.append({
        "index": index,
        "record": record,
        "image": image_path,
        "stem": image_path.stem,
        "bucket": bucket,
        "width": width,
        "height": height,
    })

selected = samples[:limit] if limit else samples
stale = sorted(video_root.glob(".*.partial.mp4"))
assert not stale, {
    "stale_partial_files": [str(path) for path in stale],
    "action": "inspect and remove these temporary files before retrying",
}

pending = []
for sample in selected:
    output = video_root / f"{sample['stem']}.mp4"
    if output.exists():
        validate_video(output, sample["width"], sample["height"])
        print({
            "index": sample["index"] + 1,
            "stem": sample["stem"],
            "status": "skipped_valid",
        })
    else:
        pending.append(sample)

if not pending:
    counts = Counter(sample["bucket"] for sample in selected)
    print({
        "selected": len(selected),
        "generated": 0,
        "buckets": dict(counts),
        "status": "complete",
    })
    raise SystemExit(0)

pipeline = Cosmos3OmniPipeline.from_pretrained(
    str(model),
    torch_dtype=torch.bfloat16,
    device_map="cuda",
    enable_safety_checker=False,
    local_files_only=True,
)
pipeline.scheduler = UniPCMultistepScheduler.from_config(
    pipeline.scheduler.config,
    flow_shift=10.0,
)

for sample in pending:
    output = video_root / f"{sample['stem']}.mp4"
    temporary = video_root / f".{sample['stem']}.partial.mp4"
    assert not output.exists() and not temporary.exists()
    generator = torch.Generator(device="cuda").manual_seed(1234)
    torch.cuda.synchronize()
    started = time.monotonic()
    try:
        result = pipeline(
            prompt=sample["record"]["text_instruction"],
            negative_prompt="",
            image=load_image(str(sample["image"])),
            num_frames=189,
            height=sample["height"],
            width=sample["width"],
            fps=24,
            num_inference_steps=35,
            guidance_scale=6.0,
            enable_sound=False,
            generator=generator,
            output_type="pil",
            return_dict=True,
            use_system_prompt=True,
            add_resolution_template=False,
            add_duration_template=False,
            enable_safety_check=False,
        )
        torch.cuda.synchronize()
        generation_seconds = time.monotonic() - started
        export_to_video(
            result.video,
            str(temporary),
            fps=24,
            macro_block_size=1,
        )
        validate_video(temporary, sample["width"], sample["height"])
        os.replace(temporary, output)
        print({
            "index": sample["index"] + 1,
            "total": len(samples),
            "stem": sample["stem"],
            "bucket": sample["bucket"],
            "resolution": [sample["width"], sample["height"]],
            "generation_seconds": generation_seconds,
            "status": "generated",
        })
    finally:
        temporary.unlink(missing_ok=True)
    del result
    gc.collect()

counts = Counter()
for sample in selected:
    output = video_root / f"{sample['stem']}.mp4"
    validate_video(output, sample["width"], sample["height"])
    counts[sample["bucket"]] += 1
print({
    "selected": len(selected),
    "generated": len(pending),
    "buckets": dict(counts),
    "status": "complete",
})
PY
}
```

运行日志中的 `generated` 表示新视频已通过检查并发布到最终文件名，`skipped_valid` 表示已有视频通过同一组检查。末尾的 `complete` 表示本次 `selected` 范围已经全部验证；它只描述当前 `WMB_LIMIT` 选择的范围，单样本运行中的 `complete` 不代表 350 条已经生成。

## 先生成一个样本

设置 `WMB_LIMIT=1` 后，同一批处理程序只选择测试集第一条记录。这个试跑会覆盖 Pipeline 加载、一次完整推理、临时文件验收和最终文件发布，不会采用另一套简化参数。

```bash
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export WMB_LIMIT=1

generate_cosmos3_videos
```

第一次运行会加载模型并生成测试集第 1 条记录。输出末尾应包含 `status: generated` 和 `status: complete`。`generated` 对应单条视频已经发布，`complete` 对应所选的 1 条记录已全部验证。随后用 FFprobe 读取结构信息，再用 FFmpeg 执行一次独立的完整解码：

```bash
export WMB_SMOKE_VIDEO="$(find "$WMB_VIDEO_ROOT" -maxdepth 1 -name '*.mp4' -print -quit)"
ffprobe -v error -count_frames -select_streams v:0 \
  -show_entries stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration \
  -of json "$WMB_SMOKE_VIDEO"
ffmpeg -v error -i "$WMB_SMOKE_VIDEO" -f null -
```

预期为 H.264、189 帧、24 FPS、7.875 秒，并且 FFmpeg 完整解码无错误。显存不足通常发生在 pipeline 加载或去噪阶段；应停止当前配置并更换能够容纳约 39 GiB 峰值的设备。降低输出规格后得到的是另一套生成配置，不能继续引用该参考运行的资源数据。

## 单卡生成全部 350 条

移除 `WMB_LIMIT` 后，`selected` 恢复为全部 350 条记录。函数会先验证并跳过已经生成的第 1 条，再顺序生成其余记录；`tee` 同时把控制台输出保存到生成日志：

```bash
unset WMB_LIMIT
generate_cosmos3_videos 2>&1 | tee "$WMB_ROOT/results/cosmos3-generation.log"
```

每条成功记录都会输出索引、stem、bucket、分辨率和耗时。正常 Ctrl-C 会删除当前隐藏临时文件，已经发布的 MP4 保持不变。进程被强制终止后若留下 `.*.partial.mp4`，下次运行会停止并列出这些文件；确认它们属于中断任务后，可删除列出的隐藏临时文件，再重新执行同一命令。

已有最终 MP4 若损坏或与当前配置不符，续跑会在加载模型前停止并报告对应路径。保留该文件用于调查，或将其移出输出目录后重新生成；命令不会自动覆盖未知产物。

## 查看进度

生成命令只在视频通过检查后发布最终文件，因此当前目录中的顶层 MP4 数量代表已完成数量：

```bash
export WMB_COMPLETE="$(
  find "$WMB_VIDEO_ROOT" -maxdepth 1 -type f -name '*.mp4' | wc -l
)"
export WMB_REMAINING="$((350 - WMB_COMPLETE))"
printf 'valid_videos=%s remaining=%s\n' "$WMB_COMPLETE" "$WMB_REMAINING"

find "$WMB_VIDEO_ROOT" -maxdepth 1 -type f -name '*.mp4' \
  -printf '%T@ %f\n' | sort -nr | head -n 1
```

目录包含外部复制的文件时，数量不能替代结构检查；重新执行 `generate_cosmos3_videos` 会在续跑前验证已有文件。

## 验收完整输出

350 条生成完成后，再次执行生成函数。它不会加载 pipeline，而是验证并跳过全部视频：

```bash
unset WMB_LIMIT
generate_cosmos3_videos
```

最终输出应包含：

```text
{'selected': 350, 'generated': 0, 'status': 'complete'}
```

bucket 计数应为 `16:9` 215 条、`4:3` 116 条、`1:1` 14 条、`9:16` 5 条、`3:4` 0 条。数量不同表示测试集 revision、bucket 集合或选择逻辑发生变化。全量验收通过后，模型无关检查负责确认 stem 覆盖，再由官方评测读取这些 MP4。

## 导航

- 返回上级：[评测复现](../06-reproduction.md)
- 上一节：[准备评测视频](02-prepare-evaluation-videos.md)
- 下一节：[运行官方评测](04-run-official-evaluation.md)
