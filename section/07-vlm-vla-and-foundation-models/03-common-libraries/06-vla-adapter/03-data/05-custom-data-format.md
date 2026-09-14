# 自定义数据接入

目标：理解改数据格式、接自定义 RLDS、替换 action 或 proprio 时，VLA-Adapter 中需要同步检查的源码入口。

VLA-Adapter 的训练代码默认走 RLDS / OXE pipeline。接入新数据时，重点是让新数据满足同一套字段和配置约束：OXE 能找到 dataset name，标准化函数能把原始字段整理成 image / language / action / proprio，batch transform 能读到这些字段，statistics 能保存并在评测或部署中被同一个 `unnorm_key` 找到。

## 最小改动面

| 读者任务 | 主要入口 | 影响 |
| --- | --- | --- |
| 接入新的 RLDS / TFDS 数据集 | TFDS schema、`data_root_dir`、版本目录 | TFDS builder 能否读到样本和 metadata |
| 注册数据集名称 | `oxe/mixtures.py`、`oxe/configs.py` | `dataset_name` 能否找到 mixture、camera view、state key、action encoding |
| 统一字段语义 | `oxe/transforms.py` | 原始字段能否变成 VLA-Adapter 期望的 action、`EEF_state`、`gripper_state` 或自定义 state |
| 改 action / proprio 维度 | `prismatic/vla/constants.py`、action head、proprio projector | `ACTION_DIM`、`PROPRIO_DIM`、`NUM_ACTIONS_CHUNK` 和 checkpoint 组件是否一致 |
| 改图像输入数量 | `num_images_in_input`、`image_obs_keys`、`RLDSBatchTransform`、eval / deploy obs | primary / wrist 图像是否在训练、评测和 server 请求中一致 |
| 共享 statistics | `dataset_statistics.json`、`check_unnorm_key()`、policy server payload | action 反归一化和 proprio normalization 是否使用同一数据 key |

## 注册新数据集

如果新数据仍然采用 RLDS / TFDS 格式，可以沿用 OXE 的三处注册入口。下面是最小形态，字段名需要替换成新数据的真实 schema：

```python
# prismatic/vla/datasets/rlds/oxe/mixtures.py
OXE_NAMED_MIXTURES["my_robot_task"] = [("my_robot_task", 1.0)]

# prismatic/vla/datasets/rlds/oxe/configs.py
OXE_DATASET_CONFIGS["my_robot_task"] = {
    "image_obs_keys": {"primary": "image", "secondary": None, "wrist": "wrist_image"},
    "depth_obs_keys": {"primary": None, "secondary": None, "wrist": None},
    "state_obs_keys": ["EEF_state", "gripper_state"],
    "state_encoding": StateEncoding.POS_EULER,
    "action_encoding": ActionEncoding.EEF_POS,
}

# prismatic/vla/datasets/rlds/oxe/transforms.py
OXE_STANDARDIZATION_TRANSFORMS["my_robot_task"] = my_robot_task_transform
```

`mixtures.py` 负责名字能否被 `RLDSDataset` 识别；`configs.py` 负责 camera view、state key 和 action encoding；`transforms.py` 负责把原始 trajectory 改成这些配置能读取的字段。三者使用同一个 key，训练命令里的 `--dataset_name my_robot_task` 才能走完整链路。

## 编写标准化函数

标准化函数适合处理原始 schema 和 VLA-Adapter 内部字段之间的差异。LIBERO 的做法可以作为参照：action 的前 6 维保持末端控制，gripper 维经过 clip 和方向反转，state 被拆成 `EEF_state` 与 `gripper_state`。

```python
def my_robot_task_transform(trajectory):
    trajectory["action"] = build_action_from_raw_fields(trajectory)
    trajectory["observation"]["EEF_state"] = trajectory["observation"]["state"][:, :6]
    trajectory["observation"]["gripper_state"] = trajectory["observation"]["state"][:, -2:]
    return trajectory
```

