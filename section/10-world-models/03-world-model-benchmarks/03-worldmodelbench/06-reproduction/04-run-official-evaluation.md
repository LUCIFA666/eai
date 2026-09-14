# 运行官方评测

官方评测从已经通过检查的 350 个 MP4 开始，执行固定 revision 下未修改的 `evaluation.py`。评测只依赖视频目录、原始测试记录和 VILA-EWM Judge，不读取 Cosmos3-Nano 的生成实现。

## 设置输入与结果路径

这组变量把一次评测的三个对象关联起来：`WMB_MODEL_NAME` 是写入结果的模型标识，`WMB_VIDEO_ROOT` 是该模型的 350 个输入视频，`WMB_RESULT_DIR` 是本次评测的独立输出目录。`WMB_SAVE_PREFIX` 不带扩展名，`evaluation.py` 会在其后添加 `.json`，因此 `WMB_RESULT` 指向最终结果文件。

```bash
cd worldmodelbench-repro
export WMB_ROOT="$PWD"
export WMB_BENCHMARK="$WMB_ROOT/src/WorldModelBench"
export WMB_DATASET="$WMB_BENCHMARK/worldmodelbench.json"
export WMB_JUDGE_ENV="$WMB_ROOT/envs/judge-vila-c8f603b4"
export WMB_JUDGE="$WMB_ROOT/models/vila-ewm-qwen2-1.5b"

export WMB_MODEL_NAME=my-video-model
export WMB_VIDEO_ROOT="$WMB_ROOT/videos/$WMB_MODEL_NAME"
export WMB_RESULT_DIR="$WMB_ROOT/results/$WMB_MODEL_NAME"
export WMB_SAVE_PREFIX="$WMB_RESULT_DIR/worldmodelbench_results"
export WMB_RESULT="$WMB_SAVE_PREFIX.json"
```

使用 Cosmos3-Nano 页面生成的视频时，将模型名和目录设置为：

```bash
export WMB_MODEL_NAME=Cosmos3-Nano-I2V-411f42a8
export WMB_VIDEO_ROOT="$WMB_ROOT/videos/cosmos3-nano-411f42a8"
export WMB_RESULT_DIR="$WMB_ROOT/results/cosmos3-nano-411f42a8"
export WMB_SAVE_PREFIX="$WMB_RESULT_DIR/worldmodelbench_results"
export WMB_RESULT="$WMB_SAVE_PREFIX.json"
```

结果目录由模型名显式确定。不要通过目录排序自动选择最近一次运行；分析已有结果时，应直接设置其完整路径。

## 正式评测预检

预检不加载 checkpoint，也不发送评测问题。它依次核对四部分：

1. WorldModelBench 仓库是否位于固定 commit，`evaluation.py` 的 SHA256 是否与经过验证的脚本一致；
2. 测试集的 350 个预期 stem 是否与视频目录完全相同；
3. 每个 MP4 是否非空，并且其第一条视频流能由 FFmpeg 完整解码；
4. Judge 环境中的 Python，以及语言模型、视觉投影器和视觉编码器权重是否存在。

因此，`formal_evaluation_started: False` 表示命令只完成输入预检，没有消耗 Judge 推理时间：

