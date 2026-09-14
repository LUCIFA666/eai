# 跨帧 token 缓存

VLA-Cache 的选择逻辑集中在 `experiments/robot/vla_cache_utils.py`，通过 `experiments/robot/openvla_utils.py` 的 `get_vla_action()` 挂进推理流程。本页按这条链给出三段选择逻辑的实现、复用索引与每层比例如何写进模型配置、跨帧 cache 怎样携带裁剪，以及可调参数和加速数字。按上一帧缓存逐层替换复用 token 的 KV 这一步不在主仓库的可见代码里，据其 README 由配套改动的 `transformers` 完成。

## 本节目标

理解静态 patch 检测、任务相关剔除、层自适应比例三段代码各做什么、参数默认值是多少、复用信息经哪两个 config 字段传入注意力、KV 替换为什么要配套改动版 `transformers`，以及跨帧 cache 的携带与裁剪如何逐帧衔接。

## 静态 patch 检测

`find_static_patches` 在原始像素 patch 上算帧间余弦相似度，过阈值后按相似度取 Top-k。图像固定 224px、patch 边长 14，因此是 16×16 的 patch 网格：

```python
def find_static_patches(img_0, img_1, patch_size=14, top_k=150, sim_threshold=0.996):
    patches1 = patchify(img_0, patch_size)
    patches2 = patchify(img_1, patch_size)
    similarity = calculate_patch_similarity(patches1, patches2)   # 逐 patch 余弦相似度
    grid_size = 224 // patch_size                                 # = 16
    similarity_2d = similarity.reshape(grid_size, grid_size)
    patch_scores = [(i * grid_size + j, similarity_2d[i, j])
                    for i in range(grid_size) for j in range(grid_size)
                    if similarity_2d[i, j] >= sim_threshold]       # 过阈值 τ
    patch_scores.sort(key=lambda x: x[1], reverse=True)
    return [idx for idx, _ in patch_scores[:top_k]]                # 取最稳的 top_k 个
```

阈值 `sim_threshold` 默认 0.996，判定偏严，只把几乎不变的 patch 收进来。相似度直接在像素上算、不过视觉编码器，这一步开销约 $\mathcal{O}(H^2)$，远低于每层基线成本。

## 任务相关剔除

第二段从解码器的 text-to-vision 注意力算任务相关度，再把任务相关 patch 从静态集里减掉。`token_attention_merge` 取某一解码层的注意力，按 OpenVLA 的固定 token 布局切出 text 到 vision 的子块并在多头上取均值。布局是 1 个前缀 token、256 个视觉 token、35 个文本 token：

```python
def token_attention_merge(multihead_attention, layer_id=15):
    attn_map = multihead_attention[layer_id].to(torch.float32).squeeze(0).mean(dim=0)  # 多头取均值
    v_token_start = 1; v_token_end = v_token_start + 256          # 视觉 token 区间
    t_token_start = v_token_end; t_token_end = t_token_start + 35 # 文本 token 区间
    attention_pos = multihead_attention[-1]
    text_mask = (attention_pos >= t_token_start) & (attention_pos < t_token_end)
    relation = attn_map[text_mask, v_token_start:v_token_end]     # 文本 -> 视觉
    return relation.mean(dim=0).cpu()
```

`task_relevant_selection` 取注意力分数的 Top-k 作为任务相关 patch，与静态集做差集，得到静态且非任务相关的复用集。返回的索引统一 `+1`，对应前缀 token 占据的下标 0：

```python
def task_relevant_selection(multihead_attention, image, significant_patches, top_k=120):
    attn_score = token_attention_merge(multihead_attention)
    top_patches = get_top_attention_patches(attn_score, top_k)    # 任务相关 patch
    only_significant = set(significant_patches) - set(top_patches)  # 静态且非任务相关
    ...
    v_token_start = 1
    remaining = sorted([pid + v_token_start for pid in only_significant])  # +1 偏移，对应前缀 token
    return np.array(result_image), remaining
```

这里 `only_significant` 就是复用集 $\mathcal{P}_{\mathrm{reuse}} = \mathcal{P}_{\mathrm{static}} \setminus \mathcal{P}_{\text{task-relevant}}$。1 前缀加 256 视觉加 35 文本、patch 边长 14、16×16 网格、224px 输入都是 OpenVLA 的固定几何，换基座模型时这套下标需要按对应布局调整。

## 层自适应复用比例

