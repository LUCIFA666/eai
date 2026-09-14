# 准备评测视频

WorldModelBench 不直接调用被测视频生成模型。生成阶段把测试记录转换为 350 个 MP4；评测阶段再按文件名将视频与原始动作指令关联。这个接口允许不同模型和推理框架使用同一套 Judge。

## 测试记录与模型输入

`worldmodelbench.json` 的每条记录包含三个与生成有关的字段：

| 字段 | 含义 |
| --- | --- |
| `text_first_frame` | 初始场景的文本描述 |
| `text_instruction` | 场景随后应发生的事件或动作 |
| `first_frame` | I2V 使用的首帧图像，也是输出文件名的依据 |

T2V 和 I2V 的输入方式不同：

| 输入模式 | 模型输入 | 输出文件 |
| --- | --- | --- |
| T2V | `" ".join([text_first_frame, text_instruction])` | `<first_frame stem>.mp4` |
| I2V | `first_frame` 图像与 `text_instruction` | `<first_frame stem>.mp4` |

例如，记录中的 `first_frame` 为 `images/69620089860948e38a4921dd4869d24f.jpg` 时，两种模型都必须输出：

```text
69620089860948e38a4921dd4869d24f.mp4
```

文件名中的 stem 负责关联记录，输出视频不需要保留 `images/` 子目录。

## 建立视频目录

```bash
cd worldmodelbench-repro
export WMB_ROOT="$PWD"
export WMB_BENCHMARK="$WMB_ROOT/src/WorldModelBench"
export WMB_DATASET="$WMB_BENCHMARK/worldmodelbench.json"
export WMB_JUDGE_ENV="$WMB_ROOT/envs/judge-vila-c8f603b4"

export WMB_MODEL_NAME=my-video-model
export WMB_VIDEO_ROOT="$WMB_ROOT/videos/$WMB_MODEL_NAME"
mkdir -p "$WMB_VIDEO_ROOT"
```

`WMB_MODEL_NAME` 和 `WMB_VIDEO_ROOT` 应替换为实际模型名称与视频目录。正式检查只读取 `WMB_VIDEO_ROOT` 顶层的 `*.mp4`，嵌套目录中的文件不会参与评测。

## 生成视频

WorldModelBench 没有规定 codec、precision、分辨率、帧数、FPS、推理步数、采样器或随机种子。这些设置会改变被测模型的输出，应与结果一起记录：

- 模型仓库和 revision；
- T2V 或 I2V，以及实际 prompt 变换；
- 首帧的缩放、裁剪或填充方式；
- 输出分辨率、帧数、FPS 和 codec；
- precision、采样器、推理步数和 guidance；
- 随机种子、negative prompt 和 system prompt；
- prompt 扩写或安全过滤；
- 生成拒绝、失败或缺失样本的处理方式。

同一次结果应采用明确且一致的生成协议。若模型根据输入画幅选择不同分辨率，应记录选择规则，而不是只记录某一个输出尺寸。

评测视频可以通过以下两种方式准备：

1. 已有符合要求的视频时，将 MP4 放入 `WMB_VIDEO_ROOT` 或者使用软链接。
2. 如果没有符合要求的视频，可以选择合适的 T2V 或 I2V 模型，按照本页定义的输入和命名规则生成视频，并将输出写入 `WMB_VIDEO_ROOT`。[使用 Cosmos3-Nano 生成视频](03-generate-videos-with-cosmos3-nano.md)提供了一种生成视频的参考实现。

## 检查覆盖与文件结构

通用验收分为集合检查和逐文件检查。集合检查从 `worldmodelbench.json` 取得 350 个预期 stem，再与 `WMB_VIDEO_ROOT` 顶层的 MP4 比较，因而能同时发现缺失文件、额外文件和重复 stem。集合一致后，逐文件检查依次确认：

1. 文件大小大于 0；
2. FFprobe 能找到视频流；
3. FFmpeg 能从头到尾解码该视频。

文件存在只说明目录中有对应路径；包含视频流说明容器中有可识别的视频轨道；完整解码通过才说明整条轨道没有在中途损坏。下面的命令要求三个条件全部成立：

```bash
"$WMB_JUDGE_ENV/bin/python" - <<'PY'
import json
import os
from pathlib import Path
import subprocess

dataset = Path(os.environ["WMB_DATASET"])
video_root = Path(os.environ["WMB_VIDEO_ROOT"])
records = json.loads(dataset.read_text(encoding="utf-8"))
expected_list = [Path(record["first_frame"]).stem for record in records]
expected = set(expected_list)
paths = list(video_root.glob("*.mp4"))
actual_list = [path.stem for path in paths]
actual = set(actual_list)

assert len(expected_list) == len(expected) == 350, "dataset stems are not unique"
assert len(actual_list) == len(actual), "video stems are not unique"
assert actual == expected, {
    "missing": sorted(expected - actual),
    "extra": sorted(actual - expected),
}

for index, stem in enumerate(sorted(expected), start=1):
    video = video_root / f"{stem}.mp4"
    assert video.stat().st_size > 0, f"empty video: {video}"
    probe = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=index",
            "-of", "csv=p=0",
            str(video),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert probe.stdout.strip(), f"no video stream: {video}"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"],
        check=True,
    )
    if index % 50 == 0 or index == 350:
        print({"checked": index, "total": 350})

print({"videos": len(actual), "coverage": "complete", "decode": "passed"})
PY
```

成功输出应包含：

```text
{'videos': 350, 'coverage': 'complete', 'decode': 'passed'}
```

断言中的 `missing` 表示测试记录没有对应视频；`extra` 表示目录中存在不属于当前测试集的 MP4。两种情况都应在评测前修正，不能通过改动测试 JSON 隐藏。空文件、无视频流或 FFmpeg 解码失败表示生成或写盘未完成，应重新生成相应 stem。

这项通用检查不判断视频内容是否正确，也不要求所有模型采用相同的时长和画幅。模型自身的输出规格应由生成记录说明。

## 评测入口

视频通过上述检查后，进入[运行官方评测](04-run-official-evaluation.md)。

## 导航

- 返回上级：[评测复现](../06-reproduction.md)
- 上一节：[准备 Benchmark 与 Judge](01-prepare-benchmark-and-judge.md)
- 下一节：[使用 Cosmos3-Nano 生成视频](03-generate-videos-with-cosmos3-nano.md)
