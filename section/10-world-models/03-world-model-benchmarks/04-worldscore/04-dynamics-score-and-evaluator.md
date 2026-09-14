# 动态指标、聚合与评测器

动态集合在固定相机下检查指定对象如何变化。它不把“画面中存在运动”视为完成，而是分别量化运动是否出现在正确位置、运动是否足够明显、相邻帧之间是否平滑。三项与静态七项共享归一化和模型级聚合链，但它们的参照信号不同。

## 三项动态指标

| 指标 | 计算对象 | 高分表示 | 不能单独说明 |
| --- | --- | --- | --- |
| Motion accuracy | 用 SAM2 在生成序列传播数据集 mask，以 SEA-RAFT 估计目标区内外的光流 | 指定对象区域的运动相对背景更符合文字对象 | 运动是否连续自然 |
| Motion magnitude | 相邻帧光流幅值 | 生成了较显著的运动 | 运动是否发生在正确对象上 |
| Motion smoothness | VFIMamba 由偶数帧插值得到中间帧，再与真实奇数帧比较 MSE、SSIM、LPIPS | 中间运动与插值预测一致 | 运动幅度或语义正确性 |

motion accuracy 用目标区域和非目标区域的光流中位数之差抵消非预期全局相机运动；对于 T2V，源码还用 Grounding DINO 将对象文字与生成结果关联。motion magnitude 只奖励更大的光流，因此可与 accuracy 脱钩：镜头错误地移动或背景被无关动画扰动，也可能提高幅度。motion smoothness 由 MSE、SSIM 和 LPIPS 三个分量共同归一化，分别处理数值误差、结构相似和感知差异。

## 从分项到两个总分

评测器按下列名单读取单样本的归一化分数。每个 aspect 当前只有一个或一组内部 metric；`subjective_quality` 的两个质量代理先在 aspect 内平均，`motion_smoothness` 的三个分量也先在 metric 内平均。

```python
worldscore_list = {
    "static": [
        "camera_control", "object_control", "content_alignment",
        "3d_consistency", "photometric_consistency",
        "style_consistency", "subjective_quality",
    ],
    "dynamic": [
        "motion_accuracy", "motion_magnitude", "motion_smoothness"],
}
```

记归一化后的静态 aspect 分数为 \(s_1,\ldots,s_7\)，动态 aspect 分数为 \(d_1,d_2,d_3\)，则 `run_evaluate.py` 的模型级聚合为：

\[
\mathrm{WorldScore\text{-}Static}=100\cdot\frac{1}{7}\sum_{i=1}^{7}s_i,
\qquad
\mathrm{WorldScore\text{-}Dynamic}=100\cdot\frac{1}{10}\left(\sum_{i=1}^{7}s_i+\sum_{j=1}^{3}d_j\right).
\]

3D 注册类型只运行 static。论文中的总表仍为它们呈现 dynamic 总分，并将三个动态项按 0 计入；因此 `WorldScore-Dynamic` 对静态模型不是“已验证的动态能力”，而是包含缺失动态能力的综合比较数值。

## `evaluation.json` 到 `worldscore.json`

评测过程先按静态或动态目录读取每个实例的 `evaluation.json`。文件在 aspect 下保存 metric 名、原始 `score` 与 `score_normalized`。`calculate_mean_scores()` 收集同一 metric 的所有样本归一化值，先得到 aspect 的模型均值，再将 7 项或 10 项 aspect 平均写入模型根目录的 `worldscore.json`。

```python
metric_score_list.append(
    np.mean([item["score_normalized"] for item in metric_scores])
)
scores[aspect] = round(np.mean(metric_score_list) * 100, 2)

worldscore_static = np.mean([scores[name] for name in metrics_static])
worldscore_dynamic = np.mean(
    [scores[name] for name in metrics_static + metrics_dynamic]
)
```

这个顺序意味着总分不是先把所有帧或所有原始 metric 值直接混合，而是经过“样本 → metric → aspect → 总分”的多级平均。缺少 `evaluation.json` 的实例不会进入该函数的收集列表；完整性检查与实际提交分数因而是两个不同的条件。

## 分数的解释边界

所有分项都依赖辅助估计器：DROID-SLAM、Grounding DINO、SAM2、SEA-RAFT、VFIMamba、CLIP 系列质量模型。分辨率、帧数、模型输出的时间采样及其版本都可能改变这些代理信号。经验归一化会进一步把原始差异裁剪到固定范围。WorldScore 适合在相同源码、数据和配置下分析同类模型的分项权衡；它不提供跨 benchmark 的通用量纲，也不构成真实物理模拟或下游策略收益的证明。

## 导航

- 返回上级：[WorldScore](../04-worldscore.md)
- 上一节：[静态世界的控制与质量指标](03-static-metrics.md)
- 下一节：[结果、验证与解释边界](05-results-validation-and-limits.md)
