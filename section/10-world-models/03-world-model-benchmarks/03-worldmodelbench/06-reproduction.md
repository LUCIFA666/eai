# 评测复现

WorldModelBench 以生成视频为评测对象。VILA-EWM Judge 读取视频和动作指令，为指令遵循、物理规律和常识生成评分回答；官方 `evaluation.py` 保存回答并聚合出 0–10 分的评测结果。

## 页面分工

| 页面 | 完成的工作 | 主要产物 |
| --- | --- | --- |
| [准备 Benchmark 与 Judge](06-reproduction/01-prepare-benchmark-and-judge.md) | 固定数据与评测版本，安装 Judge，完成单视频冒烟 | 可运行的 VILA-EWM Judge 环境 |
| [准备评测视频](06-reproduction/02-prepare-evaluation-videos.md) | 理解 T2V/I2V 输入和 MP4 命名，检查已有视频 | 通过覆盖与解码检查的视频目录 |
| [使用 Cosmos3-Nano 生成视频](06-reproduction/03-generate-videos-with-cosmos3-nano.md) | 建立 Cosmos3-Nano 推理环境，生成并验收 350 个 I2V 视频 | 350 个 Cosmos3-Nano MP4 |
| [运行官方评测](06-reproduction/04-run-official-evaluation.md) | 对完整视频集执行未修改的 `evaluation.py` | `worldmodelbench_results.json` |
| [评测结果](06-reproduction/05-check-results.md) | 检查输出形状，重新聚合并解释分数 | 可核验的 0–10 分评测结果 |

## 复现路径

复现依次完成[准备 Benchmark 与 Judge](06-reproduction/01-prepare-benchmark-and-judge.md)、[准备评测视频](06-reproduction/02-prepare-evaluation-videos.md)和[运行官方评测](06-reproduction/04-run-official-evaluation.md)，最后在[评测结果](06-reproduction/05-check-results.md)中解读结果文件并复核分数。

WorldModelBench 不固定被测视频生成模型。论文评测的模型包括 CogVideoX-5B、OpenSora v1.2、OpenSoraPlan v1.3 等；其他 T2V 或 I2V 模型也可以接入。无论采用哪一种模型，生成结果都需要符合准备评测视频页面定义的条件构造、stem 命名、覆盖范围和解码要求。选择 Cosmos3-Nano 生成评测视频时，可以阅读[使用 Cosmos3-Nano 生成视频](06-reproduction/03-generate-videos-with-cosmos3-nano.md)，按照其中的参考实现准备环境并生成视频。已有符合要求的视频，或者选择其他 T2V 或 I2V 模型时，不需要阅读该页面。

## 导航

- 返回上级：[WorldModelBench](../03-worldmodelbench.md)
- 上一节：[评测发现与适用边界](05-results-and-limits.md)
