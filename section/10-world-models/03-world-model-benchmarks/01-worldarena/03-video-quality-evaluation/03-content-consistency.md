# Content Consistency

Content Consistency 检查主体、背景和像素运动在时间上是否稳定。三项指标都可以只读取生成视频，但依赖 DINO、CLIP 或光流估计器，并使用 Dynamic Degree 抑制近静态输出。

| 指标 | 表征 | 高分表示什么 |
| --- | --- | --- |
| Subject Consistency | DINO 对象结构特征 | 主体形状和部件布局保持稳定 |
| Background Consistency | CLIP 全局场景特征 | 场景语义与机位变化较小 |
| Photometric Consistency | 前向、反向光流循环 | 相邻帧的往返运动较自洽 |

## Subject Consistency

Subject Consistency 的输入只有生成视频。DINO 将每帧转换为对象结构特征，重点保留形状、部件布局和空间拓扑，并对轻微光照变化保持一定容忍度。评测器让当前帧同时与首帧和前一帧比较：首帧提供整段视频的身份锚点，前一帧用于发现相邻时刻的突然跳变。计算相似度时，负余弦值先截断为 0：

$$
q(a,b)=\max\left(0,
\frac{a^\top b}{\lVert a\rVert_2\lVert b\rVert_2}
\right).
$$

评测器实现的逐视频原始分数为

$$
S_{\mathrm{subj,raw}}
=\frac{1}{T-1}\sum_{t=2}^{T}
\frac{q(f_t,f_1)+q(f_t,f_{t-1})}{2},
$$

其中 $f_t$ 是第 $t$ 帧的 DINO 特征。每个当前帧得到两个相似度，两者平均后再汇总整段视频。高分表示主体在相邻帧间连续，并且到视频后段仍保留首帧中的结构；低分表示主体逐渐变形、部件消失，或在某一帧突然变成另一种外观。论文附录公式写成求和，但相邻文字称其为平均值；评测器明确除以 $T-1$。

论文定义使用 Dynamic Degree 进行连续惩罚：

$$
S_{\mathrm{subj}}^{\mathrm{paper}}
=S_{\mathrm{subj,raw}}
\min\left(1,\frac{S_{\mathrm{dyn}}}{\gamma}\right).
$$

评测器固定阈值 `0.1213`，采用不同的分段实现：

$$
S_{\mathrm{subj}}^{\mathrm{eval}}=
\begin{cases}
S_{\mathrm{subj,raw}}S_{\mathrm{dyn}}, & S_{\mathrm{dyn}}\le 0.1213,\\
S_{\mathrm{subj,raw}}, & S_{\mathrm{dyn}}>0.1213.
\end{cases}
$$

以抓起带棱纹的瓶子为例，如果瓶身、瓶盖和标签在离开桌面后仍保持原有位置关系，当前帧与首帧的 DINO 特征通常较接近；如果瓶身在抓取后变成长条、标签移动到瓶盖上，或者夹爪与瓶子融合，分数会下降。主体即使被完整地搬到错误位置，外观仍可保持高度相似，因此高分不表示任务正确。大幅视角变化、夹爪遮住瓶身或物体旋转到背面也可能降低特征相似度，即使瓶子本身没有发生形变。

## Background Consistency

Background Consistency 也只读取生成视频，但使用逐帧 CLIP 视觉特征 $h_t$。与 DINO 的主体结构特征相比，CLIP 更偏向全局场景语义和布局，例如画面是否仍是同一张机器人工作台、柜体和地面是否位于相近区域、机位是否突然改变。评测器同样让当前帧分别与首帧和前一帧比较，并复用非负相似度 $q$：

$$
S_{\mathrm{bg,raw}}
=\frac{1}{T-1}\sum_{t=2}^{T}
\frac{q(h_t,h_1)+q(h_t,h_{t-1})}{2}.
$$

