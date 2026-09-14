# 静态世界的控制与质量指标

静态部分包含 7 个 aspect。前三项判断生成是否执行 world specification，后四项判断输出视频是否维持可用的几何、外观和感知质量。每项先在样本或帧对上得到原始值，再按 `aspect_info` 指定的方向和经验范围变为 0–1；最终模型级分数才乘以 100。

## Controllability

| 指标 | 参照与计算 | 高分表示 | 典型失败 |
| --- | --- | --- | --- |
| Camera control | DROID-SLAM 从生成帧估计轨迹，与 \(\mathcal T\) 的旋转和尺度对齐平移误差比较 | 镜头沿指定路径变化 | 镜头不动、方向相反、视角漂移 |
| Object control | 从下一场景文本抽取一至两个对象描述，以 Grounding DINO 检测生成场景中的对应对象 | 指定对象出现 | 新场景缺少目标物或对象替换错误 |
| Content alignment | CLIPScore 比较下一场景文本和生成场景 | 整体语义与文本相符 | 物体存在但场景类型、属性或关系不符 |

相机项先分别得到旋转误差 \(e_\theta\) 与平移误差 \(e_t\)，再以几何均值形成原始相机误差：

\[
e_{\mathrm{camera}}=\sqrt{e_\theta e_t}.
\]

实现对平移执行尺度对齐，这使该项检查轨迹形状和相对移动，不把未知的全局尺度直接当成错误。对象检测只覆盖从后续文本抽取的少量对象；CLIPScore 覆盖完整文本，两项结合后才同时描述前景对象与整体场景语义。

## Quality

| 指标 | 参照与计算 | 高分表示 | 未覆盖的内容 |
| --- | --- | --- | --- |
| 3D consistency | DROID-SLAM 的共视像素重投影误差 | 跨帧几何稳定 | 文本是否正确 |
| Photometric consistency | SEA-RAFT 前向/反向光流闭环的平均 endpoint error | 外观随时间不闪烁、不漂移 | 静态画面是否美观 |
| Style consistency | 初始图像与场景锚帧在 VGG19 多层 Gram matrix 上的风格损失 | 整体风格保持 | 对象几何是否正确 |
| Subjective quality | CLIP-IQA+ 与 CLIP Aesthetic 的归一化分数组合 | 人类偏好的感知质量代理较高 | 动作与物理规律 |

3D consistency 和 photometric consistency 的参照不同。前者依赖 SLAM 的几何重投影，后者用相邻帧光流来回映射后的 AEPE 捕捉纹理闪烁；同一座山可以保持类别和几何轮廓，却在草地纹理上发生明显漂移。Style consistency 则比较初始图像和该场景代表帧的 VGG 特征 Gram matrix，关注风格统计而非逐像素相等。

## 归一化方向与尺度

`aspect_info` 不直接平均原始量纲。相机误差、重投影误差、AEPE 和 Gram matrix 损失的原始值越低越好；对象检测率、CLIPScore 和两项质量代理越高越好。实现对带多个分量的 camera error 分别裁剪并归一化后取几何均值；对带统计基线的 CLIPScore 和质量代理先做 z-score 映射，再裁剪到指定区间。

```python
"camera_error": {
    "empirical_max": [15, 0.5],
    "empirical_min": [0, 0],
    "higher_is_better": [False, False],
},
"content_alignment": {
    "avg": 26.67, "std": 0.8875,
    "z_max": 1.2741, "z_min": -1.5950,
    "range": [0.25, 0.75], "higher_is_better": True,
}
```

经验上下界、均值和标准差是该 benchmark 的评分协议。它们让异质指标可以进入同一平均值，也意味着 100 分不是原始物理量，更不能与使用其他归一化方式的基准直接互换。高静态分数表示这些指标在指定数据上的联合表现较好，不足以推出模型具有完整的物理因果理解。

## 导航

- 返回上级：[WorldScore](../04-worldscore.md)
- 上一节：[数据与生成结果契约](02-dataset-and-generation-contract.md)
- 下一节：[动态指标、聚合与评测器](04-dynamics-score-and-evaluator.md)
