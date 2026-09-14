# 评测器

公开评测器 `evaluation.py` 将条件视频转换为结构化分数。它读取每条测试记录的动作指令和对应生成视频，按 instruction、physical laws 与 common sense 三种类型构造问题，再把视频和问题共同交给 VILA-EWM judge。judge 的自然语言回答经过解析后形成 8 个数值，最终按模型、指标和子项聚合。

评测器不比较生成视频与参考后续视频，也不访问生成模型的隐变量、扩散轨迹或控制状态。它观察的是最终视频和公开条件，因此整个协议属于基于输出行为的评测。

## 从条件到分数的数据流

一次完整评测包含五个连续阶段：

1. 测试记录提供 `text_instruction` 以及与生成视频对应的样本标识。
2. `EvaluationType` 将问题分为 instruction、physical laws 和 common sense。
3. 评测器为当前类型填充问题模板，把生成视频与问题共同送入 judge。
4. judge 返回带有解释和结论的自然语言回答，评测器将结论解析为分数或布尔值。
5. 单条回答写入原始预测集合，解析值进入指标数组，全部样本完成后形成模型级结果。

三种类型共享同一段视频，却使用不同的条件信息。instruction 问题包含当前样本的 `text_instruction`，因为动作目标随记录变化；五个物理问题和两个常识问题使用固定模板，它们检查所有视频中相同类别的违规。

| 类型 | 每个视频的问题数 | 问题中的条件 | 回答契约 | 数值范围 |
| --- | ---: | --- | --- | ---: |
| `instruction` | 1 | 当前 `text_instruction` | `Score: [score]` | 0–3 |
| `physical_laws` | 5 | 固定违规描述 | `Yes` 或 `No` | 每项 0/1 |
| `common_sense` | 2 | 固定质量问题 | `Yes` 或 `No` | 每项 0/1 |

每段视频因此产生 8 个回答。350 条条件完整覆盖时，共有 350 个 instruction 回答、1,750 个 physics 回答和 700 个 commonsense 回答，合计 2,800 个判断。

## 三类问题模板

`EvaluationType` 只定义三个顶层类别，细粒度问题由 `QUESTION_POOL` 展开。instruction 没有问题池，因为每条记录只有一个动态动作目标；另两类分别遍历固定问题。

```python
class EvaluationType(Enum):
    INSTRUCTION = "instruction"
    PHYSICAL_LAWS = "physical_laws"
    COMMON_SENSE = "common_sense"
```

instruction 模板在问题中写入动作指令，并列出 0–3 四级标准。judge 需要同时识别视频中的主体、动作和结果状态，最后输出一个等级。固定物理问题依次检查无外力运动、质量或固体形变、异常流体、物体穿透和重力异常；固定常识问题检查低质画面与时序不连续。

这种拆分避免让 judge 在一次回答中同时权衡所有现象。五个物理问题独立作答后，质量守恒问题不会被正常重力表现抵消；两项常识问题也不会因为 instruction 完成而自动通过。代价是同一视频需要多次判断，而且各项仍可能受到共同的视觉理解误差影响。

## 四级分数与二值问题

instruction 使用四级量表，是因为动作完成具有明显的中间状态。主体缺失、动作方向错误、朝目标发展和完整完成分别对应 0、1、2、3。只使用二值成功会把错误动作与接近完成的动作放在同一类别，也会增加短视频结尾位置对结果的影响。

物理与常识问题采用二值输出，因为问题已经写成是否出现某种违规。评测器的问题语义是：

\[
\text{Does the video exhibit violation } q?
\]

所以 `Yes` 表示检测到问题，记 0 分；`No` 表示未检测到问题，记 1 分。这一方向与指标名称容易产生混淆：结果数组中的 `true` 或 1 表示通过该项，而不是违规成立。

| judge 结论 | 问题语义 | 聚合值 |
| --- | --- | ---: |
| `Yes` | 视频出现所述违规或质量问题 | 0 |
| `No` | 视频未出现所述违规或质量问题 | 1 |

二值问题没有区分违规持续时间或严重程度。一帧短暂穿透与长时间穿透都记为该项失败；完全没有相关对象的视频与清晰展示正确交互的视频都可能记为通过。二值值适合统计问题出现率，无法表达物理正确性的连续程度。

## 自然语言回答的解析

judge 先生成自然语言，再由规则提取最终结论。instruction 回答要求以 `Score: [score]` 收束，评测器取最后一个冒号后的文本并解析为浮点数。解析失败时，该项被记为 0。这个默认值把输出格式错误与动作完全失败合并到同一数值，因此原始回答是解释异常低分的重要依据。

physics 与 commonsense 的解析规则检查回答的小写文本是否包含 `no`：

