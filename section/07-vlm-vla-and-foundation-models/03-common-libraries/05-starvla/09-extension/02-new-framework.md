# 新 framework

目标：添加一个自己的 VLA framework，并复用 StarVLA 的 dataloader、trainer 和 deployment。

官方“乐高式设计”文档给出的最小步骤是：

1. 在 `starVLA/model/framework/` 下创建 framework 文件。
2. 继承基类并实现 `forward()` 和 `predict_action()`。
3. 在文件末尾添加单文件验证入口。
4. 在训练 YAML 中设置 `framework.name`。

## 文件位置

当前代码已经把 framework 分成子目录：

```text
starVLA/model/framework/VLM4A/
starVLA/model/framework/WM4A/
```

如果是 VLM-based action model，建议放在 `VLM4A/`；如果是 world-model-based，建议放在 `WM4A/`。`_auto_import_framework_modules()` 会扫描子包并 import 模块。

## 最小模板

```python
from dataclasses import dataclass, field
import numpy as np
import torch

from starVLA.model.framework.base_framework import baseframework
from starVLA.model.framework.share_tools import merge_framework_config
from starVLA.model.tools import FRAMEWORK_REGISTRY


@dataclass
class MyFrameworkDefaultConfig:
    name: str = "MyFramework"
    qwenvl: dict = field(default_factory=lambda: {
        "base_vlm": "<MODEL_ROOT>/Qwen3-VL-4B-Instruct",
        "attn_implementation": "flash_attention_2",
    })
    action_model: dict = field(default_factory=lambda: {
        "action_dim": 7,
        "state_dim": 7,
        "action_horizon": 8,
    })


@FRAMEWORK_REGISTRY.register("MyFramework")
class MyFramework(baseframework):
    def __init__(self, config=None, **kwargs):
        super().__init__()
        self.config = merge_framework_config(MyFrameworkDefaultConfig, config)
        # self.backbone = ...
        # self.action_model = ...

    def forward(self, examples, **kwargs):
        actions = [example["action"] for example in examples]
        # action_loss = ...
        return {"action_loss": action_loss}

    @torch.inference_mode()
    def predict_action(self, examples, **kwargs):
        # normalized_actions = ...
        return {"normalized_actions": normalized_actions}
```

## 单文件验证

文件末尾建议写：

```python
if __name__ == "__main__":
    from omegaconf import OmegaConf
    from PIL import Image

    cfg = OmegaConf.load("examples/LIBERO/train_files/starvla_cotrain_libero.yaml")
    cfg.framework.name = "MyFramework"
    model = MyFramework(cfg).cuda()

    image = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    sample = {
        "image": [image],
        "lang": "test instruction",
        "action": np.zeros((8, 7), dtype=np.float32),
    }
    out = model.forward([sample])
    print(out["action_loss"])
    print(model.predict_action([sample])["normalized_actions"].shape)
```

这个测试比直接跑训练更快暴露 shape 和 import 问题。

## 对外 API 要保持干净

官方文档强调 `starVLA/model/framework/<your_framework>.py` 是模型对外接口的主要位置，应尽量和论文框架图结构一致。实践中可以理解为：

- trainer 不应该知道你的内部模块细节。
- dataloader 不应该做你的 tokenizer 或特殊图像处理。
- deployment 不应该为你的模型写特殊分支。
- 特殊行为通过 config 或 `predict_action(**kwargs)` 暴露。

## 小结

- 新 framework 必须注册到 `FRAMEWORK_REGISTRY`。
- `forward()` 返回 `action_loss`，`predict_action()` 返回 `normalized_actions`。
- 单文件验证是必须步骤，先于多卡训练。
- framework 是模型对外边界，内部可以复杂，对外接口要稳定。

## 动手练习

1. 运行 `rg -n "class Qwen_OFT|FRAMEWORK_REGISTRY.register|def forward|def predict_action" starVLA/model/framework/VLM4A/QwenOFT.py`，提取最小 framework 的结构。
2. 在本地新建 `MyFramework` 后，把 YAML 中 `framework.name` 设为注册名，并调用 `build_framework()`。成功输出应返回你的 class 实例。
3. 用随机图像、语言和动作跑一次 `forward()`，成功输出应包含可反向传播的 loss 标量或你定义的等价训练指标。

## 导航

- 上一节：[01 接入自有 LeRobot 数据](01-custom-lerobot-dataset.md)
- 返回上级：[扩展 StarVLA](../09-extension.md)
- 下一节：[03 新 backbone 或 action head](03-new-backbone-or-head.md)
