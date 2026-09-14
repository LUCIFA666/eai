# World specification 与任务

WorldScore 将世界生成拆成连续的 next-scene generation。第 (k) 步不直接要求模型复现某一段真实未来，而是给出当前场景、希望抵达的下一场景和空间布局。形式化地，当前场景、下一场景和布局分别为：

\[
\mathcal C=\{\mathbf I,\mathcal P\},\qquad
\mathcal N,\qquad
\mathcal L=\{\mathcal T,\mathcal Y\},
\]

其中 \(\mathbf I\) 是当前图像，\(\mathcal P\) 是其文字描述；\(\mathcal N\) 描述下一场景应出现的内容；\(\mathcal T=(\mathbf C_1,\ldots,\mathbf C_N)\) 是相机矩阵轨迹，\(\mathcal Y\) 是相机运动文字。模型经自身的条件预处理后输出视频：

\[
\mathbf V=g_{\mathrm{world}}\bigl(w_{\mathrm{proc}}(\mathcal C,\mathcal N,\mathcal L)\bigr).
\]

因此，图像条件、文本条件和显式轨迹不是同一种约束：图像固定已知状态，\(\mathcal N\) 检查内容扩展，\(\mathcal T\) 提供几何参照，\(\mathcal Y\) 为主要依赖语言条件的视频模型提供可读的相机指令。

## 静态世界与动态世界

静态任务中的变化主要来自场景扩展和相机移动。小世界只含一个后续场景，大世界连续生成三个后续场景，因而总共跨越四个场景。`DataLoader.set_interpframe_num()` 对每个场景段保留 `frames - 1` 个新增帧，并在相邻段复用锚帧；大世界的长序列错误会在后续锚帧继续传递。

动态任务保持场景内容与相机位置，\(\mathcal N\) 改为描述场内运动，例如动物移动或液体流动。该设置把镜头运动从运动信号中分离出来，使目标区域是否发生指定运动、运动量是否足够以及帧间是否抖动可以独立计分。动态数据还提供运动对象和 mask，供 motion accuracy 使用。

| 任务 | 场景内容 | 相机 | 主要评分信号 |
| --- | --- | --- | --- |
| Static | 新场景或同场景视角扩展 | 指定轨迹与相机运动 | controllability、quality |
| Dynamic | 同一场景中的指定物体运动 | 固定 | dynamics，及静态质量/控制项形成的总分基础 |

## 相机布局

公开实现用 `layout_info` 将布局名映射为文字提示与类型。单个测试样本可包含一个或多个该类运动，代码中的组合布局也有明确的文字形式。

| 布局 | 提示词 | 类型 |
| --- | --- | --- |
| `push_in` | `push in` | intra-scene |
| `orbit_left` / `orbit_right` | `orbit left` / `orbit right` | intra-scene |
| `pull_out` | `pull out` | inter-scene |
| `move_left` / `move_right` | `move left` / `move right` | inter-scene |
| `pan_left` / `pan_right` | `pan left` / `pan right` | inter-scene |
| `pull_left` / `pull_right` | 移动、拉远、平移的组合 | inter-scene |
| `fixed` | `fixed` | 固定相机 |

实现中的单项记录同时保存 `prompt`、`scenenum` 和 `layout_type`：

```python
layout_info = {
    "push_in": {"scenenum": 1, "prompt": "push in", "layout_type": "intra"},
    "move_left": {"scenenum": 1, "prompt": "move left", "layout_type": "inter"},
    "fixed": {"scenenum": 1, "prompt": "fixed", "layout_type": "camera fix"},
}
```

intra-scene 运动仍在原场景中，评测器会跳过该段的 `content_alignment` 与对象控制分支：原有场景内容没有被要求替换，因而把它当成新场景文本服从度会混入不适用的条件。这个跳过规则只限制相应内容指标，不取消相机轨迹和一致性检查。

## 统一视频输出的含义

3D 模型可以先建模场景再按 \(\mathcal T\) 渲染，4D 模型可以建模时空变化，视频模型可以直接按 I2V 或 T2V 条件采样。WorldScore 不要求这些模型共享表示，也不把内部状态作为评分对象；评测器读取的共同对象是有序帧、初始图像、文本和必要的轨迹或 mask。这样的统一消除了输出格式差异，但不会消除任务能力差异：只有静态能力的 3D 模型无法由该接口获得动态运动分项。

## 导航

- 返回上级：[WorldScore](../04-worldscore.md)
- 下一节：[数据与生成结果契约](02-dataset-and-generation-contract.md)
