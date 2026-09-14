# 模型组件

目标：理解 VLA-Adapter 的 backbone、processor、action head、proprio projector、Pro flags、statistics 和 checkpoint 组件如何配套使用。

读 VLA-Adapter 的训练和评测命令时，容易把 `pretrained_checkpoint`、`vlm_path`、`use_proprio`、`use_pro_version` 这些参数看成彼此独立的开关。实际运行时，它们会落到不同模型组件上：有些决定基础 VLM 和 processor，有些决定 action head 结构，有些决定 proprio 输入和 normalization。这里先把这些对应关系理顺，后面排查 checkpoint、rollout 和 policy server 时会更容易定位问题。

可以按加载来源、动作输出、状态输入、Pro 配置和评测加载顺序来读下面几页。

## 学习路径

| 页面 | 关注点 | 重点 |
| --- | --- | --- |
| [Prismatic Backbone](04-model/01-prismatic-backbone.md) | `vlm_path`、`config_file_path`、processor 分别影响什么 | tiny Prismatic、`use_minivlm`、processor/config |
| [Action Head 与 Action Chunk](04-model/02-action-head-and-action-chunk.md) | VLA-Adapter 如何输出 7D x 8-step 动作 | L1 head、`ACTION_DIM`、`NUM_ACTIONS_CHUNK`、open-loop |
| [Proprio Projector](04-model/03-proprio-projector.md) | `use_proprio=True` 会牵动哪些输入和文件 | 8D proprio、projector 权重、proprio normalization |
| [Pro Version Flags](04-model/04-pro-version-flags.md) | Pro checkpoint 为什么要求 flags 成套对齐 | `use_pro_version`、`num_images_in_input`、`use_film`、`use_proprio` |
| [Checkpoint 组件加载](04-model/05-checkpoint-component-loading.md) | eval / deploy 到底从 checkpoint 里加载哪些组件 | `openvla_utils.py`、本地路径、HF repo id、组件体检 |
| [训练、评测与部署的一致性](04-model/06-training-eval-consistency.md) | 训练、评测和部署之间要保持一致的配置 | flags、维度常量、statistics、checkpoint 路径、`unnorm_key` |

## 这些配置分别影响哪里

```text
vlm_path / config_file_path
  -> Prismatic backbone + processor
num_images_in_input
  -> 图像输入数量
use_proprio
  -> proprio projector + 8D state + statistics
use_l1_regression / use_pro_version
  -> action head 结构和权重文件
ACTION_DIM / NUM_ACTIONS_CHUNK
  -> action shape 和 eval open-loop 节奏
dataset_statistics.json / unnorm_key
  -> action/proprio normalization 和 unnormalization
```

同一个 checkpoint 要和同一组输入结构、组件权重、statistics 和 flags 一起使用。只要其中一项来自另一套配置，问题可能在加载阶段暴露，也可能等到 rollout 时才表现为动作尺度异常或成功率异常。

## 导航

- 上一节：[自定义数据接入](03-data/05-custom-data-format.md)
- 返回上级：[VLA-Adapter](../06-vla-adapter.md)
- 下一节：[Prismatic Backbone](04-model/01-prismatic-backbone.md)