`get_layer_mask_schedule` 把每层注意力熵折算成复用比例。熵越低表示注意力越集中，复用比例越高：

```python
def get_layer_mask_schedule(multihead_attention, apply_weighted_growth=True, growth_factor=0.55):
    entropies = []
    for attn in multihead_attention[:-1]:
        attn = attn.mean(dim=1)[0]
        attn /= attn.sum(dim=-1, keepdim=True) + 1e-10
        token_entropy = -torch.sum(attn * torch.log(attn + 1e-10), dim=-1)  # 每 token 注意力熵
        entropies.append(token_entropy.mean())
    entropies = torch.stack(entropies)
    norm_entropy = (entropies - entropies.min()) / (entropies.max() - entropies.min() + 1e-10)
    reuse = 1.0 - norm_entropy                       # 熵低（更集中）-> 复用更多
    if apply_weighted_growth:                        # 对逐层上升的增量做平滑
        reuse = reuse.tolist()
        for i in range(1, len(reuse)):
            delta = reuse[i] - reuse[i - 1]
            if delta > 0:
                reuse[i] = reuse[i - 1] + delta * growth_factor
        reuse = torch.tensor(reuse, ...)
    return reuse
```

`growth_factor` 默认 0.55，对相邻层之间上升的复用比例增量做平滑，避免复用比例沿层跳增。

## 挂载与 KV 替换的落点

三段逻辑在 `get_vla_action()` 里衔接。复用信息通过两个 config 字段传进语言模型：`reusable_patches` 是复用 token 的索引，`proportion_attn_var` 是每层复用比例。首帧没有上一帧缓存与注意力，跳过选择，走完整前向：

```python
if cfg.use_vla_cache:
    if prompt_cache is not None:                     # 有上一帧缓存才做静态选择
        stable_patches = find_static_patches(image, prev_image, top_k=130)
    if prev_attn is not None:                        # 有上一帧注意力才做任务相关过滤
        result_image, remaining_static_tokens_indices = task_relevant_selection(prev_attn, image, stable_patches)
        mask_indices = torch.tensor(remaining_static_tokens_indices, device=DEVICE) if remaining_static_tokens_indices else None
        vla.language_model.config.reusable_patches   = mask_indices                     # 复用哪些 token
        vla.language_model.config.proportion_attn_var = get_layer_mask_schedule(prev_attn)  # 每层比例 α^l
...
action, last_caches = vla.predict_action(**inputs, do_sample=False, return_dict_in_generate=True,
                                         output_attentions=True, past_key_values=prompt_cache)
```

注意这里静态选择用的 `top_k=130`，与 `find_static_patches` 定义里的默认 150 不同，实际生效的是调用处这个 130。写入 config 之后，注意力前向按这两个字段、逐层用上一帧缓存替换复用 token 的 KV，这一步的代码不在主仓库里。据主仓库 `README_VLA_Cache.md`，它由配套改动的 `transformers` 完成，因此运行 VLA-Cache 需要装该仓库指定的改动版 `transformers`，装官方版不会触发复用。

## 跨帧 cache 携带与裁剪

跨帧复用要求把这一帧的 KV cache 和注意力留给下一帧。`predict_action()` 在 `modeling_prismatic.py` 里生成动作后，把 KV cache 裁掉刚生成的约 7 个动作 token，只保留 prompt 部分，回填成下一帧的起始缓存：

```python
results = self.generate(input_ids, max_new_tokens=self.get_action_dim(unnorm_key), **kwargs)
attentions = results.attentions
past_key_values = results.past_key_values
max_cache_length = past_key_values._seen_tokens - self.get_action_dim(unnorm_key) + 1
past_key_values.crop(max_length=max_cache_length)                # 裁掉动作 token，留 prompt 缓存
last_caches = {"past_key_values": past_key_values, "attentions": attentions[0]}
```

评测循环 `libero/run_libero_eval.py` 持有 `last_caches`（起始为 `None`），并在观测里带上 `prev_image`，把缓存与上一帧图像逐帧传给 `get_vla_action`。于是第 $t$ 帧复用第 $t-1$ 帧的 KV cache 与注意力：注意力用于任务相关过滤和熵调度，cache 用于 KV 替换。

## 可调参数

VLA-Cache 的行为由几个阈值和比例控制，实际生效值以调用处为准：

