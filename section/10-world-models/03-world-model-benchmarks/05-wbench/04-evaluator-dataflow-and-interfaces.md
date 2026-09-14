# 评测器数据流与模型接口

WBench 的评测对象是与 case 一一对应的多轮视频。`main.py` 以 `work_dirs/<model>/videos/case_<id>_combined.mp4` 作为模型输出入口，读取 `data/cases/case_<id>.json` 取得 interaction、评测问题和适用维度，再将每项结果写入 `work_dirs/<model>/evaluation/<metric>/case_<id>.json`。最后的 `report.json` 分别聚合完整集合与 navigation 子集的均值和样本数；Navigation Score 还保留 Accuracy 与 Consistency 各自的有效样本数。

## 从 case 到分项结果

评测流程包含四类中间对象：case JSON 规定条件和问题，合成视频承载所有 turn，预计算结果提供几何和目标跟踪信息，分项 JSON 保存每一项判断。`precompute` 阶段为视频生成 MegaSaM 位姿、SAM2 掩码和 Depth Anything 3 深度；`gpu` 阶段处理视觉特征、轨迹与重投影指标；`vlm` 阶段处理场景、主体、语义交互和因果问题；`report` 阶段按指标收集 case 分数并计算 `full` 与 `navi` 聚合。

`visual_plausibility` 使用独立的视觉判别器执行，结果仍落入同一 `evaluation/visual_plausibility/` 目录，随后由 report 阶段读入。因而 22 项指标并非由一种模型或一次前向计算产生：相机位姿、实例掩码、深度、视觉特征、VLM 和物理伪影判别器分别提供不同证据。

| 阶段 | 输入 | 主要产物 | 对应指标 |
| --- | --- | --- | --- |
| precompute | 多轮视频、navigation case | MegaSaM poses、SAM2 masks、DA3 depth | navigation、空间/视角/主体/重投影一致性 |
| gpu | 视频与预计算结果 | 各视觉和几何分项 JSON | quality、consistency、navigation |
| vlm | 视频、case 条件和评测问题 | 语义判断 JSON | setting、语义 interaction、causal fidelity |
| report | 各指标 JSON | `report.json` 中的均值和样本数；Navigation Score 的分量均值与两个样本数 | full 与 navi 汇总 |

Navigation Score 的逐 case 结果包含 `accuracy`、`consistency` 和 `NavScore`。没有重复或对称动作对时，后两项为 `null`，但该 case 的 Accuracy 仍参与模型级聚合。`report.json` 因而分别生成 `navigation_accuracy` 与 `navigation_consistency`，再将两项均值合成为 `navigation_trajectory`；其中 `n` 对应 Accuracy 的样本数，`n_consistency` 对应 Consistency 的样本数。该结构将缺少可比较动作对与评测执行失败区分开。

## Case 字段如何进入评测

`src/utils/case_loader.py` 将原始字典拆为 `Settings`、`Interaction` 与 `EvalQuestion`。以下摘录展示被评测器消费的核心字段；`eval_dimensions` 指定某个 case 可启用的评测维度，`eval_questions` 绑定当前轮的判定条件。

```python
settings = Settings(
    scene=scene,
    style=settings_dict.get("style", ""),
    perspective=settings_dict.get("perspective", ""),
    subject=subject,
    initial_image=settings_dict.get("initial_image"),
)

interactions.append(Interaction(
    turn=inter_dict.get("turn", 0),
    type=inter_dict.get("type", ""),
    action=inter_dict.get("action", ""),
    prompt=inter_dict.get("prompt", ""),
))
```

`settings.perspective` 影响导航目标轨迹的解释，`interactions` 决定视频应如何按轮切分，`eval_questions` 将 event edit、subject action 和 perspective switch 的 VLM 判断限制在该 case 声明的目标上。公开视频缺失 case JSON 时仍可计算部分纯视频指标，但无法对 setting、语义交互或 case 专属物理问题作出有条件的判断。

## 按轮切分视频

语义交互与导航分数都依赖正确的轮次边界。`src/utils/turn_splitter.py` 优先使用已切出的 `clips/case_<id>/turn_<i>.mp4`；没有单独 clip 时，根据模型名、总帧数和每轮时长推导边界。不同生成器具有不同的首帧条件、窗口重叠和 VAE 尾帧规则，因此统一等分整段视频可能会把某轮动作归入相邻轮。

```python
def resolve_turns(model, case_id, video_path, interactions, clips_dir=None):
    n_turns = len(interactions) if interactions else 1
    bounds = split_turns(
        model,
        total_frames,
        chunk_lengths=[item.get("chunk_length", 4) for item in interactions],
        n_turns=n_turns,
        case_id=case_id,
    )
    return ResolvedTurns(source="clips" if clips_exist else "bounds", turns=turns)
```

这里的 `bounds` 为左闭右开帧区间。若边界提前或滞后，VLM 可能在错误片段中寻找事件，导航估计也会把一个动作的位姿变化分配给另一轮；这类偏差会改变逐轮分数，即使合成视频的总时长不变。

## 三类模型接口

| 模型类别 | 输入接口 | 生成组织 | 覆盖范围 |
| --- | --- | --- | --- |
| text-conditioned | 首帧、环境/主体提示和每轮交互提示 | 每轮生成后把末帧传给下一轮 | 289 个 case、四类交互 |
| camera-conditioned | 首帧和由导航转换的每轮 6-DoF pose | 根据位姿轨迹生成完整导航视频 | 158 个 navigation case |
| action-conditioned | 首帧和离散键盘/鼠标动作 | 根据动作计划生成完整导航视频 | 158 个 navigation case |

camera-conditioned 适配器将 `W/A/S/D` 与方向键先转换为 `{move, yaw, pitch}`，再映射为相机外参和内参；action-conditioned 适配器保留 token，并可生成 `{keyboard, mouse}` 表示。两类接口都没有 event editing、subject action 和 perspective switching 的统一输入表达。评测报告将完整集合与 navigation 子集分开保存，避免用缺少语义接口的模型去比较完整交互分数。

## 导航

- 返回上级：[WBench](../05-wbench.md)
- 上一节：[一致性与物理指标](03-consistency-and-physical-metrics.md)
- 下一节：[结果与解释](05-results-and-interpretation.md)
