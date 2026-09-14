# 指标归一化与总分聚合

WoW-World-Eval 的原始指标具有不同方向和量纲。FVD、轨迹距离与相机误差越低越好，PSNR、相似度和语义评分越高越好；数值范围还覆盖 0–1、1–5、像素对数比和无固定上界的距离。评分协议先把原始值转为 0–100 的可取性分数，再形成指标组与 Overall Score。

## 从原始值到可取性分数

对模型 \(i\) 和指标 \(m\)，原始测量记为 \(x_{i,m}\)。流程包含四层：

\[
x_{i,m}
\longrightarrow
\hat x_{i,m}
\longrightarrow
s_{i,m}
\longrightarrow
S_{i,g}
\longrightarrow
S_{i,\mathrm{overall}}.
\]

\(\hat x_{i,m}\) 是方向统一后的 0–1 值，\(s_{i,m}\) 是映射后的 0–100 指标分，\(S_{i,g}\) 是 Video Quality、Instruction Understanding、Planning Reasoning 或 Physical Law 组分。

## 固定锚点、裁剪与方向统一

每项指标使用固定下界 \(L_m\) 和上界 \(U_m\)。裁剪函数为

\[
\mathrm{clip}(u;a,b)=\min\{\max\{u,a\},b\}.
\]

对于 higher-is-better（HIB）指标：

\[
\hat x_{i,m}^{\mathrm{HIB}}
=
\frac{\mathrm{clip}(x_{i,m};L_m,U_m)-L_m}
{U_m-L_m}.
\]

对于 lower-is-better（LIB）指标，先执行同样缩放，再反转方向：

\[
\hat x_{i,m}^{\mathrm{LIB}}
=1-\hat x_{i,m}^{\mathrm{HIB}}.
\]

论文明确给出两个绝对锚点：

| 指标 | 方向 | \(L_m\) | \(U_m\) |
| --- | --- | ---: | ---: |
| PSNR | HIB | 0 | 50 |
| FVD | LIB | 0 | 2000 |

其他指标使用理论范围或任务相关绝对目标，但论文未列出完整 \(L_m,U_m\) 表。裁剪意味着超出上下界的原始差异不会继续反映在分数中；锚点选择也会改变分数分辨率。

## 四类单调映射

预缩放后使用单调函数 \(f_m(\cdot;\theta_m)\)，并放大到 0–100：

\[
s_{i,m}
=100f_m(\hat x_{i,m};\theta_m).
\]

论文考虑四种函数：

\[
\begin{aligned}
\text{Simple:}\quad
&f(x)=x,\\
\text{Power:}\quad
&f_\gamma(x)=x^\gamma,\quad \gamma>0,\\
\text{Logit temperature:}\quad
&f_T(x)=\sigma(\mathrm{logit}(x)/T),\quad T>0,\\
\text{Tanh slope:}\quad
&f_\kappa(x)=\frac12\left[\tanh(\kappa(2x-1))+1\right],
\quad \kappa>0.
\end{aligned}
\]

Logit temperature 在计算 \(\mathrm{logit}\) 前把输入裁剪到 \([\epsilon,1-\epsilon]\)，避免端点产生无穷值。Power 改变高低区间的展开程度；Logit temperature 与 Tanh slope 主要改变中间区域和端点的压缩。函数保持排序单调，但会改变模型间的数值间隔。

## 参数选择

论文以人工评分作为监督，为每项指标选择映射类型和参数。附录一处将过程概括为在 \([0,5]\) 网格内选择 Pearson 相关性最高的设置；后续正式定义写为在固定开发集上进行 \(K\) 折交叉验证，最大化 Fisher-\(z\) 平均后的 Pearson 相关性，并以 Spearman 相关性作为并列时的选择依据。参数选定后冻结并用于所有评测。

论文未给出开发集划分、\(K\) 值、候选网格、人工样本与最终测试样本的交叠关系。映射后的 0–100 分因此包含人类评分监督，不是从原始物理量直接得到的自然单位。

## 逐指标映射参数

