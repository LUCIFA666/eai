# 评测结果

未修改的 `evaluation.py` 将原始 Judge 回答和解析值保存在 `worldmodelbench_results.json`。结果检查只使用该文件，不引入另一套解析或替代分数。

## 结果文件的三部分

结果检查只需要 Judge 环境中的 Python 和明确的 JSON 路径。`WMB_MODEL_NAME` 用于选择对应结果目录，`test -f` 在解析前确认文件存在：

```bash
cd worldmodelbench-repro
export WMB_ROOT="$PWD"
export WMB_JUDGE_ENV="$WMB_ROOT/envs/judge-vila-c8f603b4"

export WMB_MODEL_NAME=my-video-model
export WMB_RESULT="$WMB_ROOT/results/$WMB_MODEL_NAME/worldmodelbench_results.json"
test -f "$WMB_RESULT"
```

使用 Cosmos3-Nano 参考结果时设置：

```bash
export WMB_MODEL_NAME=Cosmos3-Nano-I2V-411f42a8
export WMB_RESULT="$WMB_ROOT/results/cosmos3-nano-411f42a8/worldmodelbench_results.json"
```

JSON 包含三个顶层字段：

| 字段 | 内容 |
| --- | --- |
| `model_name` | 正式评测命令记录的被测模型名称 |
| `preds` | 每个 stem 的 8 个原始自然语言回答 |
| `accs` | `evaluation.py` 从回答中解析出的数值或布尔值 |

完整结果中，`preds` 有 350 条；`accs.instruction`、`accs.physical_laws` 和 `accs.common_sense` 的长度分别为 350、1750 和 700。

`preds` 按 stem 保留分组后的自然语言回答，可以定位某个样本及某个问题的 Judge 输出。`accs` 按评测顺序保存脚本已经解析的值，适合直接聚合分数。结果解释出现异常时，`accs` 用于确认实际计分值，`preds` 用于追溯该值来自哪段回答。

## 分数的组成

每条视频产生三组结果：

- Instruction：一个 0–3 分的指令遵循分数；
- Physics：五个物理违规问题，没有检测到相应违规时各计 1 分；
- Common Sense：Poor Aesthetics 与 Temporal Inconsistency 两个问题，没有检测到相应问题时各计 1 分。

模型级分数由各项均值相加：

| 指标 | 范围 | 聚合方式 |
| --- | ---: | --- |
| Instruction | 0–3 | 350 个指令分数的均值 |
| Physics | 0–5 | 五个物理问题通过率之和 |
| Common Sense | 0–2 | 两个常识问题通过率之和 |
| 总分 | 0–10 | 三组分数之和 |

## 重新聚合 `accs`

三个 `accs` 数组按样本顺序排列。Instruction 每个样本只有一个值，可以直接对 350 个值求均值。Physics 中每个样本连续保存 5 个问题的值，因此 `physics[offset::5]` 会从每组取出相同位置，恢复某一个 Physics 子项的 350 个结果；Common Sense 使用步长 2 以相同方式恢复两个子项。

每个子项先跨 350 个样本求平均，通过率随后相加得到 Physics 0–5 分和 Common Sense 0–2 分。Instruction 均值、Physics 分数和 Common Sense 分数再相加得到 0–10 总分。下面的命令直接使用 `evaluation.py` 保存的 `accs` 重现这一过程：

```bash
"$WMB_JUDGE_ENV/bin/python" - <<'PY'
import json
import os
from pathlib import Path

result = json.loads(Path(os.environ["WMB_RESULT"]).read_text(encoding="utf-8"))
accs = result["accs"]
instruction = [float(value) for value in accs["instruction"]]
physics = [bool(value) for value in accs["physical_laws"]]
common = [bool(value) for value in accs["common_sense"]]

assert len(instruction) == 350
assert len(physics) == 350 * 5
assert len(common) == 350 * 2

instruction_score = sum(instruction) / 350
physics_items = [
    sum(physics[offset::5]) / 350
    for offset in range(5)
]
common_items = [
    sum(common[offset::2]) / 350
    for offset in range(2)
]
physics_score = sum(physics_items)
common_score = sum(common_items)
total = instruction_score + physics_score + common_score

print(json.dumps({
    "model_name": result["model_name"],
    "instruction": instruction_score,
    "physics_items": physics_items,
    "physics": physics_score,
    "common_sense_items": common_items,
    "common_sense": common_score,
    "total": total,
}, indent=2))
PY
```

重新计算的 Instruction、Physics、Common Sense 和总分应与正式评测日志一致。差异表示结果路径、样本覆盖或聚合数组不是同一次完整运行。

## `evaluation.py` 的解析限制

`evaluation.py` 直接从自然语言回答中提取值。Instruction 使用冒号后的最后一段转换为浮点数；转换失败时记为 0。因此，Instruction 为 0 既可能表示动作完全失败，也可能表示回答格式不能解析，具体原因需要查看同一 stem 的 `preds.instruction`。

物理和常识问题使用以下判断：

```python
"no" in pred.lower()
```

这项规则没有检查独立单词，`noticeable` 等包含连续字母 `no` 的文本也可能被判为通过。`preds` 保留了原始回答，可用于识别这类解析风险；报告评测结果时仍应保留未修改的 `accs` 和评测分数。

`evaluation.py` 将第一个 common-sense 子项显示为 `framewise`，但对应问题实际是 Poor Aesthetics。解释结果时应使用 Poor Aesthetics 这一语义，同时保留脚本字段名和数值。

## Cosmos3-Nano 参考运行

固定 Cosmos3-Nano 生成设置和 VILA-EWM 评测组合得到一次完整本地运行：

| 项目 | 参考结果 |
| --- | ---: |
| 视频样本 | 350 / 350 |
| Judge 回答 | 2,800 / 2,800 |
| Instruction | 2.1885714286 / 3 |
| Physics | 4.2885714286 / 5 |
| Common Sense | 1.1142857143 / 2 |
| 总分 | 7.5914285714 / 10 |
| 单卡评测墙钟时间 | 2,582.594 秒，约 43 分钟 |
| 单卡评测峰值显存 | 6,005 MiB |

`7.5914` 描述的是锁定生成参数、关闭 safety checker、开启 system prompt、固定视频输入和随机 Judge 下的一次运行。它不是复现验收线、稳定期望值或排行榜基准。完整复现的验收对象是 revision、350 个输入视频、2,800 个回答、结果形状和 `evaluation.py` 的聚合方法；Judge 随机采样可能使重复运行的具体分数发生变化。

参考运行的七个二值子项通过率为：

| 子项 | 通过率 |
| --- | ---: |
| Newton | 1.0000 |
| Mass / solid | 0.5771 |
| Fluid | 0.9914 |
| Penetration | 0.7229 |
| Gravity | 0.9971 |
| Poor Aesthetics | 0.6000 |
| Temporal | 0.5143 |

这些数值用于核对字段顺序和聚合口径，不用于规定其他视频生成模型应达到的水平。

## 导航

- 返回上级：[评测复现](../06-reproduction.md)
- 上一节：[运行官方评测](04-run-official-evaluation.md)
