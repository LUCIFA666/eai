# OXE 与 RLDS

目标：理解 OpenVLA 为什么把机器人数据放在 Open X-Embodiment / RLDS 这条数据链路里，以及这条链路在训练中承担什么。

OpenVLA 的主模型来自大规模机器人演示数据训练。本页关注许多机器人数据集如何以统一格式进入同一个 VLA 训练脚本。OpenVLA 选择 Open X-Embodiment 数据集合，并用 RLDS / TFDS 作为训练数据入口。

## OXE 在 OpenVLA 中的位置

Open X-Embodiment 提供了多来源的机器人演示数据。OpenVLA 的主模型使用其中面向 manipulation 的数据 mixture，并在 README 中把主模型数据规模写成 970K trajectories。这个规模解释了 OpenVLA 为什么适合作为 fine-tuning 起点：checkpoint 已经见过多种任务、场景和机器人数据。

数据规模本身不能直接说明目标机器人上的成功率。目标任务还要看动作空间、相机视角、语言指令格式和统计量是否对齐。后面进入 LoRA、LIBERO 或 Bridge 时，这些条件都要单独检查。

## RLDS 负责什么

RLDS / TFDS 给 OpenVLA 提供统一的数据读取方式。训练脚本不直接手写每个数据集的文件读取逻辑，而是把数据集交给 RLDS loader，再由 OpenVLA 的 dataset wrapper 转成模型需要的 batch。

`RLDSDataset` 是这条链路在 PyTorch 侧的入口：

```python
if self.data_mix in OXE_NAMED_MIXTURES:
    mixture_spec = OXE_NAMED_MIXTURES[self.data_mix]
else:
    mixture_spec = [(self.data_mix, 1.0)]

per_dataset_kwargs, weights = get_oxe_dataset_kwargs_and_weights(
    self.data_root_dir,
    mixture_spec,
    load_camera_views=("primary",),
    load_depth=False,
    load_proprio=False,
    load_language=True,
    action_proprio_normalization_type=NormalizationType.BOUNDS_Q99,
)
```

这段代码说明 `data_mix` 有两种读法：命中 `OXE_NAMED_MIXTURES` 时，它是一组数据集和采样权重；没有命中时，它会被当成单个数据集。OpenVLA 默认只加载 primary camera、语言指令和动作，不加载 depth，也不把 proprio 作为模型输入。

## Batch 进入模型前变成什么

RLDS batch 还要经过 `RLDSBatchTransform`。这一步把一条 transition 转成图像、prompt、action tokens 和 labels：

```python
dataset_name, action = rlds_batch["dataset_name"], rlds_batch["action"][0]
img = Image.fromarray(rlds_batch["observation"]["image_primary"][0])
lang = rlds_batch["task"]["language_instruction"].decode().lower()

conversation = [
    {"from": "human", "value": f"What action should the robot take to {lang}?"},
    {"from": "gpt", "value": self.action_tokenizer(action)},
]
```

这里的 `action` 已经是数据管线归一化后的动作。`action_tokenizer(action)` 只负责把它写成 token 字符串；动作尺度来自更早的数据统计量步骤。

## LIBERO RLDS 也按同一套接口检查

OpenVLA 复现中会遇到 LIBERO RLDS 数据。数据侧仍然先按 RLDS 接口检查：主相机图像能否读到，`language_instruction` 是否存在，action 维度是否符合 checkpoint，统计量 key 能否和 `unnorm_key` 对上。suite 名称、任务数量和 rollout 步数会影响评测记录，但不会改变这里的数据读取接口。

## 本页小结

- OXE 提供多来源机器人演示数据，RLDS / TFDS 提供统一读取入口。
- `data_mix` 可以指向命名 mixture，也可以指向单个数据集。
- `RLDSBatchTransform` 把 RLDS transition 转成图像、prompt、action tokens 和 labels。
- 动作尺度来自数据统计量，action tokenizer 只处理归一化后的动作表示。

## 导航

- 上一节：[数据与动作统计量](../04-data-and-statistics.md)
- 返回上级：[数据与动作统计量](../04-data-and-statistics.md)
- 下一节：[Mixture 与 Transform](02-mixtures-and-transforms.md)