```bash
"$WMB_JUDGE_ENV/bin/python" - <<'PY'
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

benchmark = Path(os.environ["WMB_BENCHMARK"])
dataset = Path(os.environ["WMB_DATASET"])
video_root = Path(os.environ["WMB_VIDEO_ROOT"])
judge = Path(os.environ["WMB_JUDGE"])
judge_python = Path(os.environ["WMB_JUDGE_ENV"]) / "bin/python"

revision = subprocess.run(
    ["git", "-C", str(benchmark), "rev-parse", "HEAD"],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
).stdout.strip()
assert revision == "00b7aa17a05f9fd1ab5c8f66bcf476d04c9c33bf", revision

evaluation = benchmark / "evaluation.py"
assert evaluation.is_file()
assert sha256(evaluation.read_bytes()).hexdigest() == (
    "f77747cb500b5eab678387d500bf35cf32e4dff3e5a92f5921356581e55f6203"
)

records = json.loads(dataset.read_text(encoding="utf-8"))
expected = {Path(record["first_frame"]).stem for record in records}
actual = {path.stem for path in video_root.glob("*.mp4")}
assert len(expected) == 350
assert actual == expected, {
    "missing": sorted(expected - actual),
    "extra": sorted(actual - expected),
}

for index, stem in enumerate(sorted(expected), start=1):
    video = video_root / f"{stem}.mp4"
    assert video.stat().st_size > 0, video
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(video),
            "-map", "0:v:0", "-f", "null", "-",
        ],
        check=True,
    )
    if index % 50 == 0 or index == 350:
        print({"decoded": index, "total": 350})

required_weights = [
    judge / "llm/model.safetensors",
    judge / "mm_projector/model.safetensors",
    judge / "vision_tower/model.safetensors",
]
assert judge_python.is_file(), judge_python
assert all(path.is_file() for path in required_weights)
print({
    "benchmark_revision": revision,
    "videos": len(actual),
    "decode": "passed",
    "judge_files": "present",
    "formal_evaluation_started": False,
})
PY
```

预期输出包含 350 个视频、`decode: passed` 和 `formal_evaluation_started: False`。缺失或额外 stem 应回到视频准备页处理；解码失败应重新生成对应视频；Judge 文件或 Python 环境缺失应回到第一页重新完成 checkpoint 加载和冒烟。

## 确认 Judge 的随机采样设置

采样参数保存在 checkpoint 的 `llm/generation_config.json` 中，而不是写在后面的评测命令里。下面的检查读取实际配置，并与参考 checkpoint 的五项取值比较：

```bash
"$WMB_JUDGE_ENV/bin/python" - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["WMB_JUDGE"]) / "llm/generation_config.json"
config = json.loads(path.read_text(encoding="utf-8"))
actual = {
    key: config[key]
    for key in (
        "do_sample",
        "temperature",
        "top_p",
        "top_k",
        "repetition_penalty",
    )
}
expected = {
    "do_sample": True,
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "repetition_penalty": 1.1,
}
assert actual == expected, actual
print(actual)
PY
```

正式命令不覆盖这些参数，也不传 `--cot`。`do_sample=True` 表示每次回答由温度、top-p 和 top-k 共同控制的随机采样产生。相同视频与 checkpoint 可以得到不同措辞，解析后的个别值也可能变化；重复评测核对的是输入、revision 和输出形状，回答文本和分数不要求逐字节相同。

## 前台运行官方评测

官方脚本发现结果 JSON 已存在时会直接加载旧结果并跳过推理。开始前创建新的空结果目录：

```bash
test ! -e "$WMB_RESULT_DIR"
mkdir -p "$WMB_RESULT_DIR"
```

`test ! -e` 失败表示目标目录已经存在。检查目录内容并为新评测改用新的显式目录名，不要删除或覆盖来源不明的结果。

评测调用实际传入四个参数：

| 参数 | 作用 |
| --- | --- |
| `--model_name` | 将被测模型标识写入结果的 `model_name` 字段 |
| `--video_dir` | 指定 350 个顶层 MP4 所在目录 |
| `--judge` | 指定 VILA-EWM checkpoint 目录 |
| `--save_name` | 指定结果文件前缀，脚本会写出同名 `.json` |

选择 GPU 后，从 benchmark 目录运行未修改的脚本。标准输出和标准错误通过 `tee` 同时显示在终端并保存到 `evaluation.log`：

```bash
export PHYSICAL_GPU=0
export CUDA_VISIBLE_DEVICES="$PHYSICAL_GPU"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

(
  cd "$WMB_BENCHMARK"
  "$WMB_JUDGE_ENV/bin/python" evaluation.py \
    --model_name "$WMB_MODEL_NAME" \
    --video_dir "$WMB_VIDEO_ROOT" \
    --judge "$WMB_JUDGE" \
    --save_name "$WMB_SAVE_PREFIX"
) 2>&1 | tee "$WMB_RESULT_DIR/evaluation.log"
export WMB_EVAL_STATUS="${PIPESTATUS[0]}"
test "$WMB_EVAL_STATUS" -eq 0
test -f "$WMB_RESULT"
```