逐帧相似度的平均值越接近 1，场景在 CLIP 特征空间中越稳定。论文与评测器的动态惩罚差异和 Subject Consistency 相同：论文乘以 $\min(1,S_{\mathrm{dyn}}/\gamma)$，评测器仅在 $S_{\mathrm{dyn}}\le0.1213$ 时直接乘以 $S_{\mathrm{dyn}}$。

以把红色方块从桌面移到蓝色垫子为例，固定机位下的桌沿、垫子和储物柜在整个过程中应保持相近布局；如果视频中途从正视工作台切换成俯视柜体，当前帧与首帧的 CLIP 相似度会下降。桌面上的小划痕或远处物体颜色持续漂移时，CLIP 仍可能把画面概括为同一类机器人工作区，分数变化可能很小。任务协议若允许移动相机，合理的视角变化也会被当成背景不稳定。

## Photometric Consistency

Photometric Consistency 的输入仍是生成视频，但当前评测器实际检查的是相邻帧之间的光流循环。SEA-RAFT 先估计从当前帧到下一帧的前向光流，再估计从下一帧回到当前帧的反向光流。若前向流把像素位置 $p$ 移到下一帧，再由反向流移回，最终位置应接近 $p$。AEPE 是往返后的平均端点误差：误差越小，前后两次匹配对像素运动的解释越一致。

论文将该过程定义为图像变换：

$$
E_{\mathrm{photo}}^{\mathrm{paper}}
=\frac{1}{T}\sum_{t=1}^{T}
\left\lVert
\operatorname{Warp}_{\mathrm{back}}\!\left(
\operatorname{Warp}_{\mathrm{fwd}}(I_t,\mathbf u_t),\mathbf u'_{t+1}
\right)-I_t
\right\rVert_2,
$$

$$
S_{\mathrm{photo,raw}}^{\mathrm{paper}}
=\frac{1}{E_{\mathrm{photo}}^{\mathrm{paper}}}
\min\left(1,\frac{S_{\mathrm{dyn}}}{\gamma}\right).
$$

评测器没有重建图像颜色，而是使用 SEA-RAFT 估计双向光流。对中央裁剪区域 $\Omega$ 中的位置 $p$，其坐标循环误差为

$$
E_{\mathrm{flow}}^{\mathrm{eval}}
=\operatorname{mean}_{t,p\in\Omega}
\left\lVert
\mathbf u_t(p)+
\mathbf u'_{t+1}\!\left(
\operatorname{clip}\!\left(\operatorname{round}(p+\mathbf u_t(p))\right)
\right)
\right\rVert_2.
$$

评测器只在中央裁剪区域内汇总误差，以减少画面边缘的越界匹配。它取 $1/E_{\mathrm{flow}}^{\mathrm{eval}}$，因此循环误差越小，原始分数越高；随后再应用 `0.1213` 分段动态惩罚，防止近静态视频轻易取得高分。经验边界为 `0.1257` 和 `6.7899`。论文公式比较往返变换后的图像，实现比较往返后的像素坐标，因此两者不能视为同一测量对象。

以把绿色方块搬到桌子右侧为例，若方块边缘从当前位置向右移动，反向光流又能把对应边缘带回原位置，循环误差较小；如果方块在相邻帧中突然裂成两块、边缘闪烁或位置跳变，前后光流难以形成一致对应，分数通常下降。当前实现不会直接比较颜色值，因此方块由绿色变成红色但轮廓和运动完全一致时，分数未必明显降低。遮挡、金属反光和快速运动也会破坏光流匹配，使物理合理的视频产生较大 AEPE。高分只说明可见像素运动较自洽，不表示颜色、材质或动作目标正确。

## 三项信号的关系

主体结构漂移首先影响 DINO，场景和机位变化首先影响 CLIP，运动对应关系异常首先影响光流循环。三项都不能判断稳定的动作是否符合指令，也不能单独证明颜色、材质或物理状态真实。

## 导航

- 返回上级：[视频质量评测](../03-video-quality-evaluation.md)
- 上一节：[Motion Quality](02-motion-quality.md)
- 下一节：[Physics Adherence](04-physics-adherence.md)
