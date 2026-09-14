# Pro Version Flags

目标：理解 `use_pro_version`、`use_proprio`、`num_images_in_input`、`use_film` 为什么要和 checkpoint 配置保持一致。

VLA-Adapter 官方提供 Pro checkpoint 和常规版 checkpoint。课程主线使用 Pro checkpoint，训练和评测命令里的几项配置需要保持同一组取值：

```bash
--use_proprio True
--num_images_in_input 2
--use_film False
--use_pro_version True
```

## 每个 flag 影响什么

| flag | VLA-Adapter 中的影响 | 不匹配时的风险 |
| --- | --- | --- |
| `use_proprio` | 是否加载 proprio projector，是否把 state 送入 action head。 | projector 文件缺失、state 缺失、输入结构不一致。 |
| `num_images_in_input` | processor 和模型输入图像数量。 | observation 提供图像数量与模型期望不一致。 |
| `use_film` | 是否启用 FiLM vision backbone wrapper，并加载对应 vision backbone 组件。 | backbone 分支和 checkpoint 文件不匹配。 |
| `use_pro_version` | action head 内部 block 结构。 | action head 加载失败，或加载后输出行为不可信。 |

`use_pro_version` 主要影响 `L1RegressionActionHead` 内部使用普通 block 还是 Pro block。checkpoint 是按训练时的结构保存的，所以评测时把这个 flag 临时改成另一种取值，并不会把权重转换成另一种模型。

主线的 eval 和 deploy 命令里，`use_pro_version` 是 `GenerateConfig` / `DeployConfig` 的显式字段（默认 `True`）。自定义脚本或 notebook 里构造的 cfg 如果缺这个字段，`get_action_head()` 会从 checkpoint 路径是否包含 `Pro` 自动推断（`experiments/robot/openvla_utils.py:502-506`）。显式传入 `--use_pro_version` 可以脱开这条路径名推断，例如把普通版 checkpoint 放进名字含 `Pro` 的目录时不会被误判成 Pro。

## Pro checkpoint 还会牵动哪些取值

官方 LIBERO-Pro checkpoint 的评测命令和本节训练命令都围绕上面的组合展开。实际排查时，还要一起看下面这些值：

| 依赖项 | 主线取值 |
| --- | --- |
| `use_l1_regression` | `True` |
| `ACTION_DIM` | `7` |
| `PROPRIO_DIM` | `8` |
| `NUM_ACTIONS_CHUNK` | `8` |
| `ACTION_PROPRIO_NORMALIZATION_TYPE` | `BOUNDS_Q99` |

如果确实要比较 Pro / Non-Pro，或者打开 FiLM，需要从训练命令、保存出来的 checkpoint 文件、评测命令和结果记录一起区分。只改 eval 命令里的一个 flag，通常只会制造加载错误或不可信的 rollout。

## 常见现象

如果 checkpoint 是 Pro 版但评测时用了 `--use_pro_version False`，或者训练时不开 proprio 但评测时打开 proprio，错误可能不只表现为加载失败，也可能表现为 rollout 成功率异常低。

## 导航

- 上一节：[Proprio Projector](03-proprio-projector.md)
- 返回上级：[模型组件](../04-model.md)
- 下一节：[Checkpoint 组件加载](05-checkpoint-component-loading.md)