管道最后一个进程是 `tee`，直接读取 `$?` 只能得到日志写入状态。`${PIPESTATUS[0]}` 保存管道中评测子 shell 的退出状态，后两个 `test` 分别确认推理正常退出和结果 JSON 已生成。

控制台会依次处理 350 个视频，每个视频产生 1 个 instruction、5 个 physical laws 和 2 个 common sense 回答。脚本只在整批结束后保存 JSON；进程中断时保留日志，使用新的结果目录重新运行，不要拼接部分输出。

## 可选的 tmux 运行

长任务可以在独立 tmux session 中执行同一条官方命令。`-c` 显式指定 benchmark 工作目录，不依赖 tmux 启动时的当前目录：

```bash
export WMB_SESSION="wmb-eval-$(date -u +%Y%m%dT%H%M%SZ)"
tmux new-session -d \
  -s "$WMB_SESSION" \
  -c "$WMB_BENCHMARK" \
  "CUDA_VISIBLE_DEVICES='$PHYSICAL_GPU' \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
'$WMB_JUDGE_ENV/bin/python' evaluation.py \
--model_name '$WMB_MODEL_NAME' \
--video_dir '$WMB_VIDEO_ROOT' \
--judge '$WMB_JUDGE' \
--save_name '$WMB_SAVE_PREFIX' \
> '$WMB_RESULT_DIR/evaluation.log' 2>&1"

tmux attach -t "$WMB_SESSION"
```

`Ctrl-b d` 只分离终端，不停止评测。session 结束后，`test -f "$WMB_RESULT"` 用于确认整批结果已经保存。若目录中只有日志而没有 JSON，评测没有完整结束。

## 检查结果形状

每条样本在 `preds` 中保存 8 个原始回答，因此 350 条样本应有 2,800 个回答。相同回答经脚本解析后写入三个扁平数组：Instruction 每条 1 个值，共 350 个；Physics 每条 5 个值，共 1,750 个；Common Sense 每条 2 个值，共 700 个。下面的命令同时核对样本级结构与三个数组长度：

```bash
"$WMB_JUDGE_ENV/bin/python" - <<'PY'
import json
import os
from pathlib import Path

result = json.loads(Path(os.environ["WMB_RESULT"]).read_text(encoding="utf-8"))
assert result.get("model_name") == os.environ["WMB_MODEL_NAME"]
preds = result["preds"]
accs = result["accs"]
assert len(preds) == 350, len(preds)

for stem, item in preds.items():
    assert len(item["instruction"]) == 1, stem
    assert len(item["physical_laws"]) == 5, stem
    assert len(item["common_sense"]) == 2, stem

assert len(accs["instruction"]) == 350
assert len(accs["physical_laws"]) == 1750
assert len(accs["common_sense"]) == 700
answers = sum(
    len(group)
    for item in preds.values()
    for group in item.values()
)
assert answers == 2800, answers
print({
    "model_name": result["model_name"],
    "samples": len(preds),
    "answers": answers,
    "instruction_values": len(accs["instruction"]),
    "physics_values": len(accs["physical_laws"]),
    "common_sense_values": len(accs["common_sense"]),
})
PY
```

只有 350 个样本和 2,800 个回答全部通过，结果才代表完整 WorldModelBench 运行。样本不足通常由缺失视频或错误视频目录引起，应以评测日志和 `preds` 中的 stem 定位。

## 导航

- 返回上级：[评测复现](../06-reproduction.md)
- 上一节：[使用 Cosmos3-Nano 生成视频](03-generate-videos-with-cosmos3-nano.md)
- 下一节：[评测结果](05-check-results.md)