| 指标 | 映射 | 参数 |
| --- | --- | ---: |
| FVD | Gamma | 1.52 |
| PSNR | Tanh | 4.71 |
| SSIM | Gamma | 0.61 |
| DINO | Gamma | 3.06 |
| DreamSim | Gamma | 2.94 |
| Caption Score | Gamma | 0.12 |
| Sequence Match Score | Gamma | 2.45 |
| Execution Quality Score | Gamma | 2.97 |
| Planning DAG | Simple | — |
| Robot Consistency | Gamma | 2.93 |
| Object Consistency | Tanh | 4.93 |
| Scene Consistency | Gamma | 3.94 |
| Robot Trajectory L2Norm | Gamma | 2.86 |
| Robot Trajectory DTW | Gamma | 1.87 |
| Robot Trajectory FD | Gamma | 4.00 |
| Object Trajectory L2Norm | Gamma | 1.27 |
| Object Trajectory DTW | Gamma | 2.99 |
| Object Trajectory FD | Gamma | 3.52 |
| Physical Score | Simple | — |
| Camera ATE | Simple | — |
| Camera RPE | Simple | — |

表中 Simple 表示预缩放后的线性分数，不使用额外参数。Gamma 或 Tanh 参数只在预缩放之后作用，无法在缺失原始锚点时单独恢复最终分数。

## 指标组

论文结果表所示的组内 Overall 是映射分数的算术平均：

\[
S_{i,\mathrm{VQ}}
=\frac15\sum_{m\in\mathrm{VQ}}s_{i,m},
\]

\[
S_{i,\mathrm{IU}}
=\frac13\sum_{m\in\mathrm{IU}}s_{i,m},
\]

\[
S_{i,\mathrm{PL}}
=\frac1{12}\sum_{m\in\mathrm{PL}}s_{i,m}.
\]

各组组成如下：

| 指标组 | 组成 |
| --- | --- |
| Video Quality | FVD、PSNR、SSIM、DINO、DreamSim |
| Instruction Understanding | Caption、Sequence Match、Execution Quality |
| Planning Reasoning | Planning DAG，即 `LongHorizon` |
| Physical Law | 3 项区域一致性、6 项轨迹、Physical Score、Camera ATE、Camera RPE |

总体分数对四个组赋予相同权重：

\[
S_{i,\mathrm{overall}}
=\frac14
\left(
S_{i,\mathrm{VQ}}
+S_{i,\mathrm{IU}}
+S_{i,\mathrm{PR}}
+S_{i,\mathrm{PL}}
\right).
\]

例如 Hailuo 的四个组分为 56.09、70.11、17.27 和 66.72，算术平均为 52.55。能力类别的样本数量没有直接用作总体组权重，因此 Overall 表示四组分的平衡，而不是 609 条样本的简单逐条平均。

## 22 项信号与 21 个映射项

论文将生成评测描述为 22 项信号。按原始组成计数：

\[
5\ \text{项视觉}
+3\ \text{项语义}
+2\ \text{项规划组成}
+12\ \text{项物理}
=22.
\]

映射参数表只有 21 行，因为规划部分只列出合成后的 Planning DAG，没有分别列出 Node Correctness 和 Task Completion：

\[
5+3+1+12=21.
\]

公式和表格表明，22 项可能将两个规划组成项分开计数，21 项则把二者合成为 `LongHorizon` 后再计入映射表。论文未显式解释这一计数差异，实际实现中的计数方式仍无法确认。

## 分数的解释限制

0–100 分统一了显示方向与范围，却没有建立跨 benchmark 的共同量纲。相同的 10 分差距在 Gamma、Tanh 和 Simple 映射下对应不同原始差异。锚点裁剪还会使极端原始值落在相同端点。

完整复算至少需要全部指标锚点、开发集、人工评分、参数搜索设置、辅助模型版本、组内聚合实现和视频预处理。这些工件目前尚未公开，因而无法从原始输出独立重建映射后分数或生成兼容 leaderboard 结果。

## 导航

- 返回上级：[WoW-World-Eval](../07-wow-world-eval.md)
- 上一节：[物理一致性与因果评测](06-physical-consistency-and-causal-evaluation.md)
- 下一节：[人工评测与 Human Turing Test](08-human-evaluation-and-turing-test.md)