如果新机器人不是 6D end-effector + gripper，改动会继续传到 `ActionEncoding`、`ACTION_DIM`、action head 输出维度、statistics mask 和评测动作接口。此时不适合只改 transform；更稳妥的做法是先列出训练 batch 中 `actions` 和 `proprio` 的目标 shape，再把 OXE 配置、constants、模型组件和 eval / deploy 输入同步到同一 shape。

## 改 action 或 proprio 维度

`prismatic/vla/constants.py` 会根据命令行参数推断平台；无法识别时默认使用 LIBERO 常量。

```python
LIBERO_CONSTANTS = {
    "NUM_ACTIONS_CHUNK": 8,
    "ACTION_DIM": 7,
    "PROPRIO_DIM": 8,
    "ACTION_PROPRIO_NORMALIZATION_TYPE": NormalizationType.BOUNDS_Q99,
}
```

换动作空间时，`ACTION_DIM` 会影响 action tokenizer、action head、collator 中的 `actions` shape、statistics 维度和模型输出反归一化。换 proprio 时，`PROPRIO_DIM` 会影响 `ProprioProjector`、`RLDSBatchTransform` 返回的 `proprio`、`openvla_utils.normalize_proprio()` 和评测脚本里创建 projector 的维度。LIBERO 评测脚本当前在 `initialize_model()` 中传入 `proprio_dim=8`，自定义 benchmark 如果使用不同 proprio 维度，需要有对应的评测入口。

## 改图像输入或 prompt 分支

图像输入数量同时出现在训练参数、OXE camera view 和推理观测中。`num_images_in_input > 1` 会让训练 transform 读取 wrist 图像；评测和部署侧的 `get_vla_action()` 也会在 `cfg.num_images_in_input > 1` 时把 observation 中包含 `wrist` 的图像加入输入。

```python
all_images = [obs["full_image"]]
if cfg.num_images_in_input > 1:
    all_images.extend([obs[k] for k in obs.keys() if "wrist" in k])
```

如果新数据只有单路图像，可以把训练、评测和部署都收敛到 `num_images_in_input=1`。如果增加更多 camera view，需要同时检查 `image_obs_keys`、`RLDSBatchTransform` 的 wrist 收集逻辑、processor 拼接方式和 policy server 的请求字段。

`use_minivlm` 也会影响训练和评测之间的数据接口。训练 transform 与 `openvla_utils.get_vla_action()` 都会依据这个 flag 构造 prompt；checkpoint、processor 和评测参数应保持同一分支。

## Statistics 和评测部署边界

新数据训练后，`dataset_statistics.json` 的顶层 key 应与训练 `dataset_name` 对齐。评测脚本的 `task_suite_name -> unnorm_key` fallback 当前服务 LIBERO 的 `_no_noops` 命名，如果新 benchmark 不沿用这个命名规则，就需要在评测入口显式选择或设置 `unnorm_key`。

policy server 侧还要确认请求 payload 的 observation 字段和训练一致：`full_image`、wrist 图像字段、`state` 维度、task instruction 和 `unnorm_key`。server 能返回 action 只能说明请求和模型 forward 链路打通；动作是否适合新环境，还取决于 statistics、action mask、开放循环步数和环境执行接口。

## 一个可用的改造顺序

可以按下面的顺序缩小改动范围：

1. 先让 TFDS / RLDS builder 能读到一条 raw trajectory，并确认字段名和 dtype。
2. 在 OXE registry 中增加 dataset key、camera view、state key、action encoding 和 transform。
3. 用短训练检查第一个 `RLDSBatchTransform` 输出，重点看 `actions`、`proprio`、`pixel_values_wrist` 和 `dataset_name`。
4. 检查 collator 后的 batch shape 是否匹配 `ACTION_DIM`、`PROPRIO_DIM` 和 `NUM_ACTIONS_CHUNK`。
5. 确认 run 目录生成 `dataset_statistics.json`，顶层 key 与后续 `unnorm_key` 能对应。
6. 再进入 eval / deploy，核对 observation payload、prompt 分支和 action 反归一化。

## 导航

- 上一节：[Statistics 与归一化](04-statistics-and-normalization.md)
- 返回上级：[数据接口与管线](../03-data.md)
- 下一节：[模型组件](../04-model.md)
