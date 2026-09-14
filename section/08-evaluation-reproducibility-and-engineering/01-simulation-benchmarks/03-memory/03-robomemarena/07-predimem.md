# PrediMem 方法

PrediMem 是 RoboMemArena 配套的记忆方法，作为记忆基线。它是一个双系统结构，外加一个只在训练期起作用的预测编码头。下面的架构与训练设定来自论文，预测编码头的实现来自仓库 `predictive_coding_head/`。

## 双系统结构

PrediMem 把慢思考和快执行分开：

- 系统二（慢、审议）：一个 Qwen3-VL-8B 视觉语言模型，读入当前观测与记忆库，输出下一步该做的子任务指令，并同时预测一个 `Is_Keyframe` 标志，判断当前帧是否该作为关键帧存入记忆。训练时视觉塔冻结，只微调语言侧，训练约 2 个 epoch、4 张 H100、学习率 1e-5。
- 系统一（快、执行）：一个 π0.5 流匹配（flow-matching）策略，接收系统二给出的子任务与当前观测，生成低层动作块。

两者分工明确：系统二负责在长时程上维护记忆、决定做什么，系统一负责把子任务落成连续动作。两者异步运行：系统二不必每步都推，它维护一个单槽的子任务缓冲，系统一按当前子任务连续出动作，直到系统二更新缓冲里的子任务。

## 系统二的输入输出

系统二每次推理读入双相机（俯视 `agentview_rgb` 与腕部 `eye_in_hand_rgb`）的记忆库图像，输出严格 JSON，只含两个字段：当前该执行的子任务，以及最近窗口内哪些帧是关键帧。评测参考实现的系统提示把这个契约写得很明确：

```text
# SYSTEM_PROMPT_MEMORY_DEMO（评测参考实现）
You will observe two kinds of visual evidence from the same long-horizon execution:
1. Historical keyframes: moments before the current step ...
2. A recent 5-frame dual-camera window ending at the current frame ...
- The JSON must contain exactly two fields: current_primitive and keyframe_positions.
- keyframe_positions are 1-indexed positions within the recent 5-frame window.
```

`current_primitive` 更新单槽缓冲里的子任务，`keyframe_positions` 标出最近 5 帧窗口里哪些帧该作为关键帧存进记忆（对应论文里的 `Is_Keyframe` 判定）。

## 记忆库

系统二的记忆库由两部分构成：

- 关键帧条目：由 `keyframe_positions` / `Is_Keyframe` 判定并累积存入的历史关键帧，不设容量上限（评测参考实现里 `K_MAX=0`）。
- 近期帧：最近的 5 帧双相机窗口，末帧即当前帧。

需要说明的是，论文示意图里画的近期窗口 W=16、关键帧库按 FIFO 淘汰只是示意；正文与评测参考实现用的近期窗口都是 5 帧、关键帧库都不设上限。关键帧提供跨越长时程的稀疏锚点（放了什么、放到哪），近期帧提供短时的连续上下文，两者拼起来作为系统二每步推理的记忆输入。

## 预测编码头

为了让系统二学到对未来有预测力的表示，训练时给它挂一个预测编码头：一个两层 MLP，用当前帧的图像 token 预测下一帧的图像特征。它只在训练期存在，推理期移除，不增加推理开销。头的构造是标准的两层 MLP：

```python
# predictive_coding_head.py：两层 MLP 投影头
nn.Sequential(
    nn.Linear(hidden_size, hidden_size),
    nn.GELU(),
    nn.Linear(hidden_size, hidden_size),
)
```

预测目标是下一帧图像特征，且用 `no_grad` 取教师特征（stop-gradient，梯度不回传到教师），损失由 MSE 与余弦两项组成：

```python
# 逐对（当前帧预测 → 下一帧目标）累积两项损失
mse_terms.append(F.mse_loss(predicted_next.float(), target_next.float()))
cosine_terms.append(
    1.0 - F.cosine_similarity(predicted_next.float(), target_next.float(), dim=-1).mean()
)
```

最终损失把主任务的文本损失与预测编码损失按标量权重相加，两项权重默认都是 0.1：

```python
def combine_main_and_predictive_losses(
    ce_loss, mse_loss, cosine_loss,
    mse_weight: float = 0.1, cosine_weight: float = 0.1,
):
    total_loss = ce_loss
    if mse_loss is not None and cosine_loss is not None:
        total_loss = total_loss + float(mse_weight) * mse_loss + float(cosine_weight) * cosine_loss
    return total_loss
```

也就是说，总损失是文本损失加上 0.1 倍的预测编码损失（MSE 与余弦各占 0.1）。预测下一帧特征这个辅助目标促使系统二编码出带时间预测性的记忆表示，消融中去掉这个头会掉约 6 个点。

## 导航

- 返回上级：[RoboMemArena](../03-robomemarena.md)
- 上一节：[评测协议与指标](06-evaluation-protocol.md)
- 下一节：[结果与发现](08-results.md)