| 参数 | 含义 | 默认 | 调大 / 调小的影响 |
| --- | --- | --- | --- |
| `sim_threshold` (τ) | 帧间静态判定阈值 | 0.996 | 调大更严、复用更少更稳；调小更松、复用更多但易纳入变化区域 |
| 静态 `top_k` | 静态复用集上限 | 130（调用处） | 调大复用更多、加速更强；调得过大会纳入非静态 token 而降精度 |
| 任务相关 `top_k` | 剔除的任务相关 token 数 | 120 | 调大剔除更多、更保精度但复用更少；调小复用更多但易沿用过期语义 |
| `growth_factor` | 层间复用比例增量的平滑系数 | 0.55 | 调大各层复用比例上升更快、更激进；调小更平缓保守 |

## 加速数字

LIBERO 四套件上相对 OpenVLA 的效率与精度（论文报告，RTX 4090）：

| 指标 | OpenVLA | + VLA-Cache |
| --- | --- | --- |
| 平均成功率 | 75.0% | 74.7% |
| FLOPs | 1.864T | 1.355T（约 −27%） |
| 单步延迟 | 51.91ms | 31.83ms（约 1.63×） |
| 控制频率 | 4.23Hz | 4.59Hz |

对照单帧剪枝：SparseVLM 延迟反升到 83.39ms、成功率 64.7%，FastV 延迟 53.28ms、成功率 73.3%，都不及 VLA-Cache。OpenVLA-OFT 上仍有叠加收益，控制频率 65.10Hz 提到 78.98Hz、成功率 96.8% 到 97.4%。SIMPLER 上以 CogAct 为基座，延迟从 54.29ms 降到 39.63ms（约 1.37×）、成功率相当。token 选择的消融链（LIBERO-Spatial）说明每一阶段的作用：

| 配置 | 成功率 | 单步延迟 |
| --- | --- | --- |
| OpenVLA | 84.4% | 51.56ms |
| + 静态 token | 74.2% | 31.03ms |
| + 剔除任务相关 | 82.6% | 31.03ms |
| + 层自适应 | 83.8% | 32.22ms |

只加静态复用把延迟降到 31.03ms 但精度下降，任务相关过滤在几乎不加延迟的前提下把成功率恢复到 82.6%，层自适应再提升到 83.8%。

## 运行入口

两个基座各用一个 conda 环境，在 `src/<model>/` 下 `pip install -e .`，并装仓库 README 指定的改动版 `transformers`。权重需下载到 `src/openvla/checkpoints`，不能走默认 HuggingFace 缓存：

```bash
python vla_cache_scripts/download_model_local.py --model_id openvla/openvla-7b-finetuned-libero-spatial

python experiments/robot/libero/run_libero_eval.py \
  --pretrained_checkpoint checkpoints/openvla-7b-finetuned-libero-spatial \
  --task_suite_name libero_spatial --use_vla_cache True
```

`--use_vla_cache` 一个开关控制整条复用逻辑，设 `False` 即回到原始 OpenVLA 推理，便于对照延迟与成功率。任务套件可选 `libero_spatial`、`libero_object`、`libero_goal`、`libero_long`；OpenVLA-OFT 走 `src/openvla-oft/` 下同名脚本。

## 本页小结

- 选择逻辑在 `vla_cache_utils.py`：`find_static_patches`（帧间余弦相似度过阈值取 Top-k）、`task_relevant_selection`（差集出静态且非任务相关、索引 `+1` 偏移过前缀 token）、`get_layer_mask_schedule`（注意力熵折算每层复用比例）。
- 复用信息经 `language_model.config.reusable_patches` 与 `proportion_attn_var` 传入；据主仓库 README，按这两个字段逐层替换 KV 的一步由配套改动版 `transformers` 完成，运行时需装该版本。
- 跨帧携带靠 `predict_action()` 把 KV cache 裁掉约 7 个动作 token 后回填，评测循环用 `last_caches` 与 `prev_image` 逐帧衔接，第 $t$ 帧复用第 $t-1$ 帧的缓存与注意力。
- 可调参数：`sim_threshold` 0.996、静态 `top_k` 130、任务相关 `top_k` 120、`growth_factor` 0.55；LIBERO 上 FLOPs 降约 27%、延迟约 1.63×、成功率降 0.3 个百分点。

## 导航

- 上一节：[整体架构](02-architecture.md)
- 返回上级：[VLA-Cache](../01-vla-cache.md)
