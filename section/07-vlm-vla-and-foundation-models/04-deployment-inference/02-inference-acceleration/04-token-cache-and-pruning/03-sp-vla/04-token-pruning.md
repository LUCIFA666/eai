# token 剪枝源码

SP-VLA 的剪枝逻辑在 `prismatic/extern/hf/modeling_prismatic.py` 里，由两个模块级函数 `edge_detection()`、`map_edges_to_tokens()` 和 `PrismaticVisionBackbone.forward()` 组成。剪枝发生在双视觉主干出 patch、进投影层之前：先按 SigLIP 末层注意力给 token 打分，再并上 Canny 边缘 token，最后按速度定的阈值决定保留多少。本页按这条链给出实现、默认值与加速数字。

## 本节目标

理解 Canny 边缘怎么映射到 token、SigLIP 注意力分数怎么算、注意力 token 与边缘 token 怎么取并集、剪枝阈值如何随 `z_trans` 变化，以及 `z_thre_prune`、`z_min_prune` 各控制什么。

## Canny 边缘到 token

`edge_detection()` 对原图做 Canny，`map_edges_to_tokens()` 把边缘像素映射到 14×14 的 patch 网格，凡边缘和大于 0 的 patch 对应的 token 都保留：

```python
def edge_detection(image):
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    return cv2.Canny(gray, threshold1=100, threshold2=200)     # 双阈值 Canny

def map_edges_to_tokens(image, edges, patch_size):             # patch_size=14
    n_rows, n_cols = edges.shape[0] // patch_size, edges.shape[1] // patch_size
    # 按 patch 切块，统计每块的边缘像素和
    patches = as_strided(edges, shape=(n_rows, n_cols, patch_size, patch_size), strides=...)
    patch_edge_sums = patches.sum(axis=(2, 3))
    return np.where(patch_edge_sums.ravel() > 0)[0]            # 含边缘的 token 索引
```

Canny 的双阈值 100/200 决定边缘的多少：调低会纳入更多弱边缘、保留更多 token，调高只留强轮廓。这一步补的是纯注意力打分容易漏掉的几何边界，去掉它精度会明显下降，见下面的消融。

## 注意力打分与并集选择

`PrismaticVisionBackbone.forward()` 先给 SigLIP 末层 attention 的 `q_norm`、`k_norm` 挂 hook 取出 query、key，算缩放点积注意力并在多头上取均值，得到每个 token 的注意力分数、按分数降序排序：

```python
# 从 SigLIP 末层取 Q、K，算注意力并在多头上取均值
siglip_attn = torch.matmul(siglip_q, siglip_k.transpose(-2, -1)) / math.sqrt(siglip_k.shape[-1])
siglip_attn = torch.softmax(siglip_attn, dim=-1).mean(dim=1).mean(dim=1)
attention_score, siglip_idx = torch.sort(siglip_attn, descending=True)
```

阈值按速度定。`cfg.z_trans` 是调度模块写进来的上一次真实动作的竖直平移。低于 `z_thre_prune` 时阈值取 1，等于不剪；超过后阈值随速度线性下降，速度越高阈值越低、保留越少：

```python
z_trans = cfg.z_trans
if z_trans < cfg.z_thre_prune:
    threshold = 1                                              # 低速不剪，保全 token
else:
    clipped_z = min(z_trans, 1)
    threshold = 1 - (clipped_z - cfg.z_thre_prune) * (cfg.z_min_prune / (1 - cfg.z_thre_prune))
```

保留数由累积注意力定：把排好序的注意力分数累加，累积值小于阈值的 token 全保留。再对这批高注意力 token 索引和 Canny 边缘索引取并集，`np.union1d` 天然按升序返回、保持 token 原始顺序。最后对 DINOv2、SigLIP 两路 patch 用同一份索引剪，保证两路 token 对齐：

```python
cum_scores = attention_score.cumsum(dim=1)
keep_tokens = (cum_scores < threshold).sum(dim=1) + 1         # 累积注意力定保留数
important_idx = siglip_idx[:, :keep_tokens].squeeze(0).tolist()

edge = edge_detection(cfg.raw_image)
edge_index = map_edges_to_tokens(cfg.raw_image, edge, 14)
important_idx = np.union1d(important_idx, edge_index)         # 注意力 ∪ 边缘，保序

cfg.token_prune_rate_one_step = 1 - len(important_idx) / patches.shape[1]
patches = patches[:, important_idx]                           # 剪 DINOv2
patches_fused = patches_fused[:, important_idx]               # 剪 SigLIP
```

