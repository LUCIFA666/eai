# 视频预测评测协议

直觉物理子集采用约束视频预测。世界模型接收一段场景开头的视频并生成后续帧，参考视频给出同一初始状态下的物理演化。场景刻意减少主导概念之外的变化，因此生成结果与参考结果的差异能够定位到对象运动、遮挡后的状态保持、支撑结果或透视变化。

这一协议比逐帧 RGB 误差更接近评测目标。开放式视频可能存在外观细节差异，而物理错误首先表现为对象在不应出现的位置、轮廓随时间失真、遮挡后不再出现或背景结构漂移。WorldBench 因而把前景对象和背景分开计算。

## SAM2 追踪与前景 mIoU

每个场景的首帧真值分割先转换为对象边界框。SAM2 接收生成视频与这些框作为提示，在后续帧传播对象掩码；评测将每个生成掩码与同一时刻的真值掩码比较。对于第 \(t\) 帧的对象 \(i\)，交并比为：

\[
\operatorname{IoU}_{t,i}=\frac{|M^{\mathrm{pred}}_{t,i}\cap M^{\mathrm{gt}}_{t,i}|}{|M^{\mathrm{pred}}_{t,i}\cup M^{\mathrm{gt}}_{t,i}|}。
\]

前景 mIoU 对所有被评测帧和对象取平均。高分同时要求对象保留可分割的身份、接近正确的图像位置和近似正确的轮廓；它不是对重力、摩擦或碰撞方程的直接测量。一个物体沿视觉上平滑的轨迹运动，仍可能因速度、尺度或遮挡后重现位置错误而得到较低 mIoU。

```text
# 根据论文评测流程整理的说明性伪代码，不是官方实现。
boxes = boxes_from_masks(ground_truth_masks[0])
predicted_masks = sam2.propagate(video=generated_frames, prompts=boxes)

iou = []
for frame_id, objects in paired(predicted_masks, ground_truth_masks):
    for predicted, reference in paired(objects):
        iou.append(area(predicted & reference) / area(predicted | reference))

foreground_miou = mean(iou)
```

补充材料将真实视频上的 SAM2 自动追踪与人工标注比较，报告总体 mIoU 为 0.9445。这个验证支持 SAM2 作为测量管线的一部分，但不意味着模型生成结果中的每一次对象形变都能被无误分割；分数仍同时受到生成内容和追踪质量影响。

## 背景 RMSE

背景区域由所有对象掩码的补集得到。合成场景的背景在参考视频中保持不变，因此背景像素的均方根误差可以记录模型是否在物体运动时改变了墙面、地面、光照纹理或其他环境结构：

\[
\operatorname{RMSE}_{\mathrm{bg}}=
\sqrt{\frac{1}{|B|}\sum_{p\in B}\left(I^{\mathrm{pred}}(p)-I^{\mathrm{gt}}(p)\right)^2}。
\]

\(B\) 是参考掩码定义的背景像素集合，\(I^{\mathrm{pred}}\) 与 \(I^{\mathrm{gt}}\) 是生成与参考图像。该指标越低越好。它与前景 mIoU 形成互补：模型可能保持住运动物体，却在静态环境中产生背景闪烁；也可能背景几乎不变，而对象轨迹完全错误。

## 分数的解释范围

前景 mIoU 和背景 RMSE 都依赖固定初始视频、固定参考未来与 SAM2 的追踪流程。两项数值适合比较同一场景、相同续写长度和相同模型输出设置下的相对表现，不能直接转化为动作控制精度、三维状态误差或机器人任务成功率。物理参数子集用另一条测量管线把轨迹恢复为加速度、摩擦或黏度，覆盖 mIoU 无法直接给出的定量误差。

## 导航

- 返回上级：[WorldBench](../06-worldbench.md)
- 上一节：[直觉物理数据与场景](01-intuitive-physics-data-and-scenes.md)
- 下一节：[物理参数估计](03-physical-parameter-estimation.md)