```python
score = "no" in pred.lower()
```

这段实现把输出格式纳入评测协议。标准结论 `No` 会得到通过值，标准结论 `Yes` 会得到失败值；包含额外否定词的非标准回答则可能改变解析结果。自然语言解释能够提供判断依据，但最终分数仍由字符串规则决定，而不是重新分析解释内容。

评测器还支持保留或移除逐步分析提示。两种提示形式可能改变回答内容和分数，因此使用不同提示策略得到的结果属于不同评测设置。论文中的可靠性与模型排名只支持论文采用的 judge 和提示条件，不能把提示变化视为无影响的显示选项。

## 原始预测与聚合值

结果对象分为 `preds` 和 `accs` 两个层次。`preds` 按视频保存 judge 的原始回答，保留每个问题的解释与结论；`accs` 保存从回答中解析出的数值，用于计算分项和总分。

```json
{
  "model_name": "MODEL",
  "preds": {
    "sample_id": {
      "instruction": ["... Score: 3"],
      "physical_laws": ["No", "No", "No", "No", "No"],
      "common_sense": ["No", "No"]
    }
  },
  "accs": {
    "instruction": [3.0],
    "physical_laws": [true, true, true, true, true],
    "common_sense": [true, true]
  }
}
```

两个层次回答不同问题。`preds` 说明 judge 为什么给出结论以及回答格式是否符合契约；`accs` 说明这些结论如何进入统计。仅保留模型总分会失去单样本失败位置和解析依据，仅阅读原始回答则无法直接得到统一量纲的模型比较。

数组顺序也承载子项含义。每个视频在 `physical_laws` 中依次追加 Newton、Mass、Fluid、Penetration 和 Gravity，在 `common_sense` 中依次追加 Frame-wise 与 Temporal。聚合函数按固定步长取出同一位置的值，因此子项名称、问题顺序和数组顺序必须一致。

## 模型级聚合的实现

`process_results()` 先以 `preds` 的记录数作为已评视频数 \(N\)，再根据每类数组长度与 \(N\) 的比值判断子项数量。instruction 的比值为 1，commonsense 为 2，physics 为 5。每个位置分别求均值后，同组子项相加：

```text
instruction overall = mean(instruction scores)
commonsense overall = frame-wise pass rate + temporal pass rate
physics overall = sum(five physics pass rates)
total = instruction overall + commonsense overall + physics overall
```

这种实现保留三种量纲：

- instruction overall 是 0–3 的平均等级；
- commonsense overall 是两个通过率之和，范围为 0–2；
- physics overall 是五个通过率之和，范围为 0–5。

总分范围为 0–10。分组总分不是百分比，单个二值子项才可以直接解释为通过率。例如 physics overall 为 4.2 表示五个通过率之和为 4.2，不能写成物理正确率为 420% 或 84%；只有在额外除以 5 后，才能得到五项等权平均通过率。

## 样本覆盖与领域统计

模型比较要求披露实际条件覆盖。评测器遇到无法取得的视频时会跳过该记录，聚合分母随已处理样本变化，而不会自动把缺失项记为 0。因此两个模型即使都得到 8 分，也可能分别对应不同的条件子集。论文也记录了闭源接口拒绝部分样本的情况，排行榜分数不能一概解释为对完整 350 条条件取平均；覆盖不一致时，模型差异同时包含样本集合差异。

公开脚本不直接计算领域统计，也不把 `domain` 或 `subdomain` 写入结果对象。领域结果需要用 `preds` 中实际出现的视频标识重新匹配 `worldmodelbench.json`，再把相应解析值按问题顺序分组；存在缺失视频时不能直接假定 `accs` 与 350 条原始记录逐项对齐。完整覆盖时每个领域有 50 条条件，领域总分沿用相同的 3+2+5 聚合方式。子领域样本数并不相等，细粒度均值更容易受单个样本影响。

样本完整性、输入模式和 judge 设置共同定义一次有效比较：

| 比较条件 | 不一致时的影响 |
| --- | --- |
| 条件集合 | 模型可能在难度不同的样本子集上取均值 |
| T2V 或 I2V 模式 | 初始状态的条件信息和保持约束不同 |
| judge 与提示模板 | 自然语言判断及解析结果可能变化 |
| 问题顺序与解析规则 | 子项含义或通过值方向可能错位 |

评测输出因此不仅包含一个排行榜分数，也记录分数由哪些视频、哪些问题和哪些解析值构成。协议层信息是结果可解释性的组成部分。

## 导航

- 返回上级：[WorldModelBench](../03-worldmodelbench.md)
- 上一节：[人工标注与 VILA-EWM](03-human-annotations-and-judge.md)
- 下一节：[评测发现与适用边界](05-results-and-limits.md)