`save_tokens()` 另外维护一份 6 帧的 token 历史，用 `low_speed_token_prune_flag`（`save_prune_tokens / history_token_number > 0.7`）记录近几帧是否多数在剪枝，供低速段整体收敛剪枝行为。

## 可调参数

剪枝行为由这几个参数控制，实际取值以 `run_libero.py` 里各套件的设置为准：

| 参数 | 含义 | 默认 / 示例 | 调大 / 调小的影响 |
| --- | --- | --- | --- |
| `z_thre_prune` | 开始剪枝的竖直速度下限 | 0.3–0.5（按套件） | 调大更晚开始剪、更保精度；调小更早剪、更省算力 |
| `z_min_prune` | 高速段的剪枝强度系数 | 0.7–0.9（按套件） | 调大高速时剪枝更激进、更省算力；调小高速时保留更多 |
| Canny 双阈值 | 边缘检测的强弱边界 | 100 / 200 | 调低保留更多弱边缘 token；调高只留强轮廓 |
| `token_prune_rate_one_step` | 当前帧实际剪枝比例（记录值） | 运行时写入 | 仅为观测量，反映这一帧剪掉的 token 占比 |

## 加速数字

LIBERO 四套件（OpenVLA 基座）上 SP-VLA 相对基线的成功率与 FLOPs（论文报告，精度在 A100 40GB）：

| 设定 | 平均成功率 | FLOPs 占比 | 加速 |
| --- | --- | --- | --- |
| OpenVLA 基线 | 74.60% | 100% | 1.0× |
| SP-VLA 无损档 | 74.90% | 73.64% | 1.35× |
| SP-VLA 激进档 | 71.90% | 66.51% | 1.50× |

剪枝判据的消融说明边缘分支不可省。只用注意力打分、去掉 Canny 边缘这一支时，平均成功率跌到 23.93%，因为纯注意力会漏掉对比度低但几何关键的轮廓 token，动作随即失准（论文报告）。注意力与边缘并集是保精度的必要组合，不是可选增强。

## 运行入口

公开仓库只含 OpenVLA/LIBERO 这条可运行路径，按 OpenVLA 官方步骤装好环境后从 `experiments/robot/libero/` 下跑：

```bash
cd experiments/robot/libero
python run_libero.py \
    --pretrained_checkpoint /path/to/openvla-7b-finetuned-libero-spatial \
    --task_suite_name libero_spatial \
    --cuda_device 0
```

各套件的调度与剪枝阈值写死在 `run_libero.py` 里按 `task_suite_name` 分支，例如 `libero_spatial` 用 `z_xy_rate_skip=0.4`、`z_max_skip=0.3`、`z_thre_prune=0.5`、`z_min_prune=0.9`、`step_skip=1`，`libero_object`、`libero_goal`、`libero_10` 各有一组。换套件只改 `--task_suite_name`，对应阈值随分支切换。

## 本页小结

- 剪枝在双视觉主干出 patch、进投影层前进行：`PrismaticVisionBackbone.forward()` 取 SigLIP 末层注意力打分，`edge_detection`/`map_edges_to_tokens` 取 Canny 边缘 token。
- 保留数由累积注意力过阈值定，阈值随 `cfg.z_trans` 线性变化、低于 `z_thre_prune` 时取 1 不剪；注意力与边缘索引 `np.union1d` 取并集且保序，对 DINOv2、SigLIP 两路同索引剪。
- 可调参数：`z_thre_prune` 0.3–0.5、`z_min_prune` 0.7–0.9、Canny 双阈值 100/200；去掉边缘分支平均成功率跌到 23.93%。
- LIBERO 上无损档 74.90%@1.35×（FLOPs 73.64%）、激进档 71.90%@1.50×（FLOPs 66.51%）；仓库仅 OpenVLA/LIBERO 可跑。

## 导航

- 上一节：[模型调度源码](03-model-scheduling.md)
- 返回上级：[SP-VLA](../03-sp-vla.md)
